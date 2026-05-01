from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

LOW_MATURITY_COLOR = "E06666"
MEDIUM_MATURITY_COLOR = "FFD966"
HIGH_MATURITY_COLOR = "93C47D"
DEFAULT_TARGET_MATURITY = 4.0


def safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(str(value).split()[0].replace(",", "."))
    except (TypeError, ValueError):
        return default


def average_numeric_values(values: Iterable[Any], *, default: float) -> float:
    numeric_values = [
        safe_float(value)
        for value in values
        if value not in (None, "")
        and safe_float(value, default=float("nan"))
        == safe_float(value, default=float("nan"))
    ]
    if not numeric_values:
        return default
    return sum(numeric_values) / len(numeric_values)


def average_pillar_score(
    pillars: Iterable[Mapping[str, Any]], *, default: float = 0.0
) -> float:
    return average_numeric_values(
        (pillar.get("score") for pillar in pillars), default=default
    )


def average_pillar_target(
    pillars: Iterable[Mapping[str, Any]], *, default: float = DEFAULT_TARGET_MATURITY
) -> float:
    return average_numeric_values(
        (pillar.get("target_score") for pillar in pillars),
        default=default,
    )


def band_for_score(score: float) -> str:
    return "Optimizada" if score >= 3.5 else "Básica"


def status_color_for_score(score: float) -> str:
    if score < 2.6:
        return LOW_MATURITY_COLOR
    if score < 3.4:
        return MEDIUM_MATURITY_COLOR
    return HIGH_MATURITY_COLOR
