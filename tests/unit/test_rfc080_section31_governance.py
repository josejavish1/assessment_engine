"""Unit tests for Section 3.1 Governance: CMMI score column in financial table and clean narrative."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
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


def test_rfc080_section31_bridge_and_footnote_clean(locales_catalog: Dict[str, Any]) -> None:
    """Verify that section 3.1 bridge and footnote are free of arbitrary numbers ('29'), 'tabla 4', and colloquialisms."""
    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog
        bridge = locales_catalog[locale].get("tomo_ch3_sec31_reconciliation_bridge", "")
        col_cmmi = locales_catalog[locale].get("tomo_ch3_table_col_cmmi", "")
        footnote = locales_catalog[locale].get("tomo_ch3_table4_footnote", "")

        assert len(bridge) > 20
        assert "29" not in bridge
        assert "tabla 4" not in bridge.lower()
        assert "table 4" not in bridge.lower()

        assert len(col_cmmi) > 0

        assert len(footnote) > 20
        assert "el mismo día" not in footnote.lower()
        assert "same day" not in footnote.lower()


def test_rfc080_table31_ast_contains_cmmi_scores() -> None:
    """Verify that the financial table in Section 3.1 renders CMMI maturity in Column 2."""
    compiler = Volume1AsisASTCompiler()
    global_payload = {
        "heatmap": [
            {"score": 3.30, "id": "T4", "tower_code": "T4", "tower_name": "Storage"},
            {"score": 2.14, "id": "T5", "tower_code": "T5", "tower_name": "Resiliency"},
        ],
        "financial_telemetry": {"domain_weights": {"T4": 42000.0, "T5": 206194.0}},
        "meta": {"client": "GLOBAL ENTERPRISE", "date": "2026-11-05"},
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
    assert len(tables) >= 1
    table31 = tables[0]

    # Verify header of Column 2 is Madurez CMMI
    headers = [c.text for c in table31.rows[0].cells]
    assert "Madurez CMMI" in headers[1]

    # Verify data rows have scores (e.g. 3,30 or 2,14) in Column 2
    for row in table31.rows[1:-1]:
        score_cell = row.cells[1].text.strip()
        assert len(score_cell) > 0
        # Score must be a formatted decimal like '3,30' or '2,14'
        assert "," in score_cell or "." in score_cell
