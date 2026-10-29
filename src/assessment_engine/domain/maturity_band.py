from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import TypedDict, cast

logger = logging.getLogger(__name__)


class MaturityBandDefinition(TypedDict, total=False):
    """Define the schema for a single maturity band definition."""

    min: float
    max: float
    label: str
    band_key: str


ANNEX_MATURITY_BANDS: tuple[MaturityBandDefinition, ...] = (
    {"min": 4.5, "max": float("inf"), "label": "Optimized", "band_key": "band_optimized"},
    {"min": 3.5, "max": 4.5, "label": "Managed", "band_key": "band_managed"},
    {"min": 2.5, "max": 3.5, "label": "Defined", "band_key": "band_defined"},
    {"min": 1.5, "max": 2.5, "label": "Repeatable", "band_key": "band_repeatable"},
    {"min": float("-inf"), "max": 1.5, "label": "Initial", "band_key": "band_initial"},
)

GLOBAL_MATURITY_BANDS: tuple[MaturityBandDefinition, ...] = (
    {"min": 3.5, "max": float("inf"), "label": "Optimized", "band_key": "band_optimized"},
    {"min": float("-inf"), "max": 3.5, "label": "Basic", "band_key": "band_initial"},
)


def resolve_maturity_band(
    score: float,
    bands: Iterable[MaturityBandDefinition],
    *,
    score_precision: int | None = None,
    locale: str | None = None,
) -> MaturityBandDefinition:
    """Maps a numerical score to its corresponding maturity band definition,
    supporting late-binding localization via canonical band_key tokens."""
    band_list = tuple(bands)
    if not band_list:
        raise ValueError("At least one maturity band is required.")

    normalized_score = (
        round(score, score_precision) if score_precision is not None else score
    )

    matched_band = band_list[-1]
    for band in band_list:
        if band["min"] <= normalized_score <= band["max"]:
            matched_band = band
            break

    band_dict = dict(matched_band)
    band_key = band_dict.get("band_key")
    if not band_key:
        raw_lbl = str(band_dict.get("label", "")).lower()
        if "optimi" in raw_lbl or "avanzad" in raw_lbl:
            band_key = "band_optimized"
        elif "gestionad" in raw_lbl:
            band_key = "band_managed"
        elif "definid" in raw_lbl or "estandarizad" in raw_lbl:
            band_key = "band_defined"
        elif any(k in raw_lbl for k in ["repetib", "basic"]):
            band_key = "band_repeatable"
        else:
            band_key = "band_initial"
        band_dict["band_key"] = band_key

    if locale:
        try:
            from assessment_engine.infrastructure.localization import (
                get_localized_string,
            )

            localized_label = get_localized_string(
                band_key, locale=locale, default=band_dict.get("label")
            )
            if localized_label:
                band_dict["label"] = localized_label
        except (KeyError, ValueError, AttributeError, OSError) as ex:
            logger.debug(f"[MaturityBand] Localization skipped: {ex}")

    return cast(MaturityBandDefinition, band_dict)


__all__ = [
    "ANNEX_MATURITY_BANDS",
    "GLOBAL_MATURITY_BANDS",
    "MaturityBandDefinition",
    "resolve_maturity_band",
]
