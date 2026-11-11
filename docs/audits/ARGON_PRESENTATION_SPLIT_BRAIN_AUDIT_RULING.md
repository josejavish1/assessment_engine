### 1. Ground Truth Verification

The external audit is **100% technically accurate, verifiable against the physical AST of commit `41d4c2d`, and mathematically irrefutable**. The presentation and reporting layer (`adapters/` and `compilers/`) is actively operating as an unauthorized, deterministic shadow actuarial engine that overrides, mutates, and fabricates financial and maturity telemetry at render time.

Below is the forensic verification of every single finding cited by the auditors:

#### P0 #1: `derive_in_memory_fair_risks()` is a Second Actuarial Engine
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence (`in_memory_asis_compiler.py:532-735`):**
  * **Linear Pseudo-FAIR Math:** Lines 591–606 execute hardcoded deterministic formulas when canonical fields are absent:
    $$\text{deficit} = \max(0.1, 5.0 - \text{score})$$
    $$\text{TEF} = \max(0.1, \text{round}(\text{deficit} \times 0.8, 2))$$
    $$\text{LM} = \max(0.5, \text{round}(\text{deficit} \times 1.5, 2))$$
    $$\text{ALE} = \text{TEF} \times \text{LM} \times 1000.0$$
    $$\text{P90} = \text{ALE} \times 2.5$$
    This violates Open FAIR ontology (where $\text{LEF} = \text{TEF} \times \text{Vuln}$ and $\text{ALE} = \int \text{LEF} \cdot \text{SLE}$).
  * **Arbitrary LEF/SLE Clamping:** Lines 613–620 force $\text{LEF} = \min(0.50, \max(0.08, \text{TEF} \times 0.09))$ for $\text{TEF} \ge 1.0$, deriving $\text{SLE} = \text{ALE} / \text{LEF}$ or $\text{LM} \times 5000.0$.
  * **Unobserved Blindspot Fabrication:** Lines 671–730 catch empty `risks_data_list` states, instantiate `ActuarialInferenceEngine` inside the presentation compiler, inject an ungoverned `$100,000,000.0` annual revenue fallback, and synthesize 5 latent risks (`T*.P1` through `T*.P5`) with hardcoded $\text{TEF} = 2.5$ and $\text{LM} = 3.0$.
  * **Call-Graph Reachability:** Directly invoked by `asis_fair_chapter.py:591`, `tomo_asis_ast_compiler.py:478 & 1390`, and `payload_to_ast.py:3050`.

#### P0 #2: `payload_to_ast.py` Mutates Canonical Business Results
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence:**
  * **In-Flight Telemetry Mutation (1436–1451):** Imports and executes `ActuarialDowntimeCalibrator` during AST compilation, mutating `financial_telemetry` dicts in-place.
  * **Regex Narrative Score Recalibration (726–794):** Scans qualitative text strings via regex for negative keywords and overwrites numerical maturity scores (`score = min(score, 1.25)` or `1.50`), creating a divergence between the database record and the rendered document.
  * **Synthetic Score Imputation (1548–1570):** Imputes missing capability/pillar scores to `2.5` and writes back to `score`, `overall_score`, and `exact_score`.
  * **Pro-Rata ALE Normalization (3395–3411):** Calculates a scaling ratio to force the sum of individual scenario ALEs to match the header total, silently distorting standalone scenario expectations.
  * **Card-Level Re-Simulation (3765–3838, 3989–3999):** Instantiates `FairActuarialInput` inside the UI card builder, recalculates missing SLE as $\text{RTO} \times \text{hourly\_cost}$ (lines 3824–3827), and fabricates operational toil frequency via $\text{ALE} / \text{SLE}$ or $\text{TEF} \times 6$ (lines 3989–3999).

#### P0 #3: `tomo_asis_ast_compiler.py` Reconstructs the Portfolio
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence:**
  * **Top-Down Revenue Fallback (492–497):** Computes `corporate_ale = sum(tower_ales) if tower_ales else (annual_revenue * baseline_factor)` using `DEFAULT_BASELINE_RISK_FACTOR` ($0.001$).
  * **Linear Tail Fabrication (498–509):** Falls back to `corporate_ale * tail_multiplier` ($2.5\times$) when `total_fair_p90` is missing or zero.
  * **Horizon Extrapolation (511–513):** Computes 3-year expected exposure (`corporate_ale * 3`) and 3-year stress exposure (`(corporate_ale * 3) + (corporate_p90 * TAIL_STRESS_HORIZON_FACTOR)`).
  * **Uniform Standalone Allocation & Euler Execution (1438–1463):** When a tower's standalone ALE is missing or $\le 0$, line 1445 fabricates it via uniform division (`total_ale / len(domain_topology)`), then invokes `EulerPortfolioAllocator.allocate_portfolio()` inside the document compiler to generate Table 5.

