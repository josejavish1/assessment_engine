---
status: Verified
owner: docs-governance
source_of_truth:
- ../src/assessment_engine/domain/
- ../src/assessment_engine/application/
- ../src/assessment_engine/mcp_server.py
- ../src/assessment_engine/domain/schemas/
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# System Architecture: Assessment Engine

> **Status:** verified high-level canonical overview.
>
> This file gives the global picture of the current architecture. The more focused canonical breakdown now lives under [`docs/architecture/`](architecture/README.md), especially for tower flow, global/commercial flow, MCP mode, and `working/` artifacts.

## 1. Vision & Core Principles

The `assessment-engine` is a document generation factory designed to produce structured technological assessment deliverables. The engine implements a Python-orchestrated, LLM-assisted execution pipeline to process raw evaluation telemetry and structured evidence into a series of coherent, consistent reports, spanning deep technical blueprints and executive-level consolidations.

The system is governed by several key architectural principles:

-   **Top-Down Flow:** High-level documents (e.g., an executive summary) are exclusively derived from more detailed documents (e.g., a technical blueprint). This eliminates "split-brain" contradictions by ensuring all summary artifacts inherit data directly from their parent technical blueprints.
-   **Contract-First:** Communication between pipeline stages is strictly governed by Pydantic schemas. This enforces explicit, typed data contracts at every transition point.
-   **Python Orchestration, AI Operation:** Control flow, topological sorting, and execution boundaries are managed deterministically by Python. Large Language Models are employed as functional executors for textual synthesis and reasoning tasks, operating strictly within the schemas defined by their contracts.
-   **Decoupled Rendering:** Content generation (semantic payload assembly) is decoupled from the presentation layers (compilation to `.docx` or `.html` files).
-   **Service-Oriented / Dual-Mode Operation:** The system operates either as a linear batch CLI pipeline or as an asynchronous Model Context Protocol (MCP) server, exposing capabilities as typed tools.

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

-   **Optional Upstream Enrichment: Client Intelligence.** `run_intelligence_harvesting.py` generates `working/<client>/client_intelligence.json`. This dossier encapsulates organizational context, enabling downstream LLM prompts to align with client-specific terminology and structures if present, but the main pipelines do not require it to exist for every run.

-   **Phase 1: Tower Analysis.** This is the core engine. For each technology domain (Tower), deterministic preparation modules generate `case_input.json`, `evidence_ledger.json`, `scoring_output.json`, and `findings.json`. Following this, `run_tower_blueprint_engine.py` aggregates these inputs to generate `blueprint_<tower>_payload.json` via LLM-guided synthesis. This file acts as the single source of truth for the tower. Subsequent steps, such as `run_executive_annex_synthesizer.py`, derive specialized payloads (e.g., `approved_annex_<tower>.template_payload.json`) directly from this blueprint before compilation to DOCX.

-   **Phase 2: Global Consolidation.** Once one or more towers have produced blueprints, `build_global_report_payload.py` aggregates them into `global_report_payload.json` from those blueprints. The active path is now blueprint-first without legacy fallback in the global builder. `run_executive_refiner.py` then refines the same `global_report_payload.json` in place.

-   **Phase 3: Commercial Consolidation.** `run_commercial_refiner.py` uses both the refined global payload and all available tower blueprints to create `commercial_report_payload.json`, which is then rendered to `Account_Action_Plan_<client>.docx`.

-   **Phase 4: Web Presentation.** `render_web_presentation.py` derives a client-facing HTML dashboard from `global_report_payload.json` plus tower blueprints, writing `working/<client>/presentation/index.html`.

---

## 4. Operating Modes

The system is designed to be used in two distinct modes:

-   **1. Pipeline Mode:** The primary batch execution path. The orchestrators (`run_tower_pipeline.py`, `run_global_pipeline.py`, and `run_commercial_pipeline.py`) execute the sequence of deterministic and LLM-assisted steps linearly, ensuring transactional consistency and artifact caching.

-   **2. Model Context Protocol (MCP) Mode:** Exposes select pipeline tasks as tools. This mode facilitates integration with developer environments and agentic loops, although certain tool surfaces retain compatibility with legacy structures. (The `mcp_server.py` script exposes selected capabilities as tools via FastMCP, e.g., `get_tower_state` which inspects legacy `approved_asis/generated` style artifacts).

