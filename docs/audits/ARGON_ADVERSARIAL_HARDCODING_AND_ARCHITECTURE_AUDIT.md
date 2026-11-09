---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---
# ADVERSARIAL ARCHITECTURAL AUDIT & REMEDIATION MANIFESTO
**Auditor:** `gemini-4-argon` (Principal Enterprise Architect, Chief Cybersecurity Auditor & Supreme Code Quality Arbiter)  
**Status:** **CRITICAL ARCHITECTURAL VETO — EXECUTION HALTED**  
**Subject:** Forensic Audit of Recent Delivery Pipeline Changes, Anti-Pattern Eradication, and Universal Zero-Hardcoding Architecture

---

## SECTION 1: FORENSIC CODE REVIEW & ANTI-PATTERN DISSECTION

### 1.1 The `if "Starling" in client_name:` Catastrophe (`scripts/build_client_delivery_suite.py`)
The introduction of tenant-specific conditional branching (`if "Starling" in client_name:`) inside an orchestration and payload-hydration script is a **Cardinal Violation of Enterprise Architecture**. It violates the Open-Closed Principle (OCP), the Single Responsibility Principle (SRP), and the fundamental **Zero-Hardcoding Mandate** of the Assessment Engine.

**Why this is a catastrophic architectural smell:**
1. **Complete Inversion of Data vs. Control Flow:** The assessment engine is designed as a deterministic, data-driven compiler. By injecting bespoke domain narratives (Core Banking APIs, Faster Payments, FCA/PRA compliance, Cloud HSMs) directly into Python control flow based on a substring match of `client_name`, the script ceases to be an engine and degenerates into a brittle, hardcoded mock generator.
2. **Failure to Scale Across the 5 Benchmark Archetypes (Let Alone the World):** The test suite includes 5 distinct synthetic benchmark clients (`UK_Starling_Bank`, `BR_Rede_DOr_Sao_Luiz`, `FR_Geodis_Logistics`, `MX_Grupo_Chedraui`, `US_Datadog_Cloud`). By hardcoding an `if "Starling"` branch and leaving an `else:` block with generic boilerplate, the author created a "Potemkin village": Starling Bank appears to have rich, domain-specific forensic telemetry, while Rede D'Or (Healthcare), Geodis (Logistics), Chedraui (Retail), and Datadog (SaaS) silently receive generic, low-fidelity fallback strings—or worse, fall through to contaminated static catalogs.
3. **Bypassing the Evidence Ledger & Transcript Harvester:** The entire purpose of generating `transcription_1_...docx`, `transcription_2_...docx`, and `assessment_responses.txt` in `build_synthetic_control_fixture.py` is to test the engine's ability to **extract, synthesize, and hydrate** domain-specific findings from raw client inputs. Hardcoding the output in `build_client_delivery_suite.py` completely short-circuits the ingestion pipeline, rendering the synthetic transcripts decorative dead weight.

### 1.2 Secondary Hacks, Shortcuts, and Fragile Assumptions Identified
A forensic inspection of the git diff across all touched files reveals several additional structural shortcuts that must be surgically corrected:

1. **Ad-Hoc Math & Naive ALE Partitioning in `build_client_delivery_suite.py`:**
   * Instead of invoking the canonical FAIR/Monte Carlo actuarial allocation logic (`policy_engine.py`), `build_client_delivery_suite.py` fabricates pillar-level Annualized Loss Expectancy (`ale`) by dividing total tower ALE evenly (`tower_ale / max(len(def_data.get("pillars", [])), 1)`) and multiplying by an arbitrary scalar (`max(0.2, (4.0 - p_score) / 3.0)`).
   * Furthermore, `subpillar_scores` are synthetically jittered using hardcoded modulo arithmetic (`round(max(1.0, min(5.0, p_score + ((-1) ** s_idx) * 0.15)), 2)`) rather than aggregating the actual KPI answers mapped to each subpillar in `case_input.json`!
