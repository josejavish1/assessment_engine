#!/usr/bin/env python3
"""Consult gemini-4-argon: Is 2.4M EUR for Cementos Molins defensible before a skeptical CFO/CIO, or is it an inflated theoretical artifact?"""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Fellow of the Open FAIR Institute, Principal Actuarial Arbiter, and Senior Partner in Enterprise Risk Consulting.

USER'S PROFOUND DILEMMA & HONEST SCRUTINY:
"No sé, a mí me parece mucho... ¿Nos pueden tirar ese número o es 100% real? A ver si nos va a decir: 'Pero oye tío, que tú has cogido unos números globales [1.144M EUR] pero que en realidad no es eso', o algo así... O quizás debamos dejarlos, creo que yo mismo tengo sesgos."

THE TWO NUMBERS UNDER DISPUTE:
1. LEGACY MONOLITHIC MODEL: 679,403 EUR (~0.06% of turnover).
   - Driven 100% by machine downtime.
   - Cybersecurity was only 90k EUR, FinOps was only 106k EUR.
   - Extremely comfortable for the client because it looks small and "safe".
2. PURE POLYMORPHIC FAIR MODEL: 2,419,550 EUR (~0.21% of turnover).
   - Cybersecurity (T6) is 725k EUR (30% of total), driven by NIS2 statutory fines and industrial ransomware.
   - FinOps (T8) is 503k EUR (21% of total), driven by Broadcom/VMware 2027 subscription hikes and SECIL integration debt.
   - Resilience (T5) is 239k EUR, Plant Core (T10) is 200k EUR, Compute (T2) is 192k EUR.
   - Total Net Portfolio ALE = 2.42M EUR.

YOUR MANDATE AS PRINCIPAL ACTUARIAL ARBITER:
Conduct an unflinching, objective cross-examination of the 2.42M EUR figure:
1. Is 2.42M EUR defensible before a tough CFO/CIO of a 1.14B EUR industrial group, or is it vulnerable to the objection: "You took our consolidated global turnover and applied theoretical top-down regulatory penalties that don't reflect our actual operational perimeter"?
2. What are the specific vulnerabilities in the 2.42M EUR calculation? (e.g., Did T6 assume maximum NIS2 fine exposure without factoring in supervisory enforcement discretion or insurance? Did T8 assume 5M EUR cloud spend when Molins is heavily on-prem SimpliVity?)
3. What does empirical reality dictate for a mid-cap industrial manufacturing group (1.14B EUR revenue, 3,900 employees, cement/quarries/concrete)?
4. What is the optimal, bulletproof calibration that eliminates both the "under-reported downtime fallacy" (679k) AND the "uncalibrated theoretical scare" (2.4M)? Provide the definitive ruling and exact calibrated figures.

Respond in 100% Technical English with supreme precision and zero sycophancy.
"""

def main() -> None:
    print(f"Submitting Defensibility Challenge to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_MOLINS_ACTUARIAL_DEFENSIBILITY_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nDefensibility Ruling written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:3500])
    if len(ruling) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
