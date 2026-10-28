"""Unit tests for radar chart generators."""

from __future__ import annotations

from pathlib import Path

from assessment_engine.application.generate_global_radar_chart import main as main_global_radar
from assessment_engine.application.generate_tower_radar_chart import (
    generate_radar_chart_from_pillars,
)


def test_generate_tower_radar_chart_execution(tmp_path: Path):
    """Verify that generate_radar_chart_from_pillars builds a valid PNG radar chart."""
    pillars = [
        {"pillar_label": "Arquitectura", "score_display": "3.5"},
        {"pillar_label": "Operaciones", "score_display": "4.0"},
        {"pillar_label": "Seguridad", "score_display": "2.8"},
    ]
    out_png = tmp_path / "tower_radar.png"
    result = generate_radar_chart_from_pillars(pillars, out_png)

    assert result.is_file(), "El archivo PNG de radar de torre debe existir físicamente."
    # Validación de cabecera binaria canónica PNG (RFC 2083)
    header = result.read_bytes()[:8]
    assert header == b"\x89PNG\r\n\x1a\n", "La cabecera binaria del archivo debe ser PNG válida."


def test_generate_global_radar_chart_execution(tmp_path: Path):
    """Verify that main_global_radar builds a global radar chart from global payload fixture."""
    payload_fixture = Path("tests/test_data/global_report_payload.json")
    assert payload_fixture.exists()

    out_png = tmp_path / "global_radar.png"
    main_global_radar(["global_radar", str(payload_fixture), str(out_png)])

    assert out_png.is_file(), "El archivo PNG de radar global debe existir físicamente."
    header = out_png.read_bytes()[:8]
    assert header == b"\x89PNG\r\n\x1a\n", "La cabecera binaria del archivo debe ser PNG válida."

