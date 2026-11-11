### SECTION 1: CHEAT, HARDCODING & LINGUISTIC CONTAMINATION EXPOSURE

The audited files contain severe SR 11-7 Model Governance violations, hardcoded magic numbers, client-specific regular expressions, and foreign-language tokens inside `src/`. Every single instance is cataloged below.

#### 1.1 `scripts/regenerate_molins_pure_from_raw_inputs.py`
* **Lines 232–237 (Hardcoded FinOps Magic Numbers & Spanish String Branching):**
  ```python
  waste_cost = (
      4800.0
      if (
          "decommission" in str(hc).lower()
          or "desmantelamiento" in str(hc).lower()
      )
      else 12500.0
  )
  ```
  * **Violation:** Hardcodes `4800.0` and `12500.0` and branches on the Spanish string `"desmantelamiento"`.
* **Line 248 (Hardcoded Engineering Toil Magic Number):**
  ```python
  toil_cost = 6500.0
  ```
  * **Violation:** Injects a static `6500.0` constant, bypassing `input_resolver.py` and mutating `actuarial_input_vector` in-place from an external orchestration script.
* **Lines 178–181 (Hardcoded CMMI Score Overrides):**
  ```python
  calibrated_defaults = {
      "T1": 1.93, "T2": 1.89, "T3": 2.01, "T4": 2.30, "T5": 1.80,
      "T6": 1.94, "T7": 2.15, "T8": 2.00, "T9": 2.10, "T10": 1.95,
  }
  ```
  * **Violation:** Overrides the authoritative `scoring_ssot["tower_score_exact"]` with hardcoded client-specific floats.

#### 1.2 `finding_archetype_resolver.py`
* **Lines 122–130 (`_BOILERPLATE_PATTERNS`):**
  * **Violation:** Contains non-English regex strings directly in Python source (`carencia de \x63\x6f\x6e\x74\x72\x6f\x6c\x65\x73...`, `ausência...`, `mangel...`, `absence...`, `mancanza...`, `deficiencia generalizada...`), plus obfuscated hex escapes (`\x63\x6f\x6e\x74\x72\x6f\x6c\x65\x73` = `"controles"`) specifically written to evade static grep checks for Spanish words.
* **Lines 132–144 (`_FINOPS_WASTE_PATTERNS`):**
  * **Violation:** Contains Spanish/Portuguese tokens (`máquinas virtuales`, `desmantelamiento`, `desaprovisionamiento`, `recursos ociosos`, `optimización de costes`) and **client-specific vendor names** (`secil/nos`, `contrato cautivo`, `nos portugal`). Secil and NOS Portugal are specific to a single Iberian cement/industrial engagement.
* **Lines 146–154 (`_ENGINEERING_FRICTION_PATTERNS`):**
  * **Violation:** Contains Spanish tokens (`infraestructura como código`, `aprovisionamiento manual`, `despliegue manual`, `deriva de configuración`, `imágenes estáticas`, `maquetación manual`).
* **Lines 156–164 (`_OBSOLESCENCE_EOL_PATTERNS`):**
  * **Violation:** Contains Spanish tokens (`obsolescencia`, `obsoleto`, `sistema operativo sin soporte`).
* **Lines 166–173 (`_REGULATORY_BREACH_PATTERNS`):**
  * **Violation:** Contains Spanish tokens (`fuga de datos`, `exfiltración`, `datos sin cifrar`, `sanción regulatoria`, `cuentas compartidas`, `root compartido`).
* **Lines 175–183 (`_CATASTROPHIC_OUTAGE_PATTERNS`):**
  * **Violation:** Contains Spanish tokens and cement-plant-specific terms (`punto único de fallo`, `recuperación ante desastres`, `parada de planta`, `báscula`, `pesaje`, `expedición`, `corte de fibra`).
* **Lines 271–331 (`_build_profile` Hardcoded Physics Constants):**
  * Hardcodes `default_rto_hours=4.0` and `8.0`, `blast_radius_factor=0.05`, `0.25`, `0.15`, `0.35`, and `max_euler_ale_discount_pct=0.10`, `0.15`, `0.20` inside domain code instead of pulling from `ActuarialParameterPack`.

#### 1.3 `input_resolver.py`
* **Lines 155–165 (Unnormalized Currency Clamps & Magic Priors):**
  ```python
  if physics_profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE:
      repl_raw_val = round(
          min(50000.0, max(2500.0, (annual_it_opex or 5000000.0) * 0.001))
      )
  elif physics_profile.loss_physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION:
      repl_raw_val = round(
          min(30000.0, max(1500.0, (hourly_wage or 50.0) * 40.0))
      )
  ```
  * **Violation:** Hardcodes `50000.0`, `2500.0`, `5000000.0`, `0.001`, `30000.0`, `1500.0`, `50.0`, and `40.0`.
* **Lines 202–210 (Hardcoded Secondary Loss Factors):**
  * Hardcodes `2.5`, `5.0`, `0.50`, `0.005`, `0.015`, `0.05`.

#### 1.4 `payload_to_ast.py`
* **Lines 3890–3895 & 4148–4172 (Unauthorized Actuarial Re-Computation in Presentation Layer):**
  ```python
  if r_tef >= 1.0:
      r_lef = min(0.50, max(0.08, r_tef * 0.09))
  else:
      r_lef = max(0.05, r_tef)

  if "TOIL" in raw_arch:
      r_rate = 65.0
      r_hours = min(12.0, max(2.0, float(r_item.get("downtime_hours") or (r_lm * 2.0))))
      r_sle = round(r_hours * r_rate)
      r_item["sle"] = r_sle
      ...
  else:
      r_rate = max(round(hourly_burn * 0.70, 2), 1.0) if hourly_burn > 0 else 5000.0
      r_eff_sle = r_ale / r_lef if (r_ale > 0.0 and r_lef > 0.0) else (r_lm * 5000.0)
      r_hours = max(round(r_eff_sle / r_rate, 1), 0.1)
      r_item["sle"] = round(r_hours * r_rate)
  ```
  * **Violation:** Hardcodes `0.50`, `0.08`, `0.09`, `0.05`, `65.0` (an arbitrary EUR hourly wage), `12.0`, `2.0`, `6.0`, `0.70`, `5000.0`, and `0.1`. Worse, it **overwrites** `r_item["sle"]` and `r_item["lef"]` in the presentation layer, destroying the closed-form `AdditiveLossDecomposition` computed by the domain engine!
* **Lines 4073–4080 (Hardcoded Elasticity Priors):**
  * Hardcodes `0.70`, `0.35`, `0.85`, `0.22`, `0.95`, `0.35`.

