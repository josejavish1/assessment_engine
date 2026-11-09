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
id: ADVERSARIAL_ARCHITECTURAL_AUDIT_2026
title: "Exhaustive Adversarial Architectural Audit: Assessment Engine Core"
author: "gemini-4-argon (Distinguished Staff Architect & Chief Quality Auditor)"
status: "ACTION_REQUIRED"
classification: "INTERNAL_ENGINEERING_STRICT"
target_module: "src/assessment_engine/"
mandate_compliance:
  scale_invariance: "FAILED (Hardcoded Topology Detected)"
  linguistic_purity: "FAILED (Spanish Tokens & Regex Detected)"
  exception_hygiene: "FAILED (20+ Bare Pass Blocks)"
---

# Executive Summary: Adversarial Audit Verdict

An exhaustive static and semantic evaluation of the 263 modules within `src/assessment_engine/` reveals that while the core domain schemas have progressed toward decoupling, **the application, adapter, and infrastructure layers harbor severe architectural anti-patterns**. 

To certify this engine for multi-tenant, scale-agnostic global deployments ($20M SMB to $500B+ Global Tier-1 across arbitrary verticals), we must maintain zero tolerance for heuristic string scraping, hardcoded topology (`T1`–`T10`), linguistic contamination, and silent failure states.

**Current Production Readiness Score:** **6.8 / 10.0 (HOLD FOR REMEDIATION)**

---

# 1. Telemetry Triage & False-Positive Calibration

Before categorizing active defects, an adversarial auditor must separate true architectural violations from static-scanner false positives:

* **FALSE POSITIVE (`tenant_leakage` -> token `"cement"`):** All 20 flagged instances of `"cement"` are substring matches inside the English words `replacement` and `replacements` (e.g., `direct_replacement_cost`, `template_replacements`). **Verdict:** Zero vertical leakage of "cement/manufacturing" in those specific lines.
* **TRUE POSITIVE (`tenant_leakage` via `render_tower_annex_from_template.py`):** Line 613 reveals `replacements.get("[Fecha]")` alongside `[Date]`. While not a vertical leak, this is a **Linguistic Contamination** violation inside a rendering adapter.
* **META-TOOLING EXEMPTION (`spanish_diacritics` in linters):** Occurrences of Spanish tokens inside `enforce_english_comments.py`, `linguistic_guardrail.py`, and `comment_quality.py` exist *specifically to detect and block* non-English strings. However, hardcoding raw diacritics inside `.py` source files triggers self-flagging during AST audits.

---

# 2. Categorized Architectural Anti-Patterns & Remediations

## TIER 1: CRITICAL SEVERITY (Immediate Blockers to Multi-Tenancy & Scale)

### 1.1. Hardcoded Tower Topology & Semantic Split-Brain (`T10`, `T2.P4`)
* **Locations:**
  * `src/assessment_engine/application/services/epistemic_synthesizer.py` (Line 46)
  * `src/assessment_engine/application/services/tower_payload_hydrator.py` (Lines 139, 758, 842, 1008)
  * `src/assessment_engine/infrastructure/policies/deduplication.py` (Line 87)
  * `src/assessment_engine/infrastructure/text_utils.py` (Line 324)
  * `src/assessment_engine/infrastructure/epistemic_graph_service.py` (Line 65)
* **The Architectural Defect:**
  The codebase hardcodes tower identifiers (`"T10"`, `"T2.P4"`) directly into control-flow logic, dictionary mappings, and conditional branches. Worse, **there is an ontological split-brain regarding what `T10` actually represents**:
  * In `epistemic_synthesizer.py:46`, `T10` is mapped to `"modernization", "legacy", "iseries", "as400", "mainframe"`.
  * In `tower_payload_hydrator.py:139 & 1008`, `T10` is mapped to `"Mission-Critical Operations & Local Infrastructure"` and `"TIER_3_EDGE_DISTRIBUTION"`.
  * In `text_utils.py:324`, `T10` is hardcoded in Spanish as `("10", "Sistemas_Expedicion_Operaciones")`.
