---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
---
document_id: ARCH-PLAN-2026-FFES-GPE
title: "Architectural Execution Plan: Fact-First Executive Synthesis & Granular Progression Engine"
author: "gemini-4-argon (Distinguished Staff Architect / Lead Enterprise Ontologist)"
status: "APPROVED FOR EXECUTION"
version: "2.0.0"
classification: "STRICTLY CONFIDENTIAL // CORE ENGINE ARCHITECTURE"
target_modules:
  - "src/compilers/in_memory_asis_compiler.py"
  - "src/config/locales.json"
  - "src/config/cmmi_progression_matrix.json"
---

# 1. Executive Architectural Assessment

To elevate our automated assessment engine from a deterministic text assembler to an undisputed Tier-1 Principal Advisory platform, we must eradicate the three identified structural antipatterns. The current implementation suffers from **Context-Free String Slicing** (resulting in broken anaphoric references), **Meta-Narrative Bloat** (opening paragraphs by discussing the survey process rather than the architectural reality), and **Ontological Imprecision** (applying macro-tower remediation paths to micro-domain capabilities).

This execution plan establishes a universal, scale-invariant, and 100% localized architecture that enforces linguistic integrity and domain-specific precision across all 50 enterprise capabilities.

---

# 2. Core Architectural Paradigms

## 2.1. Anaphora Resolution Guard (Syntactic Subject Anchor Engine)

When the AST compiler extracts clauses from free-text findings to synthesize the baseline state or primary risk, splitting naively by sentence boundaries (`.`) frequently yields orphaned clauses. In linguistics, an *anaphora* is an expression whose interpretation depends upon another expression in context (its antecedent). If a synthesized block opens with *"This generates latency..."* or *"Unlike the secondary node..."*, the antecedent is missing, destroying executive credibility.

### Algorithmic Resolution Strategy
We will implement a deterministic **Syntactic Subject Anchor Guard** (`_enforce_syntactic_anchor`) within the text sanitation pipeline. 
1. **Locale-Driven Tokenization**: `locales.json` will house a strict array of `anaphoric_and_orphan_prefixes` (e.g., `"This "`, `"These "`, `"That "`, `"Those "`, `"It "`, `"However"`, `"Therefore"`, `"Unlike"`, `"Consequently"`, `"Additionally"`, and their exact localized equivalents in target languages).
2. **Iterative Clause Scanning**: When extracting a target sentence from a multi-sentence block:
   * The raw string is split into candidate sentences using a regex boundary that respects abbreviations: `(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s+`.
   * The engine evaluates Sentence $S_0$. It strips leading punctuation/whitespace and performs a case-insensitive prefix match against `anaphoric_and_orphan_prefixes`.
   * **Discard & Shift**: If $S_0$ triggers a match, it is classified as an *Orphaned Anaphoric Clause* and discarded. The pointer shifts to $S_1$, repeating the evaluation until a sentence with an independent syntactic subject is found.
3. **Graceful Degradation (Zero-Defect Fallback)**: If all candidate sentences in the raw input are flagged as orphaned (or if the resulting string falls below a minimum lexical threshold of 15 characters), the method aborts raw extraction and returns a deterministic, localized fallback constant (`fallback_baseline_clause` or `fallback_risk_clause`) interpolated with the specific Pillar Name.

```text
[Raw Text Block] 
       │
       ▼
[Regex Sentence Boundary Split] ──► [S_0, S_1, ... S_n]
       │
       ▼
[Evaluate S_i against `locales.anaphoric_prefixes`]
       │
       ├──► Match Found (Orphaned) ──► Discard S_i ──► Increment i (Loop)
       │
       ├──► Clean Subject Anchor   ──► Return S_i (Formatted)
       │
       └──► Exhausted Array        ──► Return `locales.fallback_clause`
```

---

## 2.2. Fact-First Dynamic Templates (Anti-Boilerplate Engine)

Tier-1 human consultants do not open executive cards by congratulating the client on filling out a survey correctly (*"The initial self-assessment and technical diagnostic fully align..."*). They open with **Operational Reality**. Survey divergence is only relevant when a dangerous cognitive blind spot exists (Overestimation) or when undocumented operational maturity is discovered (Underestimation).

