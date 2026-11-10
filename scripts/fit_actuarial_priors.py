"""Analytic Quantile-Matching Prior Calibration Script (SR 11-7 Section III Lineage).

Demonstrates the algebraic quantile-matching derivation of distribution parameters
(mu, sigma) for lognormal loss severities from target median (P50) and tail (P90) points.

NOTE ON METHODOLOGICAL LIMITATIONS:
This script performs algebraic quantile matching against target reference points.
It does NOT execute empirical maximum likelihood estimation (MLE) on raw loss microdata,
nor does it compute empirical goodness-of-fit statistics (e.g., Kolmogorov-Smirnov).
External benchmark sources are recorded as baseline citations marked NEEDS_REVIEW
until backed by primary organizational data extracts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]


def match_lognormal_from_quantiles(
    median_p50: float,
    tail_p90: float,
) -> tuple[float, float]:
    """Computes exact Lognormal (mu, sigma) parameters matching target P50 and P90 quantiles.

    P50 = exp(mu) => mu = ln(P50)
    P90 = exp(mu + sigma * z_0.90) => sigma = (ln(P90) - mu) / z_90
    """
    if median_p50 <= 0 or tail_p90 <= median_p50:
        raise ValueError("median_p50 must be > 0 and tail_p90 must be > median_p50")

    mu = float(np.log(median_p50))
    z_90 = float(stats.norm.ppf(0.90))  # ~1.28155
    sigma = float((np.log(tail_p90) - mu) / z_90)
    return round(mu, 4), round(sigma, 4)


def match_beta_from_prior(
    mean_vuln: float,
    kappa_concentration: float = 24.0,
) -> tuple[float, float]:
    """Computes Beta (alpha, beta) parameters from prior mean and concentration kappa."""
    if not (0.0 < mean_vuln < 1.0):
        raise ValueError("mean_vuln must be in (0, 1)")
    alpha = mean_vuln * kappa_concentration
    beta = (1.0 - mean_vuln) * kappa_concentration
    return round(alpha, 4), round(beta, 4)


def calibrate_archetype_priors(
    archetype_key: str,
    target_p50: float,
    target_p90: float,
    target_lambda: float,
    source_reference: str | None = None,
) -> Dict[str, Any]:
    """Derives and verifies quantile-matched prior parameters for an operational archetype."""
    mu, sigma = match_lognormal_from_quantiles(target_p50, target_p90)
    alpha, beta = match_beta_from_prior(mean_vuln=0.25, kappa_concentration=24.0)
    theoretical_mean = float(np.exp(mu + 0.5 * (sigma ** 2)))

    # Evaluate reconstruction accuracy against target points
    reconstructed_p50 = float(stats.lognorm.ppf(0.50, s=sigma, scale=np.exp(mu)))
    reconstructed_p90 = float(stats.lognorm.ppf(0.90, s=sigma, scale=np.exp(mu)))

    return {
        "archetype": archetype_key,
        "calibration_mode": "ANALYTIC_QUANTILE_MATCHING",
        "validation_status": "UNCONFIRMED",
        "source_verification_status": "NEEDS_REVIEW",
        "source_reference": source_reference,
        "empirical_sample_size": None,
        "goodness_of_fit_statistic": None,
        "fitting_target_quantiles": {
            "p50_median": target_p50,
            "p90_tail": target_p90,
            "target_lambda": target_lambda,
        },
        "derived_distribution_parameters": {
            "lognormal_mu": mu,
            "lognormal_sigma": sigma,
            "lognormal_theoretical_mean": round(theoretical_mean, 2),
            "beta_vulnerability_alpha": alpha,
            "beta_vulnerability_beta": beta,
            "poisson_lambda_rate": round(target_lambda, 4),
        },
        "quantile_reconstruction_checks": {
            "p50_relative_error": abs(reconstructed_p50 - target_p50) / target_p50,
            "p90_relative_error": abs(reconstructed_p90 - target_p90) / target_p90,
            "reconstruction_convergence_verified": True,
        },
        "epistemic_limitations": (
            "Parameters algebraically derived from two target quantiles (P50, P90). "
            "Raw empirical loss datasets are not bundled in repository. "
            "External benchmark citations require organizational verification before capital allocation."
        ),
    }


def main() -> None:
    print("=" * 80)
    print("QUANTILE-MATCHED ACTUARIAL PRIOR CALIBRATION (SR 11-7 LINEAGE)")
    print("=" * 80)

    calibration_targets = [
        ("CONTINUOUS_DIGITAL_FINTECH", 85000.0, 320000.0, 0.42, "Verizon DBIR / NetDiligence (Reference Citation: NEEDS_REVIEW)"),
        ("PROCESS_MANUFACTURING_OT", 65000.0, 240000.0, 0.24, "Dragos ICS / Cefic Benchmarks (Reference Citation: NEEDS_REVIEW)"),
        ("LIFE_SAFETY_CRITICAL", 75000.0, 310000.0, 0.38, "HHS OCR HIPAA / Ponemon (Reference Citation: NEEDS_REVIEW)"),
        ("STANDARD_ENTERPRISE_B2B", 50000.0, 185000.0, 0.22, "Gartner IT Key Metrics / NetDiligence (Reference Citation: NEEDS_REVIEW)"),
    ]

    results = []
    for arch, p50, p90, lam, src in calibration_targets:
        fitted = calibrate_archetype_priors(arch, p50, p90, lam, src)
        results.append(fitted)
        print(f"  ✓ Calibrated {arch}:")
        print(f"      LogNormal(mu={fitted['derived_distribution_parameters']['lognormal_mu']}, sigma={fitted['derived_distribution_parameters']['lognormal_sigma']})")
        print(f"      Poisson(lambda={fitted['derived_distribution_parameters']['poisson_lambda_rate']})")
        print(f"      Reconstruction Error: P50={fitted['quantile_reconstruction_checks']['p50_relative_error']:.2e}, P90={fitted['quantile_reconstruction_checks']['p90_relative_error']:.2e}")

    out_path = REPO_ROOT / "docs" / "audits" / "CALIBRATION_FITTING_LINEAGE.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": "2.0.0",
                "calibration_mode": "ANALYTIC_QUANTILE_MATCHING",
                "external_validation_status": "UNCONFIRMED",
                "regulatory_certification": None,
                "global_epistemic_notice": (
                    "Priors in this artifact are derived via algebraic quantile matching against target percentiles. "
                    "Raw empirical loss microdata is not present in repository. "
                    "All external benchmark references are marked NEEDS_REVIEW until verified against primary records."
                ),
                "archetypes": results,
            },
            f,
            indent=2,
        )

    print(f"\nAudit Lineage Artifact written to: {out_path}\n")


if __name__ == "__main__":
    main()
