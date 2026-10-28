"""Unit test for rendering tower annex from template."""

from __future__ import annotations

from pathlib import Path
from docx import Document

from assessment_engine.adapters.render_tower_annex_from_template import main


def test_render_tower_annex_from_template_execution(tmp_path: Path):
    """Verify that main() renders a tower annex DOCX document from payload and template."""
    payload_path = Path("tests/test_data/approved_annex_t2.template_payload.json")
    template_path = Path("templates/docx/tower_annex_template.docx")
    output_docx = tmp_path / "Annex_T2_rendered.docx"

    assert payload_path.exists(), "Payload fixture missing."
    assert template_path.exists(), "Template DOCX missing."

    main(["render_tower_annex", str(payload_path), str(template_path), str(output_docx)])

    assert output_docx.exists(), "Output DOCX was not generated."
    assert output_docx.stat().st_size > 5000, "Output DOCX is unexpectedly small."

    doc = Document(str(output_docx))
    assert len(doc.paragraphs) > 10, "Rendered document should contain paragraphs."
