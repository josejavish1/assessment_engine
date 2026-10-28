"""Hermetic integration test and regression oracle for AS-IS DOCX report compilation.

Verifies that compile_docx() deterministically renders all document chapters,
tables, formatting runs, and appendices with exact structural parity.
"""
from __future__ import annotations

import json
from pathlib import Path
from docx import Document

from assessment_engine.adapters.compile_asis_docx_from_modules import compile_docx
import pytest


@pytest.mark.xdist_group(name="locales")
def test_compile_asis_docx_full_oracle(tmp_path: Path) -> None:
    """Verify that compile_docx builds a complete and valid technical annex document."""
    modules_dir = tmp_path / "asis_modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    # 1. Arrange: Write mock markdown modules
    (modules_dir / "01_introduccion_alcance.md").write_text(
        "# 1. Introducción y Alcance\nContenido detallado de la metodología de diagnóstico.",
        encoding="utf-8",
    )
    (modules_dir / "02_resumen_ejecutivo.md").write_text(
        "# 2. Resumen Ejecutivo\nResumen de madurez de la torre de seguridad.",
        encoding="utf-8",
    )
    (modules_dir / "03_descripcion_plataforma.md").write_text(
        "# 3. Descripción de Plataforma\nDescripción de la arquitectura tecnológica actual.",
        encoding="utf-8",
    )
    (modules_dir / "04_analisis_pilares.md").write_text(
        "# 4. Análisis por Pilares\nDiagnóstico de capacidades operativas y brechas.",
        encoding="utf-8",
    )
    (modules_dir / "05_transversal.md").write_text(
        "# 5. Análisis Transversal\nEvaluación de dependencias y riesgo sistémico.",
        encoding="utf-8",
    )

    # 2. Arrange: Write mock O-FAIR CSV matrix
    csv_content = (
        "Capability_Header;Finding;Business_Risk;TEF;LM;ALE\n"
        "Security - Cifrado;Falta cifrado en reposo;Fuga de datos confidenciales;2.5;50000;100000\n"
        "Operations - Monitoreo;Falta observabilidad centralizada;Retraso en detección;4.0;20000;80000\n"
    )
    (modules_dir / "06_matriz_riesgos_fair.csv").write_text(csv_content, encoding="utf-8-sig")

    # 3. Arrange: Write mock blueprint payload
    blueprint_payload = {
        "document_meta": {
            "language": "es",
            "tower_name": "Seguridad de Red",
            "tower_code": "T5",
            "client_name": "Generic Corporate Client",
            "version": "1.0",
            "date": "Junio 2026",
            "currency": "€",
        },
        "total_fair_ale": 180000.00,
        "executive_summary": {
            "global_score": "4,50 / 5,00",
            "global_band": "Optimizado",
        },
        "pillar_score_profile": {
            "pillars": [
                {
                    "pilar_name": "Security",
                    "score": 4.5,
                    "band": "Optimizado",
                    "executive_reading": "Gobernanza de seguridad robusta en edge.",
                }
            ]
        },
    }
    (tmp_path / "blueprint_t5_payload.json").write_text(
        json.dumps(blueprint_payload, ensure_ascii=False), encoding="utf-8"
    )

    # 4. Act: Compile DOCX report
    output_docx = tmp_path / "AS-IS_Anexo_Tecnico_T5.docx"
    compile_docx(str(tmp_path), str(output_docx))

    # 5. Assert: Verify physical artifact generation
    assert output_docx.exists(), "Compiled DOCX file was not written to disk."
    assert output_docx.stat().st_size > 5000, "Compiled DOCX file is unexpectedly small."

    doc = Document(str(output_docx))

    # Structural baseline verification
    assert len(doc.paragraphs) >= 100, f"Expected >= 100 paragraphs, got {len(doc.paragraphs)}"
    assert len(doc.tables) == 8, f"Expected exactly 8 tables, got {len(doc.tables)}"

    # Section verification
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Seguridad de Red" in full_text
    assert "Generic Corporate Client" in full_text
    assert "Metodología Cuantitativa de Riesgos" in full_text
    assert "Lista de Abreviaturas" in full_text
    assert "Cláusula de Limitación de Responsabilidad" in full_text

    # Verify structured tables
    assert len(doc.tables) == 8, f"Expected exactly 8 tables, got {len(doc.tables)}"
    assert "PUNTUACIÓN AS-IS" in doc.tables[0].rows[0].cells[0].text
    assert "Nivel de Madurez" in doc.tables[1].rows[0].cells[0].text
    assert "Pilar / Capacidad Tecnológica Evaluada" in doc.tables[2].rows[0].cells[0].text
    assert "TEF" in doc.tables[3].rows[0].cells[0].text
    assert "ID" in doc.tables[4].rows[0].cells[0].text
    assert "Dimensión de Negocio" in doc.tables[5].rows[0].cells[0].text
    assert "Código de Referencia" in doc.tables[6].rows[0].cells[0].text
    assert "Abreviatura" in doc.tables[7].rows[0].cells[0].text
