### LAYER 1: Semantic Archetype Blindness (Tower-Level vs. Finding-Level Polymorphism)

#### 1.1 Forensic Root Cause & Exact Code Trace
The platform exhibits a catastrophic violation of Domain-Driven Design (DDD) by conflating **Organizational Custody (Tower ID)** with **Actuarial Loss Physics (Loss Archetype)**.

1. **`input_resolver.py` (Lines 1–145 & Secondary Loss Resolution):**
   In `FindingInputResolver.resolve_finding_inputs()`, when `hc.get("loss_archetype")` is absent from the raw payload, the resolver falls back to `tower_spec = get_actuarial_archetype_registry().get_mapping_for_tower(tower_id)`. It binds `archetype = tower_spec.primary_archetype`. Because `T2` (Compute & Virtualization) and `T4` (Cloud & Platform Engineering) map to `LossArchetypeType.AVAILABILITY_OUTAGE` at the macro-tower level, **every finding inside T2 or T4 inherits the physical parameters of a full-scale plant/infrastructure outage** (`default_rto_hours = 14.0`, `default_direct_replacement_cost`, and hourly revenue burn).
2. **`payload_to_ast.py` (Lines 4120–4135):**
   ```python
   canonical_t_id = str(ctx.get("tower_id") or blueprint_data.get("document_meta", {}).get("tower_id", "T1")).strip().upper()
   arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(canonical_t_id)
   primary_arch = arch_mapping.primary_archetype
   ...
   strategy = ActuarialReceptorFactory.get_strategy(primary_arch)
   ```
   Here, `payload_to_ast.py` instantiates a single `ActuarialReceptorStrategy` for the entire document based solely on `canonical_t_id`. All risk cards in that document are forced through the same mathematical receptor template.
3. **Ingestion Pipeline (`regenerate_molins_pure_from_raw_inputs.py` / Raw Telemetry Ingestion):**
   The ingestion script loops over `pillars_analysis -> health_check_asis` and invokes the actuarial engine passing `tower_id` as the primary discriminator without classifying the semantic vector of the individual finding (`finding`, `capability`, `control_vulnerability`, `primary_impact`).

#### 1.2 Why Idle VM Decommissioning & Missing Terraform Were Modeled as 14-Hour Factory Blackouts
When a finding such as *"Lack of automated decommissioning for orphaned/idle VMs"* (FinOps/OpEx waste) or *"Absence of Terraform IaC state locking / Kubernetes CSI driver standardization"* (Engineering friction / configuration drift) is ingested under Tower `T2` or `T4`:
1. The engine looks up `T2` in `ActuarialArchetypeRegistry` $\rightarrow$ returns `AVAILABILITY_OUTAGE`.
2. `input_resolver.py` sees no explicit `rto_hours` on the finding $\rightarrow$ injects `tower_spec.default_rto_hours` (e.g., 14.0 hours of physical plant stoppage).
3. The engine multiplies 14.0 hours by the client's `hourly_revenue_at_risk` (derived from `annual_revenue * buffering_elasticity_beta / 8760`), generating a fabricated ~143,000 € plant blackout loss for a finding that actually represents a 1,200 €/month cloud billing inefficiency or developer velocity drag.

#### 1.3 Universal Polymorphic Finding-Level Archetype Resolution
To work universally across Starling Bank (UK Fintech), Molins (Heavy Manufacturing), Rede D'Or (Healthcare), and US Power Utilities (SCADA/NERC-CIP), loss physics must be dispatched at the **Finding Level** (`FindingLossArchetypeResolver`) using a deterministic 3-tier precedence hierarchy:

1. **Tier 1: Explicit Canonical Ontology Tag** (`hc.get("loss_archetype")` or `hc.get("capability_id")` mapped in the canonical `CapabilityTaxonomyRegistry`).
2. **Tier 2: Multi-Lingual Semantic Vector Classifier (Causal Verb + Asset Class + Impact Mechanism):**
   Evaluates the finding's token stream (`finding`, `capability`, `business_risk`, `primary_impact`) against language-agnostic canonical concept stems across five orthogonal actuarial physics equations:
   * `FINOPS_RESOURCE_WASTE` (Deterministic/Low-Variance OpEx Drain): Orphaned VMs, idle storage, unattached EBS/disks, over-provisioned licenses, right-sizing, zombie assets. **Physics:** $\text{RTO} = 0$, $\text{Downtime Revenue Loss} = 0$. Loss is modeled as $\text{Annualized Unoptimized Spend} \times \text{Waste Ratio}$.
   * `ENGINEERING_VELOCITY_FRICTION` (Operational Drag / MTTR Inflation): Missing IaC (Terraform/Ansible), manual deployment, lack of CI/CD, missing documentation, toil. **Physics:** No direct plant blackout. Modeled via **Labor Remediation Hours ($\text{FTE Cost} \times \text{Hours}$)** + **Conditional Vulnerability Multiplier** (inflating MTTR/RTO of *actual* availability risks via copula conditioning, or standalone rework cost).
   * `REGULATORY_AND_BREACH` (Statutory & Data Exfiltration): PII/PHI exposure, GDPR/LGPD/HIPAA/NERC-CIP non-compliance, unencrypted databases, missing audit logs. **Physics:** $\text{RTO} = 0$. Modeled via $\text{Records Exposed} \times \text{Per-Record Cost} + \text{Statutory Fine Distribution}$.
   * `ASSET_OBSOLESCENCE_AND_INTEGRITY` (Technical Debt / EoL Hardware-Software): CentOS 5/6/7 EoL, Windows Server 2008, unsupported firmware, legacy ERP. **Physics:** Modeled via **Accelerated Replacement / Migration CapEx/OpEx** + **Elevated Vulnerability Probability ($\text{TEF} \times \text{Exploitability}$)**, bounded by the isolated blast radius of the specific workload (`blast_radius_factor` $\in [0.01, 1.0]$).
   * `AVAILABILITY_OUTAGE` (True Service/Plant Interruption): Single point of failure (SPOF), unredundant switches/SCADA PLCs, failing backups, missing DR failover. **Physics:** $\text{RTO} \times \text{Hourly Value at Risk} \times \text{Blast Radius Factor}$.
3. **Tier 3: Scoped Tower Fallback with Blast-Radius Attenuation:**
   If Tier 1 and Tier 2 yield no specific override, fallback to the Tower's `primary_archetype`, **but** constrain the blast radius using a mandatory `workload_blast_radius_factor` (defaulting to `0.15` for localized findings rather than `1.00` enterprise-wide total blackout).

---

