"""Unit tests for the topological Mermaid Gantt chart generator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from assessment_engine.application.generate_mermaid_gantt import generate_mermaid_gantt


def test_generate_mermaid_gantt_with_mock_render(tmp_path: Path):
    """Verify that generate_mermaid_gantt compiles blueprint dependencies into Mermaid syntax and saves PNG."""
    fixture_path = Path("tests/test_data/blueprint_t2_payload.json")
    assert fixture_path.is_file(), "Fixture blueprint_t2_payload.json missing."

    out_png = tmp_path / "gantt.png"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    with patch("requests.get", return_value=mock_resp) as mock_get:
        success = generate_mermaid_gantt(str(fixture_path), str(out_png))
        assert success is True
        assert mock_get.called
        assert out_png.is_file()
        assert out_png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_generate_mermaid_gantt_empty_roadmap(tmp_path: Path):
    """Verify that empty roadmap returns False gracefully."""
    empty_json = tmp_path / "empty.json"
    empty_json.write_text("{}", encoding="utf-8")
    out_png = tmp_path / "gantt.png"

    assert generate_mermaid_gantt(str(empty_json), str(out_png)) is False
