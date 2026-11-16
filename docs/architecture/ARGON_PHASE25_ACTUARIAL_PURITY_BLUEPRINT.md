# ARGON PHASE 25: ACTUARIAL PURITY & ORTHOGONAL ECONOMIC VECTOR BLUEPRINT

**Document ID:** `ARGON-ARCH-BP-025`  
**Target Artifact:** `docs/architecture/ARGON_PHASE25_ACTUARIAL_PURITY_BLUEPRINT.md`  
**Author:** Gemini-4-Argon, Global Chief Systems Architect & Fellow of the Society of Actuaries (FSA)  
**Status:** MANDATORY EXECUTION DIRECTIVE  
**Compliance:** Open FAIR™ Standard, CAS/SOA Risk Aggregation Principles, Zero-Hardcoding Invariant  

---

## 1. EXECUTIVE SUMMARY & ACTUARIAL PARADIGM SHIFT

### 1.1 The Numerological Antipattern
During the forensic audit of `chapter4_synthesizer.py`, a severe mathematical and epistemological antipattern was identified within the Cost of Inaction (COI) synthesis engine: **Parametric Numerology & Vector Entanglement**. 

Specifically, the legacy system computes Lever 3 (Contractual & Licensing Escalation) by anchoring it to linear combinations of Lever 1 (Engineering Toil) and Lever 2 (Probabilistic Outage Annualized Loss Expectancy [ALE]) via arbitrary, hardcoded scalar weights:

```python
# LEGACY ANTIPATTERN - DO NOT REPLICATE
baseline_economic_anchor = (outage_min * 0.60) + (toil_min * 0.45)
```

Furthermore, portfolio-level risk aggregation currently relies on an elementary, unbounded linear heuristic:

```python
# LEGACY ANTIPATTERN - DO NOT REPLICATE
subadditivity_factor = 1.0 - 0.05 * (N - 1)
```

### 1.2 Actuarial Failure Modes
This implementation fails Tier-1 CFO/CTO scrutiny for three fundamental reasons:
1. **Violation of Vector Orthogonality:** In microeconomic and actuarial theory, vendor licensing escalation (e.g., Broadcom/VMware core-count price hikes or Cisco SmartNet renewals) is a deterministic balance-sheet liability driven by capital/operational expenditure ratios. It shares **zero covariance** with stochastic network downtime (Lever 2) or internal FTE ticket-handling friction (Lever 1). Conditioning contractual drag on outage frequency introduces catastrophic circularity: if a client achieves 99.999% uptime, the legacy model falsely asserts their software licensing costs approach zero.
2. **Breakdown at Scale (Non-Monotonicity):** The linear subadditivity heuristic $1.0 - 0.05(N - 1)$ becomes mathematically degenerate when $N > 21$ risk scenarios, yielding negative loss expectancies and violating the axiom of non-negativity in probability spaces.
3. **Opaque Magic Numbers:** Hardcoding coefficients (`0.60`, `0.45`, `0.05`) inside imperative Python logic violates the Separation of Concerns (SoC) principle, making regulatory auditing and sensitivity analysis impossible without code mutation.

### 1.3 The Target Actuarial Architecture
Phase 25 completely eradicates parametric numerology by establishing a **Pure Orthogonal Vector Space** $\mathbb{R}^3$ for economic synthesis, governed entirely by declarative schemas in `engine_config/`:

$$\text{COI}_{\text{total}} = \mathbf{V}_{\text{Toil}} \oplus \mathbf{V}_{\text{Outage}} \oplus \mathbf{V}_{\text{Contract}}$$

Where:
* $\mathbf{V}_{\text{Toil}}$ (**Lever 1 - Operational Friction**): A deterministic/bounded-interval vector derived strictly from wasted engineering hours multiplied by a blended, location-adjusted Fully Burdened Labor Rate.
* $\mathbf{V}_{\text{Outage}}$ (**Lever 2 - Stochastic Risk Exposure**): A probabilistic vector derived strictly from Open FAIR™ Monte Carlo/parametric synthesis ($\text{ALE} = \text{TEF} \times \text{Vulnerability} \times \text{SLE}$), aggregated across $N$ scenarios using a **Variance-Covariance Copula Diversification Factor**.
* $\mathbf{V}_{\text{Contract}}$ (**Lever 3 - Contractual & Licensing Drag**): A macroeconomic vector derived strictly from the organization's Gross Annual Revenue, mapped through an industry-specific IT Spend Ratio (Gartner/Flexera benchmarks), isolated to the addressable infrastructure footprint, and compounded by empirical vendor escalation rates.

$$\frac{\partial \mathbf{V}_{\text{Contract}}}{\partial \mathbf{V}_{\text{Outage}}} = 0, \quad \frac{\partial \mathbf{V}_{\text{Contract}}}{\partial \mathbf{V}_{\text{Toil}}} = 0$$

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

### Phase 25.1: Declarative Actuarial Parameters (`engine_config/` & Schemas)

All actuarial constants, industry benchmarks, and correlation coefficients must be extracted from Python modules and codified into version-controlled, declarative JSON artifacts validated by strict Pydantic V2 contracts at engine bootstrap.

#### 25.1.1 Target Configuration Topology
We will introduce `engine_config/actuarial_benchmarks.json` and expand `engine_config/rate_card.json`.

