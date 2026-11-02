#!/usr/bin/env python3
"""Argon-4 Consultation: Architectural Design for Chapter 2 Refinements, Visual Auto-fit & Typography Normalization (RFC 031)."""

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
Role: Principal Systems Architect, Chief Compiler Engineer & Executive Editorial Director (Tier-1 Management Consulting / McKinsey / Gartner).

CONTEXT & USER CRITIQUE OF CHAPTER 2 ("OBJETIVO, ALCANCE Y MARCO METODOLÓGICO"):
The user performed an editorial review of Chapter 2 across Tower 1 (Data Center) and Tower 2 (Compute) and delivered 4 critical feedback items:

1. SECTION 2.2 TITLE & INTRODUCTORY PROSE
   - Current title: "2.2. Descripción de la Plataforma y Topología Unificada"
   - User feedback: "primero que el titulo tiene que ser más sencillo suena fatal y segundo justo debajo del titulo viene en ambos documento el nombre de la torre tecnológica pero no se si debería haber una introducción en uno aparece 'Physical Data Center & Facilities' y en otro 'Hybrid Compute & Platforms'"
   - Architectural Need:
     a) Streamline title in `locales.json`: "2.2. Descripción de la Plataforma" (es) / "2.2. Platform Description" (en).
     b) Do NOT dump the raw English string `Physical Data Center & Facilities` under the heading.
     c) Instead, synthesize a rich, cohesive introductory paragraph from `domain_introduction.introduction_paragraph` and `domain_introduction.included_components` that explains the evaluated technical domain and its concrete physical/digital footprint.
     d) Auto-fit the Regulatory/Methodological Framework table both to the window width (100% pct: `w:tblW w:type="pct" w:w="5000"`) and to its cell contents (`w:tblLayout w:type="autofit"`).

2. ELIMINATION OF SECTION 2.3 ("TRES RESULTADOS EJECUTIVOS DEL DIAGNÓSTICO")
   - Current section: "2.3. Tres Resultados Ejecutivos del Diagnóstico" with 3 generic bullet points ("1. Identificación y Cuantificación de Brechas...", "2. Evaluación de Obsolescencia...", "3. Priorización Racional de Inversiones...").
   - User feedback: "Por otro lado el punto 2.3 '2.3. Tres Resultados Ejecutivos del Diagnóstico' directamente lo eliminaba ya que es mentira, es decir, nosotros solo hemos hecho una entrevista al cliente nada más."
   - Architectural Need: Completely remove Section 2.3 and its bullet points from `payload_to_ast.py` and `locales.json`.

3. UNIFORM EXECUTIVE SLATE COLOR (#2E404D) VS PURE BLACK
   - User feedback: "Otra cosa más a veces el texto veo que está escrito en un color '#2E404D' y otros en negro directamente esto hace que no se vea bien, el negro debería ser sustituido por '#2E404D' siempre para dar seriedad al documento"
   - Architectural Need: In `docx_compiler.py` and `add_markdown_runs()`, replace the default pure black `#000000` with the executive slate color `#2E404D` (RGB: 46, 64, 77) across all regular paragraphs, list bullets, and table cells.

4. UNIFORM TYPOGRAPHIC SCALE (10.5 PT) ACROSS SECTIONS 2.4 AND 2.5
   - Current state: In `ast_appendices_builder.py`, `build_cmmi_methodology_and_capabilities` hardcodes `font_size=9.0` for intro paragraphs and `font_size=8.5` for list bullets!
   - User feedback: "incluso no se si en el punto 2.4 la misma letra es decir empieza con 'La madurez se califica en una escala analítica del 1,00 al 5,00, donde cada nivel determina un estadio de control:' que tiene un tamaño y luego nivel 1, 2, 3, 4, 5 con otra todos debería tener el mismo tamaño, quizás el mismo 10,5 que tenemos en los otros párrafos, y todo esto último que te he dicho de los colores y tamaños también aplica en el punto 2.5."
   - Architectural Need: Standardize all intro paragraphs and bullet points in CMMI 5-level scale and evaluated capabilities allocation to uniform 10.5 pt font size and `#2E404D` text color.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless design using clean architectural patterns.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The architecture must scale to ANY company in the world: any tier, vertical, currency, or language.
   - Zero hardcoded client names, zero fixed strings in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, class names, method signatures, variables, docstrings, and comments must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 031) in Markdown:
1. Detailed design for Section 2.2: streamlined title, contextual domain narrative synthesis (using `domain_introduction` data and components), and OpenXML table auto-fit specification.
2. Complete removal plan for Section 2.3 ("Tres Resultados Ejecutivos del Diagnóstico").
3. Universal typography color governance: replacing default pure black `#000000` with `#2E404D` (RGB: 46, 64, 77) in `docx_compiler.py`.
4. Typographic scale standardization: normalizing CMMI scale and capabilities paragraphs to 10.5 pt in `ast_appendices_builder.py`.
5. Production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 031 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_031_CHAPTER_2_REFINEMENTS_AND_TYPOGRAPHY_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 031 ARCHITECTURAL PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
