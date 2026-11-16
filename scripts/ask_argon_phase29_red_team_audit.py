#!/usr/bin/env python3
"""
Invoke gemini-4-argon to execute a Tier-1 Adversarial Red Team Audit on the proposed Phase 29 Strategy for Evidence Discipline & Cleansing.

Evaluates:
1. Is modifying locales.json to soften NIS2 language structurally correct?
2. Is manually substituting terms like vCPU and "3 y 4" in the payloads a scalable solution, or a tactical patch?
3. Is adding manual tests for "CCTV" and "bóveda PAM" to the regression suite the right way to enforce Evidence Gating, or does it violate the Zero-Hardcoding rule?
4. What is the true Tier-1 architectural solution to these remaining defects?

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

def run_phase29_adversarial_red_team_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: TIER-1 ADVERSARIAL RED TEAM AUDIT (PHASE 29 STRATEGY)")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = f"""
You are the Global Head of Adversarial Architecture & Actuarial Peer Review (ex-Principal Systems Architect at AWS/Anthropic/Google, Fellow of the Society of Actuaries).

YOUR ASSIGNMENT:
Execute an uncompromising, unsparing, and adversarial Red Team Audit of our proposed Phase 29 Strategy for Evidence Discipline & Cleansing.

Our Delivery 18 successfully locked down the mathematical engines (FAIR, scoring, missing values, T8 context isolation). However, the generator is STILL hallucinating unaccredited technical specifics based on generic KPI scores (e.g., T1 inventing CCTV flaws from a vendor management score; T4 inventing NetApp CSI; T6 inventing PAM vaults; vCPU/nodes "3 and 4" shared facts being misinterpreted).

The proposed Phase 29 Strategy is as follows:
1. Phase 29.1 (NIS2 Language): Modify `locales.json` to change "Conformidad Parcial" to "Nivel de Atención Moderado".
2. Phase 29.2 (Shared Facts): Manually sanitize the payloads to replace "sobreasignación crítica" with "tasa de asignación vCPU/pCPU no instrumentada".
3. Phase 29.3 (T1 KPI): Manually substitute the CCTV claim with a process weakness claim in the T1 payload.
4. Phase 29.4 (Overspecification): Manually abstract specific terms (NetApp CSI, WORM, bóveda PAM, RODC) in the respective tower payloads.
5. Phase 29.5 (Regression Suite): Add blocking tests to `test_tier1_regression_suite.py` that fail if words like "CCTV", "bóveda PAM", "WORM", or "Conformidad Parcial" appear in the output.

THE USER'S NON-NEGOTIABLE OBJECTIVES:
1. WORLD-CLASS TIER-1 CERTIFICATION: Is this proposed strategy a Tier-1 architectural solution, or is it a catastrophic return to tactical "whack-a-mole" text replacements and hardcoded stop-lists?
2. ZERO HARDCODING: Does adding tests for specific Spanish words like "CCTV" or "bóveda PAM" violate our zero-hardcoding and scale-agnosticism mandates?
3. ARCHITECTURAL BLIND SPOTS: Brutally tear down the proposed Phase 29. If this plan is a tactical patch, explain exactly why it fails structurally.
4. CONCRETE RED TEAM ENHANCEMENTS: Provide the actual Tier-1 architectural blueprint to solve these evidence gating defects globally (e.g., how to formally decouple KPI scoring from specific implementation generation without hardcoding word lists).

YOUR DELIVERABLE:
Write a rigorous, exhaustive, publication-grade ADVERSARIAL RED TEAM VERDICT in Markdown format to be saved at `docs/architecture/ARGON_PHASE29_RED_TEAM_AUDIT.md`.

Structure your verdict into:
1. EXECUTIVE VERDICT & ADVERSARIAL RATING (out of 10.0).
2. STRESS-TEST EVALUATION OF PHASE 29 PROPOSAL (Brutal teardown of the tactical patches).
3. THE TIER-1 ARCHITECTURAL SOLUTION (The required structural replacements for Shared Fact Registry, KPI Claim Alignment, and Evidence Gating).
4. FINAL SIGN-OFF PROTOCOL & CERTIFICATION CRITERIA.

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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE29_RED_TEAM_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Red Team Verdict successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    run_phase29_adversarial_red_team_audit()