2. **Naive String Replacement in `localization.py` (`format_currency_text`):**
   * The newly added `format_currency_text()` function performs raw string replacements (`result.replace("€", symbol).replace("EUR", code)`) and only converts numeric magnitudes when `EUR` is explicitly followed by `M` or `K` (`r"(\d+(?:\.\d+)?)\s*([MK])\s*(?:€|EUR)"`).
   * **The Bug:** In `locales.json`, values like `"75,000 € / yr"` are not suffixed with `M` or `K`. Consequently, `format_currency_text("75,000 € / yr", fx_rate=5.40)` for a Brazilian Real (`BRL`) client simply swaps `€` for `R$` without applying the `5.40` exchange rate, yielding `"75,000 R$ / yr"`—a 540% financial misstatement!
3. **Symptom-Masking in `tomo_asis_ast_compiler.py`:**
   * Changing the precedence order in `_build_tower_deep_dives_section()` from `t_meta.get("subpillars") or bp_data.get("subpillars")` to `bp_data.get("subpillars") or t_meta.get("subpillars")` is **architecturally correct** (dynamic runtime blueprint data *must* override static fallback metadata).
   * **However**, the reason this change was made was to mask the fact that `locales.json` (`t_meta`) contained polluted cement-plant data, and the only reason Starling passed the test afterwards was because `build_client_delivery_suite.py` hardcoded Starling's `subpillars` into `bp_data`!

### 1.3 Production Code & Regression Impact Assessment
* **Core Engine Integrity:** `policy_engine.py`, `taxonomy_resolver.py`, and the core AST rendering primitives were **not** corrupted.
* **Config Loader (`config_loader.py`):** The addition of `_INDUSTRY_ALIASES` and `_normalize_industry_key()` is clean, deterministic, and non-destructive, properly mapping granular vertical names (e.g., `"Banking & FinTech"`, `"Healthcare & Hospitals"`) to canonical actuarial risk profiles (`financial_services`, `healthcare`, etc.).
* **Compiler Precedence (`tomo_asis_ast_compiler.py`):** Preferring `bp_data` (dynamic client payload) over `t_meta` (static locale fallback) is the right design, provided `t_meta` itself is sanitized and `bp_data` is hydrated from real evidence rather than hardcoded `if` statements.

---

## SECTION 2: RESIDUAL HARDCODING IN THE BASELINE (`locales.json`)

### 2.1 Why Cement/Weighbridge Terminology Exists in `engine_config/locales.json`
During earlier phases of engine development, the baseline reference tenant used to calibrate the Tomo 1 AS-IS compiler was a heavy-materials/cement manufacturing enterprise (e.g., industrial weighbridges, automated barrier controls, cement dispatch software, SCADA/PLC networks, and `€ / yr` currency strings). Instead of abstracting those strings into tenant-agnostic architectural templates, a developer dumped the literal forensic output of that cement client into `locales.json` under `tomo_tower_forensic_catalog` (`T1` through `T10`, across `en`, `es`, `pt`, `fr`).

### 2.2 Why the AST Compiler Fell Back to This Text
In `tomo_asis_ast_compiler.py`, `_build_tower_deep_dives_section()` loads `tower_catalog = self._t("tomo_tower_forensic_catalog", {})`. For every tower `t_id`, it merges static defaults (`t_meta = tower_catalog.get(t_id, {})`) with dynamic blueprint payloads (`bp_data = tower_blueprints.get(t_id, {})`).
Whenever a blueprint payload omitted a field—or when `t_meta` took precedence over `bp_data` for `subpillars`—the compiler injected the static `locales.json` catalog directly into the final Word document. Thus, a UK Cloud-Native FinTech (`Starling Bank`) or a US Cloud SaaS provider (`Datadog`) inherited findings about *"Industrial weighbridge control terminals"* and *"cement dispatch software"*.