#### P1 #4: `build_global_report_payload.py` Contains a Parallel Financial Model
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence (`build_global_report_payload.py:394-616`):**
  * Implements an autonomous 3-layer TCO/ROI financial model in the reporting adapter using ungoverned constants: `EUR`, `$100M` revenue, `$5,000/h` downtime cost, `$2M` regulatory fine, FinOps cash waste ratio (`annual_revenue * finops_waste_ratio`), `27h` baseline downtime, tail risk bounds (`0.45` to `0.65 * total_fair_ale`), `40%` OpEx ratio, `$250k` OpEx fallback, `6.0` months default payback, and `1.0x` default ROI.
  * Defines `annual_value_protected = layer_1_amount + layer_2_amount + layer_3_max` (summing cash waste, deterministic downtime, and $0.65 \times \text{ALE}$), which is actuarially invalid (summing expected values, deterministic operational budgets, and scaled loss metrics as equivalent cash savings).

#### P1 #5: `asis_fair_chapter.py` Fabricates P90, Max Loss, and Risk Tiers
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence (`asis_fair_chapter.py:64-67, 405-430, 629-630, 722, 759`):**
  * Defines module-level actuarial constants inside a Word chapter builder: `P90_ALE_MULTIPLIER_FALLBACK = 2.5`, `MAX_LOSS_P90_MULTIPLIER_FALLBACK = 1.5`, `TIER1_THRESHOLD_MULTIPLIER = 1.5`, and `TIER2_THRESHOLD_MULTIPLIER = 0.5`.
  * Dynamically computes P90 (`ale * 2.5`), Maximum Probable Loss (`p90 * 1.5`), and risk tiering thresholds relative to sample means during table rendering.

#### P1 #6: Ungoverned Heuristics and Fabricated Citations in `payload_to_ast.py`
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence:** Hardcodes 100% perimeter revenue share, injects unverified external benchmark citations (`"Gartner / ITIC Global Downtime Benchmark"`), applies a `40%` sector impact factor, sets target maturity to `score + 1.5`, uses `P90 = ALE * 2.2` (contradicting the `2.5` multiplier in `asis_fair_chapter.py` and `in_memory_asis_compiler.py`), sets recovery ceiling to `24h`, risk tiers at `15%` and `3%`, coupling factors (`1.5 / 1.2 / 1.0`), alpha weights (`0.70 / 0.40 / 0.20`), productivity rate (`$65/h`), and RTO fallback (`LM * 0.85` or `3.5h`).

#### P1 #7: Global Renderer Invents Positive Maturity ("Greenwashing")
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence (`adapters/render_global_report_from_template.py:1751-1757`):**
  * When a tower's bottom-line summary is incomplete or unassessed, the renderer defaults to `score = 4.0`, `band = "Managed"`, `status_color = "green"`. In an enterprise audit context, defaulting unassessed control environments to CMMI Level 4 (Managed) is a catastrophic misrepresentation of control posture.

#### P1 #8: Maturity Split-Brain Across Compilers
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence:** `in_memory_asis_compiler.py` (lines 1258–1272, 1354–1370, 1725–1728, 1874–1897) and `payload_to_ast.py` (lines 763–772) apply competing, non-identical text-heuristic ceilings (`1.25` vs `1.50` vs narrative token penalties) to mutate CMMI maturity scores independently.

#### P0 Tests: Test Suite Enforces the Anti-Pattern
* **Verdict:** **CONFIRMED (100% Truth).**
* **Forensic Evidence:**
  * `test_presentation_modules_do_not_calculate_financial_metrics_ast` uses a naive blocklist of 6 function names, allowing inline arithmetic (`tef_val * lm_val * 1000.0`), domain imports (`EulerPortfolioAllocator`), and class instantiations (`ActuarialInferenceEngine`) to pass undetected.
  * `test_rfc084_zero_ale_prohibition_gate.py` explicitly asserts that 9 towers with zero empirical findings *must* yield $\text{ALE} > \$100,000$. This test mathematically forces the codebase to retain the synthetic fallback engine in `in_memory_asis_compiler.py` to stay green.

