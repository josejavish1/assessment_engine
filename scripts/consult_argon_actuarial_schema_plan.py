#!/usr/bin/env python3
"""Consult gemini-4-argon for a phased implementation plan for a pure Schema-Driven Open FAIR Actuarial Engine."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier

PROMPT = """You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

THE SITUATION:
We are developing a Tier-1, multi-tenant Assessment Engine. We need to finalize the Quantitative Risk Engine (Open FAIR + FAIR-CAM).
We recently removed an unacceptable anti-pattern where the engine scraped Spanish keywords ("obsolescencia", "saturacion") from text strings to assign fixed 18-hour RTOs.
We prototyped a pure, schema-driven Open FAIR model that derives SLE and ALE organically from the `loss_magnitude`, `threat_event_frequency`, and `severity` fields natively present in the JSON telemetry, with domain-specific archetypes for physical parameters (alpha, RTO cap, replacement/secondary hours).

USER MANDATES:
1. Zero Hardcoding: The solution must dynamically scale for ANY company in the world ($20M SMB to $500B+ Global Tier-1) across ANY vertical. No hardcoded client names or fixed EUR values.
2. 100% Technical English Codebase: Absolutely zero Spanish words in any `.py` file, variable, function name, or regex. Localization is strictly delegated to `locales.json`.
3. Actuarial Realism (Physical SLE): The worst-case scenario must be calculated based on the physics of the failure: `Max_Crisis = (RTO * Alpha * Hourly_Rate) + Replacement_Cost + Secondary_Loss`. 
4. The ALE MUST be less than the Worst Crisis (SLE) for each tower, as physics dictate (a once-every-3-years event costs more than the annualized expected loss).
5. "Think before coding": Provide a profound, zero-error, multi-phase architectural execution plan before any code is touched. 

YOUR TASK:
Analyze this situation and provide a structured, multi-phase architectural execution plan to implement this exact schema-driven Open FAIR logic into the `TowerPayloadHydrator`.
- Explain how we will use a `FAIR_PROFILES` dictionary and a `DOMAIN_MAX_RTO` dictionary to guide the physical calculations without hardcoding to a specific client.
- Explain how we ensure that the SLE is calculated rigorously and that `ALE = TEF * VULN * SLE`.
- Provide a clear, step-by-step phased execution plan (e.g., Phase 1: Data Structures and Constants, Phase 2: Schema Parsing and Validation, Phase 3: Actuarial Hydration, Phase 4: Quality Verification).

Provide the output strictly in English, focusing on profound architectural and mathematical correctness.
"""

def main():
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon for Schema-Driven Actuarial Phase Plan...")
    response = client.models.generate_content(model=model, contents=PROMPT)
    
    out_file = REPO_ROOT / "docs/architecture/ARGON_SCHEMA_DRIVEN_ACTUARIAL_PLAN.md"
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
