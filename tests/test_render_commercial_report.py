import json

import pytest
from docx import Document
from pydantic import ValidationError

from assessment_engine.scripts.render_commercial_report import (
    load_payload,
    render_commercial_report,
)
from tests.artifact_helpers import ROOT, require_artifact_es

PAYLOAD_PATH = ROOT / "working" / "ivirma" / "commercial_report_payload.json"
TEMPLATE_PATH = (
    ROOT / "source_docs" / "templates" / "11. Template Documento General Alpha v.05.docx"
)


def test_render_commercial_report_from_real_payload(tmp_path):
    output_path = tmp_path / "commercial_report_test.docx"
    payload = load_payload(require_artifact_es(PAYLOAD_PATH))

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


def test_load_payload_fails_on_invalid_commercial_contract(tmp_path):
    payload_path = tmp_path / "invalid_commercial.json"
    payload_path.write_text(
        json.dumps(
            {
                "meta": {"client": "test", "date": "2026-05-01", "version": "v1"},
                "commercial_summary": {
                    "deal_flash": {
                        "purchase_driver": "Expansion",
                        "ntt_win_theme": "Resilience",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_payload(payload_path)
