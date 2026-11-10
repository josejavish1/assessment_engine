"""Property-based verification of actuarial SLE invariants under Hypothesis."""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from assessment_engine.domain.actuarial_calculator import calculate_severity_weighted_sle


@settings(max_examples=100)
@given(
    rto=st.floats(min_value=0.1, max_value=720.0),
    rate=st.floats(min_value=10.0, max_value=500_000.0),
    severity=st.sampled_from(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
    is_spof=st.booleans(),
)
def test_sle_non_negativity_and_positivity(
    rto: float, rate: float, severity: str, is_spof: bool
) -> None:
    """Axiom 1: Single Loss Expectancy is strictly non-negative and positive for non-zero inputs."""
    sle, alpha, repl, sec = calculate_severity_weighted_sle(rto, rate, severity, is_spof)

    assert sle > 0.0
    assert 0.0 < alpha <= 1.0
    assert repl >= 0.0
    assert sec >= 0.0
    assert sle == pytest.approx((rto * alpha * rate) + repl + sec, rel=1e-6)


@settings(max_examples=100)
@given(
    rto=st.floats(min_value=1.0, max_value=48.0),
    rate=st.floats(min_value=100.0, max_value=50_000.0),
    factor=st.floats(min_value=1.1, max_value=10.0),
)
def test_sle_degree_one_homogeneity_scale_invariance(
    rto: float, rate: float, factor: float
) -> None:
    """Axiom 2: Homogeneity of Degree One. Scaling operational hourly rate scales SLE proportionally."""
    sle_base, _, _, _ = calculate_severity_weighted_sle(rto, rate, "HIGH", is_spof=False)
    sle_scaled, _, _, _ = calculate_severity_weighted_sle(rto, rate * factor, "HIGH", is_spof=False)

    assert pytest.approx(sle_scaled, rel=1e-5) == sle_base * factor


@settings(max_examples=100)
@given(
    rto=st.floats(min_value=1.0, max_value=100.0),
    rate=st.floats(min_value=100.0, max_value=100_000.0),
)
def test_sle_severity_monotonicity(rto: float, rate: float) -> None:
    """Axiom 3: Monotonicity. Higher severity guarantees strictly greater or equal single loss exposure."""
    sle_crit, _, _, _ = calculate_severity_weighted_sle(rto, rate, "CRITICAL", is_spof=False)
    sle_high, _, _, _ = calculate_severity_weighted_sle(rto, rate, "HIGH", is_spof=False)
    sle_med, _, _, _ = calculate_severity_weighted_sle(rto, rate, "MEDIUM", is_spof=False)
    sle_low, _, _, _ = calculate_severity_weighted_sle(rto, rate, "LOW", is_spof=False)

    assert sle_crit >= sle_high >= sle_med >= sle_low
