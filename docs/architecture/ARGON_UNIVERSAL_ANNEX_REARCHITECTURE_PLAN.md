# MASTER ARCHITECTURAL BLUEPRINT: AST COMPILATION PIPELINE REMEDIATION
**Document ID:** ARCH-AST-2026-V1  
**Author:** `gemini-4-argon` (Principal Enterprise Architect & Chief Cybersecurity Auditor)  
**Target System:** Assessment Engine — AST Compilation & Localization Pipeline  
**Quality Standard:** Tier-1 Global Management Consulting (McKinsey / BCG / Bain)  
**Compliance Mandate:** 100% Technical English Codebase | Zero Hardcoding | Strict Industry Agnosticism

---

## 1. EXECUTIVE ARCHITECTURAL DIAGNOSIS

The recent compilation of **Annex 5 (Resilience & Continuity)** for our synthetic cloud-native FinTech benchmark (**Starling Bank**) exposed critical architectural violations within the Abstract Syntax Tree (AST) generation layer. The engine failed its primary mandate of universal industry agnosticism by leaking legacy Operational Technology (OT) and physical manufacturing paradigms into a 100% AWS Cloud-Native financial institution's report.

### Root Cause Analysis (RCA) of Identified Failures
1. **Cross-Vertical Hallucination (`locales.json`):** The localization catalog contains static, industry-specific domain phrasing (e.g., *"industrial networks, plant control systems, and operational technology (OT)"*) bound to generic keys like `operational_mission`. The AST builder blindly interpolates these strings without evaluating the client's `industry_vertical` or `infrastructure_topology` metadata.
2. **Hardcoded Legacy Scenarios (`ast_appendices_builder.py`):** Developers bypassed the dynamic telemetry layer and hardcoded specific historical client findings (e.g., *"500-meter proximity between datacenters"*, *"total plant halts"*) directly inside fallback string templates within the Python AST compiler.
3. **Semantic Inversion in Risk Cards (`ast_appendices_builder.py` & `payload_to_ast.py`):** When building Risk Cards, the data-binding logic maps to the `target_state` or maturity rubric descriptions (which describe the *ideal* state or active strengths, such as `[RVS03]`) rather than the `gap_analysis`, `finding`, or `vulnerability_vector` attributes. Furthermore, high-maturity controls are not being filtered out of the risk register, causing strengths to be rendered as critical financial liabilities.
4. **Degenerate String Concatenation (`ast_appendices_builder.py`):** The narrative synthesis function iterates over KPI arrays (`T5.P3.K1`, `T5.P3.K2`, etc.) and maps them to their parent Pillar's generic title rather than the specific KPI's distinct `metric_name` or `domain_focus`, resulting in robotic, repetitive prose.
5. **Unresolved Localization Keys (`payload_to_ast.py`):** The key `diag_summary_default` is passed directly as a literal string into the AST `Paragraph` node because the translation resolver (`t()`) either lacks the key in `locales.json` or is bypassed entirely during fallback execution.
6. **Naive Actuarial Flattening (`ast_appendices_builder.py`):** In the Economic Risk Evaluation section, the compiler takes the Pillar's aggregate Annualized Loss Expectancy (`pillar_ale`) and divides it equally by the number of findings ($ALE_{card} = \frac{ALE_{pillar}}{N}$). This completely destroys the upstream FAIR/Bayesian Monte Carlo distribution computed by the core math engine.

---

## 2. ARCHITECTURAL INVARIANTS & GOVERNANCE RULES

Before a single line of code is modified, the following architectural invariants are hereby enforced across the entire codebase:

* **INVARIANT 1 (Zero Domain Bias in Static Catalogs):** `locales.json` and any static templates may **never** contain industry-specific nouns (e.g., *plant, factory, OT, SCADA, branch, clinic, warehouse, datacenter*). All domain-specific context must be injected dynamically from the `ClientProfile` and `DomainTaxonomy` payload objects.
* **INVARIANT 2 (100% Technical English Codebase):** Every variable, function name, docstring, inline comment, log message, and exception string in `.py` files must be written in strict Technical English. Any Spanish nomenclature is an immediate build-breaking violation.
* **INVARIANT 3 (Strict Semantic Polarity):** An AST node designated as a `RiskCard` or `DeficitItem` must mathematically verify that $Score_{actual} < Score_{target}$ before instantiation, and may only bind to attributes with negative semantic polarity (`finding_narrative`, `risk_exposure`, `remediation_gap`).
* **INVARIANT 4 (Actuarial Immutability in the View Layer):** The AST compiler is a *presentation adapter*, not an actuarial engine. It is strictly forbidden from performing division, averaging, or arbitrary math on financial metrics. It must read pre-calculated, severity-weighted values directly from the domain payload.
* **INVARIANT 5 (Strict i18n Resolution):** No raw translation keys may ever reach the DOCX renderer. The localization resolver must implement a strict mode that raises a `LocalizationResolutionError` during compilation if a key is missing or unmapped.

