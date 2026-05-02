import asyncio
import json

import pytest
from pydantic import ValidationError

from assessment_engine.scripts import run_executive_annex_synthesizer


def test_synthesize_annex_fails_on_invalid_blueprint(monkeypatch, tmp_path):
    client_dir = tmp_path / "client"
    tower_dir = client_dir / "T5"
    tower_dir.mkdir(parents=True)

    blueprint_path = tower_dir / "blueprint_t5_payload.json"
    blueprint_path.write_text(
        json.dumps(
            {
                "document_meta": {
                    "tower_code": "T5",
                    "tower_name": "Resilience",
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        run_executive_annex_synthesizer,
        "resolve_client_dir",
        lambda _client_name: client_dir,
    )
    monkeypatch.setattr(
        run_executive_annex_synthesizer,
        "resolve_blueprint_payload_path",
        lambda _client_name, _tower_id: blueprint_path,
    )
    monkeypatch.setattr(
        run_executive_annex_synthesizer,
        "resolve_annex_template_payload_path",
        lambda _client_name, _tower_id: (
            tower_dir / "approved_annex_t5.template_payload.json"
        ),
    )
    monkeypatch.setattr(
        run_executive_annex_synthesizer,
        "resolve_client_intelligence_path",
        lambda _client_name: client_dir / "client_intelligence.json",
    )
    monkeypatch.setattr(
        run_executive_annex_synthesizer,
        "resolve_case_input_path",
        lambda _client_name, _tower_id: tower_dir / "case_input.json",
    )

    with pytest.raises(ValidationError):
        asyncio.run(run_executive_annex_synthesizer.synthesize_annex("client", "T5"))
