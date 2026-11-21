---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/annex_synthesis.py
- src/assessment_engine/domain/schemas/blueprint.py
- src/assessment_engine/domain/schemas/global_report.py
- src/assessment_engine/domain/schemas/commercial.py
- src/assessment_engine/domain/schemas/rubric.py
- src/assessment_engine/infrastructure/agentic_benchmarker.py
- src/assessment_engine/infrastructure/contract_utils.py
- src/assessment_engine/adapters/compilers/payload_to_ast.py
- src/assessment_engine/adapters/render_tower_blueprint.py
- src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
- src/assessment_engine/adapters/render_commercial_report.py
- src/assessment_engine/adapters/compilers/docx_compiler.py
enforce_on_source_changes: true
review_paths_on_source_change:
- docs/contracts/payload-render-boundaries.md
- docs/contracts/artifact-contracts.md
- docs/architecture/tower-pipeline.md
- docs/architecture/global-commercial-pipelines.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical technical specification of the structural boundaries between JSON payloads, Pydantic schemas, and OpenXML AST compilers.
---
# Payload, Schema, and Presentation Compiler Boundaries

Canonical specification defining the architectural boundaries, enforcement rigors, and responsibilities separating structured JSON payloads, Pydantic domain schemas, and OpenXML Abstract Syntax Tree (AST) presentation compilers.

---

## 1. Foundational Boundary Law: Zero Business Logic in Presentation Layers

Presentation compilers (`payload_to_ast.py`, `docx_compiler.py`, `tomo_asis_ast_compiler.py`, `render_commercial_report.py`) are strictly layout and serialization engines. They are **never sources of business truth**:

```
[ Pydantic Domain Schemas: schemas/*.py ]
                     |
                     v (Validates)
[ Structured JSON Payload: workspaces/<client>/ ]
                     |
                     v (Ingested Read-Only)
+---------------------------------------------------------------------------------------+
| DECLARATIVE AST COMPILERS: adapters/compilers/                                        |
| 1. payload_to_ast.py               --> Transforms JSON to Typed Document AST nodes    |
| 2. docx_compiler.py                 --> Serializes AST into OpenXML .docx binaries    |
| 3. tomo_asis_ast_compiler.py        --> Direct OpenXML assembly for Tomo 1 deliverable|
+---------------------------------------------------------------------------------------+
                     |
                     v (Strict OpenXML Binary Output)
[ Word Deliverables: Anexo_*.docx, Tomo_1_*.docx, Account_Action_Plan_*.docx ]
```

### Absolute Operational Invariants:
1. **No Metric Mutation:** Compilers format pre-computed data. Recalculating scores, recomputing loss expectations, or modifying quantitative maturity bands (`score -> band`) within a compiler is strictly prohibited.
2. **Upstream Resolution:** All qualitative maturity band translations must execute deterministically upstream using `maturity_band.py` and `global_maturity_policy.py`.
3. **Format Monism:** Presentation compilers compile exclusively to Microsoft Word (`.docx`). Generation of PDF or ephemeral web presentations is disabled.

---

## 2. Compiler Boundary & Schema Mapping Matrix

| Pipeline Channel | Canonical JSON Payload | Pydantic Schema Model | Target Compiler Adapter | Output Binary Deliverable |
|---|---|---|---|---|
| **Tower Technical Annex** | `approved_annex_<tower>.template_payload.json` | `AnnexPayload` | `payload_to_ast.py` + `docx_compiler.py` | `Anexo_<tower>_ASIS_<client>.docx` |
| **Tower Transformation Blueprint** | `blueprint_<tower>_payload.json` | `BlueprintPayload` | `render_tower_blueprint.py` | `Blueprint_Transformacion_<tower>_<client>.docx` |
| **Global Executive Diagnostic** | `global_report_payload.json` | `GlobalReportPayload` | `tomo_asis_ast_compiler.py` | `Tomo_1_Diagnostico_ASIS_<client>.docx` |
| **Commercial Strategy Plan** | `commercial_report_payload.json` | `CommercialReportPayload` | `render_commercial_report.py` | `Account_Action_Plan_<client>.docx` |
| **Empirical Benchmarks** | `benchmarks_snapshot.json` | `IndustryBenchmarksSnapshot`| Ingested by `run_tower_blueprint_engine.py` | Grounding evidence in blueprints |

---

## 3. Separation of Responsibilities

### Permitted in Payloads & Domain Schemas:
- Structural definition of fields, data types, and enum cardinality.
- Pydantic validation rules (`@field_validator`, `@model_validator`).
- Calculation of quantitative averages, risk distributions, and initiative prioritization.
- Ingestion of client profile variables and provenance citations.

### Permitted in Presentation Compilers:
- Layout construction: page margins, header/footer insertion, section breaks, and table grid layouts.
- Typography: font styling, text sizing, bullet point formatting, and callout box borders.
- Strict Hyphen Invariant: Enforcement of short hyphens (ASCII 0x2D), blocking em-dashes and en-dashes.
- Image embedding: insertion of pre-generated vector radar chart binaries (`pillar_radar_chart.generated.png`).

### Strictly Prohibited in Presentation Compilers:
- Providing default fallbacks for missing business-critical metrics.
- Re-scoring or re-weighting pillars.
- Inventing new transformation initiatives omitted by upstream blueprints.

---

## 4. Contract Violation & Quality Gate Oracles

The boundary between payloads and compilers is enforced automatically:

1. **Pre-Render Validation:** Compilers execute strict schema verification (`model_validate()`) prior to AST generation. Payloads failing schema validation trigger immediate transaction aborts.
2. **Deterministic Auto-Healing:** Pre-commit and CI gates execute `validate_contracts_schemas.py --autofix` to verify that Markdown contract tables perfectly match physical Pydantic model attributes.
3. **AST Unit Testing:** Tests in `tests/integration/test_validate_contracts_schemas.py` assert structural correspondence between schemas and AST compiler classes.
