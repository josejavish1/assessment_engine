# ARCHITECTURAL JUDGMENT & MASTER REMEDIATION BLUEPRINT
**Authority:** `gemini-4-argon` (Principal Enterprise Architect & Chief Forensic Auditor)  
**Target System:** Assessment Engine Core, Actuarial Compiler, & Multilingual AST Renderer  
**Standard:** Tier-1 Global Enterprise Architecture (Zero Hardcoding, 100% English Codebase, Deterministic Localization, Actuarial Coherence)

---

## 1. EXECUTIVE FORENSIC DIAGNOSIS

The vulnerabilities exposed during the Starling Bank calibration audit are not isolated rendering bugs; they are symptoms of **architectural boundary violations**:
1. **Violation of Canonical Data Neutrality:** Domain definitions (`tower_definition_T*.json`) conflate structural topology with presentation-layer strings authored in a legacy locale (`es-ES`), violating the Single Source of Truth (SSOT) principle.
2. **Permissive Silent Fallback Anti-Pattern:** The AST compiler utilizes a silent fallback (`default=raw_cap`), masking missing localization keys by injecting raw source strings into target deliverables.
3. **Namespace Collision in Actuarial Contexts:** The financial templating contract conflates **Portfolio-Level Consolidated Value-at-Risk (VaR)** with **Domain-Scoped Marginal VaR**, presenting two mathematically distinct figures under ambiguous terminology.
4. **Unattenuated Blast-Radius Modeling:** The Open FAIR narrative generator exposes the raw enterprise gross hourly burn rate without applying or articulating the **Domain Operational Attenuation Factor ($\alpha_{\text{domain}}$)**, creating unrealistic executive risk narratives (e.g., implying a facility sub-circuit failure halts 100% of cloud-native banking clearing).

To elevate the Assessment Engine to the undisputed global #1 standard across any vertical and any language, we will execute a **4-Phase Zero-Defect Architectural Overhaul**.

---

## 2. SYSTEMIC REMEDIATION ARCHITECTURE (THE 4 ROOT CAUSES)

### 2.1. Root Cause 1 & 4: Canonical Language-Neutral Topology & Strict I18n Resolution
We will decouple **Structural Topology** from **Linguistic Representation**. 

* **Canonical English-Only Topology (`tower_definition_T*.json`):**
  All structural JSON schemas, internal keys, code comments, log messages, and canonical developer descriptions must be 100% Technical English. No human-readable string from a topology file may ever be directly emitted into a customer deliverable.
* **Universal Hierarchical Resource Catalog (`taxonomy_multilingual.json` / I18n Store):**
  Every entity in the assessment universe must be addressed via an immutable **Universal Resource Identifier (URN)**:
  * Tower URN: `urn:assessment:tower:T01`
  * Pillar URN: `urn:assessment:tower:T01:pillar:P04`
  * KPI URN: `urn:assessment:tower:T01:pillar:P04:kpi:K02`
  * Risk Vector URN: `urn:assessment:risk:T01:RVS04`
* **Strict Fail-Fast Localization Resolver:**
  We will abolish `default=raw_cap`. The I18n Resolver will operate in **Strict Deterministic Mode**. When compiling an AST for target locale $L \in \{\text{en-GB}, \text{es-ES}, \text{pt-BR}, \text{fr-FR}, \text{de-DE}, \text{ja-JP}\}$, every URN must resolve to a verified entry in locale $L$. If a key is missing, the compiler raises a `MissingLocalizationKeyError` at build/compile time, halting document generation before a contaminated deliverable can be produced.

### 2.2. Root Cause 2: Disambiguated Dual-Tier Actuarial Exposure Contract
To eliminate executive confusion between consolidated enterprise exposure and single-tower exposure, we will enforce strict **Actuarial Namespace Separation** in the AST payload and narrative templates:

