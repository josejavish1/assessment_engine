---
status: Verified
owner: docs-governance
source_of_truth:
- docs/reference/data-dictionary.md
- docs/reference/reference-reports.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: editorial
notes: Canonical index and routing map for reference catalogs, data dictionaries, and deliverable baselines.
---
# Reference Catalogs & Glossaries Index

Canonical index documenting the data dictionaries, regulatory taxonomies, and reference deliverable baselines across `assessment-engine`.

---

## 1. Reference Specifications Routing Matrix

| Reference Document | Category | Epistemic Scope | Primary Implementation Source |
|---|---|---|---|
| [`data-dictionary.md`](data-dictionary.md) | Ontological Glossary | Actuarial risk metrics (TEF, VULN, ALE, SLE, VaR, CVaR), CMMI maturity scales (1-5), and tower identifiers | `engine_config/governance_scales.json`, `schemas/blueprint.py` |
| [`reference-reports.md`](reference-reports.md) | Benchmark Deliverables | Historical enterprise deliverable structures (FNMT-CERES structure) and volume hierarchy | `templates/docx/`, `working/reference_reports/` |

---

## 2. Invariant Governance Rule

Reference documents provide immutable naming conventions, units of measure, and structural standards. AI agents must strictly adhere to the acronyms, score intervals, and terminology defined in these catalogs without inventing ad-hoc variations.
