---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain
- src/assessment_engine/application
- src/assessment_engine/mcp_server.py
- src/assessment_engine/domain/schemas
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# System Architecture: Assessment Engine

Canonical architectural specification of the `assessment-engine` platform. This document defines the system topology, execution boundaries, data pipelines, and strict engineering invariants for autonomous AI agents and runtime systems.

---

## 1. Architectural Topology: Ports and Adapters (Hexagonal)

The platform strictly decouples domain logic, deterministic pipeline orchestration, and presentation compilation into clear hexagonal layers:

```
+---------------------------------------------------------------------------------------+
|                                ADAPTERS & PRESENTATION                                |
|  CLI (cli.py)  |  FastMCP Server (mcp_server.py)  |  AST Compilers (docx_compiler.py) |
+---------------------------------------------------------------------------------------+
                                          |
                                          v (Drives)
+---------------------------------------------------------------------------------------+
|                                  APPLICATION LAYER                                    |
| Orchestrators: run_tower_pipeline.py, run_global_pipeline.py, run_commercial_pipeline.py|
| Synthesizers:  run_tower_blueprint_engine.py, run_executive_annex_synthesizer.py      |
| Computation:   build_case_input.py, run_scoring.py, run_evidence_analyst.py           |
+---------------------------------------------------------------------------------------+
                                          |
                                          v (Enforces)
+---------------------------------------------------------------------------------------+
|                                    DOMAIN LAYER                                       |
| Schemas:   blueprint.py, global_report.py, commercial_report.py, workspace_contracts.py|
| Actuarial: bayesian_fair_copula_engine.py, euler_allocator.py, downtime_calibrator.py |
| Taxonomy:  finding_archetype_resolver.py, scale_engine.py                             |
+---------------------------------------------------------------------------------------+
                                          |
                                          v (Calls)
+---------------------------------------------------------------------------------------+
|                                INFRASTRUCTURE LAYER                                   |
| AI Client:       Vertex AI (Gemini 3.1 Pro Preview) via ai_client.py                  |
| Epistemic Graph: SQLite Event-Sourcing Ledger (epistemic_graph.py)                     |
| Storage:         WorkspaceManager (workspaces/<client_id>/, working/out/)             |
| Declarative Config: engine_config/ (enterprise_registry, locales, taxonomy)           |
+---------------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Invariants

Autonomous agents operating on this codebase MUST uphold the following architectural axioms:

1. **Top-Down Monism (SSOT):** High-level deliverables (Tomo 1 Consolidated Diagnostic, Commercial Action Plan) derive strictly from detailed tower blueprints (`blueprint_<tower>_payload.json`). Direct calculation or mutation of business metrics in presentation layers is strictly prohibited.
2. **Contract-First Boundaries:** Every inter-module transition is mediated by typed Pydantic models declared in `src/assessment_engine/domain/schemas/`.
3. **Deterministic Orchestration, LLM Synthesis:** Topological sorting, file I/O, data validation, and numerical modeling (TCO + FAIR Monte Carlo) execute deterministically in Python. LLMs function exclusively as bounded semantic synthesis engines constrained by JSON schemas.
4. **Exclusive DOCX Monism:** All customer-facing deliverables compile strictly to Microsoft Word (`.docx`) through the OpenXML AST compiler (`docx_compiler.py`, `tomo_asis_ast_compiler.py`). Generation of PDF or ephemeral web presentations is strictly prohibited.
5. **Zero-Entropy Ephemeral Isolation:** Dynamic execution artifacts must isolate in `working/out/<client_id>/` or `workspaces/<client_id>/`. Source trees and documentation folders must remain free of transient outputs.

---

## 3. End-to-End Pipeline Execution DAG

The execution lifecycle transitions through three sequential, dependency-ordered phases:

```
[Customer Evidence: .docx, .txt, .xlsx] + [Methodological Config: engine_config/]
                                 |
                                 v (Optional Upstream Enrichment)
             run_intelligence_harvesting.py --> [ client_intelligence.json ]
                                 |