* **Tier 1: Enterprise Portfolio Consolidated VaR (`portfolio_p90_var_exposure`):**
  Represents the Monte Carlo simulated 90th percentile loss across all active towers, accounting for inter-domain correlation matrices and tail-risk aggregation.
* **Tier 2: Domain-Isolated Marginal VaR (`domain_local_p90_var_exposure`):**
  Represents the standalone 90th percentile loss attributable strictly to the specific tower's risk vectors (`RVS01..RVSn`) in isolation.
* **Tier 3: Portfolio Risk Contribution Ratio (`domain_var_contribution_pct`):**
  A bridge metric explaining how the local domain exposure contributes to or triggers cascading effects within the consolidated portfolio exposure.
* **Narrative Contract:**
  * In Tower Annex Executive Summaries (e.g., P15), the narrative must explicitly state both metrics or strictly bind to `domain_local_p90_var_exposure`, while referencing `portfolio_p90_var_exposure` only as the overarching enterprise ceiling:
    > *"Within the isolated scope of Tower 1, direct actuarial P90 exposure stands at **{domain_local_p90_var_fmt}** (representing isolated domain vulnerability), while contributing to an aggregated cross-enterprise tail-risk ceiling of **{portfolio_p90_var_fmt}**."*

### 2.3. Root Cause 3: Open FAIR Blast-Radius & Domain Attenuation Architecture
No single tower failure automatically equates to a 100% enterprise-wide operational halt unless the architecture lacks redundancy across all availability zones. We will replace the flat hourly burn rate narrative with a **3-Factor Open FAIR Attenuation Model**:

$$\text{Effective Hourly Loss Rate } (E_{\text{hr}}) = R_{\text{gross}} \times \alpha_{\text{vertical}} \times \beta_{\text{domain}}$$

Where:
* $R_{\text{gross}}$ (`enterprise_gross_hourly_revenue_at_risk`): Total enterprise hourly transaction/revenue velocity (e.g., £140,000/hr).
* $\alpha_{\text{vertical}}$ (`vertical_dependency_elasticity`): Industry vertical sensitivity coefficient (dynamically derived from the company profile/vertical archetype—e.g., Cloud-Native Neobank vs. Heavy Manufacturing).
* $\beta_{\text{domain}}$ (`domain_blast_radius_factor`): The specific tower's operational coupling factor ($0.0 < \beta \le 1.0$). For a cloud-native neobank, physical facilities (`T01`) have a low blast-radius factor (e.g., $\beta = 0.08$ to $0.15$) due to cloud workload abstraction, whereas Core Cloud Platform (`T04`) or Cybersecurity (`T07`) may have $\beta = 0.85$.

The AST narrative contract will transparently present:
1. The Gross Enterprise Baseline ($R_{\text{gross}}$).
2. The Domain Blast-Radius Attenuation Factor ($\beta_{\text{domain}}$) based on architectural decoupling.
3. The Resulting Net Domain Hourly Impact ($E_{\text{hr}}$), ensuring mathematical alignment with the domain's local P90 exposure (`£14,098`).

---

## 3. MULTI-PHASE EXECUTION PLAN

To guarantee zero regressions and complete linguistic and mathematical purity, implementation will proceed across **four strictly gated phases**.

### PHASE 1: Linguistic Decontamination & Canonical Schema Refactoring
**Objective:** Purge 100% of Spanish strings from the codebase and structural definitions, establishing an English-only canonical schema and a complete KPI-level multilingual taxonomy.

1. **Codebase Forensic Sweep & English Normalization:**
   * Audit all `.py`, `.json`, `.yaml`, and `.j2`/template files across the repository.
   * Translate all code comments, docstrings, exception messages, logger outputs, and variable/key names into 100% Technical English.
