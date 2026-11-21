---
status: Verified
owner: docs-governance
source_of_truth:
- AGENTS.md
- .github/copilot-instructions.md
- .github/pull_request_template.md
- docs/operations/engineering-quality-gates.md
- src/assessment_engine/domain
- tests
- .github/workflows/ci.yml
- .github/workflows/quality.yml
- .github/workflows/typing.yml
review_when_source_changes:
- AGENTS.md
- .github/copilot-instructions.md
- .github/pull_request_template.md
- docs/operations/engineering-quality-gates.md
- docs/operations/product-owner-orchestrator.md
- .github/workflows/ci.yml
- .github/workflows/quality.yml
- .github/workflows/typing.yml
review_paths_on_source_change:
- docs/operations/agentic-development-workflow.md
- docs/operations/engineering-quality-gates.md
- docs/operations/README.md
- docs/README.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Canonical operational guide defining the spec-first agentic software development workflow.
---
# Agentic Software Development Workflow

Canonical operational specification establishing the engineering protocols, quality constraints, and change discipline for autonomous AI agents and human collaborators in `assessment-engine`.

---

## 1. Core Principle: Anti-Vibe Coding & Verifiable Specifications

Autonomous AI agents are strictly prohibited from implementing changes based on conversational prompts, ambiguous requests, or speculative refactoring. Every non-trivial modification requires a **Minimum Verifiable Specification (MVS)** defining bounded surgical scope, schema impacts, and empirical verification oracles:

```
[ Problem Statement ] ──> [ MVS Formulation ] ──> [ Plan-Act-Validate Loop ] ──> [ Automated Quality Gate ]
```

### Mandates for Autonomous Agents:
1. **Spec-First Primacy:** Formulate the explicit in-scope and out-of-scope boundaries before touching any file.
2. **Empirical Reproduction:** Reproduce reported defects with an automated test failure prior to altering production code.
3. **No Unilateral Gate Modification:** Agents are strictly forbidden from relaxing thresholds in `[tool.importlinter]`, `.coveragerc`, or `.github/workflows/quality.yml`.

---

## 2. Minimum Verifiable Specification (MVS) Schema

Every development task or Pull Request MUST conform to this formal structural declaration:

```text
Problem:
- Concise technical definition of defect, missing invariant, or architectural gap.

In-Scope:
- Explicit list of files and components authorized for modification.

Out-of-Scope:
- Non-negotiable boundary exclusions to prevent collateral refactoring.

Source of Truth:
- Canonical Pydantic schemas, physical code paths, or configuration catalogs.

System Invariants:
- Behavioral and mathematical properties that must remain intact.

Verification Oracles:
- Mandatory test commands, linters, and typecheck passes required for sign-off.
```

---

## 3. The Plan-Act-Validate Development Lifecycle

Autonomous agents operating on this repository MUST progress through three deterministic phases:

### Phase 1: Research & Discovery
- Trace existing symbol usage via `grep_search` and AST inspection.
- Inspect canonical documentation (`docs/contracts/`, `docs/architecture/`) to identify established patterns.
- Formulate the MVS and confirm alignment with repository laws in `AGENTS.md`.

### Phase 2: Surgical Execution
- **Golden Path Enforcement:** When scaffolding new components or services, agents MUST inherit from established templates in the `templates/golden_paths` directory. Ad-hoc scaffolding from scratch is prohibited.
- **Python-First Business Logic:** Implement all scoring calculations, risk distributions, and transformation rules in pure Python domain modules located in `src/assessment_engine/domain` package. LLM prompts are restricted to qualitative semantic synthesis.
- **Language Decoupling Law:** All source code, docstrings, exceptions, logs, and prompt signatures MUST be written in 100% Technical English. Spanish is allowed only as localized data within `engine_config/locales.json`.

### Phase 3: Verification & Gate Certification
Execute local quality validation before committing or opening a PR:
```bash
# 1. Run incremental quality gate (Ruff, Mypy, Import Linter)
python src/assessment_engine/application/tools/run_incremental_quality_gate.py --base origin/main

# 2. Run documentation governance validator
python src/assessment_engine/application/tools/validate_documentation_governance.py --repo-root . --documentation-map docs/documentation-map.yaml --today $(date -u +%F)

# 3. Execute targeted test suite
pytest tests/unit/ tests/integration/ -q
```

---

## 4. Strictly Prohibited Engineering Anti-Patterns

1. **Silent Fallbacks:** Using `except Exception: pass` or providing default values that mask upstream data corruption.
2. **Prompt-Confined Business Logic:** Confining business formulas, thresholds, or CMMI maturity bands within LLM system prompts.
3. **Dual Sources of Truth:** Introducing alternative configuration dictionaries, parallel schemas, or hardcoded constants outside `engine_config/`.
4. **Boundary Creep:** Mutating files outside the declared MVS in-scope boundary without explicit prior authorization.
5. **Format Divergence:** Generating PDF deliverables or HTML presentations; deliverable compilation is strictly Word `.docx`.

---

## 5. Automated Pull Request Reconciler Protocol

When an autonomous agent reconciles pull requests or addresses review feedback:
- The agent must analyze failing CI check logs and test failure tracebacks.
- Merge conflicts must be rebased or reconciled against `main` without dropping verified changes.
- The PR checklist in `.github/pull_request_template.md` (specifically **Assessment Coherence Checks**) must be formally validated before merge approval.
