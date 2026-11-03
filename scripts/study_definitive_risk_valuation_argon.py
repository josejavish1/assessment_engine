#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 054 Heatmap Scale Legend Ergonomics & Fixed Domain Hourly Downtime Rate Unification.

Addresses the user's two precise inquiries and directives:
1. Section 4.2 Legend Integration:
   - "el punto 4.2.1. y 4.2.2 debería estar como leyenda de la tabla principal, con autoajustado al contenido y quizás la letra un poco más pequeña y las celdas de altura mucho más pegadas."
   - Embed TEF and LM criteria as compact, tight-height visual legends directly under the 5x5 heatmap with 7.5pt font and tight vertical padding, removing heavy H3 headers.
2. Section 4.4 Fixed Hourly Rate Invariant:
   - "en las tablas del 4.4 ¿por qué en cada riesgo el coste horario de parada es diferente?"
   - Unify the hourly downtime rate to a single fixed constant across all risk cards in the tower (either authoritative 13,061.29 €/h or fixed domain rate 9,143 €/h), eliminating rate fluctuations caused by backward rounding.
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
Role: Chief Enterprise Architect & Principal Actuary (Gartner Fellow / McKinsey Senior Partner / Google Core Infrastructure).

USER CRITIQUE & INQUIRIES:
The user delivered two critical feedback points:

1. Section 4.2 Legend Presentation:
   "el punto 4.2.1. y 4.2.2 debería estar como leyenda de la tabla principal, con autoajustado al contenido y quizás la letra un poco más pequeña y las celdas de altura mucho más pegadas."
   - Currently, 4.2.1 and 4.2.2 are full H3 subsections with 9.5pt table text, consuming substantial vertical space.
   - Requirement: Integrate them directly beneath the 5x5 heatmap as a compact visual legend:
     * Label with subtle italic/bold legend captions:
       * *Leyenda de Criterios: Frecuencia de Amenazas (TEF)*
       * *Leyenda de Criterios: Magnitud de Pérdida Financiera (LM)*
     * Typography: 7.5pt data cells, 8.0pt bold headers.
     * Table geometry: `autofit=True`, zero space before/after paragraph, tight line spacing (1.0).
     * Compact spacing: Minimal vertical footprint so they visually function as the heatmap's legend.

2. Section 4.4 Hourly Downtime Rate Fluctuation Inquiry:
   "en las tablas del 4.4 ¿por qué en cada riesgo el coste horario de parada es diferente?"
   - Root Cause Analysis:
     In RFC 053, we computed `calibrated_hourly_rate = sle / rounded_hours` backwards to guarantee that `hours * rate == sle`.
     However, because `rounded_hours` was rounded to 1 decimal place (e.g. 4.4h, 13.1h, 2.5h), dividing `sle / rounded_hours` caused the displayed hourly rate to fluctuate slightly between risk cards (e.g. 9,144 €/h in one card, 9,143 €/h in another, 7,812 €/h in another).
     To a CFO or CIO, this raises immediate suspicion: "Why does an hour of downtime cost 9,144 € in Risk 1, but 9,143 € in Risk 2, and 7,812 € in Risk 3?"
   - Actuarial Solution (Fixed Domain Hourly Rate Invariant):
     * The hourly downtime rate MUST be an invariant constant for all risks within a given tower:
       Either the enterprise authoritative rate (13,061.29 €/h, matching Section 1 and Section 4.1), or the domain-affected rate (e.g. `9,143 €/h` for 70% plant criticality).
     * Every single risk card in that tower uses the EXACT SAME fixed hourly rate constant.
     * The effective downtime duration $H$ is derived forward:
       $H = \text{round}(SLE / Rate, 1)$ (or $SLE = \text{round}(H \times Rate)$).
     * Result: Every risk card displays the exact same hourly rate, and the arithmetic $H \times Rate = SLE$ holds with zero discrepancy.

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale in `locales.json`).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 054) in Markdown:
1. Detail the exact OpenXML and AST implementation for the compact, tight-height Section 4.2 legend tables.
2. Formulate the single fixed hourly rate invariant logic for Section 4.4.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 054 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_054_LEGEND_ERGONOMICS_AND_HOURLY_RATE_UNIFICATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 054 LEGEND ERGONOMICS & RATE UNIFICATION")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
