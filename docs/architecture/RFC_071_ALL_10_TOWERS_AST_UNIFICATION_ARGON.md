# RFC 071: Universal Multi-Tenant Telemetry Hydration & Eradication of the Annex Split-Brain (T1–T10 Declarative AST Unification)

**Status:** APPROVED / EMERGENCY EXECUTION  
**Classification:** Tier-1 Enterprise Architecture / Document Compilation Pipeline  
**Governance Standard:** 100% Technical English Codebase | Zero-Legacy Tolerance | Multi-Tenant Agnosticism  

---

## 1. Forensic Root Cause Analysis (RCA) of the Split-Brain

A forensic audit of `working/out/Molins_Entrega_Oficial_Piramide_Tier1/` and the orchestration pipeline (`scripts/build_full_client_delivery_suite.py`) reveals a three-tier architectural fracture:

### 1.1 Stale Artifact Persistence in the Output Directory
In `02_ANEXOS_TECNICOS_ESPECIALISTAS/`, two incompatible document architectures coexisted:
* **Towers 1 & 2 (`Anexo_01_Data_Center_ASIS.docx`, `Anexo_02_Computo_Hibrido_ASIS.docx`):** Compiled via the modern Declarative AST Engine (`compile_asis_docx_via_ast`), exhibiting ~115 KB file sizes, FNMT CERES typography, CMMI V2.0 maturity matrices, and zero raw Markdown leakage.
* **Towers 3 through 10 (`Anexo_03` to `Anexo_10`):** Unpurged legacy artifacts (~295–315 KB) generated on October 30 by the deprecated Markdown-injection compiler. Because the orchestrator did not purge the target directory prior to execution and only overwrote T1 and T2, the legacy files persisted on disk, creating a visual and structural split-brain.

### 1.2 Incomplete Orchestration & Missing Financial Telemetry Hydration
In `scripts/build_full_client_delivery_suite.py`, `compile_and_export_tower(...)` was explicitly invoked **only** for `T1` and `T2`. Towers `T3` through `T10` were excluded from the build script because their raw blueprint JSON payloads (`working/out/molins_baseline_pre_rebuild/T3..T10/*_blueprint.json`) lacked root-level `financial_telemetry` and `annual_revenue` attributes. When passed directly to `compile_asis_docx_via_ast`, the strict domain validator in `src/domain/services/downtime_calibrator.py` raised a `TelemetryResolutionError`.

### 1.3 Asymmetric Payload Injection in Tomo 1 (Consolidated AS-IS Diagnostic)
Because the orchestrator only loaded `t1_payload` and `t2_payload`, it passed an incomplete dictionary (`tower_payloads = {"T1": t1_payload, "T2": t2_payload}`) to `compile_consolidated_asis_tomo1(...)`. Consequently, within Chapter 4 of Tomo 1, Sections 4.1 (T1) and 4.2 (T2) rendered full forensic telemetry from live blueprints, whereas Sections 4.3 through 4.10 fell back to localized static catalog summaries.

---

## 2. Target Architecture: Universal Payload Hydrator & 10-Tower AST Engine

To permanently eliminate this split-brain across all current and future tenants, we introduce a **Universal Multi-Tenant Payload Hydrator** in the application layer and enforce **100% Declarative AST Compilation** across all 10 specialist annexes and Tomo 1.

```
+-----------------------------------------------------------------------------+
|                        GLOBAL TENANT CONTEXT (JSON)                         |
|   (client_name, annual_revenue, downtime_hourly_rate, currency, locale)     |
+--------------------------------------+--------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                 UNIVERSAL MULTI-TENANT PAYLOAD HYDRATOR                     |
|         src/application/services/tower_payload_hydrator.py                  |
|                                                                             |
|  1. Loads raw blueprint payloads for Towers T1..T10 from baseline storage.  |
|  2. Injects/normalizes tenant financial_telemetry (annual_revenue,          |
|     hourly_downtime_rate, currency) into every tower payload.               |
|  3. Enriches metadata (tower_code, canonical title, client identity)        |
|     using localized tower catalog definitions.                              |
+------------------+---------------------------------------+------------------+
                   |                                       |
                   v                                       v
+-------------------------------------+ +-------------------------------------+
|     TOMO 1 AST COMPILER ENGINE      | |   10-TOWER ANNEX AST ORCHESTRATOR   |
|  compile_consolidated_asis_tomo1()  | |    compile_asis_docx_via_ast()      |
|                                     | |                                     |
| - Receives full hydrated dict:      | | - Purges legacy files in            |
|   tower_payloads["T1".."T10"]       | |   02_ANEXOS_TECNICOS_ESPECIALISTAS/ |
| - Renders 100% homogeneous Ch. 4    | | - Compiles Anexos 01 to 10 in       |
|   sections across all 10 towers.    | |   parallel via ProcessPoolExecutor. |
+-------------------------------------+ +-------------------------------------+
```

