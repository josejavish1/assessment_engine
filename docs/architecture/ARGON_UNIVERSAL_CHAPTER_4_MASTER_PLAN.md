# ARGON UNIVERSAL CHAPTER 4 MASTER PLAN
**Document ID:** `ARGON-ARCH-CH4-2026-REV5`  
**Target Location:** `docs/architecture/ARGON_UNIVERSAL_CHAPTER_4_MASTER_PLAN.md`  
**Classification:** Production Architecture Specification — Actuarial & Rendering Subsystem  
**Author:** Gemini-4-Argon (Chief Systems Architect, Actuarial Fellow, Global Managing Partner)  
**Status:** MANDATORY / NON-NEGOTIABLE EXECUTION BLUEPRINT

---

## 1. EXECUTIVE SUMMARY & ACTUARIAL MANIFESTO

### 1.1 The Crisis of Credibility in Traditional Technical Due Diligence
Standard technical due diligence assessments produced by legacy consultancies (McKinsey, Gartner, Bain, Big-4) suffer from two fatal defects in their economic risk evaluations:
1. **Qualitative Hand-Waving:** Presenting heatmaps populated by arbitrary "High / Medium / Low" ordinal labels without financial grounding, rendering them useless to Private Equity Investment Committees, CFOs, and Board Audit Committees.
2. **The Actuarial Fallacy of False Precision:** Where financial quantification is attempted, legacy tools conflate deterministic operational inefficiency with stochastic catastrophe, outputting absurdly precise figures (e.g., `"Annual Risk Exposure: $142,853.42"`) that collapse under cross-examination by actuarial fellows or quantitative risk officers.

### 1.2 The Argon Actuarial Manifesto: Open FAIR Monism & Structural Decoupling
To establish the Assessment Engine as the undisputed #1 global standard across all 10 Specialist Domain Annexes, Chapter 4 (*Infrastructure Risk Economic Evaluation & Cost of Inaction*) is governed by **Strict Actuarial Monism** grounded in the **Open FAIR™ (Factor Analysis of Information Risk)** standard (ISO/IEC 27005 & Open Group C13K).

We enforce a strict structural decoupling between two fundamentally distinct economic phenomena:

1. **Chronic Operational Drag ($COD$):** Deterministic, ongoing fiscal erosion caused by architectural entropy, manual firefighting, unpatched legacy runtimes, and suboptimal vendor structures. It occurs with probability $P = 1.0$ every fiscal year the status quo is maintained.
   $$\text{COD} = \text{Manual Engineering Toil} + \text{Contractual / Licensing Escalation Penalty}$$
2. **Probabilistic Event Risk ($ALE$):** Stochastic fiscal loss resulting from discrete failure events (ransomware execution, core switch collapse, database corruption, regulatory audit sanction). Modeled via Monte Carlo-calibrated lognormal/PERT distributions parameterized by **Loss Event Frequency ($LEF$)** and **Loss Magnitude ($LM$)**.
   $$\text{ALE} = \sum_{i=1}^{N} \left( \text{LEF}_i \times \text{LM}_i \right) \times \Psi_{\text{portfolio}}$$

### 1.3 Eradicating the Split-Brain Anti-Pattern
Historically, assessment engines suffered from "Split-Brain Calculation": Section 4.1 (Cost of Inaction) computed financial totals using heuristic multipliers, Section 4.2 (Risk Concentration & Heatmap) counted findings using static severity weights, and Section 4.3 (Technical Risk Cards) generated individual risk exposures on the fly during AST rendering. This caused mathematical contradictions between executive tables and technical cards.

**Architectural Law:** Under the Argon Architecture, **100% of mathematical computation is executed upstream** within a deterministic, pure-Python actuarial engine (`Chapter4ActuarialEngine`). It emits a single, frozen, immutable Pydantic V2 domain artifact: `Chapter4SynthesisPayload`. The downstream presentation layer (`PayloadToASTBridge`) is reduced to a **zero-math, pure functional projection** of this payload into Pandoc/LaTeX AST nodes.

---

## 2. UNIVERSAL MATHEMATICAL FORMULATION

To operate universally across any enterprise scale ($50M mid-market to $100B+ mega-cap), industry vertical (OT manufacturing, Tier-1 banking, clinical healthcare, SaaS), and maturity state (CMMI Level 1 to Level 5), all equations are parameterized via externalized configuration catalogs (`EnterpriseRegistry`, `RateCardCatalog`, `VerticalCalibrationCatalog`).

### 2.1 Enterprise Scale & Hourly Downtime Derivation
Let $\mathcal{E}$ be the target enterprise profile resolved from `EnterpriseRegistry`. We avoid hardcoded downtime costs by deriving the **Baseline Hourly Operational Value ($\mathcal{V}_{\text{hour}}$)** and **Critical Downtime Cost ($\mathcal{C}_{\text{down}}$)** from empirical enterprise telemetry:

$$\mathcal{V}_{\text{hour}} = \frac{R_{\text{annual}}}{H_{\text{op}}(\mathcal{V}_{\text{vertical}})}$$

Where:
* $R_{\text{annual}} \in \mathbb{R}^+$ is the verified Annual Gross Revenue in base currency.
* $H_{\text{op}}(\mathcal{V}_{\text{vertical}}) \in [2080, 8760]$ is the annual operational hour denominator governed by the industry vertical (e.g., $8760\text{ hrs}$ for 24/7 Continuous Process Manufacturing, Banking, or Energy Grids; $2920\text{ hrs}$ for single-shift discrete operations).

The **Effective Hourly Downtime Loss ($\mathcal{C}_{\text{down}}$)** incorporates vertical-specific elasticity and SLA penalty multipliers:

$$\mathcal{C}_{\text{down}} = \mathcal{V}_{\text{hour}} \times \left( 1 - \theta_{\text{recovery}}(\mathcal{V}_{\text{vertical}}) \right) + \Lambda_{\text{SLA}}(\mathcal{E}) + \left( N_{\text{emp}} \times \rho_{\text{idle}} \times W_{\text{blended}} \right)$$

Where:
* $\theta_{\text{recovery}} \in [0.0, 0.85]$ is the **Revenue Deferral Recovery Factor** (e.g., $0.05$ for High-Frequency Trading or Emergency Clinical Care where lost minutes are permanently lost; $0.65$ for B2B Batch Manufacturing where delayed orders can be fulfilled via overtime).
* $\Lambda_{\text{SLA}}(\mathcal{E})$ is the contractual SLA penalty rate per hour.
* $N_{\text{emp}}$ is total impacted headcount, $\rho_{\text{idle}} \in [0, 1]$ is the operational dependency ratio, and $W_{\text{blended}}$ is the blended hourly employee cost from `RateCardCatalog`.

