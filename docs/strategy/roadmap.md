---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/operations/engineering-quality-gates.md
- src/assessment_engine/mcp_server.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Thematic product and infrastructure roadmap structured across Now, Next, and Later horizons.
---
# Product & Infrastructure Roadmap: The Sovereign Engine

Canonical strategic specification detailing the product evolution, platform infrastructure milestones, and thematic horizons (**Now, Next, Later**) across `assessment-engine`.

---

## 1. Architectural Boundary: Platform Kernel vs. Domain Applications

To ensure the platform remains modular and reusable across diverse enterprise portfolios, the architecture enforces a strict division:

- **Sovereign Engine (Platform Layer):** Low-level execution substrate. Manages tenant isolation, asynchronous orchestration, checkpointing, OpenXML AST compilation primitives, and telemetry. Contains zero domain-specific client heuristics.
- **Business Applications (Domain Layer):** Methodological implementations built *on top* of the platform. Defines Pydantic data schemas, technology tower rubrics, CMMI maturity scales, and client deliverables (`.docx`).

---

## 2. Thematic Engineering Horizons

```text
===================================================================================================
|  NOW (Active & Baseline)  ──►  NEXT (Planned Enhancements)  ──►  LATER (Future Strategic North) |
===================================================================================================
```

### Horizon 1: NOW (Active & Certified Baseline)
*Objective: Solidify local agent determinism, enforce client data sovereignty, and eliminate stochastic vibe-scoring.*

- **Quality Gate Compliance [Active]:** Automated CI gates and local preflight checkers blocking commits when code drifts from established Golden Paths.
- **Token Budgeting & Prompt Caching [Active]:** Strict `max_output_tokens` enforcement per agent persona in `model_profiles.json` and Vertex AI caching.
- **Empirical RAGE Engine [Active]:** Grounded external regulatory benchmarking combining OSINT search with local PDF snapshotting to eliminate ungrounded scoring.
- **Ephemeral Sandbox Isolation [Active]:** Multi-tenant isolation enforced via `TenantWorkspace` records in `src/assessment_engine/infrastructure/runtime_paths.py`.

---

### Horizon 2: NEXT (Protocols, Automation & Developer Control Plane)
*Objective: Expose pipeline execution through open agentic protocols and automate continuous code refactoring.*

- **Universal FastMCP Developer Control Plane:** Complete tool exposure of all CLI and compiler capabilities via `src/assessment_engine/mcp_server.py` for direct agent interaction in Cursor and VS Code.
- **Tier-1 English Kernel Architecture:** Full decoupling of the software core into 100% Technical English, delegating multilingual delivery to declarative catalogs (`locales.json`) and OpenXML AST layout engines.
- **Autonomous Doctor Diagnostic Loop:** Decoupling defect diagnosis from implementation agents. Diagnostic analyzers evaluate Pytest failures and provide explicit repair plans to coding sub-agents.
- **Dynamic Human-in-the-Loop (HITL) Gates:** Interactive action gates (`authorize_action_gate`) pausing execution upon critical architectural ambiguity until an operator provides explicit authorization.

---

### Horizon 3: LATER (Autonomous Stigmergic Governance)
*Objective: Scale the platform to a decentralized, neuro-symbolic enterprise digital twin.*

- **Cryptographic Liability Attestations (EU AI Act):** Automated compliance signers emitting immutable SHA-256 audit attestations binding compiled deliverables to input data hashes and engine commit states under Article 14 of the EU AI Act.
- **Digital Stigmergy (Shared Epistemic Graph):** Eliminating hierarchical message bottlenecks; multiple autonomous agents coordinate asynchronously by reading and writing semantic assertions to a shared knowledge graph.
- **Temporal Episodic Memory:** Long-term digital twins supporting Time-to-Live (TTL) decay across enterprise technology observations, enabling continuous organizational assessment.
