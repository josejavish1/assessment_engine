# ARGON TIER-1 FORENSIC AUDIT & STRUCTURAL REMEDIATION PLAN (ITERATION 3)
**Target:** Tower 2 (Hybrid Compute & Platforms) & Transversal Engine Standards
**Author:** Red Team Senior Systems Architect / Principal Refactoring Lead
**Status:** Approved for Implementation (Zero-Trust, Zero-Hardcoding, Pure Ontological Governance)

---

## Executive Summary
This document establishes the exhaustive Root Cause Analysis (RCA) and Tier-1 architectural remediation plan for the 6 critical and substantive findings identified during the forensic audit of the newly regenerated Tower 2 deliverable (`Molins_202610_Anexo_T2_ASIS_Regenerado.docx`).

Every remediation in this plan is designed under strict enterprise engineering invariants:
1. **Zero Hardcoded Strings in Code:** 100% Technical English for all engineering artifacts (code, variables, docstrings, tests). All language data resides strictly in declarative localization registries (`engine_config/locales.json`, `taxonomy_multilingual.json`).
2. **Zero Domain Contamination:** Core compiler strategies and domain models must never assume tower-specific or client-specific concepts.
3. **Mathematical Closure & Single Source of Truth (SSOT):** Mathematical consistency across all chapters (ALE, P90 VaR, Max SLE, Hourly Rate).
4. **Algorithmic Adaptability:** Algorithms must scale dynamically to any portfolio size, industry vertical, and financial scale without linear or static threshold hacks.

---

## 🚨 Finding 1: Raw English KPI and Factor Names in Section 2.4 (P47 to P51)

### 1. The Symptom
In Chapter 2, Section 2.4 (*Capacidades Evaluadas y Cálculo del Score*, Paragraphs 47 to 51), each pillar description begins in formal Spanish, but then lists all of its evaluation factors in raw, untranslated English:
* **P47 (Fundamentos de Cómputo):** *«...analizando críticamente factores clave como **Compute Estate Standardization (Clusters, Hosts & Hardware Baselines); Compute Lifecycle Management (Patching, Firmware & OS Upgrades); Capacity & Performance Management (CPU/RAM Overcommit & Saturation)** y **Compute Platform Availability (Host HA & Concurrent Maintainability)**.»*
* **P48 (Contenedores):** *«...factores clave como **Core Kubernetes Services (Ingress, Registry, Certificates & Storage Classes); Cluster Lifecycle Management (Version Upgrades & Deprecations)**...»*
* **P49 (Cloud Híbrido):** *«...factores clave como **Cloud Landing Zone Architecture & Multi-Account Structure; Cloud Governance Guardrails & Technical Policy Enforcement (Policy-as-Code)**...»*
* **P50 (Automatización):** *«...factores clave como **Infrastructure as Code (IaC) Provisioning Coverage; Service Catalog Maturity & Self-Service Provisioning Lead Time; Golden Image Pipeline & Standard Baseline Configuration**...»*
* **P51 (Operaciones):** *«...factores clave como **Platform Observability Coverage (Metrics, Logs, Traces & Alerts); Platform Service Level Objectives (SLOs) & Error Budget Tracking**...»*

### 2. Root Cause Analysis (RCA)
* **Location:** `src/assessment_engine/adapters/compilers/ast_appendices_builder.py`, lines 160–205 in function `build_cmmi_methodology_and_capabilities`.
* **Mechanism:**
  The loop iterating over `kpi_list` extracted `k.get("kpi_name", "").strip()` directly from the raw tower definition JSON (`engine_config/towers/{tower_id}/tower_definition_{tower_id}.json`). In `tower_definition_T2.json`, all KPI definitions are authored in canonical English.
  The compiler appended `raw_kname` directly to `distinct_names` without passing it through `TaxonomyResolver.resolve_capability_name(raw_kname, default=raw_kname, locale=meta_lang)`.