---

## 3. MULTI-PHASE REMEDIATION MASTER PLAN

---

### PHASE 1: Baseline & Catalog Sanitization (Zero-Bias I18n Architecture)

**Objective:** Purge all hardcoded industry-specific terminology, legacy client scenarios, and Spanish residuals from the localization catalogs and AST builders. Establish a context-aware interpolation mechanism.

#### 1.1. Target Files for Modification
* `engine_config/locales.json`
* `src/assessment_engine/adapters/compilers/ast_appendices_builder.py`
* `src/assessment_engine/core/i18n/translator.py` (or equivalent localization resolver)

#### 1.2. Detailed Execution Steps
1. **Audit and Purge `locales.json`:**
   * Execute a regex scan across `locales.json` for prohibited domain tokens: `\b(plant|plants|OT|SCADA|industrial|factory|500-meter|meters|cement|kiln|branch|branches|on-premise|datacenter)\b`.
   * Refactor `operational_mission` and all annex introductory templates to use parameterized, universal enterprise tokens:
     * *Legacy (Flawed):* `"The operational mission relies on industrial networks, plant control systems, and operational technology (OT)..."`
     * *Remediated (Universal):* `"The operational mission relies on {critical_infrastructure_descriptor}, core business applications, and {technology_stack_descriptor} to sustain value delivery..."`
   * Add the missing `diag_summary_default` key to `locales.json` across all supported languages (`en`, `es`, `pt`, `fr`, `de`), ensuring it uses dynamic placeholders for company name, primary pillar, and maturity state.

2. **Context-Aware Token Injection (`payload_to_ast.py`):**
   * Create a helper method `_build_lexical_context(client_profile: dict) -> dict` that maps the client's vertical and architecture (e.g., `FinTech` + `Cloud-Native`) to appropriate lexical descriptors (e.g., `critical_infrastructure_descriptor = "distributed cloud environments and high-availability API gateways"`).
   * Pass this lexical context dictionary into all `translator.translate(key, **context)` calls.

3. **Purge Hardcoded Scenarios from `ast_appendices_builder.py`:**
   * Locate the dashboard synthesis function (specifically around the Resilience/Continuity narrative generation).
   * Delete the hardcoded string containing *"500-meter proximity between datacenters sharing electrical feeds turns localized power cuts into total plant halts"*.
   * Replace it with a data-driven extraction call that pulls the `primary_threat_scenario` directly from the highest-weighted risk item in the current annex's payload: `top_risk.get("scenario_description")`.

---

### PHASE 2: AST Compiler Decoupling & Semantic Fixes

**Objective:** Eliminate semantic inversions in Risk Cards, resolve raw key leaks, and replace repetitive KPI string concatenation with an intelligent, deduplicated syntactic aggregator.

#### 2.1. Target Files for Modification
* `src/assessment_engine/adapters/compilers/ast_appendices_builder.py`
* `src/assessment_engine/adapters/compilers/payload_to_ast.py`

#### 2.2. Detailed Execution Steps

1. **Fix Semantic Inversion in Risk Cards (`ast_appendices_builder.py`):**
   * **Target Function:** `_build_risk_cards_section()` / `_create_risk_card_node()`
   * **Filter Implementation:** Currently, the loop iterates over all evaluated controls/sub-pillars regardless of score. Introduce a strict predicate filter:
     ```python
     # Only controls with an actual maturity deficit qualify as risks
     active_risks = [
         item for item in pillar_data.get("evaluated_items", [])
         if item.get("maturity_score", 5.0) < item.get("target_maturity", 3.0)
         and item.get("risk_status") != "OPTIMAL"
     ]
     ```
   * **Attribute Remapping:** Change the AST node data binding:
     * **REMOVE:** `description = item.get("target_state")` or `item.get("rubric_description")` (which pulls `[RVS03] Standardized procedures...`).
     * **REPLACE WITH:** `description = item.get("finding_narrative") or item.get("vulnerability_description") or item.get("gap_summary")`.
     * Strip internal rubric tags (e.g., `[RVS03]`, `[GOV01]`) from executive-facing risk titles using a regex sanitizer `re.sub(r'^\[[A-Z0-9_-]+\]\s*', '', raw_text)` unless explicitly required in technical audit tables.

