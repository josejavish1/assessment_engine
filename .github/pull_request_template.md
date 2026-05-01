## Summary

- describe the main change
- explain the affected area

## Change spec

- Problem:
- In scope:
- Out of scope:
- Source of truth:
- Invariants to preserve:
- Validation plan:

## Documentation impact

- [ ] I reviewed whether this change affects architecture, contracts, operations, CI, prompts, or onboarding
- [ ] I updated the canonical documentation when needed
- [ ] I updated `docs/documentation-map.yaml` when a document changed state, scope, or destination
- [ ] If no documentation change was needed, I explained why below

## Documentation notes

<!-- Explain why docs were updated or why they were intentionally not needed. -->

## Validation

- [ ] I ran the relevant local validation for my change
- [ ] I checked whether this change depends on artifacts in `working/`

## Governance checks

- [ ] I did not introduce new source-of-truth content only in agent-specific files
- [ ] This change had a minimal explicit spec before implementation (problem, scope, source of truth, invariants, validation)
- [ ] The change scope is intentionally bounded and does not mix unrelated redesigns unnecessarily
- [ ] I reviewed whether the change duplicates existing logic or creates another source of truth
- [ ] I encoded important implementation rules in code, tests, schemas, or workflows instead of leaving them only in prompts or tribal knowledge
- [ ] If I changed score, band, target, color, or client-facing semantics, I updated the related coherence tests
- [ ] I kept payload/schema changes aligned with their consuming renderers or updated the related contract docs
- [ ] If I changed engineering quality rules or tooling, I updated `docs/operations/engineering-quality-gates.md`
- [ ] If a source-linked documentation rule applied, I updated one of the required canonical docs
