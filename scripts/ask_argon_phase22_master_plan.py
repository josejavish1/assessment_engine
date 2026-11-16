#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 22 Master Implementation Blueprint.

Addresses the final 3 architectural antipatterns identified by the Tier-1 Red Team:
1. Implementation Hallucination (Confusing capability score with specific product usage).
2. FAIR Actuarial Bipolarity (Static 0.80/0.95 vulnerability vs true dynamic derivation).
3. False Certainty in Contradictions (Arbitrary 1.00 down-scoring for ambiguous evidence).

Adheres strictly to:
1. 100% Technical English (Language Decoupling Law).
2. Universal Enterprise Agnosticism (Zero hardcoding, scales globally).
3. Pure Clean Architecture.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def request_argon_phase22_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: PHASE 22 MASTER IMPLEMENTATION BLUEPRINT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Global Chief Systems Architect, Principal Compiler Engineer, and Fellow of the Society of Actuaries.

MANDATE & OBJECTIVE:
We have successfully closed 7 major architectural gates, achieving a fully dynamic Epistemic Context Router and Missing Data Circuit Breaker. However, the external adversarial audit still flags 3 critical architectural antipatterns preventing a Tier-1 (8+/10) certification.
Your goal is to architect a comprehensive, multi-phase Master Implementation Blueprint to eradicate these final 3 antipatterns from the codebase completely.

THE 3 ANTIPATTERNS TO RESOLVE:

1. THE "IMPLEMENTATION HALLUCINATION" SYLLOGISM:
   - Defect: When a client marks a "4" or "5" on a questionnaire but mentions no specific brands in the interview, the LLM hallucinates typical industry products to fill the narrative (e.g., inferring "BitLocker" or "Entra ID" from a score of 5). 
   - Goal: Enforce strict Evidence-Based Specificity. The engine must describe the *agnostic operational profile* of that maturity band. Specific vendor/product names can ONLY be generated if explicitly linked to a source transcript `evidence_id`.

2. THE "ACTUARIAL BIPOLARITY" IN FAIR VULNERABILITY:
   - Defect: The vulnerability derivation in `chapter4_synthesizer.py` relies on a hardcoded, static binary split: `vuln_ratio = 0.80 if is_tier1 else 0.95`. This destroys the actuarial credibility of the Monte Carlo simulation, as every risk across 10 towers gets exactly 80% or 95%.
   - Goal: Implement true dynamic vulnerability derivation based on the actual maturity scores of the specific KPIs guarding against that risk (e.g., `Vuln = 1.0 - (Control_Score / 5.0) * Effectiveness_Factor`).

3. "FALSE CERTAINTY" IN CONTRADICTION SCORING:
   - Defect: When qualitative evidence contradicts a high self-assessed score (e.g., Kubernetes), the `ContradictionEngine` correctly flags the discrepancy but then arbitrarily forces the calibrated score to exactly `1.00 / 5.00`.
   - Goal: Introduce a `PROVISIONAL` or `UNRESOLVED` state. The score should retain the self-assessed value (e.g., `4.25*`) but mathematically flag it as provisional, pending field validation, without projecting false mathematical certainty.

NON-NEGOTIABLE CORE INVARIANTS:
1. 100% TECHNICAL ENGLISH: The entire plan, logic, and generated code must be in strict Technical English. Zero Spanish words.
2. ZERO HARDCODING: Solutions must be universally applicable to any enterprise globally. No client-specific strings.

YOUR DELIVERABLE:
Write an exhaustive, high-signal, publication-grade MASTER IMPLEMENTATION BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE22_MASTER_IMPLEMENTATION_BLUEPRINT.md`.

Structure your blueprint into:
1. EXECUTIVE SUMMARY & PARADIGM SHIFT.
2. DETAILED PHASED IMPLEMENTATION STRATEGY (How to tackle each of the 3 antipatterns in pure code, step-by-step).
3. ARCHITECTURAL CONTRACTS & SCHEMAS (Define the Pydantic models or algorithm changes needed).
4. QUALITY GATES & VERIFICATION ORACLES (How we will empirically prove these fixes).
"""

    print("Sending prompt to Gemini-4-Argon for Phase 22 Master Blueprint...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE22_MASTER_IMPLEMENTATION_BLUEPRINT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Blueprint successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    request_argon_phase22_master_plan()