### Refactoring `_build_diagnostic_rationale`
We will decouple the **Divergence Alert** from the **Core Diagnostic Narrative**.
1. **Delta Calculation**: Let $\Delta = \text{Score}_{\text{self}} - \text{Score}_{\text{calibrated}}$.
2. **Threshold Evaluation**:
   * **Aligned State ($|\Delta| < 1.0$)**: The divergence prefix is completely suppressed (`""`). The narrative opens 100% Fact-First, immediately stating the operational maturity state, the verified baseline architecture, and the structural resilience gap.
   * **Optimism Bias / Blind Spot ($\Delta \ge 1.0$)**: Prepends a sharp, executive `divergence_overestimated_prefix` highlighting the operational risk of unverified assumptions, followed immediately by the Fact-First core narrative.
   * **Conservative Baseline ($\Delta \le -1.0$)**: Prepends a `divergence_underestimated_prefix` noting that tactical controls exceed formal documentation, followed by the Fact-First core narrative.
3. **Dynamic Lexical Variation**: To prevent consecutive aligned pillars from reading identically, the Fact-First core template in `locales.json` will be bifurcated by maturity tier (`tier_low_fact_template`, `tier_mid_fact_template`, `tier_high_fact_template`), ensuring dynamic structural pacing across the 50 cards.

---

## 2.3. 50-Pillar Granular Ontology (`cmmi_progression_matrix.json`)

Mapping remediation milestones at the 10-Tower macro level causes severe domain bleed (e.g., recommending UPS battery bank topologies inside a Precision HVAC pillar). We must refactor `cmmi_progression_matrix.json` from a 10-key dictionary into a **50-Key Canonical Capability Ontology**, with a hierarchical fallback mechanism.

### Schema Architecture
The JSON schema will transition to an explicit `pillar_archetypes` map indexed by universal, immutable canonical IDs (`T{1..10}_P{1..5}_{DOMAIN_CODE}`), backed by `tower_fallbacks` to guarantee 100% scale-invariance and zero `KeyError` exceptions if custom or legacy pillars are injected.

```json
{
  "$schema": "https://enterprise-architecture.internal/schemas/cmmi-matrix-v2.json",
  "version": "2.0.0",
  "pillar_archetypes": {
    "T1_P1_POWER": {
      "domain_label": "Electrical Power & Distribution",
      "levels": {
        "1": { "state": "...", "milestone": "..." },
        "2": { "state": "...", "milestone": "Implement N+1 UPS topology and automated ATS failover." },
        "3": { "state": "...", "milestone": "Establish dual-bus (2N) active-active power feeds with independent utility substations." },
        "4": { "state": "...", "milestone": "Deploy continuous telemetry, harmonic distortion monitoring, and automated load-shedding." },
        "5": { "state": "...", "milestone": "Achieve autonomous microgrid islanding and AI-driven predictive capacitor/battery lifecycle management." }
      }
    },
    "T1_P2_HVAC": {
      "domain_label": "Precision Cooling & Environmental Control",
      "levels": {
        "1": { "state": "...", "milestone": "..." },
        "2": { "state": "...", "milestone": "Transition from comfort cooling to dedicated CRAC/CRAH units with N+1 redundancy." },
        "3": { "state": "...", "milestone": "Implement hot/cold aisle containment and dual-loop chilled water piping without single points of failure." },
        "4": { "state": "...", "milestone": "Integrate CFD (Computational Fluid Dynamics) thermal modeling and automated variable-speed airflow modulation." },
        "5": { "state": "...", "milestone": "Deploy AI-driven autonomous thermal optimization linked directly to workload orchestrators." }
      }
    },
    "T6_P2_PAM": {
      "domain_label": "Privileged Access Management (PAM)",
      "levels": {
        "1": { "state": "...", "milestone": "..." },
        "2": { "state": "...", "milestone": "Eliminate shared administrative credentials and deploy a centralized password vault." },
        "3": { "state": "...", "milestone": "Enforce mandatory session recording, MFA for all privileged elevation, and automated credential rotation." },
        "4": { "state": "...", "milestone": "Implement Just-In-Time (JIT) ephemeral privilege elevation and Zero Standing Privileges (ZSP)." },
        "5": { "state": "...", "milestone": "Continuous behavioral biometrics on active privileged sessions with automated anomaly termination." }
      }
    }
  },
  "tower_fallbacks": {
    "T1_FACILITIES": { "levels": { "1": {}, "2": {}, "3": {}, "4": {}, "5": {} } }
  },
  "universal_default": { "levels": { "1": {}, "2": {}, "3": {}, "4": {}, "5": {} } }
}
```

