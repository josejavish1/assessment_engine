from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from assessment_engine.scripts.lib.maturity_band import (
    GLOBAL_MATURITY_BANDS,
    resolve_maturity_band,
)

LOW_MATURITY_COLOR = "E06666"
MEDIUM_MATURITY_COLOR = "FFD966"
HIGH_MATURITY_COLOR = "93C47D"
DEFAULT_TARGET_MATURITY = 4.0


def safe_float(value: Any, default: float = 0.0) -> float:
    """Attempt to convert a value to a float, returning a default on failure.

    The conversion process is designed to be robust against common data
    inconsistencies. The input value is first cast to a string. It is then
    processed by taking only the first whitespace-separated token and replacing
    commas with periods to normalize the decimal separator. This allows for
    successful conversion of inputs like "123,45 EUR" to 123.45.

    If the input is None or an empty string, or if a `TypeError` or `ValueError`
    occurs during the final float conversion, the function returns the specified
    default value instead of raising an exception.

    Args:
        value: The input value to convert.
        default: The value to return if conversion fails. Defaults to 0.0.

    Returns:
        The converted float value, or the `default` value upon failure.
    """
    if value in (None, ""):
        return default
    try:
        return float(str(value).split()[0].replace(",", "."))
    except (TypeError, ValueError):
        return default


def average_numeric_values(values: Iterable[Any], *, default: float) -> float:
    """Calculates the statistical mean of numeric values within an iterable.

    Iterates through the provided values, converting valid numeric representations
    to floats for averaging. Values of `None`, empty strings, and non-numeric
    strings are silently ignored.

    Args:
        values: An iterable of values to process. Non-numeric items are ignored.
        default: The value to return if `values` contains no valid numeric data.

    Returns:
        The calculated mean, or the `default` value if no numeric values were
        found.
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
    """Calculate the average value of the 'score' key from an iterable of pillar mappings."""
    return average_numeric_values(
        (pillar.get("score") for pillar in pillars), default=default
    )


def average_pillar_target(
    pillars: Iterable[Mapping[str, Any]], *, default: float = DEFAULT_TARGET_MATURITY
) -> float:
    """Calculate the average 'target_score' from an iterable of pillar mappings."""
    return average_numeric_values(
        (pillar.get("target_score") for pillar in pillars),
        default=default,
    )


def band_for_score(score: float) -> str:
    """Resolve the maturity band label for a given score using the global band definitions."""
    return resolve_maturity_band(score, GLOBAL_MATURITY_BANDS)["label"]


def status_color_for_score(score: float) -> str:
    """{'docstring': 'Map a numerical maturity score to its corresponding status color string.'}."""
    if score < 2.6:
        return LOW_MATURITY_COLOR
    if score < 3.4:
        return MEDIUM_MATURITY_COLOR
    return HIGH_MATURITY_COLOR
