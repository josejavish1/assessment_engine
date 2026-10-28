"""Unit tests for the executive roadmap timeline image generator."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.application.generate_executive_roadmap_image import main


def test_generate_executive_roadmap_image_full_render(tmp_path: Path):
    """Verify that main renders a valid PNG Gantt timeline image from execution_roadmap."""
    payload_data = {
        "execution_roadmap": {
            "horizons": {
                "quick_wins_0_3_months": [
                    {
                        "title": "Despliegue de Observabilidad",
                        "program": "Resiliencia Operativa",
                        "start_month": 1,
                        "duration_months": 3,
                    }
                ],
                "year_1_3_12_months": [
                    {
                        "title": "Migración a Contenedores",
                        "program": "Modernización",
                        "start_month": 3,
                        "duration_months": 8,
                    }
                ],
                "year_2_12_24_months": [],
                "year_3_24_36_months": [],
            }
        }
    }

    payload_file = tmp_path / "global_payload.json"
    payload_file.write_text(json.dumps(payload_data), encoding="utf-8")
    out_png = tmp_path / "roadmap.png"

    main(["script", str(payload_file), str(out_png)])

    assert out_png.is_file(), "La imagen del roadmap debe haberse generado físicamente."
    header = out_png.read_bytes()[:8]
    assert header == b"\x89PNG\r\n\x1a\n", "Debe ser una imagen PNG válida (cabecera RFC 2083)."


def test_generate_executive_roadmap_image_empty_exit(tmp_path: Path):
    """Verify that main terminates cleanly with sys.exit(0) when horizons are empty."""
    empty_payload = tmp_path / "empty.json"
    empty_payload.write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["script", str(empty_payload)])
    assert exc_info.value.code == 0
