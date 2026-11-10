"""Unit tests for the Universal Actuarial Telemetry Calibration Engine (UATCE).

Validates cross-vertical mathematical invariance and monotonicity across global industries.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from assessment_engine.domain.actuarial.calibration_engine import (
    CalibratedRiskVector,
    TenantTelemetryOverrides,
    UniversalActuarialCalibrationEngine,
)
from assessment_engine.domain.actuarial.financial_profile import IndustryArchetype


def test_cementos_molins_manufacturing_calibration() -> None:
    """Case A: Cementos Molins (Heavy Process Manufacturing OT)."""
    scores = {
        "availability": 2.20,
        "cybersecurity": 2.10,
        "governance": 2.00,
        "finops_architecture": 2.00,
    }
    vec = UniversalActuarialCalibrationEngine.compute_calibrated_ale(
        gross_annual_revenue=1_140_000_000.0,
        archetype=IndustryArchetype.PROCESS_MANUFACTURING_OT,
        maturity_scores=scores,
        uncalibrated_base_downtime_loss=1_850_000.0,
        currency_iso="EUR",
    )

    assert isinstance(vec, CalibratedRiskVector)
    assert vec.currency_iso == "EUR"
    # Expected: ~1.49M EUR within +/- 5% tolerance
    assert 1_400_000.0 <= vec.total_annualized_loss_expectancy <= 1_580_000.0
    # Effective revenue perimeter should reflect 62% prior
    assert round(vec.effective_revenue_perimeter) == 706_800_000


def test_starling_bank_fintech_calibration() -> None:
    """Case B: Starling Bank (Continuous Digital FinTech)."""
    scores = {
        "availability": 4.50,
        "cybersecurity": 4.50,
        "governance": 4.50,
        "finops_architecture": 4.50,
    }
    vec = UniversalActuarialCalibrationEngine.compute_calibrated_ale(
        gross_annual_revenue=140_000_000.0,
        archetype=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
        maturity_scores=scores,
        currency_iso="GBP",
    )

    assert vec.currency_iso == "GBP"
    # High maturity (4.5) dramatically attenuates risk to ~0.4% - 0.5% of turnover
    assert 400_000.0 <= vec.total_annualized_loss_expectancy <= 750_000.0


def test_rede_dor_healthcare_calibration() -> None:
    """Case C: Rede D'Or (Life Safety Healthcare Network)."""
    scores = {
        "availability": 2.50,
        "cybersecurity": 2.10,
        "governance": 2.00,
        "finops_architecture": 2.00,
    }
    vec = UniversalActuarialCalibrationEngine.compute_calibrated_ale(
        gross_annual_revenue=40_000_000_000.0,
        archetype=IndustryArchetype.LIFE_SAFETY_CRITICAL,
        maturity_scores=scores,
        currency_iso="BRL",
    )

    assert vec.currency_iso == "BRL"
    # ~200M BRL expected (~0.5% of 40B BRL revenue) within realistic bounds
    assert 150_000_000.0 <= vec.total_annualized_loss_expectancy <= 250_000_000.0


def test_chedraui_retail_calibration() -> None:
    """Case D: Grupo Comercial Chedraui (High Tempo Commercial Retail)."""
    scores = {
        "availability": 2.40,
        "cybersecurity": 2.10,
        "governance": 2.00,
        "finops_architecture": 2.00,
    }
    vec = UniversalActuarialCalibrationEngine.compute_calibrated_ale(
        gross_annual_revenue=250_000_000_000.0,
        archetype=IndustryArchetype.HIGH_TEMPO_COMMERCIAL,
        maturity_scores=scores,
        currency_iso="MXN",
    )

    assert vec.currency_iso == "MXN"
    # ~950M MXN expected (~0.38% of 250B MXN revenue) within realistic bounds
    assert 800_000_000.0 <= vec.total_annualized_loss_expectancy <= 1_200_000_000.0


def test_mathematical_monotonicity_across_maturities() -> None:
    """Asserts that as maturity improves from 1.0 to 5.0, ALE strictly decreases."""
    archetypes = [
        IndustryArchetype.PROCESS_MANUFACTURING_OT,
        IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
        IndustryArchetype.LIFE_SAFETY_CRITICAL,
        IndustryArchetype.HIGH_TEMPO_COMMERCIAL,
        IndustryArchetype.DEFERRED_NETWORK_LOGISTICS,
        IndustryArchetype.STANDARD_ENTERPRISE_B2B,
    ]

    for arch in archetypes:
        prev_ale = float("inf")
        for m_level in [1.5, 2.5, 3.5, 4.5]:
            scores = {
                "availability": m_level,
                "cybersecurity": m_level,
                "governance": m_level,
                "finops_architecture": m_level,
            }
            vec = UniversalActuarialCalibrationEngine.compute_calibrated_ale(
                gross_annual_revenue=100_000_000.0,
                archetype=arch,
                maturity_scores=scores,
            )
            current_ale = vec.total_annualized_loss_expectancy
            assert current_ale < prev_ale, (
                f"Monotonicity violation for {arch} at maturity {m_level}: "
                f"Current ALE ({current_ale:,.2f}) >= Previous ALE ({prev_ale:,.2f})"
            )
            prev_ale = current_ale


def test_zero_client_hardcoding_in_calibration_module() -> None:
    """Enforces the Zero Hardcoding Law: No client names in calibration_engine.py."""
    engine_file = Path(__file__).resolve().parents[4] / "src" / "assessment_engine" / "domain" / "actuarial" / "calibration_engine.py"
    content = engine_file.read_text(encoding="utf-8").lower()

    prohibited_names = ["molins", "starling", "chedraui", "geodis", "rede_dor", "santander", "bbva"]
    for name in prohibited_names:
        assert name not in content, f"Zero Hardcoding Violation: Found '{name}' in {engine_file.name}!"
