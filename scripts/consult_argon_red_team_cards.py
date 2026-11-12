"""Consult gemini-4-argon: Adversarial Red Team Attack on Proposed Risk Card & Actuarial Presentation Reform."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

PROMPT = """You are 'gemini-4-argon', operating as the Chief Adversarial Red Team Leader, Head of Model Validation (SR 11-7), and Senior Fellow of the Open FAIR Institute.

A team of software engineers has just proposed a 4-point reform to fix executive and auditor complaints regarding risk cards in the generated deliverables:

--- BEGIN PROPOSAL UNDER ATTACK ---
PROPOSAL 1: Arithmetic Breakdown in Risk Cards:
Instead of printing "8.0h * 9,142 €/h = 45,224 €", break down the Single Loss Expectancy (SLE) into 3 additive terms:
  Primary Downtime Impact (Hours * Rate * Alpha) = 25,598 €
+ Direct Replacement Cost (Emergency hardware/response) = 15,000 €
+ Secondary Loss Magnitude (SLA / fines / PR) = 4,626 €
= Total Single Loss Expectancy (SLE): 45,224 €

PROPOSAL 2: Linear Open FAIR Equation Display on the Card:
Show:
  Threat Event Frequency (TEF): 2.5 events/year
* Effective Vulnerability (Vuln): 62% (derived from CMMI 1.93)
= Loss Event Frequency (LEF): 1.55 losses/year
* Single Loss Expectancy (SLE): 45,224 €
= Annualized Loss Expectancy (ALE): 70,079 €/year
So any auditor multiplying 1.55 * 45,224 € gets exactly 70,079 €.

PROPOSAL 3: Severity-Based RTO Dispersion Multipliers:
In parameter packs, define:
  CRITICAL: 2.0x RTO multiplier
  HIGH: 1.0x RTO multiplier
  MEDIUM: 0.40x RTO multiplier
  LOW: 0.15x RTO multiplier
So that when findings lack explicit RTO, they don't all get a flat 8.0 hours.

PROPOSAL 4: Heatmap Strict Alignment to SLE:
Align the Heatmap Loss Magnitude (LM 1 to LM 5) strictly to the mean SLE shown on the card (e.g. 45,224 € -> LM 2).
--- END PROPOSAL UNDER ATTACK ---

YOUR MISSION (RED TEAM ATTACK):
Ruthlessly dissect, attack, and expose every mathematical, actuarial, architectural, and operational flaw in this proposal.

Specifically analyze:
1. Jensen's Inequality & Non-Linear Monte Carlo vs Linear Display (Proposal 1 & 2):
   - In a compound Poisson-Lognormal copula simulation with secondary loss binomial thinning, does E[LEF * SLE] equal E[LEF] * E[SLE]?
   - If the portfolio engine applies Euler sub-additive diversification allocation (where allocated_ale < standalone_ale), what happens if you display standalone LEF * SLE on the card? Will the card total contradict the portfolio and tower subtotal?
2. Conditional Mean vs Additive Breakdown (Proposal 1):
   - If secondary loss only occurs with probability p_sec = 0.10, is E[Secondary Loss | Event >= 1] equal to adding a flat secondary cost to every single event? What happens to variance and tail percentiles?
3. Double-Counting Severity Multipliers (Proposal 3):
   - If severity (CRITICAL, HIGH, etc.) is ALREADY used to scale TEF, does scaling RTO with severity introduce correlated double-counting?
4. The Heatmap Masking Trap (Proposal 4):
   - If a catastrophic, single-point-of-failure risk has low frequency (TEF = 0.05) and moderate mean SLE, but a 10M € P99 tail shock, will putting it in LM 2 make the Board think it's a minor green risk?
5. The Infallible Alternative:
   - How can we display complete mathematical clarity that satisfies a ruthless auditor WITHOUT committing actuarial fraud or lying about Monte Carlo copula dynamics?

Respond in 100% Technical English with supreme adversarial rigor and zero polite filler.
"""


def main() -> None:
    print(f"Submitting Red Team Review to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_ACTUARIAL_CARD_PROPOSAL_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nRed Team Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500] + ("\n... [TRUNCATED]" if len(report) > 3500 else ""))


if __name__ == "__main__":
    main()
