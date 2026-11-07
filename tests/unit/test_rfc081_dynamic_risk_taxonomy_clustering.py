"""Unit tests for RFC 081: Section 3.2 Dynamic Risk Taxonomy Clustering & Heatmap Legend Governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)
from assessment_engine.domain.actuarial_taxonomy_clusterer import (
    CANONICAL_TAXONOMY_KEYS,
    ActuarialTaxonomyClusterer,
)
from assessment_engine.domain.schemas.ast import TableNode

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")


@pytest.fixture
def locales_catalog() -> Dict[str, Any]:
    """Loads the canonical locales catalog."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    with open(locales_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_rfc081_taxonomy_locales_symmetry(locales_catalog: Dict[str, Any]) -> None:
    """Verify that all taxonomy families and legend table keys exist symmetrically across all 6 locales."""
    required_keys = [
        "sec_3_2_taxonomy_table_title",
        "sec_3_2_taxonomy_bridge_narrative",
        "sec_3_2_col_taxonomy_family",
        "sec_3_2_col_matrix_codes",
        "sec_3_2_col_systemic_threat_rationale",
        "sec_3_2_col_forensic_breakdown",
        "sec_3_2_col_clustered_ale",
        "sec_3_2_findings_badge_template",
        "sec_3_2_row_total_reconciled",
        "sec_3_2_row_total_rationale",
    ]
    for key in CANONICAL_TAXONOMY_KEYS:
        required_keys.append(f"{key}_TITLE")
        required_keys.append(f"{key}_RATIONALE")

    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog, f"Missing locale '{locale}'"
        catalog = locales_catalog[locale]
        for k in required_keys:
            assert k in catalog, f"Missing key '{k}' in locale '{locale}'"
            val = catalog[k].strip()
            assert len(val) > 0, f"Empty key '{k}' in locale '{locale}'"
            assert "molins" not in val.lower()


def test_rfc081_clusterer_prunes_empty_families() -> None:
    """Verify that ActuarialTaxonomyClusterer only returns non-empty families (Zero-Hardcoding Law)."""
    # 2 risks in Cybersecurity, 1 in Operational Continuity
    risk_vectors = [
        {"id": "T06.R01", "risk_name": "Privilege escalation and PAM gap", "ale": 125000.0},
        {"id": "T06.R02", "risk_name": "CVE vulnerability exposure", "ale": 35000.0},
        {"id": "T05.R01", "risk_name": "Industrial plant outage and lack of DRP", "ale": 206194.0},
    ]

    clusters = ActuarialTaxonomyClusterer.build_dynamic_clusters(risk_vectors=risk_vectors)

    # Must only emit the 2 active families, NOT all 6
    assert len(clusters) == 2
    active_ids = {c.taxonomy_id for c in clusters}
    assert "TAXONOMY_CYBER_IDENTITY_GOVERNANCE" in active_ids
    assert "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE" in active_ids
    assert "TAXONOMY_STRUCTURAL_OBSOLESCENCE" not in active_ids

    # Sorted descending by ALE: T05 (206k) must precede T06 (160k)
    assert clusters[0].taxonomy_id == "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE"
    assert clusters[0].cluster_ale == pytest.approx(206194.0, abs=1.0)
    assert clusters[1].taxonomy_id == "TAXONOMY_CYBER_IDENTITY_GOVERNANCE"
    assert clusters[1].cluster_ale == pytest.approx(160000.0, abs=1.0)


def test_rfc081_ast_compiler_renders_taxonomy_legend_table() -> None:
    """Verify that Chapter 3 renders the dynamic taxonomy legend table directly beneath the 5x5 heatmap."""
    compiler = Volume1AsisASTCompiler()
    global_payload = {
        "corporate_heatmap_risks": [
            {"id": "T05.R01", "risk_name": "Plant outage without BCP", "tef": 2.0, "lm": 4.0, "ale": 206194.0},
            {"id": "T02.R01", "risk_name": "EoL hardware and memory saturation", "tef": 3.0, "lm": 3.0, "ale": 100806.0},
        ],
        "financial_telemetry": {"domain_weights": {"T5": 206194.0, "T2": 100806.0}},
        "meta": {"client": "GLOBAL BANK", "date": "2026-11-05"},
    }

    nodes: list = []
    compiler._build_chapter_3_actuarial_risk_register(
        nodes=nodes,
        global_payload=global_payload,
        tower_payloads={},
        currency="€",
        doc_lang="es",
    )

    tables = [n for n in nodes if isinstance(n, TableNode)]
    # Table 0 is Table 3.1, Table 1 is 3-Tier, Table 2 is 5x5 Heatmap, Table 3 is Taxonomy Legend Table
    assert len(tables) >= 4, f"Expected at least 4 tables in Chapter 3, found {len(tables)}"

    legend_tables = [
        t for t in tables
        if any("Familia Taxonómica" in c.text or "Taxonomy Family" in c.text for c in t.rows[0].cells)
    ]
    assert len(legend_tables) == 1, f"Expected 1 taxonomy legend table, found {len(legend_tables)}"
    legend_table = legend_tables[0]
    headers = [c.text for c in legend_table.rows[0].cells]
    assert "Familia Taxonómica" in headers[0] or "Taxonomy Family" in headers[0]
    assert "Códigos" in headers[1] or "Codes" in headers[1]

    # Footer row must be the reconciled total
    footer_cells = [c.text for c in legend_table.rows[-1].cells]
    assert "TOTAL" in footer_cells[0]
    assert "N = 2" in footer_cells[1]
    assert "100.0%" in footer_cells[4] or "100,0%" in footer_cells[4]
