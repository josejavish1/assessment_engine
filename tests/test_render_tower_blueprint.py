import json

from docx import Document

from assessment_engine.scripts.render_tower_blueprint import (
    load_annex_data,
    load_client_intelligence,
    load_payload,
    render_blueprint,
)
from tests.artifact_helpers import ROOT, require_artifact_es

CLIENT_DIR = ROOT / "working" / "ivirma"
PAYLOAD_PATH = CLIENT_DIR / "T5" / "blueprint_t5_payload.json"


def test_render_tower_blueprint_from_real_payload(tmp_path):
    output_path = tmp_path / "tower_blueprint_test.docx"
    annex_data = load_annex_data(CLIENT_DIR, "T5")
    payload = load_payload(require_artifact_es(PAYLOAD_PATH), annex_data=annex_data)

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


def test_render_tower_blueprint_uses_payload_adjacent_artifacts(tmp_path):
    client_dir = tmp_path / "exported-client"
    tower_dir = client_dir / "T5"
    tower_dir.mkdir(parents=True)

    (client_dir / "client_intelligence.json").write_text(
        json.dumps({"financial_tier": "Tier X"}),
        encoding="utf-8",
    )
    (tower_dir / "approved_annex_t5.template_payload.json").write_text(
        json.dumps({"executive_summary": {"headline": "Adjunto"}}),
        encoding="utf-8",
    )

    assert load_client_intelligence(client_dir)["financial_tier"] == "Tier X"
    assert load_annex_data(client_dir, "T5")["executive_summary"]["headline"] == "Adjunto"
