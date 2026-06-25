from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict


class MaturityBandDefinition(TypedDict):
    """Specify a maturity band with an inclusive numerical range and an associated label."""

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
    """Resolve a numerical score to its corresponding maturity band.

    This function iterates through a sequence of band definitions to find the first
    band whose inclusive range [`min`, `max`] contains the score. The score can
    be rounded to a specified precision before comparison.

    If the score does not fall within any of the defined bands (e.g., it is
    higher than the maximum value of the last band), the last band in the
    sequence is returned as a fallback.

    Args:
        score (float): The numerical score to classify.
        bands (Iterable[MaturityBandDefinition]): An iterable of maturity band
            definitions. Each must be a mapping containing 'min' and 'max' keys.
        score_precision (int | None): Keyword-only. The number of decimal places
            to round the score to before comparison. If None, no rounding is
            performed.

    Returns:
        MaturityBandDefinition: The first matching band definition found. If no
        band's range includes the score, the last band from the `bands` iterable
        is returned.

    Raises:
        ValueError: If `bands` is an empty iterable.
    """
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