### LAYER 2: Upstream-Downstream Actuarial Split-Brain (The Plug Number Fraud)

#### 2.1 Forensic Trace of the Plug Number (`stochastic_tail_adj`)
In `payload_to_ast.py` (inside `_build_fair_risk_analysis`), the presentation compiler attempts to render an itemized financial breakdown table on each Risk Card showing:
1. Primary Downtime Loss (`primary_downtime_loss`)
2. Direct Replacement Cost (`repl_cost_num`)
3. Secondary Weighted Loss (`sec_weighted_loss`)
4. Total Single Loss Expectancy (`reconciled_sle`)

**Why the Split-Brain Occurs:**
1. **Upstream (`BayesianFairCopulaEngine`):** Runs 10,000 Monte Carlo iterations. In each iteration $i$, it samples $\text{RTO}_i \sim \text{PERT}(r_{\min}, r_{\text{mode}}, r_{\max})$, applies lognormal/Frechet severity multipliers, applies non-linear buffering elasticity $\beta$, adds replacement cost, and samples binary/compound secondary loss ($\text{SLE}_i$). Finally, it scales the output or computes `mean_sle` and `portfolio_allocated_ale`.
2. **Downstream (`payload_to_ast.py`):** Does **not** have access to the Monte Carlo component expectations $E[\text{Downtime}]$, $E[\text{Replacement}]$, and $E[\text{Secondary}]$. Instead, `payload_to_ast.py` re-computes a naive deterministic formula on the fly:
   $$\text{Deterministic Sum} = (\text{rto\_mode} \times \text{hourly\_rate}) + \text{repl\_cost} + (\text{sec\_prob} \times \text{sec\_mean})$$
3. Meanwhile, `reconciled_sle` is back-solved from the portfolio-diversified ALE divided by LEF:
   $$\text{reconciled\_sle} = \frac{\text{calibrated\_ale}}{\text{calc\_lef}}$$
4. Because `calibrated_ale` has been slashed by Euler diversification (e.g., $-70\%$) OR inflated by PERT skew ($\mu_{\text{PERT}} \neq \text{mode}$), the naive deterministic sum in `payload_to_ast.py` is wildly different from `reconciled_sle`.
5. To force the table rows to sum to `reconciled_sle`, a developer wrote the fraudulent plug line in `payload_to_ast.py`:
   ```python
   stochastic_tail_adj = round(reconciled_sle - (primary_downtime_loss + repl_cost_num + sec_weighted_loss))
   ```
   and labeled it `"Ajuste estocástico de dispersión"` (*Stochastic dispersion adjustment*). When Euler slashed the risk by 70%, `reconciled_sle` became tiny while `primary_downtime_loss` remained huge, producing massive negative plug numbers (**-30,000 € to -102,000 €**).

#### 2.2 Mathematical & Architectural Resolution: Closed-Form Additive Vector Lineage
Under **SR 11-7 (Federal Reserve Model Risk Management)** and **BCBS 239**, a presentation compiler (`payload_to_ast.py`) is strictly forbidden from performing domain arithmetic or inventing balancing plug items.

1. **Upstream Expectation Tracking (`BayesianFairCopulaEngine`):**
   During the Monte Carlo simulation of $N$ trials, for each trial $i \in \{1 \dots N\}$:
   $$\text{SLE}_i = L_{\text{downtime}, i} + L_{\text{replacement}, i} + L_{\text{secondary}, i}$$
   By the **Linearity of Expectation**, the sample mean of the sum equals the exact sum of the sample means:
   $$\mathbb{E}[\text{SLE}] = \mathbb{E}[L_{\text{downtime}}] + \mathbb{E}[L_{\text{replacement}}] + \mathbb{E}[L_{\text{secondary}}]$$
2. **Distinguishing PERTSkew from Base Mode (If Displayed):**
   If we wish to show the difference between Mode-based downtime and PERT-mean downtime, it is a strictly positive/analytical quantity:
   $$\Delta_{\text{PERT}} = \mathbb{E}[L_{\text{downtime}}] - L_{\text{downtime}}(\text{rto}_{\text{mode}}) = \left(\frac{r_{\min} + 4r_{\text{mode}} + r_{\max}}{6} - r_{\text{mode}}\right) \times \text{HourlyRate} \times \text{BlastRadius}$$
3. **Decoupling Standalone SLE from Portfolio Diversification:**
   Euler diversification applies to **Annualized Loss Expectancy ($\text{ALE}$)** at the portfolio aggregation level, **never** by mutating the physical Single Loss Expectancy ($\text{SLE}$) of an individual event!
   * **Standalone SLE ($\text{SLE}_{\text{gross}}$):** $\mathbb{E}[L_{\text{downtime}}] + \mathbb{E}[L_{\text{replacement}}] + \mathbb{E}[L_{\text{secondary}}]$
   * **Standalone ALE ($\text{ALE}_{\text{gross}}$):** $\mathbb{E}[\text{LEF}] \times \text{SLE}_{\text{gross}}$ (plus any $\text{Cov}(\text{LEF}, \text{SLE})$ if correlated, folded pro-rata into component expectations).
   * **Portfolio Diversification Adjustment ($\Delta_{\text{Euler}}$):** Explicitly shown on the **ALE line** ($\text{ALE}_{\text{net}} = \text{ALE}_{\text{gross}} + \Delta_{\text{Euler}}$), leaving $\text{SLE}_{\text{gross}}$ 100% physically intact and free of any plug number.

---

### LAYER 3: Unconstrained Euler Diversification (The 78% Risk Eraser)

#### 3.1 Forensic Trace of the 60%–79% Risk Erasure
Looking at Excerpt 3 (`euler_allocator.py`), `EulerPortfolioAllocator.allocate_portfolio()` has a guardrail limiting tower-level copula discount to `[18%, 28%]` (max `35%`). **So how did individual risks get slashed by 60% to 79%?**

