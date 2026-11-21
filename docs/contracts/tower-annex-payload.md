---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/annex_synthesis.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical technical specification of the AnnexPayload Pydantic data contract.
---
# Tower Annex Payload Contract

Canonical data contract specification defining the structure, fields, and Pydantic constraints of `approved_annex_<tower>.template_payload.json`.

This contract is governed by `src/assessment_engine/domain/schemas/annex_synthesis.py` and synthesized downstream from the Tower Blueprint SSOT by `run_executive_annex_synthesizer.py`.

---

## 1. Root Model: `AnnexPayload`

The top-level container encapsulating the complete executive annex presentation state:

| Field Name | Type | Description |
|---|---|---|
| `generation_metadata` | `Optional[Dict[str, Any]]` | Execution lineage, timestamp, generator version, and run ID. |
| `document_meta` | `Dict[str, Any]` | Client slug, tower identifier, target locale, and company metadata. |
| `executive_summary` | `ExecutiveSummaryAnnex` | High-level synthesis, maturity ratings, and executive headline. |
| `domain_introduction` | `DomainIntroduction` | Technological domain boundaries, audited scope, and capabilities. |
| `pillar_score_profile` | `MaturityScoreProfile` | Quantitative scoring breakdown across technology pillars and radar visual. |
| `sections` | `AnnexSections` | Structured sections covering current state, target state, gaps, and roadmap. |

---

## 2. Core Section Sub-Models

### `ExecutiveSummaryAnnex`

Executive elevator pitch and portfolio-level maturity indicators:

| Field Name | Type | Description |
|---|---|---|
| `global_score` | `str` | Overall quantitative maturity score formatted as string (e.g., `"2.8"`). |
| `global_band` | `str` | Qualitative maturity band (e.g., `"Managed"`, `"Defined"`). |
| `target_maturity` | `str` | Target CMMI maturity score (e.g., `"3.5"`). |
| `headline` | `str` | High-impact C-level headline summarizing assessment outcome. |
| `summary_body` | `str` | Synthesized executive elevator pitch. |
| `financial_coi` | `Optional[str]` | Cost of Inaction (COI) exposure summary. |
| `message_strength` | `str` | Key operational strength identified during evaluation. |
| `message_gap` | `str` | Primary structural deficiency requiring transformation. |
| `message_bottleneck`| `str` | Identified systemic bottleneck across operations or architecture. |
| `key_business_impacts` | `List[str]` | Prioritized strategic and business ramifications. |

### `DomainIntroduction`

Defines technology scope and operational footprint:

| Field Name | Type | Description |
|---|---|---|
| `introduction_paragraph` | `str` | Overview of the evaluated technology domain. |
| `technological_domain` | `str` | Domain title (e.g., `"Hybrid Cloud & Compute Infrastructures"`). |
| `domain_objective` | `str` | Core business objective supporting the technical domain. |
| `evaluated_capabilities` | `List[str]` | Functional capabilities analyzed during assessment. |
| `included_components` | `List[str]` | In-scope platforms, infrastructure clusters, and services. |

### `MaturityScoreProfile`

Structured pillar scores and visualization metadata:

| Field Name | Type | Description |
|---|---|---|
| `profile_intro` | `str` | Contextual note explaining scoring methodology. |
| `scoring_method_note` | `str` | Formal CMMI rating framework reference. |
| `radar_chart` | `str` | Relative filesystem path to generated vector radar graphic (`.png`). |
| `pillars` | `List[Dict[str, Any]]` | Pillar-level scores, qualitative bands, and findings count. |

### `FinancialCOIProfile`

Quantitative Cost of Inaction actuarial metrics:

| Field Name | Type | Description |
|---|---|---|
| `annual_loss_exposure` | `float` | Mean Annualized Loss Expectancy (ALE) from FAIR model. |
| `coi_3y_ordinary` | `float` | Expected 3-year cumulative operational cost of inaction. |
| `coi_3y_extreme` | `float` | 95th percentile Value-at-Risk (VaR) extreme loss exposure. |

### `AnnexSections`

Container aggregating the core narrative and roadmap sections:

| Field Name | Type | Description |
|---|---|---|
| `asis` | `AsIsAnnex` | Current state diagnostic, operational strengths, and liabilities. |
| `tobe` | `ToBeAnnex` | Target architecture vision and design principles. |
| `gap` | `GapAnnex` | Pillar-by-pillar comparative gap matrix. |
| `todo` | `TodoAnnex` | Prioritized strategic initiatives and execution waves. |
| `risks` | `RisksAnnex` | Consolidated technological, operational, and regulatory risks. |
| `conclusion` | `ConclusionAnnex` | Board-level conclusion and strategic recommendations. |

---

## 3. Detailed Component Models

### `AsIsAnnex`
| Field Name | Type | Description |
|---|---|---|
| `narrative` | `str` | Narrative assessment of current state operations. |
| `strengths` | `List[str]` | Validated organizational and architectural strengths. |
| `gaps` | `List[str]` | Primary technical deficiencies identified from evidence. |
| `operational_impacts` | `List[str]` | Business and technical liabilities of current baseline. |

### `ToBeAnnex`
| Field Name | Type | Description |
|---|---|---|
| `vision` | `str` | 3-year target transformation state description. |
| `design_principles` | `List[str]` | Non-negotiable architectural axioms governing target state. |

### `GapAnnex` & `GapRowAnnex`
| Field Name | Type | Description |
|---|---|---|
| `introduction` | `str` | Introductory narrative for gap analysis. |
| `target_capabilities` | `List[str]` | Target technical capabilities. |
| `gap_rows` | `List[GapRowAnnex]` | Matrix rows mapping current baseline to target state per pillar. |
| `closing_summary` | `str` | Executive summary of overall transformation distance. |

*`GapRowAnnex` Attributes:*
- `pillar`: Name of technology pillar.
- `as_is_summary`: Current operational baseline.
- `target_state`: Target operational objective.
- `key_gap`: Core missing capability.

### `TodoAnnex` & `InitiativeAnnex`
| Field Name | Type | Description |
|---|---|---|
| `introduction` | `str` | Introduction to remediation roadmap. |
| `priority_initiatives` | `List[InitiativeAnnex]` | Ordered transformation projects. |
| `closing_summary` | `str` | Executive roadmap summary. |

*`InitiativeAnnex` Attributes:*
- `sequence`: Sequential priority index.
- `initiative`: Initiative title.
- `objective`: Business and technical objective.
- `priority`: Priority level (`High`, `Medium`, `Low`).
- `expected_outcome`: Target deliverable or capability.
- `dependencies_display`: Formatted dependency prerequisites.

### `RisksAnnex` & `RiskItemAnnex`
| Field Name | Type | Description |
|---|---|---|
| `introduction` | `str` | Introduction to risk profile. |
| `risks` | `List[RiskItemAnnex]` | Consolidated risk entries. |
| `closing_summary` | `str` | Residual risk posture statement. |

*`RiskItemAnnex` Attributes:*
- `risk`: Risk title and scenario description.
- `impact`: Qualitative and financial business impact.
- `probability`: Likelihood rating (`High`, `Medium`, `Low`).
- `mitigation_summary`: Recommended tactical mitigation.

### `ConclusionAnnex`
| Field Name | Type | Description |
|---|---|---|
| `final_assessment` | `str` | Final strategic evaluation. |
| `executive_message` | `str` | Directive conclusion for C-level leadership. |
| `priority_focus_areas` | `List[str]` | Top focus domains for immediate investment. |
| `closing_statement` | `str` | Closing executive sign-off text. |