### 2.2 Dynamic CMMI Maturity Loss Equations (Level 1 to Level 5)
A critical failure of naive risk engines is applying static failure probabilities regardless of the organization's operational maturity. In the Argon Engine, the target domain's evaluated CMMI maturity score $M \in [1.0, 5.0]$ dynamically modulates both **Vulnerability ($\text{Vuln}$)** and **Mean Time To Recover ($\text{MTTR}$)**.

#### Vulnerability Moderation Function $\Omega_{\text{vuln}}(M)$:
In Open FAIR, $\text{LEF} = \text{TEF} \times \text{Vuln}$, where $\text{TEF}$ is Threat Event Frequency (governed by vertical threat landscape and asset exposure) and $\text{Vuln} \in (0, 1)$ is the probability that a threat event results in a loss event.

$$\text{Vuln}(s, M) = \text{ clamp}\left( \beta_0(s) \times e^{-\lambda_v (M - 1.0)}, \,\, 0.01, \,\, 0.99 \right)$$

Where $s \in \{\text{CRITICAL}, \text{HIGH}, \text{MEDIUM}, \text{LOW}\}$ is the intrinsic technical severity of the finding, $\beta_0(s)$ is the CMMI Level 1 baseline vulnerability susceptibility, and $\lambda_v = 0.55$ is the empirical maturity decay constant:

| Maturity Level ($M$) | Governance State | Vulnerability Multiplier $e^{-\lambda_v(M-1)}$ | MTTR Amplification Factor $\Phi_{\text{MTTR}}(M)$ | Chronic Toil Multiplier $\tau(M)$ |
| :--- | :--- | :---: | :---: | :---: |
| **CMMI 1.0 (Initial)** | Ad-hoc, Heroic Firefighting | $1.000\times$ | $2.40\times$ | $1.85\times$ |
| **CMMI 2.0 (Managed)** | Reactive, Basic Monitoring | $0.577\times$ | $1.65\times$ | $1.35\times$ |
| **CMMI 3.0 (Defined)** | Standardized, Runbooks Exist | $0.333\times$ | $1.00\times$ | $1.00\times$ |
| **CMMI 4.0 (Quantitatively Managed)** | Automated Telemetry & SLOs | $0.192\times$ | $0.55\times$ | $0.65\times$ |
| **CMMI 5.0 (Optimizing)** | Self-Healing, Chaos-Tested | $0.111\times$ | $0.25\times$ | $0.35\times$ |

#### Loss Magnitude Formulation ($\text{LM}_i$):
For each technical finding $i$, the Loss Magnitude Interval $[\text{LM}_{i,\min}, \text{LM}_{i,\max}]$ is decomposed into Primary Loss ($\text{PL}_i$, direct outage and restoration cost) and Secondary Loss ($\text{SL}_i$, regulatory fines, reputation, legal defense):

$$\text{PL}_i(M) = \left( \text{MTTR}_{\text{base}}(i) \times \Phi_{\text{MTTR}}(M) \times \mathcal{C}_{\text{down}} \times \alpha_{\text{blast}}(i) \right) + \left( H_{\text{remed}}(i) \times R_{\text{tier3}} \right)$$

$$\text{SL}_i(\mathcal{E}) = P_{\text{secondary}}(i) \times \left( \text{Fine}_{\text{reg}}(\mathcal{E}, i) + \text{Cost}_{\text{ir}}(\mathcal{E}) \right)$$

$$\text{LM}_i = \text{PL}_i(M) + \text{SL}_i(\mathcal{E})$$

Where $\alpha_{\text{blast}}(i) \in (0, 1]$ is the **Blast Radius Factor** (fraction of enterprise infrastructure crippled by finding $i$), $H_{\text{remed}}(i)$ is emergency forensic/restoration engineering hours, and $R_{\text{tier3}}$ is the Senior Specialist Emergency Rate resolved from `RateCardCatalog`.

### 2.3 Chronic Operational Drag ($COD$) Formulation
Chronic Operational Drag represents the guaranteed annual cash burn wasted on maintaining broken architectures:

$$\text{COD}_{\text{toil}} = \sum_{i=1}^{N} \left( H_{\text{toil\_weekly}}(i) \times 52 \times \tau(M) \times R_{\text{ops}} \right)$$

$$\text{COD}_{\text{escalation}} = C_{\text{licensing\_base}}(\mathcal{E}) \times \left( \gamma_{\text{eosl\_penalty}} + \gamma_{\text{cloud\_waste}} \right)$$

$$\text{COD}_{\text{total}} = \text{COD}_{\text{toil}} + \text{COD}_{\text{escalation}}$$

### 2.4 Portfolio Sub-Additivity Factor ($\Psi_{\text{portfolio}}$)
In complex infrastructure domains, multiple technical findings often share an underlying failure domain (e.g., three separate findings regarding missing BGP route filtering, outdated core switch firmware, and lack of out-of-band management all contribute to the same "Core Network Partition" outage event). Summing their individual $\text{ALE}_i$ values linearly ($\sum \text{ALE}_i$) violates probability theory by double-counting overlapping downtime hours.

We introduce the **Portfolio Sub-Additivity & Shared Blast-Radius Factor ($\Psi_{\text{portfolio}}$)**:

Let findings $i \in \{1 \dots N\}$ be partitioned into $K$ orthogonal Failure Domains $\mathcal{D}_1, \mathcal{D}_2, \dots, \mathcal{D}_K$ (e.g., *Compute Virtualization*, *Storage SAN*, *Perimeter Security*, *Identity/AD*). Within each Failure Domain $\mathcal{D}_k$ of cardinality $n_k = |\mathcal{D}_k|$:

$$\text{ALE}(\mathcal{D}_k) = \left( \max_{j \in \mathcal{D}_k} \text{ALE}_j \right) + \sum_{\substack{j \in \mathcal{D}_k \\ j \neq j_{\max}}} \left( \text{ALE}_j \times \delta_{\text{corr}}^{(\text{rank}(j) - 1)} \right)$$

Where $\delta_{\text{corr}} \in [0.35, 0.75]$ is the **Intra-Domain Marginal Contribution Decay Factor** (default $0.55$). The total Portfolio Annualized Loss Expectancy is then:

$$\text{ALE}_{\text{portfolio}} = \sum_{k=1}^{K} \text{ALE}(\mathcal{D}_k), \quad \text{with implied } \Psi_{\text{portfolio}} = \frac{\text{ALE}_{\text{portfolio}}}{\sum_{i=1}^{N} \text{ALE}_i} \in (0.40, 1.00]$$