* **Industry IT Spend Ratios ($\rho_{\text{IT}}$):** Maps standard NAICS/GICS industry verticals to bounded intervals `[min, median, max]` representing IT Expenditure as a percentage of Gross Annual Revenue (e.g., Financial Services: `[0.065, 0.082, 0.105]`; Manufacturing: `[0.018, 0.025, 0.035]`).
* **Domain Addressable Allocation ($\alpha_{\text{domain}}$):** The fraction of total IT spend attributable to the target assessment domain (e.g., Core Network & Security Infrastructure: `[0.15, 0.22, 0.30]`).
* **Contractual Escalation Rates ($\lambda_{\text{esc}}$):** Annualized inflationary and punitive licensing renewal rates (e.g., Legacy Maint/EOSL Penalty, Hypervisor Core-Licensing Shift).
* **Copula Correlation Parameters ($\theta_{\text{copula}}$):** Defines the inter-scenario tail-dependence and average pairwise Pearson/Spearman correlation $\bar{\rho}$ for systemic infrastructure risks.

---

### Phase 25.2: Orthogonal Lever Mechanics (Refactoring `chapter4_synthesizer.py`)

We will surgically excise the entangled calculation blocks in `chapter4_synthesizer.py` and replace them with three isolated, pure functional calculators.

#### 25.2.1 Lever 1: Engineering Toil Calculator (`_compute_orthogonal_toil_vector`)
$$\mathbf{V}_{\text{Toil}} = \sum_{i=1}^{M} \left( H_{\text{friction}, i} \times R_{\text{FTE}, i} \times \omega_{\text{reclaim}, i} \right)$$
* $H_{\text{friction}, i}$: Annualized engineering hours lost to manual toil in operational domain $i$.
* $R_{\text{FTE}, i}$: Blended hourly fully-burdened rate from `rate_card.json`.
* $\omega_{\text{reclaim}, i}$: Productivity recapture efficiency factor (from `actuarial_benchmarks.json`), recognizing that 100% of saved time does not convert linearly to hard capital unless headcount is avoided or reallocated to high-yield CAPEX projects.

#### 25.2.2 Lever 2: Probabilistic Outage ALE Calculator (`_compute_orthogonal_outage_vector`)
$$\text{ALE}_{k} = \text{TEF}_{k} \times P(\text{Loss}_{k}) \times \text{SLE}_{k}$$
Each risk scenario $k \in \{1, \dots, N\}$ is evaluated independently via the FAIR engine, producing a three-point actuarial estimate $(\text{ALE}_{k,\text{min}}, \text{ALE}_{k,\text{mode}}, \text{ALE}_{k,\text{max}})$. No licensing or FTE maintenance variables are permitted in this pipeline.

#### 25.2.3 Lever 3: Contractual Drag Calculator (`_compute_orthogonal_contract_vector`)
Lever 3 is completely decoupled from Levers 1 and 2. It is anchored to the enterprise's macroeconomic profile:

$$\text{Baseline\_IT\_Spend} = \text{Revenue}_{\text{annual}} \times \vec{\rho}_{\text{IT}}(\text{Industry})$$
$$\text{Addressable\_Spend} = \text{Baseline\_IT\_Spend} \times \vec{\alpha}_{\text{domain}}$$
$$\mathbf{V}_{\text{Contract}} = \text{Addressable\_Spend} \times \vec{\lambda}_{\text{esc}}(\text{Maturity\_Tier})$$

**Scale Agnosticism Fallback:** If `Revenue_annual` is not explicitly provided in the telemetry payload, it is deterministically inferred via a declarative Employee-to-Revenue multiplier ($\text{FTE}_{\text{total}} \times \text{Rev\_Per\_Employee}_{\text{Industry}}$) defined in `actuarial_benchmarks.json`.

---

### Phase 25.3: Subadditive Portfolio Aggregation (Copula Diversification)

To aggregate $N$ individual risk scenarios in Lever 2 without overstating total exposure (which occurs via naive linear summation $\sum \text{ALE}_k$) or generating negative numbers (which occurs via the legacy $1 - 0.05(N-1)$ hack), we implement a **Closed-Form Gaussian/t-Copula Variance-Covariance Diversification Multiplier**.

#### 25.3.1 Mathematical Formulation
In actuarial portfolio theory, the variance of a sum of $N$ correlated random loss variables $X_1, X_2, \dots, X_N$ with standard deviations $\sigma_1, \dots, \sigma_N$ and pairwise correlation matrix $\Sigma = [\rho_{ij}]$ is:

$$\sigma_{\text{portfolio}}^2 = \sum_{i=1}^{N} \sigma_i^2 + 2 \sum_{i=1}^{N} \sum_{j < i} \rho_{ij} \sigma_i \sigma_j$$

Assuming a homogeneous systemic correlation coefficient $\bar{\rho} \in (0, 1)$ across IT infrastructure failure modes (derived from `actuarial_benchmarks.json`, typically $\bar{\rho} \approx 0.25$ for shared control-plane dependencies) and normalizing across the portfolio, the asymptotic **Subadditivity Diversification Factor** $\Psi(N, \bar{\rho})$ is defined as:

$$\Psi(N, \bar{\rho}) = \sqrt{\bar{\rho} + \frac{1 - \bar{\rho}}{N} + \tau_{\text{tail}} \cdot \left(\frac{N - 1}{N}\right)}$$

Where:
* $N \ge 1$ is the cardinality of active risk scenarios.
* $\bar{\rho} \in [0.05, 0.95]$ is the baseline inter-scenario correlation parameter.
* $\tau_{\text{tail}} \in [0.0, 0.20]$ is the Student-t Copula tail-dependence shock surcharge (capturing cascading common-mode failures like a global BGP route leak or Active Directory collapse).

#### 25.3.2 Boundary Properties of $\Psi(N, \bar{\rho})$
1. **Identity at $N=1$:** $\Psi(1, \bar{\rho}) = \sqrt{\bar{\rho} + 1 - \bar{\rho} + 0} = 1.0$. (A single scenario experiences zero diversification adjustment).
2. **Strict Positivity & Asymptotic Floor:** As $N \to \infty$, $\lim_{N \to \infty} \Psi(N, \bar{\rho}) = \sqrt{\bar{\rho} + \tau_{\text{tail}}} > 0$. It is mathematically impossible for this function to yield zero or negative multipliers, regardless of whether $N = 5$ or $N = 50,000$.
3. **Monotonic Subadditivity:** For all $N > 1$ and $\bar{\rho} + \tau_{\text{tail}} < 1$, $0 < \Psi(N, \bar{\rho}) < 1.0$.

The aggregated portfolio ALE vector is then computed as:

$$\mathbf{V}_{\text{Outage\_Portfolio}} = \Psi(N, \bar{\rho}) \times \sum_{k=1}^{N} \vec{\text{ALE}}_k$$

---

## 3. ARCHITECTURAL CONTRACTS & DECLARATIVE CONFIGURATIONS

### 3.1 Declarative Configuration: `engine_config/actuarial_benchmarks.json`

```json
{
  "schema_version": "25.0.0",
  "description": "Declarative Actuarial Benchmarks for Orthogonal COI Synthesis and Copula Risk Aggregation.",
  "copula_aggregation_parameters": {
    "baseline_pairwise_correlation_rho": 0.25,
    "tail_dependence_surcharge_tau": 0.08,
    "min_diversification_floor": 0.35
  },
  "toil_efficiency_parameters": {
    "productivity_recapture_factor": {
      "min": 0.50,
      "mode": 0.65,
      "max": 0.80
    },
    "annual_ productive_hours_per_fte": 1880.0
  },
  "contractual_escalation_parameters": {
    "default_domain_spend_allocation_ratio": {
      "min": 0.14,
      "mode": 0.20,
      "max": 0.28
    },
    "annual_escalation_rates_by_maturity": {
      "TIER_1_AD_HOC": { "min": 0.12, "mode": 0.18, "max": 0.25 },
      "TIER_2_FRAGMENTED": { "min": 0.08, "mode": 0.12, "max": 0.17 },
      "TIER_3_STANDARDIZED": { "min": 0.04, "mode": 0.07, "max": 0.10 },
      "TIER_4_OPTIMIZED": { "min": 0.02, "mode": 0.035, "max": 0.05 }
    }
  },
  "industry_macro_benchmarks": {
    "FINANCIAL_SERVICES": {
      "it_spend_to_revenue_ratio": { "min": 0.065, "mode": 0.082, "max": 0.105 },
      "implied_revenue_per_employee_usd": 650000.0
    },
    "MANUFACTURING": {
      "it_spend_to_revenue_ratio": { "min": 0.015, "mode": 0.024, "max": 0.035 },
      "implied_revenue_per_employee_usd": 380000.0
    },
    "HEALTHCARE": {
      "it_spend_to_revenue_ratio": { "min": 0.035, "mode": 0.048, "max": 0.065 },
      "implied_revenue_per_employee_usd": 290000.0
    },
    "TECHNOLOGY_SAAS": {
      "it_spend_to_revenue_ratio": { "min": 0.080, "mode": 0.110, "max": 0.150 },
      "implied_revenue_per_employee_usd": 520000.0
    },
    "RETAIL_ECOMMERCE": {
      "it_spend_to_revenue_ratio": { "min": 0.020, "mode": 0.032, "max": 0.048 },
      "implied_revenue_per_employee_usd": 310000.0
    },
    "DEFAULT_ENTERPRISE": {
      "it_spend_to_revenue_ratio": { "min": 0.030, "mode": 0.045, "max": 0.060 },
      "implied_revenue_per_employee_usd": 400000.0
    }
  }
}
```

### 3.2 Declarative Configuration: `engine_config/rate_card.json` (Updated Schema)

```json
{
  "schema_version": "25.0.0",
  "currency": "USD",
  "labor_rates_hourly_blended": {
    "L1_NOC_OPERATOR": { "min": 45.0, "mode": 60.0, "max": 80.0 },
    "L2_NETWORK_ENGINEER": { "min": 75.0, "mode": 95.0, "max": 125.0 },
    "L3_PRINCIPAL_ARCHITECT": { "min": 115.0, "mode": 145.0, "max": 185.0 },
    "SECOPS_ANALYST": { "min": 85.0, "mode": 110.0, "max": 145.0 },
    "DEFAULT_BLENDED_FTE": { "min": 80.0, "mode": 105.0, "max": 135.0 }
  },
  "vendor_licensing_modifiers": {
    "eosl_extended_support_surcharge": 0.22,
    "unconsolidated_multi_vendor_tax": 0.15,
    "audit_non_compliance_penalty_rate": 0.10
  }
}
```