+--------------------------------v-----------------------------------------------------+
| PHASE 1: SINGLE-TOWER EVALUATION PIPELINE (run_tower_pipeline.py --tower Txx)         |
+--------------------------------------------------------------------------------------+
| 1. build_case_input.py           --> [ case_input.json ]                             |
| 2. financial_scale_calibrator.py --> [ financial_scale.json ]                        |
| 3. run_scoring.py                --> [ scoring_output.json ]                         |
| 4. run_evidence_analyst.py       --> [ findings.json ]                               |
| 5. run_sota_researcher.py        --> Ingests external industry benchmarks            |
| 6. run_tower_blueprint_engine.py --> [ blueprint_Txx_payload.json ] (TOWER SSOT)     |
| 7. run_executive_annex_synthesizer.py --> [ approved_annex_Txx.template_payload.json]|
| 8. payload_to_ast.py + docx_compiler.py --> [ Annex_Txx_ASIS.docx, Blueprint_Txx.docx]|
+--------------------------------------------------------------------------------------+
                                 |
            (Collects all completed blueprint_Txx_payload.json)
                                 |
+--------------------------------v-----------------------------------------------------+
| PHASE 2: GLOBAL CONSOLIDATION PIPELINE (run_global_pipeline.py)                      |
+--------------------------------------------------------------------------------------+
| 1. build_global_report_payload.py  --> [ global_report_payload.json ]                 |
| 2. run_executive_refiner.py        --> Refines executive narrative in-place          |
| 3. TomoAsisAstCompiler             --> [ Tomo_1_Diagnostico_ASIS_<client>.docx ]     |
+--------------------------------------------------------------------------------------+
                                 |
+--------------------------------v-----------------------------------------------------+
| PHASE 3: COMMERCIAL STRATEGY PIPELINE (run_commercial_pipeline.py)                   |
+--------------------------------------------------------------------------------------+
| 1. run_commercial_refiner.py      --> [ commercial_report_payload.json ]             |
| 2. render_commercial_report.py    --> [ Account_Action_Plan_<client>.docx ]          |
+--------------------------------------------------------------------------------------+
```

---

## 4. Execution Surfaces

The platform provides two formal execution entrypoints:

### A. Batch Pipeline Mode (CLI)
Automated CLI suite driven by `cli.py` or standalone application scripts:
```bash
# Execute single-tower end-to-end evaluation
python -m assessment_engine.application.run_tower_pipeline --tower T1 --client acme_corp

# Execute global consolidation across all towers
python -m assessment_engine.application.run_global_pipeline acme_corp

# Execute commercial refiner and account action plan
python -m assessment_engine.application.run_commercial_pipeline acme_corp
```

### B. Model Context Protocol (FastMCP) Mode
The service layer exposes typed tools for external LLM orchestrators via FastMCP (`src/assessment_engine/mcp_server.py`):
- `get_tower_state`: Inspects generated payloads and compilation readiness.
- `run_tower_stage`: Executes discrete pipeline sub-tasks (scoring, evidence analysis, blueprint synthesis).
- `inspect_evidence_ledger`: Queries the epistemic graph and forensic assertions.

---

## 5. Declarative Engine Configuration (`engine_config/`)

All methodological baselines, industry weights, labor rates, and question rubrics reside declaratively in `engine_config/`:

| Configuration Catalog | Purpose in Pipeline |
|---|---|
| `enterprise_registry.json` | Multitenant client profiles, legal identifiers, currency locales, and risk tolerances. |
| `governance_scales.json` | CMMI maturity level rubrics (1.0 to 5.0) and quantitative scoring thresholds. |
| `country_labor_rates.json` | Blended hourly engineering and operational labor rates for TCO/ROI modeling. |
| `rate_card.json` | NTT DATA staffing grades and service cost modeling. |
| `locales.json` | Declarative multilingual catalog for customer deliverables (English default, Spanish optional). |
| `taxonomy/` | Ontological mapping of technical domains, finding archetypes, and vulnerability clusters. |
| `policies/` | FAIR loss event distributions and jurisdictional sovereignty guardrails. |
