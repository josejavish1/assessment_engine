---
status: Verified
owner: docs-governance
source_of_truth:
- docs/SYSTEM_ARCHITECTURE.md
- docs/contracts/payload-render-boundaries.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: editorial
notes: Master index and governance policy for Architecture Decision Records (ADRs).
---
# Architecture Decision Records (ADR) Master Index

Canonical index documenting the architectural decisions, trade-offs, and immutable constraints governing `assessment-engine`.

---

## 1. Governance Standard: MADR (Markdown Architecture Decision Records)

Autonomous AI agents and engineers operating in this repository MUST consult the ADR registry before proposing structural changes. An approved ADR represents an **immutable architectural contract**. Proposals contradicting an accepted ADR are rejected unless a new superseding ADR is formally drafted, reviewed, and accepted.

### Decision Status Lifecycle:
- **`Proposed`:** Draft under review; non-binding.
- **`Accepted`:** Formally approved; binding invariant across code and documentation.
- **`Superseded`:** Obsolete; replaced by a subsequent numbered ADR.
- **`Deprecated`:** Retired without replacement.

---

## 2. Active ADR Registry

| ADR ID & Title | Status | Date | Core Invariant & Boundary Constraint |
|---|:---:|:---:|---|
| [`0001-exclusive-docx-monism.md`](0001-exclusive-docx-monism.md) | **Accepted** | 2026-10-15 | All customer deliverables compile strictly to Microsoft Word (`.docx`). PDF generation and ephemeral HTML web presentations are permanently banned. |
| [`0002-sqlite-epistemic-graph-wal.md`](0002-sqlite-epistemic-graph-wal.md) | **Accepted** | 2026-10-20 | Epistemic graph assertions and audit event ledgers persist in local SQLite with Write-Ahead Logging (WAL), eliminating external database dependencies. |
| [`0003-single-pass-policy-compiler.md`](0003-single-pass-policy-compiler.md) | **Accepted** | 2026-11-01 | Domain, actuarial, and regulatory constraints enforce via a deterministic single-pass policy compiler (`SovereignPolicyEngine`) prior to presentation layout. |

---

## 3. Mandatory Structure for New ADRs

Every new ADR added to `docs/adr/` must follow the numbering convention `NNNN-<slug>.md` and declare:

```markdown
# NNNN. Title of Decision

- **Status:** Proposed | Accepted | Superseded by [NNNN]
- **Date:** YYYY-MM-DD
- **Deciders:** Principal Architect / Autonomous Arbiter

## Context & Problem Statement
[Technical background and motivation for change]

## Decision Drivers
[Key architectural forces, constraints, and requirements]

## Considered Options
1. [Option 1]
2. [Option 2]

## Decision Outcome
Chosen option: [Option X], because [justification].

### Positive Consequences
- [Benefit 1]

### Negative Consequences & Trade-offs
- [Trade-off 1]
```
