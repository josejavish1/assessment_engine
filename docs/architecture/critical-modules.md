---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_tower_blueprint_engine.py
- src/assessment_engine/application/run_executive_annex_synthesizer.py
- src/assessment_engine/adapters/render_tower_blueprint.py
- src/assessment_engine/adapters/compilers/payload_to_ast.py
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/build_global_report_payload.py
- src/assessment_engine/application/run_executive_refiner.py
- src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/application/run_commercial_refiner.py
- src/assessment_engine/adapters/render_commercial_report.py
- src/assessment_engine/adapters/compilers/docx_compiler.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Functional matrix, data contracts, and failure modes of critical execution modules.
---
# Critical Execution Modules Matrix

Canonical specification cataloging the responsibilities, data contracts, dependency flows, and failure modes across the core execution modules of `assessment-engine`.

---

## 1. Architectural Classification Taxonomy

Modules are categorized into four deterministic archetypes:

| Module Archetype | Functional Scope & Architectural Boundary |
|---|---|
| **Orchestrator** | Governs stage execution sequences, transactional checkpointing, environment resolution, and execution timeouts. |
| **Synthesis Engine** | Executes bounded Generative AI prompts under strict Pydantic output schemas, validating domain invariants. |
| **Data Builder** | Deterministically aggregates, normalizes, and validates intermediate payloads across multiple input streams. |
| **AST Compiler** | Transforms validated Pydantic JSON payloads into OpenXML Abstract Syntax Trees and serializes `.docx` binaries. |

---

## 2. Phase 1: Single-Tower Evaluation Modules

| Module Name | Archetype | Primary Responsibility | Input Contract | Output Contract | Degradation & Risk Mode |
|---|---|---|---|---|---|
| `run_tower_pipeline.py` | Orchestrator | Drives end-to-end tower workflow; manages workspace isolation, preflights, and recovery. | CLI arguments (`--tower`, `--client`) + `engine_config/`. | Integrated artifacts in `workspaces/<client>/<tower>/`. | Pipeline abort; leaves tower in incomplete state without deliverable generation. |
| `run_tower_blueprint_engine.py` | Synthesis Engine | Generates the canonical **Tower Blueprint SSOT** reconciling questionnaire scores, findings, and evidence. | `case_input.json`, `findings.json`, `client_intelligence.json`. | `blueprint_<tower>_payload.json` (`schemas/blueprint.py`). | Total loss of technical ground truth for the technology domain. |
| `run_executive_annex_synthesizer.py` | Synthesis Engine | Derives the executive narrative from the blueprint SSOT, enforcing strategic alignment. | `blueprint_<tower>_payload.json`. | `approved_annex_<tower>.template_payload.json`. | Narrative split-brain between technical findings and executive delivery. |
| `render_tower_blueprint.py` | AST Compiler | Compiles structured blueprint payload into formatted OpenXML technical specification. | `blueprint_<tower>_payload.json`. | `Blueprint_Transformacion_<tower>_<client>.docx`. | Malformed technical delivery document. |
| `payload_to_ast.py` + `docx_compiler.py` | AST Compiler | Maps annex payloads into OpenXML AST nodes (tables, callouts, KPI boxes) and compiles binary DOCX. | `approved_annex_<tower>.template_payload.json`. | `Anexo_<tower>_ASIS_<client>.docx`. | Presentation formatting corruption, visual regressions, or layout solver exceptions. |

---

## 3. Phase 2: Global Consolidation Modules

| Module Name | Archetype | Primary Responsibility | Input Contract | Output Contract | Degradation & Risk Mode |
|---|---|---|---|---|---|
| `run_global_pipeline.py` | Orchestrator | Coordinates multi-tower consolidation, global refinement, and Tomo 1 compilation. | Completed tower blueprints in `workspaces/<client>/`. | Consolidated Tomo 1 deliverable binary. | Incomplete executive visibility; lack of cross-tower portfolio synthesis. |
| `build_global_report_payload.py` | Data Builder | Aggregates all active tower blueprints into a unified multi-domain payload. | List of `blueprint_<tower>_payload.json`. | `global_report_payload.json` (`schemas/global_report.py`). | Cross-tower metric mismatch or omitted domain data. |
| `run_executive_refiner.py` | Synthesis Engine | Refines high-level executive sections (Executive Summary, Macro Risks, Strategic Direction). | `global_report_payload.json`. | `global_report_payload.json` (Refined in-place). | Unpolished or overly technical narrative lacking C-level actionability. |
| `tomo_asis_ast_compiler.py` | AST Compiler | Compiles global report payload directly into Tomo 1 Consolidated Diagnostic Word document. | Refined `global_report_payload.json`. | `Tomo_1_Diagnostico_ASIS_<client>.docx`. | Presentation failure of the primary client deliverable. |

---

## 4. Phase 3: Commercial Strategy Modules

| Module Name | Archetype | Primary Responsibility | Input Contract | Output Contract | Degradation & Risk Mode |
|---|---|---|---|---|---|
| `run_commercial_pipeline.py` | Orchestrator | Drives commercial synthesis from the refined global payload and active blueprints. | Refined `global_report_payload.json` + blueprints. | `Account_Action_Plan_<client>.docx`. | Stalled commercial engagement; lack of prioritized investment proposal. |
| `run_commercial_refiner.py` | Synthesis Engine | Correlates strategic gaps with tower initiatives to generate a commercial account plan. | Global payload, blueprints, and `rate_card.json`. | `commercial_report_payload.json` (`schemas/commercial.py`). | Misaligned commercial sizing, invalid rate calculations, or unrealistic project phasing. |
| `render_commercial_report.py` | AST Compiler | Compiles the commercial proposal payload into the executive Account Action Plan document. | `commercial_report_payload.json`. | `Account_Action_Plan_<client>.docx`. | Failure to generate commercial deliverable. |

---

## 5. Architectural Invariant Constraints

When refactoring or extending critical modules, agents MUST uphold:

1. **Top-Down Authority:** Downstream synthesizers (`run_executive_annex_synthesizer.py`, `run_executive_refiner.py`) must NEVER invent new technical findings omitted by upstream blueprints.
2. **Presentation Decoupling:** AST compilers (`docx_compiler.py`, `tomo_asis_ast_compiler.py`) are strictly layout and rendering engines. Recalculation or mutation of business metrics in compiler classes is prohibited.
3. **Format Monism:** Deliverable output is strictly Microsoft Word (`.docx`). PDF generation and ephemeral HTML presentations are permanently disabled.
