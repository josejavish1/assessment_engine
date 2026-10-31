# golden-path: ignore
"""Unit tests verifying pure domain maturity band logic, contiguity invariants, and late-binding translation."""
from __future__ import annotations

import math
import pytest

from assessment_engine.domain.exceptions import (
    DomainValidationError,
    InvalidScoreError,
    MaturityBandContiguityError,
    UnmappedScoreError,
)
from assessment_engine.domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    GLOBAL_MATURITY_BANDS,
    MaturityBand,
    MaturityBandCatalog,
    resolve_maturity_band,
)


def test_maturity_band_boundary_invariants() -> None:
    # 1. Reject empty band_id
    with pytest.raises(DomainValidationError):
        MaturityBand(band_id="", canonical_key="band_test", min_score=0.0, max_score=10.0)

    # 2. Reject empty canonical_key
    with pytest.raises(DomainValidationError):
        MaturityBand(band_id="test", canonical_key="", min_score=0.0, max_score=10.0)

    # 3. Reject min_score >= max_score
    with pytest.raises(DomainValidationError):
        MaturityBand(band_id="test", canonical_key="key", min_score=20.0, max_score=10.0)

    # 4. Reject out-of-spectrum bounds
    with pytest.raises(DomainValidationError):
        MaturityBand(band_id="test", canonical_key="key", min_score=-1.0, max_score=10.0)

    # 5. Reject boolean boundary scores
    with pytest.raises(DomainValidationError):
        MaturityBand(band_id="test", canonical_key="key", min_score=True, max_score=10.0)  # type: ignore[arg-type]


def test_maturity_band_catalog_contiguity_invariants() -> None:
    # 1. Reject spectrum not starting at 0.0
    with pytest.raises(MaturityBandContiguityError):
        MaturityBandCatalog(
            bands=[
                MaturityBand("b1", "k1", 10.0, 100.0, is_inclusive_min=True, is_inclusive_max=True),
            ]
        )

    # 2. Reject spectrum not ending at 100.0
    with pytest.raises(MaturityBandContiguityError):
        MaturityBandCatalog(
            bands=[
                MaturityBand("b1", "k1", 0.0, 90.0, is_inclusive_min=True, is_inclusive_max=True),
            ]
        )

    # 3. Reject gap between adjacent bands
    with pytest.raises(MaturityBandContiguityError):
        MaturityBandCatalog(
            bands=[
                MaturityBand("b1", "k1", 0.0, 40.0, is_inclusive_min=True, is_inclusive_max=False),
                MaturityBand("b2", "k2", 50.0, 100.0, is_inclusive_min=True, is_inclusive_max=True),
            ]
        )

    # 4. Reject overlap between adjacent bands
    with pytest.raises(MaturityBandContiguityError):
        MaturityBandCatalog(
            bands=[
                MaturityBand("b1", "k1", 0.0, 60.0, is_inclusive_min=True, is_inclusive_max=False),
                MaturityBand("b2", "k2", 50.0, 100.0, is_inclusive_min=True, is_inclusive_max=True),
            ]
        )


def test_maturity_band_catalog_deterministic_resolution() -> None:
    catalog = MaturityBandCatalog(
        bands=[
            MaturityBand("initial", "band_initial", 0.0, 25.0, is_inclusive_min=True, is_inclusive_max=False),
            MaturityBand("defined", "band_defined", 25.0, 75.0, is_inclusive_min=True, is_inclusive_max=False),
            MaturityBand("optimized", "band_optimized", 75.0, 100.0, is_inclusive_min=True, is_inclusive_max=True),
        ]
    )

    # Invariants on boundary transitions
    assert catalog.resolve_canonical_key(0.0) == "band_initial"
    assert catalog.resolve_canonical_key(24.999) == "band_initial"
    assert catalog.resolve_canonical_key(25.0) == "band_defined"
    assert catalog.resolve_canonical_key(74.999) == "band_defined"
    assert catalog.resolve_canonical_key(75.0) == "band_optimized"
    assert catalog.resolve_canonical_key(100.0) == "band_optimized"

    # Out of bounds raises InvalidScoreError
    with pytest.raises(InvalidScoreError):
        catalog.resolve_band(-0.01)

    with pytest.raises(InvalidScoreError):
        catalog.resolve_band(100.01)

    # Boolean values must be rejected as InvalidScoreError
    with pytest.raises(InvalidScoreError):
        catalog.resolve_band(True)  # type: ignore[arg-type]

    with pytest.raises(InvalidScoreError):
        catalog.resolve_band(False)  # type: ignore[arg-type]


def test_resolve_maturity_band_legacy_compatibility() -> None:
    # Test standard Annex resolution
    res_annex = resolve_maturity_band(4.8, ANNEX_MATURITY_BANDS)
    assert res_annex["label"] == "Optimized"
    assert res_annex["band_key"] == "band_optimized"

    # Test standard Global resolution
    res_global = resolve_maturity_band(2.0, GLOBAL_MATURITY_BANDS)
    assert res_global["label"] == "Basic"
    assert res_global["band_key"] == "band_initial"

    # Boolean score rejected
    with pytest.raises(InvalidScoreError):
        resolve_maturity_band(True, ANNEX_MATURITY_BANDS)  # type: ignore[arg-type]


def test_resolve_maturity_band_injected_translator() -> None:
    def custom_translator(key: str, locale: str, default: str | None = None) -> str:
        if locale == "ja" and key == "band_optimized":
            return "最適化 (Optimized)"
        return default or key

    res = resolve_maturity_band(
        4.9,
        ANNEX_MATURITY_BANDS,
        locale="ja",
        translator=custom_translator,
    )
    assert res["label"] == "最適化 (Optimized)"
