---
status: Verified
owner: docs-governance
source_of_truth:
- docs/documentation-map.yaml
- src/assessment_engine/application/tools/validate_documentation_governance.py
- .github/workflows/quality.yml
last_verified_against: 2026-11-21
applies_to:
- repository
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Documentation directory index and map overview.
---
# Documentation Master Index

This directory represents the **epistemic knowledge graph and canonical specification layer** of `assessment-engine`. It serves exclusively as the deterministic retrieval substrate for autonomous AI agents and execution runtimes.

---

## 1. Single Source of Truth (SSOT) Axiomatic Hierarchy

When resolving epistemic dissonance, schema drift, or behavioral ambiguity across the codebase, agents MUST evaluate authority according to the strict total order:

$$\text{Code (L0)} \succ \text{Contracts (L1)} \succ \text{Architecture (L1)} \succ \text{Operations (L2)} \succ \text{Audits/Reference (L3)} \succ \text{Adapters (L4)}$$

| Tier | Layer Classification | Concrete Artifacts | Epistemic Invariant |
|---|---|---|---|
| **L0** | Executable Runtime | `src/assessment_engine/domain/schemas/`, pytest suites, CI workflows | Immutable ground truth; overrides all prose and derived documentation. |
| **L1** | Canonical Specifications | `docs/contracts/`, `docs/architecture/`, `docs/SYSTEM_ARCHITECTURE.md` | Formal design invariants, payload contracts, and system topology. |
| **L2** | Operational Runbooks | `docs/operations/` | Deterministic CLI recipes, execution sequences, and recovery procedures. |
| **L3** | Reference & Audits | `docs/reference/`, `docs/audits/` | Generated catalogs, forensic audit results, and historical certificates. |
| **L4** | Agent Operational Adapters | `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md` | Model-specific context injection limits; strictly prohibited from defining new truth. |

---

## 2. Deterministic Subtree Routing Graph

Autonomous agents navigating this repository MUST route context retrieval according to the following directed mapping:

| Target Domain | Canonical Entrypoint | Invariant Scope | Primary Ground Truth Source |
|---|---|---|---|
| **System Architecture** | [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) | High-level data pipelines, hexagonal topology, execution boundaries | `src/assessment_engine/application/`, `src/assessment_engine/mcp_server.py` |
| **Component Architecture** | [`architecture/README.md`](architecture/README.md) | Single-tower flows, RAGE engine, epistemic graphs, policy engine | `src/assessment_engine/domain/`, `src/assessment_engine/infrastructure/` |
| **Data Contracts & Payloads** | [`contracts/artifact-contracts.md`](contracts/artifact-contracts.md) | Pydantic model schemas, OpenXML rendering boundaries, tower payloads | `src/assessment_engine/domain/schemas/` |
| **Operational Procedures** | [`operations/README.md`](operations/README.md) | Environment setup, pipeline execution, CI/CD quality gates, triage | `pyproject.toml`, `.github/workflows/`, CLI entrypoints |
| **Governance & Machine Policy** | [`ai/documentation-governance.md`](ai/documentation-governance.md) | Front matter metadata rules, freshness enforcement, verification modes | `docs/documentation-map.yaml`, `validate_documentation_governance.py` |
| **Architecture Decision Records** | [`adr/README.md`](adr/README.md) | Immutable records of architectural decisions and invariants | System design & code invariants |
| **Machine Registry** | [`documentation-map.yaml`](documentation-map.yaml) | YAML manifest of all governed files, owners, and dependency trees | Invariant check across repository via CI |

---

## 3. Mandatory Document Metadata Schema

Every governed Markdown file in `docs/` MUST declare strict YAML front matter matching the following schema:

```yaml
---
status: Verified | Needs Review | Draft | Deprecated
owner: docs-governance | engineering | actuarial
source_of_truth:
  - relative/path/to/source/file_or_schema
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

## 4. Automated Verification & Auto-Healing Pipeline

Documentation validity is deterministically enforced by automated tools:

1. **Governance & Link Integrity:**
   ```bash
   python src/assessment_engine/application/tools/validate_documentation_governance.py --repo-root . --documentation-map docs/documentation-map.yaml --today $(date -u +%F)
   ```
2. **Schema & Contract Auto-Healing:**
   ```bash
   python src/assessment_engine/application/tools/validate_contracts_schemas.py --repo-root . --documentation-map docs/documentation-map.yaml --autofix
   ```
3. **Executable Code Snippet Validation:**
   ```bash
   python src/assessment_engine/application/tools/validate_documentation_snippets.py --repo-root . --documentation-map docs/documentation-map.yaml
   ```
4. **Style & Linguistic Guardrails:**
   ```bash
   python src/assessment_engine/application/tools/lint_documentation_style.py --repo-root . --documentation-map docs/documentation-map.yaml
   ```

---

## 5. Epistemic Drift Resolution Protocol

When an agent detects a discrepancy between prose documentation and executable code:

1. **Step 1 (Source Extraction):** Read `source_of_truth` declared in the target document front matter.
2. **Step 2 (Structural Diff):** Compare Pydantic schema signatures or AST tokens against the documented Markdown tables.
3. **Step 3 (Authoritative Reconciliation):** The code in `src/assessment_engine/` is ground truth. Apply automatic contract reconciliation via `validate_contracts_schemas.py --autofix` or downgrade status to `Needs Review`.
4. **Step 4 (Anti-Hallucination Guard):** NEVER patch code to fit unverified documentation prose. Code changes require formal issue tracking and regression tests.
