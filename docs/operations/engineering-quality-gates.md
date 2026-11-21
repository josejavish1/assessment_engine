---
status: Verified
owner: docs-governance
source_of_truth:
- docs/operations/agentic-development-workflow.md
- pyproject.toml
- uv.lock
- .github/workflows/quality.yml
- .github/workflows/typing.yml
- .github/pull_request_template.md
- AGENTS.md
- .github/copilot-instructions.md
- src/assessment_engine/infrastructure/global_maturity_policy.py
- src/assessment_engine/application/tools/run_incremental_quality_gate.py
- src/assessment_engine/application/tools/run_incremental_typecheck.py
- tests/integration/test_policy_engine.py
review_when_source_changes:
- docs/operations/agentic-development-workflow.md
- pyproject.toml
- uv.lock
- .github/workflows/quality.yml
- .github/workflows/typing.yml
- .github/pull_request_template.md
- AGENTS.md
- .github/copilot-instructions.md
- src/assessment_engine/infrastructure/global_maturity_policy.py
- src/assessment_engine/application/tools/run_incremental_quality_gate.py
- src/assessment_engine/application/tools/run_incremental_typecheck.py
- tests/integration/test_policy_engine.py
review_paths_on_source_change:
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
notes: Canonical technical specification of the automated engineering quality gates and static analysis checks.
---
# Engineering Quality Gates & Static Analysis Checks

Canonical operational specification defining the automated quality gates, static typing checks, architectural fitness tests, and audit probes enforcing codebase integrity across `assessment-engine`.

---

## 1. Active Verification Surface

Automated quality gates inspect changes across the active development surface:

- `src/assessment_engine/domain/` (Entities, schemas, actuarial models)
- `src/assessment_engine/application/` (Orchestrators, synthesizers, calculators)
- `src/assessment_engine/adapters/` (OpenXML AST compilers, CLI entrypoints)
- `src/assessment_engine/infrastructure/` (Clients, event store, config loaders)
- `tests/` (Unit, integration, and architecture regression suites)

### Operational Invariant Axiom:
Core business invariants, CMMI maturity scales, and data contracts MUST NOT reside solely in LLM prompt strings or manual code reviews. Every architectural invariant must be enforced by at least one executable gate:
1. **Domain Policies:** Pure-Python modules encapsulating centralized business formulas.
2. **Typed Pydantic Schemas:** Schema boundary validation (`validate_contracts_schemas.py`).
3. **Automated Test Coverage:** Regression suites blocking semantic drift.
4. **CI/CD Quality Checkpoints:** Automated GitHub Actions workflows blocking pull requests.

---

## 2. The Four Executable Quality Gates

```
+---------------------------------------------------------------------------------------+
| 1. INCREMENTAL QUALITY GATE (quality.yml / run_incremental_quality_gate.py)           |
| - Ruff Linter: Syntax, complexity, and PEP compliance                                 |
| - Ruff Formatter: Deterministic code formatting (--check)                             |
| - Golden Path Check: Validates scaffolding compliance (templates/golden_paths)        |
| - Import Linter: Layered architecture enforcement (blocks domain -> infrastructure)   |
+---------------------------------------------------------------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------------+
| 2. INCREMENTAL TYPING GATE (typing.yml / run_incremental_typecheck.py)                |
| - Strict Mypy typecheck on changed modules and direct dependents                      |
| - Blocks implicit Any casts and untyped signatures                                    |
+---------------------------------------------------------------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------------+
| 3. DOMAIN COHERENCE GATE (tests/integration/test_policy_engine.py)                     |
| - Centralized maturity resolution via maturity_band.py                                |
| - Cross-tower consistency asserting zero metric divergence between blueprints & annexes|
+---------------------------------------------------------------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------------+
| 4. COMPREHENSIVE AUDIT SUITE (python -m assessment_engine.application.cli audit)       |
| - 21 Automated Probes: SAST, Shannon entropy secrets, mutation score, AST reachability|
| - Generates docs/audits/AUDIT_REPORT.json and AUDIT_CERTIFICATE.html                  |
+---------------------------------------------------------------------------------------+
```

---

## 3. Local Execution Recipes

Prior to pushing changes or opening a pull request, operators and autonomous agents MUST execute the local incremental quality checks:

### Incremental Quality Gate (Linting, Formatting & Golden Path):
```bash
python src/assessment_engine/application/tools/run_incremental_quality_gate.py \
  --repo-root . \
  --base-sha origin/main \
  --head-sha HEAD
```

### Incremental Static Typing (Mypy):
```bash
python src/assessment_engine/application/tools/run_incremental_typecheck.py \
  --repo-root . \
  --base-sha origin/main \
  --head-sha HEAD
```

### Targeted Module Testing:
```bash
python src/assessment_engine/application/tools/run_incremental_quality_gate.py \
  --repo-root . \
  --path src/assessment_engine/domain/schemas/blueprint.py \
  --path tests/unit/test_config_registry.py
```

### Full Audit Probe Suite:
```bash
python -m assessment_engine.application.cli audit
```

---

## 4. Architectural Invariants for AI Agents

1. **Gate Immutability:** Agents must never alter rule configurations in `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`, `[tool.importlinter]`) to bypass failing checks. Code must adapt to the gates, never the reverse.
2. **Zero Suppression Hacks:** Disabling warnings via `# type: ignore`, `# noqa`, or casting to `Any` without explicit human authorization is strictly prohibited.
3. **Deterministic Business Logic:** All quantitative calculations (averages, maturity mappings, risk distributions) must be executed in Python domain code, never inside LLM system prompts.
