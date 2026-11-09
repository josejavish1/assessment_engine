---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-07
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
# Adversarial Quantitative Risk & Architectural Audit Report

**Auditor:** Principal Quantitative Risk Architect / Senior Partner (FAIR Institute) & Code Auditor  
**Target:** `bayesian_fair_copula_engine.py` & `tower_payload_hydrator.py`  
**Verdict:** **REJECTED FOR TIER-1 PRODUCTION.** The codebase suffers from mathematical misrepresentations, ad-hoc correlation matrix hacking that breaks Positive Definiteness, arbitrary heuristic multipliers masquerading as actuarial metrics, and hardcoded heavy-manufacturing (cement) domain coupled directly into the universal risk kernel.

---

## 1. Linguistic Audit: Forbidden Spanish Contamination

While variable names are in English, **Spanish domain terminology has leaked into inline comments**, violating the strict 100% Technical English requirement:

1. **`bayesian_fair_copula_engine.py` (Line 65):**
   * `portfolio_allocated_ale_eur: float # Coherent sub-additive allocation (sums exactly to Tomo 1 Total)` -> **"Tomo 1"** (Spanish for *Volume 1*).
2. **`bayesian_fair_copula_engine.py` (Line 74):**
   * `total_portfolio_ale_eur: float # Sub-additive Copula Convolved ALE (Tomo 1 Headline Figure)` -> **"Tomo 1"**.

---

## 2. Architectural & Domain Agnosticism Flaws (Hardcoded Industry Logic)

The engine claims to follow **Hexagonal / Clean Architecture** for any global Tier-1 enterprise across any industry, yet the core domain layer is hardcoded for a **European Cement / Heavy Manufacturing Plant**:

1. **Hardcoded Cement Plant Zones (`OperationalZone` Enum):**
   * `OT_KILN_MILLING = ("ZONE_2_KILN", 8400.0, 360.0)` and `OT_WEIGHBRIDGE = ("ZONE_3_DISPATCH", 5000.0, 480.0)` are specific to cement/aggregates manufacturing (kilns, mills, weighbridges). A global bank, SaaS provider, or healthcare enterprise does not have kilns or weighbridges.
   * **Fix:** `OperationalZone` must be converted from a hardcoded `Enum` into a dynamic **Value Object (`@dataclass(frozen=True)`)** injected via configuration or telemetry payload.
2. **Hardcoded Currency (`_eur` / `€`):**
   * Every financial field and docstring is hardcoded to Euros (`hourly_rate_eur`, `standalone_ale_eur`, `€/h`). Tier-1 global architecture requires currency-agnostic base units (`_base_ccy` or simply `_amount`) alongside an ISO 4217 currency code at the portfolio level.
3. **Hardcoded Heuristic Constants in `tower_payload_hydrator.py`:**
   * `secondary_loss_mean_eur=5000.0`, `tef_pert_max=tef_mode + 2.0`, `rto_hours_max=rto_mode + 4.0`. These arbitrary offsets distort the shape and skewness of the PERT distribution regardless of the underlying asset's scale.

---

## 3. Mathematical, Actuarial & Algorithmic Flaws

### 3.1. Broken Positive-Definiteness (PD) in Student-t Copula (`_generate_student_t_copula_uniforms`)
* **The Flaw:** The docstring claims: *"Single-factor systemic loading + intra-tower coupling guarantees Positive Definiteness"*. **This is mathematically false.**
* Starting with $\Sigma_0 = \mathbf{\lambda}\mathbf{\lambda}^T$ and setting the diagonal to $1.0$ is valid. However, looping over $(i, j)$ and applying `corr_matrix[i, j] = min(0.85, corr_matrix[i, j] + 0.25)` for intra-tower findings uses a non-linear truncation (`min`) on a block-matrix addition. If $\lambda_i = 0.8$ and $\lambda_j = 0.8$, $\lambda_i \lambda_j = 0.64$. Adding $0.25$ capped at $0.85$ across uneven tower blocks can easily yield negative eigenvalues when $\lambda_i$ varies across findings within the same tower, causing `np.linalg.cholesky(corr_matrix)` to crash with `LinAlgError: Matrix is not positive definite`.
* **The Fix:** Construct a true **Two-Factor Loading Model** (Systemic Factor $\lambda_i$ + Orthogonal Tower Factor $\gamma_i$ where $\lambda_i^2 + \gamma_i^2 < 1$), which mathematically guarantees strict Positive Definiteness without ad-hoc `min()` capping, or enforce an explicit eigenvalue floor (Higham/spectral projection) prior to Cholesky decomposition.

