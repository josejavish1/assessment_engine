"""
Unit test suite for Phase 1: Canonical Workspace Contracts and Persistence Manager.
Verifies strict Pydantic V2 schema enforcement (extra="forbid"), crash-safe atomic persistence,
and physical workspace integration in working/[client_slug]/.
"""

import json
import pytest
from datetime import datetime, UTC
from pathlib import Path
from pydantic import ValidationError
from starlette.testclient import TestClient

from assessment_engine.domain.schemas.workspace_contracts import (
    ClientDossierV3,
    PerimeterDefinition,
    PerimeterScopeType,
    FinancialParameters,
    RegulatoryFrameworkSpec,
    DigitalTwinStateContract,
    SecurityTowerState,
    QuestionResponseItem,
    EvidenceVaultContract,
    EvidenceFragment,
    EvidenceSourceType,
    PipelineStatusContract,
    PipelineStageStatus,
)
from assessment_engine.infrastructure.storage.workspace_manager import (
    WorkspacePersistenceManager,
)
from server import app


@pytest.fixture
def temp_workspace(tmp_path: Path) -> WorkspacePersistenceManager:
    return WorkspacePersistenceManager(root_dir=tmp_path / "working")


def test_client_dossier_v3_strict_validation():
    """Verify ClientDossierV3 enforces valid formats and rejects arbitrary extra fields."""
    valid_dossier = ClientDossierV3(
        schema_version="3.0.0",
        client_slug="test-corp",
        legal_entity_name="Test Corporation",
        industry_vertical_code="heavy_manufacturing",
        primary_hq_country_iso="ES",
        output_locale="es",
        last_updated_utc=datetime.now(UTC).isoformat(),
        perimeter=PerimeterDefinition(
            scope_type=PerimeterScopeType.GLOBAL_HOLDING,
            target_entity_name="Test Corporation",
            employee_headcount=1200,
            operating_countries_iso=["ES", "FR"],
            critical_assets_summary=["Main Plant"],
        ),
        financials=FinancialParameters(
            base_currency_iso="EUR",
            annual_revenue_amount=450.0,
            ebitda_margin_pct=18.5,
            insurable_cyber_limit=10.0,
        ),
        regulatory_landscape=[
            RegulatoryFrameworkSpec(
                framework_id="NIS2",
                jurisdiction_iso="ES",
                enforcement_tier="Essential Entity",
                applicability_rationale="Heavy industrial manufacturing supplier",
            )
        ],
        executive_context_synthesis="Test corporate baseline summary.",
        strategic_pain_points=["OT/IT convergence"],
    )
    assert valid_dossier.client_slug == "test-corp"
    assert valid_dossier.financials.base_currency_iso == "EUR"

    # Verify extra="forbid" raises ValidationError
    data = valid_dossier.model_dump()
    data["arbitrary_injected_field"] = "HACK"
    with pytest.raises(ValidationError):
        ClientDossierV3.model_validate(data)


