from docx import Document

from assessment_engine.scripts.render_global_report_from_template import (
    load_payload,
    render_global_report,
)
from tests.artifact_helpers import ROOT, require_artifact_es

PAYLOAD_PATH = ROOT / "working" / "ivirma" / "global_report_payload.json"
TEMPLATE_PATH = (
    ROOT / "source_docs" / "templates" / "11. Template Documento General Alpha v.05.docx"
)


def test_render_global_report_from_real_payload(tmp_path):
    output_path = tmp_path / "global_report_test.docx"
    payload = load_payload(require_artifact_es(PAYLOAD_PATH))

    render_global_report(
        payload=payload,
        template_path=TEMPLATE_PATH,
        output_path=output_path,
        client_dir=PAYLOAD_PATH.parent,
    )

    assert output_path.exists()

    doc = Document(output_path)
    text_content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    assert "Informe Estratégico" in text_content
    assert "Resumen Ejecutivo" in text_content
