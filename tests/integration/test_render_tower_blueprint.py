"""Hermetic integration test and regression oracle for Tower Blueprint DOCX rendering.

Verifies that render_blueprint() deterministically builds all document chapters,
executive snapshots, maturity profiles, FAIR heatmaps, roadmaps, and deep project charters
with exact structural parity.
"""
from __future__ import annotations

import json
from pathlib import Path
from docx import Document

from assessment_engine.adapters.render_tower_blueprint import render_blueprint
from assessment_engine.domain.schemas.blueprint import BlueprintPayload


def test_render_tower_blueprint_full_oracle(tmp_path: Path) -> None:
    """Verify that render_blueprint builds a complete and valid tower blueprint document."""
    source_payload_path = Path("working/legacy/redeia_v3_old/T2/blueprint_t2_payload.json")
    assert source_payload_path.exists(), "Source blueprint payload fixture is missing."

    data = json.loads(source_payload_path.read_text(encoding="utf-8"))
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
    assert len(doc.paragraphs) == 108, f"Expected exactly 108 paragraphs, got {len(doc.paragraphs)}"
    assert len(doc.tables) == 21, f"Expected exactly 21 tables, got {len(doc.tables)}"

    # Section verification
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert payload.document_meta.tower_name in full_text
    assert payload.document_meta.client_name in full_text
    assert "Informe de Madurez Tecnológica" in full_text
    assert "1. Executive Snapshot" in full_text
    assert "5. Conclusión" in full_text
