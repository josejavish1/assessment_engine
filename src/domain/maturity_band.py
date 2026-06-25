from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict


class MaturityBandDefinition(TypedDict):
    """Define the schema for a single maturity band definition."""

    min: float
    max: float
    label: str


ANNEX_MATURITY_BANDS: tuple[MaturityBandDefinition, ...] = (
    {"min": 4.5, "max": float("inf"), "label": "Optimizado"},
    {"min": 3.5, "max": 4.5, "label": "Gestionado"},
    {"min": 2.5, "max": 3.5, "label": "Definido"},
    {"min": 1.5, "max": 2.5, "label": "Repetible"},
    {"min": float("-inf"), "max": 1.5, "label": "Inicial"},
)

GLOBAL_MATURITY_BANDS: tuple[MaturityBandDefinition, ...] = (
    {"min": 3.5, "max": float("inf"), "label": "Optimizada"},
    {"min": float("-inf"), "max": 3.5, "label": "Básica"},
)


def resolve_maturity_band(
    score: float,
    bands: Iterable[MaturityBandDefinition],
    *,
    score_precision: int | None = None,
) -> MaturityBandDefinition:
    r"""{'docstring': "Maps a numerical score to its corresponding maturity band definition.\n\n    The function iterates through an ordered sequence of bands and returns the\n    first definition whose inclusive `min` and `max` score range contains the\n    input `score`. The score can optionally be rounded to a specified number of\n    decimal places before comparison.\n\n    If the score does not fall within any of the defined bands, the last band\n    in the sequence is returned as a fallback.\n\n    Args:\n        score: The numerical score to categorize.\n        bands: An iterable of `MaturityBandDefinition` objects. The order is\n            significant, as the first band whose range contains the score is\n            returned. Each definition must be a mapping with 'min' and 'max' keys.\n        score_precision: If provided, the number of decimal places to which the\n            `score` will be rounded before comparison.\n\n    Returns:\n        The first `MaturityBandDefinition` from `bands` whose score range\n        contains the `score`. If no band matches, the last band in the `bands`\n        iterable is returned.\n\n    Raises:\n        ValueError: If the `bands` iterable is empty."}."""
    band_list = tuple(bands)
    if not band_list:
        raise ValueError("At least one maturity band is required.")

    normalized_score = (
        round(score, score_precision) if score_precision is not None else score
    )

    for band in band_list:
        if band["min"] <= normalized_score <= band["max"]:
            return band

    return band_list[-1]


__all__ = [
    "ANNEX_MATURITY_BANDS",
    "GLOBAL_MATURITY_BANDS",
    "MaturityBandDefinition",
    "resolve_maturity_band",
]
