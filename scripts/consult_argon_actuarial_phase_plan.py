#!/usr/bin/env python3
"""Consult gemini-4-argon for a phased implementation plan for Actuarial Realism."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier

PROMPT = """You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

THE SITUATION:
We are building a Tier-1, multi-tenant Assessment Engine. We need to finalize the quantitative risk engine (Open FAIR + FAIR-CAM).
We recently identified a severe anti-pattern: the worst-case scenario (Tail Risk / P95) was being calculated using an arbitrary "x2.5" multiplier on the Annualized Loss Expectancy (ALE). 
Furthermore, we need to correctly handle "epistemic dissonance" (when a client claims high maturity in a questionnaire but confesses to severe vulnerabilities in the live interview transcript).

USER MANDATES:
1. Zero Hardcoding: The solution must dynamically scale for ANY company in the world ($20M to $500B+ revenue) and ANY vertical. No magic multipliers (like x2.5). No hardcoded client names or fixed EUR values.
2. 100% Technical English Codebase: Absolutely zero Spanish words in any `.py` file, variable, function name, or regex. Localization is strictly delegated to `locales.json`.
3. Actuarial Realism (Physical SLE): The worst-case scenario must be calculated based on the physics of the failure: `Max_Crisis = (Max_RTO_Hours * Hourly_Downtime_Rate) + Emergency_Replacement_Costs + Fines/Penalties`.
4. Objective Penalization (Epistemic Ledger): Discrepancies between questionnaire and transcript must not result in "invented" monetary penalties. Instead, if a discrepancy is backed by a verified quote in the `EpistemicLedger`, it should mathematically adjust the Vulnerability (VULN) and the empirical RTO, leaving a clear forensic audit trail.
5. "Think before coding": We need a profound, zero-error, phased architectural execution plan before any code is touched.

YOUR TASK:
Analyze this situation and provide a structured, multi-phase architectural execution plan to implement this exact logic into the `BayesianFairCopulaEngine` and `TowerPayloadHydrator`.
- Explain how we will eradicate the x2.5 multiplier and implement the Physical SLE formula dynamically based on the severity of the findings and the zone's operational limits.
- Explain how we will wire the `dissonance_flag` from the `EpistemicLedger` to shift the VULN prior and RTO without hardcoding penalties.
- Provide a clear, step-by-step phased execution plan (e.g., Phase 1: Data Structures, Phase 2: Engine Core, Phase 3: Hydration, Phase 4: Quality Gates).

Provide the output strictly in English, focusing on profound architectural and mathematical correctness.
"""

def main():
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon for Actuarial Phase Plan...")
    response = client.models.generate_content(model=model, contents=PROMPT)
    
    out_file = REPO_ROOT / "docs/architecture/ARGON_ACTUARIAL_REALISM_AND_DISSONANCE_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {out_file.name})")
    print("=" * 80)

if __name__ == "__main__":
    main()