---

### 2. Root Cause Analysis

#### Why Presentation Modules Contain Actuarial Engines and Multipliers
1. **Defensive Rendering Against Upstream Schema Fragility:** Historically, upstream LLM extraction pipelines and partial-scope assessments emitted incomplete JSON payloads (missing `fair_ale`, `sle`, `p90`, or `score`). Instead of enforcing a strict Domain Validation Gate prior to persistence, developers patched missing fields at the furthest downstream point—the DOCX AST compilers—to prevent `KeyError`, `NoneType` formatting crashes, or blank tables in client deliverables.
2. **Perverse Test Incentives (RFC-084 Gate):** The introduction of `test_rfc084_zero_ale_prohibition_gate.py` codified a flawed business requirement ("never show $0 ALE to a client, even when a tower has no findings"). Because the test was wired against the compiler output rather than the application orchestration layer, developers embedded `ActuarialInferenceEngine` and `ALE * 2.5` fallbacks directly inside `in_memory_asis_compiler.py` and `tomo_asis_ast_compiler.py`.
3. **Lack of a Canonical Read-Model (Presentation DTO):** Compilers accept untyped `dict[str, Any]` (`b_data`, `global_payload`). Because the schema is amorphous, each compiler (`payload_to_ast.py`, `tomo_asis_ast_compiler.py`, `in_memory_asis_compiler.py`, `build_global_report_payload.py`) implemented its own ad-hoc normalization, reconciliation, and fallback math.

#### Architectural & Regulatory Violations
* **Violation of Hexagonal / Clean Architecture:** In Clean Architecture, dependencies must point strictly inward (`Adapters -> Application -> Domain`). Currently, outer presentation adapters (`compilers/`) import domain services (`EulerPortfolioAllocator`, `ActuarialInferenceEngine`, `ActuarialDowntimeCalibrator`) and execute domain business logic during view rendering. Worse, they mutate the input dictionaries in-place, creating side effects that depend on chapter rendering execution order.
* **Violation of Separation of Concerns (CQRS / Read-Write Segregation):** A document compiler's sole responsibility is **syntactic projection**—mapping pre-computed, immutable domain values into typographic AST nodes (`ParagraphNode`, `TableNode`, formatted currency strings). By calculating $\text{ALE}$, $\text{P90}$, ROI, and CMMI caps, the view layer usurps the domain model.
* **Violation of Federal Reserve SR 11-7 (Model Risk Management):**
  * **Conceptual Soundness:** Multiplying $\text{ALE} \times 2.5$ (or $2.2$ in `payload_to_ast.py`) to obtain $\text{P90}$, and $\text{P90} \times 1.5$ for Max Loss, violates probability theory. In heavy-tailed lognormal/Pareto distributions typical of cyber/operational risk, the ratio $\text{VaR}_{0.90} / \mathbb{E}[L]$ is a function of the shape parameter $\sigma$ and frequency $\lambda$, never a static scalar constant.
  * **Single Source of Truth & Auditability:** When `payload_to_ast.py` uses $\text{P90} = 2.2 \times \text{ALE}$ on an executive card while `asis_fair_chapter.py` uses $\text{P90} = 2.5 \times \text{ALE}$ in the chapter table, the same deliverable exhibits internal numerical contradiction. Under SR 11-7, unvalidated shadow models embedded in reporting scripts constitute a **Severity 1 Model Governance Failure**.

---

### 3. Risks and Blast Radius of Proposed Remediation

#### What Will Break Across the 10 Tower DOCX Pipelines If Purged Naively
If we strip all math, fallbacks, and mutations from `adapters/` and `compilers/` without upstream compensation, the following pipeline failures will occur immediately:
1. **Partial-Scope / Zero-Finding Towers (Towers without `health_check_asis` entries):**
   * Without the `if not risks_data_list:` block in `derive_in_memory_fair_risks()`, towers with zero empirical findings will return an empty risk list `[]`.
   * Downstream chapters (`asis_fair_chapter.py`, `tomo_asis_ast_compiler.py` Table 5) that expect at least one risk scenario or positive standalone ALE will either render empty tables, divide by zero when computing portfolio shares (`s_ale / total_ale`), or fail `test_rfc084_zero_ale_prohibition_gate.py`.
