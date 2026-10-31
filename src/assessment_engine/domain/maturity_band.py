"""Pure Domain Model for Maturity Bands and Score Resolution.

Zero static infrastructure dependencies and zero natural language hardcoding.
"""
from __future__ import annotations

import importlib
import logging
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Callable, Protocol, TypedDict, cast

from assessment_engine.domain.exceptions import (
    DomainValidationError,
    InvalidScoreError,
    MaturityBandContiguityError,
    UnmappedScoreError,
)

logger = logging.getLogger(__name__)

SPECTRUM_MIN_SCORE: float = 0.0
SPECTRUM_MAX_SCORE: float = 100.0


class LocalizationProviderPort(Protocol):
    """Application/Domain Port for resolving canonical semantic tokens into human-readable strings."""

    def translate(self, canonical_key: str, locale: str = "en") -> str:
        """Resolves a canonical key (e.g., 'band_optimized') to a localized string."""
        ...


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
    translator: Callable[..., str | None] | None = None,
) -> MaturityBandDefinition:
    """Maps a numerical score to its corresponding maturity band definition,
    supporting late-binding localization via canonical band_key tokens."""
    if isinstance(score, bool) or not isinstance(score, (int, float)) or math.isnan(score):
        raise InvalidScoreError(
            score=1.0 if score is True else (0.0 if score is False else 0.0),
            min_allowed=float("-inf"),
            max_allowed=float("inf"),
        )

    band_list = tuple(bands)
    if not band_list:
        raise DomainValidationError("At least one maturity band is required.")

    normalized_score = (
        round(score, score_precision) if score_precision is not None else score
    )

    matched_band: MaturityBandDefinition | None = None
    for band in band_list:
        b_min = float(band.get("min", float("-inf")))
        b_max = float(band.get("max", float("inf")))
        if b_min <= normalized_score <= b_max:
            matched_band = band
            break

    if matched_band is None:
        matched_band = band_list[-1]

    band_dict = dict(matched_band)
    band_key = band_dict.get("band_key")
    if not band_key:
        raw_label = str(band_dict.get("label", "")).strip().lower().replace(" ", "_")
        band_key = f"band_{raw_label}" if raw_label else "band_initial"
        band_dict["band_key"] = band_key

    # Resolve localized presentation label via injected translator port or late-binding resolution
    if locale:
        active_translator = translator
        if active_translator is None:
            try:
                loc_mod = importlib.import_module("assessment_engine.infrastructure.localization")
                active_translator = getattr(loc_mod, "get_localized_string", None)
            except (ImportError, AttributeError):
                active_translator = None

        if active_translator is not None:
            try:
                localized_label = active_translator(
                    band_key, locale=locale, default=band_dict.get("label")
                )
                if localized_label:
                    band_dict["label"] = localized_label
            except Exception as ex:
                logger.debug("[MaturityBand] Translation resolution skipped: %s", ex)

    return cast(MaturityBandDefinition, band_dict)


@dataclass(frozen=True)
class MaturityBand:
    """Immutable Domain Value Object representing a single maturity tier.

    Contains strictly mathematical boundaries and canonical semantic tokens.
    """

    band_id: str
    canonical_key: str
    min_score: float
    max_score: float
    is_inclusive_min: bool = True
    is_inclusive_max: bool = False

    def __post_init__(self) -> None:
        if not self.band_id or not self.band_id.strip():
            raise DomainValidationError(
                "MaturityBand 'band_id' cannot be empty.",
                context={"band_id": self.band_id},
            )
        if not self.canonical_key or not self.canonical_key.strip():
            raise DomainValidationError(
                "MaturityBand 'canonical_key' cannot be empty.",
                context={"canonical_key": self.canonical_key},
            )
        if isinstance(self.min_score, bool) or isinstance(self.max_score, bool):
            raise DomainValidationError(
                "MaturityBand score boundaries must be numerical, not boolean.",
                context={"band_id": self.band_id},
            )
        if math.isnan(self.min_score) or math.isnan(self.max_score):
            raise DomainValidationError(
                "MaturityBand boundaries cannot be NaN.",
                context={"band_id": self.band_id},
            )
        if self.min_score < SPECTRUM_MIN_SCORE or self.max_score > SPECTRUM_MAX_SCORE:
            raise DomainValidationError(
                f"MaturityBand '{self.band_id}' boundaries [{self.min_score}, {self.max_score}] "
                f"exceed valid spectrum [{SPECTRUM_MIN_SCORE}, {SPECTRUM_MAX_SCORE}].",
                context={
                    "band_id": self.band_id,
                    "min_score": self.min_score,
                    "max_score": self.max_score,
                },
            )
        if self.min_score >= self.max_score:
            raise DomainValidationError(
                f"MaturityBand '{self.band_id}' min_score ({self.min_score}) must be "
                f"strictly less than max_score ({self.max_score}).",
                context={
                    "band_id": self.band_id,
                    "min_score": self.min_score,
                    "max_score": self.max_score,
                },
            )

    def contains(self, score: float) -> bool:
        """Evaluates whether a given numerical score falls within this band's interval."""
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or math.isnan(score)
            or score < SPECTRUM_MIN_SCORE
            or score > SPECTRUM_MAX_SCORE
        ):
            raise InvalidScoreError(
                score=1.0 if score is True else (0.0 if score is False else float(score)),
                min_allowed=SPECTRUM_MIN_SCORE,
                max_allowed=SPECTRUM_MAX_SCORE,
            )

        lower_match = score >= self.min_score if self.is_inclusive_min else score > self.min_score
        upper_match = score <= self.max_score if self.is_inclusive_max else score < self.max_score
        return lower_match and upper_match