### 2.5 Total Cost of Inaction ($COI$) & 3-Year TCO Horizon
The **Annualized Cost of Inaction ($\text{COI}_{\text{annual}}$)** is the sum of deterministic drag and sub-additive probabilistic risk:

$$\text{COI}_{\text{annual}} = \left[ \text{COD}_{\text{total},\min} + \text{ALE}_{\text{portfolio},\min}, \quad \text{COD}_{\text{total},\max} + \text{ALE}_{\text{portfolio},\max} \right]$$

Over a standard 36-month Private Equity / Strategic Planning horizon, accounting for architectural entropy compounding at rate $r_{\text{entropy}} = 0.08$ per annum:

$$\text{COI}_{3\text{yr}} = \sum_{t=1}^{3} \text{COI}_{\text{annual}} \times (1 + r_{\text{entropy}})^{t-1}$$

### 2.6 The Actuarial Significant Figures Rounding Policy
To eradicate the **Actuarial Fallacy of False Precision**, every monetary figure emitted into `Chapter4SynthesisPayload` MUST pass through the deterministic rounding operator $\mathcal{R}_{\text{actuarial}}(x)$ prior to serialization or aggregation reconciliation.

$$\mathcal{R}_{\text{actuarial}}(x) = \text{round\_half\_up}\left( \frac{x}{S(x)} \right) \times S(x)$$

Where the **Step Quantum $S(x)$** is dynamically selected by order of magnitude:

| Magnitude Band ($|x|$ in Base Currency) | Step Quantum $S(x)$ | Valid Output Examples (EUR) | Invalid (Forbidden) Examples |
| :--- | :---: | :--- | :--- |
| $0 \le |x| < 1,000$ | $50$ | `450 €`, `800 €` | `432,18 €`, `789 €` |
| $1,000 \le |x| < 10,000$ | $250$ | `2.500 €`, `8.750 €` | `2.412 €`, `8.710,50 €` |
| $10,000 \le |x| < 100,000$ | $1,000$ | `14.000 €`, `55.000 €` | `14.230 €`, `55.412 €` |
| $100,000 \le |x| < 1,000,000$ | $5,000$ | `145.000 €`, `680.000 €` | `146.200 €`, `681.900 €` |
| $1,000,000 \le |x| < 10,000,000$ | $25,000$ | `1.450.000 €`, `8.225.000 €` | `1.452.000 €`, `8.219.400 €` |
| $|x| \ge 10,000,000$ | $100,000$ | `14.500.000 €`, `120.400.000 €` | `14.512.000 €` |

**Reconciliation Law (The Bottom-Line Invariant):** We round leaf components first, and compute parent totals as the exact sum of the already-rounded leaf intervals. We NEVER round a parent total independently of its displayed children, guaranteeing that any executive auditing a table with a calculator verifies $A + B + C = \text{Total}$ with **zero rounding discrepancy**.

---

## 3. THE 5-PHASE INDUSTRIAL EXECUTION ROADMAP

```
+---------------------------------------------------------------------------------------------------+
|                        ARGON CHAPTER 4 MONISTIC EXECUTION PIPELINE                                |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [EnterpriseRegistry]   [RateCardCatalog]   [VerticalCalibrationCatalog]   [RegulatoryCatalog]    |
|            \                    |                        |                         /              |
|             v                   v                        v                        v               |
|  +---------------------------------------------------------------------------------------------+  |
|  | PHASE 2: Chapter4Synthesizer (Upstream Domain & Maturity Calibration)                       |  |
|  | - Ingests raw technical findings from Specialist Annexes (01..10)                           |  |
|  | - Resolves CMMI Maturity (1..5), Vertical Blast Radius, and Applicable Regulatory Frameworks|  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                 |                                                 |
|                                                 v                                                 |
|  +---------------------------------------------------------------------------------------------+  |
|  | PHASE 1: Chapter4ActuarialEngine (Open FAIR Mathematical Core)                              |  |
|  | - Computes COD (Toil + Escalation) & ALE (LEF * LM) with Portfolio Sub-Additivity           |  |
|  | - Applies Actuarial Significant Figures Rounding Policy & Bottom-Line Reconciliation        |  |
|  | - Emits Immutable Pydantic V2 Artifact: Chapter4SynthesisPayload                            |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                 |                                                 |
|                                                 v                                                 |
|  +---------------------------------------------------------------------------------------------+  |
|  | PHASE 3: PayloadToASTBridge (Pure Functional AST Projection — ZERO MATH)                    |  |
|  | - Section 4.1: Cost of Inaction Executive Breakdown Table (COD + ALE = COI)                 |  |
|  | - Section 4.2: Strategic Risk Concentration & 5x5 Heatmap (Human-Readable Finding Titles)   |  |
|  | - Section 4.3: Actuarial Risk Cards (Top-N Critical/High Cards + Compact Residual Summary)  |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                 |                                                 |
|                                                 v                                                 |
|  +---------------------------------------------------------------------------------------------+  |
|  | PHASE 4 & 5: Multi-Vertical Calibration Suite & Continuous Quality Gate Tribunal            |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

### PHASE 1: Declarative Pydantic V2 Domain Schemas & Mathematical Engine
**Objective:** Construct the immutable, strongly-typed data contracts and pure actuarial calculation engine in `src/domain/actuarial/`. Zero presentation logic or hardcoded strings are permitted in this layer.

#### 1.1 File & Module Inventory
* `src/domain/actuarial/schemas.py`: Immutable Pydantic V2 models (`ConfigDict(frozen=True, extra="forbid")`).
* `src/domain/actuarial/rounding.py`: Implementation of the Actuarial Significant Figures Rounding Policy ($\mathcal{R}_{\text{actuarial}}$).
* `src/domain/actuarial/engine.py`: Implementation of `Chapter4ActuarialEngine` executing Open FAIR calculations, CMMI adjustments, and sub-additive portfolio aggregation.

#### 1.2 Production-Grade Reference Implementation (`src/domain/actuarial/schemas.py`)
```python
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Annotated, List, Tuple
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskSeverityTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FailureDomainCategory(str, Enum):
    COMPUTE_AND_VIRTUALIZATION = "COMPUTE_AND_VIRTUALIZATION"
    STORAGE_AND_BACKUP_INTEGRITY = "STORAGE_AND_BACKUP_INTEGRITY"
    NETWORK_CORE_AND_PERIMETER = "NETWORK_CORE_AND_PERIMETER"
    IDENTITY_AND_ACCESS_GOVERNANCE = "IDENTITY_AND_ACCESS_GOVERNANCE"
    OT_SCADA_AND_INDUSTRIAL_CONTROL = "OT_SCADA_AND_INDUSTRIAL_CONTROL"
    DATA_PLATFORM_AND_DATABASE = "DATA_PLATFORM_AND_DATABASE"
    CLOUD_CONTROL_PLANE = "CLOUD_CONTROL_PLANE"
    OBSERVABILITY_AND_INCIDENT_RESPONSE = "OBSERVABILITY_AND_INCIDENT_RESPONSE"
    SOFTWARE_SUPPLY_CHAIN_AND_CICD = "SOFTWARE_SUPPLY_CHAIN_AND_CICD"
    ITSM_AND_VENDOR_GOVERNANCE = "ITSM_AND_VENDOR_GOVERNANCE"


