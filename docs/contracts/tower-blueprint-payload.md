---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/blueprint.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical technical specification of the BlueprintPayload Pydantic data contract.
---
# Tower Blueprint Payload Contract

Canonical data contract specification defining the structure, fields, and Pydantic constraints of `blueprint_<tower>_payload.json`.

This artifact acts as the **authoritative Single Source of Truth (SSOT)** for an individual technology tower. All downstream artifacts (annex, global consolidated report, and Word compilation) derive strictly from this payload. Governed by `src/assessment_engine/domain/schemas/blueprint.py` and synthesized by `run_tower_blueprint_engine.py`.

---

## 1. Root Model: `BlueprintPayload`

The root container encapsulating the complete architectural, actuarial, and initiative baseline of a tower:

| Field Name | Type | Description |
|---|---|---|
| `document_meta` | `BlueprintDocumentMeta` | Metadata identifying the client, technology tower, currency, and horizons. |
| `executive_snapshot` | `ExecutiveSnapshot` | High-level synthesis, cost of inaction, and board-level decisions. |
| `cross_capabilities_analysis` | `CrossCapabilitiesAnalysis` | Transversal deficiency patterns and technical debt analysis. |
| `pillars_analysis` | `List[PillarBlueprintDraft]` | Detailed technical diagnostics, target states, and projects per pillar. |
| `roadmap` | `List[RoadmapWave]` | Phased delivery schedule allocating projects across horizons ($H_1, H_2, H_3$). |
| `external_dependencies` | `List[ExternalDependency]` | Cross-tower dependency mappings and blocking prerequisites. |
| `total_fair_ale` | `Optional[float]` | Aggregated Annualized Loss Expectancy (ALE) from FAIR Monte Carlo runs. |
| `total_fair_p90` | `Optional[float]` | 90th percentile Value-at-Risk loss magnitude. |
| `total_fair_cvar_90` | `Optional[float]` | Conditional Value-at-Risk (tail risk expectancy at 90%). |

---

## 2. Core Sub-Models

### `BlueprintDocumentMeta`

Operational metadata identifying the engagement context:

| Field Name | Type | Description |
|---|---|---|
| `client_name` | `str` | Legal corporate name of the audited client. |
| `tower_name` | `str` | Title of the evaluated technology domain. |
| `tower_code` | `str` | Domain code (e.g., `"T1"`, `"T2"`, `"T3"`, `"T5"`). |
| `financial_tier` | `str` | Corporate classification tier governing financial sizing bounds. |
| `transformation_horizon` | `str` | Timeframe for roadmap execution (e.g., `"3 years"`). |
| `currency` | `str` | Localized billing currency symbol (e.g., `"EUR"`, `"USD"`, `"JPY"`). |

### `PillarBlueprintDraft`

Detailed architectural diagnostic per technological pillar:

| Field Name | Type | Description |
|---|---|---|
| `pillar_id` | `str` | Canonical pillar code (e.g., `"P1"`, `"P2"`). |
| `pillar_name` | `str` | Name of the evaluated capability pillar. |
| `score` | `float` | Quantitative CMMI maturity score $\in [1.0, 5.0]$. |
| `target_score` | `float` | Target CMMI maturity threshold $\in [1.0, 5.0]$. |
| `asis_architecture_description` | `str` | Narrative baseline diagnostic of current infrastructure. |
| `health_check_asis` | `List[HealthCheckAsIs]` | Itemized operational findings and discovered vulnerabilities. |
| `target_architecture_tobe` | `TargetArchitectureToBe` | Target architectural vision, principles, and capabilities. |
| `projects_todo` | `List[ProjectToDo]` | Actionable transformation projects mitigating identified gaps. |

### `HealthCheckAsIs`

Granular baseline technical finding anchored to empirical evidence:

