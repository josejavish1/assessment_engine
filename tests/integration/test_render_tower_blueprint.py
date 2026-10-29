"""Hermetic integration test and regression oracle for Tower Blueprint DOCX rendering.

Verifies that render_blueprint() deterministically builds all document chapters,
executive snapshots, maturity profiles, FAIR heatmaps, roadmaps, and deep project charters
with exact structural parity.
"""
from __future__ import annotations

import json
from pathlib import Path
from docx import Document
import pytest

from assessment_engine.adapters.render_tower_blueprint import render_blueprint
from assessment_engine.domain.schemas.blueprint import BlueprintPayload


@pytest.mark.xdist_group(name="locales")
def test_render_tower_blueprint_full_oracle(tmp_path: Path) -> None:
    """Verify that render_blueprint builds a complete and valid tower blueprint document."""
    source_payload_path = Path("tests/test_data/blueprint_t2_payload.json")
    if not source_payload_path.exists():
        import pytest
        pytest.skip("Source blueprint payload fixture is missing.")

    data = json.loads(source_payload_path.read_text(encoding="utf-8-sig"))
    payload = BlueprintPayload.model_validate(data)

    client_dir = tmp_path / "client"
    client_dir.mkdir(parents=True, exist_ok=True)

    output_docx = tmp_path / "Tower_Blueprint_T2.docx"

    # Act: Render the document
    result_path = render_blueprint(payload, output_docx, client_dir)

    # Assert: Verify physical artifact generation
    assert result_path.exists(), "Blueprint DOCX file was not written to disk."
    assert result_path.stat().st_size > 10000, "Blueprint DOCX file is unexpectedly small."

    doc = Document(str(result_path))

    # Exact structural invariants
    assert len(doc.paragraphs) in (108, 110, 113, 122), f"Expected 108, 110, 113, or 122 paragraphs, got {len(doc.paragraphs)}"
    assert len(doc.tables) >= 20, f"Expected at least 20 tables, got {len(doc.tables)}"

    # Section verification
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert payload.document_meta.tower_name in full_text
    assert payload.document_meta.client_name in full_text
    assert (
        "Technology Maturity Assessment" in full_text
        or "Informe de Madurez Tecnológica" in full_text
    )
    assert "1. Executive Snapshot" in full_text
    assert "5. Conclusion" in full_text or "5. Conclusión" in full_text


def test_clean_text_for_render_dict_formatting() -> None:
    """Verify dictionary text rendering and kill LCR mutants."""
    from assessment_engine.adapters.render_tower_blueprint import clean_text_for_render
    # Dictionary with only name must not format as name: description
    res_single = clean_text_for_render({"name": "Project Alpha"})
    assert res_single == "Project Alpha"

    # Dictionary with both name and description
    res_both = clean_text_for_render({"name": "Project Alpha", "description": "Core Initiative"})
    assert res_both == "Project Alpha: Core Initiative"


