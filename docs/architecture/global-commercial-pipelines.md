---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/build_global_report_payload.py
- src/assessment_engine/application/run_executive_refiner.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/application/run_commercial_refiner.py
- src/assessment_engine/infrastructure/pipeline_runtime.py
- src/assessment_engine/domain/schemas/global_report.py
- src/assessment_engine/domain/schemas/commercial.py
- src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
- src/assessment_engine/adapters/render_commercial_report.py
enforce_on_source_changes: true
review_paths_on_source_change:
- docs/architecture/global-commercial-pipelines.md
- docs/architecture/critical-modules.md
- docs/contracts/payload-render-boundaries.md
- docs/contracts/artifact-contracts.md
- docs/operations/pipeline-execution.md
- docs/operations/pipeline-controls-runbook.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Canonical architecture specification of the global consolidation and commercial strategy pipelines.
---
# Global and Commercial Pipelines Architecture

Canonical specification defining the execution sequence, data contracts, multi-agent synthesis, and AST compilation of the Global Consolidation and Commercial Strategy pipelines.

---

## 1. Dual-Tier Value Chain

Following single-tower blueprint generation, `assessment-engine` projects technical findings into two high-level business deliverables:

```
[ Active Tower Blueprints: workspaces/<client>/T*/blueprint_*_payload.json ]
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v (Global Consolidation)                                  v (Commercial Activation)
run_global_pipeline.py                                    run_commercial_pipeline.py
         |                                                         |
         v                                                         v
[ global_report_payload.json ]                            [ commercial_report_payload.json ]
         |                                                         |
         v (TomoAsisAstCompiler)                                   v (render_commercial_report)
[ Tomo_1_Diagnostico_ASIS_<client>.docx ]                 [ Account_Action_Plan_<client>.docx ]
```

- **Global Pipeline:** Aggregates isolated tower blueprints into a cohesive portfolio diagnostic for C-level leadership (CIO/CTO).
- **Commercial Pipeline:** Correlates transformation initiatives against NTT DATA rate cards and client budget envelopes to generate proactive pre-sales account plans.

---

## 2. Phase 2: Global Consolidation Pipeline

Driven by `src/assessment_engine/application/run_global_pipeline.py`, this pipeline executes four deterministic stages:

### Stage 2.1: Blueprint-First Payload Aggregation (`build_global_report_payload.py`)
- **Input:** Inspects `workspaces/<client_id>/` to gather all valid `blueprint_<tower>_payload.json` files.
- **Blueprint-Only Invariant:** Operates in strict `blueprint-only` mode (`source_version: "blueprint-only"`). Legacy AS-IS fragments are ignored.
- **Consolidation Mechanics:**
  - Extracts `tower_summaries` and cross-tower maturity heatmaps.
  - Resolves CMMI maturity bands (1.0 to 5.0) via `global_maturity_policy.py` delegating to `maturity_band.py`.
  - Aggregates macro risks, governance principles, and cross-cutting transformation initiatives.
- **Output:** Writes initial `global_report_payload.json` validated against `src/assessment_engine/domain/schemas/global_report.py`.

### Stage 2.2: Strategic Executive Refinement (`run_executive_refiner.py`)
Executes sequential LLM refinement passes to editorialize technical findings into C-level language:
1. `executive_summary`: High-level strategic elevator pitch and macro investment rationale.
2. `burning_platform`: Systemic technological liabilities, unhedged operational risks, and regulatory exposure.
3. `tower_bottom_lines`: Synthesized executive takeaway per technology domain.
4. `target_vision` & `execution_roadmap`: 3-year phased transformation target states.
5. `executive_decisions`: Prioritized list of immediate board-level approvals required.
- **Mutation Invariant:** Refines `global_report_payload.json` in-place.

### Stage 2.3: Quantitative Visuals Generation (`generate_tower_radar_chart.py`)
Generates vector-grade multi-axis radar charts comparing baseline vs target maturity across all evaluated domains.

### Stage 2.4: OpenXML AST Compilation (`TomoAsisAstCompiler`)
Compiles refined `global_report_payload.json` directly into Microsoft Word:
- **Module:** `src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py`.
- **Output:** `Tomo_1_Diagnostico_ASIS_<client>.docx`.

---

## 3. Phase 3: Commercial Strategy Pipeline

Driven by `src/assessment_engine/application/run_commercial_pipeline.py`, this pipeline maps technical gap remediations to sales opportunities:

### Stage 3.1: Multi-Agent Commercial Refinement (`run_commercial_refiner.py`)
- **Inputs:** Ingests refined `global_report_payload.json`, all active `blueprint_<tower>_payload.json` files, and `engine_config/rate_card.json`.
- **Hierarchical Agent Personas:**
  - **Global Account Director:** Formulates account-level positioning, executive relationship goals, and commercial win themes.
  - **Enterprise Presales Architect:** Translates technical gaps into structured opportunity pipelines.
  - **Delivery & Solutions Orchestrator:** Structures proactive project proposals with formal staffing models (Engagement Manager, Lead Architect, Delivery Director, Staff Engineers), effort day estimates, and sizing ($S, M, L, XL$).
- **Output:** Emits `commercial_report_payload.json` validated against `src/assessment_engine/domain/schemas/commercial.py`.

### Stage 3.2: Account Action Plan Compilation (`render_commercial_report.py`)
- **Module:** `src/assessment_engine/adapters/render_commercial_report.py`.
- **Output:** Compiles `Account_Action_Plan_<client>.docx`.

---

## 4. Architectural Invariants for AI Agents

1. **Top-Down Monism:** Downstream global and commercial aggregators MUST NOT modify or recalculate single-tower maturity scores or risk metrics. Tower blueprints are immutable ground truth.
2. **Schema Enforcement:** Every pipeline stage must pass strict Pydantic model validation (`GlobalReportPayload`, `CommercialReportPayload`) prior to invocation of compiler adapters.
3. **Format Invariant:** Output deliverables compile strictly to Microsoft Word (`.docx`). Generation of PDF or ephemeral web presentations is strictly prohibited.
4. **Environment Isolation:** Child pipeline processes must inherit validated environment variables and paths from `pipeline_runtime.py` without hardcoded fallback paths.
