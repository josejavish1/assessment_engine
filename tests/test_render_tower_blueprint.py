from pathlib import Path

from docx import Document

from assessment_engine.scripts.render_tower_blueprint import (
    load_annex_data,
    load_payload,
    render_blueprint,
)


ROOT = Path(__file__).resolve().parents[1]
CLIENT_DIR = ROOT / "working" / "ivirma"
PAYLOAD_PATH = CLIENT_DIR / "T5" / "blueprint_t5_payload.json"


def test_render_tower_blueprint_from_real_payload(tmp_path):
    output_path = tmp_path / "tower_blueprint_test.docx"
    annex_data = load_annex_data(CLIENT_DIR, "T5")
    payload = load_payload(PAYLOAD_PATH, annex_data=annex_data)

    render_blueprint(
        payload=payload,
        output_path=output_path,
        client_dir=CLIENT_DIR,
    )

    assert output_path.exists()

    doc = Document(output_path)
    text_content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    assert "Informe de Madurez Tecnológica" in text_content
    assert "Resumen ejecutivo" in text_content
    assert "Capacidad:" in text_content
