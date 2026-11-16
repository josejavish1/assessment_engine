#!/usr/bin/env python3
"""
Invoke gemini-4-argon to execute a Tier-1 Adversarial Red Team Audit on the proposed Phase 27 Epistemic Evidence Gating Blueprint.

Evaluates:
1. Is the proposed Zero-Prompt-Reliance architecture (AST Lexical Gating, Semantic Envelopes, Payload Isolation) the definitive Tier-1 solution?
2. Does it guarantee the elimination of all tactical workarounds (whack-a-mole) for hallucinations and tower contamination?
3. Does it scale to any type of company globally, in any language?
4. Are there any hidden theoretical flaws, scaling limits, or edge cases in the proposed design?

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

def run_phase27_adversarial_red_team_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: TIER-1 ADVERSARIAL RED TEAM AUDIT (PHASE 27 EVIDENCE GATING)")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = f"""
You are the Global Head of Adversarial Architecture & Actuarial Peer Review (ex-Principal Systems Architect at AWS/Anthropic/Google, Fellow of the Society of Actuaries).

YOUR ASSIGNMENT:
Execute an uncompromising, unsparing, and adversarial Red Team Audit of our proposed Phase 27 Master Blueprint (`ARGON_PHASE27_EVIDENCE_GATING_BLUEPRINT.md`).

Our proposed Phase 27 attempts to solve severe "whack-a-mole" epistemic hallucinations (KPI-to-Claim misalignment, specific protocol/hardware hallucination like BGP/CCTV, Capability vs Implementation conflation, and Tower context contamination) using a strict "Zero-Prompt-Reliance" architecture.

The core components of Phase 27 are:
1. KpiEpistemicEnvelope (Semantic Bounding): Forbidding physical assertions if the KPI lacks transcript evidence (forcing "Capability-Only Mode").
2. Transcript Lexicon Indexer (TLI) & AST Technical Gate: Extracting all High-Specificity Technical Tokens (HSTTs) from the generated AST and triggering a compiler panic/redaction if the token lacks a lexical witness in the source transcripts.
3. Tower Context Filtration: Masking and projecting entities so T8 (Governance) receives abstract assets (e.g., "[Enterprise Storage Asset]") instead of literal hardware names (e.g., "NetApp"), stopping cross-contamination.
4. FAIR Provenance Schema: Enforcing `tef_source`, `vuln_source`, and `sle_source` fields in Pydantic.

THE USER'S NON-NEGOTIABLE OBJECTIVES:
1. WORLD-CLASS TIER-1 CERTIFICATION: Is this Zero-Prompt-Reliance AST/Compiler-based architecture truly the state-of-the-art approach to permanently solve generative hallucinations globally? Does it scale to any company size and vertical without tactical patches?
2. ZERO HARDCODING: Does this architecture eliminate reliance on hardcoded Spanish logic or manually curated stop-lists?
3. CHAPTER 4 ACTUARIAL PERFECTION: Will this definitively prevent unaccredited commercial entities and cross-contaminated hardware logic from entering the deliverables?
4. ARCHITECTURAL BLIND SPOTS: Brutally tear down the proposed Phase 27. What failure modes, parsing edge cases, or theoretical weaknesses exist in the Lexical Witness Gate or Context Filtration?
5. CONCRETE RED TEAM ENHANCEMENTS: Exactly what modifications, simplifications, or structural invariants must be added to elevate this plan from "promising" to "flawless and bulletproof"?

YOUR DELIVERABLE:
Write a rigorous, exhaustive, publication-grade ADVERSARIAL RED TEAM VERDICT in Markdown format to be saved at `docs/architecture/ARGON_PHASE27_RED_TEAM_AUDIT.md`.

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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE27_RED_TEAM_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Red Team Verdict successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    run_phase27_adversarial_red_team_audit()