### 3.3 Pydantic V2 Architectural Contracts (`src/models/actuarial_contracts.py`)

```python
from __future__ import annotations
from enum import Enum
from typing import Dict
from pydantic import BaseModel, Field, model_validator, ConfigDict


class IndustryVertical(str, Enum):
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    MANUFACTURING = "MANUFACTURING"
    HEALTHCARE = "HEALTHCARE"
    TECHNOLOGY_SAAS = "TECHNOLOGY_SAAS"
    RETAIL_ECOMMERCE = "RETAIL_ECOMMERCE"
    DEFAULT_ENTERPRISE = "DEFAULT_ENTERPRISE"


class MaturityTier(str, Enum):
    TIER_1_AD_HOC = "TIER_1_AD_HOC"
    TIER_2_FRAGMENTED = "TIER_2_FRAGMENTED"
    TIER_3_STANDARDIZED = "TIER_3_STANDARDIZED"
    TIER_4_OPTIMIZED = "TIER_4_OPTIMIZED"


class PertDistributionTriplet(BaseModel):
    """Represents a strictly ordered three-point actuarial estimate [min, mode, max]."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    min: float = Field(..., ge=0.0, description="Lower bound (P10) estimate.")
    mode: float = Field(..., ge=0.0, description="Most likely (Modal) estimate.")
    max: float = Field(..., ge=0.0, description="Upper bound (P90) estimate.")

    @model_validator(mode="after")
    def validate_monotonicity(self) -> PertDistributionTriplet:
        if not (self.min <= self.mode <= self.max):
            raise ValueError(
                f"Actuarial Invariant Violation: Triplet must satisfy min <= mode <= max. "
                f"Received: min={self.min}, mode={self.mode}, max={self.max}"
            )
        return self

    def scale(self, factor: float) -> PertDistributionTriplet:
        if factor < 0.0:
            raise ValueError(f"Scalar factor must be non-negative. Got {factor}")
        return PertDistributionTriplet(
            min=round(self.min * factor, 2),
            mode=round(self.mode * factor, 2),
            max=round(self.max * factor, 2),
        )

    def multiply_triplet(self, other: PertDistributionTriplet) -> PertDistributionTriplet:
        return PertDistributionTriplet(
            min=round(self.min * other.min, 2),
            mode=round(self.mode * other.mode, 2),
            max=round(self.max * other.max, 2),
        )

    def add_triplet(self, other: PertDistributionTriplet) -> PertDistributionTriplet:
        return PertDistributionTriplet(
            min=round(self.min + other.min, 2),
            mode=round(self.mode + other.mode, 2),
            max=round(self.max + other.max, 2),
        )


class CopulaAggregationParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    baseline_pairwise_correlation_rho: float = Field(..., gt=0.0, lt=1.0)
    tail_dependence_surcharge_tau: float = Field(..., ge=0.0, lt=0.5)
    min_diversification_floor: float = Field(..., gt=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_copula_stability(self) -> CopulaAggregationParameters:
        if (self.baseline_pairwise_correlation_rho + self.tail_dependence_surcharge_tau) >= 1.0:
            raise ValueError(
                "Sum of baseline correlation (rho) and tail surcharge (tau) must be strictly < 1.0 "
                "to preserve portfolio subadditivity."
            )
        return self


class ToilEfficiencyParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    productivity_recapture_factor: PertDistributionTriplet
    annual_productive_hours_per_fte: float = Field(..., gt=0.0, le=8760.0)


class ContractualEscalationParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_domain_spend_allocation_ratio: PertDistributionTriplet
    annual_escalation_rates_by_maturity: Dict[MaturityTier, PertDistributionTriplet]


class IndustryMacroBenchmark(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    it_spend_to_revenue_ratio: PertDistributionTriplet
    implied_revenue_per_employee_usd: float = Field(..., gt=0.0)


class ActuarialBenchmarksConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str
    description: str
    copula_aggregation_parameters: CopulaAggregationParameters
    toil_efficiency_parameters: ToilEfficiencyParameters
    contractual_escalation_parameters: ContractualEscalationParameters
    industry_macro_benchmarks: Dict[IndustryVertical, IndustryMacroBenchmark]


class OrthogonalCOISynthesisResult(BaseModel):
    """Output contract guaranteeing strict vector orthogonality."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    lever_1_engineering_toil_usd: PertDistributionTriplet
    lever_2_probabilistic_outage_ale_usd: PertDistributionTriplet
    lever_3_contractual_escalation_usd: PertDistributionTriplet
    total_cost_of_inaction_usd: PertDistributionTriplet
    applied_copula_diversification_factor: float = Field(..., gt=0.0, le=1.0)
    scenario_cardinality_n: int = Field(..., ge=0)
    derived_baseline_it_spend_usd: PertDistributionTriplet
```

---

### 3.4 Refactored Implementation: `src/synthesizers/chapter4_synthesizer.py`

