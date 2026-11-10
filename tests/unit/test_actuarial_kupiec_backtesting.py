"""Actuarial Synthetic Quantile Coverage Consistency Test (Kupiec POF Likelihood-Ratio).

Verifies that the Monte Carlo copula simulation kernel achieves nominal quantile coverage
under synthetic pseudo-random sampling.

Note: In accordance with model risk governance (SR 11-7), this test validates the statistical
consistency and implementation coverage of the simulation engine. It does not constitute
historical backtesting against observed real-world loss microdata.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
)


def kupiec_pof_test(
    exceedances: int,
    total_trials: int,
    nominal_p: float,
    significance_level: float = 0.05,
) -> tuple[float, float, bool]:
    """Computes the Kupiec POF Likelihood Ratio test statistic and decision.

    LR_pof = -2 * ln( ((1 - p)^(N - x) * p^x) / ((1 - x/N)^(N - x) * (x/N)^x) ) ~ Chi2(1)
    """
    if total_trials <= 0:
        raise ValueError("total_trials must be positive")
    if exceedances == 0:
        # One-sided zero exceedance test
        lr = -2.0 * (total_trials * math.log(1.0 - nominal_p))
    else:
        p_hat = exceedances / total_trials
        if math.isclose(p_hat, nominal_p, abs_tol=1e-6):
            return 0.0, 1.0, True

        log_num = (total_trials - exceedances) * math.log(1.0 - nominal_p) + exceedances * math.log(nominal_p)
        log_den = (total_trials - exceedances) * math.log(1.0 - p_hat) + exceedances * math.log(p_hat)
        lr = -2.0 * (log_num - log_den)

    p_value = 1.0 - stats.chi2.cdf(lr, df=1)
    passed = bool(p_value > significance_level)
    return float(lr), float(p_value), passed


def test_kupiec_pof_mathematical_oracle() -> None:
    """Verifies that the Kupiec test correctly rejects biased models and accepts well-calibrated quantiles."""
    # Exact nominal: 100 exceedances out of 1000 for 10% (p=0.10)
    lr, p_val, passed = kupiec_pof_test(exceedances=100, total_trials=1000, nominal_p=0.10)
    assert passed, f"Expected pass, got p_val={p_val}"
    assert lr < 3.841

    # Severe underestimation (too many exceedances: 160 out of 1000 for 10%)
    lr_bad, p_val_bad, passed_bad = kupiec_pof_test(exceedances=160, total_trials=1000, nominal_p=0.10)
    assert not passed_bad, f"Expected reject for underestimation, got p_val={p_val_bad}"
    assert lr_bad > 3.841


def test_bayesian_copula_var90_coverage_kupiec() -> None:
    """Certifies that BayesianFairCopulaEngine's VaR90 achieves valid empirical coverage under backtesting."""
    zone = OperationalZone(
        zone_id="ZONE_TEST",
        hourly_burn_rate=10000.0,
        max_annual_outage_hours=48.0,
    )
    findings = [
        FindingTelemetry(
            finding_id="F1",
            tower_id="T1",
            title="Core Database SPOF",
            cmmi_maturity=2.4,
            zone=zone,
            tef_pert_min=0.10,
            tef_pert_mode=0.30,
            tef_pert_max=0.70,
            rto_hours_min=2.0,
            rto_hours_mode=6.0,
            rto_hours_max=14.0,
            secondary_loss_mean=5000.0,
            blast_radius_alpha=0.60,
        ),
        FindingTelemetry(
            finding_id="F2",
            tower_id="T1",
            title="Primary Storage Replication Gap",
            cmmi_maturity=2.8,
            zone=zone,
            tef_pert_min=0.08,
            tef_pert_mode=0.20,
            tef_pert_max=0.50,
            rto_hours_min=1.0,
            rto_hours_mode=4.0,
            rto_hours_max=10.0,
            secondary_loss_mean=3000.0,
            blast_radius_alpha=0.40,
        ),
    ]

    engine = BayesianFairCopulaEngine(num_simulations=4096)
    summary = engine.evaluate_portfolio(findings, currency_code="EUR")

    # Draw out-of-sample test realizations using independent seed
    rng_oos = np.random.default_rng(999)
    n_oos = 1000
    exceedances = 0
    t_result = summary.towers["T1"]
    var_90 = t_result.var_90

    # Simulate out-of-sample operational trials
    for _ in range(n_oos):
        # Draw discrete events
        n1 = rng_oos.poisson(0.30 * ((5.0 - 2.4) / 4.0))
        n2 = rng_oos.poisson(0.20 * ((5.0 - 2.8) / 4.0))
        loss = 0.0
        if n1 > 0:
            loss += n1 * rng_oos.uniform(2.0, 14.0) * 10000.0 * 0.60
        if n2 > 0:
            loss += n2 * rng_oos.uniform(1.0, 10.0) * 10000.0 * 0.40
        if loss > var_90:
            exceedances += 1

    lr, p_val, passed = kupiec_pof_test(
        exceedances=exceedances,
        total_trials=n_oos,
        nominal_p=0.10,
        significance_level=0.05,
    )
    assert passed, f"Kupiec POF test failed at 5% significance: LR={lr:.4f}, p_val={p_val:.4f}, exceedances={exceedances}/{n_oos}"
    assert t_result.cvar_90 >= t_result.var_90, "Coherence violation: CVaR90 must be >= VaR90"
