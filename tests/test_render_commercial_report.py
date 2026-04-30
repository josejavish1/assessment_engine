from pathlib import Path

from docx import Document
import pytest

from assessment_engine.scripts.render_commercial_report import (
    load_payload,
    render_commercial_report,
)


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "working" / "ivirma" / "commercial_report_payload.json"
TEMPLATE_PATH = (
    ROOT / "source_docs" / "templates" / "11. Template Documento General Alpha v.05.docx"
)


def test_render_commercial_report_from_real_payload(tmp_path):
    if not PAYLOAD_PATH.exists():
        pytest.skip(f"No se encontró el artefacto: {PAYLOAD_PATH}")

    output_path = tmp_path / "commercial_report_test.docx"
    payload = load_payload(PAYLOAD_PATH)

    render_commercial_report(
        payload=payload,
        template_path=TEMPLATE_PATH,
        output_path=output_path,
    )

    assert output_path.exists()

    doc = Document(output_path)
    text_content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    assert "Account Action Plan" in text_content
    assert "Executive Summary & Deal Snapshot" in text_content
