---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/ai/documentation-governance.md
- docs/operations/engineering-quality-gates.md
- pyproject.toml
- .github/workflows/quality.yml
last_verified_against: 2026-11-12
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: editorial
notes: Tier-1 engineering contribution guidelines, AI-assisted development policy, and testing discipline.
---
# Contributing to Assessment Engine

This guide establishes the mandatory engineering standards, AI-assisted workflow policies, and verification gates required for all contributions to `assessment-engine`.

---

## 1. AI-Assisted Contribution Policy

All contributions—whether authored by human engineers, pair-programmed with LLMs (Claude Code, Cursor, Copilot), or generated via autonomous agent pipelines—must submit to the following governance rules:

- **Author of Record Responsibility:** The contributor submitting the pull request is strictly responsible for every single line of code, comment, and configuration. Unverified AI outputs ("vibe coding") are strictly rejected.
- **Root Cause Problem-Solving:** Never commit AI-generated workarounds, silent `try-except: pass` blocks, or disabled warnings to bypass CI failures. The root architectural cause must be addressed.
- **Language Decoupling Law:** Regardless of the human operator's language, **ALL** source code, inline comments, docstrings, variable names, test descriptions, and git commit messages MUST be written strictly in **100% Technical English**. Multilingual content resides solely in declarative catalogs (`engine_config/locales.json`).
- **Behavioral Drift Sentinel:** Autonomous agents operating across extended multi-turn sessions must maintain the sentinel tag `[CANARY: V4 | MONISM: SSOT | LOCALE: EN]` to detect context rot.

---

## 2. Deterministic Toolchain & Local Setup

The repository enforces deterministic dependency management using `uv` and Python 3.11.

```bash
# 1. Clone repository and verify Python 3.11
python3 --version  # Must be 3.11.x

# 2. Synchronize hermetic virtual environment with exact lockfile
uv sync --all-groups

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install pre-commit quality hooks
uv run pre-commit install
```

Manual dependency installation via raw `pip` or unpinned `poetry` is strictly prohibited. All dependency updates must be committed via `uv.lock`.

---

## 3. Architectural Boundaries & Domain Purity

The codebase strictly adheres to Hexagonal (Ports and Adapters) architecture under `src/assessment_engine/`:

*   **Domain Purity (`domain/`):** Business logic and actuarial models must be 100% pure. Domain classes must NOT perform disk I/O, network requests, or import outer layers (`infrastructure`, `adapters`, `application`).
*   **Presentation-Layer Immunity:** Document compilers (`adapters/compilers/docx_compiler.py`, `payload_to_ast.py`) are passive formatting engines. Never calculate, adjust, or patch business numbers or risk scores in view compilers.
*   **Single Source of Truth (SSOT) Monism:** Actuarial calculations are strictly governed by the probabilistic models (Bayesian Copula and Monte Carlo 10,000 iterations). Heuristic shortcuts or hardcoded overrides are prohibited.
*   **Golden Paths:** When creating new workers or services, use the templates in `templates/golden_paths/`. For pure models, annotate the header with `# golden-path: ignore`.

---

## 4. Testing Discipline & Quality Gates

Every pull request must pass the automated test suite and static analysis gates before review:

```bash
# Run the hermetic test suite (zero external network dependencies)
uv run pytest tests/

# Execute static analysis and strict typing validation
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ tests/

# Validate documentation governance and context synchronization
uv run pytest tests/functional/test_validate_documentation_governance.py tests/functional/test_compile_llms_full.py
```

### Negative Testing Constraints:
- **Zero External Network Calls in `pytest`:** Automated tests must execute completely hermetic. Diagnostic network tests belong exclusively under `tests/diagnostics/` prefixed with `diag_*.py`.
- **Zero `# type: ignore`:** Suppressing MyPy warnings with `# type: ignore` or unstructured `cast()` is forbidden. Resolve typing mismatches through Pydantic schemas or explicit type guards (`isinstance`).

---

## 5. GitOps & Conventional Commits

All commits must follow the **Conventional Commits** specification:

```text
<type>(<scope>): <short imperative summary>

[optional body explaining WHY the change was made]

[optional footer(s)]
```

### Permitted Types:
- `feat`: A new feature or actuarial capability.
- `fix`: A bug fix or defect remediation.
- `chore`: Tooling, root hygiene, or dependency updates.
- `docs`: Documentation updates or governance mapping.
- `refactor`: Code reorganization with zero behavioral change.
- `test`: Adding or refactoring test suites.

Administrative merges (`--admin`), forced pushes (`--force`), or bypassing branch protection rules on `main` are strictly forbidden.
