# System Architecture: Assessment Engine

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

The system is composed of three main sequential pipelines that process data from the most detailed level to the most strategic.

```
========================================================================================================================
| INPUTS                                                                                                               |
========================================================================================================================
|                                                                                                                      |
|   [ Customer Files: .docx, .txt ]                                                                                    |
|   (Responses, Business Context, etc.)                                                                                |
|                                                                                                                      |
|   [ Methodological Config: .json ]                                                                                   |
|   (Located in /engine_config)                                                                                        |
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
|      - run_executive_annex_synthesizer.py --> [ annex_Txx_payload.json ]                                             |
|      - render_tower_blueprint.py          --> [ Blueprint_Txx.docx ]                                                 |
|      - render_tower_annex.py              --> [ Annex_Txx.docx ]                                                     |
|      - generate_tower_radar_chart.py      --> [ radar_chart.png ] (path injected into annex_payload)                 |
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
|      - run_executive_refiner.py    --> [ refined_global_report.json ]                                                |
|      - run_commercial_refiner.py   --> [ commercial_payload.json ] (Uses *all* blueprints + global report)           |
|                                                                                                                      |
|   3. Final Deliverable Rendering:                                                                                    |
|      - render_global_report.py     --> [ CIO_Ready_Report.docx ]                                                     |

|      - render_commercial_report.py --> [ Internal_Commercial_Plan.docx ]                                           |
|      - render_web_presentation.py  --> [ Interactive_Dashboard.html ] (The most advanced deliverable)                |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'

```

---

## 3. Pipeline Phases in Detail

-   **Phase 1: Tower Analysis:** This is the core engine. For each technology tower (e.g., "T5 - Resilience"), it takes the client's raw answers and context. It first runs a series of deterministic scripts to prepare the data (calculating scores, structuring evidences). Then, the main AI engine (`run_tower_blueprint_engine.py`) creates the `blueprint_payload.json`, which is the most detailed technical analysis and the single source of truth. All other tower-level documents, like the shorter Executive Annex, are **synthesized** from this master blueprint, ensuring consistency.

-   **Phase 2: Global & Commercial Consolidation:** Once multiple towers have been analyzed, this phase begins. It aggregates the key findings from all `blueprint_payload.json` files into a single `global_report_payload.json`. This consolidated report is then refined by high-level AI agents to create a strategic narrative for the CIO. In parallel, the commercial refiner uses *both* the global strategy and the deep technical details from *all* blueprints to generate a concrete, internal-use "Account Action Plan".

---

## 4. Operating Modes

The system is designed to be used in two distinct modes:

-   **1. Pipeline Mode:** This is the primary mode of operation, executed via the command line. The orchestrators (`run_tower_pipeline.py`, `run_global_pipeline.py`) are called to run the entire, pre-defined sequence of steps in a batch process. This is ideal for standard, end-to-end report generation.

-   **2. Tool Server Mode:** The `mcp_server.py` script exposes the engine's core capabilities (e.g., "render a document", "generate a chart") as a set of tools. This allows an external, higher-level AI supervisor agent (e.g., built with LangGraph) to call these functions on demand. This mode enables more flexible, dynamic, and interactive workflows where an AI agent, rather than a fixed script, is in control of the process. The `get_tower_state` tool is crucial here, as it allows the supervisor to check the progress and decide which tool to call next.

---

## 5. Component Map

The project is organized into several key component types. The detailed documentation for each file can be found in this directory.

-   **Orchestrators:** Python scripts that define and execute the sequence of a pipeline. (e.g., `run_tower_pipeline.py`).
-   **Logic & Preparation Scripts:** Deterministic Python scripts that prepare data, calculate metrics, or generate visual assets. (e.g., `run_scoring.py`, `generate_tower_radar_chart.py`).
-   **AI Engines & Refiners:** Python scripts that orchestrate AI agents to perform complex analysis or creative generation. (e.g., `run_tower_blueprint_engine.py`, `run_commercial_refiner.py`).
-   **Renderers:** Scripts responsible for the final presentation layer, converting data payloads into `.docx` or `.html` files. (e.g., `render_global_report_from_template.py`, `render_web_presentation.py`).
-   **Prompts:** The "source code" for the AI agents, defining their personality, rules, and tasks.
-   **Schemas:** Pydantic models that define the "data contracts" for all the `payloads` exchanged between scripts.
-   **Libraries (`lib/`):** Reusable Python utilities for common tasks like interacting with the AI, loading configuration, or cleaning text.
-   **Support & Testing (`tools/`, `bootstrap/`, `tests/`):** Scripts for initializing new towers, generating test data, and ensuring the quality and integrity of the system.

---

## 6. Historical Context: The "Legacy" Architecture

The `_legacy` folders in the `scripts` and `docs` directories contain the previous version of the architecture.

-   **Old Model ("Bottom-Up"):** The original design generated each section of a report (`AS-IS`, `TO-BE`, `GAP`, etc.) in parallel, isolated processes. At the end, a script (`assemble_tower_annex.py`) would "assemble" these independent JSON files into a final report.
-   **The "Split-Brain" Problem:** This approach suffered from a critical flaw: since the `AS-IS` and `TO-BE` sections were created without knowledge of each other, the resulting `GAP` analysis could be inconsistent or illogical.
-   **The Solution ("Top-Down"):** The current architecture was created to solve this. By generating the most detailed document (the Blueprint) first and then deriving all other summaries from it, consistency is guaranteed by design.

Understanding this evolution is key to understanding the rationale behind the current system's structure.