2. **Legacy / Incomplete JSON Payloads Missing Pre-Computed Actuarial Fields:**
   * Saved assessment snapshots or test fixtures that only populate raw qualitative fields (`finding`, `score`) without running the full application-layer actuarial pipeline will lack `fair_ale`, `fair_p90_score`, `sle`, `lef`, and `euler_net_contribution`.
   * Passive compilers will render `"N/A"` or `"UNQUANTIFIED"` instead of synthetic currency strings, breaking snapshot tests that assert formatted currency presence on raw fixture inputs.
3. **Unassessed Maturity Nodes:**
   * Removing the `2.5` fallback in `payload_to_ast.py` and the `4.0 ("Managed")` fallback in `render_global_report_from_template.py` will expose `None` scores. Any sorting, radar chart plotting, or heatmap coloring logic that assumes `float` scores in `[1.0, 5.0]` will raise `TypeError: '<' not supported between instances of 'NoneType' and 'float'`.
4. **Portfolio Table 5 Reconciliation (`tomo_asis_ast_compiler.py`):**
   * If `EulerPortfolioAllocator` is removed from `tomo_asis_ast_compiler.py`, the compiler requires pre-allocated Euler decomposition rows inside the input payload. Payloads generated without running the portfolio aggregation use-case will lack `decomp.allocations`.

#### Canonical Presentation DTO Design (`application/dtos/presentation_dtos.py`)
To eliminate all calculations from the presentation layer while guaranteeing zero runtime crashes in the 10 tower pipelines, the **Application Layer** must assemble and validate frozen, strictly-typed Read-Model DTOs *before* invoking any compiler or renderer.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class EpistemicState(str, Enum):
    EMPIRICAL_OBSERVED = "EMPIRICAL_OBSERVED"
    LATENT_INFERRED = "LATENT_INFERRED"          # Explicitly governed Bayesian prior in Domain
    UNASSESSED_OUT_OF_SCOPE = "UNASSESSED_OUT_OF_SCOPE"
    INSUFFICIENT_TELEMETRY = "INSUFFICIENT_TELEMETRY"

class OwnershipType(str, Enum):
    PRIMARY_CUSTODIAN = "PRIMARY_CUSTODIAN"
    TANGENTIAL_CONTRIBUTOR = "TANGENTIAL_CONTRIBUTOR"

@dataclass(frozen=True)
class ProvenanceMetadataDTO:
    model_version: str
    calibration_source: str                      # e.g., "MonteCarlo_10k_LogNormal_v4.2"
    epistemic_state: EpistemicState
    assumptions_registry_id: str

@dataclass(frozen=True)
class PresentationFindingDTO:
    finding_id: str
    node_id: str
    pillar_id: str
    pillar_name: str
    capability_name: str
    finding_narrative: str
    business_risk_narrative: str
    ownership_type: OwnershipType
    primary_risk_ref: Optional[str]
    contributing_towers: tuple[str, ...]
    # Pre-computed, immutable CMMI maturity (None if unassessed)
    cmmi_score: Optional[float]
    target_cmmi_score: Optional[float]
    cmmi_band_label: str                         # e.g., "Level 2 - Repeatable" or "UNASSESSED"
    # Pre-computed, immutable Open FAIR metrics (None if unquantified)
    tef_annual: Optional[float]
    vulnerability_prob: Optional[float]
    lef_annual: Optional[float]
    sle_mean: Optional[float]
    ale_expected: Optional[float]
    p90_var: Optional[float]
    max_probable_loss: Optional[float]
    rto_hours: Optional[float]
    toil_frequency_annual: Optional[float]
    risk_tier_label: str                         # Pre-classified by Domain: "TIER_1", "TIER_2", "TIER_3", "UNQUANTIFIED"
    # Pre-formatted display strings (or presentation-ready localized tokens)
    ale_display: str
    p90_display: str
    sle_display: str
    provenance: ProvenanceMetadataDTO

@dataclass(frozen=True)
class PresentationPillarDTO:
    pillar_id: str
    pillar_name: str
    cmmi_score: Optional[float]
    cmmi_band_label: str
    status_color_token: str                      # "red", "amber", "green", "grey" (for unassessed)
    findings: tuple[PresentationFindingDTO, ...]