2. **Eliminate Repetitive KPI String Concatenation (`ast_appendices_builder.py`):**
   * **Target Function:** `_synthesize_pillar_kpi_narrative()` (or the paragraph builder in the Executive Summary / Pillar Overview).
   * **Root Cause:** The current code iterates over `kpis` and prints `f"{pillar_name} operational controls ({kpi_id})"` for every single KPI.
   * **Remediation Algorithm (Syntactic Grouping):**
     * Extract the specific `kpi_name` or `short_label` for each KPI (e.g., *"RTO/RPO Compliance"*, *"Automated Failover Testing"*).
     * If multiple KPIs share a parent category label, group their IDs instead of repeating the text:
       * *Degenerate Output:* `"...analyzing disaster recovery controls (T5.P3.K1), disaster recovery controls (T5.P3.K2), disaster recovery controls (T5.P3.K3)..."`
       * *Remediated Output:* `"...analyzing critical telemetry across Multi-Region Failover Testing (T5.P3.K1), RTO/RPO SLA Adherence (T5.P3.K2), and Immutable Backup Integrity (T5.P3.K3)..."`
     * Fallback safeguard: If individual KPI names are missing in a malformed payload and only the parent category exists, group the IDs under a single noun phrase: `"...analyzing Disaster Recovery Architecture & Failover controls (T5.P3.K1 – T5.P3.K4)..."`.

3. **Resolve `diag_summary_default` Leak (`payload_to_ast.py` & `ast_appendices_builder.py`):**
   * Locate every occurrence of `"diag_summary_default"` in the compiler files.
   * Ensure it is wrapped in the localization resolver: `self.i18n.t("diag_summary_default", company=client_name, pillar=pillar_title, ale=formatted_ale)`.
   * Implement a pre-render AST validation hook `_validate_ast_text_nodes(ast_root)` that traverses the AST prior to DOCX compilation and raises a `ValueError` if any string matches the pattern `^[a-z0-9_]+_[a-z0-9_]+$` (snake_case leak detection).

---

### PHASE 3: Actuarial Math & Financial Integrity

**Objective:** Eradicate naive equal-division math in the presentation layer and enforce true Bayesian/FAIR severity-weighted financial distribution across all Risk Cards and Economic Evaluation tables.

#### 3.1. Target Files for Modification
* `src/assessment_engine/adapters/compilers/ast_appendices_builder.py`
* `src/assessment_engine/ adapters/compilers/payload_to_ast.py`
* `src/assessment_engine/core/financial/ale_distributor.py` (if upstream adjustment is required)

#### 3.2. Detailed Execution Steps

1. **Remove Naive Division from the AST Builder:**
   * Locate the code block in `ast_appendices_builder.py` calculating `card_ale = total_pillar_ale / len(risk_cards)`. **Delete this line immediately.**

2. **Bind to Upstream FAIR/Bayesian Component ALE:**
   * Each evaluated control/risk item in the payload must carry its own `annualized_loss_expectancy` (`item_ale`) computed by the core actuarial engine.
   * If the payload only provides `pillar_ale` at the aggregate level and `risk_weight` / `severity_score` at the item level, implement a deterministic **Non-Linear Severity Weighting Function** inside `payload_to_ast.py` (acting as the canonical data adapter):
     $$W_i = (\text{Target}_i - \text{Actual}_i)^\gamma \times \text{Criticality}_i$$
     $$\text{ALE}_i = \text{ALE}_{\text{pillar}} \times \frac{W_i}{\sum_{j=1}^{N} W_j}$$
     *(Where $\gamma = 2.0$ to reflect exponential tail-risk escalation in cybersecurity deficits, ensuring severe gaps receive a disproportionately higher share of the financial exposure than minor gaps).*