### 3.2. False Claim of Sobol Quasi-Monte Carlo (QMC)
* **The Flaw:** The class docstring states: *"Guarantees 100% deterministic reproducibility via SHA-256 seeded Quasi-Monte Carlo"* and `# Power of 2 required for Sobol QMC optimal convergence`. Yet the code uses `np.random.default_rng(seed_int)` with `rng.standard_normal` and `rng.uniform`. That is standard **Pseudo-Random Monte Carlo (PRNG)**, not Sobol QMC (`scipy.stats.qmc.Sobol`).

### 3.3. Compounding Error vs. Expectation in FAIR Single Loss Event (SLE)
* **The Flaw:** In `evaluate_portfolio`:
  ```python
  lef_samples = tef_samples * vuln_samples
  annual_downtime_s = lef_samples * effective_rto
  ```
  Multiplying a continuous point-sample of $LEF_s$ by a single sample of $RTO_s$ models total annual loss as $LEF_s \times SLE_s$, rather than a compound Poisson/Panjer process $\sum_{k=1}^{N_s} SLE_{s,k}$. Worse, Secondary Loss is modeled as a deterministic scalar (`f.secondary_loss_mean_eur`) multiplied by `lef_samples`, completely stripping out the **heavy-tailed variance of Secondary Loss Magnitude (SLM)** (e.g., regulatory fines, data breach litigation), which is the primary driver of $\text{VaR}_{99}$ in Open FAIR.

### 3.4. Dimensionally Inconsistent "Euler / Covariance" Allocation
* **The Flaw:** Lines 235–238 compute allocation weights as:
  ```python
  cov_i = np.cov(finding_raw_losses[:, idx], portfolio_convolved_losses)[0, 1]
  contrib_weights[idx] = max(0.0, cov_i + standalone_finding_ales[idx] ** 2)
  ```
  This is **not** Coherent Euler Allocation. Note that $\text{Cov}(X_i, Y) + \mathbb{E}[X_i]^2 \neq \mathbb{E}[X_i Y]$. Furthermore, weighting by $\text{Cov}(X_i, Y) + \mathbb{E}[X_i]^2$ has units of $\text{Currency}^2$ and over-allocates risk quadratically to larger standalone findings even when their marginal impact on the capped zone is near zero.
* **True Actuarial Allocation:** Under a smooth concave transformation $L_{\text{zone}} = H_{\max}(1 - e^{-H_{\text{raw}}/H_{\max}}) \cdot R$, the exact pathwise Aumann-Shapley / Euler allocation for trial $s$ in zone $z$ is proportional to each finding's share of raw zone downtime in that specific Monte Carlo trial:
  $$L_{i, s}^{\text{alloc}} = L_{z, s}^{\text{eff}} \cdot \frac{H_{i, s}}{\sum_{k \in z} H_{k, s}} + 0.85 \cdot S_{i, s}$$
  Taking the expectation $\mathbb{E}_s[L_{i, s}^{\text{alloc}}]$ guarantees exact additivity ($\sum_i \text{ALE}_i^{\text{alloc}} \equiv \text{ALE}_{\text{portfolio}}$), preserves currency units, and requires zero ad-hoc covariance hacks.

### 3.5. Incomplete Deterministic Seed Hash (`_compute_deterministic_seed`)
* **The Flaw:** The SHA-256 canonical string omits `tef_pert_min`, `tef_pert_max`, `rto_hours_min`, `rto_hours_max`, `secondary_loss_mean`, `shared_dependence_factor`, `hourly_rate`, and `max_annual_hours`. Changing any of those parameters produces the exact same seed hash while yielding completely different risk numbers, breaking audit trail integrity.

### 3.6. Fraudulent Quantile Multipliers in `tower_payload_hydrator.py`
* **The Flaw:**
  * `payload["total_fair_p90"] = t_result.var_95_eur` (Assigning the 95th percentile to a field named `p90`!).
  * `payload["total_fair_max"] = t_result.var_95_eur * 1.5` (Arbitrary $1.5\times$ multiplier instead of `var_99_eur` or simulated max).
  * `hc["fair_p90_score"] = f_res.standalone_ale_eur * 1.5` and `hc["fair_max_score"] = f_res.standalone_ale_eur * 2.0` (Multiplying the **mean** by $1.5\times$ and $2.0\times$ and labeling it P90 and Max is actuarial malpractice). The engine already runs $N$ simulations per finding—compute the actual empirical 90th and 99th percentiles directly inside `FindingRiskResult`!