* **Architectural Flaw:**
  Bypassing the localization resolution layer (`TaxonomyCatalogPort`). Raw catalog definitions must never leak to client-facing AST nodes without locale normalization.

### 3. Tier-1 Structural Remediation
1. **Enforce Localization in `ast_appendices_builder.py`:**
   In `build_cmmi_methodology_and_capabilities`, resolve each KPI name against the multilingual taxonomy catalog:
   ```python
   for k in kpi_list:
       raw_kname = k.get("kpi_name", "").strip()
       kpi_id = k.get("kpi_id", "").strip()
       localized_kname = resolver.resolve_capability_name(
           raw_kname, default=raw_kname, locale=meta_lang
       )
       if localized_kname and localized_kname not in distinct_names:
           distinct_names.append(localized_kname)
   ```
2. **Catalog Parity in `taxonomy_multilingual.json`:**
   Ensure all canonical KPI names and capability identifiers for Tower 2 map to their official localized translations in `engine_config/taxonomy_multilingual.json` for all supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`).
3. This guarantees that Section 2.4 renders 100% in the target deliverable language for any tower and any organization.

---

## 🚨 Finding 2: Algebraic Formula with Underscores in Section 4.1 (P105)

### 1. The Symptom
In Chapter 4, Section 4.1, Paragraph 105:
> *«ALE = LEF × (Duración_Parada × Tasa_Erosión_Horaria + Esfuerzo_Recuperación + Penalizaciones_SLA)»*

The document exposes programming variable names with underscores (`_`) and academic algebraic acronyms (`ALE`, `LEF`) directly to business executives.

### 2. Root Cause Analysis (RCA)
* **Location:** `engine_config/locales.json`, key `annex_ch4_receptors["AVAILABILITY_OUTAGE"]["formula_expression"]`.
* **Mechanism:**
  The template string was authored using pseudo-code syntax. When `BaseReceptorStrategy` formatted and rendered `formula_expression`, it displayed the raw equation with underscores.
* **Architectural Flaw:**
  Violation of the **Plain Business Language Law**. Algebraic symbols and code-like syntax belong in the computational domain model, not in executive Board-level deliverables.

### 3. Tier-1 Structural Remediation
1. **Declarative Business Equation in `locales.json`:**
   Update `formula_expression` across all receptor types in `engine_config/locales.json`:
   * `es`: `"Pérdida Anual Estimada = Probabilidad de Avería al Año × (Coste de Parada de Planta + Restitución de Activos + Guardias Técnicas)"`
   * `en`: `"Estimated Annual Loss = Annual Outage Probability × (Operational Stoppage Cost + Asset Remediation + Emergency Support)"`
2. This eliminates all underscores and algebraic acronyms, aligning the financial methodology presentation with intuitive executive language.

---

## ⚠️ Finding 3: Missing Diacritical Accents in Chapter 3.2 Detailed Findings (P88, P98, P99)

### 1. The Symptom
In Chapter 3, Section 3.2 (*Diagnóstico Técnico Detallado por Capacidad*), formal technical prose contains missing Spanish accents:
* **P88 (Cloud Híbrido):** *«...gobernanza **tecnica**...»* $\rightarrow$ Missing accent on **técnica**.
* **P98 (Operaciones):** *«...**proyeccion** de capacidad con modelado **analitico** limitado y **gestion** basada...»* $\rightarrow$ Missing accents on **proyección**, **analítico**, **gestión**.
* **P99 (Operaciones):** *«...**absorcion** **automatica** de cargas ante contingencias de infraestructura **fisica**...»* $\rightarrow$ Missing accents on **absorción**, **automática**, **física**.

### 2. Root Cause Analysis (RCA)
* **Location:** `src/assessment_engine/adapters/compilers/payload_to_ast.py`, method `_build_detailed_findings_log`, and `working/molins/T2/blueprint_t2_payload.json`.
* **Mechanism:**
  The health check findings in `blueprint_t2_payload.json` were authored or synthesized without proper UTF-8 diacritics. Although `payload_to_ast.py` possesses a diacritic restoration helper (`restore_locale_diacritics`), it was applied selectively to chapter headings and summary callouts, but was NOT invoked over the health check finding body paragraphs in Section 3.2.
* **Architectural Flaw:**
  Inconsistent application of text sanitization and diacritic restoration across AST node builders.

### 3. Tier-1 Structural Remediation
1. **Comprehensive Diacritic Restoration Gatekeeper:**
   In `payload_to_ast.py`, ensure that all prose paragraphs generated from health checks (`finding_text`, `risk_text`, and capability introduction summaries) pass through `restore_locale_diacritics(text, meta_lang)` prior to `ParagraphNode` instantiation.
2. **Payload Hygiene:**
   Correct the diacritics in `blueprint_t2_payload.json` for pillars P3 and P5 so that the Single Source of Truth is clean at rest.

---

## ⚠️ Finding 4: False 0.5h Plant Stoppage Attributed to Lack of SLOs in Risk Card RVS15 (Table 18)

### 1. The Symptom
In Risk Card RVS15 (*Objetivos de Nivel de Servicio (SLOs) y Presupuestos de Error*, Table 18), the cost justification states:
> *«Ante una contingencia imprevista, se estima una **parada técnica de unas 0,5 horas** con un impacto por evento de **15.262 €**...»*

Lacking a monitoring dashboard with SLOs and Error Budgets is a platform reliability and observability governance gap; it does not stop factory operations or weighbridge gates for 30 minutes.

### 2. Root Cause Analysis (RCA)
* **Location:** `src/assessment_engine/domain/actuarial/finding_archetype_resolver.py`, `src/assessment_engine/domain/actuarial/plain_language_narrative.py`, and `working/molins/T2/blueprint_t2_payload.json`.
* **Mechanism:**
  In `blueprint_t2_payload.json`, RVS15 had `loss_physics = "PLATFORM_DEGRADATION"` and an explicit `recovery_time_hours = 0.5`. In `plain_language_narrative.py`, any finding with `rto_hours > 0` that was not FinOps or Engineering Friction fell into the outage minor branch, printing *«se estima una parada técnica de unas 0,5 horas»*.
* **Architectural Flaw:**
  **Physical Archetype Misclassification.** Platform governance and reliability telemetry deficiencies belong strictly to `ENGINEERING_VELOCITY_FRICTION` (measuring engineering toil, manual incident triage, and reliability analysis hours), with `allows_downtime_burn = False` (0.0h of plant stoppage).

### 3. Tier-1 Structural Remediation
1. **Sub-Pillar Admissibility Enforcement:**
   In `finding_archetype_resolver.py`, ensure that reliability governance and SLO tracking findings in `T2.P5` resolve to `ENGINEERING_VELOCITY_FRICTION` or governance telemetry, setting `default_rto_hours = 0.0`.
2. **Payload Classification Update:**
   Update RVS15 in `blueprint_t2_payload.json` to have `loss_physics: "ENGINEERING_VELOCITY_FRICTION"` and `rto_hours: 0.0`.
3. This ensures RVS15 renders an engineering toil narrative (*«horas de ingeniería interna y soporte de fiabilidad»*) rather than asserting 30 minutes of factory shutdown.

---

## 🔍 Finding 5: Missing Comma in P90 Callout P127

### 1. The Symptom
In Chapter 4, Section 4.3 (Paragraph 127):
> *«...soporte prioritario de fabricantes **guardias de soporte 24/7 y** peritaje de restitución operativa.»*

Missing separating comma between *"fabricantes"* and *"guardias"*.

### 2. Root Cause Analysis (RCA)
* **Location:** `engine_config/locales.json`, key `p90_callout_p3`.
* **Mechanism:**
  A typographical omission in the localization template string.
* **Architectural Flaw:**
  Punctuation defect in the static localization template.

### 3. Tier-1 Structural Remediation
1. **Template Correction in `locales.json`:**
   In `engine_config/locales.json`, update `p90_callout_p3`:
   * `es`: *«...soporte prioritario de fabricantes, guardias de soporte 24/7 y peritaje de restitución operativa).»*
   * Verify and ensure parity in the English template (`p90_callout_p3`).

---

## 🔍 Finding 6: Conjunction Cacophony in Executive Summary P21

### 1. The Symptom
In Chapter 1, Paragraph 21:
> *«...alcanza 2,75 sobre 5,0 (**Fundamentos de Cómputo y Virtualización y Operaciones de Plataforma, Observabilidad y Confiabilidad**)... en **Plataforma de Contenedores y Operaciones Kubernetes y Automatización, Aprovisionamiento y Autoservicio (1,00 sobre 5,0)**.»*

Joining compound pillar names that already contain internal conjunctions (*«Cómputo **y** Virtualización»*, *«Contenedores **y** Kubernetes»*, *«Automatización **y** Autoservicio»*) using a simple `" y "` creates an ungrammatical repetition of *"y ... y ... y ..."*.

### 2. Root Cause Analysis (RCA)
* **Location:** `src/assessment_engine/adapters/compilers/payload_to_ast.py`, function `extract_dimension_boundary_profile`.
* **Mechanism:**
  When multiple tied pillars were detected, the string construction joined them with:
  ```python
  weakest_name = "; ".join(weakest_names[:-1]) + and_connector + weakest_names[-1]
  ```
  Where `and_connector` was `" y "`. When the preceding element ends without a semicolon, it produces *«Kubernetes y Automatización»*, which collides with the internal *"y"* of both titles.
* **Architectural Flaw:**
  Insufficient syntactic separation for compound nouns with internal copulative conjunctions.

### 3. Tier-1 Structural Remediation
1. **Syntactic Conjunction Normalization:**
   In `payload_to_ast.py` (`extract_dimension_boundary_profile`), when joining multiple compound pillar names:
   ```python
   if len(tied_weakest) > 1:
       weakest_names = [d[0] for d in tied_weakest]
       weakest_name = "; ".join(weakest_names[:-1]) + f"; {and_connector.strip()} " + weakest_names[-1]
   ```
   Result: *«...en Plataforma de Contenedores y Operaciones Kubernetes; y Automatización, Aprovisionamiento y Autoservicio (1,00 sobre 5,0).»*
2. This establishes formal, unambiguous grammatical punctuation across all multi-pillar tie scenarios.

---

## Verification Matrix & Quality Gate Checklist

| Finding | Target File | Verification Metric | Pass Criteria |
| :--- | :--- | :--- | :--- |
| **1. Unlocalized KPIs in 2.4** | `ast_appendices_builder.py` | AST Inspection of P47–P51 | Zero raw English KPI names; all factors translated via `TaxonomyResolver`. |
| **2. Formula Underscores** | `locales.json` | AST Inspection of P105 | Displays plain business formula without `_`, `ALE`, or `LEF`. |
| **3. Missing Accents** | `payload_to_ast.py` / Payload | Text Inspection of P88, P98, P99 | Accents restored on *técnica, proyección, analítico, gestión, absorción, automática, física*. |
| **4. False SLO Outage** | `finding_archetype_resolver.py` / Payload | Risk Card RVS15 Row 4 Inspection | Displays engineering toil narrative; 0.0h plant downtime. |
| **5. Missing Comma in P127** | `locales.json` | Text Inspection of P127 | Comma present: *«...soporte de fabricantes, guardias de soporte 24/7...»*. |
| **6. Conjunction Cacophony** | `payload_to_ast.py` | Text Inspection of P21 | Semicolon separation: *«...Kubernetes; y Automatización...»*. |
