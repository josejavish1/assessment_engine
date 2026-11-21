---
status: Verified
owner: docs-governance
source_of_truth:
- docs/SYSTEM_ARCHITECTURE.md
- src/assessment_engine/domain
- src/assessment_engine/application
- src/assessment_engine/mcp_server.py
- src/assessment_engine/domain/schemas
- tests
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Architecture directory index and canonical component specification map.
---
# Architecture Specification Index

Canonical subsystem index defining the modular architecture, execution boundaries, epistemic components, and pipeline data contracts of `assessment-engine`.

---

## 1. Subsystem Routing Matrix

Autonomous agents navigating architectural specifications MUST route context retrieval according to this deterministic mapping:

| Subsystem Domain | Specification Entrypoint | Epistemic Invariant Scope | Primary Implementation Source |
|---|---|---|---|
| **High-Level Flow** | [`assessment-factory-flow.md`](assessment-factory-flow.md) | End-to-end value chain from raw evidence to deliverable | `src/assessment_engine/application/` |
| **Single-Tower Lifecycle** | [`tower-pipeline.md`](tower-pipeline.md) | Phase 1 deterministic scoring, evidence analysis, and blueprint SSOT | `src/assessment_engine/application/run_tower_pipeline.py` |
| **Global & Commercial** | [`global-commercial-pipelines.md`](global-commercial-pipelines.md) | Multi-tower aggregation, Tomo 1 consolidation, and account action plan | `src/assessment_engine/application/run_global_pipeline.py` |
| **Client Intelligence** | [`client-intelligence.md`](client-intelligence.md) | Upstream context harvesting, corporate profiling, and vocabulary grounding | `src/assessment_engine/application/run_intelligence_harvesting.py` |
| **RAGE Benchmarking** | [`rage-architecture.md`](rage-architecture.md) | Adversarial evaluation, rubric validation, and hallucination containment | `src/assessment_engine/application/tools/agentic_benchmarker.py` |
| **Actuarial Policy Engine** | [`policy-engine-architecture.md`](policy-engine-architecture.md) | FAIR Bayesian copula modeling, TCO downtime calibration, Euler allocation | `src/assessment_engine/domain/actuarial/` |
| **Epistemic Graph** | [`epistemic-graph-architecture.md`](epistemic-graph-architecture.md) | SQLite event-sourcing ledger, CQRS projections, evidence traceability | `src/assessment_engine/infrastructure/epistemic_graph.py` |
| **Data Provenance** | [`data-provenance-ontology.md`](data-provenance-ontology.md) | Formal fact extraction, citation envelopes, and lexical boundary checks | `src/assessment_engine/domain/provenance/` |
| **Commercial Portal** | [`business-command-center-portal.md`](business-command-center-portal.md) | Next.js and Refine.dev portal client, auth challenge, sovereign sessions | `business_command_center/` |
| **Isolation Boundaries** | [`security-boundaries.md`](security-boundaries.md) | Tenant execution sandboxing, subprocess confinement, credential isolation | `src/assessment_engine/infrastructure/` |
| **Service Integration** | [`mcp-mode.md`](mcp-mode.md) | FastMCP tool server definitions, agentic supervisors, and JSON-RPC dispatch | `src/assessment_engine/mcp_server.py` |
| **Artifact Lifecycle** | [`working-artifacts.md`](working-artifacts.md) | Transient directory structure, payload hashing, and output isolation | `src/assessment_engine/infrastructure/runtime_paths.py` |
| **Critical Modules** | [`critical-modules.md`](critical-modules.md) | High-impact code paths, dependency graph, and regression hot spots | Core Python runtime modules in `src/` |

---

## 2. Execution Topologies

The system operates under two distinct execution surfaces:

### A. Linear Pipeline Orchestration
- **Application Modules:** `run_tower_pipeline.py`, `run_global_pipeline.py`, `run_commercial_pipeline.py`.
- **Control Pattern:** Sequential execution with transactional state barriers. Each stage verifies precondition JSON payloads against Pydantic schemas prior to invoking downstream LLM synthesis or compilation.

### B. Asynchronous FastMCP Server
- **Service Module:** `src/assessment_engine/mcp_server.py`.
- **Control Pattern:** Tool-based API exposing discrete pipeline stages (`get_tower_state`, `run_tower_stage`, `inspect_evidence_ledger`) for autonomous agent orchestrators.

---

## 3. Structural Layers & Component Mapping

| Architectural Layer | Physical Repository Path | Responsibility & Boundary Constraints |
|---|---|---|
| **Domain Schemas** | `src/assessment_engine/domain/schemas/` | Typed Pydantic models for all intermediate and deliverable payloads. Zero external dependencies. |
| **Domain Logic** | `src/assessment_engine/domain/` | Mathematical models (FAIR, TCO, CMMI), taxonomy resolvers, scoring engines. Pure Python business logic. |
| **Application Services** | `src/assessment_engine/application/` | Workflow orchestrators, LLM prompt execution harnesses, deterministic calculation stages. |
| **Adapters & Compilers** | `src/assessment_engine/adapters/` | OpenXML AST compilers (`docx_compiler.py`, `tomo_asis_ast_compiler.py`), CLI handlers. Strictly DOCX output. |
| **Infrastructure** | `src/assessment_engine/infrastructure/` | Vertex AI client, SQLite epistemic event graph, config loaders, runtime path resolvers. |
| **Declarative Config** | `engine_config/` | Enterprise registries, country labor rate cards, CMMI governance scales, prompt YAML templates. |

---

## 4. Architectural Invariant Checklists for AI Agents

When implementing modifications to this layer, agents MUST verify:

1. **Top-Down Monism:** Deliverable summaries must derive strictly from parent blueprints; recalculation of metrics in presentation adapters is prohibited.
2. **Strict Schema Validation:** Every payload transition must pass Pydantic validation via `validate_contracts_schemas.py`.
3. **Format Invariant:** Output generation is restricted to Microsoft Word (`.docx`). PDF and HTML generation are disabled.
4. **Zero-Entropy Rule:** Dynamic files must isolate into `workspaces/<client_id>/` or `working/out/<client_id>/`.
