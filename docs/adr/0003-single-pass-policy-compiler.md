---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/policy_engine.py
- docs/architecture/policy-engine-architecture.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: editorial
notes: ADR 0003 accepting single-pass deterministic policy compilation via SovereignPolicyEngine.
---
# ADR 0003: Deterministic Single-Pass Policy Compilation (`SovereignPolicyEngine`)

- **Status:** Accepted
- **Date:** 2026-11-01
- **Deciders:** Principal Architect / Sovereign Engineering Board

---

## 1. Context & Problem Statement

Large Language Models (LLMs) frequently hallucinate during multi-pillar synthesis. Common pathologies include:
- Generating redundant initiatives across multiple technology towers (e.g., duplicated cloud governance tasks).
- Violating physical sequencing rules (e.g., scheduling production cutovers before foundational identity architectures exist).
- Neglecting critical infrastructure regulatory perimeters (e.g., proposing software firewalls where hardware data diodes are legally mandated).
- Omitting provenance citations linking remediation projects back to discovered evidence.

Prompt engineering alone fails to guarantee 100% compliance with non-negotiable architectural axioms.

---

## 2. Decision Drivers

- **Zero-Tolerance Invariant Enforcement:** Critical business and compliance rules must enforce with mathematical certainty (100% pass rate).
- **Execution Speed:** Policy checks must execute within milliseconds without making secondary network LLM calls.
- **Audit Defensibility:** Transformation plans presented to enterprise boards must be backed by deterministic rule verification.

---

## 3. Considered Options

| Option | Invariant Guarantee | Latency Overhead | Architecture Cleanliness | Verdict |
|---|:---:|:---:|:---:|:---:|
| **Option 1: Adversarial LLM Critic** | Probabilistic (<90%) | High (>60s API roundtrip) | Low (Stochastic loop) | Rejected |
| **Option 2: AST Hacks in Compilers** | Deterministic (100%) | Negligible | Low (Layering violation) | Rejected |
| **Option 3: Single-Pass Policy Compiler** | Deterministic (100%) | Microseconds (<50ms) | High (Upstream domain gate) | **Accepted** |

---

## 4. Decision Outcome

**Chosen Option: Option 3 (Single-Pass Deterministic Policy Compiler).**

`SovereignPolicyEngine` (`src/assessment_engine/infrastructure/policy_engine.py`) intercepts candidate blueprints before disk persistence and applies 8 registered deterministic policy passes (deduplication, chronological sequencing, OT hardware data diodes, reverse traceability, sanitization, and FAIR risk modeling).

### Positive Consequences:
- **Zero Hallucination Escape:** Non-compliant initiatives are filtered, merged, or adjusted deterministically before deliverables compile.
- **Microsecond Latency:** Pure Python execution introduces $< 50\text{ms}$ overhead, avoiding multi-minute recursive LLM calls.
- **Architectural Separation:** Compilers remain pure presentation engines; all business governance centralizes upstream in `policy_engine.py`.

### Negative Consequences & Trade-offs:
- Engineers must write explicit Python logic in `POLICY_REGISTRY` to introduce new governance rules rather than simply modifying prompt text.
