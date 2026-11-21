---
status: Verified
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: editorial
notes: Canonical index and routing map for AI agent governance and context adapters.
---
# AI Agent Governance & Context Specifications Index

Canonical index documenting the automated governance policies, agent prompt adaptations, and context injection rules for autonomous LLM agents operating across `assessment-engine`.

---

## 1. AI Governance Specifications Routing Matrix

| Specification | Epistemic Role | Primary Invariants | Enforced Tools |
|---|---|---|---|
| [`documentation-governance.md`](documentation-governance.md) | Universal Governance Policy | Monolithic corpus, front matter parity, freshness decay, and source-linked review gates | `validate_documentation_governance.py` |

---

## 2. Invariant Context Hierarchy

Autonomous AI agents (Gemini, Claude, Copilot) MUST consult `documentation-governance.md` to resolve documentation lifecycle states, verification modes, and pull request review obligations.
