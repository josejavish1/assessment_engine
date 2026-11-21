---
status: Verified
owner: docs-governance
source_of_truth:
- .github/workflows
- src/assessment_engine/application
- .
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Central operations manual index and deterministic runbook routing matrix.
---
# Operations Manual Index & Runbook Matrix

Canonical operational index providing deterministic routing to environment provisioning, pipeline execution recipes, CI/CD quality gates, and failure triage runbooks across `assessment-engine`.

---

## 1. Operational Invariant Axiom

When executing system maintenance or diagnosing anomalies, autonomous agents and operators MUST prioritize authority according to the total order:

$$\text{Executable Code \& Workflows } (L_0) \succ \text{Operational Runbooks } (L_2) \succ \text{Historical Notes } (L_3)$$

If a command or parameter in a runbook contradicts the physical script interface, the script's `argparse` / `--help` specification is the immutable ground truth.

---

## 2. Master Runbook Routing Matrix

| Operational Domain | Runbook Entrypoint | Primary Objective | Authoritative Verification Source |
|---|---|---|---|
| **Environment Provisioning** | [`installation.md`](installation.md) | Virtual environment bootstrap, Python 3.11 setup, and Google Cloud Vertex AI credentials. | `pyproject.toml`, `.assessment_env.sh` |
| **CI/CD Pipelines** | [`ci-cd-workflows.md`](ci-cd-workflows.md) | Automated GitHub Actions execution (`quality.yml`, `docs-governance.yml`, `ci.yml`). | `.github/workflows/` |
| **Agentic Workflow** | [`agentic-development-workflow.md`](agentic-development-workflow.md) | Spec-first change discipline, anti-vibe coding protocols, and PR reconciliation. | `AGENTS.md`, `.github/copilot-instructions.md` |
| **Quality Gates** | [`engineering-quality-gates.md`](engineering-quality-gates.md) | Incremental Ruff formatting, Mypy strict typing, and import-linter dependency bounds. | `run_incremental_quality_gate.py` |
| **Commit Integrity** | [`signing-commits-policy.md`](signing-commits-policy.md) | Cryptographic GPG/SSH commit signature standards and branch protection. | Repository security configuration |
| **Pipeline Execution** | [`pipeline-execution.md`](pipeline-execution.md) | Standard CLI execution syntax for tower, global, and commercial pipelines. | `run_tower_pipeline.py`, `run_global_pipeline.py` |
| **Execution Controls** | [`pipeline-controls-runbook.md`](pipeline-controls-runbook.md) | Stage resumption (`--start-from`), timeout management, and process confinement. | `pipeline_runtime.py` |
| **PO Orchestrator** | [`product-owner-orchestrator.md`](product-owner-orchestrator.md) | High-level autonomous product owner orchestrator and backlog management. | `run_product_owner_orchestrator.py` |
| **Streaming Sentinel** | [`streaming-sentinel-guide.md`](streaming-sentinel-guide.md) | Asynchronous filesystem event watcher and dynamic RAPTOR tree updater. | `streaming_sentinel.py` |
| **Triage & Smoke Tests** | [`troubleshooting-working.md`](troubleshooting-working.md) | Scratchpad recovery, missing payload triage, and smoke test regeneration. | `regenerate_smoke_artifacts.py` |
| **Data Coherence** | [`assessment-coherence-remediation.md`](assessment-coherence-remediation.md) | Automated detection and repair of metric divergence across intermediate payloads. | `run_autonomous_remediation.py` |
| **Resilience & FMEA** | [`resilience-and-fallbacks.md`](resilience-and-fallbacks.md) | Rate limit backoff, API circuit breakers, and offline snapshot fallbacks. | `ai_client.py`, `agentic_benchmarker.py` |

---

## 3. Standard Operational Lifecycle for Agents

Autonomous agents executing operational tasks MUST adhere to the following sequence:

1. **Preflight Environment Validation:** Verify Python 3.11 `.venv` activation and Vertex AI environment variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`).
2. **Quality Gate Compliance:** Execute incremental quality checks (`run_incremental_quality_gate.py`) before submitting any change.
3. **Deterministic Execution:** Use explicit module execution (`python -m assessment_engine.application.<module>`) with validated CLI flags.
4. **Post-Flight Validation:** Verify compiled deliverables using physical format inspection (`docx.Document`) asserting zero structural corruption.