---

## 5. Component Map

The project is organized into several key component types. The legacy per-file reference is now archived under `docs/reference/generated/legacy-gemini/`, but canonical narrative documentation should now live under `docs/architecture/`, `docs/operations/`, `docs/contracts/`, and related top-level docs.

-   **Orchestrators:** Scripts defining the execution sequence and managing task state (e.g., `run_tower_pipeline.py`).
-   **Preparation & Computation:** Deterministic scripts calculating quantitative metrics, sorting topologies, and compiling input telemetry (e.g., `run_scoring.py`, `generate_tower_radar_chart.py`).
-   **LLM-Assisted Synthesis & Refinement:** Scripts leveraging models for domain analysis, structural drafting, and stylistic consolidation under strict schema constraints (e.g., `run_tower_blueprint_engine.py`, `run_commercial_refiner.py`).
-   **Renderers & Compilers:** Modules mapping Pydantic-validated JSON payloads into presentation formats such as OpenXML `.docx` or semantic `.html` (e.g., `render_global_report_from_template.py`).
-   **Prompt Templates:** Versioned, structured text templates defining agent boundaries, execution instructions, and output schemas.
-   **Data Contracts (Schemas):** Strict Pydantic models that validate and structure every intermediate payload exchanged between modules.
-   **Core Utilities (`infrastructure/`):** Common modules for LLM API invocation, configuration parsing, logging, and string utilities.
-   **Verification & Lifecycle:** Preflight verification scripts, automated smoke-test generators, and test suites.

---

## 6. Declarative Engine Configuration & Latent Infrastructure

The behavior of the execution pipeline is driven declaratively via files inside the `engine_config/` directory. This allows fine-tuning and policy enforcement without code alterations.

To preserve institutional knowledge and support upcoming roadmap phases, the system maintains several highly valuable **latent design artifacts** under this directory. These represent planned infrastructure that should not be deleted, as they outline the future path of the engine's capabilities:

-   **OPA Rego Policy Validation (`engine_config/policies/ontology/vendor_constraints.rego`):**
    -   **Status:** Planned / Latent Infrastructure.
    -   **Description:** Implements strict Open Policy Agent (Rego) syntax to enforce semantic constraints on generated claims and technological drivers. It acts as a safety barrier to prevent competitor "hallucination collisions" (e.g., mixing exclusive market rivals or preventing false entities like "Microsoft AWS").
    -   **Roadmap Integration:** Planned for integration into the core Policy Engine (`policy_engine.py`) to programmatically validate synthesized payloads before compilation.
-   **Differentiated Content Rendering Modes (`engine_config/render_modes/tower_annex_modes.json`):**
    -   **Status:** Planned / Latent Infrastructure.
    -   **Description:** Specifies quantitative boundaries (e.g., maximum word counts, headlines, key message limits) for different deliverables depending on the requested target profile (such as `standard_high_value` or `executive_light`).
    -   **Roadmap Integration:** Scheduled to be loaded dynamically by downstream generation and refinement engines to programmatically enforce narrative verbosity profiles based on the selected mode.

---

## 7. Historical Context: The "Legacy" Architecture

The `_legacy` folders in the `scripts` and `docs` directories contain the previous version of the architecture.

-   **Asynchronous Parallel Drafting (Bottom-Up):** The legacy architecture generated report sections (`AS-IS`, `TO-BE`, `GAP`) in isolated, parallel processes, merging them at compilation via `assemble_tower_annex.py`.
-   **Logical Coherence Failure (Split-Brain):** Since sections were generated in isolation, they lacked contextual cohesion. The resulting gap analysis often diverged from the baseline state, producing contradictory narratives.
-   **Deterministic Derivation (Top-Down):** The blueprint-first model generates a unified, detailed technical blueprint as the absolute source of truth. All summary sheets, roadmap items, and commercial deliverables are derived directly from this single payload, guaranteeing consistency by design.

Understanding this evolution is key to understanding the rationale behind the current system's structure.
