---
status: Verified
owner: docs-governance
source_of_truth:
  - src/assessment_engine/
  - src/assessment_engine/scripts/
  - src/assessment_engine/mcp_server.py
  - src/assessment_engine/schemas/
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# System Architecture: Assessment Engine

> **Status:** verified high-level canonical overview.
>
> This file gives the global picture of the current architecture. The more focused canonical breakdown now lives under [`docs/architecture/`](architecture/README.md), especially for tower flow, global/commercial flow, MCP mode, and `working/` artifacts.

## 1. Vision & Core Principles

The `assessment-engine` is a document generation factory designed to produce B2B technology assessment deliverables. It uses a Python-orchestrated, AI-assisted pipeline to transform raw evaluation data into a series of coherent, high-value reports, from deep technical analyses to strategic executive summaries.

The system is governed by several key architectural principles:

-   **Top-Down Flow:** High-level documents (e.g., an executive summary) are exclusively derived from more detailed documents (e.g., a technical blueprint). This prevents "split-brain" inconsistency and ensures all artifacts are aligned.
-   **Contract-First:** All communication between pipeline stages is done through data artifacts (`payloads`) with a strictly defined structure (Pydantic Schemas). This makes the system predictable and robust.
-   **Python Orchestration, AI Operation:** The control flow, business logic, and pipeline decisions are explicitly handled by Python scripts. AI acts as a specialized "operator" that performs specific creative or analytical tasks within the boundaries of its data contract.
-   **Decoupled Rendering:** The logic that generates the content (the data) is completely separate from the logic that presents it (the generation of `.docx` or `.html` files).
-   **Service-Oriented / Dual-Mode Operation:** The engine can be run as a linear command-line pipeline or expose its capabilities as a tool server for external orchestration.

---

## 2. High-Level Architecture & Data Flow

The dominant production flow is **top-down**: tower blueprints act as the main source of truth, and client-level artifacts are derived from them. Around that flow, the repo exposes one optional enrichment step and one secondary service surface:

- **Optional client intelligence harvesting** creates `client_intelligence.json` before tower analysis.
- **Primary pipeline mode** runs tower, global, commercial, and web generation from the command line.
- **Secondary MCP mode** exposes selected operations as tools, but still reflects part of the legacy section-based model.

```
========================================================================================================================
| INPUTS + OPTIONAL ENRICHMENT                                                                                        |
========================================================================================================================
|                                                                                                                      |
|   [ Customer Files: .docx, .txt ]                                                                                    |
|   (Responses, Business Context, etc.)                                                                                |
|                                                                                                                      |
|   [ Methodological Config: .json ]                                                                                   |
|   (Located in /engine_config)                                                                                        |
|                                                                                                                      |
|   Optional upstream enrichment:                                                                                      |
|   - run_intelligence_harvesting.py --> [ client_intelligence.json ]                                                  |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'
                                                     |
                                                     V
========================================================================================================================
| PHASE 1: TOWER ANALYSIS PIPELINE (per-Tower)                                                                         |
| Orchestrator: run_tower_pipeline.py                                                                                  |
========================================================================================================================
|                                                                                                                      |
|   1. Data Preparation (Deterministic):                                                                               |
|      - build_case_input.py         --> [ case_input.json ]                                                           |
|      - build_evidence_ledger.py    --> [ evidence_ledger.json ]                                                      |
|      - run_scoring.py              --> [ scoring_output.json ]                                                       |
|      - run_evidence_analyst.py     --> [ findings.json ]                                                             |
|                                                                                                                      |
|   2. Core AI Analysis (Creation of the Single Source of Truth):                                                      |
|      - run_tower_blueprint_engine.py --> [ blueprint_Txx_payload.json ]  <--- (THE SINGLE SOURCE OF TRUTH)            |
|                                                                                                                      |
|   3. Synthesis & Rendering (Derivation from the Source of Truth):                                                    |
|      - run_executive_annex_synthesizer.py --> [ approved_annex_txx.template_payload.json ]                          |
|      - render_tower_blueprint.py          --> [ Blueprint_Txx.docx ]                                                 |
|      - render_tower_annex_from_template.py --> [ Annex_Txx.docx ]                                                    |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'
                                                     |
                                                     V (Gathers multiple blueprint_payloads)
========================================================================================================================
| PHASE 2: GLOBAL & COMMERCIAL PIPELINES                                                                               |
| Orchestrators: run_global_pipeline.py, run_commercial_pipeline.py                                                    |
========================================================================================================================
|                                                                                                                      |
|   1. Global Aggregation:                                                                                             |
|      - build_global_report_payload.py --> [ global_report_payload.json ]                                             |
|                                                                                                                      |
|   2. Global & Commercial AI Refinement:                                                                              |
|      - run_executive_refiner.py    --> [ global_report_payload.json ] (refined in place)                            |
|      - run_commercial_refiner.py   --> [ commercial_report_payload.json ] (Uses *all* blueprints + global report)    |
|                                                                                                                      |
|   3. Final Deliverable Rendering:                                                                                    |
|      - render_global_report_from_template.py --> [ Informe_Ejecutivo_Consolidado_<client>.docx ]                    |
|      - render_commercial_report.py --> [ Account_Action_Plan_<client>.docx ]                                         |
|      - render_web_presentation.py  --> [ working/<client>/presentation/index.html ]                                 |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'

```