* **Why It Threatens the Architecture:**
  1. **Destroys Vertical & Scale Agnosticism:** A cloud-native SaaS client has no "Edge Distribution Facilities" or "AS/400 Mainframes", and may have 6 towers or 14 towers instead of 10.
  2. **Silent Data Corruption:** Because `epistemic_synthesizer` thinks `T10` is Legacy Mainframes while `tower_payload_hydrator` thinks `T10` is Edge/Facility Operations, cross-tower risk synthesis and financial rollups will hallucinate hybrid failure modes.
* **Tier-1 Remediation Plan:**
  * **Eradicate `T1..T10` literals from all `.py` files.**
  * Define a declarative `TopologyManifest` (loaded from tenant configuration / ontology schema) where each tower declares its `domain_archetype` (e.g., `EDGE_OPERATIONS`, `LEGACY_CORE`, `CLOUD_PLATFORM`), `tier_classification`, and `canonical_slug`.
  * Refactor `tower_payload_hydrator.py` and `deduplication.py` to evaluate `tower.archetype == DomainArchetype.EDGE_OPERATIONS` instead of `if code_u == "T10" or "edge" in code_u.lower()`.

---

### 1.2. Bilingual & Legacy Spanish Contamination in Core Logic
* **Locations:**
  * `src/assessment_engine/infrastructure/text_utils.py` (Line 324: `"T10": ("10", "Sistemas_Expedicion_Operaciones")`)
  * `src/assessment_engine/infrastructure/policies/deduplication.py` (Line 87: `if "platform" in p_name or "plataforma" in p_name or p_id == "T2.P4":`)
  * `src/assessment_engine/adapters/render_tower_annex_from_template.py` (Line 613: `replacements.get("[Fecha]")`)
* **The Architectural Defect:**
  Business logic and infrastructure utilities contain hardcoded Spanish strings (`"Sistemas_Expedicion_Operaciones"`, `"plataforma"`, `"[Fecha]"`).
* **Why It Threatens the Architecture:**
  Violates Mandate #2 (100% Technical English in `.py` files; localization strictly in `locales.json`). Embedding `"plataforma"` in `deduplication.py` couples deduplication policies to Spanish/English string matching rather than canonical ontological IDs.
* **Tier-1 Remediation Plan:**
  * Delete the hardcoded tuple table in `text_utils.py:324` and resolve file/directory naming via `locales.json` or the tenant's `TopologyManifest`.
  * In `deduplication.py:87`, remove substring checks (`"platform"`, `"plataforma"`) and `"T2.P4"`. Deduplicate strictly via structural graph equivalence or canonical capability taxonomy tags.
  * In `render_tower_annex_from_template.py:613`, inject localized template tokens from the active locale profile (`locale_config.template_tokens.date_placeholder`).

---

## TIER 2: HIGH SEVERITY (Epistemic Fragility & Silent Failures)

### 2.1. Heuristic Keyword Scraping in Markdown & Domain Adapters
* **Locations:**
  * `src/assessment_engine/adapters/generate_asis_markdown_modules.py` (Lines 344–353)
  * `src/assessment_engine/domain/schemas/common.py` (Line 92)
* **The Architectural Defect:**
  `generate_asis_markdown_modules.py` inspects rendered prose strings using substring searches (`"ALE" in text`, `"inaction" in text.lower()`, `"maturity" in text.lower()`, `"fair" in text.lower()`) and a `legacy_keywords` dictionary to decide whether financial exposure or maturity sections exist in a narrative block.
* **Why It Threatens the Architecture:**
  This is the exact same anti-pattern we just eradicated in RTO assignment. Scraping generated prose to infer domain state creates a brittle feedback loop:
  1. If a localized report uses a different term or phrasing, the substring check fails and the adapter either drops or duplicates sections.
  2. It violates unidirectional data flow (Domain State $\rightarrow$ AST $\rightarrow$ Renderer). A renderer must never parse its own text output to guess what data was passed to it.