@dataclass(frozen=True)
class PresentationTowerDTO:
    tower_id: str
    tower_name: str
    currency_iso: str
    currency_symbol: str
    locale: str
    epistemic_state: EpistemicState
    overall_cmmi_score: Optional[float]
    overall_cmmi_band: str
    status_color_token: str                      # Never defaults to "green"; "grey" if None
    standalone_ale: Optional[float]
    standalone_p90: Optional[float]
    standalone_max_loss: Optional[float]
    euler_net_ale: Optional[float]
    diversification_adjustment: Optional[float]
    portfolio_share_pct: Optional[float]
    pillars: tuple[PresentationPillarDTO, ...]
    all_findings: tuple[PresentationFindingDTO, ...]
    provenance: ProvenanceMetadataDTO

@dataclass(frozen=True)
class ExecutiveFinancialBridgeDTO:
    """Replaces the shadow financial model in build_global_report_payload.py."""
    epistemic_state: EpistemicState
    annual_revenue: Optional[float]
    hourly_downtime_cost: Optional[float]
    finops_cash_waste_annual: Optional[float]
    operational_downtime_friction_annual: Optional[float]
    actuarial_tail_mitigated_min: Optional[float]
    actuarial_tail_mitigated_max: Optional[float]
    year_1_opex: Optional[float]
    total_capex: Optional[float]
    annual_value_protected: Optional[float]
    three_year_value_protected: Optional[float]
    payback_months: Optional[float]
    roi_ratio: Optional[float]
    provenance: ProvenanceMetadataDTO

@dataclass(frozen=True)
class PresentationPortfolioDTO:
    tenant_id: str
    currency_iso: str
    currency_symbol: str
    locale: str
    corporate_ale: Optional[float]
    corporate_p90: Optional[float]
    corporate_max_loss: Optional[float]
    var_3y_expected: Optional[float]
    var_3y_stress: Optional[float]
    towers: tuple[PresentationTowerDTO, ...]
    financial_bridge: ExecutiveFinancialBridgeDTO
    provenance: ProvenanceMetadataDTO
