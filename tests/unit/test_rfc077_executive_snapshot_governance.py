"""Unit tests for RFC 077: Executive Single-Page Portfolio Snapshot & Polarity Governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")


@pytest.fixture
def locales_catalog() -> Dict[str, Any]:
    """Loads the canonical locales catalog."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    with open(locales_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_rfc077_locales_symmetry_and_zero_hardcoding(locales_catalog: Dict[str, Any]) -> None:
    """Verify that RFC 077 polarity keys exist symmetrically across all 6 locales without hardcoded strings."""
    required_keys = (
        "tomo_ch1_p1",
        "tomo_polarity_section_title",
        "tomo_polarity_col_axis",
        "tomo_polarity_col_domain",
        "tomo_polarity_col_telemetry",
        "tomo_polarity_leader_axis",
        "tomo_polarity_leader_domain",
        "tomo_polarity_leader_desc",
        "tomo_polarity_risk_axis",
        "tomo_polarity_risk_domain",
        "tomo_polarity_risk_desc",
        "tomo_polarity_lagging_axis",
        "tomo_polarity_lagging_domain",
        "tomo_polarity_lagging_desc",
        "tomo_ch1_challenges_title",
        "tomo_ch1_econ_title",
    )

    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog, f"Missing locale '{locale}'"
        catalog = locales_catalog[locale]
        for key in required_keys:
            assert key in catalog, f"Missing key '{key}' in locale '{locale}'"
            assert len(catalog[key].strip()) > 0, f"Empty key '{key}' in locale '{locale}'"

        # Assert p1 is parameterized and has zero hardcoding of CMMI Level 2 or 10 domains
        p1 = catalog["tomo_ch1_p1"]
        assert "{client}" in p1
        assert "{domain_count}" in p1
        assert "{score}" in p1
        assert "{cmmi_label}" in p1
        assert "diez dominios" not in p1.lower()
        assert "ten domains" not in p1.lower()
        assert "nivel 2" not in p1.lower()
        assert "level 2" not in p1.lower()


def test_rfc077_dynamic_portfolio_polarity_algorithm() -> None:
    """Verify mathematical polarity calculation across N-domain topology with tie-breakers."""
    compiler = Volume1AsisASTCompiler()

    # Domain topology: (code, name, score, _, _)
    topology = [
        ("T1", "Physical Facilities", 2.61, "", ""),
        ("T2", "Hybrid Compute", 2.46, "", ""),
        ("T3", "Networks & WAN", 2.52, "", ""),
        ("T4", "Storage & Backup", 3.30, "", ""),      # Expected Leader (score=3.30)
        ("T5", "Operational Resiliency", 2.14, "", ""), # Expected Lagging (score=2.14) & Top Risk (ALE=206,194)
        ("T6", "Cybersecurity", 2.80, "", ""),
        ("T7", "Databases & ITSM", 2.60, "", ""),
        ("T8", "Core Business Apps", 2.42, "", ""),
        ("T9", "Digital Workplace", 3.14, "", ""),
        ("T10", "Site Operations", 2.38, "", ""),
    ]

    reconciled_allocations = {
        "T1": 118500,
        "T2": 95400,
        "T3": 82500,
        "T4": 42000,
        "T5": 206194,  # Peak ALE
        "T6": 125000,
        "T7": 75000,
        "T8": 68000,
        "T9": 35000,
        "T10": 68822,
    }

    polarity = compiler._compute_portfolio_polarity_extremes(
        domain_topology=topology,
        reconciled_allocations=reconciled_allocations,
        currency="€",
        doc_lang="es",
    )

    assert polarity.domain_count == 10
    assert polarity.leader.code == "T4"
    assert "3,30" in polarity.leader.score_formatted

    assert polarity.top_risk.code == "T5"
    assert "206.194" in polarity.top_risk.ale_formatted
    assert float(polarity.top_risk.ale_share_pct.replace(",", ".")) == pytest.approx(22.5, abs=0.5)

    assert polarity.lagging.code == "T5"
    assert "2,14" in polarity.lagging.score_formatted


def test_rfc077_chapter_1_ast_structure_and_eradicated_redundant_triad() -> None:
    """Verify that Chapter 1 builds exactly 4 non-redundant blocks and terminates with a page break."""
    from assessment_engine.domain.schemas.ast import PageBreakNode, TableNode

    compiler = Volume1AsisASTCompiler()
    global_payload = {
        "heatmap": [
            {"score": 3.30, "id": "T4", "tower_code": "T4", "tower_name": "Storage"},
            {"score": 2.14, "id": "T5", "tower_code": "T5", "tower_name": "Resiliency"},
        ],
        "burning_platform": [
            {"theme": "Operational Continuity", "business_risk": "Local plant vulnerabilities."},
        ],
        "financial_telemetry": {"domain_weights": {"T4": 42000.0, "T5": 206194.0}},
        "meta": {"client": "GLOBAL ENTERPRISE", "date": "2026-11-05"},
    }

    nodes: list = []
    compiler._build_chapter_1_executive_summary(
        nodes=nodes,
        global_payload=global_payload,
        tower_payloads={},
        client_name="GLOBAL ENTERPRISE",
        currency="€",
        doc_lang="es",
    )

    # 1. Exactly 2 tables in Chapter 1: Cockpit Table and Polarity Extremes Table
    tables = [n for n in nodes if isinstance(n, TableNode)]
    assert len(tables) == 2, f"Expected exactly 2 tables (Cockpit + Polarity), got {len(tables)}"

    # 2. Check that the second table is the Polarity Table (3 data rows + 1 header = 4 rows)
    polarity_table = tables[1]
    assert len(polarity_table.rows) == 4
    header_cells = [c.text for c in polarity_table.rows[0].cells]
    assert "Indicador Clave" in header_cells[0]

    # 3. Last node must be PageBreakNode to strictly lock Chapter 1 onto Page 3
    assert isinstance(nodes[-1], PageBreakNode)
