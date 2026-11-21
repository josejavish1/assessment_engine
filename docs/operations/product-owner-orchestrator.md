---
status: Verified
owner: docs-governance
source_of_truth:
- pyproject.toml
- engine_config/policies/orchestrator_policy.json
- engine_config/runtime_manifest.json
- src/assessment_engine/infrastructure/product_owner_models.py
- src/assessment_engine/application/tools/run_product_owner_orchestrator.py
- src/assessment_engine/domain/prompts/product_owner_prompts.py
- .github/workflows/ci.yml
- .github/workflows/quality.yml
- .github/workflows/typing.yml
- .github/workflows/orchestrator-pr-reconcile.yml
- .github/scripts/reconcile_prs.sh
review_when_source_changes:
- pyproject.toml
- engine_config/policies/orchestrator_policy.json
- engine_config/runtime_manifest.json
- src/assessment_engine/infrastructure/product_owner_models.py
- src/assessment_engine/application/tools/run_product_owner_orchestrator.py
- src/assessment_engine/domain/prompts/product_owner_prompts.py
- .github/workflows/ci.yml
- .github/workflows/quality.yml
- .github/workflows/typing.yml
review_paths_on_source_change:
- docs/operations/product-owner-orchestrator.md
- docs/operations/agentic-development-workflow.md
- docs/operations/README.md
- docs/README.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Canonical technical specification of the Product Owner to Pull Request autonomous orchestration engine.
---
# Product Owner Orchestrator Engine

Canonical operational specification defining the autonomous Product Owner to Pull Request (PO-to-PR) workflow, vendor-agnostic executor dispatch, iterative task verification, and automated PR reconciliation in `assessment-engine`.

---

## 1. System Mission & Architectural Decoupling

The Product Owner Orchestrator automates the translation of unstructured business requirements into verified, production-ready Pull Requests. The platform decouples governance, decomposition, and gate enforcement from the underlying AI code-generation backend:

```
[ Natural Language Business Request ]
                  |
                  v (run_product_owner_orchestrator.py plan)
[ Minimum Verifiable Specification (MVS) & Task WBS ]
                  |
                  v (Iterative Task Execution Loop)
+---------------------------------------------------------------------------------------+
| EXECUTOR DISPATCH HARNESS                                                             |
| - Configurable CLI command: --executor-command "<cmd> {repo_root} {task_prompt_file}" |
| - Default Wrapper: ./.github/scripts/orchestrator-gemini-executor.sh                  |
+---------------------------------------------------------------------------------------+
                  |
                  v (Automated Quality Gates Verification)
[ pytest + ruff + mypy + validate_documentation_governance.py ]
                  |
                  v (All Gates Green)
[ Git Branch Creation ──> Commit ──> gh pr create ──> Auto-Reconciliation ]
```

---

## 2. CLI Invocation Syntax

The orchestrator operates via the Python tool entrypoint or the native helper alias `po-run`:

### A. Plan Formulation Mode:
Synthesizes the MVS, risk level, branch name, and task breakdown without mutating code:
```bash
python src/assessment_engine/application/tools/run_product_owner_orchestrator.py plan \
  --request "Prioritize critical infrastructure loss scenarios in global report"
```

### B. End-to-End Execution Mode:
Executes planning, iterative dispatch to the configured coding agent, and CI gate validation:
```bash
python src/assessment_engine/application/tools/run_product_owner_orchestrator.py run \
  --request "Harden PR reconciliation timeout handling" \
  --executor-command "./.github/scripts/orchestrator-gemini-executor.sh --repo {repo_root} --task-file {task_prompt_file}"
```

### C. Resuming an Existing PR:
Resumes reconciliation on an open pull request to resolve failing CI checks:
```bash
python src/assessment_engine/application/tools/run_product_owner_orchestrator.py resume-pr \
  --pr-number 12 \
  --executor-command "./.github/scripts/orchestrator-gemini-executor.sh --repo {repo_root} --task-file {task_prompt_file}"
```

---

## 3. Four-Phase Orchestration Lifecycle

### Phase 1: MVS Planning & Task Decomposition
- **Prompt Role:** `product_owner_planner` (`src/assessment_engine/domain/prompts/product_owner_prompts.py`).
- **Emitted Bundle:** Persisted under `working/product_owner_requests/<timestamp>_<slug>/`:
  - `mvs.json`: Declares in-scope files, out-of-scope exclusions, and system invariants.
  - `tasks.json`: Ordered sequence of atomic tasks with explicit acceptance criteria.
  - `metadata.json`: Branch name, commit title, PR title, and risk tier.

### Phase 2: Iterative Task Execution
For each task in the plan:
1. Generates an isolated task prompt containing the global MVS context and current task instructions.
2. Invokes the configured executor backend within a confined subprocess group under a strict execution timeout.
3. Automatically sets `PYTHONDONTWRITEBYTECODE=1` to prevent `__pycache__/` pollution in the working tree.

### Phase 3: Automated Quality Gate Verification
Following task execution, the orchestrator triggers local quality gates:
1. `pytest tests/ -q` (Unit & integration test suites).
2. `validate_documentation_governance.py` (Front matter and documentation integrity).
3. `run_incremental_quality_gate.py` (Ruff formatting, linting, import-linter rules).
4. `run_incremental_typecheck.py` (Mypy static typing).
- *Feedback Loop:* If any gate fails, the orchestrator feeds the traceback directly into the executor's next iteration.

### Phase 4: Git Delivery & PR Reconciliation
1. Creates an isolated feature branch (`git checkout -b <branch_name>`).
2. Stages only modified in-scope files (`git add <files>`) and commits with the planned title.
3. Opens a Pull Request via GitHub CLI (`gh pr create --fill`).
4. Invokes `.github/scripts/reconcile_prs.sh` to rebase against `origin/main`.

---

## 4. Architectural Invariants for AI Agents

1. **Pluggable Executor Independence:** Orchestration logic must never couple to vendor-specific SDKs; all coding delegation operates via configurable shell commands.
2. **Immutable Quality Gates:** The orchestrator must reject code changes that fail standard repository quality gates; bypassing checks via `--no-verify` or force merging is prohibited.
3. **Workspace Isolation:** All planning artifacts and prompt logs must isolate under `working/product_owner_requests/`.
