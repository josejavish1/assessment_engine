#!/usr/bin/env python3
"""Argon-4 Consultation: Architectural Design for Site-Weighted Actuarial Realism (RFC 036)."""

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


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Role: Principal Actuarial Systems Architect & Chief Compiler Engineer (Google Tier-1 / Anthropic Core Infrastructure / MIT Actuarial Fellow).

CONTEXT & USER CRITIQUE (FINANCIAL REALISM & SITE-SPECIFIC WEIGHTING):
The user reviewed the executive narrative and raised two critical objections regarding the financial calculations:

1. "por cierto que digas que molins tienn facturación anual consolidada de 1.000.000.000 € (1.000 M€ / 1 Billion EUR). Suena demsiado rendondo como inventado como si ese número no lo hubieras cogido de la fuente oficial, ¿puede que sea algún gap o tenemos alguna fuente para saberlo."
   - The user noticed the 1,000,000,000 € figure and correctly suspects it is a hardcoded fallback or gap. 
   - We did, in fact, discover `raw_rev = organization_profile.get("annual_revenue_amount") or organization_profile.get("annual_revenue_eur") or 1000000000` in `src/assessment_engine/domain/actuarial/downtime_calibrator.py`. This is a hardcoded fallback!

2. "Además eses calculo parece un poco simplista no? es decir, tiene muchas fabricas una parada en una no tiene un peso total. Sigo pensando que tenemos serios problemas generales en cuanto a los calculos de los riesgos."
   - The user correctly identifies a major actuarial flaw: applying the *global consolidated corporate turnover* to a *single local site outage* (e.g., the Sant Vicenç dels Horts plant) is mathematically simplistic and heavily inflates the risk. If a company has 15 factories, an outage at one factory does not paralyze 100% of the global revenue. 
   - We need a `site_revenue_weight_pct` or `perimeter_criticality_factor` that mathematically scales down the global revenue to the specific business value sustained by the audited perimeter (the specific data center, plant, or business unit).

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless mathematical and architectural design.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The engine must scale to ANY company in the world: any tier (50M€ to 50B€ turnover), any vertical, any currency, and any language.
   - Zero hardcoded client names, zero hardcoded monetary amounts in Python code.
   - The 1,000,000,000 fallback MUST BE PURGED. We must either read the exact value from the payload or fail-fast/default gracefully using actuarial standards without faking a round number.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, and docstrings must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 036) in Markdown:
1. Architectural fix for the 1,000,000,000 € hardcoding in `downtime_calibrator.py`: How to extract the real revenue from the intelligence payloads, and what to do if it's missing (without hardcoding a round number).
2. The Actuarial Design for "Site-Weighted Revenue Scaling" (Site Revenue Factor):
   - Introduce a new parameter (e.g., `perimeter_revenue_weight_pct`) into the telemetry to represent the percentage of global revenue that flows through the audited site/perimeter.
   - Update the mathematical formula: `Hourly Cost = (Annual Revenue * Site Weight %) * Sector Factor`.
3. Pedagogy: Update the executive narrative template in `locales.json` to explicitly mention this site-weighting factor so the CIO sees the calculation is highly realistic and granular to their specific facility.
4. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 036 (Site-Weighted Actuarial Realism) from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_036_SITE_WEIGHTED_ACTUARIAL_REALISM_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 036 SITE-WEIGHTED ACTUARIAL REALISM")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