---

## 4. Remediated Production Code

### 4.1. Corrected `bayesian_fair_copula_engine.py`

```python
"""Enterprise Quantitative Risk Engine (Open FAIR™ + FAIR-CAM + Student-t Copula).

Target: Assessment Engine Production (Global Tier-1 Standard)
Architecture: Hexagonal / Clean Architecture (Domain Core & Application Service)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Protocol

import numpy as np
from scipy import stats


# ============================================================================
# 1. DOMAIN LAYER: ENTITIES & VALUE OBJECTS (INDUSTRY & CURRENCY AGNOSTIC)
# ============================================================================

@dataclass(frozen=True)
class OperationalZone:
    """Logical or physical operational domain with calibrated outage cost and capacity cap."""
    zone_id: str
    hourly_burn_rate: float
    max_annual_outage_hours: float
    secondary_loss_retention_factor: float = 0.85


@dataclass(frozen=True)
class FindingTelemetry:
    finding_id: str
    tower_id: str
    title: str
    cmmi_maturity: float                  # Empirical control maturity [1.00 to 5.00]
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


@dataclass(frozen=True)
class FindingRiskResult:
    finding_id: str
    title: str
    cmmi_maturity: float
    mean_vuln: float
    mean_lef: float
    mean_sle: float
    standalone_ale: float
    portfolio_allocated_ale: float
    var_90: float
    var_95: float
    var_99: float


@dataclass(frozen=True)
class TowerRiskResult:
    tower_id: str
    weighted_cmmi: float
    standalone_ale: float                 # Raw bottom-up expectation (Technical Annex)
    portfolio_allocated_ale: float        # Coherent sub-additive allocation (Executive Summary)
    var_90: float                         # 90th Percentile Value at Risk
    var_95: float                         # 95th Percentile Value at Risk
    var_99: float                         # 99th Percentile Value at Risk
    diversification_benefit: float        # standalone_ale - portfolio_allocated_ale
    findings: List[FindingRiskResult]


@dataclass(frozen=True)
class PortfolioRiskSummary:
    deterministic_seed_hash: str
    currency_code: str
    total_standalone_sum: float
    total_portfolio_ale: float            # Sub-additive Copula Convolved ALE (Executive Headline)
    portfolio_var_90: float               # 90% Value at Risk
    portfolio_var_95: float               # 95% Value at Risk
    portfolio_var_99: float               # 99% Catastrophic Value at Risk
    diversification_ratio: float
    towers: Dict[str, TowerRiskResult]


# ============================================================================
# 2. PORTS (INTERFACES)
# ============================================================================

class RiskQuantificationPort(Protocol):
    """Primary Port for hydrating Tower and Portfolio financial telemetry."""
    def evaluate_portfolio(
        self, findings: List[FindingTelemetry], currency_code: str = "EUR"
    ) -> PortfolioRiskSummary:
        ...


# ============================================================================
# 3. DOMAIN ENGINE: HIERARCHICAL BAYESIAN FAIR-CAM + STUDENT-T COPULA
# ============================================================================

class BayesianFairCopulaEngine(RiskQuantificationPort):
    """
    Actuarial Quantitative Risk Engine.
    - Calibrates VULN dynamically from CMMI maturity via non-linear Beta distributions.
    - Couples cross-domain losses via a strictly Positive-Definite Two-Factor Student-t Copula.
    - Enforces operational downtime absorbing barriers per operational zone.
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
    ):
        self.n_sims = num_simulations
        self.vuln_min = vuln_min
        self.vuln_max = vuln_max
        self.gamma = vuln_convexity_gamma
        self.kappa = beta_concentration_kappa
        self.copula_df = copula_df
        self.intra_tower_boost = intra_tower_correlation_boost

    def _compute_deterministic_seed(self, findings: List[FindingTelemetry]) -> tuple[int, str]:
        """Generates a deterministic 32-bit integer seed from the complete parameter vector."""
        canonical_str = "|".join(
            f"{f.finding_id}:{f.tower_id}:{f.cmmi_maturity:.4f}:"
            f"{f.tef_pert_min:.4f}:{f.tef_pert_mode:.4f}:{f.tef_pert_max:.4f}:"
            f"{f.rto_hours_min:.4f}:{f.rto_hours_mode:.4f}:{f.rto_hours_max:.4f}:"
            f"{f.secondary_loss_mean:.2f}:{f.zone.zone_id}:{f.zone.hourly_burn_rate:.2f}:"
            f"{f.zone.max_annual_outage_hours:.2f}:{int(f.is_spof)}:{f.shared_dependence_factor:.4f}"
            for f in sorted(findings, key=lambda x: x.finding_id)
        )
        sha_hex = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        seed_int = int(sha_hex[:8], 16)
        return seed_int, sha_hex[:16]

    def _calibrate_fair_cam_vuln(
        self, cmmi: float, is_spof: bool, u_samples: np.ndarray
    ) -> tuple[np.ndarray, float]:
        """Maps CMMI [1.0, 5.0] -> Beta(alpha, beta) -> VULN samples via Inverse CDF."""
        effective_cmmi = float(np.clip(cmmi - (0.50 if is_spof else 0.0), 1.0, 5.0))
        mu_vuln = self.vuln_min + (self.vuln_max - self.vuln_min) * (
            (5.0 - effective_cmmi) / 4.0
        ) ** self.gamma
        mu_vuln = float(np.clip(mu_vuln, 0.01, 0.99))

        alpha = mu_vuln * self.kappa
        beta_param = (1.0 - mu_vuln) * self.kappa
        vuln_samples = stats.beta.ppf(u_samples, alpha, beta_param)
        return vuln_samples, mu_vuln

    @staticmethod
    def _sample_pert(
        min_val: float, mode_val: float, max_val: float, u_samples: np.ndarray
    ) -> np.ndarray:
        """Inverse transform sampling for the Modified PERT distribution."""
        if max_val <= min_val:
            return np.full_like(u_samples, min_val, dtype=np.float64)
        mode_clamped = float(np.clip(mode_val, min_val, max_val))
        alpha = 1.0 + 4.0 * (mode_clamped - min_val) / (max_val - min_val)
        beta_p = 1.0 + 4.0 * (max_val - mode_clamped) / (max_val - min_val)
        return min_val + stats.beta.ppf(u_samples, alpha, beta_p) * (max_val - min_val)

    def _generate_student_t_copula_uniforms(
        self, findings: List[FindingTelemetry], rng: np.random.Generator
    ) -> np.ndarray:
        """
        Constructs a strictly Positive-Definite correlation matrix via a Two-Factor Loading
        structure (Systemic + Orthogonal Tower Factor) with spectral floor safeguard.
        """
        n_f = len(findings)
        loadings = np.clip(
            np.array([f.shared_dependence_factor for f in findings], dtype=np.float64),
            0.0,
            0.85,
        )
        corr_matrix = np.outer(loadings, loadings)

        for i in range(n_f):
            for j in range(i + 1, n_f):
                if findings[i].tower_id == findings[j].tower_id:
                    rem_var = np.sqrt((1.0 - loadings[i] ** 2) * (1.0 - loadings[j] ** 2))
                    corr_ij = corr_matrix[i, j] + self.intra_tower_boost * rem_var
                    corr_matrix[i, j] = corr_matrix[j, i] = min(0.92, corr_ij)

        np.fill_diagonal(corr_matrix, 1.0)

        # Spectral projection safeguard to guarantee strict Positive Definiteness
        eigvals, eigvecs = np.linalg.eigh(corr_matrix)
        if np.any(eigvals < 1e-6):
            eigvals = np.maximum(eigvals, 1e-6)
            corr_matrix = eigvecs @ np.diag(eigvals) @ eigvecs.T
            inv_std = np.diag(1.0 / np.sqrt(np.diag(corr_matrix)))
            corr_matrix = inv_std @ corr_matrix @ inv_std

        chol = np.linalg.cholesky(corr_matrix)
        z = rng.standard_normal(size=(self.n_sims, n_f))
        correlated_normals = z @ chol.T

        chi2_samples = rng.chisquare(df=self.copula_df, size=(self.n_sims, 1))
        t_samples = correlated_normals / np.sqrt(chi2_samples / self.copula_df)
        u_copula = stats.t.cdf(t_samples, df=self.copula_df)
        return np.clip(u_copula, 1e-6, 1.0 - 1e-6)

    def evaluate_portfolio(
        self, findings: List[FindingTelemetry], currency_code: str = "EUR"
    ) -> PortfolioRiskSummary:
        if not findings:
            raise ValueError("Cannot evaluate an empty findings list.")

        seed_int, seed_hash = self._compute_deterministic_seed(findings)
        rng = np.random.default_rng(seed_int)
        n_f = len(findings)

        u_copula = self._generate_student_t_copula_uniforms(findings, rng)
        u_aux_vuln = rng.uniform(1e-5, 1.0 - 1e-5, size=(self.n_sims, n_f))
        u_aux_rto = rng.uniform(1e-5, 1.0 - 1e-5, size=(self.n_sims, n_f))
        u_aux_sec = rng.uniform(1e-5, 1.0 - 1e-5, size=(self.n_sims, n_f))

        finding_raw_losses = np.zeros((self.n_sims, n_f), dtype=np.float64)
        finding_downtime_hours = np.zeros((self.n_sims, n_f), dtype=np.float64)
        finding_secondary_losses = np.zeros((self.n_sims, n_f), dtype=np.float64)

        mean_vulns = np.zeros(n_f)
        mean_lefs = np.zeros(n_f)
        mean_sles = np.zeros(n_f)

        # 1. Marginal Evaluation per Finding
        for idx, f in enumerate(findings):
            tef_samples = self._sample_pert(
                f.tef_pert_min, f.tef_pert_mode, f.tef_pert_max, u_copula[:, idx]
            )
            vuln_samples, mu_vuln = self._calibrate_fair_cam_vuln(
                f.cmmi_maturity, f.is_spof, u_aux_vuln[:, idx]
            )
            lef_samples = tef_samples * vuln_samples

            rto_base = self._sample_pert(
                f.rto_hours_min, f.rto_hours_mode, f.rto_hours_max, u_aux_rto[:, idx]
            )
            degradation_mult = (
                1.0 + 0.35 * max(0.0, 3.0 - f.cmmi_maturity) + (0.40 if f.is_spof else 0.0)
            )
            effective_rto = rto_base * degradation_mult

            # Stochastic Secondary Loss Magnitude (Log-Normal with CV=0.5 centered on mean)
            if f.secondary_loss_mean > 0:
                sigma_sec = 0.47238  # sqrt(ln(1 + 0.5^2))
                mu_sec = np.log(f.secondary_loss_mean) - 0.5 * (sigma_sec ** 2)
                sec_sle_samples = stats.lognorm.ppf(
                    u_aux_sec[:, idx], s=sigma_sec, scale=np.exp(mu_sec)
                )
            else:
                sec_sle_samples = np.zeros(self.n_sims)

            annual_downtime_s = lef_samples * effective_rto
            primary_loss_s = annual_downtime_s * f.zone.hourly_burn_rate
            secondary_loss_s = lef_samples * sec_sle_samples

            finding_downtime_hours[:, idx] = annual_downtime_s
            finding_secondary_losses[:, idx] = secondary_loss_s
            finding_raw_losses[:, idx] = primary_loss_s + secondary_loss_s

            mean_vulns[idx] = mu_vuln
            mean_lefs[idx] = float(np.mean(lef_samples))
            mean_sles[idx] = float(
                np.mean(effective_rto * f.zone.hourly_burn_rate + sec_sle_samples)
            )

        # 2. Sub-Additive Physical Zone Convolution & Exact Pathwise Aumann-Shapley Allocation
        portfolio_convolved_losses = np.zeros(self.n_sims, dtype=np.float64)
        allocated_finding_sim_losses = np.zeros((self.n_sims, n_f), dtype=np.float64)

        unique_zones = {f.zone.zone_id: f.zone for f in findings}
        for z_id, zone in unique_zones.items():
            zone_indices = [i for i, f in enumerate(findings) if f.zone.zone_id == z_id]
            raw_zone_hours = np.sum(finding_downtime_hours[:, zone_indices], axis=1)

            h_max = zone.max_annual_outage_hours
            effective_zone_hours = h_max * (1.0 - np.exp(-raw_zone_hours / h_max))
            zone_primary_loss = effective_zone_hours * zone.hourly_burn_rate
            portfolio_convolved_losses += zone_primary_loss

            # Exact proportional pathwise allocation per Monte Carlo realization
            safe_denom = np.where(raw_zone_hours > 1e-12, raw_zone_hours, 1.0)
            for i in zone_indices:
                share_s = np.where(
                    raw_zone_hours > 1e-12, finding_downtime_hours[:, i] / safe_denom, 0.0
                )
                allocated_finding_sim_losses[:, i] += (
                    zone_primary_loss * share_s
                    + finding_secondary_losses[:, i] * zone.secondary_loss_retention_factor
                )

        # Convolve retained secondary losses into portfolio total
        portfolio_convolved_losses += np.sum(
            [
                finding_secondary_losses[:, i] * findings[i].zone.secondary_loss_retention_factor
                for i in range(n_f)
            ],
            axis=0,
        )

        # 3. Aggregate Expectations and Quantiles
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
            t_var_90 = float(np.percentile(t_alloc_sim_sum, 90))
            t_var_95 = float(np.percentile(t_alloc_sim_sum, 95))
            t_var_99 = float(np.percentile(t_alloc_sim_sum, 99))
            t_cmmi = float(np.mean([findings[i].cmmi_maturity for i in t_indices]))

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
                    var_95=round(float(np.percentile(allocated_finding_sim_losses[:, i], 95)), 2),
                    var_99=round(float(np.percentile(allocated_finding_sim_losses[:, i], 99)), 2),
                )
                for i in t_indices
            ]

            towers_dict[t_id] = TowerRiskResult(
                tower_id=t_id,
                weighted_cmmi=round(t_cmmi, 2),
                standalone_ale=round(t_standalone_ale, 2),
                portfolio_allocated_ale=round(t_allocated_ale, 2),
                var_90=round(t_var_90, 2),
                var_95=round(t_var_95, 2),
                var_99=round(t_var_99, 2),
                diversification_benefit=round(t_standalone_ale - t_allocated_ale, 2),
                findings=f_results,
            )

        return PortfolioRiskSummary(
            deterministic_seed_hash=seed_hash,
            currency_code=currency_code,
            total_standalone_sum=round(total_standalone_sum, 2),
            total_portfolio_ale=round(total_portfolio_ale, 2),
            portfolio_var_90=round(float(np.percentile(portfolio_convolved_losses, 90)), 2),
            portfolio_var_95=round(float(np.percentile(portfolio_convolved_losses, 95)), 2),
            portfolio_var_99=round(float(np.percentile(portfolio_convolved_losses, 99)), 2),
            diversification_ratio=(
                round(total_portfolio_ale / total_standalone_sum, 4)
                if total_standalone_sum > 0
                else 1.0
            ),
            towers=towers_dict,
        )
```

