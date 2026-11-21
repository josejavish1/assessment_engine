---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/blueprint.py
- src/assessment_engine/domain/schemas/annex_synthesis.py
- src/assessment_engine/domain/schemas/global_report.py
- src/assessment_engine/domain/schemas/commercial.py
- src/assessment_engine/application/run_tower_blueprint_engine.py
- src/assessment_engine/application/run_executive_annex_synthesizer.py
- src/assessment_engine/application/build_global_report_payload.py
- src/assessment_engine/application/run_executive_refiner.py
- src/assessment_engine/application/run_commercial_refiner.py
- src/assessment_engine/adapters/render_tower_blueprint.py
- src/assessment_engine/adapters/compilers/payload_to_ast.py
- src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
- src/assessment_engine/adapters/render_commercial_report.py
- src/assessment_engine/adapters/compilers/docx_compiler.py
- docs/contracts/payload-render-boundaries.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical reference specification of artifact contracts, lifecycle producers, consumers, and validation gates.
---
# Artifact Contracts & Quality Gate Specifications

Canonical reference specification defining the data schemas, producers, consumers, and validation gates for all intermediate payloads and final deliverables across `assessment-engine`.

---

## 1. Artifact Taxonomy & Authority Invariants

Every data artifact produced within `assessment-engine` is governed under four deterministic dimensions:
1. **Producer:** The specific application module responsible for synthesizing and validating the payload.
2. **Schema Contract:** The typed Pydantic model (`src/assessment_engine/domain/schemas/`) defining valid syntax and constraints.
3. **Consumer:** Downstream pipeline stages dependent on the artifact.
4. **Degradation Risk:** Operational and architectural failure modes emerging upon schema drift or omission.

### Hierarchical Conflict Resolution Axioms:
1. **JSON Overrides DOCX:** If a compiled Word document conflicts with its source JSON payload, **the JSON payload is authoritative**.
2. **Upstream Overrides Downstream:** If a downstream summary payload contradicts its parent blueprint, **the parent blueprint is authoritative**.
3. **Compilers Do Not Calculate:** Presentation compilers (`docx_compiler.py`, `tomo_asis_ast_compiler.py`) format pre-computed data; they are strictly prohibited from mutating or recalculating business metrics.

---

## 2. Master Artifact Contracts Matrix

