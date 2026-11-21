---
status: Verified
owner: docs-governance
source_of_truth:
- pyproject.toml
- tests/integration/test_validate_contracts_schemas.py
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
- docs/architecture/working-artifacts.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Operational playbook for troubleshooting workspace scratchpads and reproducing canonical smoke test fixtures.
---
# Workspace Troubleshooting & Smoke Artifacts Playbook

Canonical operational playbook establishing diagnostic triage protocols, physical scratchpad recovery, and reproducible smoke test regeneration (`smoke_ivirma`) across `assessment-engine`.

---

## 1. Compliance Baseline State (`smoke_ivirma`)

Contract tests (`test_validate_contracts_schemas.py`) and golden master regression suites consume real pre-compiled test payloads from disk. For the test suite to pass with 100% green status, the following baseline artifacts must physically exist on the local filesystem:

```text
working/smoke_ivirma/
├── global_report_payload.json
├── commercial_report_payload.json
├── Tomo_1_Diagnostico_ASIS_smoke_ivirma.docx
├── Account_Action_Plan_smoke_ivirma.docx
└── T5/
    ├── blueprint_t5_payload.json
    ├── approved_annex_t5.template_payload.json
    ├── Blueprint_Transformacion_T5_smoke_ivirma.docx
    └── annex_t5_smoke_ivirma_final.docx
```

If these baseline artifacts are accidentally deleted, altered, or corrupted, integration test suites will fail.

---

## 2. Rapid Diagnostic Inspection

When encountering unexpected test failures in workspace contracts, execute these physical filesystem checks:

### Inspect Workspace Directory Layout:
```bash
find working/smoke_ivirma -maxdepth 3 -type f | sort
```

### Inspect Single-Tower Payload Schema Validity:
```bash
python src/assessment_engine/application/tools/validate_contracts_schemas.py \
  --repo-root . \
  --documentation-map docs/documentation-map.yaml
```

---

## 3. Smoke Artifacts Regeneration Playbook

When baseline fixtures are missing or modified, use the platform's deterministic regeneration runner:

### A. Standard Baseline Regeneration:
Regenerates client `smoke_ivirma`, tower `T5`, and scenario `baseline` using deterministic seed `42`:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts
```

### B. Dry-Run Preflight Simulation:
Validates pipeline wiring and AST layout compilation without making external Vertex AI calls:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --dry-run
```

### C. Air-Gapped / Offline Execution:
If offline or if external cloud providers experience outages, regenerate the local baseline from static caches:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --local-only
```

### D. Full End-to-End Consolidated Smoke Suite:
Regenerates single-tower, global consolidation, and commercial strategy deliverables in a single pass:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts \
  --with-global \
  --with-commercial
```

---

## 4. Google Cloud / Vertex AI Connectivity Triage

To validate credentials, active project IDs, and API quotas before launching LLM-assisted regeneration:

```bash
python -m assessment_engine.application.tools.check_vertex_ai_access
```

### Common Authentication Triage:
- **Symptom:** `GoogleDefaultCredentialsError` or `PermissionDenied`.
- **Remedy:**
  1. Re-authenticate local Application Default Credentials:
     ```bash
     gcloud auth application-default login
     ```
  2. Confirm `GOOGLE_CLOUD_PROJECT` is exported:
     ```bash
     export GOOGLE_CLOUD_PROJECT="sub403o4u0q5"
     export GOOGLE_CLOUD_LOCATION="europe-west1"
     ```
  3. If cloud access remains unavailable, switch to offline mode (`--local-only`).
