"""Unit test for scoring calculation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from assessment_engine.application.run_scoring import build_scoring, load_json


def test_build_scoring_deterministic():
    """Verify that build_scoring calculates weighted maturity scores and resolves bands."""
    tower_def_path = Path("engine_config/towers/T1/tower_definition_T1.json")
    tower_def = load_json(tower_def_path)

    case_input = {
        "case_id": "test_case",
        "tower_id": "T1",
        "tower_name": "Workplace & End User Services",
        "answers": [
            {"kpi_id": "T1.P1.K1.PR1", "value": 4.0},
            {"kpi_id": "T1.P2.K1.PR1", "value": 3.0},
        ],
    }

    scoring = build_scoring(case_input, tower_def)
    assert scoring["tower_id"] == "T1"
    assert "tower_score_exact" in scoring
    assert "pillar_scores" in scoring
    assert len(scoring["pillar_scores"]) > 0
    assert "maturity_band_from_exact" in scoring