def test_atomic_persistence_lifecycle(temp_workspace: WorkspacePersistenceManager):
    """Verify atomic write, flush, and read lifecycle across all four contracts."""
    slug = "atomic-tenant"

    # 1. Client Intelligence
    dossier = ClientDossierV3(
        schema_version="3.0.0",
        client_slug=slug,
        legal_entity_name="Atomic Tenant Inc",
        industry_vertical_code="banking",
        primary_hq_country_iso="GB",
        output_locale="en",
        last_updated_utc=datetime.now(UTC).isoformat(),
        perimeter=PerimeterDefinition(
            scope_type=PerimeterScopeType.GLOBAL_HOLDING,
            target_entity_name="Atomic Tenant Inc",
            employee_headcount=2500,
            operating_countries_iso=["GB"],
            critical_assets_summary=["Core Banking Ledger"],
        ),
        financials=FinancialParameters(
            base_currency_iso="GBP",
            annual_revenue_amount=520.0,
        ),
    )
    saved_path = temp_workspace.save_client_intelligence(slug, dossier)
    assert saved_path.is_file()
    loaded_dossier = temp_workspace.load_client_intelligence(slug)
    assert loaded_dossier is not None
    assert loaded_dossier.legal_entity_name == "Atomic Tenant Inc"
    assert loaded_dossier.financials.base_currency_iso == "GBP"

    # 2. Digital Twin State
    twin = DigitalTwinStateContract(
        client_slug=slug,
        last_synchronized_utc=datetime.now(UTC).isoformat(),
        overall_maturity_index=3.85,
        completion_percentage=70.0,
        towers={
            "T1": SecurityTowerState(
                tower_id="T1",
                calibrated_maturity_score=3.5,
                target_to_be_score=4.5,
                assessor_forensic_notes="Tier III redundancy verified.",
                is_applicable=True,
                completed=True,
                question_responses=[
                    QuestionResponseItem(
                        question_id="T1.P1.K1.PR1",
                        response_text="Certified dual feed.",
                        maturity_indicator=3.5,
                    )
                ],
            )
        },
    )
    twin_path = temp_workspace.save_digital_twin_state(slug, twin)
    assert twin_path.is_file()
    loaded_twin = temp_workspace.load_digital_twin_state(slug)
    assert loaded_twin is not None
    assert loaded_twin.overall_maturity_index == 3.85
    assert loaded_twin.towers["T1"].calibrated_maturity_score == 3.5

    # 3. Evidence Vault
    vault = EvidenceVaultContract(
        client_slug=slug,
        total_fragments=1,
        integrity_hash="abc123hash",
        fragments=[
            EvidenceFragment(
                evidence_id="EV-1A2B3C",
                source_type=EvidenceSourceType.INTERVIEW_TRANSCRIPT,
                source_filename="transcript.docx",
                ingestion_timestamp_utc=datetime.now(UTC).isoformat(),
                raw_verbatim_text="We have completed migration to EKS.",
                normalized_claim="Full container orchestration in place",
                mapped_domain_ids=["T2"],
                confidence_score=0.95,
            )
        ],
    )
    vault_path = temp_workspace.save_evidence_vault(slug, vault)
    assert vault_path.is_file()
    loaded_vault = temp_workspace.load_evidence_vault(slug)
    assert loaded_vault is not None
    assert loaded_vault.total_fragments == 1
    assert loaded_vault.fragments[0].evidence_id == "EV-1A2B3C"

    # 4. Pipeline Status
    status = PipelineStatusContract(
        job_id="job-test-99",
        client_slug=slug,
        status=PipelineStageStatus.RUNNING,
        current_stage="FAIR_SIMULATION",
        progress_pct=35.0,
        message_key="pipeline.stage.fair",
    )
    status_path = temp_workspace.save_pipeline_status(slug, status)
    assert status_path.is_file()
    loaded_status = temp_workspace.load_pipeline_status(slug)
    assert loaded_status is not None
    assert loaded_status.status == PipelineStageStatus.RUNNING
    assert loaded_status.progress_pct == 35.0


def test_api_intake_persists_physical_workspace():
    """Verify that submit_intake on the live FastAPI app writes physical files to working/[client_slug]/."""
    client = TestClient(app)

    # 1. Login to obtain token
    login_res = client.post(
        "/api/auth/login",
        json={"email": "cto@atomic-test-enterprise.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Submit Intake
    intake_payload = {
        "profile": {
            "companyName": "Atomic Test Enterprise",
            "country": "ES",
            "industry": "heavy_manufacturing",
            "employees": 3400,
            "revenueM": 890.0,
            "currency": "EUR",
            "deliverableLanguage": "es",
            "operatingModel": "Hybrid IT/OT industrial operations",
            "primaryProviders": "AWS, Siemens, Fortinet",
            "strategicChallenges": "OT segmentation",
        },
        "evidence": [
            {
                "filename": "meeting_notes.docx",
                "summary": "OT air-gap partially dismantled for predictive telemetry",
                "towerId": "T6",
                "uploadedAt": datetime.now(UTC).isoformat(),
            }
        ],
        "ratings": {
            "T1": {"score": 3.2, "completed": True, "notes": "On-premise primary DC", "answers": {}},
            "T6": {"score": 2.8, "completed": True, "notes": "Legacy SCADA exposure", "answers": {}},
        },
    }

    res = client.post("/api/assessment/intake", json=intake_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PROCESSED"
    client_slug = data["client_slug"]
    assert client_slug in ["atomic-test-enterprise", "atomic_test_enterprise"]

    # 3. Verify physical files were created in working/[client_slug]/
    client_dir = Path("working") / client_slug
    assert client_dir.is_dir()
    assert (client_dir / "client_intelligence.json").is_file()
    assert (client_dir / "digital_twin_state.json").is_file()
    assert (client_dir / "evidence_vault.json").is_file()

    # Read back client_intelligence.json and verify contents
    with open(client_dir / "client_intelligence.json", "r", encoding="utf-8") as f:
        dossier_data = json.load(f)
    assert dossier_data["legal_entity_name"] == "Atomic Test Enterprise"
    assert dossier_data["financials"]["annual_revenue_amount"] == 890.0
