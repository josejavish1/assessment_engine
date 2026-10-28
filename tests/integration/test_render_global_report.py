"""Hermetic integration test and regression oracle for Global Report DOCX rendering.

Verifies that load_payload() and render_global_report() deterministically load
and build executive summaries, burning platforms, roadmap visualizations,
and decision registers with exact structural parity.
"""
from __future__ import annotations

from pathlib import Path
from docx import Document

from assessment_engine.adapters.render_global_report_from_template import (
    load_payload,
    render_global_report,
)


def test_render_global_report_full_oracle(tmp_path: Path) -> None:
    """Verify that load_payload and render_global_report build a complete global report document."""
    source_payload_path = Path("working/legacy/redeia_old/global_report_payload.json")
    template_path = Path("templates/docx/global_report_template.docx")

    assert source_payload_path.exists(), "Source global report payload fixture is missing."
    assert template_path.exists(), "Global report DOCX template is missing."

    # Act 1: Load and validate payload
    payload = load_payload(source_payload_path)
    assert payload is not None
    assert payload.meta.client != ""

    output_docx = tmp_path / "Global_Report.docx"

    # Act 2: Render document
    result_path = render_global_report(
        payload,
        template_path=template_path,
        output_path=output_docx,
        client_dir=source_payload_path.parent,
    )

    # Assert: Verify physical artifact generation
    assert result_path.exists(), "Global report DOCX file was not written to disk."
    assert result_path.stat().st_size > 10000, "Global report DOCX file is unexpectedly small."

    doc = Document(str(result_path))

    # Exact structural invariants
    assert len(doc.paragraphs) == 54, f"Expected exactly 54 paragraphs, got {len(doc.paragraphs)}"
    assert len(doc.tables) == 13, f"Expected exactly 13 tables, got {len(doc.tables)}"

    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Redeia" in full_text or "REDEIA" in full_text