2. **Topology Schema Refactoring (`engine_config/towers/T*/tower_definition_T*.json`):**
   * Replace all legacy Spanish `name`, `title`, and `description` fields in Tower, Pillar, Risk Vector (`RVS*`), and KPI (`K1..Kn`) objects with canonical Technical English definitions.
   * Bind every Tower, Pillar, Risk Vector, and KPI to a deterministic `i18n_key` (URN pattern).
3. **KPI-Level Multilingual Taxonomy Expansion (`engine_config/taxonomy_multilingual.json`):**
   * Extend the schema of `taxonomy_multilingual.json` to include a dedicated `kpis` and `risk_vectors` hierarchy under each Tower/Pillar.
   * Populate verified, domain-accurate translations for every KPI (`K1..Kn`) and Risk Vector (`RVS*`) across all supported target locales (`en`, `es`, `pt`, `fr`, `de`, `ja`).
4. **Abolition of Permissive Fallbacks (`in_memory_asis_compiler.py` & `payload_to_ast.py`):**
   * Remove `default=raw_cap` and similar silent fallback mechanisms.
   * Implement `StrictTaxonomyResolver.resolve(urn, locale)` which raises a fatal compile-time exception if a translation is missing or empty.

**Phase 1 Exit Criteria:** Zero Spanish tokens exist anywhere in `.py` files or `tower_definition_T*.json` files. Compiling any tower in `en-GB` resolves 100% of Tower, Pillar, Risk, and KPI names via the `en` branch of `taxonomy_multilingual.json`.

---

### PHASE 2: Actuarial Context Disambiguation & Open FAIR Attenuation Engine
**Objective:** Reconcile the P90 exposure discrepancy and implement dynamic Open FAIR blast-radius attenuation for any company size and industry vertical.

1. **Actuarial Payload Schema Split:**
   * Refactor the financial compiler output contract to explicitly emit:
     * `portfolio_p90_var_exposure` & `portfolio_p90_var_exposure_fmt`
     * `domain_local_p90_var_exposure` & `domain_local_p90_var_exposure_fmt`
     * `domain_var_share_pct` (percentage of domain risk relative to total unmitigated risk).
2. **Open FAIR Attenuation Calculator:**
   * Introduce parameterized calculation of `domain_blast_radius_factor` ($\beta_{\text{domain}}$) and `effective_domain_hourly_burn_rate` ($E_{\text{hr}}$) inside the actuarial engine.
   * Ensure $\beta_{\text{domain}}$ is dynamically derived from the client's topology maturity, redundancy profile, and vertical dependency weights—with **zero hardcoded company assumptions**.
3. **Narrative Template Alignment:**
   * Update Executive Summary (P15) and Section 4.3 (P108) AST builders and localized templates so that:
     * P15 clearly distinguishes between the **Domain-Specific P90 Exposure** and the **Enterprise Portfolio P90 Exposure**.
     * P108 matches the exact `domain_local_p90_var_exposure_fmt` stated in P15.
     * The downtime impact narrative explicitly states the Gross Hourly Burn Rate, the Domain Blast-Radius Attenuation Factor ($\beta_{\text{domain}}$), and the Net Domain Hourly Exposure ($E_{\text{hr}}$).

**Phase 2 Exit Criteria:** P15 and P108 display 100% consistent actuarial figures. The mathematical relationship between Gross Hourly Rate, Attenuated Domain Rate, SLE (Single Loss Expectancy), and Domain P90 VaR is transparent and auditable by a Chief Risk Officer.

---

### PHASE 3: Automated CI/CD Linguistic Purity & Actuarial Integrity Gates
**Objective:** Make it architecturally impossible for foreign language leakage or actuarial contradictions to ever reach production again.

1. **Gate 1: Source Code & Schema English-Purity Linter (`ci_gate_english_purity.py`):**
   * A static analysis scanner running on every commit that inspects all `.py` files and `tower_definition_*.json` files.
   * Detects Spanish/non-English diacritics (`á, é, í, ó, ú, ñ, ü, ç, ã, õ`) and runs an N-gram/lexicon check against forbidden non-English stop-words (`de`, `la`, `el`, `para`, `con`, `operación`, `protección`, `seguridad`, `capacidad`, etc.).
   * **Exception Scope:** Only explicit localization catalog files (`taxonomy_multilingual.json`, `locales/*.json`) are permitted to contain non-English characters.
