# ARCHITECTURAL & ACTUARIAL AUDIT REPORT
**Auditor:** `gemini-4-argon` (Supreme Enterprise Architect & Chief Actuarial Examiner)  
**Date:** November 2026  
**Verdict:** **REJECTED — SEVERE ARCHITECTURAL ANTIPATTERN & ACTUARIAL INTEGRITY VIOLATIONS DETECTED**

---

## EXECUTIVE SUMMARY

The user’s adversarial challenge is **100% valid, mathematically sound, and architecturally indisputable**. 

What has been committed in `finding_physics_lexicon.json` and `finding_archetype_resolver.py` is a textbook **1990s brittle regex-whack-a-mole antipattern** disguised as a domain classifier. Attempting to classify enterprise loss physics across global industries and languages by writing negative lookbehinds in Spanish (`(?<!no\sprovoca\suna\s)parada\s+de\s+f[aá]brica`) and hardcoding currency symbols (`\u20ac`) inside a taxonomy file is an embarrassment to Tier-1 November 2026 AI Systems Engineering.

Furthermore, the uncommitted diff in `canonical_risk_orchestrator.py` introduces a **fatal mathematical bug** (mixing a probability distribution's **Mode** with stochastic **Means**), which will deterministically crash `AdditiveLossDecomposition.validate_conservation()` or corrupt the presentation layer.

Below is the uncompromising audit across all four mandated dimensions, followed by the exact SOTA remediation blueprint.

---

## 1. THE `finding_physics_lexicon.json` & REGEX ANTIPATTERN

### 1.1 Critique of the Current Implementation
In `engine_config/taxonomy/finding_physics_lexicon.json` and `finding_archetype_resolver.py`, the system attempts to infer the actuarial physics of a finding (`FindingLossPhysics`) by running regexes over natural language prose (`combined_corpus`) downstream in the domain layer.

**Why this is a catastrophic antipattern:**
1. **The Negation & Context Fallacy (NLP 101 Failure):** The diff literally contains `(?<!no\sprovoca\suna\s)parada\s+de\s+f[aá]brica`. Evidently, an upstream text stated *"este fallo en el clúster HA no provoca una parada de fábrica"*, the regex matched *"parada de fábrica"*, misclassified an HA failover as a catastrophic plant shutdown, and the developer patched it with a Spanish negative lookbehind! What if the next report says *"no ocasiona una parada de fábrica"*, *"evita la parada de planta"*, or is written in Japanese, Arabic, or Polish? Regexes cannot parse syntax trees, negation scope, or counterfactuals.
2. **Domain & Scale Parochialism:** Words like `"parada de planta"`, `"corte de fibra"`, `"ambos cpds"`, `"windows autopilot"`, and `"broadcom|vmware"` overfit to a specific industrial/manufacturing client with on-prem data centers. A $500B Tier-1 global investment bank, a SaaS unicorn, or a hospital network has completely different failure modes (e.g., *FIX engine sequence desync, BGP route leak, HL7 FHIR API throttling, Kubernetes etcd quorum loss*).
3. **Priority Cascade Fragility:** In `PolymorphicFindingClassifier`, if `has_catastrophic_outage` is triggered by a single false-positive substring anywhere in the text, it bypasses `PLATFORM_DEGRADATION` and `ASSET_OBSOLESCENCE` entirely, defaulting the finding to a massive `AVAILABILITY_OUTAGE`.

### 1.2 How November 2026 Tier-1 Architectures Solve This
In November 2026, **no Tier-1 system uses regexes over presentation text to deduce domain types.** Natural language is a *rendering artifact* or an *unstructured ingestion source*—never the medium of internal domain state communication.

When an LLM synthesizes or ingests a finding (`HealthCheckAsIs`), the LLM already possesses full cross-lingual, multi-vertical semantic comprehension of the context, negations, and technical mechanics. Forcing the LLM to emit untyped prose, only to have a downstream Python script guess what the LLM meant using regex word lists, is **architectural schizophrenia**.

**The True SOTA Pattern (Upstream Structured Generation & Deterministic Parameter Contracts):**
1. **Constrained Structured Outputs at Ingestion/Synthesis:** The Pydantic schema (`HealthCheckAsIs` in `blueprint.py`) must mandate an explicit, strongly-typed `loss_physics: FindingLossPhysics` enum and an explicit `actuarial_Vector` (or normalized 0.0–1.0 severity/blast-radius coordinates) generated *at the moment the finding is structured* via Constrained Decoding (JSON Schema / Pydantic v2).
2. **Taxonomy-Anchored Priors:** Every node in the universal assessment taxonomy (`node_id` / capability pillar) carries an intrinsic default `FindingLossPhysics` prior and permissible physics bounds in the language-agnostic `archetype_registry`.
3. **Zero-Text Actuarial Engine:** The Python actuarial engine (`PolymorphicFindingClassifier` / `CanonicalRiskOrchestrator`) operates **100% on typed enums and numerical vectors**. It never reads `title`, `description`, or `evidence` strings. Whether the prose is in Spanish, Mandarin, or Swahili is completely invisible to the math engine.

---

## 2. CODE QUALITY, HARDCODING & LINGUISTIC PURITY AUDIT

### 2.1 Violations Found in Evidence
1. **Spanish & Portuguese Hardcoded in Engine Taxonomy (`finding_physics_lexicon.json`):**
   - Contains Spanish (`parada de fábrica`, `saturación de ram`, `cuello de botella`), Portuguese (`indisponibilidade crítica`, `tarefas manuais`), German, French, and Italian regexes.
   - **Rule Violation:** Engine configuration and taxonomy logic must be 100% language-agnostic. Only `locales.json` is permitted to hold natural language translations for deliverable rendering.
2. **Hardcoded Currency & Vendor Names (`finding_physics_lexicon.json`):**
   - Line 18: `"absorbe\\s+m[aá]s\\s+de\\s+[\\d.,]+\\s*\u20ac\\s+de\\s+opex"` — Hardcodes the Euro symbol (`€` / `\u20ac`) and a specific sentence structure from a single client assessment.
   - Line 15: `"licenciamiento.*(?:broadcom|vmware|oracle|microsoft)"` — Hardcodes specific software vendors.
   - Line 27: `"windows\\s+autopilot"` — Hardcodes a specific Microsoft endpoint tool.
3. **Hardcoded Regulatory Reference in `locales.json`:**
   - Line 677 (`locales.json`): Hardcodes `"bajo NIS2 (CVaR P99)"` in a static string, whereas Line 750 properly uses `{reg_name}` and `{reg_fine_limit}`. Static strings in `locales.json` must use dynamic template variables (`{reg_name}`) so a US Healthcare client sees `HIPAA`, a US Financial client sees `SEC/SOX`, and an EU entity sees `NIS2/DORA`.
4. **Hexagonal Architecture Violation in `finding_archetype_resolver.py`:**
   - `_get_external_physics_lexicon()` performs hidden, lazy filesystem I/O (`Path(__file__).resolve()...`) inside the **Domain Layer** (`src/assessment_engine/domain/actuarial/`). Domain services must be pure functions with zero filesystem awareness.
5. **Untyped Dict Soup in `blueprint.py`:**
   - Adding `additive_loss_decomposition: Optional[dict[str, Any]]` and `actuarial_input_vector: Optional[dict[str, Any]]` to `HealthCheckAsIs` violates strict typing. These must be strongly typed Pydantic models (`AdditiveLossDecompositionModel`, `ActuarialInputVectorModel`), not `dict[str, Any]`.

---

## 3. ACTUARIAL CREDIBILITY & LOSS DERIVATION AUDIT

### 3.1 CRITICAL BUG: Mode vs. Mean Conservation Failure (`canonical_risk_orchestrator.py`)
Look at lines 402–419 of the uncommitted diff in `canonical_risk_orchestrator.py`:
```python
rto_mode = float(inputs_dump.get("rto_hours_mode", {}).get("effective_value", 0.0))
hourly_rate = float(inputs_dump.get("hourly_burn_rate", {}).get("effective_value", 0.0))
alpha = float(inputs_dump.get("blast_radius_alpha", {}).get("effective_value", 1.0))
repl_cost = float(inputs_dump.get("direct_replacement_cost", {}).get("effective_value", 0.0))
sec_loss = float(inputs_dump.get("secondary_loss_mean", {}).get("effective_value", 0.0))
expected_downtime = rto_mode * hourly_rate * alpha
```
And then compare this against `AdditiveLossDecomposition.validate_conservation()`:
```python
sle_sum = (
    self.expected_downtime_loss
    + self.expected_replacement_cost
    + self.expected_secondary_loss
)
if sle_sum != self.gross_mean_sle:
    raise ValueError("SLE Additive Conservation Violation...")
```
**Why this is mathematically broken:**
1. **Mode $\neq$ Mean in Skewed PERT/Lognormal Distributions:** In a PERT distribution for RTO ($RTO_{min}, RTO_{mode}, RTO_{max}$), the expected value (mean) is $\mu_{RTO} = \frac{RTO_{min} + 4 \cdot RTO_{mode} + RTO_{max}}{6}$. Because outage durations are right-skewed ($RTO_{max} \gg RTO_{mode}$), $\mu_{RTO} > RTO_{mode}$.
2. **Expectation of Product vs. Product of Modes:** The Monte Carlo simulation calculates `f_res.mean_sle` across 10,000 stochastic trials using the **full PERT/Lognormal distributions** (incorporating tail skewness and secondary loss trigger probabilities). Computing `rto_mode * hourly_rate * alpha` outside the kernel yields the *modal* deterministic downtime, NOT the *expected (mean)* downtime!
3. **Guaranteed Mismatch / Plugging:** Consequently, `expected_downtime + repl_cost + sec_loss` will **never** equal `f_res.mean_sle` for any skewed distribution! And look at `payload_to_ast.py` line 4609:
   `stochastic_tail_adj = int(round(float(decomp.get("stochastic_pert_adjustment", 0))))`
   This reveals that someone previously invented a fudge factor (`stochastic_pert_adjustment`) or is letting the presentation layer show three numbers that do not add up to the SLE!

**The Actuarial Fix:**
By **Linearity of Expectation**, for any random variables $D$ (Downtime Loss), $R$ (Replacement Cost), and $S$ (Secondary Loss) simulated across $N$ Monte Carlo trials where $SLE_i = D_i + R_i + S_i$:
$$\mathbb{E}[SLE] = \mathbb{E}[D] + \mathbb{E}[R] + \mathbb{E}[S]$$
The Monte Carlo simulation kernel (`f_res`) **must** directly output the sample means of the three vectors from the actual simulation trials (`f_res.mean_downtime_loss`, `f_res.mean_replacement_cost`, `f_res.mean_secondary_loss`), with exact largest-remainder integer rounding applied once so that `int(D) + int(R) + int(S) == int(SLE)` holds identically without any "stochastic tail adjustment" plug!

### 3.2 Loss Physics Calibration Critique (`PLATFORM_DEGRADATION` vs. `TOIL` vs. `OUTAGE`)
1. **`PLATFORM_DEGRADATION` Mis-mapping:**
   - In `FindingLossPhysics.to_canonical_archetype()`, `PLATFORM_DEGRADATION` is mapped to `LossArchetypeType.AVAILABILITY_OUTAGE`.
   - Furthermore, its `PhysicsDefaultSpec` sets `default_rto_hours=0.5` and `default_blast_radius_factor=0.10`.
   - **Critique:** If a $500B enterprise has a Hourly Revenue Burn Rate of $50M/hour, a `0.10` blast radius with `0.5h` RTO still asserts that a minor RAM saturation or HA node failover burns **$2.5M in top-line revenue per event**! An HA cluster failover (`activo-pasivo` / `node failover`) is designed specifically so that **revenue downtime is ~0**, incurring only minor engineering intervention cost (`direct_replacement_cost` / incident response labor) or localized transaction retry latency (`blast_radius_factor` $\le 0.005$ to $0.02$).
2. **Governance & Productivity Toil (`ENGINEERING_VELOCITY_FRICTION`):**
   - Missing a service catalog, lacking cloud tags, or manual VM provisioning must strictly enforce `allows_downtime_burn = False` (`expected_downtime_loss = 0`).
   - If `expected_downtime_loss == 0` and `expected_secondary_loss == 0`, then `expected_replacement_cost` (which represents **Operational Toil / Remediation Labor / Resource Waste** for non-outage archetypes) **MUST equal 100% of `gross_mean_sle`**.
   - If the presentation layer fails to populate `expected_replacement_cost` with the toil/opex loss, the UI Risk Card renders the absurd napkin math: `0 (Downtime) + 0 (Replacement) + 0 (Secondary) = €50,000 SLE`.

---

## 4. ACTIONABLE REMEDIATION SPECIFICATION (THE SOTA BLUEPRINT)

Execute the following 4-step architectural refactoring immediately. No workarounds, no regexes.

### Step 1: Delete the Regex Lexicon & Purge `_PATTERNS`
1. **DELETE FILE:** `git rm engine_config/taxonomy/finding_physics_lexicon.json`
2. **PURGE FROM `finding_archetype_resolver.py`:**
   - Delete `_REGISTERED_PHYSICS_LEXICON`, `register_physics_lexicon()`, and `_get_external_physics_lexicon()`.
   - Delete `_BOILERPLATE_PATTERNS`, `_FINOPS_WASTE_PATTERNS`, `_ENGINEERING_FRICTION_PATTERNS`, `_OBSOLESCENCE_EOL_PATTERNS`, `_REGULATORY_BREACH_PATTERNS`, `_PLATFORM_DEGRADATION_PATTERNS`, `_CATASTROPHIC_OUTAGE_PATTERNS`, and `_matches_category()`.

### Step 2: Enforce Upstream Typed Contracts in `blueprint.py`
Update `HealthCheckAsIs` in `src/assessment_engine/domain/schemas/blueprint.py` so that the LLM / Ingestion compiler emits the structured physics and epistemic classification directly via Pydantic schema enforcement:

```python
class ActuarialClassificationSpec(BaseModel):
    """Language-agnostic, LLM-emitted or taxonomy-derived actuarial physics contract."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    loss_physics: FindingLossPhysics = Field(
        ...,
        description=(
            "Strict physical loss mechanism: "
            "AVAILABILITY_OUTAGE ( strictly for unmitigated SPOFs causing total service/plant halt), "
            "PLATFORM_DEGRADATION (HA failover, resource contention, latency without total outage), "
            "FINOPS_RESOURCE_WASTE (idle cloud/licensing OpEx waste, 0h downtime), "
            "ENGINEERING_VELOCITY_FRICTION (manual toil, missing IaC/catalog/tagging, 0h downtime), "
            "REGULATORY_AND_BREACH (data exposure, compliance/audit gap, 0h downtime), "
            "ASSET_OBSOLESCENCE_AND_INTEGRITY (EoL tech debt, unsupported versions)."
        ),
    )
    epistemic_state: EpistemicEvidenceState = Field(
        default=EpistemicEvidenceState.VERIFIED_EMPIRICAL,
        description="Provenance of evidence backing this finding.",
    )
    scoped_blast_radius_factor: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fraction of enterprise value stream impacted (0.0 to 1.0).",
    )
```
Add `loss_physics: Optional[FindingLossPhysics] = None` and `epistemic_state: Optional[EpistemicEvidenceState] = None` as first-class typed fields on `HealthCheckAsIs`, and replace `dict[str, Any]` with strongly-typed Pydantic models for `additive_loss_decomposition` and `actuarial_input_vector`.

### Step 3: Refactor `PolymorphicFindingClassifier` into a Pure Deterministic Resolver
In `src/assessment_engine/domain/actuarial/finding_archetype_resolver.py`, replace the regex matching cascade with deterministic resolution:
1. **Primary Resolution:** Read `hc.loss_physics` (or `hc.get("loss_physics")`) directly as a validated `FindingLossPhysics` enum.
2. **Secondary Resolution (Taxonomy Prior Fallback):** If `loss_physics` is not explicitly provided on an older payload, resolve it deterministically from the **Capability Taxonomy Registry** (`taxonomy_node_id -> default_loss_physics`), where FinOps pillars map to `FINOPS_RESOURCE_WASTE`, Governance/Automation pillars map to `ENGINEERING_VELOCITY_FRICTION`, Security/Compliance pillars map to `REGULATORY_AND_BREACH`, and HA/Compute pillars map to `PLATFORM_DEGRADATION` unless `severity == CRITICAL` and `control_maturity <= 1` (SPOF).
3. **Recalibrate `PLATFORM_DEGRADATION` Physics:**
   ```python
   FindingLossPhysics.PLATFORM_DEGRADATION: PhysicsDefaultSpec(
       allows_downtime_burn=True,
       allows_secondary_regulatory_fallout=False,
       default_rto_hours=0.25,          # 15-min automated/semi-automated failover window
       default_blast_radius_factor=0.02, # Scoped micro-degradation (2% vs 10%)
       max_euler_ale_discount_pct=0.15,
       max_euler_var_discount_pct=0.20,
   ),
   ```

### Step 4: Fix the SLE / ALE Additive Conservation Math in `CanonicalRiskOrchestrator` & Simulation Kernel
1. **Extract Component Means Directly from the Simulation Result (`f_res`):**
   Never recompute `expected_downtime = rto_mode * hourly_rate * alpha` outside the kernel. Ensure the Monte Carlo / Actuarial evaluator returns the exact expected component values (`f_res.expected_downtime_loss`, `f_res.expected_replacement_cost`, `f_res.expected_secondary_loss`) whose sum is mathematically guaranteed to equal `f_res.mean_sle`:
   $$\text{SLE}_{\text{mean}} = \mathbb{E}[\text{Downtime}] + \mathbb{E}[\text{Replacement/Toil}] + \mathbb{E}[\text{Secondary}]$$
2. **Enforce Zero-Downtime Conservation for Non-Outage Archetypes:**
   When `allows_downtime_burn is False` (`FINOPS_RESOURCE_WASTE`, `ENGINEERING_VELOCITY_FRICTION`, `REGULATORY_AND_BREACH`), `expected_downtime_loss` is strictly `0`. All primary operational toil, remediation labor, or resource waste **must** be mapped to `expected_replacement_cost` (or primary operational loss component) so that:
   `0 + expected_replacement_cost + expected_secondary_loss == gross_mean_sle`
   Always call `AdditiveLossDecomposition.validate_conservation()` inside `CanonicalRiskOrchestrator` before emitting the payload to `payload_to_ast.py`, and remove the `stochastic_pert_adjustment` fudge factor from `payload_to_ast.py`.
3. **Parameterize `locales.json`:**
   Replace the hardcoded `"NIS2"` on line 677 of `locales.json` with `{reg_name}` to preserve 100% jurisdictional neutrality across all enterprises globally.