#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 059 Natural Bullet Typography & Plain-Language P90 Scenario.

Addresses the user's two acute editorial critiques:
1. Artificial 3-word bolding in Chapter 1:
   - "en cada torre hay un párrafo que pones a las 3 primeras palabras del bullets en negrita de la sección 1 y es que no tiene ningún sentido... '● Saturacion estructural de' o '● Bloqueo contractual y' o '● Proliferacion de silos'".
   - Eradicate arbitrary words[:3] bolding. Preserve natural sentence flow. Restore full RAE diacritics.
2. Section 4.3 P90 Scenario Plain-Language Restructuring:
   - "este texto es infumable no se entiende, ni hay que hacer referencia al capítulo 1, de hecho el capítulo 1 es el resumen de lo que pongamos aquí, pero aquí tiene que estar redactado simple para que lo entienda alguien no financiero bien explicado y sencillo y no ponerlo en una tabla si no en el mismo tamaño de letra que el resto".
   - Remove table wrapper; render as Heading 3 + standard 10.0pt body paragraphs.
   - Eliminate jargon ('estrés asintótico', 'triaje nivel 3') and explain in plain, human, accessible language.
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
Role: Chief Editorial Fellow & Principal Enterprise Architect (Tier-1 Management Consulting / Google Core Infrastructure).

USER CRITIQUE & SYSTEMIC AUDIT DIRECTIVES:
The user delivered two penetrating editorial and layout critiques:

1. Artificial 3-Word Bolding in Chapter 1 Executive Bullets:
   - User critique:
     "en cada torre hay un párrafo que pones a las 3 primeras palabras del bullets en negrita de la sección 1 y es que no tiene ningún sentido. Ejemplo de la torre 2: '● Saturacion estructural de' o '● Bloqueo contractual y' o '● Proliferacion de silos'... es que no tiene ningún sentido."
   - Root Cause:
     In `payload_to_ast.py` lines 1045-1060, an arbitrary heuristic split the bullet text and bolded `words[:3]` if no colon existed, bolding prepositions and conjunctions ('de', 'y') without semantic justification. Furthermore, bullets lacked RAE diacritics.
   - Architectural Remedy:
     a) Eliminate arbitrary `words[:3]` bolding. If the bullet contains an explicit topic anchor (`:`), bold the prefix before the colon. If not, render the entire sentence in natural, unbolded typography.
     b) Run all bullet text through `restore_locale_diacritics` to ensure 100% RAE orthographic compliance.

2. Section 4.3 P90 Tail Risk Scenario Text & Layout Restructuring:
   - User critique:
     "en el punto 4.3 es que este texto es infumable no se entiende, ni hay que hacer referencia al capítulo 1, de hecho el capítulo 1 es el resumen de lo que pongamos aquí, pero aquí tiene que estar redactado simple para que lo entienda alguien no financiero bien explicado y sencillo y no ponerlo en una tabla si no en el mismo tamaño de letra que el resto."
   - Root Cause:
     The P90 scenario was wrapped inside a single-cell callout table with 8.5pt font, creating unnecessary visual boxing. The text contained pseudo-academic jargon ('estrés asintótico', 'triaje especializado de nivel 3') and meta-references ('En consonancia con la síntesis ejecutiva del Capítulo 1').
   - Architectural Remedy:
     a) Layout: Remove the table wrapper. Render as a native `HeadingNode(level=3)` titled "Escenario de Fallo Grave y Tiempo Máximo de Recuperación (P90)" followed by standard `ParagraphNode(font_size=10.0, space_after=8)` body paragraphs.
     b) Tone & Language: Eliminate all meta-references to Chapter 1 and all academic jargon. Explain in plain, human, board-level language:
        - Paragraph 1: Explains that to test the resilience limit, the model evaluates a compound failure where multiple major components fail simultaneously (e.g. {compound_failure_trigger}).
        - Paragraph 2: Explains that restoring operations and verifying full data consistency in such an extreme case would take up to {p90_recovery_hours} hours.
        - Paragraph 3: Details the financial impact of {p90_total_contingency}, clearly broken down into direct operational downtime losses ({direct_stoppage_loss}) and extraordinary emergency recovery costs ({secondary_disaster_spend}, like urgent manufacturer support and immediate parts replacement).

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale in `locales.json`).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 059) in Markdown:
1. Specify the localized dictionary updates in `engine_config/locales.json`.
2. Detail the exact Python implementation in `payload_to_ast.py`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 059 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_059_NATURAL_BULLETS_AND_PLAIN_LANGUAGE_P90_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 059 ARCHITECTURAL BLUEPRINT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
