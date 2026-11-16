#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 25 Master Implementation Blueprint for Actuarial Purity.

Addresses the 'Magic Numbers & Parametric Numerology' antipattern:
1. Eradication of hardcoded coefficients (0.60, 0.45) cross-contaminating economic levers.
2. Independent, orthogonal derivation of Toil, Outage, and Contractual Drag.
3. Declarative, ontology-driven parametrization.

100% Technical English in prompt and generated blueprint.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def request_argon_phase25_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: PHASE 25 ACTUARIAL PURITY MASTER BLUEPRINT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Global Chief Systems Architect, Principal Compiler Engineer, and Fellow of the Society of Actuaries.

MANDATE & OBJECTIVE:
We have successfully eliminated epistemic hallucinations and FAIR bipolarity from our assessment engine. However, our internal actuarial calculations for the "Cost of Inaction" (COI) in `chapter4_synthesizer.py` still contain a critical structural antipattern: "Magic Numbers & Parametric Numerology."

Specifically, the calculation for Lever 3 (Contractual & Licensing Escalation) is artificially intertwined with Lever 1 (Toil) and Lever 2 (Outage) using hardcoded, arbitrary coefficients:
`baseline_economic_anchor = (outage_min * 0.60) + (toil_min * 0.45)`

This violates the mathematical independence of the three economic vectors and destroys the credibility of the model for a Tier-1 CTO or CFO. A rise in VMware licensing costs (Lever 3) has zero physical or economic relationship to how many hours the network was down (Lever 2).

Your goal is to architect a comprehensive, multi-phase Master Implementation Blueprint to eradicate this numerological antipattern and establish a mathematically pure, universally scalable economic model.

THE REQUIRED ARCHITECTURAL SHIFT:
1. PURE ORTHOGONAL VECTORS: The three economic levers must be strictly independent:
   - Lever 1 (Engineering Toil): Derived purely from FTE friction hours * Blended Labor Rate.
   - Lever 2 (Probabilistic Outage ALE): Derived purely from Open FAIR (TEF * Vulnerability * SLE).
   - Lever 3 (Contractual Drag): Must be derived from a Baseline IT Spend metric (calculated via industry revenue ratios from declarative config) * Annual Escalation Rate (from rate_card.json). It must NOT depend on Toil or Outages.
2. COPULA-DRIVEN PORTFOLIO SUBADDITIVITY: Replace the linear heuristic `1.0 - 0.05 * (N - 1)` with a rigorous, configuration-driven subadditivity copula factor for portfolio ALE aggregation.
3. ZERO HARDCODING: All mathematical constants (industry baseline ratios, labor rates, escalation percentages) MUST reside in declarative JSON configuration files (`engine_config/`), never in Python code.

NON-NEGOTIABLE CORE INVARIANTS:
1. 100% TECHNICAL ENGLISH: The entire plan, logic, and generated code must be in strict Technical English. Zero Spanish words.
2. TOTAL SCALE AGNOSTICISM: The math must hold for a $50M regional manufacturer or a $100B+ global bank.

YOUR DELIVERABLE:
Write an exhaustive, high-signal, publication-grade MASTER IMPLEMENTATION BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE25_ACTUARIAL_PURITY_BLUEPRINT.md`.

Structure your blueprint into:
1. EXECUTIVE SUMMARY & ACTUARIAL PARADIGM SHIFT.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 25.1: Declarative Actuarial Parameters (Schemas and `engine_config` mappings).
   - Phase 25.2: Orthogonal Lever Mechanics (Refactoring `chapter4_synthesizer.py`).
   - Phase 25.3: Subadditive Portfolio Aggregation (Replacing linear heuristics).
3. ARCHITECTURAL CONTRACTS (Define the updated Pydantic models or JSON configurations).
4. QUALITY GATES & VERIFICATION ORACLES (Deterministic pytest suites).
"""

    print("Sending prompt to Gemini-4-Argon for Phase 25 Master Blueprint...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE25_ACTUARIAL_PURITY_BLUEPRINT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Blueprint successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    request_argon_phase25_master_plan()
