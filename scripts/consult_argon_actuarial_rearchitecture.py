#!/usr/bin/env python3
"""Consult gemini-4-argon for a definitive, zero-hardcoding actuarial architecture plan."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier

PROMPT = """You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

THE SITUATION:
We are developing a world-class, multi-tenant Assessment Engine (Tier-1 global standard). We need to resolve an actuarial dilemma. 
1. We previously had a hardcoded `domain_weights` dictionary that locked the total Annualized Loss Expectancy (ALE) to 916,416 EUR for our client "Molins" (1.14B EUR revenue, 13,061 EUR/h downtime). This produced numbers the CIO/CFO found highly credible (e.g., 3-year cost of inaction = 2.75M EUR, tail risk P90 = 2.29M EUR).
2. We then introduced a dynamic, bottom-up `BayesianFairCopulaEngine` based on transcript findings. However, because it lacked properly scaled secondary losses and used strict sub-additive diversification, the total portfolio ALE compressed to ~454,000 EUR. 
3. The user rightly rejected the 454K figure as too low (it doesn't justify a 1.4M EUR transformation budget) but also strongly rejects returning to hardcoded dictionaries (the 916K static weights), as that breaks the mandate of being 100% dynamic, transcript-sensitive, and applicable to any company in the world (from $20M to $500B).

USER MANDATES:
1. "Think before coding": Propose a multi-phase architectural plan to guarantee zero errors and Tier-1 quality.
2. Zero Hardcoding: No client names, no static weights, no fixed EUR amounts in the code. It must dynamically scale based on the client's financial telemetry (revenue, downtime hourly rate).
3. 100% Technical English Codebase: No Spanish words in any `.py` file, variable, or regex. Localization happens strictly via `locales.json`.
4. Justifiable Economics: Every Euro calculated must be transparently derivable (e.g., TEF * VULN * (RTO * hourly_rate + secondary_loss)) so a CFO can validate the math.

YOUR TASK:
Analyze this situation deeply and provide a structured, phased architectural plan to implement the optimal solution. 
- Explain mathematically how we can achieve ~900K+ EUR for a 1.14B EUR manufacturing client *dynamically* from transcript findings, without hardcoding the target.
- How do we handle Primary Loss (downtime hours) vs Secondary Loss (fines, OEM emergency fees, brand damage)?
- How do we calibrate the Copula engine so it doesn't artificially squash the risk for highly correlated industrial plants?
- Provide a clear, step-by-step phased execution plan that we will follow to program this flawlessly.

Do not write the full code yet, just the profound analysis and the phased plan.
"""

def main():
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon for Actuarial Rearchitecture Plan...")
    response = client.models.generate_content(model=model, contents=PROMPT)
    
    out_file = REPO_ROOT / "docs/architecture/ARGON_ACTUARIAL_REARCHITECTURE_PLAN.md"
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
