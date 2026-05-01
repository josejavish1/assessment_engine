from __future__ import annotations

from typing import Any

from assessment_engine.scripts.lib.global_maturity_policy import (
    average_pillar_score,
    average_pillar_target,
    band_for_score,
    safe_float,
    status_color_for_score,
)


def test_average_pillar_metrics_ignore_missing_values() -> None:
    pillars: list[dict[str, Any]] = [
        {"score": 2.8, "target_score": 3.8},
        {"score": "3.2", "target_score": "4.2"},
        {"score": None, "target_score": ""},
    ]

    assert average_pillar_score(pillars) == 3.0
    assert average_pillar_target(pillars) == 4.0


def test_maturity_policy_uses_shared_thresholds() -> None:
    assert band_for_score(3.5) == "Optimizada"
    assert band_for_score(3.4) == "Básica"
    assert status_color_for_score(2.5) == "E06666"
    assert status_color_for_score(3.0) == "FFD966"
    assert status_color_for_score(3.4) == "93C47D"


def test_safe_float_handles_strings_and_invalid_values() -> None:
    assert safe_float("4,2") == 4.2
    assert safe_float("3.7 / 5.0") == 3.7
    assert safe_float("invalid", default=1.5) == 1.5