class MaturityBandCatalog:
    """Immutable Domain Aggregate managing the complete spectrum of MaturityBands.

    Guarantees mathematical contiguity, completeness, and mutual exclusivity across [0.0, 100.0].
    """

    def __init__(self, bands: Sequence[MaturityBand]) -> None:
        if not bands:
            raise MaturityBandContiguityError(
                "MaturityBandCatalog requires at least one MaturityBand."
            )

        sorted_bands = tuple(sorted(bands, key=lambda b: (b.min_score, b.max_score)))
        self._validate_spectrum_contiguity(sorted_bands)
        self._bands: tuple[MaturityBand, ...] = sorted_bands

    @property
    def bands(self) -> tuple[MaturityBand, ...]:
        """Returns an immutable tuple of the ordered maturity bands."""
        return self._bands

    @staticmethod
    def _validate_spectrum_contiguity(sorted_bands: tuple[MaturityBand, ...]) -> None:
        """Enforces strict partition invariants over [0.0, 100.0]:
        1. First band must start at 0.0 (inclusive).
        2. Last band must end at 100.0 (inclusive).
        3. Adjacent bands must share an exact boundary value without gaps or overlaps.
        4. Exactly one touching boundary must be inclusive.
        """
        first_band = sorted_bands[0]
        if (
            not math.isclose(first_band.min_score, SPECTRUM_MIN_SCORE, abs_tol=1e-9)
            or not first_band.is_inclusive_min
        ):
            raise MaturityBandContiguityError(
                f"Spectrum must start at {SPECTRUM_MIN_SCORE} (inclusive). "
                f"First band '{first_band.band_id}' starts at {first_band.min_score}.",
                context={
                    "first_band_id": first_band.band_id,
                    "min_score": first_band.min_score,
                    "is_inclusive_min": first_band.is_inclusive_min,
                },
            )

        last_band = sorted_bands[-1]
        if (
            not math.isclose(last_band.max_score, SPECTRUM_MAX_SCORE, abs_tol=1e-9)
            or not last_band.is_inclusive_max
        ):
            raise MaturityBandContiguityError(
                f"Spectrum must end at {SPECTRUM_MAX_SCORE} (inclusive). "
                f"Last band '{last_band.band_id}' ends at {last_band.max_score}.",
                context={
                    "last_band_id": last_band.band_id,
                    "max_score": last_band.max_score,
                    "is_inclusive_max": last_band.is_inclusive_max,
                },
            )

        for idx in range(len(sorted_bands) - 1):
            current_band = sorted_bands[idx]
            next_band = sorted_bands[idx + 1]

            if not math.isclose(current_band.max_score, next_band.min_score, abs_tol=1e-9):
                if current_band.max_score < next_band.min_score:
                    raise MaturityBandContiguityError(
                        f"Score gap detected between '{current_band.band_id}' "
                        f"(max={current_band.max_score}) and '{next_band.band_id}' "
                        f"(min={next_band.min_score}).",
                        context={
                            "left_band": current_band.band_id,
                            "right_band": next_band.band_id,
                        },
                    )
                raise MaturityBandContiguityError(
                    f"Score overlap detected between '{current_band.band_id}' "
                    f"(max={current_band.max_score}) and '{next_band.band_id}' "
                    f"(min={next_band.min_score}).",
                    context={
                        "left_band": current_band.band_id,
                        "right_band": next_band.band_id,
                    },
                )

            # Exactly one boundary must be inclusive
            if current_band.is_inclusive_max == next_band.is_inclusive_min:
                boundary_state = (
                    "both inclusive (overlap)"
                    if current_band.is_inclusive_max
                    else "both exclusive (point gap)"
                )
                raise MaturityBandContiguityError(
                    f"Invalid boundary inclusivity at score {current_band.max_score} "
                    f"between '{current_band.band_id}' and '{next_band.band_id}': {boundary_state}.",
                    context={
                        "boundary_score": current_band.max_score,
                        "left_band": current_band.band_id,
                        "right_band": next_band.band_id,
                    },
                )

    def resolve_band(self, score: float) -> MaturityBand:
        """Deterministically resolves a numerical score in [0.0, 100.0] to its MaturityBand."""
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or math.isnan(score)
            or score < SPECTRUM_MIN_SCORE
            or score > SPECTRUM_MAX_SCORE
        ):
            raise InvalidScoreError(
                score=1.0 if score is True else (0.0 if score is False else float(score)),
                min_allowed=SPECTRUM_MIN_SCORE,
                max_allowed=SPECTRUM_MAX_SCORE,
            )

        for band in self._bands:
            if band.contains(score):
                return band

        raise UnmappedScoreError(score=score)

    def resolve_canonical_key(self, score: float) -> str:
        """Resolves a numerical score directly to its canonical semantic token."""
        return self.resolve_band(score).canonical_key


__all__ = [
    "ANNEX_MATURITY_BANDS",
    "GLOBAL_MATURITY_BANDS",
    "LocalizationProviderPort",
    "MaturityBand",
    "MaturityBandCatalog",
    "MaturityBandDefinition",
    "resolve_maturity_band",
]
