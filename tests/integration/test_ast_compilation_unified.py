"""Integration test verifying unified declarative AST compilation (RFC-026 / Pattern #1)."""

from __future__ import annotations

import json
from pathlib import Path
from docx import Document
import pytest

from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast


@pytest.fixture
def sample_payload_file(tmp_path: Path) -> Path:
    """Fixture providing complete synthetic assessment payload."""
    payload = {
        "document_meta": {
            "tower_code": "T1",
            "tower_name": "Physical Data Center & Facilities",
            "client_name": "IBM Cloud & Global Financial Corp",
            "language": "en",
            "date": "October 2026",
            "version": "1.0",
        },
        "total_fair_ale": 1250000.0,
        "pillars_analysis": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Power & Electrical Continuity",
                "score": 2.5,
                "health_check_asis": [
                    {
                        "target_state": "Dual Bus Power Feed Redundancy",
                        "finding": "Substation bus transfer lacks automated failover orchestration.",
                        "business_risk": "Elevated risk of unscheduled power interruption across core compute racks.",
                        "threat_event_frequency": 3.0,
                        "loss_magnitude": 4.0,
                        "fair_ale_score": 450000.0,
                        "fair_p90_score": 950000.0,
                    }
                ],
            }
        ],
    }
    p_file = tmp_path / "blueprint_t1_payload.json"
    p_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p_file


@pytest.mark.parametrize("doc_lang", ["en", "es"])
def test_compile_asis_docx_via_ast(sample_payload_file: Path, tmp_path: Path, doc_lang: str) -> None:
    """Verify that compile_asis_docx_via_ast compiles DOCX directly via declarative AST across locales."""
    out_docx = tmp_path / f"Technical_Annex_T1_AST_{doc_lang}.docx"

    compiled_path = compile_asis_docx_via_ast(
        payload_path=sample_payload_file,
        output_docx_path=out_docx,
        doc_lang=doc_lang,
    )

    assert compiled_path.exists()
    assert compiled_path.stat().st_size > 5000

    doc = Document(str(compiled_path))
    assert len(doc.paragraphs) > 5
    assert len(doc.tables) >= 1

    # Verify that the table contains the pillar from AST
    table_texts = [
        " ".join(c.text for c in row.cells)
        for t in doc.tables
        for row in t.rows
    ]
    assert any("Power & Electrical Continuity" in t_txt for t_txt in table_texts)