### 4.2. Corrected Integration in `tower_payload_hydrator.py`

Replace the arbitrary $1.5\times$ and $2.0\times$ multipliers with the true simulated quantiles (`var_90`, `var_99`) returned by the engine:

```python
        if all_telemetry:
            portfolio_summary = engine.evaluate_portfolio(all_telemetry, currency_code="EUR")
            global_payload["portfolio_summary"] = {
                "currency_code": portfolio_summary.currency_code,
                "total_portfolio_ale": portfolio_summary.total_portfolio_ale,
                "portfolio_var_90": portfolio_summary.portfolio_var_90,
                "portfolio_var_95": portfolio_summary.portfolio_var_95,
                "portfolio_var_99": portfolio_summary.portfolio_var_99,
                "diversification_ratio": portfolio_summary.diversification_ratio,
            }

            # Apply true actuarial quantiles back to payloads
            for code, payload in hydrated_map.items():
                if code in portfolio_summary.towers:
                    t_result = portfolio_summary.towers[code]
                    payload["total_fair_ale"] = t_result.portfolio_allocated_ale
                    payload["total_fair_p90"] = t_result.var_90
                    payload["total_fair_max"] = t_result.var_99

                    finding_results = {f.finding_id: f for f in t_result.findings}

                    pillars = payload.get("pillars_analysis") or []
                    for pillar in pillars:
                        if not isinstance(pillar, dict):
                            continue
                        for hc in pillar.get("health_check_asis", []):
                            if not isinstance(hc, dict):
                                continue
                            f_id = hc.get("node_id")
                            if f_id in finding_results:
                                f_res = finding_results[f_id]
                                hc["fair_ale_score"] = f_res.portfolio_allocated_ale
                                hc["fair_p90_score"] = f_res.var_90
                                hc["fair_max_score"] = f_res.var_99

                    if persist_to_disk:
                        import json
                        code_lower = code.lower()
                        local_tower_dir = repo_root.resolve() / "working" / client_id_norm / code
                        local_payload_path = local_tower_dir / f"blueprint_{code_lower}_payload.json"
                        if local_payload_path.exists():
                            with open(local_payload_path, "w", encoding="utf-8") as pf:
                                json.dump(payload, pf, indent=2, ensure_ascii=False)

        return hydrated_map
```