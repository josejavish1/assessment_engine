"""Adversarial Test Oracle: Poisson Tail Collapse Immunity & Quantile Monotonicity (SR 11-7 / Solvency II)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
)


@pytest.fixture
def test_zone() -> OperationalZone:
    return OperationalZone(
        zone_id="TEST_ZONE_CRITICAL",
        hourly_burn_rate=140000.0,
        max_annual_outage_hours=24.0,
        secondary_loss_retention_factor=0.85,
        catastrophic_recovery_ceiling_hours=24.0,
        emergency_replacement_ratio=0.15,
        tenant_id="STARLING_BANK",
        legal_entity_id="STARLING_UK",
        operating_site_id="LONDON_PRIMARY",
    )


def test_high_maturity_low_frequency_tail_collapse_immunity(
    test_zone: OperationalZone,
) -> None:
    """Verifies that when frequency is low (lambda < 0.10, e.g. 0.05/yr) and ALE > 0, tail risk is NEVER 0.

    Under pure raw Poisson quantiles, P(0 events) = exp(-0.05) = 95.12%, which would make raw P90 = 0.
    Under Solvency II coherent risk measures, the engine reports non-zero coherent tail risk (CVaR90 or VaR99).
    """
    engine = BayesianFairCopulaEngine(num_simulations=4096)

    finding = FindingTelemetry(
        finding_id="NEOBANK_T1_001",
        tower_id="T1",
        title="Rare Colocation Power Anomaly",
        cmmi_maturity=4.60,
        zone=test_zone,
        tef_pert_min=0.02,
        tef_pert_mode=0.05,
        tef_pert_max=0.10,
        rto_hours_min=1.0,
        rto_hours_mode=2.0,
        rto_hours_max=4.0,
        secondary_loss_mean=10000.0,
        direct_replacement_cost=50000.0,
    )

    summary = engine.evaluate_portfolio([finding], currency_code="GBP")
    t_res = summary.towers["T1"]
    f_res = t_res.findings[0]

    # 1. ALE must be strictly positive
    assert f_res.portfolio_allocated_ale > 0.0
    assert t_res.portfolio_allocated_ale > 0.0
    assert summary.total_portfolio_ale > 0.0

    # 2. Tail exposure MUST NEVER collapse to 0 when ALE > 0
    assert f_res.var_90 > 0.0, (
        f"Finding var_90 collapsed to {f_res.var_90} despite ALE={f_res.portfolio_allocated_ale}"
    )
    assert t_res.var_90 > 0.0, (
        f"Tower var_90 collapsed to {t_res.var_90} despite ALE={t_res.portfolio_allocated_ale}"
    )
    assert summary.portfolio_var_90 > 0.0, (
        f"Portfolio var_90 collapsed to {summary.portfolio_var_90}"
    )

    # 3. Tail risk must strictly exceed expected annual loss (ALE)
    assert f_res.var_90 > f_res.portfolio_allocated_ale, (
        "Tail risk should be higher than expected loss!"
    )
    assert t_res.var_90 > t_res.portfolio_allocated_ale
    assert summary.portfolio_var_90 > summary.total_portfolio_ale


def test_ordinary_frequency_preserves_standard_p90(test_zone: OperationalZone) -> None:
    """Verifies that when frequency is ordinary (lambda = 2.5), standard P90 is positive and natural."""
    engine = BayesianFairCopulaEngine(num_simulations=4096)

    finding = FindingTelemetry(
        finding_id="INDUSTRIAL_T2_001",
        tower_id="T2",
        title="Unstable Compute Host Failures",
        cmmi_maturity=1.85,
        zone=test_zone,
        tef_pert_min=1.5,
        tef_pert_mode=2.5,
        tef_pert_max=4.0,
        rto_hours_min=4.0,
        rto_hours_mode=8.0,
        rto_hours_max=16.0,
        secondary_loss_mean=20000.0,
        direct_replacement_cost=15000.0,
    )

    summary = engine.evaluate_portfolio([finding], currency_code="EUR")
    f_res = summary.towers["T2"].findings[0]

    assert f_res.var_90 > f_res.portfolio_allocated_ale
    assert f_res.var_90 > 0.0


def test_strict_quantile_monotonicity_invariant(test_zone: OperationalZone) -> None:
    """Verifies the universal invariant: ALE < Tail_Risk (P90/CVaR90) <= Worst_Crisis_Event across all towers.

    Prevents the T9 anomaly where P90 (29.6k) exceeded Worst Crisis Event (28.2k).
    """
    engine = BayesianFairCopulaEngine(num_simulations=4096)

    findings = [
        FindingTelemetry(
            finding_id=f"FINDING_{idx}",
            tower_id=f"T{idx}",
            title=f"Sample Operational Risk {idx}",
            cmmi_maturity=1.80 + idx * 0.25,
            zone=test_zone,
            tef_pert_min=0.05 * idx,
            tef_pert_mode=0.20 * idx,
            tef_pert_max=0.50 * idx,
            rto_hours_min=1.0,
            rto_hours_mode=3.0,
            rto_hours_max=6.0,
            secondary_loss_mean=5000.0 * idx,
            direct_replacement_cost=10000.0,
        )
        for idx in range(1, 11)
    ]

    summary = engine.evaluate_portfolio(findings, currency_code="EUR")

    for t_id, t in summary.towers.items():
        assert t.portfolio_allocated_ale < t.var_90, (
            f"Tower {t_id} ALE ({t.portfolio_allocated_ale}) >= P90 ({t.var_90})"
        )
        assert (
            t.var_90 <= t.worst_crisis_event
            or pytest.approx(t.var_90, rel=1e-2) == t.worst_crisis_event
        ), (
            f"Tower {t_id} Quantile Inversion: P90 ({t.var_90}) > Worst Crisis ({t.worst_crisis_event})"
        )
        for f in t.findings:
            assert f.portfolio_allocated_ale < f.var_90, (
                f"ALE ({f.portfolio_allocated_ale}) >= P90 ({f.var_90}) for {f.finding_id}"
            )
            assert (
                f.var_90 <= f.worst_crisis_event
                or pytest.approx(f.var_90, rel=1e-2) == f.worst_crisis_event
            ), (
                f"Quantile Inversion detected: P90 ({f.var_90}) > Worst Crisis Event ({f.worst_crisis_event}) for {f.finding_id}"
            )