2. **Gate 2: Taxonomy Completeness Validator (`ci_gate_taxonomy_completeness.py`):**
   * Cross-references every Tower, Pillar, Risk Vector, and KPI ID defined across `tower_definition_T*.json` against `taxonomy_multilingual.json`.
   * Verifies bijective (1:1) coverage across all supported languages. Fails the build if any KPI lacks a translation in any required language.
3. **Gate 3: Post-Compile Deliverable Forensic Scanner (`ci_gate_output_forensics.py`):**
   * Parses the generated AST / Markdown / DOCX text of the compiled deliverable.
   * Runs language detection per paragraph/table cell against the requested target locale (e.g., `en-GB`). If a single cell or bullet point triggers a foreign language confidence threshold (e.g., Spanish leakage in an English report), the pipeline fails immediately.
   * Verifies actuarial invariants (e.g., asserts `domain_local_p90_var_exposure <= portfolio_p90_var_exposure` and verifies that formatted currency strings match across sections).

**Phase 3 Exit Criteria:** All 3 automated gates are integrated into the test suite and return `PASS` with zero warnings.

---

### PHASE 4: Multi-Vertical, Multi-Locale Calibration & Certification
**Objective:** Empirically validate the architecture across diverse enterprise archetypes and languages.

1. **Synthetic Matrix Verification:**
   * Execute end-to-end compilation across all Towers (`T01..Tn`) using contrasting corporate profiles (e.g., UK Cloud Neobank in `en-GB`, LatAm Retail Conglomerate in `es-ES`, Brazilian Financial Institution in `pt-BR`) to confirm zero hardcoding and universal vertical adaptability.
2. **Forensic Diff Audit:**
   * Inspect generated ASTs and final deliverables for Starling Bank (`en-GB`) to confirm:
     * Table 13 and Table 14 Risk Titles render in 100% idiomatic British/Technical English.
     * Executive Bullets P11–P13 render KPI names in 100% Technical English.
     * P15 and P108 actuarial figures and attenuated hourly burn rates are 100% coherent.

---

## 4. ARCHITECTURAL GOVERNANCE SUMMARY

| Vulnerability | Legacy Failure Mode | New Tier-1 Architectural Standard | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **1. Foreign String Leaks** | Spanish KPI/Pillar strings in `tower_definition_T*.json` + `default=raw_cap` fallback | 100% English canonical definitions + Full KPI-level `taxonomy_multilingual.json` + Fail-Fast URN resolution | `StrictTaxonomyResolver` + CI Gate 2 & Gate 3 |
| **2. P90 VaR Discrepancy** | Ambiguous variable `{p90_var_exposure_fmt}` used for both portfolio and local scope | Explicit namespace separation: `portfolio_p90_var_exposure` vs. `domain_local_p90_var_exposure` | Actuarial Contract Schema + CI Gate 3 Invariant Check |
| **3. Blanket Downtime Rate** | Unattenuated enterprise gross burn rate applied to localized facility risks | Open FAIR 3-Factor Attenuation ($R_{\text{gross}} \times \alpha_{\text{vertical}} \times \beta_{\text{domain}}$) | Actuarial Engine Attenuation Calculator |
| **4. Codebase Impurity** | Mixed Spanish/English literals, comments, and schemas | 100% Technical English engineering artifacts; localization isolated strictly to I18n catalogs | CI Gate 1 (`ci_gate_english_purity.py`) |

---
**Awaiting Authorization:** Upon your directive, we will initiate **Phase 1** (Linguistic Decontamination, Canonical Schema Refactoring, and KPI Taxonomy Expansion).