### 2.3 Cleansing Protocol for Static Fallback Catalogs
`engine_config/locales.json` is a **global, multi-tenant localization dictionary**. It must obey strict tenant neutrality:
1. **Zero Vertical-Specific Nouns:** All references to cement, weighbridges, barriers, plants, factories, or any specific industry vertical must be purged from `tomo_tower_forensic_catalog` across all languages (`en`, `es`, `pt`, `fr`).
2. **Canonical Enterprise Architecture Terminology:** Fallback descriptions in `tomo_tower_forensic_catalog` must use strictly universal, domain-agnostic IT/Security taxonomy aligned with each tower's canonical scope (e.g., for `T10` Legacy & Industrial/Core Systems: *"Core mission-critical legacy platforms, proprietary runtime environments, and high-throughput transactional engines"*).
3. **Parameterized Currency & Metrics:** Static locale catalogs must never hardcode `"75,000 € / yr"`. Any fallback financial metric must be dynamically formatted through the localization engine's `CurrencyContext` using base-currency numeric scalars (`float`) converted by `fx_rate_to_eur`.

---

## SECTION 3: TARGET UNIVERSAL ARCHITECTURE FOR ARTIFACT GENERATION

To guarantee **10.0/10.0 Tier-1 quality** for any company in the world—from a $20M regional SMB to a $500B global conglomerate, in any vertical and any language—without a single hardcoded client branch, the pipeline must operate as a **strict, 5-stage deterministic data transformation pipeline**.

```text
[Stage 1: Raw Evidence] 
   ├── transcription_*.docx (Executive & Technical Interviews)
   ├── assessment_responses.txt (240 KPI Telemetry & Collector Notes)
   └── company_profile.json (Revenue, Employees, Vertical, Locale, Currency)
          │
          ▼
[Stage 2: Evidence Ingestion & Semantic Ledger Hydration]
   ├── Parses KPI scores + collector notes + interview paragraphs
   ├── Maps domain evidence to canonical Towers (T1..T10), Pillars, & Subpillars
   └── Emits: case_input.json (per tower), evidence_vault.json, raptor_tree.json
          │
          ▼
[Stage 3: Actuarial FAIR & Maturity Policy Engine (policy_engine.py)]
   ├── Evaluates exact KPI weights -> Subpillar Scores -> Pillar Scores -> Tower Scores
   ├── Runs deterministic Monte Carlo / FAIR loss calibration scaled by Revenue & Vertical
   └── Emits: run_manifest.json, audit_ledger.json, executive_summary.json
          │
          ▼
[Stage 4: Universal Blueprint Hydrator (Evidence-Driven Synthesis)]
   ├── Combines Policy Engine scores/ALE with extracted Evidence Vault citations
   ├── Hydrates Subpillar inventories, forensic findings, and target horizons dynamically
   └── Emits: blueprint_{T_ID}_payload.json & Tomo 2..N Annex DOCX deliverables
          │
          ▼
[Stage 5: Declarative AST Document Compiler (tomo_asis_ast_compiler.py)]
   ├── Consumes company_profile + policy_engine outputs + blueprint payloads + clean locales.json
   ├── Applies strict CurrencyContext (FX conversion + symbol localization)
   └── Emits: Tomo_1_Informe_Ejecutivo_Comite_Direccion_AS_IS.docx (100% Tenant-Pure)
```

### Exact Data Contracts Between Pipeline Stages

#### A. Raw Evidence Contract (`Input Workspace`)
* `company_profile.json`: Defines `client_name`, `industry`, `annual_revenue_eur`, `employee_count`, `locale`, `currency_code`, `currency_symbol`, `fx_rate_to_eur`, `active_towers`, and `regulatory_frameworks`.
* `assessment_responses.txt`: Contains structured KPI evaluations (`KPI_ID | Score | Status | Collector_Observation_Note`) where `Collector_Observation_Note` holds the specific technological evidence observed in the client's environment.
* `transcription_*.docx`: Unstructured/semi-structured discovery interviews containing verbatim quotes, architectural inventory details, and operational bottlenecks voiced by the client's C-suite and engineering leads.

#### B. Evidence Ledger & Semantic Harvester Contract (`evidence_vault.json` & `case_input.json`)
* **No LLM Hallucination or Client-Name Branching:** A deterministic **Evidence Harvester (`src/assessment_engine/domain/evidence_harvester.py`)** parses `assessment_responses.txt` and `transcription_*.docx`.
* It extracts:
  1. **Quantitative KPI Vector:** Populates `case_input.json` for each tower (`kpi_id`, `value`, `evidence_note`, `transcript_quote`).
  2. **Domain Inventory & Findings Graph (`evidence_vault.json`):** Indexes extracted technical assets (e.g., *PostgreSQL, Envoy, SAP S/4HANA, PACS/HIS, WMS, Core Banking Ledger*) and verbatim findings by `tower_id -> pillar_id -> subpillar_id`.

