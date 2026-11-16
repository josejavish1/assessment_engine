#!/usr/bin/env python3
"""
Invoke gemini-4-argon to execute a Tier-1 Adversarial Red Team Audit on the proposed Phase 24 Prompt-Level Constrained Decoding strategy.

Evaluates:
1. Is shifting the evidence guard from post-generation regex to pre-generation prompt contracts (Structured JSON decoding, explicit ALLOWED_ENTITIES lists) the definitive Tier-1 solution?
2. Does it guarantee the elimination of all tactical workarounds and hardcoding?
3. Does it scale to any type of company globally, in any language?
4. Are there any hidden theoretical flaws, scaling limits, or edge cases?

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

def run_phase24_adversarial_red_team_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: TIER-1 ADVERSARIAL RED TEAM AUDIT (PHASE 24 PROMPT-LEVEL GATING)")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = f"""
You are the Global Head of Adversarial Architecture & Actuarial Peer Review (ex-Principal Systems Architect at AWS/Anthropic/Google, Fellow of the Society of Actuaries, and Senior Partner for Quantitative Enterprise Due Diligence).

YOUR ASSIGNMENT:
Execute an uncompromising, unsparing, and adversarial Red Team Audit of our proposed Phase 24 strategy to finally eradicate "Implementation Hallucinations" (where the LLM invents products like BitLocker or VESDA just to fill space when a capability scores a 5.0 but lacks interview evidence).

Our previous approach (Phase 23) relied on a Post-Generation Lexical Sanitizer (a regex-based whack-a-mole replacing words after they were generated). We have identified this as a fragile antipattern (The Open-World Fallacy). 

OUR NEW PROPOSED SOLUTION (Phase 24):
Shift epistemic control entirely to the prompt boundary using Structural Prompting and Constrained Decoding.
1. The master prompts in `engine_config/prompts/` will prohibit free-form prose detailing unverified technical architecture.
2. We will enforce a strict JSON Schema on the LLM output:
   - `capability_description`: The agnostic operational mechanics of the process (no brands allowed).
   - `verified_vendor_products`: A strictly verified array of products that the LLM is ONLY allowed to populate if accompanied by an explicit `chunk_id` from the interview transcript. If no audio transcript exists for that capability, this array MUST be `[]`.
3. The prompt will inject `ALLOWED_ENTITIES: [...]` derived from the upstream `VerifiedEntityRegistry` during context assembly. If the entity isn't in the list, the LLM is syntactically forbidden from asserting it.

THE USER'S NON-NEGOTIABLE OBJECTIVES:
1. WORLD-CLASS TIER-1 CERTIFICATION: Is this proposed architecture truly the state-of-the-art approach for enterprise assessment generation globally? Can it scale to any type of company in the world (from $50M mid-market to $100B+ multinationals, any vertical, any language) without tactical patches?
2. ZERO HARDCODING & TOTAL SCALE AGNOSTICISM: Does this architecture eliminate all hardcoding and heuristics? 
3. CHAPTER 4 ACTUARIAL PERFECTION: Will this definitively prevent unaccredited commercial entities from leaking into risk scenarios and compromising the actuarial credibility of the report?
4. ARCHITECTURAL BLIND SPOTS & VULNERABILITIES: Brutally tear down the naive proposal. What failure modes, edge cases, or theoretical weaknesses exist in this Phase 24 design?
5. CONCRETE RED TEAM ENHANCEMENTS: Exactly what modifications or structural safeguards must be added to elevate this plan from "promising" to "flawless and unassailable"?

YOUR DELIVERABLE:
Write a rigorous, exhaustive, publication-grade ADVERSARIAL RED TEAM VERDICT in Markdown format to be saved at `docs/architecture/ARGON_TIER1_RED_TEAM_PHASE24_VERDICT.md`.

Structure your verdict into:
1. EXECUTIVE VERDICT & ADVERSARIAL RATING (out of 10.0).
2. STRESS-TEST EVALUATION ACROSS MANDATORY DIMENSIONS (Universality, Epistemic Integrity, Zero Hardcoding).
3. IDENTIFIED ARCHITECTURAL BLIND SPOTS & FAILURE MODES (Brutal teardown).
4. MANDATORY RED TEAM ENHANCEMENTS (The actual Tier-1 corrections to the blueprint to make it flawless).
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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_TIER1_RED_TEAM_PHASE24_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Red Team Verdict successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    run_phase24_adversarial_red_team_audit()