3. **Reconciliation & Formatting Invariant:**
   * Verify that $\sum_{i=1}^{N} \text{ALE}_i \equiv \text{ALE}_{\text{pillar}}$ (applying largest-remainder rounding to prevent penny/pound discrepancies in executive tables).
   * Format all currency outputs dynamically using the client's `currency_code` and `revenue_scale` from the payload (e.g., `£14,250 / year` vs `£4,120 / year` for SMB/Mid-Market, or `$1.42M / year` for Global Fortune 500).

---

### PHASE 4: Final Certification & Multi-Vertical Verification

**Objective:** Mathematically and linguistically certify that the remediated AST pipeline produces Tier-1 consulting output across radically different industries, company sizes, and languages without a single regression.

#### 4.1. The 5-Client Synthetic Verification Matrix
We will execute end-to-end compilation of **Annex 5 (and all companion annexes)** across our 5 canonical benchmark archetypes:
1. **Starling Bank (UK):** Cloud-Native FinTech | 100% AWS | Currency: `GBP (£)` | Language: `EN-GB`
2. **CEMEX / Holcim Archetype (Mexico/Global):** Heavy Industrial & Cement Manufacturing | Hybrid OT/IT & SCADA | Currency: `USD ($)` | Language: `ES`
3. **BioNTech / Moderna Archetype (Germany):** Regulated Life Sciences & Pharma | GxP Cloud + Lab Environments | Currency: `EUR (€)` | Language: `DE`
4. **Shopify / MercadoLibre Archetype (LATAM/North America):** High-Velocity E-Commerce | Multi-Cloud Microservices | Currency: `USD ($)` | Language: `PT-BR`
5. **Regional Healthcare Provider ($25M SMB):** Healthcare Services | Legacy On-Premise + SaaS | Currency: `USD ($)` | Language: `EN-US`

#### 4.2. Automated Certification Gates (CI/CD Test Suite)
We will implement `tests/certification/test_annex_ast_integrity.py` containing four mandatory automated gates:

* **Gate 1: Cross-Vertical Lexical Contamination Test:**
  * Parses the generated AST and final `.docx` XML for Starling Bank.
  * **Assertion:** Zero occurrences of `["plant", "OT", "SCADA", "industrial", "500-meter", "factory", "kiln"]`.
* **Gate 2: Semantic Polarity & Rubric Leak Test:**
  * Inspects every `RiskCard` node in the AST.
  * **Assertion:** Zero occurrences of `[RVS03]` or high-maturity strings (`"Standardized procedures and automated controls active"`) inside risk descriptions. Asserts that every rendered risk card corresponds to a control with `maturity_score < target_maturity`.
* **Gate 3: Linguistic & Key Resolution Test:**
  * Scans the entire AST text corpus for raw localization keys (`diag_summary_default`, `*_label`, `*_desc`) and n-gram repetition (ensuring no phrase of $>5$ words is repeated $>2$ times within the same paragraph).
  * Scans the Python AST compiler codebase to verify 0% Spanish tokens in comments, variables, or strings.
* **Gate 4: Actuarial Variance & Reconciliation Test:**
  * Extracts all financial figures from the Risk Cards in Annex 5.
  * **Assertion 1 (Variance):** If $N_{\text{cards}} > 1$ and maturity scores differ, the standard deviation of `card_ale` must be strictly greater than zero ($\sigma_{\text{ALE}} > 0$), proving that flat division is eradicated.
  * **Assertion 2 (Reconciliation):** The sum of individual risk card ALEs equals the Pillar Total ALE displayed in the Executive Dashboard within a tolerance of $\pm 1$ currency unit.

---

## 4. IMMEDIATE NEXT STEPS FOR EXECUTION

Upon your authorization of this Master Architectural Blueprint, we will proceed strictly in sequence:
1. **Step 1:** Inspect and sanitize `engine_config/locales.json` (Phase 1).
2. **Step 2:** Refactor `payload_to_ast.py` and `ast_appendices_builder.py` to fix the semantic inversion, KPI prose generation, and missing key resolution (Phase 2).
3. **Step 3:** Wire the non-linear FAIR/Bayesian severity weights into the AST Risk Card financial binding (Phase 3).
4. **Step 4:** Run the Starling Bank compilation and execute the 4 Automated Certification Gates (Phase 4).

*Awaiting command to initiate Phase 1 execution.*