#### C. Actuarial FAIR & Maturity Policy Engine Contract (`policy_engine.py`)
* Consumes `case_input.json` + `company_profile.json` + `engine_config/towers/{T_ID}/tower_definition_{T_ID}.json`.
* Computes **exact bottom-up hierarchical scores**:
  * $\text{Subpillar Score} = \frac{\sum (\text{KPI Score} \times \text{KPI Weight})}{\sum \text{KPI Weight}}$ (not synthetic `(-1)**s_idx * 0.15` jitter!).
  * $\text{Pillar Score} = \frac{\sum (\text{Subpillar Score} \times \text{Subpillar Weight})}{\sum \text{Subpillar Weight}}$.
  * $\text{Tower Score} = \frac{\sum (\text{Pillar Score} \times \text{Pillar Weight})}{\sum \text{Pillar Weight}}$.
* Computes **Actuarial Risk Exposure (ALE)** per Tower and distributes ALE across Pillars and Subpillars proportionally to their **Risk Deficit Weight** $(5.0 - \text{Score})^\alpha \times \text{CriticalityWeight}$.

#### D. Universal Blueprint Hydrator Contract (`blueprint_{T_ID}_payload.json`)
* Hydrates the exact schema required by both the **Tomo 1 AST Compiler** and the **Specialist Annex Renderers**:
  * `score`, `maturity_band`, `target_score`, `ale` (formatted in client currency via `CurrencyContext`), `horizon`.
  * `inventory`: Synthesized directly from the client's `evidence_vault.json` for that tower.
  * `findings`: Top critical findings extracted from the lowest-scoring KPIs' `evidence_note` and `transcript_quote` entries for that tower.
  * `subpillars`: List of `{id, name, score, finding}` where `score` is the true mathematical subpillar score and `finding` is the specific evidence observation attached to that subpillar's KPIs.
  * `pillars_analysis`: Full pillar breakdown with true scores, risk gaps, and evidence-backed root causes.

#### E. Declarative AST Document Compiler Contract (`tomo_asis_ast_compiler.py`)
* Strictly declarative rendering. Zero business logic, zero ad-hoc math, zero tenant conditionals.
* Validates that all injected strings conform to the target `locale` and `CurrencyContext`.

---

## SECTION 4: DEFINITIVE MULTI-PHASE MASTER REMEDIATION PLAN

We will execute the remediation in **4 surgical, test-gated phases**. No phase may begin until the previous phase passes 100% of unit and functional verification gates.

### PHASE 1: Baseline Sanitization & Currency Engine Hardening
**Objective:** Purge all cement/weighbridge contamination from `engine_config/locales.json` and fix the currency conversion regex in `localization.py`.
1. **Refactor `engine_config/locales.json`:**
   * Audit every entry under `tomo_tower_forensic_catalog` (`T1`..`T10`) across `en`, `es`, `pt`, `fr`.
   * Replace all cement/weighbridge/factory-specific strings in `T10` (and any other contaminated towers) with universal, domain-neutral enterprise architecture taxonomy.
   * Ensure zero Spanish words exist in `en` keys or in Python source code (100% adherence to the **Language Decoupling Law**).
2. **Refactor `src/assessment_engine/infrastructure/localization.py`:**
   * Upgrade `format_currency_text()` to parse and convert **both** suffixed magnitudes (`1.5M €`, `250K EUR`) **and** standard comma/dot-formatted currency literals (`75,000 €`, `120,000 EUR`) using `fx_rate_to_eur`, formatting the output cleanly in the client's target currency symbol and code.
3. **Phase 1 Gate:** Run unit tests verifying zero occurrences of `"weighbridge"`, `"cement"`, or un-converted EUR values across all locales.

