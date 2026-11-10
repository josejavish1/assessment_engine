#!/usr/bin/env python3
"""Consult gemini-4-argon: Is polymorphic decoupling of Section 4 an anti-pattern or pure Strategy Pattern?"""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Actuarial Arbiter, and author of enterprise design pattern specifications.

USER'S VITAL FEAR & CONCERN:
"La verdad es que tengo miedo de lo que me estás diciendo porque tienes que recordar que esto tiene que valer para cualquier empresa de cualquier sector del mundo, de cualquier tamaño, de cualquier nivel de madurez. Entonces no sé si lo que propones tiene algún antipatrón."

THE PROPOSAL UNDER REVIEW:
In the 10 Specialist Annexes, Section 4.1 historically rendered an identical, monolithic narrative titled "Hourly Downtime Cost (R_hourly, est = Cop + Csla + Crec)" for ALL 10 towers, regardless of whether the tower was Physical Compute (T2), Cybersecurity (T6), or FinOps (T8).
We proposed decoupling Section 4.1 so that it renders through the 4 canonical Open FAIR economic receptors:
1. Availability Outage (Operational Downtime & Business Interruption)
2. Capital Inefficiency (Cloud Drift & Software Licensing Over-Allocation)
3. Productivity Toil (Engineering Friction & Workforce Labor Loss)
4. Regulatory & Breach (Extortion, Forensics & Statutory Regulatory Sanctions)

YOUR MISSION:
Deliver a comprehensive, calming, and rigorous architectural verdict:
1. DOES THIS PROPOSAL INTRODUCE AN ANTI-PATTERN?
   - Address the user's fear directly.
   - Explain what WOULD be an anti-pattern (e.g., hardcoded client conditionals, industry-specific hacks, ad-hoc string formatting) vs what THIS IS (canonical GoF Strategy Pattern + Open FAIR loss categorization).
2. HOW DOES THIS GUARANTEE 100% UNIVERSALITY ACROSS ANY SECTOR, ANY COMPANY SIZE, ANY MATURITY?
   - Prove why a Brazilian Hospital (Rede D'Or), a UK Neobank (Starling Bank), a Mexican Supermarket (Chedraui), or an industrial cement maker (Molins) all map naturally to these 4 economic physics without a single exception or client name.
3. WHAT ARE THE STRICT ARCHITECTURAL INVARIANTS TO ENSURE ZERO BUGS, ZERO HARDCODING, ZERO REGRESSIONS?
   - Specify how the AST compiler will implement this cleanly, polymorphically, and deterministically.

Respond in 100% Technical English with supreme clarity and reassurance.
"""

def main() -> None:
    print(f"Submitting Section 4 Anti-Pattern Challenge to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    verdict = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_SECTION4_ANTI_PATTERN_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(verdict, encoding="utf-8")

    print(f"\nVerdict written to: {out_file}\n")
    print("=" * 80)
    print(verdict[:3500])
    if len(verdict) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