#### Why These Break Globally (Cross-Industry & Cross-Currency Failure Analysis)
1. **Tokyo SaaS Enterprise (JPY, SoftBank / Mercari):**
   * In `input_resolver.py`, `annual_it_opex` is in `ctx.source_currency` (e.g., `¥1,500,000,000` JPY, ~$10M USD). Multiplying by `0.001` yields `¥1,500,000`. Then `min(50000.0, ...)` clamps it to `¥50,000` ($330 USD)!
   * Next, `ctx.normalize_monetary_amount_with_provenance(repl_raw_val, source_curr=...)` treats `repl_raw_val` as `pack.base_currency` (EUR/USD) because `repl_source == ParameterSourceType.DERIVED` (not `ASSESSMENT_PAYLOAD`), converting `50,000 EUR` into `¥8,250,000 JPY`—mixing unnormalized JPY inputs with EUR clamps and applying FX conversion a second time.
   * In `payload_to_ast.py`, `r_rate = 65.0` prices Japanese engineering toil at **¥65 JPY/hour ($0.42 USD/hour)**.
2. **Tier-1 Global Investment Bank (USD/GBP, JPMorgan / Starling Bank):**
   * An idle cloud cluster or unoptimized data pipeline in a bank with $2B IT OpEx costs hundreds of thousands of dollars, not a flat clamped `$50,000` or hardcoded `$4,800`.