There are **two compounding mechanisms** causing the 78% erasure:
1. **Intra-Tower Risk-Level Allocation vs. Inter-Tower Allocation (`portfolio_allocated_ale`):**
   Upstream in the copula engine (before `EulerPortfolioAllocator` is even called, or when allocating a Tower's capped ALE across $M$ findings within that tower), the engine computes a sub-additive portfolio total for $K$ findings using a Gaussian/Student-$t$ copula with low correlation ($\rho \approx 0.10 - 0.25$) or caps the tower total against a macroscopic budget ceiling (`max_credit_limit` / `ebitda` cap). When $K=61$ findings are aggregated with low pairwise correlation, the Central Limit Theorem causes the ratio of the diversified metric to the sum of standalone metrics to shrink at a rate of $O(1/\sqrt{K})$, yielding a **65% to 79% reduction**!
2. **Expectation Non-Additivity Confusion (Applying VaR Euler Allocation to Mean ALE):**
   **Critical Mathematical Fallacy in Upstream Engine:**
   In probability theory, **Mathematical Expectation (Mean ALE) is strictly additive**, regardless of correlation or copula structure!
   $$\mathbb{E}\left[\sum_{i=1}^K X_i\right] = \sum_{i=1}^K \mathbb{E}[X_i]$$
   Correlation and copulas only create diversification in **Tail Risk / Value-at-Risk ($\text{VaR}_{90}, \text{VaR}_{99}, \text{ES}_\alpha$)** OR when removing **overlapping double-counted causal events (Common-Cause Event Deduplication)**.
   Applying a VaR dispersion ratio $\frac{\text{VaR}_{90}(\sum X_i)}{\sum \text{VaR}_{90}(X_i)}$ (which is $\approx 0.25$ for 61 risks) directly to scale down **Mean ALE** (`portfolio_allocated_ale`) is a severe actuarial error under Basel III / Solvency II. The only valid reduction to Mean ALE is **Common-Cause Overlap Deduplication** (preventing two findings that trigger the exact same outage from counting the same downtime twice).

#### 3.2 Regulatory & Statistical Boundaries (SR 11-7 / Basel III / Solvency II / Open FAIR)
1. **Basel III (MAR30 / OPE) & Solvency II (SCR Standard Formula):**
   * Under Solvency II and Basel III AMA/SMA, inter-risk diversification credit on capital ($\text{VaR}_{99.5}$) is strictly bounded (typically **15% to 25%** across operational risk categories).
   * For **Expected Loss ($\text{EL}$ / Mean $\text{ALE}$)**, diversification credit is **0%** for independent risks, and strictly limited to **Causal Overlap Deduplication** ($\le 25\%$ maximum adjustment) when multiple control findings share a single downstream failure mode.
   * **Deterministic OpEx / FinOps Waste / Licensing / EoL Migration Costs** have **0.0% diversification** ($\rho = 1.0$, zero variance overlap). You cannot "diversify away" an AWS bill for orphaned VMs or a mandatory CentOS-5 migration.

#### 3.3 The Bounded Sub-Additive Allocation Law
We must enforce three hard invariants in both the upstream Copula Engine and `EulerPortfolioAllocator`:
1. **Archetype-Specific Diversification Eligibility:**
   * `FINOPS_RESOURCE_WASTE`: Max diversification credit = **0.0%** (`is_diversifiable = False`).
   * `ENGINEERING_VELOCITY_FRICTION`: Max diversification credit = **10.0%**.
   * `REGULATORY_AND_BREACH`, `ASSET_OBSOLESCENCE_AND_INTEGRITY`, `AVAILABILITY_OUTAGE`: Max causal overlap credit on Mean ALE = **20.0%**, Max tail diversification credit on $\text{VaR}_{90}$ (`P90`) = **25.0%**.
2. **Per-Finding Floor Invariant (Anti-Anesthesia Guardrail):**
   For every individual finding $i$:
   $$\text{ALE}_{\text{net}, i} \ge 0.75 \times \text{ALE}_{\text{standalone}, i}$$
   No risk card may ever have more than **25%** of its standalone actuarial exposure deducted via portfolio overlap adjustment.
3. **Exact Integer Hare-Niemeyer Conservation:**
   $$\sum_{i=1}^K \text{ALE}_{\text{standalone}, i} + \sum_{i=1}^K \Delta_{\text{overlap}, i} = \text{ALE}_{\text{net, portfolio}}$$

---

### LAYER 4: Epistemic Hallucination & Robotic Boilerplate

#### 4.1 Forensic Trace of the 17 Robotic Boilerplate Risks
In Excerpt 4 (`in_memory_asis_compiler.py`, lines 18–23):
```python
finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
raw_risk = str(hc.get("business_risk") or hc.get("primary_impact") or "").strip()
if raw_risk and not _is_severity_enum_token(raw_risk, doc_lang) and len(raw_risk.split()) >= 4:
    business_risk = raw_risk
else:
    business_risk = _extract_verified_business_risk(hc, pillar_name, doc_lang)
```
And upstream during questionnaire ingestion (`_extract_verified_business_risk` and raw questionnaire converter):
When a client answers a maturity survey question with a low score (e.g., Score 1 or 2) **without providing written audit notes or empirical telemetry**, the ingestion mapper synthesizes a generic finding string:
`"Carencia de controles operativos formalizados y falta de supervisión continua en..."` (or its localized equivalent) and injects it into `health_check_asis` as if it were a verified empirical audit finding! Worse yet, `FindingInputResolver` then assigns `MODEL_DEFAULT` financial parameters to this synthetic string and runs a 10,000-iteration Monte Carlo simulation on it.

#### 4.2 Epistemic State Machine & Anti-Boilerplate Quarantine
To satisfy **SR 11-7 Section IV (Model Inputs & Data Quality)**, every finding must be classified by an **Epistemic Gatekeeper (`EpistemicEvidenceClassifier`)** before entering the Monte Carlo engine:

1. **`VERIFIED_EMPIRICAL_EVIDENCE`:**
   Contains concrete telemetry, asset identifiers, metric quantities, or specific architectural observations, and does **not** match any known synthetic boilerplate template regex.
   * **Action:** Full Bayesian FAIR Monte Carlo quantification + Full Actuarial Risk Card.
2. **`QUESTIONNAIRE_INFERRED_LOW_EVIDENCE`:**
   Derived solely from a Likert-scale questionnaire score (e.g., CMMI 1–2) or matches synthetic boilerplate signatures (e.g., `"Carencia de controles operativos formalizados..."`, `"Lack of formalized operational controls and continuous monitoring..."`, `"Ausência de controles operacionais formalizados..."`).
   * **Action:** **Quarantined from Fabrication.** Do **NOT** generate a fake 14-hour outage risk card with fabricated monetary plug numbers. Instead, route to a dedicated **"Epistemic Coverage & Control Maturity Gaps (Unquantified Telemetry Scope)"** summary table, explicitly flagged as `EPISTEMIC_STATUS: INFERRED_FROM_SURVEY_ONLY — TELEMETRY_REQUIRED_FOR_ACTUARIAL_QUANTIFICATION` with `ALE = UNQUANTIFIED ( Prior Range Only )`.
3. **`UNASSESSED_OUT_OF_SCOPE`:**
   Zero findings or silent pillar.
   * **Action:** Render a clean institutional scope-exclusion notice without synthetic risk cards.

---

### LAYER 5: THE UNIFIED INSTITUTIONAL RE-ARCHITECTURE

Below is the complete, production-ready Technical English implementation across the domain, compiler, and presentation layers.

#### 5.1 Canonical Domain Contracts & Polymorphic Archetype Classifier (`src/assessment_engine/domain/actuarial/finding_archetype_resolver.py`)

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Final, Mapping, Optional, Sequence

from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
)


