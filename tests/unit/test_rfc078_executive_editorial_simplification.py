"""Unit tests for RFC 078: Executive Editorial Simplification & Value Diagnosis Governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")


@pytest.fixture
def locales_catalog() -> Dict[str, Any]:
    """Loads the canonical locales catalog."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    with open(locales_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_rfc078_table_1_1_zero_developer_jargon(locales_catalog: Dict[str, Any]) -> None:
    """Verify that internal developer jargon (SSOT, Telemetría) is eradicated from Table 1.1 headers."""
    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog
        col_axis = locales_catalog[locale].get("tomo_polarity_col_axis", "")
        col_domain = locales_catalog[locale].get("tomo_polarity_col_domain", "")
        col_telemetry = locales_catalog[locale].get("tomo_polarity_col_telemetry", "")

        assert "ssot" not in col_domain.lower()
        assert "telemetría" not in col_telemetry.lower()
        assert "telemetry" not in col_telemetry.lower()
        assert "eje de polaridad" not in col_axis.lower()
        assert "polarity axis" not in col_axis.lower()


def test_rfc078_table_1_1_leader_row_omits_ale_distraction(locales_catalog: Dict[str, Any]) -> None:
    """Verify that maturity leader description focuses on control/redundancy and omits confusing {leader_ale}."""
    for locale in SUPPORTED_LOCALES:
        leader_desc = locales_catalog[locale].get("tomo_polarity_leader_desc", "")
        assert "{leader_score}" in leader_desc
        assert "{leader_ale}" not in leader_desc


def test_rfc078_table_1_1_risk_and_lagging_token_signatures(locales_catalog: Dict[str, Any]) -> None:
    """Verify that Risk row retains {top_risk_ale} and {top_risk_share_pct}, and Lagging retains {lagging_score}."""
    for locale in SUPPORTED_LOCALES:
        risk_desc = locales_catalog[locale].get("tomo_polarity_risk_desc", "")
        lagging_desc = locales_catalog[locale].get("tomo_polarity_lagging_desc", "")

        assert "{top_risk_ale}" in risk_desc
        assert "{top_risk_share_pct}" in risk_desc
        assert "{lagging_score}" in lagging_desc


def test_rfc078_document_headings_clean_and_simplified(locales_catalog: Dict[str, Any]) -> None:
    """Verify that all simplified headings across Volume 1 exist and are direct."""
    heading_keys = (
        "tomo_polarity_section_title",
        "tomo_ch1_challenges_title",
        "tomo_ch1_econ_title",
        "tomo_ch3_step1_heading",
        "tomo_sec32_heatmap_title",
        "tomo_ch3_p90_title",
        "tomo_ch4_spof_title",
        "tomo_ch5_title",
    )
    for locale in SUPPORTED_LOCALES:
        catalog = locales_catalog[locale]
        for k in heading_keys:
            assert k in catalog, f"Missing heading key '{k}' in locale '{locale}'"
            val = catalog[k]
            assert "radiografía de polaridad" not in val.lower()
            assert "cuantificación actuarial" not in val.lower()
