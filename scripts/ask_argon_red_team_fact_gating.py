#!/usr/bin/env python3
"""
Invoke gemini-4-argon to execute a Tier-1 Adversarial Red Team Audit on the proposed SharedFactRegistry and ClaimGatingOracle.

Evaluates:
1. Universal Enterprise Agnosticism ($50M to $100B+, any global vertical).
2. Elimination of all tactical workarounds and hardcoding.
3. Guaranteeing epistemic integrity and zero hallucination across all 10 domain towers.
4. Identification of architectural blind spots, theoretical flaws, or potential failure modes.

100% Technical English in prompt and generated verdict.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def run_adversarial_red_team_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: TIER-1 ADVERSARIAL RED TEAM AUDIT (FACT & CLAIM GATING)")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are the Global Head of Adversarial Architecture & Actuarial Peer Review (ex-Principal Systems Architect at AWS/Anthropic/Google, Fellow of the Society of Actuaries, and Senior Partner for Quantitative Enterprise Due Diligence).

YOUR ASSIGNMENT:
Execute an uncompromising, unsparing, and adversarial Red Team Audit of our proposed structural solution to eliminate tactical JSON patching. The current proposal is to implement a `SharedFactRegistry` (to restrict canonical facts like "613 days uptime" strictly to their owner domains) and a `ClaimGatingOracle` (to validate LLM output and reject hallucinated technologies like "VESDA" or "BitLocker" if absent from the evidence corpus).

THE USER'S NON-NEGOTIABLE OBJECTIVES:
1. WORLD-CLASS TIER-1 CERTIFICATION: Is this proposed architecture (SharedFactRegistry + ClaimGatingOracle) truly the state-of-the-art approach for enterprise assessment generation globally, or is it just another brittle patch?
2. ZERO HARDCODING & TOTAL SCALE AGNOSTICISM: Does this architecture scale seamlessly to ANY client without hardcoding facts like "613 days"? How do we build a truly dynamic fact registry?
3. CHAPTER 4 ACTUARIAL PERFECTION: How does this ensure that the financial and risk models in Chapter 4 are fed 100% verified facts without semantic drift?
4. ARCHITECTURAL BLIND SPOTS & VULNERABILITIES: What failure modes, edge cases, or theoretical weaknesses exist in the proposed design?
5. CONCRETE RED TEAM ENHANCEMENTS: Exactly what modifications or safeguards must be added to elevate the plan from "good" to "unassailable" and purely structural?

YOUR DELIVERABLE:
Write a rigorous, exhaustive, publication-grade ADVERSARIAL RED TEAM VERDICT in Markdown format to be saved at `docs/architecture/ARGON_TIER1_RED_TEAM_FACT_GATING_VERDICT.md`.

Structure your verdict into:
1. EXECUTIVE VERDICT & ADVERSARIAL RATING (out of 10.0).
2. STRESS-TEST EVALUATION ACROSS THE MANDATORY DIMENSIONS (Universality, Epistemic Integrity, Zero Hardcoding).
3. IDENTIFIED ARCHITECTURAL BLIND SPOTS & FAILURE MODES (Brutal teardown of the naive proposal).
4. MANDATORY RED TEAM ENHANCEMENTS (The actual Tier-1 blueprint to build a dynamic, ontology-driven fact and claim engine).
5. FINAL SIGN-OFF PROTOCOL & CERTIFICATION CRITERIA.

CORE INVARIANTS:
- 100% Technical English.
- Zero sycophancy: deliver brutal, unvarnished, high-signal engineering truth.
"""

    print("Sending prompt to Gemini-4-Argon Red Team...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_TIER1_RED_TEAM_FACT_GATING_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Red Team Verdict successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    run_adversarial_red_team_audit()