### Canonical 50-Pillar Taxonomy Matrix
The ontology will encode all 50 archetypes across the 10 Enterprise Towers:
* **T1 (Facilities)**: `T1_P1_POWER`, `T1_P2_HVAC`, `T1_P3_FIRE_PHYS`, `T1_P4_CABLING`, `T1_P5_DCIM`
* **T2 (Compute & Hardware)**: `T2_P1_SERVER_ARCH`, `T2_P2_STORAGE_SAN`, `T2_P3_VIRT_HYPERVISOR`, `T2_P4_FIRMWARE_LIFECYCLE`, `T2_P5_CAPACITY_HW`
* **T3 (Network & Connectivity)**: `T3_P1_WAN_SDWAN`, `T3_P2_LAN_CORE`, `T3_P3_DNS_IPAM_DDI`, `T3_P4_LOAD_BALANCING`, `T3_P5_NET_TELEMETRY`
* **T4 (Cloud & Hybrid Platforms)**: `T4_P1_LANDING_ZONE`, `T4_P2_IAC_AUTOMATION`, `T4_P3_CONTAINERS_K8S`, `T4_P4_FINOPS_COST`, `T4_P5_MULTI_CLOUD_GOV`
* **T5 (Data & Databases)**: `T5_P1_RDBMS_HA`, `T5_P2_NOSQL_CACHING`, `T5_P3_DATA_PIPELINE_ETL`, `T5_P4_DATA_GOV_CATALOG`, `T5_P5_ANALYTICS_BI`
* **T6 (Cybersecurity & IAM)**: `T6_P1_IAM_CORE`, `T6_P2_PAM`, `T6_P3_PERIMETER_ZTNA`, `T6_P4_EDR_XDR_SOC`, `T6_P5_VULN_SECOPS`
* **T7 (Application Architecture)**: `T7_P1_APP_MODULARITY`, `T7_P2_API_GATEWAY_MESH`, `T7_P3_CICD_DEVOPS`, `T7_P4_CODE_QUALITY_SAST`, `T7_P5_LEGACY_MODERNIZATION`
* **T8 (Resilience & Continuity)**: `T8_P1_BACKUP_IMMUTABILITY`, `T8_P2_DR_ORCHESTRATION`, `T8_P3_HA_CLUSTERING`, `T8_P4_CHAOS_DR_TESTING`, `T8_P5_RTO_RPO_GOVERNANCE`
* **T9 (IT Operations & Observability)**: `T9_P1_APM_FULLSTACK`, `T9_P2_LOG_SIEM_AGGREGATION`, `T9_P3_ITSM_INCIDENT`, `T9_P4_AIOPS_REMEDIATION`, `T9_P5_RUNBOOK_AUTOMATION`
* **T10 (Governance, Risk & Compliance)**: `T10_P1_IT_STRATEGY_ARCH`, `T10_P2_VENDOR_SLA_MGMT`, `T10_P3_REGULATORY_COMPLIANCE`, `T10_P4_TECH_RISK_REGISTER`, `T10_P5_TALENT_OPERATING_MODEL`

---

# 3. Sequenced Implementation Plan

## Phase 1: Localization & Linguistic Rules Policy (`src/config/locales.json`)

**Objective**: Inject the linguistic guard arrays and Fact-First narrative templates into `locales.json` without hardcoding any strings in Python.

### Execution Steps:
1. Locate the `section_3_2_cards` namespace within each supported language block in `locales.json`.
2. Add the `linguistic_guards` object containing:
   * `anaphoric_prefixes`: Array of lowercase prefixes that invalidate a standalone opening sentence (e.g., `["this ", "these ", "that ", "those ", "it ", "its ", "they ", "their ", "however", "therefore", "furthermore", "moreover", "consequently", "unlike ", "similarly", "in contrast", "as a result", "for this reason", "which ", "where "]` for `en`, and exact equivalents like `["esto ", "esta ", "estos ", "estas ", "eso ", "esa ", "sin embargo", "no obstante", "por lo tanto", "a diferencia de", "además", "lo cual ", "el cual "]` for `es`).
   * `adversative_split_tokens`: Existing array of mid-sentence splitters, refined for precision.
