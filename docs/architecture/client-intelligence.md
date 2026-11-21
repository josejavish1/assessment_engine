---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/intelligence.py
- src/assessment_engine/infrastructure/client_intelligence.py
- src/assessment_engine/application/run_intelligence_harvesting.py
- src/assessment_engine/application/build_case_input.py
- src/assessment_engine/application/run_tower_blueprint_engine.py
- src/assessment_engine/application/build_global_report_payload.py
- src/assessment_engine/application/run_executive_refiner.py
- src/assessment_engine/application/run_commercial_refiner.py
- src/assessment_engine/domain/prompts/intelligence_prompts.py
- src/assessment_engine/domain/prompts/commercial_prompts.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Architecture specification of the shared client intelligence dossier and downstream consumption.
---
# Client Intelligence Architecture

Canonical specification defining the schema, lifecycle, data contracts, and downstream consumption of `client_intelligence.json` across the `assessment-engine` platform.

---

## 1. Epistemic Role & Lifecycle Boundaries

The client intelligence dossier (`client_intelligence.json`) acts as the **cross-cutting semantic grounding layer** of the platform. It provides verified corporate, strategic, and regulatory facts to constrain LLM prompts and deterministic calculators:

```
[Raw Inputs: Transcripts, Questionnaires, Corporate Reports]
                            |
                            v
           run_intelligence_harvesting.py
                            |
                            v
       [ workspaces/<client_id>/client_intelligence.json ]
                            |
         +------------------+------------------+
         |                  |                  |
         v                  v                  v
  Single-Tower Stage   Global Synthesis    Commercial Plan
(build_case_input.py) (run_executive_refiner) (run_commercial_refiner)
```

- **Physical Path:** Deterministically located at `workspaces/<client_id>/client_intelligence.json` (or `working/<client_id>/client_intelligence.json`).
- **Generation Engine:** Ingested and synthesized by `run_intelligence_harvesting.py` via bounded AI prompts in `intelligence_prompts.py`.
- **Primary Invariant:** Downstream modules MUST consume this dossier to inherit organizational context, vendor footprints, and regulatory obligations without re-prompting upstream evidence.

---

## 2. Formal Schema Architecture: `ClientDossierV3`

Defined in `src/assessment_engine/domain/schemas/intelligence.py`, the canonical `ClientDossierV3` model enforces five structured partitions:

| Structural Partition | Model Type / Fields | Epistemic Invariant |
|---|---|---|
| **Metadata** | `metadata: Dict[str, Any]` | Cryptographic digest, creation timestamp, target locale, and harvest lineage. |
| **Corporate Profile** | `profile: ClientProfile` | Industry vertical, financial classification tier, operating model (centralized vs federated), and geographic footprint. |
| **Business Context** | `business_context: BusinessHarvest` | Strategic CEO priorities, active transformation programs, budget boundaries, and planning horizon (`TransformationHorizonV3`). |
| **Technology Context**| `technology_context: TechHarvest` | Dominant enterprise vendors, legacy footprint, infrastructure obsolescence, and security incident history. |
| **Tower Overrides** | `tower_overrides: Dict[str, TowerOverride]` | Customized target maturity thresholds (1.0 to 5.0), business criticality, regulatory pressure, and operational urgency per tower. |
| **Epistemic Claims** | `claims: List[SourcedTextV3]` | Tri-state epistemic classification (`Fact`, `Inference`, `Assumption`), confidence score (`ConfidenceV3`), and exact evidence citation (`SourceV3`). |

---

## 3. Downstream Pipeline Consumption Graph

| Consuming Module | Pipeline Phase | Ingested Data Slice | Operational Impact |
|---|---|---|---|
| `build_case_input.py` | Single-Tower (Phase 1) | `tower_overrides`, `profile` | Derives `target_maturity_default` and prunes generic questions to match client IT operating model. |
| `run_tower_blueprint_engine.py` | Single-Tower (Phase 1) | `business_context`, `technology_context` | Injects client-specific technology names and strategic goals into prompt constraints; blocks generic vendor hallucinations. |
| `build_global_report_payload.py` | Global Aggregation (Phase 2) | Full `ClientDossierV3` | Hydrates the global report payload with group-level legal entities, multi-site distributions, and holding company structures. |
| `run_executive_refiner.py` | Global Refinement (Phase 2) | `business_context`, `claims` | Aligns Tomo 1 executive diagnostic text with CEO transformation priorities and verified regulatory pressures (e.g., NIS2, DORA). |
| `run_commercial_refiner.py` | Commercial Plan (Phase 3) | `profile`, `tower_overrides`, `claims` | Maps technical gaps to commercial initiatives, budget allocation models, and partner staffing rate cards (`rate_card.json`). |

---

## 4. Multi-Version Compatibility & Migration Engine

The platform maintains automated backward compatibility across legacy formats in `src/assessment_engine/infrastructure/client_intelligence.py`:

- **Schema V1 (Flat Legacy):** Unstructured dictionary with root-level `industry`, `ceo_agenda`, and `target_maturity_matrix`.
- **Schema V2 (Transition):** Introduces `ClientDossierV2` with basic `tower_overrides` and corporate profiling.
- **Schema V3 (Epistemic Monism):** Full `ClientDossierV3` supporting typed claims, confidence bounds, and provenance tracking.

The loader executes automatic up-casting:
```python
# Automatic normalization in client_intelligence.py
dossier: ClientDossierV3 = load_client_intelligence(client_id, workspace_dir)
```
When an older payload version is loaded from disk, the loader deterministically maps legacy attributes into their corresponding `ClientDossierV3` partitions without data loss.

---

## 5. Architectural Quality Gates & Invariants

Autonomous agents modifying the intelligence subsystem MUST verify:

1. **Schema Integrity:** Any schema modification in `schemas/intelligence.py` must maintain automated serialization to `ClientDossierV3`.
2. **No Hallucination Pass-Through:** Inferences in `claims` must retain an explicit `confidence` rating and reference citation in `source`.
3. **Strict Typing:** All date-time properties must conform to ISO-8601; numeric scoring thresholds must be bounded within $[1.0, 5.0]$.
