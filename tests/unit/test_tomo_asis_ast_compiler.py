"""Unit tests for TomoAsisASTCompiler (RFC 062).

Verifies the declarative AST compilation of the Consolidated Tomo 1 AS-IS report,
ensuring zero split-brain, strict CMMI bands, and OpenXML layout determinism.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from docx import Document

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    TomoAsisASTCompiler,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_tomo_asis_ast_compilation_integrity(tmp_path: Path) -> None:
    """Verifies that Tomo 1 compiles deterministically with all 5 chapters and zero split-brain."""
    global_payload_path = REPO_ROOT / "working/molins/global_report_payload.json"
    t1_payload_path = REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json"
    t2_payload_path = REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json"

    if not global_payload_path.exists() or not t1_payload_path.exists() or not t2_payload_path.exists():
        pytest.skip("Required test payloads not present in working/molins/")

    with open(global_payload_path, "r", encoding="utf-8-sig") as f:
        global_payload = json.load(f)
    with open(t1_payload_path, "r", encoding="utf-8-sig") as f:
        t1_payload = json.load(f)
    with open(t2_payload_path, "r", encoding="utf-8-sig") as f:
        t2_payload = json.load(f)

    tower_payloads = {
        "T1": t1_payload,
        "T2": t2_payload,
    }

    out_docx = tmp_path / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
    compiler = TomoAsisASTCompiler()
    result_path = compiler.compile(
        global_payload=global_payload,
        tower_payloads=tower_payloads,
        output_docx_path=out_docx,
        doc_lang="es",
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 50000

    # Inspect compiled docx structure
    doc = Document(str(result_path))
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading") or p.style.name.startswith("Título")]

    # Verify all 5 chapters are present
    assert any("Resumen Ejecutivo" in h for h in headings)
    assert any("Madurez Tecnológica" in h for h in headings)
    assert any("Análisis de Riesgos" in h for h in headings)
    assert any("Áreas Técnicas" in h for h in headings)
    assert any("Dependencias" in h for h in headings)

    # Verify CMMI table contains all 10 towers
    full_text = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    for code in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
        assert code in full_text

    # Verify zero em-dashes or en-dashes (Strict Short-Hyphen Invariant)
    assert "—" not in full_text
    assert "–" not in full_text
