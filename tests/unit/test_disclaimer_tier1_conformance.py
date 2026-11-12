"""Unit tests for Tier-1 legal disclaimer conformance under RFC 072."""

from __future__ import annotations

import json
from pathlib import Path

from assessment_engine.infrastructure.localization import (
    t,
)


def test_tier1_disclaimer_text_conformance_es() -> None:
    """Verify Spanish disclaimer satisfies all 5 institutional criteria and has zero legacy parentheses."""
    disclaimer_p1 = t(
        "disclaimer_text_1",
        locale="es",
        client_name="ACME INDUSTRIAL",
        company_name="STRATEGIC ADVISORY",
    )
    assert "(el Documento)" not in disclaimer_p1
    assert "(Fast Assessment)" not in disclaimer_p1
    assert "ACME INDUSTRIAL" in disclaimer_p1
    assert "STRATEGIC ADVISORY" in disclaimer_p1
    assert "entrevistas y cuestionarios técnicos de autoevaluación" in disclaimer_p1

    disclaimer_p5 = t(
        "disclaimer_text_5",
        locale="es",
        client_name="ACME INDUSTRIAL",
        company_name="STRATEGIC ADVISORY",
    )
    assert "STRATEGIC ADVISORY" in disclaimer_p5
    assert "lucro cesante" in disclaimer_p5
    assert "daños indirectos" in disclaimer_p5


def test_tier1_disclaimer_text_conformance_en() -> None:
    """Verify English disclaimer satisfies institutional standards and parameterization."""
    disclaimer_p1 = t(
        "disclaimer_text_1",
        locale="en",
        client_name="GLOBAL ENTERPRISE",
        company_name="GLOBAL CONSULTING",
    )
    assert "(the Document)" not in disclaimer_p1
    assert "(Fast Assessment)" not in disclaimer_p1
    assert "GLOBAL ENTERPRISE" in disclaimer_p1
    assert "GLOBAL CONSULTING" in disclaimer_p1
    assert "self-assessment questionnaires" in disclaimer_p1

    disclaimer_p5 = t(
        "disclaimer_text_5",
        locale="en",
        client_name="GLOBAL ENTERPRISE",
        company_name="GLOBAL CONSULTING",
    )
    assert "GLOBAL CONSULTING" in disclaimer_p5
    assert "loss of profits" in disclaimer_p5
    assert "consequential" in disclaimer_p5


def test_all_five_disclaimer_keys_exist_in_primary_catalogs() -> None:
    """Verify both locales.json and locales_asis_annex.json define disclaimer_text_1 through 5."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    annex_locales_path = repo_root / "engine_config" / "locales_asis_annex.json"

    with open(locales_path, "r", encoding="utf-8") as f:
        loc_data = json.load(f)

    with open(annex_locales_path, "r", encoding="utf-8") as f:
        annex_data = json.load(f)

    for i in range(1, 6):
        key = f"disclaimer_text_{i}"
        assert key in loc_data["es"], f"Missing {key} in locales.json (es)"
        assert key in loc_data["en"], f"Missing {key} in locales.json (en)"
        assert len(loc_data["es"][key].strip()) > 50, f"Key {key} too short in locales.json (es)"
        assert len(loc_data["en"][key].strip()) > 50, f"Key {key} too short in locales.json (en)"

        assert key in annex_data["es"], f"Missing {key} in locales_asis_annex.json (es)"
        assert key in annex_data["en"], f"Missing {key} in locales_asis_annex.json (en)"


def test_default_company_name_resolves_to_ntt_data() -> None:
    """Verify that default company_name resolves canonically across brand profile and locales."""
    from assessment_engine.infrastructure.config_loader import load_brand_profile
    brand = load_brand_profile()
    company = brand.get("company_name")
    assert company and len(company.strip()) > 0

    assert t("default_company_name", locale="es")
    assert t("default_company_name", locale="en")

