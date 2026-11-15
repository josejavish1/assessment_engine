#!/usr/bin/env python3
"""
Invoke gemini-4-argon to execute a Tier-1 Adversarial Red Team Audit on the Universal Refactor Plan.

Evaluates:
1. Universal Enterprise Agnosticism ($50M to $100B+, any global vertical).
2. Elimination of all tactical workarounds and hardcoding.
3. Chapter 4 Actuarial Perfection across all 10 domain towers (Open FAIR, ALE, TCO, Heatmap, Hare-Niemeyer).
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
    print("  INVOKING GEMINI-4-ARGON: TIER-1 ADVERSARIAL RED TEAM AUDIT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    # Read the proposed master plan and root cause analysis for context
    rca_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_REFACTOR_ROOT_CAUSE_ANALYSIS.md"
    plan_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE13_SCORING_EVIDENCE_INTEGRATION.md"
    overhaul_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_GENERATOR_OVERHAUL_MASTER_PLAN.md"

    rca_text = rca_file.read_text(encoding="utf-8") if rca_file.exists() else ""
    plan_text = plan_file.read_text(encoding="utf-8") if plan_file.exists() else ""
    overhaul_text = overhaul_file.read_text(encoding="utf-8") if overhaul_file.exists() else ""

    prompt = f"""
You are the Global Head of Adversarial Architecture & Actuarial Peer Review (ex-Principal Systems Architect at AWS/Anthropic/Google, Fellow of the Society of Actuaries, and Senior Partner for Quantitative Enterprise Due Diligence).

YOUR ASSIGNMENT:
Execute an uncompromising, unsparing, and adversarial Red Team Audit of the proposed Universal Refactor Architecture documented in:
1. `ARGON_UNIVERSAL_REFACTOR_ROOT_CAUSE_ANALYSIS.md`
2. `ARGON_PHASE13_SCORING_EVIDENCE_INTEGRATION.md`
3. `ARGON_UNIVERSAL_GENERATOR_OVERHAUL_MASTER_PLAN.md`

CONTEXT DOCUMENTS SUMMARY:
--- RCA EXCERPT ---
{rca_text[:4000]}
--- PHASE 13 PLAN EXCERPT ---
{plan_text[:6000]}
--- OVERHAUL PLAN EXCERPT ---
{overhaul_text[:4000]}

THE USER'S NON-NEGOTIABLE OBJECTIVES:
1. WORLD-CLASS TIER-1 CERTIFICATION: Is this proposed architecture truly the state-of-the-art approach for enterprise assessment generation globally?
2. ZERO HARDCODING & TOTAL SCALE AGNOSTICISM: Does this architecture scale seamlessly from a $50M mid-market firm to a $100B+ multinational conglomerate across ANY vertical (heavy manufacturing, banking, healthcare, retail, critical infrastructure)?
3. CHAPTER 4 ACTUARIAL PERFECTION ACROSS ALL 10 TOWERS: How do we guarantee that Chapter 4 (Open FAIR quantification, 3-lever TCO, LEF = TEF * Vuln, subadditive Hare-Niemeyer discrete integer preservation, Heatmap coordinates, and risk cards) executes with 100% mathematical, actuarial, and linguistic perfection across all 10 domain towers without template staleness or generic numbers?
4. ARCHITECTURAL BLIND SPOTS & VULNERABILITIES: What failure modes, edge cases, or theoretical weaknesses exist in the proposed design? Where could it fail under high concurrency or ambiguous client data?
5. CONCRETE RED TEAM ENHANCEMENTS: Exactly what modifications or safeguards must be added to elevate the plan from "good" to "unassailable"?

YOUR DELIVERABLE:
Write a rigorous, exhaustive, publication-grade ADVERSARIAL RED TEAM VERDICT in Markdown format to be saved at `docs/architecture/ARGON_TIER1_RED_TEAM_REFACTOR_VERDICT.md`.

Structure your verdict into:
1. EXECUTIVE VERDICT & ADVERSARIAL RATING (out of 10.0).
2. STRESS-TEST EVALUATION ACROSS THE 4 MANDATORY DIMENSIONS:
   - Dimension A: Multi-Tenant Scale Invariance ($50M to $100B+).
   - Dimension B: Chapter 4 Actuarial Monism & Mathematical Perfection (All 10 Towers).
   - Dimension C: Forensic Evidence Ledger & Fail-Closed Technical Verification.
   - Dimension D: Epistemic Contradiction Engine & Zero Forced Overwrites.
3. IDENTIFIED ARCHITECTURAL BLIND SPOTS & FAILURE MODES (Minimum 5 critical edge cases).
4. MANDATORY RED TEAM ENHANCEMENTS (Concrete, actionable architectural addenda).
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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_TIER1_RED_TEAM_REFACTOR_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Red Team Verdict successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    run_adversarial_red_team_audit()