| Artifact Path | Producer Module | Pydantic Schema / Type | Primary Consumer | Epistemic Role & Degradation Risk |
|---|---|---|---|---|
| `case_input.json` | `build_case_input.py` | `CaseInput` | `run_scoring.py`, `run_tower_blueprint_engine.py` | Normalized case telemetry and questionnaire responses. Failure results in unanchored pillar scoring. |
| `evidence_ledger.json` | `build_evidence_ledger.py` | `EvidenceLedger` | `run_evidence_analyst.py`, `policy_engine.py` | Content-addressable evidence fragments mapped to pillars. Omission destroys auditability and citation lineage. |
| `scoring_output.json` | `run_scoring.py` | `ScoringOutput` | `run_tower_blueprint_engine.py` | Quantitative maturity scores (1.0 to 5.0) per pillar. Failure breaks CMMI baseline calculations. |
| `findings.json` | `run_evidence_analyst.py` | `FindingsPayload` | `run_tower_blueprint_engine.py` | Structured technical gaps and observations. Omission forces blueprints into generic hallucinations. |
| `benchmarks_snapshot.json` | `agentic_benchmarker.py` | `IndustryBenchmarksSnapshot` | `run_tower_blueprint_engine.py` | Empirical external regulatory benchmarks. Failure triggers fallback to default baseline scores. |
| `client_intelligence.json` | `run_intelligence_harvesting.py` | `ClientDossierV3` | All pipelines | Enterprise profile, strategic agenda, and vendor context. Failure degrades executive specificity. |
| `blueprint_<tower>_payload.json` | `run_tower_blueprint_engine.py` | `BlueprintPayload` | Annex synthesizer, global builder, blueprint compiler | **Tower Single Source of Truth (SSOT)**. Omission corrupts all downstream deliverables. |
| `approved_annex_<tower>.template_payload.json` | `run_executive_annex_synthesizer.py` | `AnnexPayload` | `payload_to_ast.py`, `docx_compiler.py` | Executive summary payload derived from blueprint SSOT. Failure prevents annex DOCX compilation. |
| `global_report_payload.json` | `build_global_report_payload.py` | `GlobalReportPayload` | `run_executive_refiner.py`, `tomo_asis_ast_compiler.py` | **Global Consolidated SSOT**. Aggregates all tower blueprints for C-level reporting. |
| `commercial_report_payload.json` | `run_commercial_refiner.py` | `CommercialReportPayload` | `render_commercial_report.py` | **Commercial Strategy SSOT**. Correlates technical gaps with staffing rate cards. |
| `Anexo_<tower>_ASIS_<client>.docx` | `docx_compiler.py` | OpenXML Binary | Client / Sponsor | Compiled technical annex deliverable. |
| `Blueprint_Transformacion_<tower>_<client>.docx` | `render_tower_blueprint.py` | OpenXML Binary | Enterprise Architects | Compiled transformation blueprint deliverable. |
| `Tomo_1_Diagnostico_ASIS_<client>.docx` | `tomo_asis_ast_compiler.py` | OpenXML Binary | C-Suite / Executive Board | Compiled consolidated diagnostic deliverable. |
| `Account_Action_Plan_<client>.docx` | `render_commercial_report.py` | OpenXML Binary | Account & Presales Teams | Compiled commercial strategy deliverable. |

---

## 3. Stage-by-Stage Quality Gate Exit Criteria

A pipeline stage may transition to downstream dependents ONLY when its output artifacts satisfy four verifiable criteria:

| Pipeline Stage | Mandatory Gate Exit Conditions | Automated Verification Oracle |
|---|---|---|
| **Deterministic Prep** | `case_input.json` and `evidence_ledger.json` present on disk with valid JSON schema. | File existence check & JSON parser verification. |
| **Scoring & Findings** | `scoring_output.json` contains scores $\in [1.0, 5.0]$ across all declared pillars. | `validate_contracts_schemas.py` |
| **Blueprint Synthesis** | `blueprint_<tower>_payload.json` passes `BlueprintPayload` schema and passes all 8 `SovereignPolicyEngine` passes. | `BlueprintPayload.model_validate()` |
| **Annex Synthesis** | `approved_annex_<tower>.template_payload.json` perfectly mirrors maturity scores and initiatives from blueprint SSOT. | Invariant check: $\text{Annex.score} == \text{Blueprint.overall\_score}$. |
| **Global Consolidation** | `global_report_payload.json` aggregates 100% of active tower blueprints in `blueprint-only` mode. | `GlobalReportPayload.model_validate()` |
| **Commercial Plan** | `commercial_report_payload.json` contains non-empty opportunity pipelines with explicit sizing ($S, M, L, XL$). | `CommercialReportPayload.model_validate()` |
| **AST Compilation** | Generated `.docx` files unpack cleanly as valid ZIP archives containing well-formed `word/document.xml`. | `docx.Document(output_path)` smoke check. |

---

## 4. Definition of Done: Certified Contract Status

An artifact contract is formally certified as `Fulfilled` when:
1. **Physical Presence:** The file exists at its deterministic workspace path (`workspaces/<client>/`).
2. **Schema Compliance:** The JSON payload passes automated validation against its canonical Pydantic model (`validate_contracts_schemas.py`).
3. **Direct Ingestion:** Consuming downstream modules ingest the payload without fallback normalization exceptions.
4. **Monistic Alignment:** Numerical metrics match across all parent and child payload projections without mathematical divergence.
