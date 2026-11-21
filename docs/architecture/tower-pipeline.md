---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_tower_blueprint_engine.py
- src/assessment_engine/application/run_executive_annex_synthesizer.py
- src/assessment_engine/infrastructure/pipeline_runtime.py
- src/assessment_engine/domain/schemas/blueprint.py
- src/assessment_engine/domain/schemas/annex_synthesis.py
enforce_on_source_changes: true
review_paths_on_source_change:
- docs/architecture/tower-pipeline.md
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
notes: Canonical technical specification of the single-tower evaluation pipeline lifecycle.
---
# Single-Tower Evaluation Pipeline Architecture

Canonical specification defining the execution sequence, state transitions, data contracts, and compilation stages of the Single-Tower Evaluation Pipeline (`run_tower_pipeline.py`).

---

## 1. Architectural Scope & Orchestration Pattern

The single-tower pipeline represents the **foundational execution engine** of `assessment-engine`. It evaluates an individual technology domain (e.g., T1 Data Center, T2 Hybrid Cloud, T3 Core Networks, T5 CyberSOC) from raw client telemetry to compiled Word `.docx` deliverables:

```
[ Customer Inputs: Transcripts (.docx), Questionnaire Responses (.txt) ]
                                   |
                                   v
+---------------------------------------------------------------------------------------+
| STAGE 1: DETERMINISTIC PREPARATION                                                    |
| 1. build_case_input.py           --> [ case_input.json ]                              |
| 2. build_evidence_ledger.py       --> [ evidence_ledger.json ]                         |
| 3. financial_scale_calibrator.py  --> [ financial_scale.json ]                         |
| 4. run_scoring.py                 --> [ scoring_output.json ]                          |
| 5. run_evidence_analyst.py        --> [ findings.json ]                                |
+---------------------------------------------------------------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------------------------+
| STAGE 2: TOP-DOWN BLUEPRINT SYNTHESIS (run_tower_blueprint_engine.py)                  |
| - Pillar grouping, empirical research injection, and LLM drafting                     |
| - Intercepted deterministically by SovereignPolicyEngine compiler                      |
| OUTPUT: blueprint_<tower>_payload.json (TOWER SINGLE SOURCE OF TRUTH)                 |
+---------------------------------------------------------------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------------------------+
| STAGE 3: EXECUTIVE ANNEX SYNTHESIS (run_executive_annex_synthesizer.py)                |
| - Handover Invariant: Derives executive framing from blueprint SSOT                    |
| OUTPUT: approved_annex_<tower>.template_payload.json (AnnexPayload Contract)          |
+---------------------------------------------------------------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------------------------+
| STAGE 4: OPENXML AST COMPILATION (payload_to_ast.py + docx_compiler.py)                |
| - Compiles Anexo_<tower>_ASIS_<client>.docx                                           |
| - Compiles Blueprint_Transformacion_<tower>_<client>.docx                             |
+---------------------------------------------------------------------------------------+
```

---

## 2. Detailed Execution Lifecycle

### Stage 1: Deterministic Evidence Preparation
- **`build_case_input.py`:** Parses raw input texts, aligns questions with pillar definitions in `engine_config/towers/<tower>/`, and emits `case_input.json`.
- **`build_evidence_ledger.py`:** Integrates atomic fragments from `evidence_vault.json` and hierarchical clusters from `raptor_tree.json` into `evidence_ledger.json`.
- **`run_scoring.py`:** Computes quantitative maturity ratings (1.0 to 5.0) per pillar using deterministic mathematical weighting.
- **`run_evidence_analyst.py`:** Maps evidence fragments to qualitative technical gap diagnoses in `findings.json`.

### Stage 2: Canonical Blueprint Generation (`run_tower_blueprint_engine.py`)
Synthesizes the **Tower Blueprint SSOT** (`blueprint_<tower>_payload.json`).
- Groups responses by pillar;
- Executes LLM synthesis bounded by `BlueprintPayload` schema (`src/assessment_engine/domain/schemas/blueprint.py`);
- Enforces the 8 deterministic compiler policies (`SovereignPolicyEngine`): deduplication, sequencing, OT perimeters, and reverse traceability.
- **Blueprint Primacy Law:** The blueprint is the authoritative technical baseline for the tower. Subsequent deliverables must derive from it without altering findings or scores.

### Stage 3: Executive Annex Synthesis (`run_executive_annex_synthesizer.py`)
Decouples **target audience** from **technical truth**:
- Loads validated blueprint payload;
- Derives overall score, maturity bands, strategic gaps, and prioritized initiatives deterministically;
- Employs bounded LLM prompts solely for executive headlines, C-level framing, and narrative tone;
- Emits `approved_annex_<tower>.template_payload.json` validating against `AnnexPayload` (`src/assessment_engine/domain/schemas/annex_synthesis.py`).

### Stage 4: OpenXML AST Compilation
Compiles deliverables directly to Microsoft Word (`.docx`):
1. **Tower Annex:** `payload_to_ast.py` maps the annex payload into OpenXML AST nodes; `docx_compiler.py` serializes `Anexo_<tower>_ASIS_<client>.docx`.
2. **Tower Blueprint:** `render_tower_blueprint.py` compiles `Blueprint_Transformacion_<tower>_<client>.docx`.

---

## 3. Data Contracts & State Validation Matrix

| Payload Artifact | Canonical Schema Contract | Validation Mode | Primary Consumer |
|---|---|---|---|
| `case_input.json` | `CaseInput` | Pydantic Schema | `run_scoring.py`, `run_tower_blueprint_engine.py` |
| `scoring_output.json` | `ScoringOutput` | Pydantic Schema | `run_tower_blueprint_engine.py` |
| `findings.json` | `FindingsPayload` | Pydantic Schema | `run_tower_blueprint_engine.py` |
| `blueprint_<tower>_payload.json` | `BlueprintPayload` | Strict Schema Gate | `run_executive_annex_synthesizer.py`, `build_global_report_payload.py` |
| `approved_annex_<tower>.template_payload.json` | `AnnexPayload` | Strict Schema Gate | `payload_to_ast.py`, `docx_compiler.py` |

---

## 4. Architectural Invariants for AI Agents

1. **Blueprint to Annex Monism:** The annex synthesizer is strictly prohibited from altering maturity scores, risks, or project roadmaps defined in the blueprint SSOT.
2. **Transaction Resumption:** Pipeline execution supports granular recovery via `--start-from <step>`. Checkpointed payloads on disk must be validated against their schema prior to downstream step invocation.
3. **Exclusive DOCX Deliverables:** Delivery formats are strictly Microsoft Word (`.docx`). PDF generation is permanently disabled.
4. **Isolated Workspaces:** All execution outputs must reside in `workspaces/<client_slug>/<TOWER_ID>/`.
