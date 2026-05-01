from __future__ import annotations

import pytest

from assessment_engine.scripts.lib.maturity_band import (
    ANNEX_MATURITY_BANDS,
    GLOBAL_MATURITY_BANDS,
    MaturityBandDefinition,
    resolve_maturity_band,
)


def test_resolve_maturity_band_honors_precision_before_matching_ranges() -> None:
    tower_bands: tuple[MaturityBandDefinition, ...] = (
        {"min": 1.0, "max": 1.8, "label": "Level 1"},
        {"min": 1.8, "max": 2.6, "label": "Level 2"},
        {"min": 2.6, "max": 3.4, "label": "Level 3"},
    )

    assert (
        resolve_maturity_band(
            2.60005,
            tower_bands,
            score_precision=4,
        )["label"]
        == "Level 2"
    )
    assert (
        resolve_maturity_band(
            2.60015,
            tower_bands,
            score_precision=4,
        )["label"]
        == "Level 3"
    )


def test_resolve_maturity_band_uses_first_matching_range_and_last_fallback() -> None:
    tower_bands: tuple[MaturityBandDefinition, ...] = (
        {"min": 1.0, "max": 1.8, "label": "Level 1"},
        {"min": 1.8, "max": 2.6, "label": "Level 2"},
        {"min": 2.6, "max": 3.4, "label": "Level 3"},
    )

    assert resolve_maturity_band(1.8, tower_bands)["label"] == "Level 1"
    assert resolve_maturity_band(0.5, tower_bands)["label"] == "Level 3"


def test_resolve_maturity_band_supports_shared_annex_and_global_policies() -> None:
    assert resolve_maturity_band(1.49, ANNEX_MATURITY_BANDS)["label"] == "Inicial"
    assert resolve_maturity_band(3.5, ANNEX_MATURITY_BANDS)["label"] == "Gestionado"
    assert resolve_maturity_band(3.49, GLOBAL_MATURITY_BANDS)["label"] == "Básica"
    assert resolve_maturity_band(3.5, GLOBAL_MATURITY_BANDS)["label"] == "Optimizada"


def test_resolve_maturity_band_requires_at_least_one_band() -> None:
    with pytest.raises(ValueError, match="At least one maturity band is required"):
        resolve_maturity_band(3.0, ())