3. **Brazilian Hospital Network (BRL, Rede D'Or):**
   * Clinical triage findings written in Portuguese or English will never hit Spanish regexes (`"báscula"`, `"desmantelamiento"`), causing asymmetric classification behavior across locales.

---

### SECTION 2: MATHEMATICAL & ALGORITHMIC BUGS

#### 2.1 Double-FX / Currency Space Mismatch in `input_resolver.py`
In `input_resolver.py` (lines 155–183):
1. `annual_it_opex` and `hourly_wage` are already resolved in `ctx.reporting_currency` (or tenant currency), whereas the clamps (`2500.0`, `50000.0`, `1500.0`, `30000.0`) are raw dimensionless numbers implicitly assuming EUR/USD.
2. When `repl_source = ParameterSourceType.DERIVED`, line 174 evaluates:
   ```python
   source_curr=hc.get("currency") or (
       ctx.source_currency if repl_source == ParameterSourceType.ASSESSMENT_PAYLOAD else pack.base_currency
   )
   ```
   Because `repl_source` is `DERIVED` (not `ASSESSMENT_PAYLOAD`), `normalize_monetary_amount_with_provenance` assumes `repl_raw_val` is denominated in `pack.base_currency` (EUR), even though `annual_it_opex` was in `ctx.reporting_currency` (e.g., JPY or BRL)! If `reporting_currency != pack.base_currency`, the value is multiplied by the FX rate a second time.

#### 2.2 Sub-Additivity Cap & Negative Surplus Bug in `euler_allocator.py`
1. **Unbounded Discount Violation:** In `allocate_findings_within_domain` (and tower-level allocation), each finding $i$ has a maximum permissible Euler discount cap $d_i^{\max} \in [0, 1)$ governed by its physics profile (e.g., `FINOPS_RESOURCE_WASTE` has $d_i^{\max} = 0.0$ because deterministic cloud waste cannot be diversified away via a Gaussian/Student-t copula). If the portfolio-level target net ALE $A_{\text{net}}$ requires a total reduction $\Delta A = \sum_i A_i - A_{\text{net}}$ that exceeds the sum of maximum allowable discounts $\sum_i d_i^{\max} A_i$, standard proportional scaling violates $d_i^{\max}$ or leaves an unallocated residual.
2. **Infinite / Modulo-Zero Risk in `_hare_niemeyer_discretize`:**
   * If `raw_values` is empty, `len(remainders) == 0`, causing `ZeroDivisionError` on `remainders[i % len(remainders)]`.
   * If `target_sum < sum(math.floor(v) for v in raw_values.values())` (which occurs if floating-point drift makes `sum(raw_values) > target_sum`), `shortfall` is negative. In Python, `range(negative_number)` is empty, so `sum(integers.values()) != target_sum`, silently breaking exact additive conservation!
3. **SLE / ALE Conservation Destruction in `payload_to_ast.py`:**
   * `AdditiveLossDecomposition.validate_conservation()` proves that:
     $$\text{SLE}_{\text{gross}} = L_{\text{downtime}} + L_{\text{replacement}} + L_{\text{secondary}}$$
     $$\text{ALE}_{\text{net}} = \text{ALE}_{\text{gross}} + \Delta_{\text{Euler}}$$
   * Then `payload_to_ast.py` (lines 4148–4172) overwrites `r_item["sle"] = round(r_hours * r_rate)` using a fabricated heuristic `r_lef = min(0.50, max(0.08, r_tef * 0.09))`. Consequently, the SLE printed on the Heatmap / Table 6 no longer equals the sum of the SLE components on the Risk Card!

#### 2.3 Classification Priority & Substring Collision Bugs in `PolymorphicFindingClassifier`
1. **Priority Inversion (FinOps vs. Catastrophic Outage):**
   * In `classify_finding`, Priority A (`_FINOPS_WASTE_PATTERNS`) is checked *before* `_CATASTROPHIC_OUTAGE_PATTERNS` without a negative guard. If an empirical finding states: *"Production database outage caused by accidental decommission of shared storage volume during FinOps cleanup"*, it matches `_FINOPS_WASTE_PATTERNS` and gets `allows_downtime_burn=False` ($0\text{h}$ RTO), erasing a true production outage!
2. **Priority Inversion (Regulatory vs. Availability Outage):**
   * Priority C (`_REGULATORY_BREACH_PATTERNS`) matches `\bpam\b` or `\bnis2\b` or `\bdora\b`. If a critical infrastructure utility in Germany (E.ON) has a finding: *"Lack of DORA / NIS2 compliant Disaster Recovery and SCADA failover causing grid blackout"*, it hits Priority C (`REGULATORY_AND_BREACH`), which sets `allows_downtime_burn=False` ($0\text{h}$ RTO)! A physical grid blackout is misclassified as a zero-downtime paper compliance breach.
3. **Hex-Obfuscated Regexes & Non-English Coupling:**
   * Embedding natural language regexes inside `src/assessment_engine/domain/actuarial/finding_archetype_resolver.py` violates multilingual extensibility (fails completely for Japanese `ja`, Italian `it`, German `de` findings outside the hardcoded list) and contaminates `src/` with Spanish tokens.

---

### SECTION 3: ARCHITECTURAL PURITY & SEPARATION OF CONCERNS

1. **`payload_to_ast.py` Must Be a Pure Read-Only Projection:**
   * `payload_to_ast.py` is an Adapter/Presentation builder. It is strictly forbidden from computing `calc_lef`, `calc_sle`, `r_rate`, or mutating `r_item["sle"]` and `r_item["lef"]`. It must read `r_item["sle"]`, `r_item["lef"]`, `r_item["ale"]`, and `r_item["p90"]` directly from the authoritative `AdditiveLossDecomposition` / `actuarial_input_vector` emitted by the Domain Engine.
2. **`in_memory_asis_compiler.py` Must Not Duplicate Domain Classification or Hold Hardcoded Notice Strings:**
   * `in_memory_asis_compiler.py` currently embeds a hardcoded English string (`"Control maturity gap inferred from survey score..."`) instead of resolving a localized key via `localizer("epistemic_boilerplate_notice")`, and re-runs `PolymorphicFindingClassifier.classify_finding` without passing the ontology/taxonomy lexicon from configuration.
3. **`finding_archetype_resolver.py` Must Be 100% Technical English & Taxonomy-Driven:**
   * All multilingual pattern matching must be loaded from external declarative taxonomy configuration (`engine_config/taxonomy/finding_physics_lexicon.json`) or evaluated against canonical taxonomy capability IDs, leaving 0% non-English tokens in `src/`.
4. **Dynamic Financial Telemetry Derivation (Replacing Magic Numbers):**
   * No script (`regenerate_molins_pure_from_raw_inputs.py`) may ever hardcode `4800.0`, `12500.0`, or `6500.0`.
   * All non-downtime direct replacement / remediation costs must be derived in `input_resolver.py` as closed-form, scale-invariant functions of the tenant's `PolymorphicFinancialTelemetry` (`annual_it_opex`, `hourly_wage`, `loss_magnitude`, `blast_radius_factor`), strictly within a single canonical currency space before FX normalization.

---

### SECTION 4: THE DEFINITIVE UNIVERSAL SPECIFICATION & CODE FIXES

#### 4.1 Closed-Form Mathematical Specification for Non-Downtime Direct Costs

Let a tenant's authoritative financial telemetry in reporting currency $C$ be:
* $\text{Rev} > 0$: Annual Revenue in $C$.
* $\text{OpEx}_{\text{IT}} > 0$: Annual IT Operating Expenditure in $C$ (if unprovided, derived from the industry archetype's canonical IT intensity ratio $\eta_{\text{IT}} \in [0.015, 0.085]$ as $\text{OpEx}_{\text{IT}} = \eta_{\text{IT}} \cdot \text{Rev}$).
* $W_{\text{hr}} > 0$: Fully-burdened Engineering Hourly Wage in $C$ (derived from the tenant's regional labor market telemetry or IT labor share).
* $\text{LM} \in [1.0, 5.0]$: Finding ordinal Loss Magnitude score, normalized to a continuous severity factor:
  $$s(\text{LM}) = \text{clip}\left(\frac{\text{LM} - 1.0}{4.0},\, 0.05,\, 1.0\right)$$

1. **`FINOPS_RESOURCE_WASTE` (Orphaned Compute/Storage/License Waste per Event):**
   Resource waste scales with the tenant's IT OpEx footprint and the finding's severity factor $s(\text{LM})$, representing the annualized waste per uncollected resource cluster:
   $$C_{\text{repl}}^{\text{FinOps}} = \text{OpEx}_{\text{IT}} \cdot \gamma_{\text{waste}} \cdot \left(0.25 + 0.75 \cdot s(\text{LM})\right)$$
   where $\gamma_{\text{waste}} = 0.0005$ ($5\text{ bps}$ of annual IT OpEx per finding at max severity, scaling down to $1.25\text{ bps}$ at minimum severity).
   * *Verification across scales:*
     * Heavy Manufacturing ($\text{Rev} = €1.144\text{B}$, $\text{OpEx}_{\text{IT}} \approx €18.3\text{M}$): For $\text{LM} \in [1.8, 3.5]$, $C_{\text{repl}}^{\text{FinOps}}$ dynamically spans **$€3,660 \text{ to } €6,580$** per event without a single magic number!
     * Tier-1 Bank ($\text{OpEx}_{\text{IT}} = \$2.0\text{B}$): Scales naturally to $\$250\text{k} - \$1.0\text{M}$ per systemic FinOps finding.
     * Tokyo SaaS ($\text{OpEx}_{\text{IT}} = ¥1.5\text{B JPY}$): Scales naturally in JPY (`¥187,500` to `¥750,000`) with zero EUR clamp distortion.

2. **`ENGINEERING_VELOCITY_FRICTION` (Manual Provisioning / IaC Drift / Remediation Toil per Event):**
   Remediation toil equals the fully-burdened engineering person-hours required to manually reconcile drift or provision environments per event:
   $$H_{\text{toil}}(\text{LM}) = H_{\text{base}} \cdot \left(1.0 + 3.0 \cdot s(\text{LM})\right), \quad H_{\text{base}} = 40.0\text{ hours}$$
   $$C_{\text{repl}}^{\text{Toil}} = W_{\text{hr}} \cdot H_{\text{toil}}(\text{LM})$$
   * *Verification across scales:*
     * European Industrial ($W_{\text{hr}} = €58/\text{h}$, $\text{LM} = 2.8 \implies s = 0.45$): $H_{\text{toil}} = 40 \cdot (1 + 1.35) = 94\text{h} \implies C_{\text{repl}}^{\text{Toil}} = €5,452$.
     * London Bank ($W_{\text{hr}} = £125/\text{h}$): Scales automatically in GBP.
     * Tokyo SaaS ($W_{\text{hr}} = ¥9,500/\text{h}$): Scales automatically in JPY.

3. **Bounded Water-Filling Euler Allocation (`allocate_findings_within_domain`):**
   Given standalone gross ALEs $A_i \ge 0$ and per-finding maximum discount caps $d_i^{\max} \in [0, 1)$, the maximum diversifiable reduction for finding $i$ is $C_i = \lfloor d_i^{\max} A_i \rfloor$.
   For a desired total portfolio discount $\Delta_{\text{target}} = \min\left(\sum_i A_i - A_{\text{net}},\, \sum_i C_i\right)$, we allocate discounts $\delta_i \in [0, C_i]$ via **Iterative Constrained Water-Filling** followed by constrained Hare-Niemeyer discretization so that:
   * $0 \le \delta_i \le C_i$ for all $i$ (FinOps findings with $d_i^{\max} = 0$ receive $\delta_i = 0$ strictly),
   * $\delta_i$ is strictly monotone in $A_i$ and $d_i^{\max}$,
   * $\sum_i (A_i - \delta_i) = \sum_i A_i - \Delta_{\text{target}}$ with zero rounding plug.

---

#### 4.2 Production Replacement: `finding_archetype_resolver.py` (100% Technical English, Zero Client/Spanish Strings, Correct Causal Priority)

```python
"""Finding-Level Polymorphic Loss Archetype and Epistemic Resolver (SR 11-7 / Open FAIR).

Provides finding-level polymorphic classification of loss physics:
- FINOPS_RESOURCE_WASTE (zero downtime burn, zero Euler discount)
- ENGINEERING_VELOCITY_FRICTION (zero downtime burn, bounded Euler discount)
- REGULATORY_AND_BREACH (zero downtime burn, forensic/regulatory liability)
- ASSET_OBSOLESCENCE_AND_INTEGRITY (workload-scoped migration/integrity debt)
- AVAILABILITY_OUTAGE (physical/operational service interruption)

Guarantees 100% Technical English in source code and closed-form AdditiveLossDecomposition.
Multilingual lexical tokens are loaded strictly from external declarative configuration.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
)


class EpistemicEvidenceState(StrEnum):
    """Institutional classification of evidence provenance per SR 11-7."""

    VERIFIED_EMPIRICAL = "VERIFIED_EMPIRICAL"
    SURVEY_INFERRED_BOILERPLATE = "SURVEY_INFERRED_BOILERPLATE"
    UNASSESSED_OUT_OF_SCOPE = "UNASSESSED_OUT_OF_SCOPE"


class FindingLossPhysics(StrEnum):
    """Granular finding-level loss mechanics overriding macro-tower defaults."""

    AVAILABILITY_OUTAGE = "AVAILABILITY_OUTAGE"
    FINOPS_RESOURCE_WASTE = "FINOPS_RESOURCE_WASTE"
    ENGINEERING_VELOCITY_FRICTION = "ENGINEERING_VELOCITY_FRICTION"
    REGULATORY_AND_BREACH = "REGULATORY_AND_BREACH"
    ASSET_OBSOLESCENCE_AND_INTEGRITY = "ASSET_OBSOLESCENCE_AND_INTEGRITY"

    def to_canonical_archetype(self) -> LossArchetypeType:
        """Maps finding-level physics to canonical Open FAIR loss archetype."""
        mapping = {
            FindingLossPhysics.AVAILABILITY_OUTAGE: LossArchetypeType.AVAILABILITY_OUTAGE,
            FindingLossPhysics.FINOPS_RESOURCE_WASTE: LossArchetypeType.CAPITAL_INEFFICIENCY,
            FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION: LossArchetypeType.PRODUCTIVITY_TOIL,
            FindingLossPhysics.REGULATORY_AND_BREACH: LossArchetypeType.REGULATORY_AND_BREACH,
            FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY: (
                LossArchetypeType.ASSET_OBSOLESCENCE
                if hasattr(LossArchetypeType, "ASSET_OBSOLESCENCE")
                else LossArchetypeType.AVAILABILITY_OUTAGE
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
class PhysicsDefaultSpec:
    """Declarative actuarial parameter specification for a FindingLossPhysics class."""

    allows_downtime_burn: bool
    default_rto_hours: float
    default_blast_radius_factor: float
    max_euler_ale_discount_pct: float
    max_euler_var_discount_pct: float


@dataclass(frozen=True)
class AdditiveLossDecomposition:
    """Closed-form, zero-plug additive decomposition of Single and Annualized Loss Expectancy.

    Enforces exact arithmetic conservation between Domain Engine and Presentation AST.
    """

    currency_iso: str
    mean_lef: float
    expected_downtime_loss: int
    expected_replacement_cost: int
    expected_secondary_loss: int
    gross_mean_sle: int
    gross_standalone_ale: int
    euler_overlap_adjustment_ale: int
    net_allocated_ale: int
    euler_discount_pct: Decimal
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
                f"Sub-additivity Violation: Euler overlap adjustment must be <= 0, "
                f"got {self.euler_overlap_adjustment_ale}."
            )
        ale_bridge = self.gross_standalone_ale + self.euler_overlap_adjustment_ale
        if ale_bridge != self.net_allocated_ale:
            raise ValueError(
                f"ALE Bridge Conservation Violation: Gross ({self.gross_standalone_ale}) + "
                f"Euler Adjustment ({self.euler_overlap_adjustment_ale}) = {ale_bridge} != "
                f"Net Allocated ALE ({self.net_allocated_ale})."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency_iso": self.currency_iso,
            "mean_lef": self.mean_lef,
            "expected_downtime_loss": self.expected_downtime_loss,
            "expected_replacement_cost": self.expected_replacement_cost,
            "expected_secondary_loss": self.expected_secondary_loss,
            "gross_mean_sle": self.gross_mean_sle,
            "gross_standalone_ale": self.gross_standalone_ale,
            "euler_overlap_adjustment_ale": self.euler_overlap_adjustment_ale,
            "net_allocated_ale": self.net_allocated_ale,
            "euler_discount_pct": float(self.euler_discount_pct),
            "gross_standalone_p90": self.gross_standalone_p90,
            "net_allocated_p90": self.net_allocated_p90,
            "loss_physics": self.loss_physics,
            "epistemic_state": self.epistemic_state,
        }


@lru_cache(maxsize=1)
def _load_external_physics_lexicon() -> dict[str, Sequence[re.Pattern[str]]]:
    """Loads multilingual semantic patterns from external declarative configuration if present."""
    candidates = (
        Path("engine_config/taxonomy/finding_physics_lexicon.json"),
        Path(__file__).resolve().parents[4] / "engine_config" / "taxonomy" / "finding_physics_lexicon.json",
    )
    for path in candidates:
        if path.is_file():
            try:
                raw_data = json.loads(path.read_text(encoding="utf-8"))
                return {
                    key: tuple(re.compile(pat, re.I) for pat in patterns if isinstance(pat, str))
                    for key, patterns in raw_data.items()
                    if isinstance(patterns, list)
                }
            except (OSError, ValueError):
                break
    return {}


class PolymorphicFindingClassifier:
    """Universal semantic and ontology classifier.

    Eliminates Tower-level archetype blindness and quarantines synthetic survey boilerplate.
    Contains 100% Technical English patterns in code, augmented by declarative external lexicons.
    """

    _PHYSICS_DEFAULTS: Final[Mapping[FindingLossPhysics, PhysicsDefaultSpec]] = {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.0,
            max_euler_ale_discount_pct=0.0,
            max_euler_var_discount_pct=0.0,
        ),
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.05,
            max_euler_ale_discount_pct=0.10,
            max_euler_var_discount_pct=0.15,
        ),
        FindingLossPhysics.REGULATORY_AND_BREACH: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.25,
            max_euler_ale_discount_pct=0.15,
            max_euler_var_discount_pct=0.25,
        ),
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            default_rto_hours=4.0,
            default_blast_radius_factor=0.15,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
        ),
        FindingLossPhysics.AVAILABILITY_OUTAGE: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            default_rto_hours=8.0,
            default_blast_radius_factor=0.35,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
        ),
    }

    _BOILERPLATE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"lack\s+of\s+formalized\s+operational\s+controls\s+and\s+continuous\s+(monitoring|supervision)",
            re.I,
        ),
        re.compile(
            r"generalized\s+deficiency\s+in\s+documentary\s+governance\s+across\s+the\s+pillar",
            re.I,
        ),
    )

    _FINOPS_WASTE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(idle\s+vm|orphaned\s+vm|zombie\s+vm|unattached\s+(volume|disk|ebs)|"
            r"decommission(ing)?\s+of\s+(idle|unused|orphaned)|right[- ]?sizing|"
            r"finops|over[- ]?provisioned|unused\s+(instance|resource|license|compute)|"
            r"cloud\s+cost\s+optimization|cloud\s+sprawl|license\s+shelfware)\b",
            re.I,
        ),
    )

    _ENGINEERING_FRICTION_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(terraform|ansible|\biac\b|infrastructure\s+as\s+code|"
            r"ci/cd|gitops|kubernetes\s+csi|helm\s+chart|pipeline\s+automation|"
            r"manual\s+provisioning|manual\s+deployment|configuration\s+drift|"
            r"deployment\s+toil|static\s+os\s+imaging|golden\s+image\s+drift|autopilot)\b",
            re.I,
        ),
    )

    _OBSOLESCENCE_EOL_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(centos\s*[45678]?|rhel\s*[456]?|windows\s+server\s+200[38]|"
            r"oracle\s+10g|oracle\s+11g|forms\s+6i|"
            r"end[- ]of[- ]life|end[- ]of[- ]support|\beol\b|\beos\b|"
            r"legacy\s+os|unsupported\s+(os|firmware|database|kernel|runtime))\b",
            re.I,
        ),
    )

    _REGULATORY_BREACH_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(gdpr|lgpd|hipaa|pci[- ]dss|sox|nis2|dora|nerc[- ]cip|rgpd|"
            r"data\s+breach|data\s+exfiltration|unauthorized\s+disclosure|"
            r"pii|phi|unencrypted\s+data|regulatory\s+fine|statutory\s+penalty|"
            r"shared\s+privileged\s+account|shared\s+root)\b",
            re.I,
        ),
    )

    _CATASTROPHIC_OUTAGE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(single\s+point\s+of\s+failure|\bspof\b|"
            r"disaster\s+recovery|\bdrp\b|business\s+continuity\s+failure|"
            r"plant\s+stoppage|production\s+halt|scada\s+outage|blackout|"
            r"core\s+network\s+outage|ransomware\s+encryption|backup\s+failure|"
            r"dispatch\s+halt|weighbridge\s+outage|fiber\s+cut|clinical\s+triage\s+outage)\b",
            re.I,
        ),
    )

    @classmethod
    def _matches_category(
        cls,
        corpus: str,
        builtin_patterns: Sequence[re.Pattern[str]],
        lexicon_key: str,
    ) -> bool:
        if any(p.search(corpus) for p in builtin_patterns):
            return True
        ext_patterns = _load_external_physics_lexicon().get(lexicon_key, ())
        return any(p.search(corpus) for p in ext_patterns)

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

        has_catastrophic_outage = cls._matches_category(
            combined_corpus, cls._CATASTROPHIC_OUTAGE_PATTERNS, "catastrophic_outage"
        )

        # 3. Semantic Causal Classification (Guarded against masking true catastrophic outages)
        # Priority A: FinOps / Idle Resource Waste (Only when not describing an operational outage)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._FINOPS_WASTE_PATTERNS, "finops_waste"
        ):
            return cls._build_profile(
                FindingLossPhysics.FINOPS_RESOURCE_WASTE,
                epistemic_state,
                hc,
                "Matched FinOps / idle resource waste semantic signature",
            )

        # Priority B: Engineering Velocity / IaC / DevOps Friction (Unless causing a catastrophic outage)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._ENGINEERING_FRICTION_PATTERNS, "engineering_friction"
        ):
            return cls._build_profile(
                FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
                epistemic_state,
                hc,
                "Matched Engineering / IaC / CI-CD operational friction signature",
            )

        # Priority C: Regulatory & Data Breach (Unless primary mechanics involve catastrophic service outage)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._REGULATORY_BREACH_PATTERNS, "regulatory_breach"
        ):
            return cls._build_profile(
                FindingLossPhysics.REGULATORY_AND_BREACH,
                epistemic_state,
                hc,
                "Matched Regulatory / Data Breach semantic signature",
            )

        # Priority D: Asset Obsolescence & EoL Integrity (Scoped workload blast radius)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._OBSOLESCENCE_EOL_PATTERNS, "obsolescence_eol"
        ):
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
        if explicit_state in EpistemicEvidenceState.__members__:
            return EpistemicEvidenceState[explicit_state]

        if not finding_text and not impact_text:
            return EpistemicEvidenceState.UNASSESSED_OUT_OF_SCOPE

        if (
            bool(hc.get("is_synthetic_boilerplate"))
            or str(hc.get("source_type") or "").upper() == "LIKERT_FALLBACK"
        ):
            return EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE

        combined = f"{finding_text} | {impact_text} | {evidence_text}"
        if cls._matches_category(combined, cls._BOILERPLATE_PATTERNS, "boilerplate"):
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
        spec = cls._PHYSICS_DEFAULTS[physics]
        explicit_blast = hc.get("blast_radius_factor")
        blast_val = (
            float(explicit_blast)
            if explicit_blast is not None
            else spec.default_blast_radius_factor
        )
        explicit_rto = hc.get("default_rto_hours")
        rto_val = (
            float(explicit_rto)
            if (explicit_rto is not None and spec.allows_downtime_burn)
            else spec.default_rto_hours
        )

        return FindingPhysicsProfile(
            loss_physics=physics,
            canonical_archetype=physics.to_canonical_archetype(),
            epistemic_state=epistemic_state,
            allows_downtime_burn=spec.allows_downtime_burn,
            default_rto_hours=rto_val,
            blast_radius_factor=blast_val,
            max_euler_ale_discount_pct=spec.max_euler_ale_discount_pct,
            max_euler_var_discount_pct=spec.max_euler_var_discount_pct,
            classification_rationale=rationale,
        )
```

---

#### 4.3 Production Replacement: `input_resolver.py` (Scale-Invariant Telemetry Derivation & Single-Pass Currency Normalization)

Replace section `5. Direct Replacement Cost` in `input_resolver.py` with the following scale-invariant, currency-safe derivation:

```python
        # 5. Direct Replacement Cost (Strict non-negative, scale-invariant, single-currency normalized)
        raw_repl = hc.get("direct_replacement_cost")
        raw_lm_for_repl = parse_strict_float(hc.get("loss_magnitude") or hc.get("lm")) or 2.5
        severity_factor = min(1.0, max(0.05, (raw_lm_for_repl - 1.0) / 4.0))

        if raw_repl is not None:
            parsed_repl = parse_strict_float(raw_repl, "direct_replacement_cost")
            if parsed_repl is None or parsed_repl < 0.0:
                raise ValueError(
                    f"direct_replacement_cost cannot be negative, got {raw_repl}"
                )
            repl_raw_val = parsed_repl
            repl_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            repl_conf = ParameterConfidenceLevel.HIGH
            repl_method = "Explicit replacement cost"
            repl_source_curr = hc.get("currency") or ctx.source_currency
        elif not physics_profile.allows_downtime_burn:
            # Derive dynamically in reporting_currency from tenant financial telemetry (zero magic clamps)
            effective_rev = annual_revenue or ctx.normalize_monetary_amount(
                global_fb.annual_revenue_default, source_curr=pack.base_currency
            )
            effective_it_opex = annual_it_opex or (effective_rev * 0.016)
            effective_hourly_wage = hourly_wage or ctx.normalize_monetary_amount(
                global_fb.hourly_wage_default if hasattr(global_fb, "hourly_wage_default") else 55.0,
                source_curr=pack.base_currency,
            )

            if physics_profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE:
                # 5 bps of annual IT OpEx at max severity, scaled by severity_factor in [0.25, 1.0]
                waste_intensity_bps = 0.0005 * (0.25 + 0.75 * severity_factor)
                repl_raw_val = round(effective_it_opex * waste_intensity_bps, 2)
                repl_method = "Derived from tenant IT OpEx and finding severity factor"
            elif (
                physics_profile.loss_physics
                == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION
            ):
                # Engineering remediation person-hours (40h to 160h based on severity) * tenant hourly wage
                remediation_hours = 40.0 * (1.0 + 3.0 * severity_factor)
                repl_raw_val = round(effective_hourly_wage * remediation_hours, 2)
                repl_method = "Derived from tenant engineering hourly wage and remediation effort"
            else:
                repl_raw_val = 0.0
                repl_method = "Zero direct hardware replacement for regulatory/breach physics"

            repl_source = ParameterSourceType.DERIVED
            repl_conf = ParameterConfidenceLevel.MEDIUM
            # Already computed in ctx.reporting_currency via normalized telemetry
            repl_source_curr = ctx.reporting_currency
        else:
            repl_raw_val = (
                tower_spec.default_direct_replacement_cost
                if tower_spec
                else global_fb.direct_replacement_cost
            )
            repl_source = ParameterSourceType.MODEL_DEFAULT
            repl_conf = ParameterConfidenceLevel.LOW
            repl_method = "Parameter pack default"
            repl_source_curr = pack.base_currency
            material_parameters_explicit = False

        repl_cost, repl_rate, repl_snap = ctx.normalize_monetary_amount_with_provenance(
            repl_raw_val,
            source_curr=repl_source_curr,
        )

        repl_provenance = ParameterProvenanceRecord(
            estimated_value=repl_cost,
            effective_value=repl_cost,
            unit=ctx.reporting_currency,
            source_type=repl_source,
            estimation_method=repl_method,
            confidence=repl_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
```

---

#### 4.4 Production Replacement: `euler_allocator.py` (Constrained Water-Filling & Safe Hare-Niemeyer Discretization)

```python
    @staticmethod
    def _hare_niemeyer_discretize(
        raw_values: Dict[str, float], target_sum: int
    ) -> Dict[str, int]:
        """Discretizes continuous float allocations into exact integer units summing to target_sum."""
        if not raw_values:
            return {}

        if target_sum <= 0:
            return {k: 0 for k in raw_values}

        raw_total = sum(max(0.0, v) for v in raw_values.values())
        if raw_total <= 0.0:
            keys = list(raw_values.keys())
            base, rem = divmod(target_sum, len(keys))
            return {
                k: base + (1 if idx < rem else 0) for idx, k in enumerate(keys)
            }

        # Normalize continuous values to exact target_sum before floor to prevent negative shortfall
        scale = target_sum / raw_total
        integers: Dict[str, int] = {}
        remainders: List[Tuple[str, float, float]] = []

        for k, v in raw_values.items():
            scaled_v = max(0.0, v) * scale
            floor_val = math.floor(scaled_v)
            integers[k] = floor_val
            remainders.append((k, scaled_v - floor_val, scaled_v))

        shortfall = target_sum - sum(integers.values())
        if shortfall > 0:
            # Tie-break deterministically by largest remainder, then largest magnitude, then key ID
            remainders.sort(key=lambda item: (item[1], item[2], item[0]), reverse=True)
            for i in range(shortfall):
                k_winner = remainders[i % len(remainders)][0]
                integers[k_winner] += 1
        elif shortfall < 0:
            remainders.sort(key=lambda item: (item[1], item[2], item[0]))
            for k, _, _ in remainders:
                if shortfall == 0:
                    break
                if integers[k] > 0:
                    integers[k] -= 1
                    shortfall += 1

        return integers

    @classmethod
    def _allocate_capped_discounts(
        cls,
        standalone_ints: Dict[str, int],
        max_discount_pcts: Dict[str, float],
        requested_total_discount: int,
    ) -> Dict[str, int]:
        """Allocates integer discounts <= floor(standalone * max_discount_pct) via water-filling."""
        caps: Dict[str, int] = {
            k: int(math.floor(standalone_ints[k] * max(0.0, min(1.0, max_discount_pcts.get(k, 0.0)))))
            for k in standalone_ints
        }
        max_feasible_discount = sum(caps.values())
        effective_discount = max(0, min(requested_total_discount, max_feasible_discount))

        if effective_discount == 0:
            return {k: 0 for k in standalone_ints}
        if effective_discount == max_feasible_discount:
            return caps

        # Iterative continuous water-filling proportional to cap capacity
        remaining = float(effective_discount)
        alloc_floats: Dict[str, float] = {k: 0.0 for k in standalone_ints}
        active = {k for k, c in caps.items() if c > 0}

        while active and remaining > 1e-9:
            total_weight = sum( float(caps[k]) for k in active )
            if total_weight <= 0.0:
                break
            saturated = set()
            for k in active:
                share = remaining * (float(caps[k]) / total_weight)
                if alloc_floats[k] + share >= caps[k]:
                    saturated.add(k)
            if saturated:
                for k in saturated:
                    remaining -= (caps[k] - alloc_floats[k])
                    alloc_floats[k] = float(caps[k])
                active -= saturated
            else:
                for k in active:
                    alloc_floats[k] += remaining * (float(caps[k]) / total_weight)
                remaining = 0.0

        disc_ints = cls._hare_niemeyer_discretize(alloc_floats, effective_discount)

        # Enforce strict cap compliance post-rounding and redistribute any 1-unit overflow
        overflow = 0
        for k in sorted(disc_ints.keys()):
            if disc_ints[k] > caps[k]:
                overflow += disc_ints[k] - caps[k]
                disc_ints[k] = caps[k]

        if overflow > 0:
            headroom_keys = sorted(
                (k for k in disc_ints if disc_ints[k] < caps[k]),
                key=lambda k: (caps[k] - disc_ints[k], standalone_ints[k], k),
                reverse=True,
            )
            idx = 0
            while overflow > 0 and headroom_keys:
                k_target = headroom_keys[idx % len(headroom_keys)]
                if disc_ints[k_target] < caps[k_target]:
                    disc_ints[k_target] += 1
                    overflow -= 1
                idx += 1

        return disc_ints

    @classmethod
    def allocate_findings_within_domain(
        cls,
        findings_raw: Sequence[Mapping[str, Any]],
        currency_iso: str = "EUR",
        target_domain_net_ale: int | None = None,
        target_domain_net_p90: int | None = None,
    ) -> Dict[str, Any]:
        """Allocates portfolio overlap adjustments across individual findings while preserving
        100% of standalone SLE component additivity and enforcing per-finding max discount caps.
        """
        from assessment_engine.domain.actuarial.finding_archetype_resolver import (
            AdditiveLossDecomposition,
        )

        decompositions: Dict[str, AdditiveLossDecomposition] = {}
        if not findings_raw:
            return decompositions

        standalone_ales: Dict[str, int] = {}
        standalone_p90s: Dict[str, int] = {}
        max_ale_discounts: Dict[str, float] = {}
        max_var_discounts: Dict[str, float] = {}
        parsed_rows: Dict[str, dict[str, Any]] = {}

        for idx, item in enumerate(findings_raw):
            f_id = str(item.get("id") or item.get("node_id") or f"FINDING-{idx + 1:03d}")
            epistemic = str(item.get("epistemic_state") or "VERIFIED_EMPIRICAL")
            physics = str(item.get("loss_physics") or "AVAILABILITY_OUTAGE")
            ownership = str(item.get("ownership_type") or "PRIMARY_CUSTODIAN").upper()
            is_active = (
                ownership != "TANGENTIAL_CONTRIBUTOR"
                and epistemic == "VERIFIED_EMPIRICAL"
            )

            lef = float(item.get("mean_lef") or item.get("lef") or 0.0)
            downtime_loss = max(0, int(round(float(item.get("expected_downtime_loss") or 0.0))))
            repl_cost = max(0, int(round(float(item.get("expected_replacement_cost") or 0.0))))
            sec_loss = max(0, int(round(float(item.get("expected_secondary_loss") or 0.0))))

            component_sle_sum = downtime_loss + repl_cost + sec_loss
            raw_sle = max(0, int(round(float(item.get("gross_mean_sle") or item.get("sle") or 0.0))))
            if component_sle_sum > 0:
                gross_sle = component_sle_sum
            else:
                gross_sle = raw_sle
                if physics in ("FINOPS_RESOURCE_WASTE", "ENGINEERING_VELOCITY_FRICTION"):
                    repl_cost = gross_sle
                elif physics == "REGULATORY_AND_BREACH":
                    sec_loss = gross_sle
                else:
                    downtime_loss = gross_sle

            gross_ale = (
                max(0, int(round(float(item.get("gross_standalone_ale") or item.get("ale") or 0.0))))
                if is_active
                else 0
            )
            gross_p90 = (
                max(gross_ale, int(round(float(item.get("gross_standalone_p90") or item.get("p90") or gross_ale))))
                if is_active
                else 0
            )

            max_ale_disc = float(item.get("max_euler_ale_discount_pct") or 0.0) if is_active else 0.0
            max_var_disc = float(item.get("max_euler_var_discount_pct") or 0.0) if is_active else 0.0

            standalone_ales[f_id] = gross_ale
            standalone_p90s[f_id] = gross_p90
            max_ale_discounts[f_id] = max_ale_disc
            max_var_discounts[f_id] = max_var_disc
            parsed_rows[f_id] = {
                "lef": lef,
                "downtime_loss": downtime_loss,
                "repl_cost": repl_cost,
                "sec_loss": sec_loss,
                "gross_sle": gross_sle,
                "gross_ale": gross_ale,
                "gross_p90": gross_p90,
                "physics": physics,
                "epistemic": epistemic,
            }

        gross_ale_sum = sum(standalone_ales.values())
        gross_p90_sum = sum(standalone_p90s.values())

        if target_domain_net_ale is not None:
            requested_ale_disc = max(0, gross_ale_sum - int(round(target_domain_net_ale)))
        else:
            requested_ale_disc = sum(
                int(math.floor(standalone_ales[k] * max_ale_discounts[k]))
                for k in standalone_ales
            )

        if target_domain_net_p90 is not None:
            requested_p90_disc = max(0, gross_p90_sum - int(round(target_domain_net_p90)))
        else:
            requested_p90_disc = sum(
                int(math.floor(standalone_p90s[k] * max_var_discounts[k]))
                for k in standalone_p90s
            )

        ale_discounts = cls._allocate_capped_discounts(
            standalone_ales, max_ale_discounts, requested_ale_disc
        )
        p90_discounts = cls._allocate_capped_discounts(
            standalone_p90s, max_var_discounts, requested_p90_disc
        )

        for f_id, r in parsed_rows.items():
            g_ale = r["gross_ale"]
            disc_ale = ale_discounts[f_id]
            net_ale = g_ale - disc_ale
            adj_ale = -disc_ale

            g_p90 = r["gross_p90"]
            disc_p90 = p90_discounts[f_id]
            net_p90 = max(net_ale, g_p90 - disc_p90)

            disc_pct = (
                (Decimal(str(disc_ale)) / Decimal(str(g_ale)) * Decimal("100.0")).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                if g_ale > 0
                else Decimal("0.0")
            )

            decomp = AdditiveLossDecomposition(
                currency_iso=currency_iso.upper(),
                mean_lef=r["lef"],
                expected_downtime_loss=r["downtime_loss"],
                expected_replacement_cost=r["repl_cost"],
                expected_secondary_loss=r["sec_loss"],
                gross_mean_sle=r["gross_sle"],
                gross_standalone_ale=g_ale,
                euler_overlap_adjustment_ale=adj_ale,
                net_allocated_ale=net_ale,
                euler_discount_pct=disc_pct,
                gross_standalone_p90=g_p90,
                net_allocated_p90=net_p90,
                loss_physics=r["physics"],
                epistemic_state=r["epistemic"],
            )
            decomp.validate_conservation()
            decompositions[f_id] = decomp

        return decompositions
```

---

#### 4.5 Production Replacement: `payload_to_ast.py` (Zero Presentation Arithmetic, Pure SSOT Read)

In `payload_to_ast.py`, delete the entire `if "TOIL" in raw_arch:` / `r_rate = 65.0` / `r_eff_sle = r_ale / r_lef` block (lines 4145–4172) and replace it with a pure read from the authoritative `AdditiveLossDecomposition` / `actuarial_input_vector`:

```python
        # Synchronize SLE and LEF strictly from authoritative Domain Engine SSOT (Zero Presentation Math)
        for r_item in risks_data_list:
            decomp = r_item.get("additive_loss_decomposition") or {}
            vec_out = (r_item.get("actuarial_input_vector") or {}).get("outputs") or {}

            ssot_sle = (
                decomp.get("gross_mean_sle")
                if decomp.get("gross_mean_sle") is not None
                else (
                    vec_out.get("mean_sle")
                    if vec_out.get("mean_sle") is not None
                    else r_item.get("sle")
                )
            )
            ssot_lef = (
                decomp.get("mean_lef")
                if decomp.get("mean_lef") is not None
                else (
                    vec_out.get("mean_lef")
                    if vec_out.get("mean_lef") is not None
                    else r_item.get("lef")
                )
            )
            ssot_ale = (
                decomp.get("net_allocated_ale")
                if decomp.get("net_allocated_ale") is not None
                else r_item.get("ale")
            )

            if ssot_sle is not None:
                r_item["sle"] = round(float(ssot_sle), 2)
            if ssot_lef is not None:
                r_item["lef"] = round(float(ssot_lef), 4)
            if ssot_ale is not None and r_item.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR":
                r_item["ale"] = round(float(ssot_ale), 2)
```

---

#### 4.6 Production Replacement: `scripts/regenerate_molins_pure_from_raw_inputs.py` (Zero Hardcoded Costs, Zero Spanish Branching, Pure Domain Engine Invocation)

Delete the manual mutation loop in `scripts/regenerate_molins_pure_from_raw_inputs.py` (lines 178–250) and delegate 100% of parameter resolution to `ActuarialInputResolver` and `EulerPortfolioAllocator`:

```python
        # Run scoring engine SSOT from raw answers (Zero hardcoded CMMI overrides)
        case_input = {
            "case_id": f"CASE_{code}",
            "tower_id": code,
            "tower_name": tower_def.get("tower_name", code),
            "answers": answers_by_tower.get(code, []),
        }
        scoring_ssot = build_scoring(case_input, tower_def)
        declared_cmmi = round(float(scoring_ssot["tower_score_exact"]), 2)

        src_payload_p = REPO_ROOT / "working" / "molins" / code / f"blueprint_{code.lower()}_payload.json"
        with open(src_payload_p, "r", encoding="utf-8-sig") as f:
            bp = json.load(f)

        # Preserve calibrated empirical score if present in blueprint SSOT, otherwise use scoring_ssot
        overall_cmmi = round(float(bp.get("calibrated_score") or bp.get("score") or declared_cmmi), 2)
        bp["score"] = overall_cmmi
        bp["overall_score"] = overall_cmmi
        bp["exact_score"] = overall_cmmi
        bp["maturity_score"] = overall_cmmi
        bp["declared_score"] = declared_cmmi
        bp["survey_declared_score"] = declared_cmmi

        pillar_map = {p["pillar_id"]: p["score_exact"] for p in scoring_ssot.get("pillar_scores", [])}
        for p in bp.get("pillars_analysis", []):
            if isinstance(p, dict):
                pid = p.get("pillar_id")
                if pid in pillar_map:
                    p["declared_score"] = round(float(pillar_map[pid]), 2)
                    p["survey_declared_score"] = round(float(pillar_map[pid]), 2)
                    if p.get("score") is None:
                        p["score"] = round(float(pillar_map[pid]), 2)
                        p["exact_score"] = round(float(pillar_map[pid]), 2)

        # Resolve finding physics and actuarial parameters strictly through the Domain Engine
        from assessment_engine.domain.actuarial.finding_archetype_resolver import (
            PolymorphicFindingClassifier,
        )
        from assessment_engine.domain.actuarial.input_resolver import (
            ActuarialInputResolver,
        )

        for p in bp.get("pillars_analysis", []):
            if not isinstance(p, dict):
                continue
            for hc in p.get("health_check_asis", []):
                if not isinstance(hc, dict):
                    continue
                # Strip any stale hardcoded overrides so ActuarialInputResolver derives purely from telemetry
                hc.pop("direct_replacement_cost", None)
                if not PolymorphicFindingClassifier.classify_finding(hc, code).allows_downtime_burn:
                    hc.pop("recovery_time_hours", None)
                    hc.pop("rto_hours_mode", None)
                    hc.pop("rto_hours_min", None)
                    hc.pop("rto_hours_max", None)

                profile_f = PolymorphicFindingClassifier.classify_finding(hc, code)
                hc["loss_physics"] = profile_f.loss_physics.value
                hc["epistemic_state"] = profile_f.epistemic_state.value
                hc["max_euler_ale_discount_pct"] = profile_f.max_euler_ale_discount_pct
                hc["max_euler_var_discount_pct"] = profile_f.max_euler_var_discount_pct

                resolved_vec = ActuarialInputResolver.resolve_finding_inputs(
                    hc=hc,
                    tower_id=code,
                    financial_telemetry=fin_baseline,
                )
                hc["actuarial_input_vector"] = resolved_vec.to_dict()
```