```

---

### 4. Concrete Implementation Strategy

#### Step-by-Step Architectural Blueprint

##### Phase 1: Consolidate All Actuarial & Maturity Logic into the Domain & Application Layers
1. **Create `AssessmentValuationOrchestrator` (`src/assessment_engine/application/services/assessment_valuation_orchestrator.py`):**
   * This application service is the **single entry point** that transforms raw assessment findings into `PresentationPortfolioDTO` and `PresentationTowerDTO`.
   * **Maturity Calibration:** Move all narrative-to-score validation rules out of `in_memory_asis_compiler.py` and `payload_to_ast.py` into a single domain service: `domain/maturity/cmmi_calibration_service.py`. Unassessed capabilities/towers receive `cmmi_score = None`, `cmmi_band_label = "UNASSESSED"`, `status_color_token = "grey"`.
   * **Scenario Valuation & Custody Resolution:** Run `DynamicCustodyResolver` and the canonical Open FAIR engine (`FairActuarialService` / `ActuarialDowntimeCalibrator`) inside `AssessmentValuationOrchestrator`. Tangential custody zeroing (`ownership == TANGENTIAL_CONTRIBUTOR -> calibrated_ale = 0.0`) occurs here and is persisted on the DTO.
   * **Epistemic State & Latent Priors Governance:**
     * If a tower has zero empirical findings, the Domain layer explicitly evaluates the tenant's policy configuration (`allow_bayesian_latent_priors: bool`).
     * When disabled (strict empirical mode), the tower DTO is marked `EpistemicState.INSUFFICIENT_TELEMETRY`, with `standalone_ale = None` (or `0.0` with explicit epistemic badge `"UNQUANTIFIED - NO EMPIRICAL EVIDENCE"`).
     * When enabled (governed prior mode), `ActuarialInferenceEngine` runs *exclusively in the Application/Domain layer*, tagging every generated scenario with `EpistemicState.LATENT_INFERRED` and full `ProvenanceMetadataDTO`.
   * **Portfolio Aggregation & Euler Allocation:** Run `EulerPortfolioAllocator.allocate_portfolio()` inside `AssessmentValuationOrchestrator` and populate `euler_net_ale`, `diversification_adjustment`, and `portfolio_share_pct` on each `PresentationTowerDTO`.
   * **Executive ROI / Financial Bridge:** Move the 3-layer ROI calculation out of `build_global_report_payload.py` into `domain/actuarial/executive_roi_calculator.py`. Require explicit governed parameters from `TenantActuarialProfile`; if inputs are missing, set the bridge state to `EpistemicState.INSUFFICIENT_TELEMETRY` and return `None` for derived ratios rather than fabricating `$250k` OpEx, `6-month` payback, or `1.0x` ROI.

##### Phase 2: Purge Compilers and Renderers (`adapters/` and `compilers/`)
1. **Refactor `in_memory_asis_compiler.py`:**
   * Delete `derive_in_memory_fair_risks()`'s math block (lines 591–625) and the `if not risks_data_list:` `ActuarialInferenceEngine` instantiation block (lines 671–730).
   * Replace `derive_in_memory_fair_risks()` with a pure projection function `map_tower_dto_to_risk_rows(tower_dto: PresentationTowerDTO)` that reads pre-computed fields from `PresentationFindingDTO`.
   * Delete all regex maturity score recalibrations (lines 1258–1272, 1354–1370, 1725–1728, 1874–1897).
2. **Refactor `payload_to_ast.py`:**
   * Enforce deep immutability at entry: convert input dictionaries via `types.MappingProxyType` recursive wrapper or accept only `PresentationTowerDTO`.
   * Delete all 16 actuarial/calibrator imports (`ActuarialDowntimeCalibrator`, `FairActuarialInput`, etc.).
   * Delete regex score mutations (lines 726–794), `2.5` score imputation (lines 1548–1570), pro-rata ALE scaling (lines 3395–3411), SLE/LEF derivations (lines 3311–3324, 3824–3827), card re-simulation (lines 3765–3838), toil frequency math (lines 3989–3999), and unverified `"Gartner / ITIC"` string literals.
3. **Refactor `tomo_asis_ast_compiler.py`:**
   * Remove `EulerPortfolioAllocator` and `resolve_iso_currency_code` imports.
   * Remove corporate ALE fallback (`annual_revenue * baseline_factor`), P90 fallback (`corporate_ale * tail_multiplier`), 3-year stress formulas, heatmap/equal-weight domain allocations (lines 821–857), and uniform standalone ALE division (`total_ale / len(domain_topology)`).
   * Render Table 5 directly by iterating over `portfolio_dto.towers`.
4. **Refactor `asis_fair_chapter.py`:**
   * Delete `P90_ALE_MULTIPLIER_FALLBACK`, `MAX_LOSS_P90_MULTIPLIER_FALLBACK`, `TIER1_THRESHOLD_MULTIPLIER`, and `TIER2_THRESHOLD_MULTIPLIER`.
   * Read `finding.p90_var`, `finding.max_probable_loss`, and `finding.risk_tier_label` directly from `PresentationFindingDTO`. If `None`, render localized `"UNQUANTIFIED"`.
5. **Refactor `render_global_report_from_template.py`:**
   * At lines 1751–1757, replace the fraudulent default (`score = 4.0, band = "Managed", status_color = "green"`) with (`score = None, band = t("status_unassessed"), status_color = "grey"`).

##### Phase 3: Remediate the Test Suite & Enforce AST Architectural Gates
1. **Repeal and Replace `test_rfc084_zero_ale_prohibition_gate.py`:**
   * Rename to `test_epistemic_integrity_and_prior_governance_gate.py`.
   * **Test Case A (Empirical Mode):** Given 9 towers with zero findings and `allow_bayesian_latent_priors=False`, assert that `standalone_ale is None` (or `0.0`), `epistemic_state == EpistemicState.INSUFFICIENT_TELEMETRY`, and the rendered AST explicitly displays an `"UNASSESSED / NO EMPIRICAL TELEMETRY"` warning banner—**never** fabricated positive currency.
   * **Test Case B (Governed Latent Mode):** Given `allow_bayesian_latent_priors=True` in the Application Orchestrator, assert that priors are generated *solely* by the Domain service before reaching the presentation layer, and that passing an empty `PresentationTowerDTO` directly to `in_memory_asis_compiler.py` produces **zero** synthetic risks.

2. **Implement the Hermetic AST Presentation Immunity Gate (`tests/architecture/test_presentation_hermetic_immunity_ast.py`):**
   Replace the weak 6-name check with a comprehensive Python `ast.NodeVisitor` gate scanning every `.py` file under `adapters/`, `compilers/`, and `presentation/`:

```python
import ast
from pathlib import Path
import pytest