class EpistemicEvidenceState(str, Enum):
    """Institutional classification of evidence provenance per SR 11-7."""

    VERIFIED_EMPIRICAL = "VERIFIED_EMPIRICAL"
    SURVEY_INFERRED_BOILERPLATE = "SURVEY_INFERRED_BOILERPLATE"
    UNASSESSED_OUT_OF_SCOPE = "UNASSESSED_OUT_OF_SCOPE"


class FindingLossPhysics(str, Enum):
    """Granular finding-level loss mechanics overriding macro-tower defaults."""

    AVAILABILITY_OUTAGE = "AVAILABILITY_OUTAGE"
    FINOPS_RESOURCE_WASTE = "FINOPS_RESOURCE_WASTE"
    ENGINEERING_VELOCITY_FRICTION = "ENGINEERING_VELOCITY_FRICTION"
    REGULATORY_AND_BREACH = "REGULATORY_AND_BREACH"
    ASSET_OBSOLESCENCE_AND_INTEGRITY = "ASSET_OBSOLESCENCE_AND_INTEGRITY"

    def to_canonical_archetype(self) -> LossArchetypeType:
        mapping = {
            FindingLossPhysics.AVAILABILITY_OUTAGE: LossArchetypeType.AVAILABILITY_OUTAGE,
            FindingLossPhysics.FINOPS_RESOURCE_WASTE: getattr(
                LossArchetypeType, "OPERATIONAL_INEFFICIENCY", LossArchetypeType.AVAILABILITY_OUTAGE
            ),
            FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION: getattr(
                LossArchetypeType, "ENGINEERING_FRICTION", LossArchetypeType.AVAILABILITY_OUTAGE
            ),
            FindingLossPhysics.REGULATORY_AND_BREACH: LossArchetypeType.REGULATORY_AND_BREACH,
            FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY: getattr(
                LossArchetypeType, "TECHNICAL_DEBT_AND_EOL", LossArchetypeType.AVAILABILITY_OUTAGE
            ),
        }
        return mapping[self]


@dataclass(frozen=True)
class FindingPhysicsProfile:
    """Immutable physics rules governing a single finding's actuarial evaluation."""

    loss_physics: FindingLossPhysics
    canonical_archetype: LossArchetypeType
    epistemic_state: EpistemicEvidenceState
    allows_downtime_burn: bool
    default_rto_hours: float
    blast_radius_factor: float
    max_euler_ale_discount_pct: float
    max_euler_var_discount_pct: float
    classification_rationale: str


@dataclass(frozen=True)
class AdditiveLossDecomposition:
    """
    Closed-form, zero-plug additive decomposition of Single and Annualized Loss Expectancy.
    Enforces exact arithmetic conservation between Domain Engine and Presentation AST.
    """

    currency_iso: str
    mean_lef: float
    # Exact additive SLE components: sum(components) == gross_mean_sle
    expected_downtime_loss: int
    expected_replacement_cost: int
    expected_secondary_loss: int
    gross_mean_sle: int
    # Exact ALE bridge: gross_standalone_ale + euler_overlap_adjustment_ale == net_allocated_ale
    gross_standalone_ale: int
    euler_overlap_adjustment_ale: int
    net_allocated_ale: int
    euler_discount_pct: Decimal
    # Tail Risk (P90 / VaR90)
    gross_standalone_p90: int
    net_allocated_p90: int
    loss_physics: str
    epistemic_state: str

    def validate_conservation(self) -> None:
        sle_sum = (
            self.expected_downtime_loss
            + self.expected_replacement_cost
            + self.expected_secondary_loss
        )
        if sle_sum != self.gross_mean_sle:
            raise ValueError(
                f"SLE Additive Conservation Violation: Downtime ({self.expected_downtime_loss}) + "
                f"Replacement ({self.expected_replacement_cost}) + Secondary ({self.expected_secondary_loss}) "
                f"= {sle_sum} != Gross Mean SLE ({self.gross_mean_sle})."
            )
        if self.euler_overlap_adjustment_ale > 0:
            raise ValueError(
                f"Sub-additivity Violation: Euler overlap adjustment must be <= 0, got {self.euler_overlap_adjustment_ale}."
            )
        ale_bridge = self.gross_standalone_ale + self.euler_overlap_adjustment_ale
        if ale_bridge != self.net_allocated_ale:
            raise ValueError(
                f"ALE Bridge Conservation Violation: Gross ({self.gross_standalone_ale}) + "
                f"Euler Adjustment ({self.euler_overlap_adjustment_ale}) = {ale_bridge} != "
                f"Net Allocated ALE ({self.net_allocated_ale})."
            )


