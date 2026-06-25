from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from domain.maturity_band import (
    GLOBAL_MATURITY_BANDS,
    resolve_maturity_band,
)

LOW_MATURITY_COLOR = "E06666"
MEDIUM_MATURITY_COLOR = "FFD966"
HIGH_MATURITY_COLOR = "93C47D"
DEFAULT_TARGET_MATURITY = 4.0


def safe_float(value: Any, default: float = 0.0) -> float:
    """Parse a float from an arbitrary value, returning a default on conversion failure."""
    if value in (None, ""):
        return default
    try:
        return float(str(value).split()[0].replace(",", "."))
    except (TypeError, ValueError):
        return default


def average_numeric_values(values: Iterable[Any], *, default: float) -> float:
    """Calculate the arithmetic mean of numeric values in an iterable.

    This function computes the mean by converting items in the iterable to floats.
    Values are excluded from the calculation if they are `None`, an empty string
    (`""`), or result in `NaN` (Not a Number) upon conversion. Infinities are
    included in the calculation.

    Args:
        values: An iterable of items to average.
        default: The float value to return if `values` contains no processable
            numeric items after filtering.

    Returns:
        The float arithmetic mean of the valid numeric values, or the `default`
        value if no such values are found.
    """
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
    """Compute the average 'score' from an iterable of pillar mappings."""
    return average_numeric_values(
        (pillar.get("score") for pillar in pillars), default=default
    )


def average_pillar_target(
    pillars: Iterable[Mapping[str, Any]], *, default: float = DEFAULT_TARGET_MATURITY
) -> float:
    """Calculate the mean 'target_score' from an iterable of pillar mappings."""
    return average_numeric_values(
        (pillar.get("target_score") for pillar in pillars),
        default=default,
    )


def band_for_score(score: float) -> str:
    """Return the maturity band label for a score using the global band configuration."""
    return resolve_maturity_band(score, GLOBAL_MATURITY_BANDS)["label"]


def status_color_for_score(score: float) -> str:
    """Map a numerical maturity score to its corresponding status color."""
    if score < 2.6:
        return LOW_MATURITY_COLOR
    if score < 3.4:
        return MEDIUM_MATURITY_COLOR
    return HIGH_MATURITY_COLOR
