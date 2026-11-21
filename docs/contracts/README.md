---
status: Verified
owner: docs-governance
source_of_truth:
- docs/contracts/artifact-contracts.md
- docs/contracts/payload-render-boundaries.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical index and routing map for data contracts, Pydantic schemas, and tool specifications.
---
# Data Contracts & Schemas Index

Canonical index documenting the structural boundaries, data schemas, and tool contracts governing `assessment-engine`.

---

## 1. Contracts Routing Matrix

Autonomous agents interacting with intermediate payloads or presentation compilers MUST adhere to these canonical contracts:

| Contract Specification | Domain & Focus | Pydantic Schema Model | Target Consumer |
|---|---|---|---|
| [`artifact-contracts.md`](artifact-contracts.md) | Lifecycle producer/consumer catalog, stage exit criteria, and SSOT authority | `src/assessment_engine/domain/schemas/` | Pipeline orchestrators, CI quality gates |
| [`payload-render-boundaries.md`](payload-render-boundaries.md) | Strict boundary rules separating data calculation from presentation compilers | `payload_to_ast.py`, `docx_compiler.py` | AST layout compilers, presentation adapters |
| [`tower-blueprint-payload.md`](tower-blueprint-payload.md) | Tower Blueprint Single Source of Truth (SSOT) data contract | `BlueprintPayload` (`schemas/blueprint.py`) | Single-tower synthesizers, global aggregators |
| [`tower-annex-payload.md`](tower-annex-payload.md) | Executive Tower Annex presentation payload contract | `AnnexPayload` (`schemas/annex_synthesis.py`) | Annex synthesizers, OpenXML compilers |
| [`tower-annex-design.md`](tower-annex-design.md) | Standard 8-section layout, typography, and styling constraints | `AnnexPayload` & OpenXML AST rules | OpenXML document layout compilers |
| [`rage-rubric-payload.md`](rage-rubric-payload.md) | Declarative regulatory framework rubric contract | `FrameworkRubric` (`schemas/rubric.py`) | RAGE empirical benchmarking engine |
| [`mcp-tool-schemas.md`](mcp-tool-schemas.md) | FastMCP JSON-RPC tool parameter and return schemas | FastMCP tool function signatures | External AI agents, Cursor/IDE orchestrators |

---

## 2. Invariant Verification Oracles

Contracts are verified mechanically:
```bash
# Verify parity between Markdown contract tables and physical Pydantic models
python src/assessment_engine/application/tools/validate_contracts_schemas.py --repo-root . --documentation-map docs/documentation-map.yaml
```