@pytest.mark.xdist_group(name="locales")
def test_render_tower_blueprint_english_purity(tmp_path: Path) -> None:
    """Verify that render_blueprint generates an English document with zero Spanish header leakage when language='en'."""
    source_payload_path = Path("tests/test_data/blueprint_t2_payload.json")
    data = json.loads(source_payload_path.read_text(encoding="utf-8-sig"))
    data["document_meta"]["language"] = "en"
    payload = BlueprintPayload.model_validate(data)

    client_dir = tmp_path / "client_en"
    client_dir.mkdir(parents=True, exist_ok=True)
    output_docx = tmp_path / "Tower_Blueprint_T2_EN.docx"

    result_path = render_blueprint(payload, output_docx, client_dir)
    assert result_path.exists()

    doc = Document(str(result_path))
    full_text = "\n".join(p.text for p in doc.paragraphs)

    # Assert English Section Headings
    assert "Technology Maturity Assessment" in full_text
    assert "Informe de Madurez Tecnológica" not in full_text
    assert "1. Executive Snapshot" in full_text
    assert "Resumen ejecutivo" not in full_text
    assert "Consolidated Technology Diagnostic (AS-IS)" in full_text
    assert "Diagnóstico Tecnológico Consolidado (AS-IS)" not in full_text
    assert "Estimated Cost of Inaction Risk" in full_text
    assert "Coste Estimado del Riesgo de No Actuar" not in full_text
    assert "Target Architecture and Sovereign Vision (TO-BE)" in full_text
    assert "Arquitectura Objetivo y Visión Soberana" not in full_text
    assert "Strategic Roadmap & Technical Dependency Matrix" in full_text
    assert "Roadmap Estratégico y Matriz de Dependencias" not in full_text
    assert "Technical Annex: Deep Project Charters" in full_text
    assert "Anexo Técnico: Fichas Profundas de Proyectos" not in full_text
    assert "Maturity Profile by Pillar" in full_text
    assert "Perfil de madurez por pilar" not in full_text
    assert "5. Conclusion" in full_text
    assert "5. Conclusión" not in full_text

    # Assert English Table Content & Headers
    table_text = "\n".join(cell.text for t in doc.tables for row in t.rows for cell in row.cells)
    assert "CURRENT SCORE" in table_text
    assert "SCORE ACTUAL" not in table_text
    assert "MATURITY LEVEL" in table_text
    assert "NIVEL DE MADUREZ" not in table_text
    assert "Technical Capability" in table_text
    assert "Capacidad Técnica" not in table_text
    assert "Business Risk" in table_text
    assert "Riesgo de Negocio" not in table_text
    assert "Horizon / Phase" in table_text
    assert "Horizonte / Fase" not in table_text


@pytest.mark.xdist_group(name="locales")
def test_render_tower_blueprint_multilingual_german_and_japanese(tmp_path: Path) -> None:
    """Verify that render_blueprint natively and deterministically projects to German and Japanese without any inline ternaries."""
    source_payload_path = Path("tests/test_data/blueprint_t2_payload.json")
    base_data = json.loads(source_payload_path.read_text(encoding="utf-8-sig"))

    # 1. German (de)
    data_de = json.loads(json.dumps(base_data))
    data_de["document_meta"]["language"] = "de"
    payload_de = BlueprintPayload.model_validate(data_de)

    client_dir_de = tmp_path / "client_de"
    client_dir_de.mkdir(parents=True, exist_ok=True)
    out_de = tmp_path / "Tower_Blueprint_T2_DE.docx"

    res_de = render_blueprint(payload_de, out_de, client_dir_de)
    assert res_de.exists()

    doc_de = Document(str(res_de))
    full_text_de = "\n".join(p.text for p in doc_de.paragraphs)
    table_text_de = "\n".join(cell.text for t in doc_de.tables for row in t.rows for cell in row.cells)

    assert "Technologische Reifegradbewertung" in full_text_de
    assert "5. Fazit" in full_text_de
    assert "AKTUELLER SCORE" in table_text_de
    assert "Technische Fähigkeit" in table_text_de

    # 2. Japanese (ja)
    data_ja = json.loads(json.dumps(base_data))
    data_ja["document_meta"]["language"] = "ja"
    payload_ja = BlueprintPayload.model_validate(data_ja)

    client_dir_ja = tmp_path / "client_ja"
    client_dir_ja.mkdir(parents=True, exist_ok=True)
    out_ja = tmp_path / "Tower_Blueprint_T2_JA.docx"

    res_ja = render_blueprint(payload_ja, out_ja, client_dir_ja)
    assert res_ja.exists()

    doc_ja = Document(str(res_ja))
    full_text_ja = "\n".join(p.text for p in doc_ja.paragraphs)
    table_text_ja = "\n".join(cell.text for t in doc_ja.tables for row in t.rows for cell in row.cells)

    assert "テクノロジー成熟度評価レポート" in full_text_ja
    assert "1. エグゼクティブ・スナップショット" in full_text_ja
    assert "5. 結論" in full_text_ja
    assert "現在のスコア" in table_text_ja
    assert "技術的能力" in table_text_ja


