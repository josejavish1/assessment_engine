"""Consult gemini-4-argon: Forensic analysis of the comprehensive Tier-1 actuarial engineering specification."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

SPEC_TEXT = """
You are working in the repository josejavish1/assessment_engine.

Expected baseline:
- Repository path: /workspace/assessment_engine
- Expected starting commit: 37f2bb1098f6443f3bab4b9dd75a918e87c145ce
- Do not overwrite unrelated local changes if HEAD or the working tree differs.
- Do not commit, push, open a PR, or modify generated customer deliverables.

Your goal is to make the existing actuarial implementation traceable, reproducible, and honest about its evidential limits. Do not redesign its mathematics and do not add mathematical sophistication in this task.

MANDATORY OPERATING RULES:
1. Read AGENTS.md, README.md, docs/README.md, docs/ai/documentation-governance.md, docs/operations/agentic-development-workflow.md, docs/operations/engineering-quality-gates.md.
2. Treat current code, schemas, and tests as the source of truth.
3. 100% Technical English.
4. Never invent sources, citations, sample sizes, customer confirmations, historical observations, confidence levels, regulatory compliance, or annual-account provenance. Missing evidence must be null, UNCONFIRMED, UNASSESSED, or NEEDS_REVIEW.
5. Do not change Poisson event-count, Rockafellar-Uryasev CVaR, copula math, loss distributions, allocation formulas, or presentation-layer calculations.
6. Do not silence failures, loosen assertions, add blanket exception handlers, add type: ignore, or modify tests merely to accept broken behavior.
7. Do not claim that the model is perfect, universally calibrated, externally validated, certified, or SR 11-7 compliant.
8. Complete the phases sequentially:

PHASE 0: Establish baseline (fails on dynamic taxonomy fallback).
PHASE 1: Fix dynamic taxonomy regression in archetype_registry.py (TowerActuarialMapping fields, tower_id regex pattern, dynamic aliases D_*, generic fallback for EDGE_01, reject T99 with KeyError).
PHASE 2: Implement complete parameter lineage contract (estimated_value, effective_value, unit, source_type, source_reference, estimation_method, confidence, validation_status, client_override, inputs/outputs sections).
PHASE 3: Build real portfolio reproduction manifest after evaluate_portfolio(), with seed hash, replay function, asserting deterministic seed equality and metric parity <= 0.01 tolerance, removing false claims from dossier.
PHASE 4: Correct calibration claims in fit_actuarial_priors.py and CALIBRATION_FITTING_LINEAGE.json (call it quantile matching, not empirical goodness of fit; mark unverified sources as NEEDS_REVIEW).
"""

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, Fellow of the Open FAIR Institute, and Master of Model Risk Governance (SR 11-7 / TRIM / Solvency II).

We have received an extraordinary, high-rigor engineering prompt from a Tier-1 Principal Model Risk Reviewer:

```markdown
{SPEC_TEXT}
```

OUR EMPIRICAL VERIFICATION OF THE BASELINE:
We ran:
`PYTHONPATH=src .venv/bin/pytest -q tests/unit/domain/taxonomy/test_archetype_registry.py tests/unit/test_tower_payload_hydrator_semantic_quarantine.py`
Result:
1. `tests/unit/domain/taxonomy/test_archetype_registry.py::test_unknown_tower_raises_key_error`: FAILED with `AttributeError: 'TowerActuarialMapping' object has no attribute 'vector_alpha_weight'`
2. `tests/unit/test_tower_payload_hydrator_semantic_quarantine.py::test_hydrator_sanitizes_findings_and_persists_clean_json`: FAILED with `AttributeError: 'TowerActuarialMapping' object has no attribute 'default_cmmi_benchmark'`
Because in commit `37f2bb1`, `TowerActuarialMapping` was constructed with non-existent fields and a rigid regex `^T\d{1,2}$` that rejects dynamic towers!

YOUR MANDATE:
Deliver an authoritative, unflinching architectural and actuarial analysis of this specification:
1. Architectural Assessment: How does this specification transform the codebase from a "theatrically compliant" model to an authentic, honest, Big-4 / Fed SR 11-7 defensible platform?
2. Detailed Execution Blueprint for each of the 4 Phases:
   - Phase 1: Provide the exact, surgical code required for `archetype_registry.py` (pattern regex, dynamic alias mapping, T99 KeyError enforcement).
   - Phase 2: Provide the exact Pydantic schema for the typed Parameter Lineage contract (`ParameterProvenanceRecord` and `ActuarialInputVector`), and how to populate it in `tower_payload_hydrator.py`.
   - Phase 3: Provide the exact architecture for `PortfolioReproductionManifest` and the deterministic `replay_portfolio_simulation` function.
   - Phase 4: Provide the exact corrections for `fit_actuarial_priors.py` (quantile-matching terminology, zero-sycophancy, NEEDS_REVIEW flags).
3. The Strategic Imperative: Explain why implementing this prompt without shortcuts is the ultimate artifact of power for Tier-1 scrutiny.

Respond in 100% Technical English with mathematical precision, concrete code structures, and absolute zero sycophancy.
"""


def main() -> None:
    print(f"Submitting Specification Analysis to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_SPECIFICATION_ANALYSIS_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nAnalysis written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:2000] + ("\n... [TRUNCATED]" if len(ruling) > 2000 else ""))


if __name__ == "__main__":
    main()
