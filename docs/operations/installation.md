---
status: Verified
owner: docs-governance
source_of_truth:
- pyproject.toml
- uv.lock
- tests/unit/test_environment.py
- .github/workflows/ci.yml
- src/assessment_engine/infrastructure/runtime_env.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
notes: Canonical operational guide for local environment provisioning, dependency synchronization, and preflight verification.
---
# Environment Provisioning & Installation Guide

Canonical operational guide defining the deterministic setup, dependency synchronization, cloud credentials configuration, and preflight certification for the `assessment-engine` platform.

---

## 1. System Requirements & Operational Baselines

- **Runtime Engine:** Python 3.11.x pinned via `.python-version`.
- **Package & Dependency Tooling:** `uv` (recommended for deterministic resolution) or `pip`.
- **Dependency Definitions:** Abstract dependencies declared in `pyproject.toml` (PEP 517/621); concrete dependency tree frozen in `uv.lock`.
- **Filesystem Sandbox:** Isolated local virtual environment located strictly at `.venv/`.
- **Cloud Provider Credentials:** Google Cloud Vertex AI access authenticated via Service Account key or Application Default Credentials (ADC).

---

## 2. Deterministic Provisioning Protocol

Execute the automated synchronization command from the repository root:

```bash
uv sync --all-groups
```

This single command deterministically executes:
1. Virtual environment initialization at `.venv/` using Python 3.11.
2. Complete dependency graph resolution from `uv.lock`.
3. Editable installation of the `assessment_engine` package (`pip install -e .`), enabling absolute native namespace resolution (`from assessment_engine...`) without dynamic `sys.path` manipulation.

---

## 3. Cloud Runtime Environment Configuration

Vertex AI LLM inference harnesses (`src/assessment_engine/infrastructure/runtime_env.py`) inspect the shell environment for authentication variables:

| Environment Variable | Default Fallback Value | Purpose |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | `sub403o4u0q5` | Target Google Cloud project hosting Vertex AI foundation model endpoints. |
| `GOOGLE_CLOUD_LOCATION` | `europe-west1` | Target Google Cloud compute region for low-latency inference. |
| `GOOGLE_APPLICATION_CREDENTIALS`| `~/.secrets/sa-key.json` | Filesystem path to the GCP service account credentials key. |

To export custom credentials in local sub-shells:
```bash
export GOOGLE_CLOUD_PROJECT="my-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="europe-west1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

---

## 4. Preflight Certification Oracles

Following environment provisioning, autonomous agents and operators MUST execute the three-stage preflight certification:

### Stage 4.1: Environment Import Sanity Check
Asserts that virtual environment mapping and core dependency libraries (`openpyxl`, `pydantic`) resolve natively:
```bash
python -m pytest tests/unit/test_environment.py -q
```

### Stage 4.2: Full Regression Test Suite
Executes the comprehensive unit and integration verification suites:
```bash
pytest tests/ -q
```

### Stage 4.3: Canonical Smoke Dry-Run
Verifies physical pipeline orchestration and OpenXML deliverable assembly without invoking external network LLMs:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --with-global --dry-run
```

---

## 5. Provisioning Acceptance Invariants (Definition of Done)

The environment setup is certified as `Fulfilled` when all four invariants hold:
1. **Absolute Importability:** `python -c "import assessment_engine"` executes with return code `0`.
2. **Zero Test Regressions:** `pytest tests/unit/` passes with 100% green status.
3. **Dry-Run Readiness:** `regenerate_smoke_artifacts --dry-run` completes without missing template exceptions.
4. **Pre-commit Gate Active:** Git pre-commit hooks installed via `pre-commit install`.
