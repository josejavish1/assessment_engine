#!/usr/bin/env python3
"""Argon-4 Deep Architectural Audit & Plan: Chapter 3 Maturity Diagnostic Refinements (RFC 037)."""

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

CONTEXT & USER CRITIQUE FOR CHAPTER 3 (TECHNOLOGICAL DIAGNOSIS & MATURITY DASHBOARD):
The user reviewed Chapter 3 of the deliverables and provided four specific editorial and structural instructions:

1. Introductory Paragraph:
   - "el primer párrafo se puede decir una introducción mucho más con un poquito más de prosa fácil de entender igual de cortita pero creo que se puede decir más sencillo"
   - Craft a concise, clear, and direct executive introductory paragraph in accessible prose that explains the purpose of the technical diagnosis without unnecessary consulting jargon.

2. Structural Unification of 3.1 and 3.2 & Friendly Score Explanation:
   - "respecto al punto 3.1 y 3.2 yo creo que ambos lo integraría dentro del punto 3 general y respecto al punto 3.1 creo que donde pone lectura de resiliencia de la plataforma gobernanza estándar creo que ahí habría que eliminarlo y contar o explicar brevemente qué significa la puntuación del asis no oye por qué significa de forma global esa nota o y explicarlo de una forma sencilla y amigable"
   - Eliminate redundant subheadings 3.1 ("Cuadro de Mando de Madurez Global de la Torre") and 3.2 ("Matriz de Diagnóstico y Desempeño"), integrating the global score snapshot and the pillar breakdown table directly under the main Chapter 3 heading.
   - Completely eradicate the robotic string "Lectura de Resiliencia de la plataforma: Gobernanza estándar".
   - Replace it with a clear, friendly, and pedagogical paragraph explaining what the global score (e.g. 2.61 / 2.46 out of 5.00) means in plain operational terms: what works well today (stability in daily operations) and what the gap represents (manual interventions, lack of automation and real-time telemetry).

3. Elimination of the "Pillar" Literal Name Bug:
   - "luego en lo que es el 3.2 en la columna de Pilar capacidades tecnológicas evaluadas aparece solo Pilar pero no aparece el nombre del Pilar"
   - Root Cause Discovered: In `payload_to_ast.py` and `in_memory_asis_compiler.py`, the code searched for `p.get("pillar_name")` and `p.get("pillar_id")` with double 'l', while raw payloads often store Spanish-keyed dictionaries with `pilar_name` and `pilar_id`. As a result, both lookups failed and defaulted to the string `"Pillar"`.
   - Architectural Fix: Ensure `TaxonomyResolver` and all pillar extractors gracefully resolve both `pillar_id`/`pilar_name` and `pilar_id`/`pilar_name`, mapping through `taxonomy_multilingual.json` to guarantee canonical, beautifully accented human-readable pillar titles in every table.

4. Table 3.3.2 / Score Justification Table:
   - "la columna de pilar pone pilar y no explica el por qué y esa tabla la del 3.3.2 la tabla también pone en la columna primera Pilar y debería poner el nombre del Pilar y esa tabla debería estar auto ajustada a la ventana y autoajustada al contenido para que se pueda ver bien."
   - Fix the pillar name resolution in `derive_in_memory_maturity_matrix` and the CSV loader (`04_matriz_madurez.csv`).
   - Set `autofit=True` on the table node so it automatically expands to 100% table width with proper cell margins and auto-fits contents cleanly.
   - Simplify any overly dense technical debt prose into plain, clear language.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless mathematical and architectural design.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - Works across all 10 towers (T1..T10), all tiers, all languages, and all verticals.
   - Zero hardcoded client names or strings in Python logic.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, and docstrings must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 037) in Markdown:
1. Exact refactoring of `payload_to_ast.py` to unify Chapter 3, remove subheadings 3.1/3.2, eradicate the robotic resilience line, and inject the friendly score explanation.
2. Robust resolution of pillar names across `payload_to_ast.py` and `in_memory_asis_compiler.py`.
3. OpenXML table autofit configuration (`autofit=True` and proportional widths).
4. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 037 Chapter 3 Maturity Diagnostic Refinements from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_037_CHAPTER_3_MATURITY_DIAGNOSTIC_REFINEMENTS_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 037 CHAPTER 3 REFINEMENTS")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