---

## 3. Pipeline Phases in Detail

For the current canonical breakdown, also see:

- [`architecture/tower-pipeline.md`](architecture/tower-pipeline.md)
- [`architecture/global-commercial-pipelines.md`](architecture/global-commercial-pipelines.md)
- [`architecture/mcp-mode.md`](architecture/mcp-mode.md)
- [`architecture/working-artifacts.md`](architecture/working-artifacts.md)

-   **Optional upstream enrichment: Client Intelligence.** `run_intelligence_harvesting.py` can create `working/<client>/client_intelligence.json`, a reusable strategic dossier that later steps may consume. The tower blueprint engine and some renderers can use it if present, but the main pipelines do not require it to exist for every run.

-   **Phase 1: Tower Analysis.** This is the core engine. For each technology tower (for example, `T5`), the system first runs deterministic preparation (`case_input.json`, `evidence_ledger.json`, `scoring_output.json`, `findings.json`). Then `run_tower_blueprint_engine.py` creates `blueprint_<tower>_payload.json`, which is the tower's canonical source of truth. `run_executive_annex_synthesizer.py` derives `approved_annex_<tower>.template_payload.json` from that blueprint, and the renderers produce the final DOCX outputs.

-   **Phase 2: Global Consolidation.** Once one or more towers have produced blueprints, `build_global_report_payload.py` aggregates them into `global_report_payload.json` from those blueprints. The active path is now blueprint-first without legacy fallback in the global builder. `run_executive_refiner.py` then refines the same `global_report_payload.json` in place.

-   **Phase 3: Commercial Consolidation.** `run_commercial_refiner.py` uses both the refined global payload and all available tower blueprints to create `commercial_report_payload.json`, which is then rendered to `Account_Action_Plan_<client>.docx`.

-   **Phase 4: Web Presentation.** `render_web_presentation.py` derives a client-facing HTML dashboard from `global_report_payload.json` plus tower blueprints, writing `working/<client>/presentation/index.html`.

---

## 4. Operating Modes

The system is designed to be used in two distinct modes:

-   **1. Pipeline Mode:** This is the primary mode of operation, executed via the command line. The orchestrators (`run_tower_pipeline.py`, `run_global_pipeline.py`) are called to run the entire, pre-defined sequence of steps in a batch process. This is ideal for standard, end-to-end report generation.

-   **2. Tool Server Mode:** The `mcp_server.py` script exposes selected capabilities as tools via FastMCP. This mode is useful for integrations and external supervisors, but it is not the main canonical path. Part of its surface still reflects the older section-based architecture, especially `get_tower_state`, which inspects legacy `approved_asis/generated` style artifacts rather than the current blueprint-first flow.

---

## 5. Component Map

The project is organized into several key component types. The legacy per-file reference is now archived under `docs/reference/generated/legacy-gemini/`, but canonical narrative documentation should now live under `docs/architecture/`, `docs/operations/`, `docs/contracts/`, and related top-level docs.

-   **Orchestrators:** Python scripts that define and execute the sequence of a pipeline. (e.g., `run_tower_pipeline.py`).
-   **Logic & Preparation Scripts:** Deterministic Python scripts that prepare data, calculate metrics, or generate visual assets. (e.g., `run_scoring.py`, `generate_tower_radar_chart.py`).
-   **AI Engines & Refiners:** Python scripts that orchestrate AI agents to perform complex analysis or creative generation. (e.g., `run_tower_blueprint_engine.py`, `run_commercial_refiner.py`).
-   **Renderers:** Scripts responsible for the final presentation layer, converting data payloads into `.docx` or `.html` files. (e.g., `render_global_report_from_template.py`, `render_web_presentation.py`).
-   **Prompts:** The "source code" for the AI agents, defining their personality, rules, and tasks.
-   **Schemas:** Pydantic models that define the "data contracts" for all the `payloads` exchanged between scripts.
-   **Libraries (`lib/`):** Reusable Python utilities for common tasks like interacting with the AI, loading configuration, or cleaning text.
-   **Support & Testing (`tools/`, `bootstrap/`, `tests/`):** Scripts for preflight checks, smoke regeneration, initialization, validation, and quality control.

---

## 6. Historical Context: The "Legacy" Architecture

The `_legacy` folders in the `scripts` and `docs` directories contain the previous version of the architecture.

-   **Old Model ("Bottom-Up"):** The original design generated each section of a report (`AS-IS`, `TO-BE`, `GAP`, etc.) in parallel, isolated processes. At the end, a script (`assemble_tower_annex.py`) would "assemble" these independent JSON files into a final report.
-   **The "Split-Brain" Problem:** This approach suffered from a critical flaw: since the `AS-IS` and `TO-BE` sections were created without knowledge of each other, the resulting `GAP` analysis could be inconsistent or illogical.
-   **The Solution ("Top-Down"):** The current architecture was created to solve this. By generating the most detailed document (the Blueprint) first and then deriving all other summaries from it, consistency is guaranteed by design.

Understanding this evolution is key to understanding the rationale behind the current system's structure.
