from __future__ import annotations

from assessment_engine.infrastructure.json_from_model import parse_json_from_text


def test_parse_clean_json_tier1() -> None:
    raw_text = '{"clave": "valor"}'
    result = parse_json_from_text(raw_text)
    assert result == {"clave": "valor"}