class PolymorphicFindingClassifier:
    """
    Universal, multi-lingual (en, es, pt, de, it, fr, ja) semantic & ontology classifier.
    Eliminates Tower-level archetype blindness and quarantines robotic survey boilerplate.
    """

    _BOILERPLATE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(r"carencia de controles operativos formalizados\s+y\s+falta de supervisi[oó]n continua", re.I),
        re.compile(r"lack of formalized operational controls\s+and\s+continuous (monitoring|supervision)", re.I),
        re.compile(r"aus[eê]ncia de controles operacionais formalizados\s+e\s+falta de supervis[aã]o cont[ií]nua", re.I),
        re.compile(r"mangel an formalisierten betrieblichen kontrollen\s+und\s+kontinuierlicher [uü]berwachung", re.I),
        re.compile(r"absence de contr[oô]les op[eé]rationnels formalis[eé]s\s+et\s+de surveillance continue", re.I),
        re.compile(r"mancanza di controlli operativi formalizzati\s+e\s+di supervisione continua", re.I),
        re.compile(r"deficiencia generalizada en la gobernanza documental del pilar", re.I),
    )

    _FINOPS_WASTE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(idle\s+vm|orphaned\s+vm|zombie\s+vm|unattached\s+(volume|disk|ebs)|"
            r"decommission(ing)?\s+of\s+(idle|unused|orphaned)|right[- ]?sizing|"
            r"finops|over[- ]?provisioned|unused\s+(instance|resource|license)|"
            r"máquinas?\s+virtuales?\s+(inactivas?|huérfanas?|en\s+desuso)|"
            r"desaprovisionamiento\s+de\s+(vm|recursos|instancias)|"
            r"recursos?\s+(ociosos?|órfãos?|inativos?)|"
            r"optimizaci[oó]n\s+de\s+costes\s+cloud)\b",
            re.I,
        ),
    )

    _ENGINEERING_FRICTION_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(terraform|ansible|iac|infrastructure\s+as\s+code|infraestructura\s+como\s+c[oó]digo|"
            r"ci/cd|gitops|kubernetes\s+csi|helm\s+chart|pipeline\s+automation|"
            r"manual\s+provisioning|aprovisionamiento\s+manual|despliegue\s+manual|"
            r"configuration\s+drift|deriva\s+de\s+configuraci[oó]n|toil)\b",
            re.I,
        ),
    )

    _OBSOLESCENCE_EOL_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(centos\s*[45678]?|rhel\s*[456]?|windows\s+server\s+200[38]|"
            r"end[- ]of[- ]life|end[- ]of[- ]support|\beol\b|\beos\b|"
            r"obsolescencia|obsoleto|sistema\s+operativo\s+sin\s+soporte|"
            r"legacy\s+os|unsupported\s+(os|firmware|database|kernel))\b",
            re.I,
        ),
    )

    _REGULATORY_BREACH_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(gdpr|lgpd|hipaa|pci[- ]dss|sox|nis2|dora|nerc[- ]cip|rgpd|"
            r"data\s+breach|exfiltration|fuga\s+de\s+datos|exfiltraci[oó]n|"
            r"pii|phi|unencrypted\s+data|datos\s+sin\s+cifrar|sanci[oó]n\s+regulatoria)\b",
            re.I,
        ),
    )

    _CATASTROPHIC_OUTAGE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(single\s+point\s+of\s+failure|\bspof\b|punto\s+[uú]nico\s+de\s+fallo|"
            r"disaster\s+recovery|\bdrp\b|recuperaci[oó]n\s+ante\s+desastres|"
            r"plant\s+stoppage|parada\s+de\s+planta|scada\s+outage|blackout|"
            r"core\s+network\s+outage|ransomware\s+encryption|backup\s+failure)\b",
            re.I,
        ),
    )

    @classmethod
    def classify_finding(
        cls,
        hc: Mapping[str, Any],
        tower_id: str,
    ) -> FindingPhysicsProfile:
        finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
        capability_text = str(hc.get("capability") or hc.get("title") or hc.get("name") or "").strip()
        impact_text = str(hc.get("business_risk") or hc.get("primary_impact") or "").strip()
        evidence_text = str(hc.get("evidence") or "").strip()
        vulnerability_text = str(hc.get("control_vulnerability") or "").strip()

        combined_corpus = " | ".join(
            filter(None, [finding_text, capability_text, impact_text, evidence_text, vulnerability_text])
        )

        # 1. Epistemic Provenance Evaluation
        epistemic_state = cls._evaluate_epistemic_state(hc, finding_text, impact_text, evidence_text)

        # 2. Explicit Payload Override Check
        explicit_physics = str(hc.get("loss_physics") or hc.get("loss_archetype") or "").strip().upper()
        if explicit_physics in FindingLossPhysics.__members__:
            physics = FindingLossPhysics[explicit_physics]
            return cls._build_profile(physics, epistemic_state, hc, "Explicit payload loss_physics tag")

        # 3. Semantic Causal Classification
        # Priority A: FinOps / Idle Resource Waste (Zero plant downtime)
        if any(p.search(combined_corpus) for p in cls._FINOPS_WASTE_PATTERNS):
            return cls._build_profile(
                FindingLossPhysics.FINOPS_RESOURCE_WASTE,
                epistemic_state,
                hc,
                "Matched FinOps / idle resource waste semantic signature",
            )

        # Priority B: Engineering Velocity / IaC / DevOps Friction (Unless explicitly causing a SPOF blackout)
        if any(p.search(combined_corpus) for p in cls._ENGINEERING_FRICTION_PATTERNS) and not any(
            p.search(combined_corpus) for p in cls._CATASTROPHIC_OUTAGE_PATTERNS
        ):
            return cls._build_profile(
                FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
                epistemic_state,
                hc,
                "Matched Engineering / IaC / CI-CD operational friction signature",
            )

        # Priority C: Regulatory & Data Breach
        if any(p.search(combined_corpus) for p in cls._REGULATORY_BREACH_PATTERNS):
            return cls._build_profile(
                FindingLossPhysics.REGULATORY_AND_BREACH,
                epistemic_state,
                hc,
                "Matched Regulatory / Data Breach semantic signature",
            )

        # Priority D: Asset Obsolescence & EoL Integrity (Scoped workload blast radius)
        if any(p.search(combined_corpus) for p in cls._OBSOLESCENCE_EOL_PATTERNS):
            return cls._build_profile(
                FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
                epistemic_state,
                hc,
                "Matched EoL / Asset Obsolescence semantic signature",
            )

        # Priority E: True Availability Outage or Tower Default (with scoped blast radius)
        return cls._build_profile(
            FindingLossPhysics.AVAILABILITY_OUTAGE,
            epistemic_state,
            hc,
            f"Resolved to Availability Outage physics for tower {tower_id}",
        )

    @classmethod
    def _evaluate_epistemic_state(
        cls,
        hc: Mapping[str, Any],
        finding_text: str,
        impact_text: str,
        evidence_text: str,
    ) -> EpistemicEvidenceState:
        explicit_state = str(hc.get("epistemic_state") or "").strip().upper()
        if explicit_state == "UNASSESSED_OUT_OF_SCOPE":
            return EpistemicEvidenceState.UNASSESSED_OUT_OF_SCOPE

        if not finding_text and not impact_text:
            return EpistemicEvidenceState.UNASSESSED_OUT_OF_SCOPE

        for pattern in cls._BOILERPLATE_PATTERNS:
            if pattern.search(finding_text) or pattern.search(impact_text) or pattern.search(evidence_text):
                return EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE

        if bool(hc.get("is_synthetic_boilerplate")) or str(hc.get("source_type") or "").upper() == "LIKERT_FALLBACK":
            return EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE

        return EpistemicEvidenceState.VERIFIED_EMPIRICAL

    @classmethod
    def _build_profile(
        cls,
        physics: FindingLossPhysics,
        epistemic_state: EpistemicEvidenceState,
        hc: Mapping[str, Any],
        rationale: str,
    ) -> FindingPhysicsProfile:
        explicit_blast = hc.get("blast_radius_factor")
        blast_val = float(explicit_blast) if explicit_blast is not None else None

        if physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=False,
                default_rto_hours=0.0,
                blast_radius_factor=blast_val if blast_val is not None else 0.0,
                max_euler_ale_discount_pct=0.0,  # Deterministic OpEx cannot be diversified
                max_euler_var_discount_pct=0.0,
                classification_rationale=rationale,
            )

        if physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=False,
                default_rto_hours=0.0,
                blast_radius_factor=blast_val if blast_val is not None else 0.05,
                max_euler_ale_discount_pct=0.10,
                max_euler_var_discount_pct=0.15,
                classification_rationale=rationale,
            )

        if physics == FindingLossPhysics.REGULATORY_AND_BREACH:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=False,
                default_rto_hours=0.0,
                blast_radius_factor=blast_val if blast_val is not None else 0.25,
                max_euler_ale_discount_pct=0.15,
                max_euler_var_discount_pct=0.25,
                classification_rationale=rationale,
            )

        if physics == FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=True,
                default_rto_hours=4.0,  # Localized workload recovery, not 14h full plant blackout
                blast_radius_factor=blast_val if blast_val is not None else 0.15,
                max_euler_ale_discount_pct=0.20,
                max_euler_var_discount_pct=0.25,
                classification_rationale=rationale,
            )

        # AVAILABILITY_OUTAGE
        return FindingPhysicsProfile(
            loss_physics=physics,
            canonical_archetype=physics.to_canonical_archetype(),
            epistemic_state=epistemic_state,
            allows_downtime_burn=True,
            default_rto_hours=8.0,
            blast_radius_factor=blast_val if blast_val is not None else 0.35,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
            classification_rationale=rationale,
        )
