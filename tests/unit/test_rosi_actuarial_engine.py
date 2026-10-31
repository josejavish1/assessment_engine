"""Unit tests for Actuarial ROSI Engine and Stochastic FinOps (RFC-027)."""

from __future__ import annotations

import numpy as np
import pytest

from assessment_engine.domain.schemas.finops_rosi import (
    ControlAttenuationVector,
    EnterpriseFinancialContext,
    FairFactorTarget,
    PertDistributionParams,
    StochasticCostProfile,
)
from assessment_engine.infrastructure.rosi_calculator import ActuarialRosiEngine


@pytest.fixture
def sample_financial_context() -> EnterpriseFinancialContext:
    """Fixture providing enterprise financial context."""
    return EnterpriseFinancialContext(
        tenant_id="global_retail_corp",
        currency_code="USD",
        discount_rate_wacc=0.08,
        amortization_horizon_years=3,
        regional_purchasing_power_multiplier=1.0,
        vertical_complexity_multiplier=1.0,
    )


@pytest.fixture
def sample_cost_profile() -> StochasticCostProfile:
    """Fixture providing stochastic CapEx and OpEx distributions."""
    return StochasticCostProfile(
        capex_distribution=PertDistributionParams(min_val=40000.0, mode_val=60000.0, max_val=90000.0),
        opex_annual_distribution=PertDistributionParams(min_val=10000.0, mode_val=15000.0, max_val=25000.0),
        headcount_fte_allocation=1.5,
        implementation_duration_months=6.0,
    )


@pytest.fixture
def sample_attenuation_vectors() -> list[ControlAttenuationVector]:
    """Fixture providing control attenuation on Vulnerability and Loss Magnitude."""
    return [
        ControlAttenuationVector(
            target_factor=FairFactorTarget.VULN,
            efficacy_distribution=PertDistributionParams(min_val=0.5, mode_val=0.7, max_val=0.85),
        ),
        ControlAttenuationVector(
            target_factor=FairFactorTarget.PRIMARY_LOSS,
            efficacy_distribution=PertDistributionParams(min_val=0.2, mode_val=0.4, max_val=0.6),
        ),
    ]


@pytest.fixture
def sample_fair_vectors() -> tuple[np.ndarray, np.ndarray]:
    """Fixture providing baseline LEF and LM simulation vectors (10,000 samples)."""
    rng = np.random.default_rng(seed=123)
    lef_vec = rng.gamma(shape=2.0, scale=1.5, size=10000)
    lm_vec = rng.lognormal(mean=9.5, sigma=0.8, size=10000)
    return lef_vec, lm_vec


def test_risk_conservation_invariant(
    sample_financial_context: EnterpriseFinancialContext,
    sample_cost_profile: StochasticCostProfile,
    sample_attenuation_vectors: list[ControlAttenuationVector],
    sample_fair_vectors: tuple[np.ndarray, np.ndarray],
) -> None:
    """Verify that ALE post mitigation is strictly less than or equal to pre mitigation."""
    lef_vec, lm_vec = sample_fair_vectors
    engine = ActuarialRosiEngine(simulations_count=10000, random_seed=42)

    result = engine.evaluate_project_rosi(
        project_id="PROJ-SEC-001",
        financial_context=sample_financial_context,
        cost_profile=sample_cost_profile,
        attenuation_vectors=sample_attenuation_vectors,
        pre_lef_vector=lef_vec,
        pre_lm_vector=lm_vec,
    )

    # Invariants
    assert result.ale_post_mitigation.mean < result.ale_pre_mitigation.mean
    assert result.delta_ale_reduction.mean > 0.0
    assert result.delta_ale_reduction.p50 > 0.0
    assert result.probability_of_positive_return >= 0.0