class MonetaryInterval(BaseModel):
    """Immutable, actuarially rounded monetary interval in base currency."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    lower_bound: int = Field(..., ge=0, description="Actuarially rounded minimum exposure.")
    upper_bound: int = Field(..., ge=0, description="Actuarially rounded maximum exposure.")
    currency_code: str = Field(..., min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def verify_bounds_ordering(self) -> MonetaryInterval:
        if self.lower_bound > self.upper_bound:
            raise ValueError(
                f"MonetaryInterval invariant violation: lower_bound ({self.lower_bound}) "
                f"exceeds upper_bound ({self.upper_bound})."
            )
        return self

    @property
    def midpoint(self) -> int:
        return (self.lower_bound + self.upper_bound) // 2

    def __add__(self, other: MonetaryInterval) -> MonetaryInterval:
        if self.currency_code != other.currency_code:
            raise ValueError(
                f"Currency mismatch in MonetaryInterval addition: "
                f"{self.currency_code} vs {other.currency_code}"
            )
        return MonetaryInterval(
            lower_bound=self.lower_bound + other.lower_bound,
            upper_bound=self.upper_bound + other.upper_bound,
            currency_code=self.currency_code,
        )


class HeatmapCoordinate(BaseModel):
    """Discrete 5x5 matrix coordinates (1 = Lowest, 5 = Highest)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    likelihood_index: int = Field(..., ge=1, le=5, description="X/Y axis: 1 (Rare) to 5 (Frequent)")
    impact_index: int = Field(..., ge=1, le=5, description="X/Y axis: 1 (Negligible) to 5 (Catastrophic)")
    display_title: str = Field(..., min_length=5, max_length=75, description="Human-readable physical title")
    severity_tier: RiskSeverityTier


class QuantifiedTechnicalRiskCard(BaseModel):
    """Single source of truth for an individual technical finding's actuarial profile."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    finding_uid: str = Field(..., description="Internal deterministic UUID; NEVER rendered as RVS code.")
    physical_title: str = Field(..., min_length=8, max_length=110, description="Human-readable executive title.")
    affected_infrastructure_scope: str = Field(..., min_length=5, max_length=160)
    failure_domain: FailureDomainCategory
    severity_tier: RiskSeverityTier

    # Open FAIR Parameters
    threat_event_frequency_min: float = Field(..., gt=0.0)
    threat_event_frequency_max: float = Field(..., gt=0.0)
    vulnerability_probability: float = Field(..., gt=0.0, lt=1.0)
    loss_event_frequency_min: float = Field(..., gt=0.0)
    loss_event_frequency_max: float = Field(..., gt=0.0)
    lef_qualitative_bandKey: str = Field(..., description="Locale key for frequency band label.")

    # Financial Magnitude & Annualized Exposure
    primary_loss_interval: MonetaryInterval
    secondary_loss_interval: MonetaryInterval
    single_loss_magnitude_interval: MonetaryInterval
    standalone_ale_interval: MonetaryInterval
    portfolio_adjusted_ale_interval: MonetaryInterval
    annual_chronic_toil_hours: int = Field(..., ge=0)
    annual_chronic_toil_cost: MonetaryInterval

    # Governance & Compliance
    heatmap_coordinate: HeatmapCoordinate
    applicable_regulations: Tuple[str, ...] = Field(default_factory=tuple)
    causal_chain_narrative: str = Field(..., min_length=30)
    remediation_horizon_days: int = Field(..., ge=1, le=1095)
    is_full_card_rendered: bool = Field(
        default=True,
        description="True for Top-N Critical/High findings; False for compact residual table rows.",
    )


class FailureDomainConcentrationRow(BaseModel):
    """Aggregated risk concentration row for Section 4.2."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_domain: FailureDomainCategory
    domain_display_name: str
    finding_count: int = Field(..., ge=1)
    critical_high_count: int = Field(..., ge=0)
    domain_subadditive_ale: MonetaryInterval
    domain_chronic_toil_cost: MonetaryInterval
    portfolio_share_percentage: float = Field(..., ge=0.0, le=100.0)


