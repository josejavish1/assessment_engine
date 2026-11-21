from __future__ import annotations

import pytest

from assessment_engine.domain.maturity_band import (
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
    # Baseline English
    assert resolve_maturity_band(1.49, ANNEX_MATURITY_BANDS)["label"] == "Initial"
    assert resolve_maturity_band(3.5, ANNEX_MATURITY_BANDS)["label"] == "Optimized"
    assert resolve_maturity_band(2.1, ANNEX_MATURITY_BANDS)["label"] == "Basic"
    assert resolve_maturity_band(3.49, GLOBAL_MATURITY_BANDS)["label"] == "Basic"
    assert resolve_maturity_band(3.5, GLOBAL_MATURITY_BANDS)["label"] == "Optimized"

    # Localized Spanish
    from assessment_engine.infrastructure.localization import t

    assert resolve_maturity_band(1.49, ANNEX_MATURITY_BANDS, locale="es", translator=t)["label"] == "Inicial"
    assert resolve_maturity_band(3.5, ANNEX_MATURITY_BANDS, locale="es", translator=t)["label"] == "Optimizado"
    assert resolve_maturity_band(2.1, ANNEX_MATURITY_BANDS, locale="es", translator=t)["label"] == "Básico"
    assert resolve_maturity_band(3.49, GLOBAL_MATURITY_BANDS, locale="es", translator=t)["label"] in ("Inicial", "Básica", "Basica")
    assert resolve_maturity_band(3.5, GLOBAL_MATURITY_BANDS, locale="es", translator=t)["label"] in ("Avanzado", "Optimizado", "Optimizada", "En Optimización", "Optimizado y Resiliente")


def test_resolve_maturity_band_requires_at_least_one_band() -> None:
    with pytest.raises(ValueError, match="At least one maturity band is required"):
        resolve_maturity_band(3.0, ())


def test_resolve_maturity_band_rejects_booleans() -> None:
    from assessment_engine.domain.exceptions import InvalidScoreError
    with pytest.raises(InvalidScoreError) as exc_info:
        resolve_maturity_band(True, ANNEX_MATURITY_BANDS)
    assert exc_info.value.context["score"] == 1.0

    with pytest.raises(InvalidScoreError) as exc_info2:
        resolve_maturity_band(False, ANNEX_MATURITY_BANDS)
    assert exc_info2.value.context["score"] == 0.0


def test_resolve_maturity_interval_levels() -> None:
    """Verify that actuarial resolve_maturity_interval maps scores to exact canonical levels."""
    from assessment_engine.domain.actuarial.maturity_band import resolve_maturity_interval

    interval_low = resolve_maturity_interval(1.5)
    assert interval_low.level == 1

    interval_mid = resolve_maturity_interval(3.2)
    assert interval_mid.level == 3

    interval_high = resolve_maturity_interval(4.8)
    assert interval_high.level == 5


