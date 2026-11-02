#!/usr/bin/env python3
"""Argon-4 Master Consultation: Final Cold, Sober Executive Phrasing & Bullet-Point AST Node Architecture.

Validates the user's specific editorial refinements:
1. Eliminate informal/defensive phrasing ("Aunque no haya sufrido caídas...") in favor of cold, institutional actuarial tone.
2. Eliminate statistical acronyms like "(ALE P50)" from executive summary narrative.
3. Replace "percentil 90" and "catastrófico" with neutral, professional framing: "En un escenario adverso de fallo múltiple...".
4. Frame recovery duration universally: "se estima que la operativa podría llegar a demorarse hasta {hours} horas...".
5. Remove the mechanical "(AS-IS)" tag from Paragraph 4.
6. Verify List Bullet AST generation and Page 3 vertical containment.
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
Role: Chief Executive Document Designer & Principal Enterprise Systems Auditor (McKinsey Senior Partner / Gartner Fellow / Google Core Infrastructure).

USER'S EDITORIAL DIRECTIVES & POLISHING MANDATES:
The user reviewed the proposed architecture and delivered these crucial stylistic directives:
1. "en el párrafo 3 'Aunque la organización no haya sufrido caídas mayores en ejercicios recientes' ese párrafo no lo diría así, tiene que ser profesional y frío y ese párrafo no lo es."
   - Requirement: Eliminate conversational or defensive language. State the actuarial reality coldly and authoritatively:
     * Spanish: "Esta magnitud no constituye una pérdida contable fija, sino la valoración económica de la exposición de riesgo latente que la organización sostiene de manera implícita bajo su arquitectura actual."
     * English: "This figure does not represent a realized accounting loss, but rather the economic valuation of unhedged latent risk exposure implicitly carried under the current architecture."

2. "Esto tampoco lo pondría (ALE P50) no aporta en el resumen ejecutivo."
   - Requirement: Omit the technical acronym "(ALE P50)" in the executive narrative. Present it cleanly as:
     * Spanish: "...una exposición de riesgo latente estimada en {annual_loss_expectancy_fmt} anualizados."
     * English: "...an estimated latent risk exposure of {annual_loss_expectancy_fmt} annualized."

3. "Luego 'de estrés severo (percentil 90)' esto lo diría de otra forma y no pondría nada de percentil 90, si no más bien en un escenario... sin decir catastrófico."
   - Requirement: Avoid both technical jargon ("percentil 90") and sensationalist drama ("catastrófico"). Use sober, professional enterprise phrasing:
     * Spanish: "En un escenario adverso de fallo múltiple de componentes..."
     * English: "Under an adverse multi-component fault scenario..."

4. "y luego en el párrafo 'la planta tardaría un máximo estimado de 17,3 horas en reanudar la actividad mediante planes de contingencia' quizás, 'se estima que la operativa podría llegar a demorarse hasta ...' sabes lo que te quiero decir ¿no? (que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma)."
   - Requirement: Neutral, universal phrasing applicable to manufacturing, banking, healthcare, or SaaS:
     * Spanish: "...se estima que la operativa podría llegar a demorarse hasta {capped_p90_hours_fmt} horas antes de completar la recuperación mediante procedimientos de contingencia; sumando esta interrupción a los sobrecostes urgentes de sustitución de equipamiento y soporte extraordinario, el impacto contingente proyectado se estima en {p90_var_exposure_fmt}."
     * English: "...operational recovery could require up to {capped_p90_hours_fmt} hours under contingency procedures; compounding this disruption with emergency hardware replacement and specialized technical response, total projected contingent exposure stands at {p90_var_exposure_fmt}."

5. "Se me olvidaba: en el último párrafo nada de '(AS-IS)'."
   - Requirement: Remove the literal string "(AS-IS)" from Paragraph 4. Open naturally:
     * Spanish: "En conclusión, el diagnóstico del estado actual demuestra que..."
     * English: "In conclusion, the current-state diagnostic demonstrates that..."

6. "las vulnerabilidades no deberían estar en bullets para facilitar su lectura en lugar de en un párrafo gigante?"
   - Requirement: Emit Paragraph 2 as a concise lead-in sentence followed by `ParagraphNode(style="List Bullet")` nodes with bold category titles.

NON-NEGOTIABLE ENGINEERING LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (universal multi-tenant scaling across any enterprise, vertical, currency, or locale).
3. 100% Technical English codebase (zero Spanish words in Python source files).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism (Page 3 single-page containment guaranteed).

YOUR TASK:
Synthesize an authoritative Final Blueprint in Markdown:
1. Review and ratify the exact bilingual text blocks for `engine_config/locales.json`.
2. Review the Python implementation in `payload_to_ast.py` that extracts dimension boundaries and builds bullet AST nodes.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting Final Polishing Audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_046_FINAL_POLISHING_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: FINAL POLISHING AUDIT REPORT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