3. Replace the legacy `rationale_aligned_template` with tiered Fact-First templates:
   * `fact_first_low_maturity`: *"Operational telemetry confirms a fragile baseline in {pillar_name} (Level {cal_score}): {clean_baseline}. This structural posture exposes the enterprise to immediate operational degradation: {clean_risk}."*
   * `fact_first_mid_maturity`: *"{pillar_name} operates with foundational controls (Level {cal_score}), characterized by {clean_baseline}. However, architectural scalability and fault tolerance remain constrained by {clean_risk}."*
   * `fact_first_high_maturity`: *"{pillar_name} demonstrates a resilient, standardized architecture (Level {cal_score}), anchored by {clean_baseline}. To prevent regression and achieve autonomous optimization, leadership must address residual friction: {clean_risk}."*
4. Add explicit divergence prefixes (invoked **only** when $|\Delta| \ge 1.0$):
   * `divergence_overestimated_prefix`: *"CRITICAL CALIBRATION DELTA: Internal self-assessment overestimated maturity by {delta} points (Self: {self_score} vs. Audited: {cal_score}), indicating an operational blind spot. "*
   * `divergence_underestimated_prefix`: *"CALIBRATION NOTE: Technical audit verified higher operational capability than self-reported (Self: {self_score} vs. Audited: {cal_score}), reflecting undocumented tactical controls. "*
5. Add safe fallback constants (`fallback_baseline_clause`, `fallback_risk_clause`) to guarantee zero-defect rendering when input text is empty or 100% anaphoric.

---

## Phase 2: 50-Pillar Ontology Expansion (`src/config/cmmi_progression_matrix.json`)

**Objective**: Upgrade the maturity progression configuration from 10 coarse towers to 50 distinct engineering archetypes.

### Execution Steps:
1. Restructure the root JSON object to include `"pillar_archetypes"`, `"tower_fallbacks"`, and `"universal_default"`.
2. Populate all 50 canonical keys (`T1_P1_POWER` through `T10_P5_TALENT_OPERATING_MODEL`) inside `"pillar_archetypes"`. Each key must contain localized dictionaries (or keys mapped via `locales.json` depending on current loader architecture) for Levels `1` through `5`, specifying:
   * `current_state_descriptor`: Exact engineering description of that level for that specific micro-domain.
   * `target_milestone_action`: Actionable, domain-pure engineering remediation required to reach the next CMMI level (e.g., `T1_P2_HVAC` strictly references thermal containment, N+1 CRAC/CRAH, and chilled-water loops; zero electrical or fire-suppression bleed).
3. Retain the existing 10 tower definitions inside `"tower_fallbacks"` as a secondary safety net.

---

## Phase 3: AST Compiler Refactoring (`src/compilers/in_memory_asis_compiler.py`)

**Objective**: Implement the Anaphora Resolution Guard, the Fact-First Rationale Builder, and the 3-Tier Ontology Resolver in pure, 100% Technical English Python.

### Step 3.1: Implement `_enforce_syntactic_anchor`
Add a private static/instance helper method to sanitize extracted text blocks:
* **Signature**: `def _enforce_syntactic_anchor(self, raw_text: str, guard_config: dict, fallback_text: str) -> str:`
* **Logic**:
  1. Validate `raw_text`. If `None` or empty after stripping, return `fallback_text`.
  2. Split `raw_text` into sentences using `re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s+', raw_text.strip())`.
  3. Retrieve `anaphoric_prefixes = tuple(p.lower() for p in guard_config.get("anaphoric_prefixes", []))`.
  4. Iterate through candidate sentences:
     * Clean leading bullets, numbers, or whitespace (`re.sub(r'^[\-\*\d\.\)\s]+', '', sentence).strip()`).
     * Strip adversative tails if applicable using `guard_config.get("adversative_split_tokens", [])`.
     * Check if `cleaned_sentence.lower().startswith(anaphoric_prefixes)` or if `len(cleaned_sentence) < 15`.
     * If `True`, `continue` to next candidate sentence.
     * If `False`, normalize capitalization/punctuation and return `cleaned_sentence`.
  5. If loop terminates without returning, return `fallback_text`.

