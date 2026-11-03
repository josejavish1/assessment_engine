#!/usr/bin/env python3
"""Argon-4 Consultation: Architectural Design for Dynamic Custody Resolver (RFC 057)."""

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
Role: Chief Systems Architect & Principal Actuary (Tier-1 Management Consulting / Google Core Infrastructure).

CONTEXT & USER DIRECTIVES:
We are currently evaluating cross-tower risk deduplication in our multi-tower assessment engine. 
A risk identified in Tower 2 (e.g., T2) might actually be owned by Tower 6 (T6). If both towers are evaluated, the risk should be a TANGENTIAL_CONTRIBUTOR in T2 (0 financial value) and a PRIMARY_CUSTODIAN in T6 (full financial value).
However, if a client only contracts T1 and T2 (omitting T6), the risk in T2 cannot remain tangential pointing to T6, because T6 will never be evaluated, resulting in a catastrophic "actuarial blind spot" where a real risk is quantified at 0.

The user demands a flawless architectural blueprint before writing any code. The user stated:
"lo único es antes de ponernos a programar hay que pensar bien como lo vamos a abordar para garantizar que queda sin errores y que vamos a aumentar la calidad de los entregables al 100% y quiero lo piense gemini-4-argon que lo haga sin bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra... Si vas a crear un scritps para pedirle a gemini-4-argon que haga el plan pídeselo en inglés"

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: The solution must be rock-solid, handling missing keys, empty scopes, and malformed risk payloads gracefully.
2. ZERO HARDCODING: Must scale to any enterprise, any vertical, any number of towers, and any language via `locales.json`.
3. 100% TECHNICAL ENGLISH: All proposed Python code, variables, classes, methods, docstrings, and comments must be strictly in English. Spanish is ONLY used as output data via `locales.json`.

YOUR TASK:
Synthesize a comprehensive, authoritative Architectural Blueprint (RFC 057) in Markdown addressing the following:
1. The `DynamicCustodyResolver` Pattern: Design the algorithm that receives an `active_towers_scope` (e.g., `{"T1", "T2"}`) and dynamically promotes a `TANGENTIAL_CONTRIBUTOR` to `PRIMARY_CUSTODIAN` if its `primary_risk_ref` points to a tower outside the active scope.
2. Code Integration Points: Detail exactly where this resolver should be invoked in the pipeline (e.g., before `derive_in_memory_fair_risks` or inside `ActuarialCalculator`).
3. Localization Strategy: Specify the new keys required in `locales.json` (for both 'en' and 'es') to generate the transparent footnote explaining when a risk has been dynamically promoted (e.g., "Risk quantified locally as primary custodian tower (T6) is outside the assessment scope.").
4. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 057 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_057_DYNAMIC_CUSTODY_RESOLVER_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 057 DYNAMIC CUSTODY RESOLVER PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
