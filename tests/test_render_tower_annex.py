from pathlib import Path

from docx import Document

from assessment_engine.scripts.render_tower_annex_from_template import main


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = (
    ROOT / "working" / "ivirma" / "T5" / "approved_annex_t5.template_payload.json"
)
TEMPLATE_PATH = (
    ROOT / "templates" / "Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx"
)


def test_render_tower_annex_from_real_payload(tmp_path):
    output_path = tmp_path / "annex_t5_test.docx"

    main(
        [
            "render_tower_annex_from_template",
            str(PAYLOAD_PATH),
            str(TEMPLATE_PATH),
            str(output_path),
        ]
    )

    assert output_path.exists()

    doc = Document(output_path)
    text_content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    assert "ANEXO T5" in text_content
    assert "Resumen ejecutivo de la torre" in text_content
