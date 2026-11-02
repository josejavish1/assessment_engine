#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 048 Assertive Partnership Tone & Executive Cockpit Layout Architecture.

Formulates the architectural blueprint before modifying any code:
1. Eradicates client-blame / prosecutorial language across the entire document in favor of assertive, constructive engineering diplomacy.
2. Simplifies convoluted consultant filler (e.g. eradicates 'en este dominio', 'desde una perspectiva económica').
3. Re-architects Chapter 1 layout into an 'Executive Cockpit' by placing the Diagnostic Triad Table directly below the KPI Scorecard strip.
4. Verifies OpenXML single-page vertical containment on Page 3.
5. Upholds 100% Technical English codebase and zero hardcoding across all 10 capability towers.
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
Role: Chief Executive Communications Strategist & Principal Document Architect (McKinsey Senior Partner / Gartner Distinguished Analyst / Google Core Infrastructure Fellow).

CONTEXT & USER CRITIQUE (DEEP CONSULTING PSYCHOLOGY & VISUAL ERGONOMICS):
The user delivered three critical insights that strike at the heart of executive client advisory:

1. Eradicating Client-Blame Language Across the Entire Document ("No echarle la culpa al cliente"):
   - User critique:
     "En la torre 1 veo una frase como 'se han identificado deficiencias estructurales que limitan su fiabilidad y exponen al negocio a interrupciones imprevistas ante cualquier fallo de componente.' en realidad decirle eso al cliente es muy fuerte y esto aplica a todo el documento: el documento no puede ser un documento de echarle la culpa al cliente, tiene que matizarse ese lenguaje, si no nos lo van a tirar a la cara. Tiene que exponerle los problemas pero en un lenguaje asertivo."
   - Psychological & Strategic Analysis:
     * In executive advisory, language that sounds prosecutorial ("deficiencias estructurales que exponen al negocio ante cualquier fallo", "aparente estabilidad que depende de la intervención reactiva del personal") triggers acute defensiveness from the IT Director, CIO, and engineering leads.
     * If the client feels attacked or blamed, they reject the findings and kill the project ("nos lo van a tirar a la cara").
     * Core Principle: **Assertive Engineering Diplomacy**.
       a) We acknowledge the dedication and foundation established by the internal teams.
       b) We frame challenges as the natural result of enterprise growth, scale, and escalating operational demands on legacy architectures.
       c) We state technical realities with firm, objective engineering precision without pejorative or accusatory adjectives.
       d) We present gaps as clear, actionable opportunities to strengthen resilience, autonomy, and fault tolerance.

2. Direct, Simple, Uncomplicated Phrasing (Kill "en este dominio" and Stiff Filler):
   - User critique:
     "Luego una frase como esta se ve rara: 'Desde una perspectiva económica, la indisponibilidad no planificada en este dominio genera un coste de parada estimado en 13.061,29 €/h (desglosado en la Sección 4.1).' Especialmente por lo de 'en este dominio', como que se complica la lectura. Quizás debería decirse más explícito y sencillo."
   - Requirement:
     * Eradicate stiff consultant boilerplate ("Desde una perspectiva económica", "en este dominio", etc.).
     * Use clean, direct, punchy phrasing:
       "En caso de producirse una parada imprevista del servicio, el coste operativo se estima en **{hourly_burn_rate_fmt}** (desglosado en la Sección 4.1)..."

3. Executive Cockpit Visual Layout (Reordering Chapter 1):
   - User critique:
     "y estoy pensando que la tabla del final de apartado 1, donde se dicen la fortaleza, brecha arquitectura y cuello de botella, quizás debería estar justo debajo de la tabla inicial 'PUNTUACIÓN ACTUAL BANDA DE MADUREZ EXPOSICIÓN ANUAL ESTIMADA'."
   - Visual Architecture Analysis:
     * Placing the Diagnostic Triad Table immediately below the KPI Scorecard strip creates an **Executive Cockpit**:
       1. Row 1: The Metrics (Score, Band, Annual Exposure).
       2. Row 2: The Triad At-a-Glance (Fortaleza Operativa, Brecha de Arquitectura, Cuello de Botella Sistémico).
       3. Row 3: Headline Finding.
       4. Row 4: Narrative Synthesis (Posture & Mission -> Scannable Bullets -> Actuarial Latent Exposure -> Current-State Diagnostic Verdict).
     * An executive scanning the first third of Page 3 gets 100% of the core metrics and triad truths in 10 seconds!
     * Vertical Budget Check: Verify that with this reordering, Page 3 remains strictly self-contained without overflowing to Page 4.

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any enterprise 50M€ to 50B€, any vertical, any currency, any locale).
3. 100% Technical English codebase (zero Spanish words in Python source files).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 048) in Markdown:
1. Editorial Lexicon & Tone Transformation: Formulate the transformation rules from accusatory prose to Assertive Engineering Diplomacy.
2. Complete bilingual templates for `engine_config/locales.json` in Spanish (`es`) and English (`en`).
3. Executive Cockpit Layout Blueprint: Show the exact AST ordering in `payload_to_ast.py`.
4. OpenXML Vertical Budget Validation for Page 3.
5. Concrete Python implementation snippets in 100% Technical English.
"""

    print(f"Requesting RFC 048 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_048_ASSERTIVE_PARTNERSHIP_TONE_AND_EXECUTIVE_COCKPIT_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 048 ASSERTIVE PARTNERSHIP TONE & EXECUTIVE COCKPIT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