Below is the production-grade refactored core for `chapter4_synthesizer.py`, enforcing zero hardcoded magic numbers and complete independence between the three economic levers.

```python
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import List, Optional

from src.models.actuarial_contracts import (
    ActuarialBenchmarksConfig,
    IndustryVertical,
    MaturityTier,
    OrthogonalCOISynthesisResult,
    PertDistributionTriplet,
)


class ActuarialSynthesizerError(Exception):
    """Raised when actuarial synthesis inputs or configurations violate mathematical invariants."""


class Chapter4ActuarialSynthesizer:
    """
    Phase 25 Orthogonal Cost of Inaction (COI) Synthesizer.
    Eliminates parametric numerology and enforces strict independence across:
      - Lever 1: Engineering Toil (Labor Friction)
      - Lever 2: Probabilistic Outage ALE (Open FAIR + Copula Subadditivity)
      - Lever 3: Contractual & Licensing Drag (Macro IT Spend * Escalation Rate)
    """

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir
        self.benchmarks = self._load_benchmarks(config_dir / "actuarial_benchmarks.json")
        self.rate_card = self._load_rate_card(config_dir / "rate_card.json")

    @staticmethod
    def _load_benchmarks(path: Path) -> ActuarialBenchmarksConfig:
        if not path.exists():
            raise ActuarialSynthesizerError(f"Missing declarative benchmark config: {path}")
        raw_data = json.loads(path.read_text(encoding="utf-8"))
        return ActuarialBenchmarksConfig.model_validate(raw_data)

    @staticmethod
    def _load_rate_card(path: Path) -> dict:
        if not path.exists():
            raise ActuarialSynthesizerError(f"Missing declarative rate card config: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def compute_copula_diversification_factor(self, scenario_count_n: int) -> float:
        """
        Computes the closed-form Variance-Covariance + Tail-Dependence Copula factor:
        Psi(N, rho, tau) = max(floor, sqrt(rho + (1 - rho)/N + tau * ((N - 1)/N)))
        """
        if scenario_count_n < 0:
            raise ActuarialSynthesizerError(f"Scenario count N cannot be negative: {scenario_count_n}")
        if scenario_count_n <= 1:
            return 1.0

        params = self.benchmarks.copula_aggregation_parameters
        rho = params.baseline_pairwise_correlation_rho
        tau = params.tail_dependence_surcharge_tau
        floor = params.min_diversification_floor

        n_float = float(scenario_count_n)
        variance_term = rho + ((1.0 - rho) / n_float)
        tail_shock_term = tau * ((n_float - 1.0) / n_float)

        psi = math.sqrt(variance_term + tail_shock_term)
        return round(max(floor, min(1.0, psi)), 6)

    def compute_lever_1_engineering_toil(
        self,
        annual_wasted_hours: float,
        role_key: str = "DEFAULT_BLENDED_FTE",
    ) -> PertDistributionTriplet:
        """
        Lever 1: Purely derived from FTE friction hours * Blended Labor Rate * Recapture Factor.
        Zero dependency on Outages or Licensing.
        """
        if annual_wasted_hours < 0.0:
            raise ActuarialSynthesizerError(f"Annual wasted hours cannot be negative: {annual_wasted_hours}")
        if annual_wasted_hours == 0.0:
            return PertDistributionTriplet(min=0.0, mode=0.0, max=0.0)

        labor_rates = self.rate_card.get("labor_rates_hourly_blended", {})
        rate_dict = labor_rates.get(role_key) or labor_rates.get("DEFAULT_BLENDED_FTE")
        if not rate_dict:
            raise ActuarialSynthesizerError(f"Role key '{role_key}' missing from rate_card.json")

        hourly_rate_triplet = PertDistributionTriplet.model_validate(rate_dict)
        recapture_triplet = self.benchmarks.toil_efficiency_parameters.productivity_recapture_factor

        raw_labor_cost = hourly_rate_triplet.scale(annual_wasted_hours)
        return raw_labor_cost.multiply_triplet(recapture_triplet)

    def compute_lever_2_probabilistic_outage_portfolio(
        self,
        scenario_ales: List[PertDistributionTriplet],
    ) -> tuple[PertDistributionTriplet, float]:
        """
        Lever 2: Purely derived from Open FAIR scenario ALEs aggregated via Copula Subadditivity.
        Zero dependency on Toil or Licensing.
        """
        n_scenarios = len(scenario_ales)
        if n_scenarios == 0:
            return PertDistributionTriplet(min=0.0, mode=0.0, max=0.0), 1.0

        unadjusted_sum = PertDistributionTriplet(min=0.0, mode=0.0, max=0.0)
        for ale in scenario_ales:
            unadjusted_sum = unadjusted_sum.add_triplet(ale)

        copula_factor = self.compute_copula_diversification_factor(n_scenarios)
        diversified_portfolio_ale = unadjusted_sum.scale(copula_factor)

        return diversified_portfolio_ale, copula_factor

    def compute_lever_3_contractual_escalation(
        self,
        industry: IndustryVertical,
        maturity_tier: MaturityTier,
        annual_revenue_usd: Optional[float] = None,
        total_employee_headcount: Optional[int] = None,
        has_eosl_penalty: bool = False,
    ) -> tuple[PertDistributionTriplet, PertDistributionTriplet]:
        """
        Lever 3: Purely derived from Macroeconomic Baseline IT Spend * Domain Allocation * Escalation Rate.
        Strictly orthogonal to Lever 1 (Toil) and Lever 2 (Outages).
        """
        macro_bench = self.benchmarks.industry_macro_benchmarks.get(
            industry,
            self.benchmarks.industry_macro_benchmarks[IndustryVertical.DEFAULT_ENTERPRISE],
        )

        # Resolve Gross Annual Revenue (Scale Agnostic)
        resolved_revenue: float
        if annual_revenue_usd is not None and annual_revenue_usd > 0.0:
            resolved_revenue = annual_revenue_usd
        elif total_employee_headcount is not None and total_employee_headcount > 0:
            resolved_revenue = float(total_employee_headcount) * macro_bench.implied_revenue_per_employee_usd
        else:
            raise ActuarialSynthesizerError(
                "Scale Agnosticism Error: Either 'annual_revenue_usd' (>0) or "
                "'total_employee_headcount' (>0) must be provided to anchor Lever 3."
            )

        # 1. Calculate Total Enterprise IT Spend Triplet
        baseline_it_spend = macro_bench.it_spend_to_revenue_ratio.scale(resolved_revenue)

        # 2. Isolate Domain-Addressable Infrastructure Spend
        domain_ratio = self.benchmarks.contractual_escalation_parameters.default_domain_spend_allocation_ratio
        addressable_spend = baseline_it_spend.multiply_triplet(domain_ratio)

        # 3. Apply Maturity-Driven Annual Escalation Rate
        escalation_rates = self.benchmarks.contractual_escalation_parameters.annual_escalation_rates_by_maturity
        base_escalation_triplet = escalation_rates[maturity_tier]

        # 4. Optional EOSL Surcharge from declarative rate_card.json
        if has_eosl_penalty:
            eosl_mod = float(
                self.rate_card.get("vendor_licensing_modifiers", {}).get("eosl_extended_support_surcharge", 0.0)
            )
            surcharge_multiplier = 1.0 + eosl_mod
            effective_escalation = base_escalation_triplet.scale(surcharge_multiplier)
        else:
            effective_escalation = base_escalation_triplet

        contractual_drag_usd = addressable_spend.multiply_triplet(effective_escalation)
        return contractual_drag_usd, baseline_it_spend

    def synthesize_orthogonal_coi(
        self,
        annual_wasted_hours: float,
        scenario_ales: List[PertDistributionTriplet],
        industry: IndustryVertical,
        maturity_tier: MaturityTier,
        annual_revenue_usd: Optional[float] = None,
        total_employee_headcount: Optional[int] = None,
        role_key: str = "DEFAULT_BLENDED_FTE",
        has_eosl_penalty: bool = False,
    ) -> OrthogonalCOISynthesisResult:
        """
        Executes full orthogonal synthesis of the Cost of Inaction across R^3 economic space.
        """
        lever_1 = self.compute_lever_1_engineering_toil(
            annual_wasted_hours=annual_wasted_hours,
            role_key=role_key,
        )

        lever_2, copula_factor = self.compute_lever_2_probabilistic_outage_portfolio(
            scenario_ales=scenario_ales,
        )

        lever_3, baseline_it_spend = self.compute_lever_3_contractual_escalation(
            industry=industry,
            maturity_tier=maturity_tier,
            annual_revenue_usd=annual_revenue_usd,
            total_employee_headcount=total_employee_headcount,
            has_eosl_penalty=has_eosl_penalty,
        )

        total_coi = lever_1.add_triplet(lever_2).add_triplet(lever_3)

        return OrthogonalCOISynthesisResult(
            lever_1_engineering_toil_usd=lever_1,
            lever_2_probabilistic_outage_ale_usd=lever_2,
            lever_3_contractual_escalation_usd=lever_3,
            total_cost_of_inaction_usd=total_coi,
            applied_copula_diversification_factor=copula_factor,
            scenario_cardinality_n=len(scenario_ales),
            derived_baseline_it_spend_usd=baseline_it_spend,
        )
```