```

---

#### 5.2 Refactoring `input_resolver.py` (Polymorphic Parameter Resolution)

Replace the monolithic tower-level RTO and secondary loss fallback in `src/assessment_engine/domain/actuarial/input_resolver.py` with finding-level physics dispatch:

```python
        # --- POLYMORPHIC FINDING-LEVEL PHYSICS RESOLUTION ---
        from assessment_engine.domain.actuarial.finding_archetype_resolver import (
            FindingLossPhysics,
            PolymorphicFindingClassifier,
        )

        physics_profile = PolymorphicFindingClassifier.classify_finding(
            hc=hc,
            tower_id=tower_id,
        )
        archetype = physics_profile.canonical_archetype

        # 4. Recovery Time Objective (RTO) PERT — Governed by FindingLossPhysics
        raw_rto = (
            hc.get("recovery_time_hours")
            if hc.get("recovery_time_hours") is not None
            else hc.get("rto_hours_mode")
        )
        if not physics_profile.allows_downtime_burn:
            # FinOps waste, IaC friction, and pure regulatory breaches do NOT cause physical plant blackouts
            rto_mode = 0.0
            rto_min = 0.0
            rto_max = 0.0
            rto_source = ParameterSourceType.DERIVED
            rto_min_source = ParameterSourceType.DERIVED
            rto_max_source = ParameterSourceType.DERIVED
            rto_conf = ParameterConfidenceLevel.HIGH
            is_explicit_rto = True
        elif raw_rto is not None:
            parsed_rto = parse_strict_float(raw_rto, "recovery_time_hours")
            if parsed_rto is None or parsed_rto < 0.0:
                raise ValueError(f"rto_hours must be >= 0.0, got {raw_rto}")
            rto_mode = parsed_rto
            rto_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            rto_conf = ParameterConfidenceLevel.HIGH
            is_explicit_rto = True

            raw_rto_min = hc.get("rto_hours_min")
            raw_rto_max = hc.get("rto_hours_max")
            if raw_rto_min is not None and raw_rto_max is not None and rto_mode > 0.0:
                rto_min = parse_strict_float(raw_rto_min, "rto_hours_min")
                rto_max = parse_strict_float(raw_rto_max, "rto_hours_max")
                if not (0.0 <= rto_min <= rto_mode <= rto_max):
                    raise ValueError(
                        f"PERT ordering violated for RTO: min ({rto_min}) <= mode ({rto_mode}) <= max ({rto_max})"
                    )
                rto_min_source = ParameterSourceType.ASSESSMENT_PAYLOAD
                rto_max_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            else:
                rto_min = rto_mode * pack.pert_dispersion.rto_min_ratio
                rto_max = rto_mode * pack.pert_dispersion.rto_max_ratio
                rto_min_source = ParameterSourceType.DERIVED
                rto_max_source = ParameterSourceType.DERIVED
        else:
            rto_mode = physics_profile.default_rto_hours
            rto_min = rto_mode * pack.pert_dispersion.rto_min_ratio
            rto_max = rto_mode * pack.pert_dispersion.rto_max_ratio
            rto_source = ParameterSourceType.MODEL_DEFAULT
            rto_min_source = ParameterSourceType.DERIVED
            rto_max_source = ParameterSourceType.DERIVED
            rto_conf = ParameterConfidenceLevel.LOW
            is_explicit_rto = False
            material_parameters_explicit = False
```

And in Step 5 & 6 of `input_resolver.py` (Direct Replacement / Remediation Cost & Secondary Loss):
```python
        # 5. Direct Replacement / Remediation / FinOps Waste Cost
        raw_repl = hc.get("direct_replacement_cost")
        if raw_repl is not None:
            parsed_repl = parse_strict_float(raw_repl, "direct_replacement_cost")
            if parsed_repl is None or parsed_repl < 0.0:
                raise ValueError(f"direct_replacement_cost cannot be negative, got {raw_repl}")
            repl_raw_val = parsed_repl
            repl_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            repl_conf = ParameterConfidenceLevel.HIGH
        else:
            raw_lm = parse_strict_float(hc.get("loss_magnitude")) or 2.5
            lm_factor = (raw_lm / 5.0) if (0.0 < raw_lm <= 5.0) else 0.50
            base_repl = (
                tower_spec.default_direct_replacement_cost
                if tower_spec
                else global_fb.direct_replacement_cost
            )
            if physics_profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE:
                # Model as annualized unoptimized infrastructure/cloud resource waste
                repl_raw_val = base_repl * 0.35 * lm_factor
            elif physics_profile.loss_physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION:
                # Model as engineering remediation & operational toil cost
                repl_raw_val = base_repl * 0.45 * lm_factor
            else:
                repl_raw_val = base_repl * lm_factor
            repl_source = ParameterSourceType.MODEL_DEFAULT
            repl_conf = ParameterConfidenceLevel.LOW
            material_parameters_explicit = False