* **Tier-1 Remediation Plan:**
  * Replace prose scraping in `generate_asis_markdown_modules.py` with explicit boolean flags or typed fields on the input DTO/AST (`payload.has_quantified_ale: bool`, `payload.has_maturity_assessment: bool`, `payload.cost_of_inaction_usd: Optional[Decimal]`).
  * In `domain/schemas/common.py:92`, audit the `phrase.lower() in text.lower()` validator. If it is enforcing forbidden boilerplate phrases, bind it to a compiled regex or externalized policy ruleset rather than ad-hoc inline substring iteration.

---

### 2.2. Widespread Exception Suppression (`bare_pass_exception`)
* **Locations:** 20 instances across critical paths:
  * **Payload & Synthesis Core:** `build_global_report_payload.py` (1433, 1438), `tower_payload_hydrator.py` (694, 699), `run_executive_annex_synthesizer.py` (810, 822), `run_intelligence_harvesting.py` (745)
  * **AST & Document Compilers:** `payload_to_ast.py` (1176), `tomo_asis_ast_compiler.py` (408), `in_memory_asis_compiler.py` (543), `asis_docx_primitives.py` (104), `render_tower_blueprint.py` (1264)
  * **Infrastructure Registry:** `infrastructure/artifacts/registry.py` (68, 80, 84, 120)
* **The Architectural Defect:**
  `except ...: pass` blocks swallow runtime exceptions without structured logging, telemetry counters, or fallback state verification.
* **Why It Threatens the Architecture:**
  In financial risk modeling (FAIR/ALE calculations) and executive document compilation, silent exception swallowing causes **Split-Brain State & Silent Data Truncation**. If `tower_payload_hydrator.py` fails to parse a metric at line 694 and hits `pass`, the engine silently emits a `$0` exposure or omits an entire architectural annex without alerting the operator or halting the pipeline.
* **Tier-1 Remediation Plan:**
  * **Ban `except ...: pass` via AST lint gate.**
  * **In Domain/Application Hydrators (`tower_payload_hydrator.py`, `build_global_report_payload.py`):** Replace with explicit typed exception handling (`except (KeyError, ValueError, ValidationError) as exc:`). Log a structured warning (`logger.warning("Failed to hydrate metric", extra={...})`) and append a `HydrationWarning` to the payload's epistemic audit trail, or fail-fast if in strict mode.
  * **In Infrastructure (`registry.py`):** If suppressing `FileNotFoundError` during cleanup, use `contextlib.suppress(FileNotFoundError)` explicitly—never a bare `pass` on broad exception classes.

---

## TIER 3: MEDIUM SEVERITY (Fixture Coupling & Guardrail Hygiene)

### 3.1. Hardcoded Topologies in Smoke Generators & Legacy Ingestion Cleaners
* **Locations:**
  * `src/assessment_engine/application/tools/generate_smoke_data.py` (Line 154: `"T10": 3.2`)
  * `src/assessment_engine/application/bootstrap/bootstrap_tower_from_matrix.py` (Lines 165–178: `_get_legacy_ingestion_cleaner()`)
* **The Architectural Defect:**
  `generate_smoke_data.py` hardcodes a 10-tower fixture structure, and `bootstrap_tower_from_matrix.py` relies on a `_get_legacy_ingestion_cleaner()` regex scrubber to strip repeated phrases from legacy matrices.
* **Why It Threatens the Architecture:**
  If smoke tests only test `T1..T10`, CI/CD never validates scale invariance (e.g., a 3-tower SMB tenant or a 25-tower global conglomerate). Furthermore, legacy ingestion regex cleaners inside bootstrap services often harbor hidden tenant-specific assumptions.
* **Tier-1 Remediation Plan:**
  * Parameterize `generate_smoke_data.py` to generate $N$ dynamic towers from an arbitrary ontology profile (testing both $N=3$ SMB and $N=15$ Tier-1 Enterprise topologies).
  * Extract `_get_legacy_ingestion_cleaner()` rules out of Python code and into an optional, explicitly versioned ingestion profile configuration.

---