PRESENTATION_DIRS = [
    Path("src/assessment_engine/adapters"),
    Path("src/assessment_engine/compilers"),
]

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "actuarial",
    "euler_allocator",
    "calibrator",
    "inference_engine",
    "fair_",
    "monte_carlo",
    "roi_calculator",
    "cmmi_calibration",
)

FORBIDDEN_BUSINESS_KEYS = {
    "score", "overall_score", "exact_score", "cmmi_score",
    "ale", "fair_ale", "fair_ale_score", "total_fair_ale", "corporate_ale",
    "p90", "fair_p90_score", "total_fair_p90", "corporate_p90",
    "sle", "lef", "tef", "lm", "threat_event_frequency", "loss_magnitude",
    "financial_telemetry", "annual_revenue", "payback_months", "roi_ratio",
}

LAYOUT_SAFE_VARIABLES = {
    "width", "height", "col_width", "row_height", "font_size", "margin",
    "padding", "space_before", "space_after", "indent", "idx", "i", "j",
    "count", "page", "line_height", "r_counter", "total_width",
}


class PresentationHermeticVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if any(f in alias.name.lower() for f in FORBIDDEN_IMPORT_SUBSTRINGS):
                self.violations.append(f"{self.filepath}:{node.lineno} Forbidden domain import '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = (node.module or "").lower()
        if any(f in module for f in FORBIDDEN_IMPORT_SUBSTRINGS):
            self.violations.append(f"{self.filepath}:{node.lineno} Forbidden domain import from '{node.module}'")
        for alias in node.names:
            if any(f in alias.name.lower() for f in FORBIDDEN_IMPORT_SUBSTRINGS):
                self.violations.append(f"{self.filepath}:{node.lineno} Forbidden symbol import '{alias.name}'")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Prohibit in-place dictionary mutation of business keys: d["score"] = ...
        if isinstance(node.ctx, ast.Store):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                if node.slice.value in FORBIDDEN_BUSINESS_KEYS:
                    self.violations.append(
                        f"{self.filepath}:{node.lineno} Direct mutation of business key ['{node.slice.value}']"
                    )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Prohibit dict.update() / dict.setdefault() on business keys
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"setdefault", "update"}:
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in FORBIDDEN_BUSINESS_KEYS:
                self.violations.append(
                    f"{self.filepath}:{node.lineno} Mutation via .{node.func.attr}('{node.args[0].value}')"
                )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Prohibit arithmetic (*, /, +, -) assigned to any business/actuarial variable name
        if self._contains_arithmetic(node.value):
            for target in node.targets:
                target_names = self._extract_target_names(target)
                for name in target_names:
                    if not any(safe in name.lower() for safe in LAYOUT_SAFE_VARIABLES):
                        if any(bk in name.lower() for bk in FORBIDDEN_BUSINESS_KEYS) or "var_" in name.lower() or "layer_" in name.lower():
                            self.violations.append(
                                f"{self.filepath}:{node.lineno} Forbidden business arithmetic assigned to '{name}'"
                            )
        self.generic_visit(node)

    def _contains_arithmetic(self, node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.Mult, ast.Div, ast.FloorDiv, ast.Sub, ast.Pow)):
                return True
        return False

    def _extract_target_names(self, target: ast.AST) -> list[str]:
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, ast.Attribute):
            return [target.attr]
        if isinstance(target, (ast.Tuple, ast.List)):
            names = []
            for elt in target.elts:
                names.extend(self._extract_target_names(elt))
            return names
        return []
```

3. **Runtime Immutability & Identity Contract Test (`tests/architecture/test_compiler_read_only_contract.py`):**
   * Deep-freeze input payloads (`copy.deepcopy(payload)` before and after compilation) and assert `assert payload_before == payload_after` across every compiler entrypoint (`compile_payload_to_ast`, `compile_tomo_asis_ast`, `build_global_report_payload`).
   * Assert **exact numerical equality** between `PresentationPortfolioDTO` fields and every rendered table cell in the output AST—proving zero re-scaling, zero fallback multiplication, and zero split-brain divergence.