| Field Name | Type | Description |
|---|---|---|
| `target_state` | `str` | Target standard capability under evaluation. |
| `risk_observed` | `str` | Identified operational failure, vulnerability, or architectural bottleneck. |
| `impact` | `str` | Business, financial, or regulatory impact of the deficiency. |
| `fragment_id` | `Optional[str]` | Provenance citation referencing source `EvidenceFragment`. |
| `literal_evidence` | `Optional[str]` | Verbatim quote extracted from client documentation. |
| `fair_ale_score` | `Optional[float]` | Actuarial Annualized Loss Expectancy computed for this risk. |

### `TargetArchitectureToBe`

Defines the target transformation vision and guiding design axioms:

| Field Name | Type | Description |
|---|---|---|
| `vision` | `str` | High-level 3-year target architecture vision. |
| `vision_3_years` | `str` | Detailed target state specification for horizon 2. |
| `vision_5_years` | `str` | Long-range north star architecture vision. |
| `expected_benefits` | `List[str]` | Quantified operational and technical improvements. |
| `cost_of_inaction_risks` | `List[str]` | Systemic liabilities incurred if target state is abandoned. |

### `ProjectToDo`

Actionable engineering remediation project:

| Field Name | Type | Description |
|---|---|---|
| `initiative` | `str` | Formal project title. |
| `transformation_typology` | `str` | Classification category (e.g., `"Modernization"`, `"Governance"`, `"Security"`). |
| `objective` | `str` | Technical delivery objective. |
| `expected_outcome` | `str` | Business and operational outcome. |
| `deliverables` | `List[str]` | Itemized technical deliverables. |
| `sizing` | `str` | T-shirt sizing estimate (`"S"`, `"M"`, `"L"`, `"XL"`). |
| `duration` | `str` | Estimated implementation schedule (e.g., `"6 months"`). |
| `mitigates_risk_id` | `Optional[str]` | Pointer linking back to the mitigated `HealthCheckAsIs` finding. |

### `ExecutiveSnapshot`

High-level briefing synthesized for C-suite stakeholders:

| Field Name | Type | Description |
|---|---|---|
| `bottom_line` | `str` | Primary diagnostic takeaway. |
| `decisions` | `List[str]` | Non-negotiable executive approvals required to commence roadmap. |
| `cost_of_inaction` | `str` | Quantified narrative exposure of maintaining status quo. |
| `structural_risks` | `List[str]` | Macro technological liabilities. |
| `business_impact` | `str` | Enterprise operational impact of discovered deficiencies. |
| `operational_benefits` | `List[str]` | Measurable efficiency and velocity gains. |
| `transformation_complexity` | `str` | Execution complexity rating (`"High"`, `"Medium"`, `"Low"`). |

### `CrossCapabilitiesAnalysis`

Transversal pattern and technical debt diagnostics:

| Field Name | Type | Description |
|---|---|---|
| `common_deficiency_patterns` | `List[str]` | Systemic issues recurring across multiple pillars. |
| `transformation_paradigm` | `str` | Strategic modernization framework. |
| `critical_technical_debt` | `str` | Obsolete components requiring immediate architectural retirement. |

### `RoadmapWave` & `ExternalDependency`

Roadmap sequencing and inter-project constraints:

| Model Name | Field Name | Type | Description |
|---|---|---|---|
| `RoadmapWave` | `wave` | `str` | Execution wave identifier (`"H1"`, `"H2"`, `"H3"`). |
| | `projects` | `List[str]` | Initiative titles allocated to this wave. |
| `ExternalDependency` | `project` | `str` | Target initiative requiring prerequisite completion. |
| | `depends_on` | `str` | Prerequisite initiative or external milestone. |
| | `reason` | `str` | Technical or operational justification for the constraint. |

---

## 3. Architectural Invariants for AI Agents

1. **Monism Enforcement:** Downstream synthesizers and compilers must never alter metrics declared in `BlueprintPayload`.
2. **Reverse Traceability:** Every `ProjectToDo` must reference a valid finding (`mitigates_risk_id`), and every `HealthCheckAsIs` must cite an empirical `fragment_id`.
3. **Pydantic Validation:** All blueprint payloads serialized to disk must validate without warnings against `BlueprintPayload.model_validate()`.