### 3.2. Self-Contaminating Linguistic Guardrails (Spanish Literals in `.py` Probes)
* **Locations:**
  * `src/assessment_engine/application/tools/enforce_english_comments.py` (Lines 71–141)
  * `src/assessment_engine/infrastructure/auditor/probes/comment_quality.py` (Lines 23–50)
  * `src/assessment_engine/domain/linguistic_guardrail.py` (Line 34)
* **The Architectural Defect:**
  The auditor probes and comment enforcers embed literal Spanish words (`"función"`, `"método"`, `"ejecución"`) and diacritic regexes (`r"[áéíóúüñÁÉÍÓÚÜÑ¿¡]"`) directly inside `.py` files.
* **Why It Threatens the Architecture:**
  Any zero-tolerance static scanner inspecting `.py` files for Spanish words or non-ASCII diacritics will perpetually flag the auditor modules themselves, creating noise that masks real regressions.
* **Tier-1 Remediation Plan:**
  * Externalize forbidden word lists (`es_stopwords`, `de_stopwords`, `banned_hype_terms`) into `src/assessment_engine/infrastructure/auditor/rules/linguistic_rules.json` (or `locales.json`).
  * Express Unicode character ranges in `.py` regexes using strictly ASCII hex/Unicode escape sequences (e.g., `r"[\u00c0-\u00ff\u00bf\u00a1]"` instead of literal `áéíóúñ¿¡`). This guarantees 100% ASCII/English purity across every single `.py` file in the repository.

---

# 3. Executive Remediation Roadmap (Path to 10.0/10 Certification)

To achieve **10.0/10 Global Production Certification**, engineering execution must proceed in four deterministic, atomic phases before any new feature development:

### Phase 1: Ontological & Topological Decoupling (Eradicate `T1`–`T10`)
1. Remove all hardcoded `"T10"` and `"T2.P4"` references across `epistemic_synthesizer.py`, `tower_payload_hydrator.py`, `deduplication.py`, `epistemic_graph_service.py`, and `text_utils.py`.
2. Resolve the `T10` split-brain (Legacy Mainframe vs. Edge/Facility Operations) by routing all domain logic through `TowerConfig.domain_archetype` and `TowerConfig.tier_level` loaded dynamically from the tenant's topology manifest.
3. Update docstrings in `universal_payload_enricher.py` and `risk_ontology.py` to use generic domain identifiers (e.g., `'DOM-CORE-01'`) rather than legacy `'T1'..'T10'` conventions.

### Phase 2: 100% Linguistic Purification
1. Strip `"Sistemas_Expedicion_Operaciones"` from `text_utils.py:324`, `"plataforma"` from `deduplication.py:87`, and `"[Fecha]"` from `render_tower_annex_from_template.py:613`.
2. Migrate all Spanish stopwords and regex patterns out of `enforce_english_comments.py`, `comment_quality.py`, and `linguistic_guardrail.py` into external JSON rule manifests, replacing inline diacritics with `\uXXXX` escapes.

### Phase 3: Elimination of Prose Scraping in Renderers
1. Refactor `generate_asis_markdown_modules.py` (Lines 344–353) to inspect strongly-typed AST/DTO properties rather than scraping rendered strings for `"ALE"`, `"Loss Exposure"`, `"inaction"`, or `"maturity"`.
2. Delete the `legacy_keywords` lookup table from the Markdown generator.

### Phase 4: Exception Hygiene & Telemetry Hardening
1. Audit and eliminate all 20 `bare_pass_exception` blocks across `adapters/`, `application/`, and `infrastructure/`.
2. Replace every silent `pass` with either:
   * Explicit `contextlib.suppress(SpecificIdempotentError)` for benign I/O cleanup in `registry.py`.
   * Structured warning emission + epistemic audit logging for hydration/compilation fallbacks in `tower_payload_hydrator.py`, `build_global_report_payload.py`, and AST compilers.
3. Enable a strict AST CI gate that fails the build on any `ExceptHandler` containing a bare `Pass` node, any non-ASCII literal in `.py` files, or any hardcoded `T[0-9]+` regex match.