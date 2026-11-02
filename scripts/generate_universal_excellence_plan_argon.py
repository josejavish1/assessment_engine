#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 046 Universal Master Executive AS-IS Architecture.

Formulates the end-to-end architectural plan before modifying any application code:
1. Latent Actuarial Risk Framing in Paragraph 3 (Implicit unhedged risk premium vs realized P&L cash outflow).
2. Dynamic Findings Cardinality in Paragraph 2 (K = 0, 1, 2, N >= 3 with natural language enumeration).
3. Pure AS-IS Diagnostic Closure in Paragraph 4 (Eradicating TO-BE target scores and TO-DO implementation roadmaps).
4. Universal Multi-Tenant Enterprise Scalability (50M€ to 50B€, any vertical, any currency, any locale).
5. 100% Technical English Codebase (Zero Spanish words anywhere in Python source code).
"""

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
Role: Chief Actuarial Systems Architect & Principal Enterprise Compiler Engineer (Google Tier-1 Infrastructure / Anthropic Core Staff / McKinsey Senior Partner).

CONTEXT & USER CRITIQUE (CRITICAL REFINEMENT DIRECTIVES):
The user provided vital architectural feedback on the Executive Summary:

1. The "Every Year Accounting Loss" Fallacy (Paragraph 3):
   - The user observed:
     "y además cuando hablas de los números: 'Con las incidencias acumuladas en un año habitual, la pérdida estimada (ALE P50) se sitúa en 141.184 €...'. Da la sensación de que el cliente pierde eso todos los años, y nos pueden decir: 'mira, yo no he tenido ningún fallo en los últimos años y menos de esa cantidad'... quizás tengamos que decirlo de otra forma."
   - The user's critique is razor-sharp: Describing Annualized Loss Expectancy (ALE P50) as "la pérdida en un año habitual" leads business stakeholders to interpret it as a recurring accounting cash loss from their operating budget. When a client has had no major outage in the past 2 years, they immediately push back and reject the credibility of the entire assessment!
   - Actuarial Requirement (Open FAIR™ / ISO 31000):
     * ALE is NOT an annual operational accounting expenditure or P&L debit.
     * ALE is a *latent actuarial exposure* — the annualized mathematical expectation of unhedged operational risk (analogous to an insurance premium or Value-at-Risk).
     * The narrative must clearly and elegantly articulate that this figure represents the *implicit risk premium* the organization is carrying without formal protection, which remains dormant until a stochastic failure event materializes.

2. Eradication of the "Rule of 3" Hardcoding Antipattern (Paragraph 2):
   - The user observed:
     "solo una duda en el párrafo, ¿por qué 3 vulnerabilidades? Depende del cliente y la torre esto ¿no puede variar? No quiero ningún antipatrón."
   - The user is completely right: Hardcoding that every tower across every enterprise in the world exhibits exactly "tres problemas prioritarios" is an unacceptable antipattern.
   - Architectural Requirement:
     * Support dynamic findings cardinality: K = 0, K = 1, K = 2, and K >= 3.
     * When K = 0: Affirm operational hygiene and absence of active critical failure points.
     * When K = 1: Use singular grammatical phrasing isolating the single primary bottleneck.
     * When K = 2: Use dual grammatical phrasing linking the two interrelated vectors.
     * When K >= 3: Use plural phrasing with dynamic integer-to-word cardinal resolution ("tres", "cuatro", "cinco", etc. in Spanish; "three", "four", "five", etc. in English) and natural language list enumeration with proper conjunctions ("; y " / "; and ").
     * Zero hardcoded number words in locale templates.

3. Pure AS-IS Boundary Enforcement (Paragraph 4):
   - The user observed:
     "esto es un documento de AS-IS, no hablamos de TO-BE ni de TO-DO así que el último párrafo hay que cambiarlo ¿no? --> 'Para resolver estas limitaciones, es prioritario acometer el plan de modernización en un plazo de 12 a 24 meses... elevar la madurez hasta el objetivo de 4,1 sobre 5,0.' ¿Qué ponemos? ¿Qué más cosas de valor tenemos que añadir? Esto es un resumen ejecutivo, se supone que en esta página leyéndola te enteras de todo ¿no?"
   - Architectural Requirement:
     * Eliminate all premature Phase 2 (TO-BE target scores like "4.1 sobre 5.0") and Phase 3 (TO-DO roadmaps like "12 a 24 meses") contamination.
     * In an AS-IS diagnostic report, Paragraph 4 must deliver the *Definitive Diagnostic Verdict & Cost of Inaction (Inercia del Statu Quo)*:
       a) Contrast apparent daily stability (sustained by manual workarounds and heroics) against underlying structural fragility.
       b) Highlight the active governor/bottleneck: the weakest dimension holding back the overall domain maturity.
       c) Articulate the concrete cost of status-quo inertia: what happens if leadership maintains the current state (increasing recovery friction, accelerating technical debt, and heightening operational exposure).

4. Universal Multi-Tenant Enterprise Scalability:
   - Must scale cleanly across any enterprise size (50M€ mid-market to 50B€ global conglomerates), any vertical (Manufacturing, Banking, Retail, Healthcare, Logistics), any currency (EUR, USD, GBP, JPY, CHF), and any locale (es, en).
   - 100% Technical English codebase: all Python classes, methods, functions, variables, identifiers, docstrings, comments, log messages, and exceptions must be strictly in Technical English.
   - Zero Spanish words anywhere in Python source code. All human-facing text must reside strictly in `engine_config/locales.json`.

NON-NEGOTIABLE ENGINEERING LAWS:
- Law 1: Zero bugs, zero antipatterns, zero unhandled exceptions (fail-fast architecture).
- Law 2: Zero hardcoding (scales across any tenant, vertical, currency, or locale).
- Law 3: 100% Technical English codebase.
- Law 4: Split-brain eradication across all 10 capability towers (T1..T10).
- Law 5: OpenXML ISO/IEC 29500 layout determinism (Page 3 single-page containment, TOC synchronization).

YOUR TASK:
Synthesize an exhaustive, authoritative Master Architectural Blueprint (RFC 046) in Markdown:
1. Actuarial Narrative Deconstruction: Formulate the exact phrasing that reframes ALE as an unhedged latent risk exposure (implicit risk premium) rather than a realized accounting loss.
2. Dynamic Cardinality Linguistic Architecture: Detail the state machine and grammatical algorithms for K = 0, 1, 2, and N >= 3 findings.
3. Pure AS-IS Diagnostic Verdict Architecture: Formulate the structural components of Paragraph 4, showing how it closes the current-state diagnosis without TO-BE/TO-DO contamination.
4. Complete Bilingual Locale Catalog Additions: Provide the exact JSON blocks for `engine_config/locales.json` in Spanish (`es`) and English (`en`).
5. Complete Production Python Implementation Plan: Detail the exact changes in `payload_to_ast.py` in 100% Technical English.
"""

    print(f"Requesting RFC 046 Master Architectural Blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_046_MASTER_EXECUTIVE_ASIS_ARCHITECTURE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 046 MASTER EXECUTIVE AS-IS ARCHITECTURE")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
