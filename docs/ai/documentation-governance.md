---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain
- tests
- pyproject.toml
- .github/workflows/ci.yml
- docs/documentation-map.yaml
review_when_source_changes:
- .github/pull_request_template.md
- .github/CODEOWNERS
- .github/workflows/docs-governance.yml
- src/assessment_engine/application/tools/validate_documentation_governance.py
- docs/documentation-map.yaml
review_paths_on_source_change:
- docs/ai/documentation-governance.md
- docs/README.md
- .github/pull_request_template.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Neutral core governance policy for documentation and context adapters.
---
# Documentation Governance Policy

Canonical policy defining ingestion, verification, schema synchronization, and lifecycle management of documentation across the `assessment-engine` repository.

---

## 1. Core Governance Invariants

1. **Monolithic Unified Corpus:** A single source of truth exists across the repository. AI agents and human contributors read and update identical documentation assets. Parallel or unmonitored knowledge bases are strictly prohibited.
2. **Runtime Code Primacy:** Executable artifacts (Pydantic schemas, unit/integration test suites, CI/CD workflows, configuration registries) constitute the primary ground truth ($L_0$). Prose specifications ($L_1$) MUST conform to code, never vice versa.
3. **Adapter Invariance:** Agent-specific operational adapters (`AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`) project context limits and behavioral constraints. They are strictly prohibited from defining new architectural facts, APIs, or business logic.
4. **Empirical Verification Requirement:** Unimplemented or speculative features MUST NOT be documented as functional. Any capability lacking automated tests or executable confirmation must be classified as `Draft` or `Needs Review`.
5. **Zero-Entropy Rule:** Historical session logs, deliberation transcripts, temporary execution plans, and scratchpad files must not accumulate in `docs/`. Git commit history is the sole historical ledger.

---

## 2. Document Classification Schema

Every Markdown document in `docs/` is classified across orthogonal axes:

### A. Document Types (`doc_type`)
| Type | Semantic Scope | Mutability Rule |
|---|---|---|
| `canonical` | Architectural invariants, data contracts, and core policies. | Subject to strict source-linked reviews. |
| `operational` | Step-by-step procedures, runbooks, and installation guides. | Must execute with verifiable CLI commands. |
| `reference_generated` | Automated reports and generated data catalogs. | Derived deterministically from source code. |
| `archived` | Deprecated historical assets retained for lineage. | Read-only; frozen from further expansion. |

### B. Lifecycle Statuses (`status`)
| Status | Operational Definition | CI Action |
|---|---|---|
| `Verified` | Actively verified against physical codebase within max age limit. | Validated on PR and daily scheduled CI. |
| `Needs Review` | Usable but identified as having potential drift or pending verification. | Generates non-blocking warnings in health reports. |
| `Draft` | Incomplete initial draft; baseline architecture under formulation. | Excluded from strict freshness expiry gates. |
| `Deprecated` | Obsolete asset slated for retirement; replacement defined. | Warning raised if referenced by canonical docs. |

### C. Diataxis Forms (`diataxis`) & Verification Modes (`verification_mode`)
- **Diataxis:** `explanation` (architecture), `how_to` (runbooks), `reference` (catalogs/APIs), `tutorial` (onboarding).
- **Verification Mode:** `schema` (AST/Pydantic validation), `code` (snippet execution), `workflow` (CI verification), `editorial` (style linter), `mixed` (multi-probe validation).

---

## 3. Mandatory Front Matter Specification

Every governed Markdown file MUST declare valid YAML front matter conforming to the schema:

```yaml
---
status: Verified | Needs Review | Draft | Deprecated
owner: logical-owner-id
source_of_truth:
  - relative/path/to/source/file
last_verified_against: YYYY-MM-DD
applies_to:
  - humans
  - ai-agents
  - repository
doc_type: canonical | operational | reference_generated | archived
diataxis: explanation | how_to | reference | tutorial
verification_mode: schema | code | workflow | editorial | mixed
---
```

---

## 4. Source-Linked Review & Enforcement Rules

To eliminate silent technical drift, changes to critical codebase paths trigger mandatory documentation updates in pull requests:

| Changed Codebase Area | Mandatory Document Review Target |
|---|---|
| `src/assessment_engine/application/**`, `mcp_server.py` | `docs/SYSTEM_ARCHITECTURE.md`, `docs/architecture/` |
| `src/assessment_engine/domain/schemas/**` | `docs/contracts/` |
| `.github/workflows/**` | `docs/operations/ci-cd-workflows.md`, `docs/operations/` |
| `pyproject.toml`, `uv.lock` | `docs/operations/installation.md` |
| `engine_config/**` | `docs/architecture/` |

### CI Automated Verification Gates
GitHub Actions (`.github/workflows/docs-governance.yml`) and pre-commit hooks enforce:
1. **Front Matter Parity:** Document front matter MUST match its registered entry in `docs/documentation-map.yaml`.
2. **Freshness Enforcement:** Any `Verified` document whose `last_verified_against` exceeds `verified_max_age_days` (180 days) fails CI.
3. **Link & Anchor Integrity:** Broken Markdown links, invalid GitHub anchors, and missing target files cause deterministic test failures.
4. **Hype Language Suppression:** Prohibits marketing language, buzzwords, and unsubstantiated claims in `Verified` documentation.
5. **Contract Auto-Healing:** Discrepancies between Pydantic schemas and documented Markdown tables are flagged or automatically resolved via `validate_contracts_schemas.py --autofix`.

---

## 5. Agent Operational Execution Rules

Autonomous agents interacting with this repository MUST adhere to the following sequence:

1. **Ingest Canonical Index:** Read `README.md`, `docs/README.md`, and `docs/SYSTEM_ARCHITECTURE.md` before initiating changes.
2. **Verify Ground Truth:** Trace all assumptions to source files in `src/assessment_engine/domain/schemas/` or `engine_config/`.
3. **No Unilateral Adapter Mutation:** Do NOT add new project requirements or architecture rules to `GEMINI.md` or `AGENTS.md`. Canonical updates belong in `docs/`.
4. **Synchronize Documentation Map:** When introducing a new document or updating a document's verification status, update `docs/documentation-map.yaml` atomically.
