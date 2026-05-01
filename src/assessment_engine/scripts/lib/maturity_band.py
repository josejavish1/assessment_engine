from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict


class MaturityBandDefinition(TypedDict):
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
