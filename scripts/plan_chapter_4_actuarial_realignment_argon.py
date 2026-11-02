#!/usr/bin/env python3
"""Argon-4 Master Architectural Consultation: RFC 043 End-to-End Actuarial Harmony & Chapter 4 Realignment.

Examines the entire deliverable architecture across Chapter 1, Chapter 2, and Chapter 4 to guarantee:
1. Universal Epistemic Modesty: All monetary figures, rates, and hours are framed strictly as actuarial estimates (probabilistic engineering projections under Open FAIR), never as realized accounting facts.
2. Complete Chapter 4 Overhaul:
   - Replaces redundant "Resumen Ejecutivo de Riesgo" with "4.1 Actuarial Quantification Framework & Mathematical Lineage".
   - Integrates the formal Mathematical Lineage Table (R_hourly = C_op + C_sla + C_rec) directly into Chapter 4.
   - Restructures Section 4.2 (5x5 Heatmap), Section 4.3 (Three Investment Portfolios), and Section 4.4 (Detailed Risk Cards).
   - Eliminates all hardcoded 10000.0 fallbacks inside _build_risk_mini_infographic_card.
3. 100% Technical English Codebase and Zero Hardcoding across all 10 towers.
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
Role: Chief Actuarial Systems Architect & Principal Enterprise Compiler Engineer (Google Tier-1 Core Infrastructure / Anthropic Engineering / MIT Actuarial Fellow).

CONTEXT & USER CRITIQUE:
The user reviewed the ongoing architectural overhaul and delivered a crucial strategic directive:
"y por supuesto todos los números deben ser indicados como estimados, nada de afirmaciones de que ya los tenemos, así que antes de ponerte a programar dime qué vas a hacer para corregir todo el punto 1 y lo que acabas de indicar de otros puntos... si pero antes de hacerlo quizás el capítulo 4 también tengas que rehacerlo entero."

CORE DEFECTS IN THE CURRENT CHAPTER 4 IMPLEMENTATION:
1. Redundant Second "Executive Summary" in Chapter 4:
   - Chapter 4 currently opens with an uninspired heading and a redundant text block titled "**Resumen Ejecutivo de Exposición al Riesgo (FAIR)**".
   - Chapter 1 is ALREADY the Executive Summary! Having a second "Resumen Ejecutivo" at the start of Chapter 4 creates cognitive fatigue and editorial amateurism.
   - It must be replaced by a proper engineering section: "4.1 Marco de Cuantificación Actuarial y Linaje Matemático (Open FAIR™)".

2. Missing Actuarial Lineage Table in Chapter 4:
   - The user emphasized that the CFO needs to see the exact formula and origin of the composite hourly burn rate (e.g. 11,428.60 €/h).
   - Chapter 4 is the NATURAL home for the formal Actuarial Lineage Table (R_hourly = C_op + C_sla + C_rec), showing the three additive vectors (operational velocity at risk, contractual SLA penalties, and emergency recovery labor burden).
   - This table mathematically bridges Chapter 1 (which introduces the rate) and Chapter 4 (which applies it to every risk scenario).

3. Lack of Universal Epistemic Modesty ("Todos los números deben ser indicados como estimados"):
   - Some risk cards and summary clauses currently present ALE and single loss figures as definitive facts rather than probabilistic projections.
   - All financial figures across Chapter 1 and Chapter 4 must be strictly qualified with epistemic modesty: "Pérdida Anual Esperada estimada (ALE)", "Impacto proyectado por evento (SLE)", "Valor en Riesgo estimado (VaR_90)", making it 100% clear to the CFO that these are actuarial engineering estimates modeled under Open FAIR™ and Monte Carlo simulations, not historical accounting entries.

4. Residual Hardcoded Fallbacks inside Chapter 4 Compiler Code:
   - `_build_risk_mini_infographic_card` in `payload_to_ast.py` (line 1860) contains a residual hardcoded fallback `or 10000.0` when reading the hourly rate.
   - This violates Law #2 (Zero Hardcoding) and must be eradicated, reading strictly from `fin_telemetry["authoritative_hourly_downtime_cost"]`.

5. 10-Tower Symmetry and Universal Enterprise Readiness:
   - Zero hardcoding of tenant names, application names, or numbers.
   - 100% Technical English codebase (zero Spanish in Python code).

YOUR TASK:
Synthesize a comprehensive, end-to-end Architectural Blueprint (RFC 043) in Markdown:
1. Re-architect Chapter 4 into 4 seamless, professional sections:
   - 4.1 Marco de Cuantificación Actuarial y Linaje Matemático (including the Actuarial Lineage Table).
   - 4.2 Matriz de Priorización de Riesgos y Mapa de Calor (5x5).
   - 4.3 Estructuración del Inventario de Riesgos en Tres Carteras Estratégicas de Inversión (Tier 1, Tier 2, Tier 3).
   - 4.4 Catálogo Detallado de Fichas de Riesgo Actuarial (with Bow-Tie causal model and probabilistic estimated framing).
2. Detail how Chapter 1, Chapter 2, and Chapter 4 achieve 100% mathematical and narrative harmony.
3. Show how every monetary figure and duration is epistemically qualified as an actuarial projection.
4. Provide complete bilingual templates for `engine_config/locales.json` (Spanish and English).
5. Provide concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 043 Master Architectural Blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_043_CHAPTER_4_REALIGNMENT_AND_ACTUARIAL_HARMONY_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 043 CHAPTER 4 REALIGNMENT & ACTUARIAL HARMONY")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