```

---

#### 5.3 Refactoring `euler_allocator.py` (Bounded Sub-Additivity & Per-Finding Guardrails)

Update `src/assessment_engine/domain/actuarial/euler_allocator.py` to enforce Basel III / Solvency II diversification caps (`max_discount_pct <= 0.25` for ALE, `0.00` for FinOps/OpEx) and provide a finding-level allocator that emits `AdditiveLossDecomposition`:

```python
class EulerPortfolioAllocator:
    """
    Actuarial engine implementing Tasche's Euler Allocation and Hare-Niemeyer discretization.
    Enforces SR 11-7 / Basel III / Solvency II sub-additivity bounds:
    - Maximum inter-domain or intra-domain Mean ALE overlap discount: 25.0%
    - Deterministic OpEx / FinOps findings: 0.0% discount
    - Zero-plug additive SLE conservation
    """

    MAX_PORTFOLIO_ALE_DISCOUNT: Final[float] = 0.25
    MIN_PORTFOLIO_ALE_DISCOUNT: Final[float] = 0.12

    @classmethod
    def allocate_findings_within_domain(
        cls,
        findings_raw: Sequence[Mapping[str, Any]],
        currency_iso: str = "EUR",
    ) -> Dict[str, AdditiveLossDecomposition]:
        """
        Allocates portfolio overlap adjustments across individual findings while preserving
        100% of standalone SLE component additivity and enforcing per-finding max discount caps.
        """
        from decimal import ROUND_HALF_UP, Decimal

        decompositions: Dict[str, AdditiveLossDecomposition] = {}
        if not findings_raw:
            return decompositions

        active_ids: list[str] = []
        standalone_ales: Dict[str, int] = {}
        max_discounts: Dict[str, float] = {}
        raw_metrics: Dict[str, dict[str, Any]] = {}

        for item in findings_raw:
            f_id = str(item["id"])
            epistemic = str(item.get("epistemic_state") or "VERIFIED_EMPIRICAL")
            physics = str(item.get("loss_physics") or "AVAILABILITY_OUTAGE")
            lef = max(0.0, float(item.get("mean_lef") or 0.0))

            # Exact integer rounding of expectation components from Monte Carlo
            e_down = max(0, int(round(float(item.get("expected_downtime_loss") or 0.0))))
            e_repl = max(0, int(round(float(item.get("expected_replacement_cost") or 0.0))))
            e_sec = max(0, int(round(float(item.get("expected_secondary_loss") or 0.0))))

            # Enforce strict closed-form identity: Gross SLE == E[Downtime] + E[Replacement] + E[Secondary]
            gross_sle = e_down + e_repl + e_sec
            gross_ale = max(0, int(round(lef * float(gross_sle))))
            gross_p90 = max(gross_ale, int(round(float(item.get("gross_p90") or (gross_ale * 1.85)))))

            max_disc = float(item.get("max_euler_ale_discount_pct") or 0.20)
            if physics == "FINOPS_RESOURCE_WASTE" or epistemic != "VERIFIED_EMPIRICAL":
                max_disc = 0.0
            else:
                max_disc = min(cls.MAX_PORTFOLIO_ALE_DISCOUNT, max(0.0, max_disc))

            active_ids.append(f_id)
            standalone_ales[f_id] = gross_ale
            max_discounts[f_id] = max_disc
            raw_metrics[f_id] = {
                "lef": lef,
                "e_down": e_down,
                "e_repl": e_repl,
                "e_sec": e_sec,
                "gross_sle": gross_sle,
                "gross_ale": gross_ale,
                "gross_p90": gross_p90,
                "physics": physics,
                "epistemic": epistemic,
                "max_var_disc": min(0.25, float(item.get("max_euler_var_discount_pct") or 0.25)),
            }

        diversifiable_ids = [
            fid for fid in active_ids if standalone_ales[fid] > 0 and max_discounts[fid] > 0.0
        ]
        n_div = len(diversifiable_ids)

        for fid in active_ids:
            m = raw_metrics[fid]
            gross_ale = m["gross_ale"]
            if n_div <= 1 or fid not in diversifiable_ids or gross_ale == 0:
                eff_disc = 0.0
                var_disc = 0.0
            else:
                # Smooth logarithmic causal overlap curve bounded strictly by [0%, max_discounts[fid]]
                # Never exceeds 20%-25% even for 60+ findings
                empirical_overlap = min(0.22, 0.05 * (n_div - 1) / (1.0 + 0.20 * (n_div - 1)))
                eff_disc = min(max_discounts[fid], empirical_overlap)
                var_disc = min(m["max_var_disc"], empirical_overlap * 1.25)

            net_ale = int(round(float(gross_ale) * (1.0 - eff_disc)))
            # Hard floor invariant: Net ALE >= 75% of Gross Standalone ALE
            net_ale = max(int(round(float(gross_ale) * (1.0 - cls.MAX_PORTFOLIO_ALE_DISCOUNT))), min(gross_ale, net_ale))
            euler_adj = net_ale - gross_ale  # Strictly <= 0

            actual_disc_pct = (
                Decimal(str((gross_ale - net_ale) * 100.0 / float(gross_ale))).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                if gross_ale > 0
                else Decimal("0.0")
            )
            net_p90 = max(net_ale, int(round(float(m["gross_p90"]) * (1.0 - var_disc))))

            decomp = AdditiveLossDecomposition(
                currency_iso=currency_iso.upper(),
                mean_lef=m["lef"],
                expected_downtime_loss=m["e_down"],
                expected_replacement_cost=m["e_repl"],
                expected_secondary_loss=m["e_sec"],
                gross_mean_sle=m["gross_sle"],
                gross_standalone_ale=gross_ale,
                euler_overlap_adjustment_ale=euler_adj,
                net_allocated_ale=net_ale,
                euler_discount_pct=actual_disc_pct,
                gross_standalone_p90=m["gross_p90"],
                net_allocated_p90=net_p90,
                loss_physics=m["physics"],
                epistemic_state=m["epistemic"],
            )
            decomp.validate_conservation()
            decompositions[fid] = decomp

        return decompositions
```

Also tighten the tower-level guardrail in `EulerPortfolioAllocator.allocate_portfolio`:
```python
        # Natural Copula Diversification Guardrail (Basel III / Solvency II Bound: [12%, 25%]):
        if subtotal_gross > 0 and len(sorted_towers) > 1:
            implied_discount = (subtotal_gross - target_net) / float(subtotal_gross)
            if implied_discount > 0.25 or implied_discount < 0.0 or target_net <= 0:
                natural_discount = min(
                    0.25, max(0.12, 0.10 + 0.015 * len(sorted_towers))
                )
                target_net = int(
                    round(float(subtotal_gross) * (1.0 - natural_discount))
                )