### 2.1 Universal Multi-Tenant Telemetry Hydrator (`src/application/services/tower_payload_hydrator.py`)
A pure, tenant-agnostic service responsible for merging global tenant context into individual tower blueprint payloads before AST compilation:
* **Financial Telemetry Inheritance:** Ensures `financial_telemetry.annual_revenue_eur` (or tenant currency equivalent), `annual_revenue`, and `downtime_cost_per_hour` are deterministically populated from `global_payload` if omitted in the raw tower JSON. This guarantees `downtime_calibrator.py` never fails on `T3–T10` for any global client.
* **Canonical Tower Registry Mapping:** Maps `T1` through `T10` to their canonical output filenames (`Anexo_01_..._ASIS.docx` through `Anexo_10_..._ASIS.docx`) via `src/domain/catalogs/tower_catalog.py`, eliminating hardcoded filenames in build scripts.
* **Schema Normalization:** Ensures `findings`, `inventory_metrics`, `maturity_assessment`, and `gap_analysis` structures satisfy the strict AST builder contracts across all 10 towers.

### 2.2 Full Tomo 1 Homogeneity (`src/infrastructure/adapters/word_ast/tomo1_ast_builder.py`)
* Tomo 1 receives the complete dictionary of 10 hydrated payloads: `tower_payloads = {f"T{i}": hydrated_payloads[f"T{i}"] for i in range(1, 11)}`.
* Every tower section in Chapter 4 (Sections 4.1 through 4.10) is compiled through the exact same AST node pipeline: Executive Diagnostic Narrative, Key Telemetry & Asset Inventory Table, Forensic Findings Matrix, and Technical Debt / Risk Quantification.

### 2.3 Strict Output Purge & CLI Modularity (`scripts/build_full_client_delivery_suite.py`)
* **Legacy Artifact Purge:** Before compiling annexes, the orchestrator removes any pre-existing `.docx` files in `02_ANEXOS_TECNICOS_ESPECIALISTAS/` to guarantee zero stale artifacts can survive on disk.
* **Fast Modular CLI Execution:** Implements `argparse` with deterministic execution targets:
  * `--only tomo1`: Hydrates all 10 tower payloads in memory and compiles strictly `01_TOMO_01_DIAGNOSTICO_ASIS_CONSOLIDADO.docx` in `< 4 seconds`.
  * `--only annexes`: Purges the annex directory and compiles all 10 specialist annexes (`Anexo_01` to `Anexo_10`) via `compile_asis_docx_via_ast` (supporting parallel execution via `ProcessPoolExecutor`).
  * `--only executive`: Compiles the C-Level Executive Deliverables (Tomo 2 TO-BE, Tomo 3 Roadmap, Tomo 4 Financial Business Case, Executive Presentation).
  * `--all` (default): Executes the complete end-to-end Tier-1 pyramid suite.

---

## 3. Step-by-Step Implementation & Verification Plan

### Step 1: Canonical Annex Metadata & Universal Payload Hydrator
1. Inspect `src/domain/catalogs/tower_catalog.py` and ensure every tower (`T1` to `T10`) defines a canonical annex filename slug (e.g., `Anexo_01_Data_Center_ASIS.docx` to `Anexo_10_Gobierno_IT_ASIS.docx`).
2. Create `src/application/services/tower_payload_hydrator.py` in 100% Technical English:
   * Implement `load_and_hydrate_all_tower_payloads(baseline_dir: Path, global_payload: dict[str, Any], lang: str = "es") -> dict[str, dict[str, Any]]`.
   * Resolve each tower directory (`T1` to `T10`), locate its primary `*_blueprint.json` payload, and deep-merge tenant-level financial telemetry, client identity, and canonical tower metadata.

### Step 2: Upgrade Orchestrator (`scripts/build_full_client_delivery_suite.py`)
1. Refactor `scripts/build_full_client_delivery_suite.py` to:
   * Parse CLI arguments (`--only [tomo1|annexes|executive|all]`, `--workers`).
   * Invoke `load_and_hydrate_all_tower_payloads(...)` to retrieve all 10 hydrated payloads (`T1`–`T10`).
   * Pass all 10 hydrated payloads into `compile_consolidated_asis_tomo1(...)`.
   * Purge stale files in `02_ANEXOS_TECNICOS_ESPECIALISTAS/` and iterate over all 10 towers (`T1` through `T10`), compiling every annex exclusively through `compile_asis_docx_via_ast`.

### Step 3: Defensive AST Hardening for Towers 3 to 10
1. Test-compile `T1` through `T10` via `compile_asis_docx_via_ast`.
2. Verify that any schema variations in `T3`–`T10` blueprints (e.g., dict vs. list representations in `subdomains`, `findings`, or `metrics`) are gracefully normalized by `tower_payload_hydrator.py` or `asis_ast_builder.py` without falling back to placeholders.

### Step 4: Automated Forensic Verification Gates
1. **Execution Gate 1 (`--only annexes`):**
   * Verify all 10 files (`Anexo_01` through `Anexo_10`) exist in `02_ANEXOS_TECNICOS_ESPECIALISTAS/`.
   * Verify modification timestamps are current (zero October 30 legacy files).
   * Verify homogeneous AST file sizes (~105 KB – 145 KB) and identical FNMT CERES XML styling across all 10 annexes.
2. **Execution Gate 2 (`--only tomo1`):**
   * Verify `01_TOMO_01_DIAGNOSTICO_ASIS_CONSOLIDADO.docx` compiles in `< 4 seconds` and integrates live telemetry across all 10 towers in Chapter 4.
3. **Unit & Integration Test Suite:**
   * Add `tests/unit/application/test_tower_payload_hydrator.py` verifying that `T1`–`T10` payloads are deterministically hydrated and pass `downtime_calibrator` validation for any arbitrary tenant.