### PHASE 2: Rich Multi-Tenant Evidence Fixture Enrichment (`build_synthetic_control_fixture.py`)
**Objective:** Ensure the raw input files (`assessment_responses.txt` and `transcription_*.docx`) for all 5 benchmark clients contain rich, authentic, vertical-specific telemetry mapped to KPIs so the downstream engine can harvest them naturally.
1. **Refactor `scripts/build_synthetic_control_fixture.py`:**
   * Structure `assessment_responses.txt` and `case_input.json` generation so that every KPI answer carries a localized, domain-authentic `observation` / `evidence_note` derived from the client's vertical profile (Banking/FinTech for Starling, Healthcare/Hospital for Rede D'Or, Global Logistics for Geodis, Omnichannel Retail for Chedraui, Cloud SaaS for Datadog).
   * Ensure zero client-specific logic leaks into the core engine; `build_synthetic_control_fixture.py` is strictly the **test fixture generator** that simulates what a human auditor/collector uploads into `input/`.
2. **Phase 2 Gate:** Verify that all 5 synthetic workspaces in `tests/fixtures/synthetic_control_suite/` contain complete, schema-valid raw inputs (`transcription_1`, `transcription_2`, `assessment_responses.txt`, `company_profile.json`).

### PHASE 3: Universal Evidence Harvester & Zero-Hardcoding Delivery Suite (`build_client_delivery_suite.py`)
**Objective:** Completely eradicate `if "Starling" in client_name:` and all hardcoded narratives/math from `scripts/build_client_delivery_suite.py`.
1. **Refactor `scripts/build_client_delivery_suite.py`:**
   * **Delete** the entire `if "Starling" in client_name:` / `else:` block (lines 257–346).
   * **Implement Deterministic Bottom-Up Scoring & Evidence Harvesting:**
     * Parse `assessment_responses.txt` and `transcription_*.docx` (alongside `case_input.json`) to extract the actual per-KPI scores, collector observations, and interview quotes.
     * Compute true mathematical scores at the **Subpillar**, **Pillar**, and **Tower** levels using `tower_definition_{T_ID}.json` KPI-to-subpillar mappings (eliminating the fake `(-1)**s_idx * 0.15` jitter).
     * Allocate Tower ALE across Pillars proportionally to their weighted maturity deficit $(5.0 - \text{PillarScore})$, formatting all monetary figures through `CurrencyContext`.
     * Hydrate `inventory`, `findings`, and `subpillars[].finding` dynamically from the harvested KPI observations and transcript evidence for **any** client.
2. **Phase 3 Gate:** Inspect `scripts/build_client_delivery_suite.py` via AST/grep audit to certify **zero** occurrences of client names (`Starling`, `Rede`, `Geodis`, `Chedraui`, `Datadog`), **zero** hardcoded domain strings, and **100% Technical English** code.

### PHASE 4: Full-Spectrum Compilation & Adversarial Certification (5 Clients × All Deliverables)
**Objective:** Prove that the universal pipeline compiles all deliverables for all 5 global benchmark clients with zero defects, zero cross-tenant leakage, and 10.0/10.0 executive fidelity.
1. **Expand `tests/functional/test_synthetic_control_delivery.py`:**
   * Enforce strict cross-contamination assertions across **all 5 clients**:
     * No cement/weighbridge strings in any client.
     * Each client's Tomo 1 DOCX and Specialist Annexes must contain its own domain terminology (e.g., `Faster Payments` in Starling, `HIS/PACS` or healthcare telemetry in Rede D'Or, `WMS/TMS` in Geodis, `POS/Omnichannel` in Chedraui, `Multi-tenant SaaS/Control Plane` in Datadog) harvested strictly from its input fixtures.
     * Verify currency symbols (`£`/`GBP`, `R$`/`BRL`, `€`/`EUR`, `MXN`, `$`/`USD`) and localized prose (`en`, `pt`, `fr`, `es`, `en`).
     * Verify zero unresolved placeholders (`{{`, `TODO`, `TBD`, `None`, `NaN`) and zero Markdown leakage (`**`, `##`).
2. **Phase 4 Gate:** Execute the complete pytest suite (`tests/unit` + `tests/functional`) and verify 100% green execution.

---
**Awaiting your authorization to execute Phase 1 through Phase 4 under this strict architectural protocol.**