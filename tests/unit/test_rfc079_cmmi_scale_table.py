"""Unit tests for RFC 079: CMMI Analytical Maturity Scale Table & Page 5 Balance Governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)
from assessment_engine.domain.schemas.ast import HeadingNode, PageBreakNode, TableNode

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")


@pytest.fixture
def locales_catalog() -> Dict[str, Any]:
    """Loads the canonical locales catalog."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    with open(locales_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_rfc079_cmmi_scale_locales_symmetry(locales_catalog: Dict[str, Any]) -> None:
    """Verify that all Section 2.2 scale keys exist symmetrically across all 6 locales without hardcoded terms."""
    required_keys = [
        "tomo_ch2_sec2_title",
        "tomo_ch2_sec2_intro",
        "tomo_ch2_scale_col_level",
        "tomo_ch2_scale_col_range",
        "tomo_ch2_scale_col_criteria",
    ]
    for i in range(1, 6):
        required_keys.append(f"tomo_ch2_scale_lvl{i}_name")
        required_keys.append(f"tomo_ch2_scale_lvl{i}_desc")

    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog, f"Missing locale '{locale}'"
        catalog = locales_catalog[locale]
        for key in required_keys:
            assert key in catalog, f"Missing key '{key}' in locale '{locale}'"
            val = catalog[key].strip()
            assert len(val) > 0, f"Empty key '{key}' in locale '{locale}'"
            assert "molins" not in val.lower()
            assert "secil" not in val.lower()


def test_rfc079_cmmi_scale_ast_structure(tmp_path: Path) -> None:
    """Verify that Chapter 2 emits Section 2.2 with a 5-row table and terminates with a page break."""
    compiler = Volume1AsisASTCompiler()
    global_payload = {
        "heatmap": [
            {"score": 2.50, "id": "T1", "tower_code": "T1", "tower_name": "Facilities"},
        ],
        "meta": {"client": "GLOBAL ENTERPRISE", "date": "2026-11-05"},
    }

    dummy_docx = tmp_path / "dummy.docx"
    nodes: list = []
    compiler._build_chapter_2_maturity_radiography(
        nodes=nodes,
        global_payload=global_payload,
        output_docx_path=dummy_docx,
        doc_lang="es",
        tower_payloads={},
    )

    # 1. Section 2.2 Heading exists
    headings = [n for n in nodes if isinstance(n, HeadingNode) and n.level == 2]
    sec22_headings = [h for h in headings if "2.2" in h.text or "Escala Analítica" in h.text]
    assert len(sec22_headings) == 1, f"Expected Section 2.2 Heading, found: {[h.text for h in headings]}"

    # 2. Section 2.2 Table exists (5 rows + 1 header = 6 rows)
    tables = [n for n in nodes if isinstance(n, TableNode)]
    assert len(tables) >= 2, f"Expected at least 2 tables in Chapter 2, found {len(tables)}"
    scale_table = tables[-1]
    assert len(scale_table.rows) == 6, f"Expected 6 rows in scale table, got {len(scale_table.rows)}"

    # 3. Chapter terminates with PageBreakNode
    assert isinstance(nodes[-1], PageBreakNode)
