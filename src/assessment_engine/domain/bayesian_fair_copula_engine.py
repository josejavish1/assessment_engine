"""Enterprise Quantitative Risk Engine (Open FAIR™ + FAIR-CAM + Student-t Copula).

Target: Assessment Engine Production (Global Tier-1 Multi-Tenant Standard)
Architecture: Hexagonal / Clean Architecture (Domain Core & Application Service)

Implements:
1. Physical Single Loss Expectancy (SLE_max) based on failure physics and operational ceilings (eradicates legacy magic multipliers).
2. Bayesian Prior Shifting and empirical RTO inflation driven by Epistemic Dissonance records.
3. Strictly Positive-Definite Two-Factor Student-t Copula with spectral floor projection.
4. Pathwise Aumann-Shapley / Euler sub-additive allocation across shared operational zones with blast radius preservation.

Strictly 100% Technical English, zero hardcoding, multi-tenant and vertical-agnostic.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

import numpy as np
from scipy import stats


# 1. DOMAIN LAYER: ENTITIES & VALUE OBJECTS (INDUSTRY & CURRENCY AGNOSTIC)

@dataclass(frozen=True)
class TenantFinancialTelemetry:
    """Contract for enterprise financial and operational scale telemetry."""

    annual_revenue: float
    currency_code: str
    operational_hours_per_year: float = 8760.0
    consolidated_hourly_downtime_rate: Optional[float] = None
    local_facility_hourly_rate: Optional[float] = None
    emergency_response_hourly_rate: Optional[float] = None


@dataclass(frozen=True)
class EpistemicDissonanceRecord:
    """Forensic contradiction record between self-reported questionnaire and live interview transcript."""

    record_id: str
    finding_id: str
    claimed_maturity: float
    empirical_reality_maturity: float
    dissonance_weight: float  # Normalized Bayesian precision weight [0.0 to 1.0]
    transcript_evidence_quote: str = ""
    impact_vector: str = "BOTH"  # "VULNERABILITY", "RECOVERY_TIME", "BOTH"


@dataclass(frozen=True)
class OperationalZone:
    """Logical or operational tier with calibrated outage burn rate and capacity cap."""

    zone_id: str
    hourly_burn_rate: float
    max_annual_outage_hours: float
    secondary_loss_retention_factor: float = 0.85
    catastrophic_recovery_ceiling_hours: float = 24.0
    emergency_replacement_ratio: float = 0.25

    def __post_init__(self) -> None:
        if self.hourly_burn_rate < 0.0:
            raise ValueError(f"hourly_burn_rate must be non-negative for zone '{self.zone_id}'.")
        if self.max_annual_outage_hours <= 0.0:
            raise ValueError(f"max_annual_outage_hours must be strictly positive for zone '{self.zone_id}'.")
        if not (0.0 <= self.secondary_loss_retention_factor <= 1.0):
            raise ValueError(
                f"secondary_loss_retention_factor must be in [0.0, 1.0] for zone '{self.zone_id}'."
            )
        if self.catastrophic_recovery_ceiling_hours <= 0.0:
            raise ValueError(
                f"catastrophic_recovery_ceiling_hours must be strictly positive for zone '{self.zone_id}'."
            )
        if not (0.0 <= self.emergency_replacement_ratio <= 1.0):
            raise ValueError(
                f"emergency_replacement_ratio must be in [0.0, 1.0] for zone '{self.zone_id}'."
            )


@dataclass(frozen=True)
class FindingTelemetry:
    """Normalized actuarial input telemetry for a single architectural finding."""

    finding_id: str
    tower_id: str
    title: str
    cmmi_maturity: float                  # Claimed or baseline control maturity [1.00 to 5.00]
    zone: OperationalZone
    tef_pert_min: float                   # Threat Event Frequency (PERT min)
    tef_pert_mode: float                  # Threat Event Frequency (PERT mode)
    tef_pert_max: float                   # Threat Event Frequency (PERT max)
    rto_hours_min: float                  # Recovery Time Objective (PERT min)
    rto_hours_mode: float                 # Recovery Time Objective (PERT mode)
    rto_hours_max: float                  # Recovery Time Objective (PERT max)
    secondary_loss_mean: float            # Expected Secondary Loss Magnitude per event
    is_spof: bool = False                 # Single Point of Failure flag
    shared_dependence_factor: float = 0.5 # Systemic correlation loading (0.0 to 0.85)
    blast_radius_alpha: float = 0.35      # Operational impact factor alpha in [0.05, 1.0]
    catastrophic_rto_hours: float = 24.0  # Physical ceiling recovery time under full control failure
    direct_replacement_cost: float = 0.0  # Emergency hardware / forensic response cost
    audit_k_failures: int = 0             # Observed control deficiencies from audit evidence
    audit_n_trials: int = 0               # Total evaluated controls/evidence items
    dissonance: Optional[EpistemicDissonanceRecord] = None


@dataclass(frozen=True)
class FindingRiskResult:
    """Actuarial simulation output for an individual finding."""

    finding_id: str
    title: str
    cmmi_maturity: float
    mean_vuln: float
    mean_lef: float
    mean_sle: float
    standalone_ale: float
    portfolio_allocated_ale: float
    var_90: float
    cvar_90: float
    var_95: float
    var_99: float
    cvar_99: float
    worst_crisis_event: float = 0.0       # Physical Single Loss Expectancy (SLE_max)
    worst_crisis_rto_hours: float = 0.0   # Physical recovery hours under worst-case disaster
    dissonance_applied: bool = False


@dataclass(frozen=True)
class TowerRiskResult:
    """Aggregated and sub-additively allocated risk metrics for an architectural tower."""

    tower_id: str
    weighted_cmmi: float
    standalone_ale: float                 # Raw bottom-up expectation (Technical Annex)
    portfolio_allocated_ale: float        # Coherent sub-additive allocation (Executive Summary)
    primary_ale: float                    # Allocated primary operational downtime loss
    secondary_ale: float                  # Allocated secondary response/regulatory/SLA loss
    var_90: float                         # 90th Percentile Value at Risk
    cvar_90: float                        # 90th Percentile Expected Shortfall (CVaR)
    var_95: float                         # 95th Percentile Value at Risk
    var_99: float                         # 99th Percentile Value at Risk
    cvar_99: float                        # 99th Percentile Expected Shortfall (CVaR)
    diversification_benefit: float        # standalone_ale - portfolio_allocated_ale
    findings: List[FindingRiskResult]
    worst_crisis_event: float = 0.0       # Physical Single Loss Expectancy (SLE_max) of worst disaster
    worst_crisis_rto_hours: float = 0.0   # Physical recovery hours of worst disaster


@dataclass(frozen=True)
class PortfolioRiskSummary:
    """Enterprise-wide convolved risk summary across all evaluated towers."""

    deterministic_seed_hash: str
    currency_code: str
    total_standalone_sum: float
    total_portfolio_ale: float            # Sub-additive Copula Convolved ALE (Executive Headline)
    total_primary_ale: float              # Convolved primary operational downtime loss
    total_secondary_ale: float            # Convolved secondary response & SLA loss
    three_year_cost_of_inaction: float    # 3-year baseline cumulative exposure
    portfolio_var_90: float               # 90% Value at Risk
    portfolio_cvar_90: float              # 90% Expected Shortfall
    portfolio_var_95: float               # 95% Value at Risk
    portfolio_var_99: float               # 99% Catastrophic Value at Risk
    portfolio_cvar_99: float              # 99% Catastrophic Expected Shortfall
    diversification_ratio: float
    towers: Dict[str, TowerRiskResult]


# 2. PORTS (INTERFACES)

class RiskQuantificationPort(Protocol):
    """Primary Port for hydrating Tower and Portfolio financial telemetry."""

    def evaluate_portfolio(
        self, findings: List[FindingTelemetry], currency_code: str
    ) -> PortfolioRiskSummary:
        """Evaluates portfolio risk across finding telemetry and returns aggregated summary."""
        ...



class BayesianFairCopulaEngine(RiskQuantificationPort):
    """Actuarial Quantitative Risk Engine.

    - Calibrates VULN dynamically from CMMI maturity via non-linear Beta distributions with Bayesian Dissonance Shifting.
    - Couples cross-domain losses via a strictly Positive-Definite Two-Factor Student-t Copula.
    - Enforces physical operational downtime absorbing barriers per operational zone with blast radius preservation.
    - Derives worst-case catastrophic crisis events from physical SLE bounds (zero magic multipliers).
    - Performs exact pathwise Aumann-Shapley / Euler sub-additive allocation.
    """

    def __init__(
        self,
        num_simulations: int = 16384,
        vuln_min: float = 0.02,
        vuln_max: float = 0.95,
        vuln_convexity_gamma: float = 1.65,
        beta_concentration_kappa: float = 20.0,
        copula_df: int = 4,
        intra_tower_correlation_boost: float = 0.20,
        secondary_loss_cv: float = 0.50,
        inaction_horizon_years: float = 3.0,
        spof_cmmi_penalty: float = 0.50,
        max_dependence_loading: float = 0.85,
        max_copula_correlation: float = 0.92,
        rto_cmmi_degradation_slope: float = 0.35,
        rto_spof_multiplier: float = 0.40,
        catastrophic_tail_quantile: float = 95.0,
    ):
        if num_simulations < 64:
            raise ValueError("num_simulations must be at least 64 for statistical convergence.")
        if copula_df < 2:
            raise ValueError("copula_df must be >= 2.")
        if not (50.0 <= catastrophic_tail_quantile < 100.0):
            raise ValueError("catastrophic_tail_quantile must be in [50.0, 100.0).")

        self.n_sims = num_simulations
        self.vuln_min = vuln_min
        self.vuln_max = vuln_max
        self.gamma = vuln_convexity_gamma
        self.kappa = beta_concentration_kappa
        self.copula_df = copula_df
        self.intra_tower_boost = intra_tower_correlation_boost
        self.secondary_loss_cv = secondary_loss_cv
        self.inaction_horizon_years = inaction_horizon_years
        self.spof_cmmi_penalty = float(spof_cmmi_penalty)
        self.max_dependence_loading = float(max_dependence_loading)
        self.max_copula_correlation = float(max_copula_correlation)
        self.rto_cmmi_degradation_slope = float(rto_cmmi_degradation_slope)
        self.rto_spof_multiplier = float(rto_spof_multiplier)
        self.catastrophic_tail_quantile = float(catastrophic_tail_quantile)

    def _compute_deterministic_seed(self, findings: List[FindingTelemetry]) -> tuple[int, str]:
        """Generates a deterministic 32-bit integer seed from the complete parameter vector."""
        canonical_parts: List[str] = []
        for f in sorted(findings, key=lambda x: (x.tower_id, x.finding_id)):
            diss_token = (
                f"{f.dissonance.record_id}:{f.dissonance.claimed_maturity:.4f}:"
                f"{f.dissonance.empirical_reality_maturity:.4f}:"
                f"{f.dissonance.dissonance_weight:.4f}:{f.dissonance.impact_vector}"
                if f.dissonance
                else "NONE"
            )
            canonical_parts.append(
                f"{f.finding_id}:{f.tower_id}:{f.cmmi_maturity:.4f}:"
                f"{f.tef_pert_min:.4f}:{f.tef_pert_mode:.4f}:{f.tef_pert_max:.4f}:"
                f"{f.rto_hours_min:.4f}:{f.rto_hours_mode:.4f}:{f.rto_hours_max:.4f}:"
                f"{f.secondary_loss_mean:.2f}:{f.zone.zone_id}:{f.zone.hourly_burn_rate:.2f}:"
                f"{f.zone.max_annual_outage_hours:.2f}:{f.zone.catastrophic_recovery_ceiling_hours:.2f}:"
                f"{f.zone.emergency_replacement_ratio:.4f}:{int(f.is_spof)}:"
                f"{f.shared_dependence_factor:.4f}:{f.blast_radius_alpha:.4f}:"
                f"{f.catastrophic_rto_hours:.2f}:{f.direct_replacement_cost:.2f}:"
                f"{f.audit_k_failures}:{f.audit_n_trials}:{diss_token}"
            )
        canonical_str = "|".join(canonical_parts)
        sha_hex = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        seed_int = int(sha_hex[:8], 16)
        return seed_int, sha_hex[:16]

    def _resolve_posterior_cmmi(
        self,
        base_cmmi: float,
        dissonance: Optional[EpistemicDissonanceRecord],
        target_vectors: tuple[str, ...],
    ) -> tuple[float, bool]:
        """Performs precision-weighted Bayesian prior shifting between claimed and empirical maturity."""
        prior_cmmi = float(np.clip(base_cmmi, 1.0, 5.0))
        if (
            dissonance is not None
            and dissonance.dissonance_weight > 0.0
            and dissonance.impact_vector in target_vectors
        ):
            w = float(np.clip(dissonance.dissonance_weight, 0.0, 1.0))
            empirical_cmmi = float(np.clip(dissonance.empirical_reality_maturity, 1.0, 5.0))
            posterior_cmmi = (1.0 - w) * prior_cmmi + w * empirical_cmmi
            return float(np.clip(posterior_cmmi, 1.0, 5.0)), True
        return prior_cmmi, False

    def _calibrate_fair_cam_vuln(
        self,
        cmmi: float,
        is_spof: bool,
        u_samples: np.ndarray,
        dissonance: Optional[EpistemicDissonanceRecord] = None,
        audit_k_failures: int = 0,
        audit_n_trials: int = 0,
    ) -> tuple[np.ndarray, float, bool]:
        """Maps posterior CMMI and empirical audit evidence -> Beta(alpha, beta) -> VULN samples via Inverse CDF."""
        posterior_cmmi, dissonance_applied = self._resolve_posterior_cmmi(
            cmmi, dissonance, ("VULNERABILITY", "BOTH")
        )
        effective_cmmi = float(
            np.clip(posterior_cmmi - (self.spof_cmmi_penalty if is_spof else 0.0), 1.0, 5.0)
        )
        mu_vuln = self.vuln_min + (self.vuln_max - self.vuln_min) * (
            (5.0 - effective_cmmi) / 4.0
        ) ** self.gamma

        mu_vuln = float(np.clip(mu_vuln, 0.01, 0.99))
        alpha_0 = mu_vuln * self.kappa
        beta_0 = (1.0 - mu_vuln) * self.kappa

        # Beta-Binomial Conjugate Update (Open FAIR™ / O-RA standard):
        # Audit deficiencies (k_failures) and successes (n_trials - k_failures) modulate control resistance
        if audit_n_trials > 0:
            k = max(0, min(audit_k_failures, audit_n_trials))
            n = max(k, audit_n_trials)
            alpha_post = alpha_0 + float(k)
            beta_post = beta_0 + float(n - k)
        else:
            alpha_post = alpha_0
            beta_post = beta_0

        vuln_samples = stats.beta.ppf(u_samples, alpha_post, beta_post)
        mu_vuln_post = float(alpha_post / (alpha_post + beta_post))
        return vuln_samples, mu_vuln_post, dissonance_applied

    @staticmethod
    def _cvar(arr: np.ndarray, pct: float = 90.0) -> float:
        """Computes exact empirical Conditional Value-at-Risk (Expected Shortfall) at percentile pct

        in (0, 100) using the Rockafellar-Uryasev index-ordered sorted tail definition.
        Immune to zero-inflated discrete distributions where VaR_pct == 0.
        """
        if arr.size == 0:
            return 0.0
        alpha = pct / 100.0
        if alpha <= 0.0:
            return float(np.mean(arr))
        if alpha >= 1.0:
            return float(np.max(arr))

        sorted_arr = np.sort(arr)
        n = sorted_arr.size
        exact_idx = n * alpha
        k = int(np.floor(exact_idx))

        tail_mass = n * (1.0 - alpha)
        if k >= n:
            return float(sorted_arr[-1])

        fractional_weight = (k + 1.0) - exact_idx
        weighted_sum = fractional_weight * sorted_arr[k]
        if k + 1 < n:
            weighted_sum += float(np.sum(sorted_arr[k + 1 :]))

        return float(weighted_sum / tail_mass)

    @staticmethod
    def _sample_pert(
        min_val: float, mode_val: float, max_val: float, u_samples: np.ndarray
    ) -> np.ndarray:
        """Inverse transform sampling for the Modified PERT distribution."""
        safe_min = max(0.0, float(min_val))
        safe_max = max(safe_min, float(max_val))
        if safe_max <= safe_min + 1e-12:
            return np.full_like(u_samples, safe_min, dtype=np.float64)
        mode_clamped = float(np.clip(mode_val, safe_min, safe_max))
        span = safe_max - safe_min
        alpha = 1.0 + 4.0 * (mode_clamped - safe_min) / span
        beta_p = 1.0 + 4.0 * (safe_max - mode_clamped) / span
        return safe_min + stats.beta.ppf(u_samples, alpha, beta_p) * span

    def _generate_student_t_copula_uniforms(
        self, findings: List[FindingTelemetry], rng: np.random.Generator
    ) -> np.ndarray:
        """Constructs a strictly Positive-Definite correlation matrix via a Two-Factor Loading

        structure (Systemic + Orthogonal Tower Factor) with spectral floor safeguard.
        """
        n_f = len(findings)
        if n_f == 1:
            z = rng.standard_normal(size=(self.n_sims, 1))
            chi2_samples = rng.chisquare(df=self.copula_df, size=(self.n_sims, 1))
            t_samples = z / np.sqrt(chi2_samples / self.copula_df)
            return np.clip(stats.t.cdf(t_samples, df=self.copula_df), 1e-6, 1.0 - 1e-6)

        loadings = np.clip(
            np.array([f.shared_dependence_factor for f in findings], dtype=np.float64),
            0.0,
            self.max_dependence_loading,
        )
        corr_matrix = np.outer(loadings, loadings)

        for i in range(n_f):
            for j in range(i + 1, n_f):
                if findings[i].tower_id == findings[j].tower_id:
                    rem_var = np.sqrt((1.0 - loadings[i] ** 2) * (1.0 - loadings[j] ** 2))
                    corr_ij = corr_matrix[i, j] + self.intra_tower_boost * rem_var
                    corr_matrix[i, j] = corr_matrix[j, i] = min(
                        self.max_copula_correlation, corr_ij
                    )

        np.fill_diagonal(corr_matrix, 1.0)

        # Spectral projection safeguard to guarantee strict Positive Definiteness
        eigvals, eigvecs = np.linalg.eigh(corr_matrix)
        if np.any(eigvals < 1e-6):
            eigvals = np.maximum(eigvals, 1e-6)
            corr_matrix = eigvecs @ np.diag(eigvals) @ eigvecs.T
            inv_std = np.diag(1.0 / np.sqrt(np.diag(corr_matrix)))
            corr_matrix = inv_std @ corr_matrix @ inv_std
            np.fill_diagonal(corr_matrix, 1.0)

        chol = np.linalg.cholesky(corr_matrix)
        z = rng.standard_normal(size=(self.n_sims, n_f))
        correlated_normals = z @ chol.T

        chi2_samples = rng.chisquare(df=self.copula_df, size=(self.n_sims, 1))
        t_samples = correlated_normals / np.sqrt(chi2_samples / self.copula_df)
        u_copula = stats.t.cdf(t_samples, df=self.copula_df)
        return np.clip(u_copula, 1e-6, 1.0 - 1e-6)

    def evaluate_portfolio(
        self, findings: List[FindingTelemetry], currency_code: str
    ) -> PortfolioRiskSummary:
        """Evaluate cross-domain portfolio loss distribution under copula correlation."""
        if not findings:
            raise ValueError("Cannot evaluate an empty findings list.")
        if not currency_code or not currency_code.strip():
            raise ValueError("A valid ISO currency_code must be provided.")

        normalized_currency = currency_code.strip().upper()
        seed_int, seed_hash = self._compute_deterministic_seed(findings)
        rng = np.random.default_rng(seed_int)
        n_f = len(findings)

        u_copula = self._generate_student_t_copula_uniforms(findings, rng)
        u_aux_vuln = rng.uniform(1e-5, 1.0 - 1e-5, size=(self.n_sims, n_f))
        u_aux_rto = rng.uniform(1e-5, 1.0 - 1e-5, size=(self.n_sims, n_f))
        u_aux_sec = rng.uniform(1e-5, 1.0 - 1e-5, size=(self.n_sims, n_f))

        finding_raw_losses = np.zeros((self.n_sims, n_f), dtype=np.float64)
        finding_equivalent_zone_hours = np.zeros((self.n_sims, n_f), dtype=np.float64)
        finding_secondary_losses = np.zeros((self.n_sims, n_f), dtype=np.float64)
        finding_crisis_events = np.zeros(n_f, dtype=np.float64)
        finding_crisis_hours = np.zeros(n_f, dtype=np.float64)
        finding_dissonance_flags = [False] * n_f

        mean_vulns = np.zeros(n_f)
        mean_lefs = np.zeros(n_f)
        mean_sles = np.zeros(n_f)

        sigma_sec = float(np.sqrt(np.log(1.0 + self.secondary_loss_cv ** 2)))

        # 1. Marginal Evaluation per Finding
        for idx, f in enumerate(findings):
            tef_samples = self._sample_pert(
                f.tef_pert_min, f.tef_pert_mode, f.tef_pert_max, u_copula[:, idx]
            )
            vuln_samples, mu_vuln, diss_vuln_applied = self._calibrate_fair_cam_vuln(
                f.cmmi_maturity,
                f.is_spof,
                u_aux_vuln[:, idx],
                f.dissonance,
                f.audit_k_failures,
                f.audit_n_trials,
            )
            # Doubly-Stochastic Poisson Process (Cox Model):
            # Draw event counts independently conditional on intensity rates lambda_rates
            # to eliminate artificial intensity-count collinearity bias (resolving Blocker 1)
            lambda_rates = tef_samples * vuln_samples
            event_counts = rng.poisson(lam=lambda_rates).astype(np.int64)

            rto_sampled = self._sample_pert(
                f.rto_hours_min, f.rto_hours_mode, f.rto_hours_max, u_aux_rto[:, idx]
            )

            posterior_rto_cmmi, diss_rto_applied = self._resolve_posterior_cmmi(
                f.cmmi_maturity, f.dissonance, ("RECOVERY_TIME", "BOTH")
            )
            finding_dissonance_flags[idx] = diss_vuln_applied or diss_rto_applied

            physical_ceiling_hours = max(
                float(f.rto_hours_max),
                float(f.catastrophic_rto_hours),
                float(f.zone.catastrophic_recovery_ceiling_hours),
            )

            if diss_rto_applied and f.dissonance is not None:
                w_rto = float(np.clip(f.dissonance.dissonance_weight, 0.0, 1.0))
                maturity_deficit_ratio = (5.0 - posterior_rto_cmmi) / 4.0
                shift_fraction = w_rto * maturity_deficit_ratio
                rto_sampled = rto_sampled + (physical_ceiling_hours - rto_sampled) * shift_fraction

            degradation_mult = (
                1.0
                + self.rto_cmmi_degradation_slope * max(0.0, 3.0 - posterior_rto_cmmi)
                + (self.rto_spof_multiplier if f.is_spof else 0.0)
            )
            effective_rto = np.minimum(rto_sampled * degradation_mult, physical_ceiling_hours)

            if f.secondary_loss_mean > 0.0:
                mu_sec = np.log(f.secondary_loss_mean) - 0.5 * (sigma_sec ** 2)
                sec_sle_samples = stats.lognorm.ppf(
                    u_aux_sec[:, idx], s=sigma_sec, scale=np.exp(mu_sec)
                )
            else:
                sec_sle_samples = np.zeros(self.n_sims, dtype=np.float64)

            # Apply blast radius alpha to operational hourly burn rate
            alpha_effective = float(np.clip(f.blast_radius_alpha, 0.05, 1.0))
            effective_hourly_rate = f.zone.hourly_burn_rate * alpha_effective

            annual_downtime_s = event_counts * effective_rto
            safe_replacement_cost = max(0.0, float(f.direct_replacement_cost))
            replacement_loss_s = event_counts * safe_replacement_cost
            primary_loss_s = (annual_downtime_s * effective_hourly_rate) + replacement_loss_s
            secondary_loss_s = event_counts * sec_sle_samples

            # Equivalent full-zone outage hours preserve blast_radius_alpha during zone convolution
            finding_equivalent_zone_hours[:, idx] = annual_downtime_s * alpha_effective
            finding_secondary_losses[:, idx] = secondary_loss_s
            finding_raw_losses[:, idx] = primary_loss_s + secondary_loss_s

            mean_vulns[idx] = mu_vuln
            mean_lefs[idx] = float(np.mean(lambda_rates))
            mean_sles[idx] = float(
                np.mean(
                    effective_rto * effective_hourly_rate
                    + sec_sle_samples
                    + safe_replacement_cost
                )
            )

            # Physical Worst-Case Single Loss Expectancy (SLE_max) under catastrophic failure (zero magic multipliers)
            catastrophic_hours = float(
                np.percentile(effective_rto, self.catastrophic_tail_quantile)
            )
            catastrophic_secondary = (
                float(np.percentile(sec_sle_samples, self.catastrophic_tail_quantile))
                if f.secondary_loss_mean > 0.0
                else 0.0
            )
            effective_replacement_cost = (
                safe_replacement_cost
                if safe_replacement_cost > 0.0
                else (
                    catastrophic_hours
                    * effective_hourly_rate
                    * f.zone.emergency_replacement_ratio
                    if f.is_spof
                    else 0.0
                )
            )
            finding_crisis_events[idx] = (
                (catastrophic_hours * effective_hourly_rate)
                + effective_replacement_cost
                + catastrophic_secondary
            )
            finding_crisis_hours[idx] = catastrophic_hours

        # 2. Sub-Additive Operational Zone Convolution & Pathwise Aumann-Shapley Allocation
        portfolio_primary_losses = np.zeros(self.n_sims, dtype=np.float64)
        portfolio_convolved_losses = np.zeros(self.n_sims, dtype=np.float64)
        allocated_finding_sim_primary = np.zeros((self.n_sims, n_f), dtype=np.float64)
        allocated_finding_sim_secondary = np.zeros((self.n_sims, n_f), dtype=np.float64)

        unique_zones = {f.zone.zone_id: f.zone for f in findings}
        for z_id, zone in unique_zones.items():
            zone_indices = [i for i, f in enumerate(findings) if f.zone.zone_id == z_id]
            raw_zone_eq_hours = np.sum(
                finding_equivalent_zone_hours[:, zone_indices], axis=1
            )

            h_max = max(1e-6, zone.max_annual_outage_hours)
            effective_zone_hours = h_max * (1.0 - np.exp(-raw_zone_eq_hours / h_max))
            zone_primary_loss = effective_zone_hours * zone.hourly_burn_rate
            portfolio_primary_losses += zone_primary_loss
            portfolio_convolved_losses += zone_primary_loss

            safe_denom = np.where(raw_zone_eq_hours > 1e-12, raw_zone_eq_hours, 1.0)
            for i in zone_indices:
                share_s = np.where(
                    raw_zone_eq_hours > 1e-12,
                    finding_equivalent_zone_hours[:, i] / safe_denom,
                    0.0,
                )
                allocated_finding_sim_primary[:, i] += zone_primary_loss * share_s

        # Convolve retained secondary losses into portfolio total
        retained_secondary_losses = np.zeros(self.n_sims, dtype=np.float64)
        for i in range(n_f):
            retained_i = (
                finding_secondary_losses[:, i] * findings[i].zone.secondary_loss_retention_factor
            )
            allocated_finding_sim_secondary[:, i] = retained_i
            retained_secondary_losses += retained_i

        portfolio_convolved_losses += retained_secondary_losses
        allocated_finding_sim_losses = (
            allocated_finding_sim_primary + allocated_finding_sim_secondary
        )

        # 3. Aggregate Expectations and Quantiles
        total_primary_ale = float(np.mean(portfolio_primary_losses))
        total_secondary_ale = float(np.mean(retained_secondary_losses))
        total_portfolio_ale = float(np.mean(portfolio_convolved_losses))

        standalone_finding_ales = np.mean(finding_raw_losses, axis=0)
        allocated_finding_ales = np.mean(allocated_finding_sim_losses, axis=0)
        total_standalone_sum = float(np.sum(standalone_finding_ales))

        towers_dict: Dict[str, TowerRiskResult] = {}
        unique_towers = sorted({f.tower_id for f in findings})

        for t_id in unique_towers:
            t_indices = [i for i, f in enumerate(findings) if f.tower_id == t_id]
            t_alloc_sim_sum = np.sum(allocated_finding_sim_losses[:, t_indices], axis=1)

            t_standalone_ale = float(np.sum(standalone_finding_ales[t_indices]))
            t_allocated_ale = float(np.sum(allocated_finding_ales[t_indices]))
            t_primary_ale = float(
                np.sum(np.mean(allocated_finding_sim_primary[:, t_indices], axis=0))
            )
            t_secondary_ale = float(
                np.sum(np.mean(allocated_finding_sim_secondary[:, t_indices], axis=0))
            )

            # Physical Worst Crisis Event is the maximum catastrophic SLE among the tower's findings
            worst_f_subidx = int(np.argmax(finding_crisis_events[t_indices]))
            worst_f_idx = t_indices[worst_f_subidx]
            t_worst_crisis = float(finding_crisis_events[worst_f_idx])
            t_worst_hours = float(finding_crisis_hours[worst_f_idx])

            t_var_90 = float(np.percentile(t_alloc_sim_sum, 90))
            t_cvar_90 = self._cvar(t_alloc_sim_sum, 90.0)
            t_var_95 = float(np.percentile(t_alloc_sim_sum, 95))
            t_var_99 = float(np.percentile(t_alloc_sim_sum, 99))
            t_cvar_99 = self._cvar(t_alloc_sim_sum, 99.0)

            cmmi_vec = np.array([findings[i].cmmi_maturity for i in t_indices], dtype=np.float64)
            weights_vec = standalone_finding_ales[t_indices]
            if np.sum(weights_vec) > 1e-9:
                t_cmmi = float(np.average(cmmi_vec, weights=weights_vec))
            else:
                t_cmmi = float(np.mean(cmmi_vec))

            f_results = [
                FindingRiskResult(
                    finding_id=findings[i].finding_id,
                    title=findings[i].title,
                    cmmi_maturity=findings[i].cmmi_maturity,
                    mean_vuln=round(float(mean_vulns[i]), 4),
                    mean_lef=round(float(mean_lefs[i]), 3),
                    mean_sle=round(float(mean_sles[i]), 2),
                    standalone_ale=round(float(standalone_finding_ales[i]), 2),
                    portfolio_allocated_ale=round(float(allocated_finding_ales[i]), 2),
                    var_90=round(float(np.percentile(allocated_finding_sim_losses[:, i], 90)), 2),
                    cvar_90=round(self._cvar(allocated_finding_sim_losses[:, i], 90.0), 2),
                    var_95=round(float(np.percentile(allocated_finding_sim_losses[:, i], 95)), 2),
                    var_99=round(float(np.percentile(allocated_finding_sim_losses[:, i], 99)), 2),
                    cvar_99=round(self._cvar(allocated_finding_sim_losses[:, i], 99.0), 2),
                    worst_crisis_event=round(float(finding_crisis_events[i]), 2),
                    worst_crisis_rto_hours=round(float(finding_crisis_hours[i]), 2),
                    dissonance_applied=finding_dissonance_flags[i],
                )
                for i in t_indices
            ]

            towers_dict[t_id] = TowerRiskResult(
                tower_id=t_id,
                weighted_cmmi=round(t_cmmi, 2),
                standalone_ale=round(t_standalone_ale, 2),
                portfolio_allocated_ale=round(t_allocated_ale, 2),
                primary_ale=round(t_primary_ale, 2),
                secondary_ale=round(t_secondary_ale, 2),
                var_90=round(t_var_90, 2),
                cvar_90=round(t_cvar_90, 2),
                var_95=round(t_var_95, 2),
                var_99=round(t_var_99, 2),
                cvar_99=round(t_cvar_99, 2),
                diversification_benefit=round(t_standalone_ale - t_allocated_ale, 2),
                findings=f_results,
                worst_crisis_event=round(t_worst_crisis, 2),
                worst_crisis_rto_hours=round(t_worst_hours, 2),
            )

        return PortfolioRiskSummary(
            deterministic_seed_hash=seed_hash,
            currency_code=normalized_currency,
            total_standalone_sum=round(total_standalone_sum, 2),
            total_portfolio_ale=round(total_portfolio_ale, 2),
            total_primary_ale=round(total_primary_ale, 2),
            total_secondary_ale=round(total_secondary_ale, 2),
            three_year_cost_of_inaction=round(
                total_portfolio_ale * self.inaction_horizon_years, 2
            ),
            portfolio_var_90=round(float(np.percentile(portfolio_convolved_losses, 90)), 2),
            portfolio_cvar_90=round(self._cvar(portfolio_convolved_losses, 90.0), 2),
            portfolio_var_95=round(float(np.percentile(portfolio_convolved_losses, 95)), 2),
            portfolio_var_99=round(float(np.percentile(portfolio_convolved_losses, 99)), 2),
            portfolio_cvar_99=round(self._cvar(portfolio_convolved_losses, 99.0), 2),
            diversification_ratio=(
                round(total_portfolio_ale / total_standalone_sum, 4)
                if total_standalone_sum > 0
                else 1.0
            ),
            towers=towers_dict,
        )
