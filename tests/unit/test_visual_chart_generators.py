"""Unit tests for radar chart generators and section output validators."""

from __future__ import annotations

import json
from pathlib import Path

from assessment_engine.application.generate_global_radar_chart import main as main_global_radar
from assessment_engine.application.generate_tower_radar_chart import (
    generate_radar_chart_from_pillars,
)
from assessment_engine.application.validate_section_output import main as main_validate_section


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


def test_validate_section_output_pass_and_fail(tmp_path: Path, monkeypatch):
    """Verify that main_validate_section checks forbidden words in section outputs."""
    case_dir = tmp_path / "working" / "client" / "T5"
    case_dir.mkdir(parents=True, exist_ok=True)

    valid_payload = {"executive_narrative": "Infraestructura actual sin menciones prohibidas."}
    (case_dir / "approved_asis.generated.json").write_text(
        json.dumps(valid_payload), encoding="utf-8"
    )

    import assessment_engine.application.validate_section_output as vso
    monkeypatch.setattr(vso, "CASE_DIR", case_dir)

    # Valid run
    main_validate_section(["validate_section", "asis"])

    # Invalid run (forbidden keyword)
    invalid_payload = {"executive_narrative": "Este es el estado objetivo TO-BE proyectado."}
    (case_dir / "approved_asis.generated.json").write_text(
        json.dumps(invalid_payload), encoding="utf-8"
    )
    import pytest
    with pytest.raises(SystemExit) as exc_info:
        main_validate_section(["validate_section", "asis"])
    assert exc_info.value.code == 1