```

---

#### 5.4 Refactoring `in_memory_asis_compiler.py` & `payload_to_ast.py` (Zero-Plug Serialization & Boilerplate Quarantine)

1. **In `in_memory_asis_compiler.py`:**
   Separate `VERIFIED_EMPIRICAL` findings from `SURVEY_INFERRED_BOILERPLATE` findings so that survey boilerplate never fabricates Monte Carlo risk cards:

```python
            from assessment_engine.domain.actuarial.finding_archetype_resolver import (
                EpistemicEvidenceState,
                PolymorphicFindingClassifier,
            )

            physics_profile = PolymorphicFindingClassifier.classify_finding(
                hc=eff_hc,
                tower_id=current_tower_id,
            )

            if physics_profile.epistemic_state == EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE:
                # Quarantine survey boilerplate from actuarial fabrication; record in epistemic gap register
                epistemic_gap_item: dict[str, Any] = {
                    "id": eff_hc.get("id", f"GAP-{r_counter:02d}"),
                    "pillar": pillar_name,
                    "pillar_id": p_id,
                    "capability": capability,
                    "epistemic_state": EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE.value,
                    "finding": "Control maturity gap inferred from questionnaire score; empirical telemetry required for FAIR quantification.",
                    "ale": 0.0,
                    "p90": 0.0,
                    "ale_str": "UNQUANTIFIED (SURVEY ONLY)",
                    "p90_str": "UNQUANTIFIED (SURVEY ONLY)",
                }
                b_data.setdefault("epistemic_maturity_gaps", []).append(epistemic_gap_item)
                r_counter += 1
                continue
```

2. **In `payload_to_ast.py` (`_build_fair_risk_analysis`):**
   **Completely delete** `stochastic_tail_adj = round(reconciled_sle - (primary_downtime_loss + repl_cost_num + sec_weighted_loss))` and replace it with strict read-only serialization of `AdditiveLossDecomposition`:

```python
            # --- STRICT READ-ONLY SERIALIZATION OF ADDITIVE LOSS DECOMPOSITION (ZERO PLUGS) ---
            decomp = risk.get("additive_loss_decomposition") or {}
            expected_downtime_loss = int(decomp.get("expected_downtime_loss", 0))
            expected_replacement_cost = int(decomp.get("expected_replacement_cost", 0))
            expected_secondary_loss = int(decomp.get("expected_secondary_loss", 0))
            gross_mean_sle = int(
                decomp.get(
                    "gross_mean_sle",
                    expected_downtime_loss + expected_replacement_cost + expected_secondary_loss,
                )
            )
            gross_standalone_ale = int(decomp.get("gross_standalone_ale", round(float(risk.get("intrinsic_ale") or 0.0))))
            euler_overlap_adj_ale = int(decomp.get("euler_overlap_adjustment_ale", 0))
            net_allocated_ale = int(decomp.get("net_allocated_ale", round(float(risk.get("ale") or 0.0))))

            # Hard assertion: Presentation layer NEVER invents a balancing plug
            assert (
                expected_downtime_loss + expected_replacement_cost + expected_secondary_loss == gross_mean_sle
            ), f"SLE conservation failure on risk {risk.get('id')}"
            assert (
                gross_standalone_ale + euler_overlap_adj_ale == net_allocated_ale
            ), f"ALE bridge conservation failure on risk {risk.get('id')}"

            # Render SLE Table Rows (Pure Physical Severity):
            # Row 1: Expected Operational Interruption Loss (E[Downtime]) -> expected_downtime_loss
            # Row 2: Direct Remediation / Replacement / Resource Cost (E[Replacement]) -> expected_replacement_cost
            # Row 3: Expected Secondary / Regulatory Loss (E[Secondary]) -> expected_secondary_loss
            # Row 4: Gross Single Loss Expectancy (SLE_gross) -> gross_mean_sle
            #
            # Render Annualized Portfolio Bridge Rows:
            # Row 5: Gross Standalone Annualized Loss (ALE_gross = LEF x SLE_gross) -> gross_standalone_ale
            # Row 6: Causal Overlap Diversification Credit (Bounded <= 25%) -> euler_overlap_adj_ale
            # Row 7: Net Portfolio-Allocated Annualized Exposure (ALE_net) -> net_allocated_ale
```

---

### SUMMARY OF ARCHITECTURAL INVARIANTS ENFORCED

| Forensic Failure Mode | Root Cause | Institutional Resolution Enforced |
| :--- | :--- | :--- |
| **1. Idle VMs & Missing IaC Modeled as 14h Factory Blackouts** | `input_resolver.py` & `payload_to_ast.py` resolved `LossArchetypeType` from `tower_id` instead of finding semantics. | `PolymorphicFindingClassifier` dispatches `FindingLossPhysics` per finding (`FINOPS_RESOURCE_WASTE` & `ENGINEERING_VELOCITY_FRICTION` enforce `allows_downtime_burn = False`, `rto_hours = 0.0`). |
| **2. Artificial Plug Numbers (-30k € to -102k €)** | `payload_to_ast.py` back-solved `reconciled_sle` from diversified ALE and subtracted deterministic mode estimates. | `AdditiveLossDecomposition` enforces $\text{SLE}_{\text{gross}} = \mathbb{E}[L_{\text{down}}] + \mathbb{E}[L_{\text{repl}}] + \mathbb{E}[L_{\text{sec}}]$ upstream and separates SLE from ALE Euler adjustments. `stochastic_tail_adj` is permanently eradicated. |
| **3. Excessive 60%–79% Euler Risk Erasure** | Upstream applied $O(1/\sqrt{K})$ VaR dispersion scaling to Mean ALE without per-finding floors. | `EulerPortfolioAllocator` caps Mean ALE causal overlap adjustment at **25.0% max** (**0.0%** for FinOps/OpEx), enforcing $\text{ALE}_{\text{net}, i} \ge 0.75 \times \text{ALE}_{\text{gross}, i}$. |
| **4. 17 Robotic Boilerplate Risk Cards** | Likert-scale survey fallbacks injected `"Carencia de controles operativos formalizados..."` into `health_check_asis`. | `EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE` quarantines unverified survey strings into the Epistemic Maturity Gap Register with status `UNQUANTIFIED (SURVEY ONLY)`. |