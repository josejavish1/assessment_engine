"""Vectorized Monte Carlo Engine for Coupling Open FAIR Risk with FinOps ROSI (RFC-027).

Designed for high-throughput, zero-hardcoding, multi-tenant execution.
"""

from __future__ import annotations

import logging
import numpy as np

from assessment_engine.domain.schemas.finops_rosi import (
    ControlAttenuationVector,
    DistributionMetrics,
    EnterpriseFinancialContext,
    FairFactorTarget,
    PertDistributionParams,
    RosiActuarialResult,
    StochasticCostProfile,
)

logger = logging.getLogger(__name__)


class ActuarialRosiEngine:
    """Executes coupled pre/post mitigation Monte Carlo simulations to compute
    Stochastic Return on Security Investment (ROSI) and Net Present Value (NPV)."""

    def __init__(self, simulations_count: int = 10000, random_seed: int | None = 42) -> None:
        """Initialize actuarial engine with configured simulation iterations and RNG seed."""
        if simulations_count < 1000:
            raise ValueError("Simulations count must be at least 1,000 for statistical convergence.")
        self.simulations_count = simulations_count
        self.rng = np.random.default_rng(seed=random_seed)

    def _sample_pert(self, params: PertDistributionParams) -> np.ndarray:
        """Generates a vectorized sample of size N from a Beta-PERT distribution.
        Handles degenerate cases (min == max) gracefully without division by zero."""
        if np.isclose(params.min_val, params.max_val):
            return np.full(self.simulations_count, params.mode_val, dtype=np.float64)

        span = params.max_val - params.min_val
        alpha = 1.0 + params.gamma * ((params.mode_val - params.min_val) / span)
        beta = 1.0 + params.gamma * ((params.max_val - params.mode_val) / span)

        beta_samples = self.rng.beta(alpha, beta, size=self.simulations_count)
        return params.min_val + (beta_samples * span)

    @staticmethod
    def _extract_metrics(vector: np.ndarray) -> DistributionMetrics:
        """Computes standard actuarial percentiles and moments from a simulation vector."""
        percentiles = np.percentile(vector, [10, 50, 90, 95])
        return DistributionMetrics(
            mean=float(np.mean(vector)),
            std_dev=float(np.std(vector)),
            p10=float(percentiles[0]),
            p50=float(percentiles[1]),
            p90=float(percentiles[2]),
            p95=float(percentiles[3]),
        )

    @staticmethod
    def _determine_verdict(
        prob_positive: float, median_rosi_pct: float, thresholds: dict[str, float] | None = None
    ) -> str:
        """Classifies the investment based on injected policy thresholds (Zero Hardcoding)."""
        thresh = thresholds or {}
        high_conf_prob = thresh.get("high_confidence_prob", 0.80)
        min_viable_prob = thresh.get("minimum_viable_prob", 0.50)
        high_yield_rosi = thresh.get("high_yield_rosi_pct", 50.0)

        if prob_positive >= high_conf_prob and median_rosi_pct >= high_yield_rosi:
            return "OPTIMAL_HIGH_YIELD_MITIGATION"
        if prob_positive >= min_viable_prob and median_rosi_pct > 0.0:
            return "VIABLE_POSITIVE_RETURN"
        if prob_positive < min_viable_prob and median_rosi_pct <= 0.0:
            return "NET_NEGATIVE_FINANCIAL_RETURN_REQUIRES_COMPLIANCE_JUSTIFICATION"
        return "MARGINAL_BREAK_EVEN_MITIGATION"

    def evaluate_project_rosi(
        self,
        project_id: str,
        financial_context: EnterpriseFinancialContext,
        cost_profile: StochasticCostProfile,
        attenuation_vectors: list[ControlAttenuationVector],
        pre_lef_vector: np.ndarray,
        pre_lm_vector: np.ndarray,
        verdict_thresholds: dict[str, float] | None = None,
    ) -> RosiActuarialResult:
        """Couples pre-mitigation FAIR vectors (LEF, LM) with control attenuation and stochastic TCO."""
        if len(pre_lef_vector) != self.simulations_count or len(pre_lm_vector) != self.simulations_count:
            raise ValueError(
                f"Input FAIR vectors must match engine simulation count ({self.simulations_count})."
            )

        # 1. Pre-Mitigation Baseline ALE
        ale_pre_vec = pre_lef_vector * pre_lm_vector

        # 2. Apply Stochastic Control Attenuation (Compound Multiplicative Damping)
        residual_lef_factor = np.ones(self.simulations_count, dtype=np.float64)
        residual_lm_factor = np.ones(self.simulations_count, dtype=np.float64)

        for control in attenuation_vectors:
            efficacy_samples = self._sample_pert(control.efficacy_distribution)
            retention_rate = np.clip(1.0 - efficacy_samples, 0.0, 1.0)

            if control.target_factor in (FairFactorTarget.TEF, FairFactorTarget.VULN, FairFactorTarget.LEF):
                residual_lef_factor *= retention_rate
            elif control.target_factor in (
                FairFactorTarget.PRIMARY_LOSS,
                FairFactorTarget.SECONDARY_LOSS,
                FairFactorTarget.COMBINED_LM,
            ):
                residual_lm_factor *= retention_rate

        post_lef_vec = pre_lef_vector * residual_lef_factor
        post_lm_vec = pre_lm_vector * residual_lm_factor
        ale_post_vec = post_lef_vec * post_lm_vec

        # 3. Net Risk Reduction (Delta ALE)
        delta_ale_vec = np.maximum(0.0, ale_pre_vec - ale_post_vec)

        # 4. Stochastic FinOps Cost Modeling (Adjusted for Regional PPP & Vertical Complexity)
        scaling_factor = (
            financial_context.regional_purchasing_power_multiplier
            * financial_context.vertical_complexity_multiplier
        )
        raw_capex_vec = self._sample_pert(cost_profile.capex_distribution) * scaling_factor
        raw_opex_vec = self._sample_pert(cost_profile.opex_annual_distribution) * scaling_factor

        horizon = financial_context.amortization_horizon_years
        wacc = financial_context.discount_rate_wacc

        # Annualized TCO = (CapEx / Horizon) + Annual OpEx
        annualized_tco_vec = (raw_capex_vec / float(horizon)) + raw_opex_vec
        safe_tco_vec = np.maximum(annualized_tco_vec, 1e-6)

        # 5. Multi-Year Net Present Value (NPV) Calculation
        discount_factors = np.array([1.0 / ((1.0 + wacc) ** t) for t in range(1, horizon + 1)])
        pv_annuity_factor = float(np.sum(discount_factors))

        npv_cost_vec = raw_capex_vec + (raw_opex_vec * pv_annuity_factor)
        npv_benefit_vec = (delta_ale_vec * pv_annuity_factor) - npv_cost_vec

        # 6. Stochastic ROSI Calculation (in Percentage)
        rosi_ratio_vec = (delta_ale_vec - safe_tco_vec) / safe_tco_vec
        rosi_pct_vec = rosi_ratio_vec * 100.0

        prob_positive = float(np.mean(delta_ale_vec > safe_tco_vec))

        # 7. Payback Period (Months) & Cost of Delay (Monthly Unmitigated Risk Savings Lost)
        monthly_savings_vec = np.maximum(delta_ale_vec / 12.0, 1e-6)
        payback_months_vec = np.clip(raw_capex_vec / monthly_savings_vec, 0.0, 120.0)
        cost_of_delay_monthly_vec = delta_ale_vec / 12.0

        rosi_metrics = self._extract_metrics(rosi_pct_vec)
        verdict = self._determine_verdict(prob_positive, rosi_metrics.p50, verdict_thresholds)

        return RosiActuarialResult(
            project_id=project_id,
            currency_code=financial_context.currency_code,
            simulations_count=self.simulations_count,
            ale_pre_mitigation=self._extract_metrics(ale_pre_vec),
            ale_post_mitigation=self._extract_metrics(ale_post_vec),
            delta_ale_reduction=self._extract_metrics(delta_ale_vec),
            annualized_tco=self._extract_metrics(annualized_tco_vec),
            npv_total_cost=self._extract_metrics(npv_cost_vec),
            npv_net_benefit=self._extract_metrics(npv_benefit_vec),
            rosi_percentage=rosi_metrics,
            probability_of_positive_return=prob_positive,
            payback_period_months=self._extract_metrics(payback_months_vec),
            cost_of_delay_monthly=self._extract_metrics(cost_of_delay_monthly_vec),
            investment_verdict=verdict,
        )
