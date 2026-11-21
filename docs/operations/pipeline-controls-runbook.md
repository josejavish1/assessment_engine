---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/adapters/compilers/docx_compiler.py
- src/assessment_engine/application/tools/check_vertex_ai_access.py
- src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
- docs/operations/pipeline-execution.md
- docs/operations/troubleshooting-working.md
review_when_source_changes:
- src/assessment_engine/application/tools/check_vertex_ai_access.py
- src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/adapters/compilers/docx_compiler.py
review_paths_on_source_change:
- docs/operations/pipeline-controls-runbook.md
- docs/operations/pipeline-execution.md
- docs/operations/troubleshooting-working.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Canonical operational runbook for pipeline controls, health telemetry, symptom diagnostics, and disaster recovery.
---
# Pipeline Controls & Diagnostic Triage Runbook

Canonical operational runbook establishing preflight checkpoints, phase health telemetry, failure diagnosis decision trees, and recovery procedures for the `assessment-engine` pipeline.

---

## 1. Operational Continuity Dimensions

1. **Transactional Integrity:** Guarantees that deliverables generate atomically without corrupting intermediate workspace states.
2. **Semantic Monism:** Prevents inter-phase divergence (*split-brain*) between technical blueprints, executive annexes, and global reports.
3. **Diagnostic Attribution:** Rapidly discriminates between network/authentication failures, schema boundary breaches, and OpenXML presentation compiler errors.

---

## 2. Preflight Operational Checkpoints

Before launching full multi-tower pipeline runs, operators and autonomous agents MUST verify:

| Preflight Checkpoint | Empirical Verification Command | Domain Objective |
|---|---|---|
| **Isolated Environment** | `python -c "import sys; assert '.venv' in sys.prefix"` | Verifies execution within the isolated Python 3.11 virtual environment. |
| **Dependency Tree** | `uv sync --check` | Asserts that physical packages match `uv.lock`. |
| **Vertex AI Connectivity** | `python -m assessment_engine.application.tools.check_vertex_ai_access` | Validates Google Cloud credentials, quotas, and API access before pipeline dispatch. |
| **Input Telemetry Provisioning** | File existence of raw `.docx` / `.txt` files in `source_docs/<client_slug>/` | Asserts raw evidence availability for ingestion. |
| **Workspace Permissions** | Write test to `workspaces/<client_slug>/` | Confirms I/O permissions for scratchpad and deliverable persistence. |

---

## 3. Phase Health Telemetry Matrix

Every execution phase emits verifiable disk artifacts required for downstream progression:

| Execution Phase | Certifying Artifact | Minimum Health Checkpoint |
|---|---|---|
| **Preflight** | Exit code `0` from `check_vertex_ai_access.py` | Cloud project authentication and quota validated. |
| **Single-Tower** | `blueprint_<tower>_payload.json` | Validates against `BlueprintPayload` schema; passes 8 policy passes. |
| **Executive Annex** | `approved_annex_<tower>.template_payload.json` | Validates against `AnnexPayload`; scores match blueprint SSOT. |
| **Global Report** | `global_report_payload.json` | Aggregates 100% of active blueprints in `blueprint-only` mode. |
| **Commercial Plan** | `commercial_report_payload.json` | Contains non-empty opportunities mapped to `rate_card.json`. |
| **OpenXML Deliverables** | `.docx` binaries in `workspaces/<client>/` | Well-formed OpenXML ZIP archives containing valid `word/document.xml`. |
| **Baseline Smoke** | Clean dry-run pass | `regenerate_smoke_artifacts.py --dry-run` exits with code `0`. |

---

## 4. Diagnostic Triage Decision Tree

```
[ Observable Pipeline Symptom ]
              |
              +---> [ Vertex AI API Timeout / Auth Error ]
              |     Remedy: Run check_vertex_ai_access.py; inspect GOOGLE_APPLICATION_CREDENTIALS.
              |
              +---> [ Raw Inputs Available but Blueprint Fails ]
              |     Remedy: Inspect run_tower_blueprint_engine.py logs and case_input.json schema.
              |
              +---> [ Blueprint Valid but Annex Synthesis Fails ]
              |     Remedy: Audit run_executive_annex_synthesizer.py and check score parity.
              |
              +---> [ Blueprints Valid but Global Consolidation Fails ]
              |     Remedy: Debug build_global_report_payload.py; verify blueprint-only mode.
              |
              +---> [ Payloads Valid but Compiled .docx Binary Corrupt ]
                    Remedy: Refactor payload_to_ast.py or docx_compiler.py; NEVER hack JSON payloads.
```

---

## 5. Disaster Recovery & Recovery Procedures

### A. Accidental Baseline or Scratchpad Corruption
Re-initialize standard canonical smoke fixtures:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts
```

### B. Transactional Resumption After Interruption
To resume execution from a failed stage without re-running completed upstream compute:
```bash
python -m assessment_engine.application.run_tower_pipeline \
  --tower T1 \
  --client acme_corp \
  --start-from blueprint
```

---

## 6. Prohibited Operational Anti-Patterns

1. **Validating from DOCX:** Evaluating OpenXML `.docx` files as proof of system correctness; JSON payloads are the sole machine-readable ground truth.
2. **Lateral Renderer Patching:** Fixing a domain calculation error by hacking presentation compilers (`docx_compiler.py`).
3. **Unanchored Retries:** Re-running a failed stage without diagnosing the underlying traceback.