class ChronicOperationalDragBreakdown(BaseModel):
    """Deterministic annual operational drag (COD) for Section 4.1."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    annual_engineering_toil_hours: int = Field(..., ge=0)
    engineering_toil_cost_interval: MonetaryInterval
    contractual_and_licensing_escalation_interval: MonetaryInterval
    total_chronic_drag_interval: MonetaryInterval

    @model_validator(mode="after")
    def verify_cod_reconciliation(self) -> ChronicOperationalDragBreakdown:
        expected = (
            self.engineering_toil_cost_interval
            + self.contractual_and_licensing_escalation_interval
        )
        if (
            self.total_chronic_drag_interval.lower_bound != expected.lower_bound
            or self.total_chronic_drag_interval.upper_bound != expected.upper_bound
        ):
            raise ValueError(
                "COD Reconciliation Invariant Violated: "
                "total_chronic_drag_interval must equal exact sum of toil + escalation."
            )
        return self


class Chapter4SynthesisPayload(BaseModel):
    """
    THE MONISTIC ACTUARIAL CONTRACT.
    Sections 4.1, 4.2, and 4.3 are strictly projections of this single immutable object.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    annex_domain_id: str = Field(..., min_length=2)
    enterprise_id: str = Field(..., min_length=2)
    vertical_id: str = Field(..., min_length=2)
    evaluated_cmmi_maturity: float = Field(..., ge=1.0, le=5.0)
    currency_code: str = Field(..., min_length=3, max_length=3)

    # Section 4.1: Cost of Inaction (COD + ALE = COI)
    chronic_operational_drag: ChronicOperationalDragBreakdown
    unadjusted_standalone_ale_sum: MonetaryInterval
    portfolio_subadditivity_factor: float = Field(..., gt=0.0, le=1.0)
    portfolio_probabilistic_ale: MonetaryInterval
    annual_cost_of_inaction: MonetaryInterval
    three_year_compounded_coi: MonetaryInterval

    # Section 4.2: Risk Concentration & 5x5 Heatmap
    domain_concentrations: Tuple[FailureDomainConcentrationRow, ...]
    heatmap_cells: Tuple[HeatmapCoordinate, ...]

    # Section 4.3: Quantified Technical Risk Cards & Residual Summary
    quantified_risk_cards: Tuple[QuantifiedTechnicalRiskCard, ...]

    @model_validator(mode="after")
    def verify_global_actuarial_monism(self) -> Chapter4SynthesisPayload:
        # Invariant 1: Annual COI == Total COD + Portfolio Probabilistic ALE
        expected_coi = (
            self.chronic_operational_drag.total_chronic_drag_interval
            + self.portfolio_probabilistic_ale
        )
        if (
            self.annual_cost_of_inaction.lower_bound != expected_coi.lower_bound
            or self.annual_cost_of_inaction.upper_bound != expected_coi.upper_bound
        ):
            raise ValueError(
                f"Monism Violation (Sec 4.1): annual_cost_of_inaction "
                f"({self.annual_cost_of_inaction}) != COD + Portfolio ALE ({expected_coi})."
            )

        # Invariant 2: Sum of Domain Sub-Additive ALEs == Portfolio Probabilistic ALE
        domain_ale_sum_low = sum(d.domain_subadditive_ale.lower_bound for d in self.domain_concentrations)
        domain_ale_sum_high = sum(d.domain_subadditive_ale.upper_bound for d in self.domain_concentrations)
        if (
            domain_ale_sum_low != self.portfolio_probabilistic_ale.lower_bound
            or domain_ale_sum_high != self.portfolio_probabilistic_ale.upper_bound
        ):
            raise ValueError(
                f"Monism Violation (Sec 4.1 vs Sec 4.2): Domain ALE sum "
                f"[{domain_ale_sum_low}, {domain_ale_sum_high}] != Portfolio ALE "
                f"[{self.portfolio_probabilistic_ale.lower_bound}, {self.portfolio_probabilistic_ale.upper_bound}]."
            )

        # Invariant 3: Sum of Risk Cards Portfolio-Adjusted ALEs == Portfolio Probabilistic ALE
        card_ale_sum_low = sum(c.portfolio_adjusted_ale_interval.lower_bound for c in self.quantified_risk_cards)
        card_ale_sum_high = sum(c.portfolio_adjusted_ale_interval.upper_bound for c in self.quantified_risk_cards)
        if (
            card_ale_sum_low != self.portfolio_probabilistic_ale.lower_bound
            or card_ale_sum_high != self.portfolio_probabilistic_ale.upper_bound
        ):
            raise ValueError(
                f"Monism Violation (Sec 4.1 vs Sec 4.3): Card Portfolio-Adjusted ALE sum "
                f"[{card_ale_sum_low}, {card_ale_sum_high}] != Portfolio ALE "
                f"[{self.portfolio_probabilistic_ale.lower_bound}, {self.portfolio_probabilistic_ale.upper_bound}]."
            )

        # Invariant 4: Heatmap population matches card count
        if len(self.heatmap_cells) != len(self.quantified_risk_cards):
            raise ValueError(
                f"Heatmap population mismatch: {len(self.heatmap_cells)} coordinates vs "
                f"{len(self.quantified_risk_cards)} risk cards."
            )

        return self
```

#### 1.3 Production-Grade Rounding Implementation (`src/domain/actuarial/rounding.py`)
```python
from decimal import Decimal, ROUND_HALF_UP


def round_to_actuarial_significance(raw_amount: float | int | Decimal) -> int:
    """
    Enforces the Argon Actuarial Significant Figures Policy.
    Eliminates false precision (cents, single digits, arbitrary hundreds on millions).
    """
    val = Decimal(str(max(0.0, float(raw_amount))))
    if val == 0:
        return 0

    if val < Decimal("1000"):
        quantum = Decimal("50")
    elif val < Decimal("10000"):
        quantum = Decimal("250")
    elif val < Decimal("100000"):
        quantum = Decimal("1000")
    elif val < Decimal("1000000"):
        quantum = Decimal("5000")
    elif val < Decimal("10000000"):
        quantum = Decimal("25000")
    else:
        quantum = Decimal("100000")

    scaled = (val / quantum).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    result = int(scaled * quantum)
    return max(int(quantum), result)
