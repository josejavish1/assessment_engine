"""
Unit test suite verifying the self-service API server, authentication flow, and static SPA delivery.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_auth_registration_and_login(client: TestClient) -> None:
    test_email = f"cto_test_{pytest.__version__.replace('.', '_')}@enterprise.com"
    test_password = "SecurePassword123!"

    # 1. Register
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Chief Technology Officer",
            "organization": "Enterprise Test Inc.",
        },
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["organization"] == "Enterprise Test Inc."

    token = reg_data["access_token"]

    # 2. Get Me with Bearer Token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == test_email
    assert me_data["fullName"] == "Chief Technology Officer"

    # 3. Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": test_email, "password": test_password},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_intake_submission_and_actuarial_summary(client: TestClient) -> None:
    token = client.post(
        "/api/auth/login",
        json={"email": "cto_intake@enterprise.com", "password": "Password123!"},
    ).json()["access_token"]

    payload = {
        "profile": {
            "companyName": "Acme Holdings S.A.",
            "industry": "Manufacturing",
            "revenueM": 500.0,
            "employees": 2500,
            "primaryCloud": "Hybrid AWS",
            "geography": "EMEA",
        },
        "evidence": [
            {"name": "spec.pdf", "size": 10240, "type": "pdf", "assignedTower": "T1"},
            {"name": "network.docx", "size": 20480, "type": "docx", "assignedTower": "T9"},
        ],
        "ratings": {
            "T1": {"towerId": "T1", "name": "Governance", "score": 3.0, "notes": "Standardized"},
            "T2": {"towerId": "T2", "name": "Datacenter", "score": 3.5, "notes": "Tier III"},
        },
    }

    res = client.post(
        "/api/assessment/intake",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PROCESSED"
    assert data["composite_score"] == 3.25
    assert data["estimated_var_m"] > 0
    assert data["deliverables_ready"] is True


def test_resolve_context_domain_and_free_text(client: TestClient) -> None:
    # 1. Test Domain Resolution (Egypt .eg)
    domain_res = client.post(
        "/api/assessment/resolve_context",
        json={"input": "acme.com.eg"},
    )
    assert domain_res.status_code == 200
    d_data = domain_res.json()
    assert d_data["countryCode"] == "EG"
    assert d_data["countryName"] == "Egypt"
    assert d_data["currency"] == "EGP"

    # 2. Test Multilingual Free-Text (Polish input with Cairo and employees)
    text_res = client.post(
        "/api/assessment/resolve_context",
        json={"input": "Firma produkcyjna w Kairze, 2000 pracownikow, 850M obrotu"},
    )
    assert text_res.status_code == 200
    t_data = text_res.json()
    assert t_data["countryCode"] == "EG"
    assert t_data["currency"] == "EGP"
    assert t_data["industry"] == "heavy_manufacturing"
    assert t_data["employees"] == 2000
    assert t_data["revenueM"] == 850.0


def test_deliverable_download(client: TestClient) -> None:
    res = client.get("/api/assessment/deliverables/Molins_202610_Tomo_1_Diagnostico_ASIS.docx")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in res.headers["content-type"]
    assert len(res.content) > 0


def test_dynamic_config_endpoints(client: TestClient) -> None:
    # 1. Towers endpoint default English
    towers_res_en = client.get("/api/config/towers")
    assert towers_res_en.status_code == 200
    towers_en = towers_res_en.json()
    assert len(towers_en) == 10
    assert towers_en[0]["tower_id"] == "T1"
    assert towers_en[0]["tower_name"] == "Physical Data Center & Facilities"

    # 2. Towers endpoint localized in Spanish
    towers_res_es = client.get("/api/config/towers?lang=es")
    assert towers_res_es.status_code == 200
    towers_es = towers_res_es.json()
    assert len(towers_es) == 10
    assert towers_es[0]["tower_id"] == "T1"
    assert "Centro de Datos" in towers_es[0]["tower_name"]

    # 3. UI locales endpoint with fallback
    ui_res = client.get("/api/config/ui_locales?lang=es")
    assert ui_res.status_code == 200
    ui_data = ui_res.json()
    assert ui_data["current_locale"] == "es"
    assert len(ui_data["supported_locales"]) >= 6
    assert "translations" in ui_data
    assert "Diagnóstico de Infraestructura TI" in ui_data["translations"]["welcome_headline"]
    assert ui_data["translations"]["tab_welcome_short"] == "Inicio"

    # 4. Reference data endpoints
    curr_res = client.get("/api/config/currencies")
    assert curr_res.status_code == 200
    assert len(curr_res.json()) >= 10

    count_res = client.get("/api/config/countries")
    assert count_res.status_code == 200
    assert len(count_res.json()) >= 10


def test_spa_static_serving(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text.lower()
    assert "Assessment Engine" in res.text