### Step 3.2: Refactor `_build_diagnostic_rationale`
Replace the legacy survey-comparison builder with the Fact-First synthesis engine:
* **Signature**: `def _build_diagnostic_rationale(self, pillar_data: dict, locale_cards: dict) -> str:`
* **Logic**:
  1. Extract `pillar_name`, `self_score` (float), and `cal_score` (float). Calculate `delta = round(self_score - cal_score, 1)`.
  2. Pass raw baseline description and raw risk description through `self._enforce_syntactic_anchor(...)` using `locale_cards["linguistic_guards"]` and localized fallbacks.
  3. **Determine Divergence Prefix**:
     * If `delta >= 1.0`: Format `locale_cards["divergence_overestimated_prefix"]`.
     * Else if `delta <= -1.0`: Format `locale_cards["divergence_underestimated_prefix"]`.
     * Else: `divergence_prefix = ""` (100% Fact-First opening).
  4. **Select Fact-First Core Template**:
     * If `cal_score < 2.5`: Select `locale_cards["fact_first_low_maturity"]`.
     * Else if `cal_score < 3.8`: Select `locale_cards["fact_first_mid_maturity"]`.
     * Else: Select `locale_cards["fact_first_high_maturity"]`.
  5. Interpolate variables (`pillar_name`, `cal_score`, `clean_baseline`, `clean_risk`) and return `f"{divergence_prefix}{core_narrative}".strip()`.

### Step 3.3: Implement `_resolve_pillar_progression`
Upgrade the CMMI lookup logic to resolve at the 50-pillar granularity:
* **Signature**: `def _resolve_pillar_progression(self, pillar_id: str, tower_id: str, current_level: int, matrix: dict) -> dict:`
* **Logic (3-Tier Cascade)**:
  1. Clamp `target_level = min(max(int(round(current_level)) + 1, 2), 5)`.
  2. **Tier 1 (Exact Pillar Archetype)**: Query `matrix.get("pillar_archetypes", {}).get(pillar_id, {}).get("levels", {}).get(str(target_level))`. If valid, return milestone payload.
  3. **Tier 2 (Dynamic Token Matching)**: If `pillar_id` is a custom client ID not matching standard `T{X}_P{Y}` nomenclature, normalize tokens from `pillar_id` / `pillar_name` against a deterministic keyword-to-archetype index stored in `matrix.get("semantic_routing_map", {})`.
  4. **Tier 3 (Tower & Universal Fallback)**: Query `matrix.get("tower_fallbacks", {}).get(tower_id, ...)` and finally `matrix.get("universal_default", ...)`.

---

# 4. Quality Gate & Verification Matrix

Before merging into the production branch, the implementation must pass the following automated verification gates:

| Gate ID | Verification Dimension | Test Vector / Assertion | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **QG-01** | **Anaphora Guard** | Input finding: `"This creates high latency in the core. The BGP routing table lacks route summarization."` | Sentence 1 is discarded due to `"This "` prefix. Output cleanly anchors on Sentence 2: `"The BGP routing table lacks route summarization."` |
| **QG-02** | **Total Orphan Fallback** | Input finding: `"However, it fails. This is critical."` (100% anaphoric/short). | Loop exhausts candidates and safely returns `locales.fallback_baseline_clause` with zero crashes or empty strings. |
| **QG-03** | **Fact-First Alignment** | Pillar with `self_score = 2.0`, `cal_score = 2.2` ($\|\Delta\| = 0.2$). | Output contains **zero** mention of "self-assessment" or "survey alignment". Opens immediately with operational reality. |
| **QG-04** | **Blind-Spot Alerting** | Pillar with `self_score = 4.0`, `cal_score = 2.0` ($\Delta = +2.0$). | Output prepends `divergence_overestimated_prefix` before transitioning into the Fact-First narrative. |
| **QG-05** | **50-Pillar Precision** | Evaluate `T1_P2_HVAC` at Level 2. | Target milestone recommends CRAC/CRAH N+1 and aisle containment. Zero mention of UPS, generators, or electrical switchgear. |
| **QG-06** | **Codebase Purity** | Run static AST linter across `in_memory_asis_compiler.py`. | Zero non-English identifiers, comments, or string literals in Python code. 100% `KeyError`-safe `.get()` dictionary access. |