```

#### 1.4 Phase 1 Quality Gate, Verification Oracle & Pre-Flight Invariant
* **Pre-Flight Invariant:** Zero imports from `src/presentation/` or `pandoc` inside `src/domain/actuarial/`.
* **Verification Oracle:** `pytest tests/unit/actuarial/test_schemas_and_rounding.py`
* **Quality Gate:** 100% branch coverage on `schemas.py`, `rounding.py`, and `engine.py`. Attempting to instantiate a `Chapter4SynthesisPayload` with a 1-euro discrepancy between Section 4.1, Section 4.2, and Section 4.3 must raise a Pydantic `ValidationError`.

---

### PHASE 2: Upstream Domain Synthesizer & Dynamic CMMI/Vertical Calibration
**Objective:** Build `Chapter4Synthesizer` in `src/application/synthesizers/chapter4_synthesizer.py` to ingest raw technical findings from any of the 10 Specialist Annexes and resolve all parameters dynamically from externalized configuration registries (`EnterpriseRegistry`, `RateCardCatalog`, `VerticalCalibrationCatalog`, `RegulatoryFrameworkCatalog`).

#### 2.1 Externalized Configuration Architecture (Zero Hardcoding)
No corporate names, currencies, labor rates, or regulatory acronyms may appear in Python code. They are loaded from validated JSON/YAML registries under `engine_config/`:
1. `engine_config/enterprises/{enterprise_id}.json`: Defines `annual_revenue`, `currency_code`, `employee_count`, `jurisdiction_codes`, `active_vertical_id`, and `licensing_baseline_spend`.
2. `engine_config/verticals/{vertical_id}.json`: Defines `annual_operational_hours`, `revenue_deferral_recovery_factor`, `intra_domain_correlation_decay`, and `threat_landscape_multiplier`.
3. `engine_config/rate_cards/{region_code}.json`: Defines `tier3_emergency_hourly_rate`, `devops_sre_hourly_rate`, and `blended_employee_hourly_cost`.
4. `engine_config/regulations/catalog.json`: Maps `(jurisdiction_code, vertical_id, failure_domain)` to exact statutory citations (e.g., `NIS2 Art. 21`, `DORA Art. 9`, `HIPAA §164.308`, `IEC 62443-3-3`, `GDPR Art. 32`, `PCI-DSS v4.0 Req. 10`).

#### 2.2 Eradication of Cryptic Machine Codes (`RVS01`, `FND-04`)
In legacy pipelines, findings were passed with machine identifiers (`RVS01`, `RVS02`, `RISK_NET_01`) that leaked into executive tables and heatmaps.
`Chapter4Synthesizer` enforces a **Semantic Title Normalizer**:
* Strips any leading or trailing machine codes (`r"^(?:RVS|FND|RSK| finding)[-_ ]?\d+[:\s-]*"`).
* Validates that `physical_title` is a substantive, human-readable engineering noun phrase (e.g., *"Single Point of Failure in Core SAN Storage Fabric"*, *"Unpatched EOL Windows Server 2012 Domain Controllers"*).

#### 2.3 Top-N Full Card Partitioning (Controlling Visual Density)
To prevent 30-page walls of repetitive tables when an annex identifies 18+ findings:
* Findings are ranked strictly in descending order by `portfolio_adjusted_ale_interval.midpoint`.
* The top $N_{\max} = 6$ findings (or all `CRITICAL` and `HIGH` findings up to 8) are flagged with `is_full_card_rendered = True` for detailed Actuarial Risk Cards in Section 4.3.
* Remaining `MEDIUM` and `LOW` findings are flagged with `is_full_card_rendered = False`. Their financial values remain 100% included in the mathematical totals and heatmap, and they are rendered in a single compact **Residual Risk Register Summary Table** at the end of Section 4.3.

#### 2.4 Phase 2 Quality Gate, Verification Oracle & Pre-Flight Invariant
* **Pre-Flight Invariant:** Static AST scan (`ruff` + custom regex guard) confirms zero hardcoded currency symbols (`€`, `$`, `£`), zero corporate names, and zero Spanish tokens in `src/application/synthesizers/`.
* **Verification Oracle:** `pytest tests/unit/synthesizers/test_chapter4_synthesizer.py`
* **Quality Gate:** Calling `Chapter4Synthesizer.synthesize()` across CMMI levels $1.0, 2.0, 3.0, 4.0, 5.0$ for the exact same finding set must demonstrate monotonic strict decrease in `annual_cost_of_inaction.midpoint`:
  $$\text{COI}(M=1) > \text{COI}(M=2) > \text{COI}(M=3) > \text{COI}(M=4) > \text{COI}(M=5)$$

---

### PHASE 3: Pure Presentation AST Projection & Radical Clutter Purge
**Objective:** Refactor `src/presentation/ast_bridge/chapter4_bridge.py` (`PayloadToASTBridge`) into a pure, stateless functional projection of `Chapter4SynthesisPayload`. Permanently purge all legacy inline math, didactic textbook tables, and cryptic machine codes.

#### 3.1 Radical Clutter Purge (What is Permanently Deleted)
1. **Eradicate the 4 Didactic Textbook Tables:** Legacy Chapter 4 wasted 2.5 pages printing academic definitions of Open FAIR terms (*"What is Threat Event Frequency?"*, *"How is Loss Magnitude defined?"*, *"Qualitative Severity Scale Legend"*). C-suite executives and Private Equity partners do not pay for textbook definitions. We replace all 4 didactic tables with a **single 3-line methodological callout box** at the top of Chapter 4.
2. **Eradicate Cryptic Machine Codes (`RVS01`..`RVS99`):** No machine IDs are ever projected into AST text nodes.
3. **Eradicate Inline Financial Multipliers:** Delete all occurrences of `* 1.25`, `* 0.15`, `round()`, or `sum()` inside `PayloadToASTBridge`.

#### 3.2 Structural Blueprint of Rendered Chapter 4
The projected AST for Chapter 4 follows a strict, executive-grade three-section architecture:

##### Section 4.1: Economic Evaluation of the Status Quo & Cost of Inaction
* **Executive Synthesis Callout Box:** High-impact summary stating the 12-month **Annual Cost of Inaction (`annual_cost_of_inaction`)** and the **36-Month Compounded TCO Erosion (`three_year_compounded_coi`)**, contrasted against the evaluated CMMI Maturity Level ($M$).
* **Table 4.1 — Consolidated Cost of Inaction Breakdown:**
  A clean, 5-row actuarial ledger reconciling Chronic Operational Drag ($COD$) and Probabilistic Event Risk ($ALE$):

| Economic Risk Vector | Actuarial Classification | Annualized Exposure Range | 36-Month Compounded Horizon |
| :--- | :--- | ---: | ---: |
| **1. Engineering Firefighting & Operational Toil** | Deterministic Drag ($P = 1.0$) | `[lower, upper]` | `[3yr_low, 3yr_high]` |
| **2. Legacy Licensing & Support Escalation Penalties** | Deterministic Drag ($P = 1.0$) | `[lower, upper]` | `[3yr_low, 3yr_high]` |
| **Subtotal: Chronic Operational Drag (COD)** | **Guaranteed Cash Erosion** | **`[cod_low, cod_high]`** | **`[3yr_cod_l, 3yr_cod_h]`** |
| **3. Portfolio Probabilistic Outage & Compliance Risk** | Stochastic Open FAIR ALE ($\Psi = \text{val}$) | `[ale_low, ale_high]` | `[3yr_ale_l, 3yr_ale_h]` |
| **TOTAL COST OF INACTION (STATUS QUO EXPOSURE)** | **Combined Economic Exposure** | **`[coi_low, coi_high]`** | **`[3yr_coi_l, 3yr_coi_h]`** |

##### Section 4.2: Strategic Risk Concentration & 5x5 Actuarial Heatmap
* **Table 4.2 — Risk Concentration by Failure Domain:** Projects `payload.domain_concentrations`, showing exact finding counts, sub-additive domain ALE, chronic toil cost, and percentage share of total portfolio risk.
* **Figure 4.1 — The 5x5 Actuarial Risk Heatmap (TikZ / LaTeX Matrix Projection):**
  * Axis X: **Annualized Loss Event Frequency ($LEF$)** from `1: Rare (<0.1/yr)` to `5: Frequent (>5.0/yr)`.
  * Axis Y: **Single Event Loss Magnitude ($LM$)** calibrated dynamically to enterprise scale from `1: Minor` to `5: Catastrophic`.
  * **Cell Content Rule:** Cells are populated with **human-readable physical risk titles** (truncated gracefully at 42 characters with ellipsis if needed, e.g., *"Core SAN Single Point of Failure"*), grouped cleanly with bullet points inside each cell. Zero `RVS` codes.

##### Section 4.3: Quantified Technical Risk Register (Actuarial Risk Cards)
* **Top-N Executive Actuarial Risk Cards (`is_full_card_rendered == True`):**
  Each card is rendered as an unbreakable LaTeX `minipage` / `tcolorbox` (`needspace{14\baselineskip}`) with a **strict 6-row specification** to guarantee vertical budget discipline (maximum 2 cards per page, zero orphan headers):
  1. **Header Bar:** `[SEVERITY BADGE]` | **Physical Risk Title** | **Portfolio-Adjusted ALE:** `[low, high] / yr`
  2. **Affected Scope & Domain:** `affected_infrastructure_scope` | **Failure Domain:** `failure_domain`
  3. **Actuarial Open FAIR Profile:** **LEF:** `lef_min`–`lef_max` events/yr (`lef_qualitative_bandKey`) | **Single Loss Magnitude (LM):** `[lm_low, lm_high]` | **Chronic Toil:** `hours` hrs/yr (`[toil_low, toil_high]`)
  4. **Causal Failure Chain:** `causal_chain_narrative` (concise 2–3 sentences linking technical root cause $\rightarrow$ operational outage $\rightarrow$ P&L impact).
  5. **Regulatory & Compliance Exposure:** `applicable_regulations` (dynamically resolved for the enterprise's jurisdiction and vertical).
  6. **Remediation Horizon:** Target mitigation window (`remediation_horizon_days` days) cross-referenced to Chapter 5 Roadmap.
* **Table 4.3 — Residual Medium/Low Risk Register Summary (`is_full_card_rendered == False`):**
  A compact 5-column ledger listing all remaining findings (`Physical Risk Title`, `Failure Domain`, `Severity`, `Chronic Toil Cost`, `Portfolio-Adjusted ALE`) so that the reader can visually verify that **every single finding in the annex sums to the exact portfolio total**.

#### 3.3 Localization & Internationalization (`engine_config/locales.json`)
All section headers, table column titles, frequency band descriptions, and currency formatting rules (`145.000 €` for `es-ES`/`de-DE`, `€145,000` or `$145,000` for `en-US`/`en-GB`, `¥22,500,000` for `ja-JP`) are resolved via `LocaleFormatter(locale_code)` reading from `engine_config/locales.json`.

#### 3.4 Phase 3 Quality Gate, Verification Oracle & Pre-Flight Invariant
* **Pre-Flight Invariant:** AST inspection of `chapter4_bridge.py` confirms zero arithmetic operators (`+`, `-`, `*`, `/`) applied to financial fields; all numbers are pulled directly from `Chapter4SynthesisPayload` attributes.
* **Verification Oracle:** `pytest tests/unit/presentation/test_chapter4_ast_bridge.py`
* **Quality Gate:** Compiled Markdown/LaTeX output contains zero occurrences of `RVS\d+`, zero didactic definition tables, and 100% diacritic integrity in target languages (`Evaluación`, `Económica`, `Pérdida`, `Exposición`, `Crítico`, `Año`).

---

### PHASE 4: Full Multi-Tenant & Multi-Vertical Calibration Suite
**Objective:** Prove that the engine adapts seamlessly without code changes across radically different enterprise scales, verticals, CMMI maturity levels, currencies, and regulatory regimes.

#### 4.1 The 6 Canonical Calibration Archetypes (`tests/calibration/archetypes/`)
We construct 6 comprehensive integration fixtures representing real-world due diligence engagements:

| Archetype ID | Profile & Industry Vertical | Annual Revenue & Scale | Evaluated Maturity | Base Currency & Locale | Resolved Regulatory Frameworks | Expected Annual COI Band |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **1. `ARCH_OT_MOLINS`** | Heavy Industrial & Cement Manufacturing (OT/SCADA + Legacy IT) | `€1,400M` (6,500 emp) | CMMI 1.8 | `EUR` (`es-ES`) | NIS2, IEC 62443, GDPR, ISO 27001 | `1.850.000 € – 3.400.000 €` |
| **2. `ARCH_BANK_TIER1`** | Global Systemic Investment & Retail Bank | `$85,000M` (140,000 emp) | CMMI 3.6 | `USD` (`en-US`) | DORA, Basel III, PCI-DSS v4.0, SOX, NYDFS | `$42,500,000 – $78,000,000` |
| **3. `ARCH_SAAS_MID`** | B2B Cloud-Native SaaS Platform | `$65M` (240 emp) | CMMI 3.2 | `USD` (`en-US`) | SOC2 Type II, GDPR Art. 32, ISO 27001 | `$380,000 – $720,000` |
| **4. `ARCH_HEALTH_ACUTE`** | Regional Acute Care Hospital Network (Clinical EHR/PACS) | `€420M` (4,200 emp) | CMMI 1.5 | `EUR` (`de-DE`) | NIS2 (Health), GDPR Art. 9, IEC 80001-1 | `2.650.000 € – 4.900.000 €` |
| **5. `ARCH_RETAIL_OMNI`** | Multinational Omnichannel Retailer & Logistics | `£12,500M` (85,000 emp) | CMMI 2.4 | `GBP` (`en-GB`) | PCI-DSS v4.0, UK GDPR, NIS Regulations | `£8,400,000 – £15,200,000` |
| **6. `ARCH_ENERGY_GRID`** | National High-Voltage Transmission Utility | `¥1,800,000M` (18,000 emp) | CMMI 4.1 | `JPY` (`ja-JP`) | NERC CIP / METI Critical Infra, IEC 62351 | `¥680,000,000 – ¥1,250,000,000` |

#### 4.2 Cross-Archetype Calibration Verification Matrix
For each of the 6 archetypes, the calibration test runner executes all 10 Specialist Domain Annexes (60 full Chapter 4 syntheses) and verifies:
1. **Proportionality to Revenue Ratio ($\text{COI}_{\text{annual}} / R_{\text{annual}}$):** A single annex's annual Cost of Inaction remains bounded within sensible actuarial guardrails ($0.02\% \le \text{COI} / R_{\text{annual}} \le 2.50\%$), preventing absurd results where a $50M company is told a single switch failure costs $100M, or an $85B bank is told a core outage costs $4,000.
2. **Vertical Regulatory Precision:** `ARCH_SAAS_MID` never cites `IEC 62443` (industrial SCADA), and `ARCH_OT_MOLINS` never cites `HIPAA` or `Basel III`.
3. **Multi-Language Rendering:** Compiles the full PDF AST in `es-ES`, `en-US`, `de-DE`, `en-GB`, and `ja-JP` with zero LaTeX box overflows (`Overfull \hbox`).

#### 4.3 Phase 4 Quality Gate, Verification Oracle & Pre-Flight Invariant
* **Pre-Flight Invariant:** All 6 archetype JSON configurations validate against `EnterpriseProfileSchema` and `VerticalCalibrationSchema`.
* **Verification Oracle:** `pytest tests/calibration/test_multi_vertical_archetypes.py`
* **Quality Gate:** 60/60 archetype-annex combinations pass actuarial proportionality assertions and compile clean ASTs in < 2.5 seconds total execution time.

---

### PHASE 5: Automated Continuous Quality Gate Tribunal & CI/CD Guards
**Objective:** Institutionalize an unbypassable automated test tribunal (`tests/tribunal/test_chapter4_invariants.py`) that runs on every Git commit and before any PDF compilation artifact is released.

#### 5.1 The 5 Automated Tribunal Guards
1. **Guard 1 — English-Only Codebase Enforcer (`test_codebase_english_purity.py`):**
   Parses Python AST across `src/` and `tests/` inspecting identifiers, docstrings, comments, string literals, and exception messages. Fails immediately if any Spanish vocabulary or non-ASCII diacritics appear outside `engine_config/locales.json`.
2. **Guard 2 — Zero Hardcoding Enforcer (`test_zero_hardcoding_ast.py`):**
   Scans `src/domain/`, `src/application/`, and `src/presentation/` for banned literals (client names, currency symbols `€$£¥`, hardcoded hourly rates, or regulatory strings).
3. **Guard 3 — Actuarial Monism & Bottom-Line Auditor (`test_actuarial_reconciliation.py`):**
   Extracts the rendered numbers directly from the generated Pandoc AST / Markdown tables in Sections 4.1, 4.2, and 4.3, parses them back into integers, and asserts:
   * $\text{Table 4.1 Row 1} + \text{Row 2} == \text{Subtotal COD}$
   * $\text{Table 4.1 Subtotal COD} + \text{Row 3 (Portfolio ALE)} == \text{Total Cost of Inaction}$
   * $\sum (\text{Table 4.2 Domain ALE Rows}) == \text{Table 4.1 Row 3 (Portfolio ALE)}$
   * $\sum (\text{Section 4.3 Risk Cards ALE}) + \sum (\text{Table 4.3 Residual ALE Rows}) == \text{Table 4.1 Row 3 (Portfolio ALE)}$
4. **Guard 4 — Actuarial Significant Rounding Auditor (`test_significant_figures_compliance.py`):**
   Regex-extracts every monetary token in Chapter 4 and verifies that 100% of values conform to the step quantum $S(x)$ defined in Section 2.6.
5. **Guard 5 — Editorial Elegance & Layout Budget Auditor (`test_editorial_layout_budget.py`):**
   Asserts zero `RVS\d+` tokens, zero textbook definition tables, maximum 8 full Risk Cards in Section 4.3, and 100% valid UTF-8 diacritics for the active locale.

---

## 4. ARCHITECTURAL INVARIANT CHECKLIST & DEFINITION OF DONE

The Chapter 4 Re-Architecture is declared **DONE** if and only if 100% of the following mathematical and architectural invariants hold true across all 10 Specialist Domain Annexes and all 6 Calibration Archetypes:

### 4.1 Mathematical & Actuarial Invariants
- [ ] **INV-MATH-01 (COD/ALE Separation):** Chronic Operational Drag ($\text{COD}$, $P=1.0$) and Probabilistic Event Risk ($\text{ALE} = \text{LEF} \times \text{LM}$) are computed separately and only summed at the final Cost of Inaction ($\text{COI}$) ledger line.
- [ ] **INV-MATH-02 (Exact Additive Reconciliation):** Across Sections 4.1, 4.2, and 4.3:
  $$\text{COI}_{\text{4.1}} \equiv \text{COD}_{\text{4.1}} + \text{ALE}_{\text{4.1}} \equiv \text{COD}_{\text{4.1}} + \sum_{k=1}^{K} \text{ALE}(\mathcal{D}_k)_{\text{4.2}} \equiv \text{COD}_{\text{4.1}} + \sum_{i=1}^{N} \text{ALE}_{i,\text{adj, 4.3}}$$
  with **zero** ($0.00$) discrepancy on both lower and upper bounds.
- [ ] **INV-MATH-03 (Order-of-Magnitude Rounding):** Every displayed monetary figure $x$ satisfies $x \pmod{S(x)} = 0$, where $S(x) \in \{50, 250, 1000, 5000, 25000, 100000\}$. Zero decimal cents or unrounded integers appear anywhere in Chapter 4.
- [ ] **INV-MATH-04 (Strict CMMI Monotonicity):** For any fixed set of infrastructure findings, increasing the evaluated CMMI maturity $M \in [1.0, 5.0]$ strictly reduces both Vulnerability ($\text{Vuln}$) and Mean Time To Recover ($\text{MTTR}$).
- [ ] **INV-MATH-05 (Portfolio Sub-Additivity):** Whenever two or more findings share a `FailureDomainCategory`, the portfolio sub-additivity factor satisfies $\Psi_{\text{portfolio}} < 1.0$, preventing double-counting of overlapping downtime hours.

### 4.2 Architectural & Editorial Invariants
- [ ] **INV-ARCH-01 (Single Immutable Model):** `PayloadToASTBridge` accepts only a frozen `Chapter4SynthesisPayload` instance and contains zero arithmetic logic.
- [ ] **INV-ARCH-02 (100% Technical English Codebase):** All Python modules, classes, variables, docstrings, comments, logs, and unit tests are written in 100% Technical English.
- [ ] **INV-ARCH-03 (Zero Hardcoding):** Zero client names, currency symbols, labor rates, or regulatory lists exist in Python source files; 100% are injected from `engine_config/`.
- [ ] **INV-EDIT-01 (Didactic Table Eradication):** All 4 legacy Open FAIR textbook definition tables are permanently removed from the AST builder.
- [ ] **INV-EDIT-02 (Machine Code Eradication):** Zero occurrences of `RVS01`, `RVS02`, or internal finding IDs appear in the 5x5 Heatmap, Concentration Table, or Risk Cards; 100% use human-readable physical titles.
- [ ] **INV-EDIT-03 (Diacritic & Typographic Integrity):** Localized deliverables in Spanish, German, French, Portuguese, and Japanese render with 100% orthographic and diacritic perfection, zero `Overfull \hbox` LaTeX warnings, and zero orphaned card headers.