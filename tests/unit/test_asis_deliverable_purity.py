"""Unit test verifying end-to-end AS-IS deliverable structural purity and Open FAIR compliance."""

from __future__ import annotations

import json
from pathlib import Path
from docx import Document
import pytest

from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast


def test_compiled_asis_document_purity(tmp_path: Path) -> None:
    # Use real Tower 1 payload fixture
    repo_root = Path(__file__).resolve().parents[2]
    payload_file = repo_root / "working/molins/T1/blueprint_t1_payload.json"
    if not payload_file.exists():
        pytest.skip("Blueprint payload fixture not found on disk.")

    out_docx = tmp_path / "test_tower_1_asis.docx"
    compile_asis_docx_via_ast(payload_file, out_docx, doc_lang="es")

    assert out_docx.exists(), "Compiled DOCX deliverable must exist."
    assert out_docx.stat().st_size > 50000, "DOCX file size indicates complete document."

    doc = Document(str(out_docx))

    paragraphs_text = "\n".join(p.text for p in doc.paragraphs)
    table_cells_text = "\n".join(
        " ".join(c.text.replace("\n", " ") for c in row.cells)
        for t in doc.tables
        for row in t.rows
    )
    full_text = paragraphs_text + "\n" + table_cells_text

    # Task 1: Cover Page Hygiene
    assert "Instalación: Perímetro de infraestructura" not in full_text
    assert "Proyecto: Diagnóstico de Arquitectura" not in full_text
    first_footer = doc.sections[0].first_page_footer
    footer_text = " ".join(p.text for p in first_footer.paragraphs)
    assert "STRATEGIC ADVISORY" in footer_text or "Confidencial" in footer_text

    # Task 2: Native Word SDT Table of Contents
    all_p_texts = [p.text for p in doc.element.xpath("//w:p")]
    assert any("Contenido" in t or "Índice" in t for t in all_p_texts)
    assert len(doc.element.xpath("//w:sdt")) >= 1

    # Task 3: Chapter 1 Forensic Purity
    assert "Para consultar la parametrización actuarial detallada" not in full_text
    assert "quiere alcanzar el Nivel 4" not in full_text

    # Task 4: Chapter 2 Streamlining
    assert "Metodología de calibración en tres fases" not in full_text

    # Task 5 & 6: Chapter 4 Mini-Infographic Cards & Realism
    assert "Hexágono de retorno" not in full_text
    assert "Palancas de Retorno de Resiliencia" not in full_text
    assert "Avería o fallo de componente electromecánico principal durante la operación continua" not in full_text
    assert "Desglose del Cálculo Actuarial" in full_text
    assert "Efecto Cascada" in full_text

    # Task 7: Chapter 5 Pure AS-IS Synthesis
    assert "Proyección Multi-Horizonte del Coste de Inacción" not in full_text
    assert "Matriz de Concentración de Vulnerabilidades" in full_text

    # Task 8: Single Technical Appendix
    assert "Registro de Custodia de Fuentes de Información" not in full_text
    assert "Apéndice A. Metodología Cuantitativa de Riesgos (Open FAIR™)" in full_text
    assert "Apéndice B. Glosario de Términos" in full_text