def test_cost_complexity_monotonicity_invariant(
    sample_financial_context: EnterpriseFinancialContext,
    sample_cost_profile: StochasticCostProfile,
    sample_attenuation_vectors: list[ControlAttenuationVector],
    sample_fair_vectors: tuple[np.ndarray, np.ndarray],
) -> None:
    """Verify that higher vertical complexity increases TCO and lowers ROSI monotonically."""
    lef_vec, lm_vec = sample_fair_vectors
    engine = ActuarialRosiEngine(simulations_count=10000, random_seed=42)

    # Standard vertical (1.0x)
    res_standard = engine.evaluate_project_rosi(
        project_id="PROJ-01",
        financial_context=sample_financial_context,
        cost_profile=sample_cost_profile,
        attenuation_vectors=sample_attenuation_vectors,
        pre_lef_vector=lef_vec,
        pre_lm_vector=lm_vec,
    )

    # High-complexity regulated vertical (1.5x)
    complex_context = sample_financial_context.model_copy(update={"vertical_complexity_multiplier": 1.5})
    res_complex = engine.evaluate_project_rosi(
        project_id="PROJ-01",
        financial_context=complex_context,
        cost_profile=sample_cost_profile,
        attenuation_vectors=sample_attenuation_vectors,
        pre_lef_vector=lef_vec,
        pre_lm_vector=lm_vec,
    )

    assert res_complex.annualized_tco.p50 > res_standard.annualized_tco.p50
    assert res_complex.npv_total_cost.p50 > res_standard.npv_total_cost.p50
    assert res_complex.rosi_percentage.p50 < res_standard.rosi_percentage.p50


def test_degenerate_pert_zero_variance() -> None:
    """Verify that deterministic inputs (min == mode == max) yield exact zero variance."""
    engine = ActuarialRosiEngine(simulations_count=5000, random_seed=42)
    params = PertDistributionParams(min_val=50000.0, mode_val=50000.0, max_val=50000.0)

    samples = engine._sample_pert(params)
    metrics = engine._extract_metrics(samples)

    assert metrics.std_dev == 0.0
    assert metrics.mean == 50000.0
    assert metrics.p10 == 50000.0
    assert metrics.p50 == 50000.0
    assert metrics.p90 == 50000.0


def test_multi_currency_scale_invariance(
    sample_financial_context: EnterpriseFinancialContext,
    sample_cost_profile: StochasticCostProfile,
    sample_attenuation_vectors: list[ControlAttenuationVector],
    sample_fair_vectors: tuple[np.ndarray, np.ndarray],
) -> None:
    """Verify that Japanese Yen (JPY) with 150x currency scale preserves identical ROSI ratio."""
    lef_vec, lm_vec = sample_fair_vectors
    engine = ActuarialRosiEngine(simulations_count=10000, random_seed=42)

    # Base USD run
    res_usd = engine.evaluate_project_rosi(
        project_id="PROJ-01",
        financial_context=sample_financial_context,
        cost_profile=sample_cost_profile,
        attenuation_vectors=sample_attenuation_vectors,
        pre_lef_vector=lef_vec,
        pre_lm_vector=lm_vec,
    )

    # JPY run (Scale up loss magnitude and costs by 150x with identical seed)
    engine_jpy = ActuarialRosiEngine(simulations_count=10000, random_seed=42)
    jpy_context = sample_financial_context.model_copy(update={"currency_code": "JPY"})
    jpy_cost_profile = StochasticCostProfile(
        capex_distribution=PertDistributionParams(
            min_val=sample_cost_profile.capex_distribution.min_val * 150.0,
            mode_val=sample_cost_profile.capex_distribution.mode_val * 150.0,
            max_val=sample_cost_profile.capex_distribution.max_val * 150.0,
        ),
        opex_annual_distribution=PertDistributionParams(
            min_val=sample_cost_profile.opex_annual_distribution.min_val * 150.0,
            mode_val=sample_cost_profile.opex_annual_distribution.mode_val * 150.0,
            max_val=sample_cost_profile.opex_annual_distribution.max_val * 150.0,
        ),
    )
    jpy_lm_vec = lm_vec * 150.0

    res_jpy = engine_jpy.evaluate_project_rosi(
        project_id="PROJ-01",
        financial_context=jpy_context,
        cost_profile=jpy_cost_profile,
        attenuation_vectors=sample_attenuation_vectors,
        pre_lef_vector=lef_vec,
        pre_lm_vector=jpy_lm_vec,
    )

    # Currency code is preserved
    assert res_jpy.currency_code == "JPY"
    # Scale invariance: ROSI percentage is mathematically scale-invariant
    assert pytest.approx(res_jpy.rosi_percentage.p50, rel=1e-3) == res_usd.rosi_percentage.p50
    assert pytest.approx(res_jpy.probability_of_positive_return, rel=1e-3) == res_usd.probability_of_positive_return
