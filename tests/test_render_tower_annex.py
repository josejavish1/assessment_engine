from pathlib import Path
import zipfile

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


def test_render_tower_annex_semantic_mode_uses_word_styles(tmp_path):
    output_path = tmp_path / "annex_t5_semantic.docx"

    main(
        [
            "render_tower_annex_from_template",
            str(PAYLOAD_PATH),
            str(TEMPLATE_PATH),
            str(output_path),
            "--semantic-styles",
        ]
    )

    doc = Document(output_path)
    paragraphs = {p.text.strip(): p for p in doc.paragraphs if p.text.strip()}
    subtitle = next(
        p
        for p in doc.paragraphs
        if p.text.strip() and "Fast Infrastructure Assessment" in p.text
    )

    assert paragraphs["ANEXO T5 – Resilience & Continuity"].style.style_id == "Ttulo"
    assert subtitle.style.style_id == "Subttulo"
    assert paragraphs["Resumen ejecutivo de la torre"].style.style_id == "Ttulo1"
    assert paragraphs["Perfil de madurez por pilar"].style.style_id == "Ttulo1"
    assert not any(p.text.strip().startswith("• ") for p in doc.paragraphs if p.text.strip())

    with zipfile.ZipFile(output_path) as zf:
        document_xml = zf.read("word/document.xml").decode("utf-8", "ignore")
        settings_xml = zf.read("word/settings.xml").decode("utf-8", "ignore")

    assert 'TOC \\o "1-2" \\h \\z \\u' in document_xml
    assert "<w:numPr>" in document_xml
    assert "updateFields" in settings_xml
