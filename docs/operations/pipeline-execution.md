---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/application/run_intelligence_harvesting.py
- src/assessment_engine/adapters/compilers/docx_compiler.py
- src/assessment_engine/infrastructure/pipeline_runtime.py
- docs/architecture/tower-pipeline.md
- docs/architecture/global-commercial-pipelines.md
enforce_on_source_changes: true
review_paths_on_source_change:
- docs/operations/pipeline-execution.md
- docs/operations/pipeline-controls-runbook.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Canonical operational runbook for executing the physical pipeline entrypoints across all assessment phases.
---
# Pipeline Execution Guide

Canonical operational guide defining the standard CLI execution recipes, arguments, input dependencies, and post-flight verifications across all `assessment-engine` pipeline phases.

---

## 1. Upstream Client Intelligence Harvesting

Ingests raw corporate documentation, corporate filings, and interview transcripts to synthesize the shared client intelligence dossier (`ClientDossierV3`):

```bash
python -m assessment_engine.application.run_intelligence_harvesting <client_slug>
```

- **Output Artifact:** `workspaces/<client_slug>/client_intelligence.json`.
- **Epistemic Invariant:** Provides baseline IT operating models, dominant vendor footprints, and corporate governance boundaries to all downstream single-tower prompts.

---

## 2. Single-Tower Evaluation Pipeline

Executes end-to-end evaluation for an individual technology domain (e.g., T1 Data Center, T2 Hybrid Cloud, T3 Networks, T5 CyberSOC):

```bash
python -m assessment_engine.application.run_tower_pipeline \
  --tower T1 \
  --client acme_corp \
  --context-file source_docs/acme_corp/context.docx \
  --responses-file source_docs/acme_corp/responses.txt
```

### Granular Stage Resumption:
To resume execution from a failed or modified stage without re-computing upstream evidence:
```bash
python -m assessment_engine.application.run_tower_pipeline \
  --tower T1 \
  --client acme_corp \
  --context-file source_docs/acme_corp/context.docx \
  --responses-file source_docs/acme_corp/responses.txt \
  --start-from "Engine: Executive Annex Synthesizer"
```

- **Output Artifacts:**
  - `workspaces/<client_slug>/T1/blueprint_T1_payload.json` (Tower SSOT)
  - `workspaces/<client_slug>/T1/approved_annex_T1.template_payload.json`
  - `workspaces/<client_slug>/T1/Anexo_T1_ASIS_acme_corp.docx`
  - `workspaces/<client_slug>/T1/Blueprint_Transformacion_T1_acme_corp.docx`

---

## 3. Empirical RAGE Benchmarking (OSINT Grounding)

Dispatches asynchronous regulatory framework benchmarking against live external reference standards:

```bash
python -m assessment_engine.application.cli rage \
  --client acme_corp \
  --industry utilities
```

- **Output Artifacts:**
  - `workspaces/<client_slug>/benchmarks_snapshot.json`
  - `workspaces/<client_slug>/evidence_cache/*.pdf` (Locally snapshotted evidence binaries preventing link rot)

---

## 4. Global Executive Consolidation Pipeline

Consolidates all completed single-tower blueprints into the C-level executive diagnostic:

```bash
python -m assessment_engine.application.run_global_pipeline acme_corp
```

- **Execution Invariant:** Runs in strict `blueprint-only` mode, aggregating maturity heatmaps, systemic liabilities, and cross-cutting transformation initiatives.
- **Output Artifacts:**
  - `workspaces/<client_slug>/global_report_payload.json`
  - `workspaces/<client_slug>/Tomo_1_Diagnostico_ASIS_acme_corp.docx`

---

## 5. Commercial Strategy Pipeline

Correlates technical gap remediations with partner staffing rate cards (`engine_config/rate_card.json`) to produce proactive investment proposals:

```bash
python -m assessment_engine.application.run_commercial_pipeline acme_corp
```

- **Output Artifacts:**
  - `workspaces/<client_slug>/commercial_report_payload.json`
  - `workspaces/<client_slug>/Account_Action_Plan_acme_corp.docx`

---

## 6. Business Command Center Portal

Launches the Next.js 16 / React 19 management portal for interactive scenario simulation and deliverable inspection:

```bash
cd business_command_center && npm run dev
```

- **Gateway URL:** `http://localhost:3000` (or reverse-proxied production port `3001`).

---

## 7. Canonical Smoke Test Runner

Regenerates baseline integration fixtures and asserts physical deliverable compilation:

```bash
# Standard dry-run preflight
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --with-global --dry-run

# Local-only execution (bypasses network LLM calls)
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --local-only

# Full multi-tower regeneration suite
python -m assessment_engine.application.tools.regenerate_smoke_artifacts \
  --client vodafone_demo \
  --scenario vodafone-public \
  --towers T2 T3 T5 \
  --with-global \
  --with-commercial
```

---

## 8. Post-Flight Health Verification Checklist

Following pipeline execution, autonomous agents MUST verify:

1. **Tower Stage:** Confirm existence and non-zero byte size of `blueprint_<tower>_payload.json`.
2. **Global Stage:** Confirm existence and non-zero byte size of `global_report_payload.json`.
3. **Commercial Stage:** Confirm existence and non-zero byte size of `commercial_report_payload.json`.
4. **Deliverable Compilation:** Verify that compiled `.docx` files unpack cleanly as valid OpenXML ZIP archives using `docx.Document(output_path)`.