---

## 4. QUALITY GATES & VERIFICATION ORACLES

To guarantee that the numerological antipattern can never regress into the codebase, the following deterministic `pytest` suite (`tests/unit/test_phase25_actuarial_purity.py`) serves as a mandatory CI/CD blocking gate.

### 4.1 Verification Suite: `tests/unit/test_phase25_actuarial_purity.py`

```python
import ast
from pathlib import Path
import pytest

from src.models.actuarial_contracts import (
    IndustryVertical,
    MaturityTier,
    PertDistributionTriplet,
)
from src.synthesizers.chapter4_synthesizer import (
    ActuarialSynthesizerError,
    Chapter4ActuarialSynthesizer,
)


@pytest.fixture(scope="module")
def synthesizer(tmp_path_factory) -> Chapter4ActuarialSynthesizer:
    """Provisions a hermetic synthesizer instance backed by Phase 25 declarative JSON configs."""
    config_dir = tmp_path_factory.mktemp("engine_config")

    benchmarks_json = """
    {
      "schema_version": "25.0.0",
      "description": "Hermetic Test Benchmarks",
      "copula_aggregation_parameters": {
        "baseline_pairwise_correlation_rho": 0.25,
        "tail_dependence_surcharge_tau": 0.08,
        "min_diversification_floor": 0.35
      },
      "toil_efficiency_parameters": {
        "productivity_recapture_factor": { "min": 0.50, "mode": 0.65, "max": 0.80 },
        "annual_productive_hours_per_fte": 1880.0
      },
      "contractual_escalation_parameters": {
        "default_domain_spend_allocation_ratio": { "min": 0.14, "mode": 0.20, "max": 0.28 },
        "annual_escalation_rates_by_maturity": {
          "TIER_1_AD_HOC": { "min": 0.12, "mode": 0.18, "max": 0.25 },
          "TIER_2_FRAGMENTED": { "min": 0.08, "mode": 0.12, "max": 0.17 },
          "TIER_3_STANDARDIZED": { "min": 0.04, "mode": 0.07, "max": 0.10 },
          "TIER_4_OPTIMIZED": { "min": 0.02, "mode": 0.035, "max": 0.05 }
        }
      },
      "industry_macro_benchmarks": {
        "FINANCIAL_SERVICES": {
          "it_spend_to_revenue_ratio": { "min": 0.065, "mode": 0.082, "max": 0.105 },
          "implied_revenue_per_employee_usd": 650000.0
        },
        "MANUFACTURING": {
          "it_spend_to_revenue_ratio": { "min": 0.015, "mode": 0.024, "max": 0.035 },
          "implied_revenue_per_employee_usd": 380000.0
        },
        "DEFAULT_ENTERPRISE": {
          "it_spend_to_revenue_ratio": { "min": 0.030, "mode": 0.045, "max": 0.060 },
          "implied_revenue_per_employee_usd": 400000.0
        }
      }
    }
    """

    rate_card_json = """
    {
      "schema_version": "25.0.0",
      "currency": "USD",
      "labor_rates_hourly_blended": {
        "DEFAULT_BLENDED_FTE": { "min": 80.0, "mode": 105.0, "max": 135.0 }
      },
      "vendor_licensing_modifiers": {
        "eosl_extended_support_surcharge": 0.22
      }
    }
    """

    (config_dir / "actuarial_benchmarks.json").write_text(benchmarks_json.strip(), encoding="utf-8")
    (config_dir / "rate_card.json").write_text(rate_card_json.strip(), encoding="utf-8")

    return Chapter4ActuarialSynthesizer(config_dir=config_dir)


class TestOrthogonalVectorIndependence:
    """
    ORACLE 1: Proves that ∂(Lever 3)/∂(Lever 1) == 0 and ∂(Lever 3)/∂(Lever 2) == 0.
    Mutating Toil or Outage ALE by orders of magnitude must result in 0.00 variance in Lever 3.
    """

    def test_lever_3_invariant_under_extreme_outage_and_toil_mutations(
        self, synthesizer: Chapter4ActuarialSynthesizer
    ) -> None:
        # Scenario A: Zero outages, Zero toil
        result_zero_operational_pain = synthesizer.synthesize_orthogonal_coi(
            annual_wasted_hours=0.0,
            scenario_ales=[],
            industry=IndustryVertical.FINANCIAL_SERVICES,
            maturity_tier=MaturityTier.TIER_2_FRAGMENTED,
            annual_revenue_usd=1_000_000_000.0,  # $1B Revenue
        )

        # Scenario B: Catastrophic outages ($500M) and massive toil (100,000 hours)
        catastrophic_ales = [
            PertDistributionTriplet(min=100_000_000.0, mode=250_000_000.0, max=500_000_000.0)
        ]
        result_catastrophic_pain = synthesizer.synthesize_orthogonal_coi(
            annual_wasted_hours=100_000.0,
            scenario_ales=catastrophic_ales,
            industry=IndustryVertical.FINANCIAL_SERVICES,
            maturity_tier=MaturityTier.TIER_2_FRAGMENTED,
            annual_revenue_usd=1_000_000_000.0,  # Same $1B Revenue
        )

        # Assert Lever 1 and Lever 2 changed dramatically
        assert result_zero_operational_pain.lever_1_engineering_toil_usd.mode == 0.0
        assert result_catastrophic_pain.lever_1_engineering_toil_usd.mode > 5_000_000.0
        assert result_zero_operational_pain.lever_2_probabilistic_outage_ale_usd.mode == 0.0
        assert result_catastrophic_pain.lever_2_probabilistic_outage_ale_usd.mode == 250_000_000.0

        # CRITICAL INVARIANT: Lever 3 (Contractual Drag) MUST BE IDENTICAL TO THE CENT
        assert (
            result_zero_operational_pain.lever_3_contractual_escalation_usd
            == result_catastrophic_pain.lever_3_contractual_escalation_usd
        )
        assert result_zero_operational_pain.lever_3_contractual_escalation_usd.mode > 0.0


class TestCopulaSubadditivityStability:
    """
    ORACLE 2: Proves that the Copula Diversification Factor is strictly bounded in (0, 1]
    and never degenerates into negative numbers at high scenario cardinality (N > 20).
    """

    @pytest.mark.parametrize("n_scenarios", [1, 2, 5, 10, 20, 21, 50, 100, 10_000])
    def test_copula_bounds_and_monotonic_asymptote(
        self, synthesizer: Chapter4ActuarialSynthesizer, n_scenarios: int
    ) -> None:
        factor = synthesizer.compute_copula_diversification_factor(n_scenarios)

        if n_scenarios == 1:
            assert factor == 1.0
        else:
            # Must be strictly positive, strictly less than 1.0, and respect the floor (0.35)
            assert 0.35 <= factor < 1.0

    def test_monotonic_decrease_with_scenario_cardinality(
        self, synthesizer: Chapter4ActuarialSynthesizer
    ) -> None:
        factors = [synthesizer.compute_copula_diversification_factor(n) for n in range(1, 30)]
        for i in range(len(factors) - 1):
            assert factors[i] >= factors[i + 1], (
                f"Non-monotonic copula behavior between N={i+1} ({factors[i]}) "
                f"and N={i+2} ({factors[i+1]})"
            )


class TestScaleAgnosticism:
    """
    ORACLE 3: Proves scale invariance from a $50M regional manufacturer to a $100B global bank,
    including employee-headcount fallback mechanics.
    """

    def test_50m_regional_manufacturer_vs_100b_global_bank(
        self, synthesizer: Chapter4ActuarialSynthesizer
    ) -> None:
        mfg_50m = synthesizer.synthesize_orthogonal_coi(
            annual_wasted_hours=2000.0,
            scenario_ales=[PertDistributionTriplet(min=50_000.0, mode=150_000.0, max=400_000.0)],
            industry=IndustryVertical.MANUFACTURING,
            maturity_tier=MaturityTier.TIER_2_FRAGMENTED,
            annual_revenue_usd=50_000_000.0,
        )

        bank_100b = synthesizer.synthesize_orthogonal_coi(
            annual_wasted_hours=200_000.0,
            scenario_ales=[PertDistributionTriplet(min=10_000_000.0, mode=45_000_000.0, max=120_000_000.0)],
            industry=IndustryVertical.FINANCIAL_SERVICES,
            maturity_tier=MaturityTier.TIER_2_FRAGMENTED,
            annual_revenue_usd=100_000_000_000.0,
        )

        # $50M Manufacturer: IT Spend Mode = 2.4% ($1.2M), Domain = 20% ($240k), Escalation = 12% ($28.8k)
        assert mfg_50m.lever_3_contractual_escalation_usd.mode == pytest.approx(28_800.0, rel=1e-3)

        # $100B Bank: IT Spend Mode = 8.2% ($8.2B), Domain = 20% ($1.64B), Escalation = 12% ($196.8M)
        assert bank_100b.lever_3_contractual_escalation_usd.mode == pytest.approx(196_800_000.0, rel=1e-3)

    def test_employee_headcount_fallback_when_revenue_omitted(
        self, synthesizer: Chapter4ActuarialSynthesizer
    ) -> None:
        # 1,000 employees in Manufacturing * $380,000/employee = $380M implied revenue
        res = synthesizer.synthesize_orthogonal_coi(
            annual_wasted_hours=500.0,
            scenario_ales=[],
            industry=IndustryVertical.MANUFACTURING,
            maturity_tier=MaturityTier.TIER_3_STANDARDIZED,
            annual_revenue_usd=None,
            total_employee_headcount=1000,
        )
        # Expected IT Spend Mode = $380M * 0.024 = $9,120,000
        assert res.derived_baseline_it_spend_usd.mode == pytest.approx(9_120_000.0, rel=1e-3)


class TestStaticASTZeroMagicNumbers:
    """
    ORACLE 4: AST Static Analysis Gate.
    Scans chapter4_synthesizer.py to ensure legacy magic numbers (0.60, 0.45, 0.05)
    do not exist anywhere in the Python AST.
    """

    FORBIDDEN_FLOATS = {0.6, 0.60, 0.45, 0.05}

    def test_no_forbidden_magic_floats_in_synthesizer_ast(self) -> None:
        synthesizer_path = Path("src/synthesizers/chapter4_synthesizer.py")
        if not synthesizer_path.exists():
            pytest.skip("Synthesizer file path not mounted in current working directory.")

        source_code = synthesizer_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code)

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                if node.value in self.FORBIDDEN_FLOATS:
                    violations.append((node.lineno, node.value))

        assert not violations, (
            f"CRITICAL ARCHITECTURAL VIOLATION: Forbidden magic float constants detected in "
            f"chapter4_synthesizer.py at (line, value): {violations}. Move all parameters to engine_config/."
        )
```

---

## 5. EXECUTION CHECKLIST & CUTOVER SEQUENCE

1. **Step 1 (Config Provisioning):** Commit `engine_config/actuarial_benchmarks.json` and update `engine_config/rate_card.json` with the Phase 25.0.0 schema.
2. **Step 2 (Contract Compilation):** Deploy `src/models/actuarial_contracts.py` and verify Pydantic V2 schema validation against the JSON files.
3. **Step 3 (Synthesizer Cutover):** Replace the legacy `baseline_economic_anchor` and linear subadditivity equations in `src/synthesizers/chapter4_synthesizer.py` with `Chapter4ActuarialSynthesizer`.
4. **Step 4 (Oracle Verification):** Execute `pytest tests/unit/test_phase25_actuarial_purity.py -v` and confirm 100% pass rate across all four verification oracles before merging to `main`.