#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 044 Pure AS-IS Executive Summary Alignment & Definitive Diagnostic Synthesis.

Addresses the user's acute observation:
"esto es un documento de AS-IS, no hablamos de TO-BE ni de TO-DO así que el último párrafo hay que cambiarlo no?
--> Para resolver estas limitaciones, es prioritario acometer el plan de modernización... elevar la madurez hasta el objetivo de 4,1 sobre 5,0.
¿Qué ponemos? ¿Qué más cosas de valor tenemos que añadir, o quizás explicar algunas mejor?
Esto es un resumen ejecutivo, se supone que en esta página leyéndola te enteras de todo no?"
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
Role: Chief Enterprise Architect & Executive Editorial Fellow (McKinsey Global Managing Partner / Gartner Senior Research VP / MIT Systems Architect).

CONTEXT & USER CRITIQUE (DEEP METHODOLOGICAL INSIGHT):
The user delivered a brilliant, fundamental critique of the Executive Summary closing paragraph:
"Esto ya me gusta mucho más, pero vamos por partes: esto es un documento de AS-IS, no hablamos de TO-BE ni de TO-DO, así que el último párrafo hay que cambiarlo ¿no?
--> 'Para resolver estas limitaciones, es prioritario acometer el plan de modernización detallado en este informe en un plazo de 12 a 24 meses, focalizado en la modernización de la plataforma... elevar la madurez hasta el objetivo de 4,1 sobre 5,0.'
¿Qué ponemos? ¿Qué más cosas de valor tenemos que añadir, o quizás explicar algunas mejor? Esto es un resumen ejecutivo, se supone que en esta página leyéndola te enteras de todo ¿no?"

CORE ARCHITECTURAL ANALYSIS:
1. Strict Boundary of Current-State (AS-IS) Assessments:
   - In tier-1 strategy consulting (McKinsey, BCG, Gartner, Big 4), the deliverables are cleanly phased:
     * Phase 1: AS-IS Technical Assessment (Current State Diagnostic, Vulnerability Inventory, Actuarial Risk Baseline).
     * Phase 2: TO-BE Target Architecture (Target Operating Model, Future Maturity Goal).
     * Phase 3: TO-DO Implementation Roadmap (Phased Migration Plan, Work Breakdown, Program Scheduling).
   - In an AS-IS diagnostic report, promising a "12 to 24 month modernization roadmap" or setting future "target scores like 4.1/5.0" is a methodological contamination! It jumps into Phase 2/3 before the executive committee has even ratified the diagnostic truth of Phase 1.

2. What Belongs in Paragraph 4 of a Pure AS-IS Executive Summary?
   - Instead of premature TO-BE planning, Paragraph 4 must deliver the **Definitive AS-IS Diagnostic Verdict & Cost of Inaction (Inercia del Statu Quo)**:
     * Apparent vs. Real Stability: Explaining that while daily operations appear functional, this stability is fragile and subsidized by manual heroics and unhedged technical debt.
     * Compounding Technical Debt & Inaction Trajectory: What happens if leadership maintains the status quo? (Accumulation of end-of-support hardware, increasing frequency of unplanned downtime, higher recovery friction, and escalating maintenance overhead).
     * Systemic Organizational Bottleneck: Pinpointing whether the primary constraint is technical debt, operational process gaps, or governance silos.
     * The Executive Call to Consciousness: Delivering the clear, sobering verdict that this domain requires structural remediation to achieve acceptable baseline reliability.

3. Maximizing Executive Self-Containment (The 1-Page Comprehensive Briefing):
   - The user states: "Esto es un resumen ejecutivo, se supone que en esta página leyéndola te enteras de todo ¿no?"
   - How can this single executive page be engineered so that a CEO, CFO, or Board Director who reads ONLY this page grasps 100% of the domain's reality:
     * Component A: Visual Scorecard (Score, Band, Annualized Loss Expectancy ALE P50).
     * Component B Headline: Executive Diagnostic Statement (The single overarching finding).
     * Component B Prose (The 4 Natural Chapters of Truth):
       1. The Baseline Posture & Domain Criticality: What is this domain, what mission does it fulfill for the business, and what is its current maturity rating?
       2. The Three Concrete Physical Vulnerabilities: What are the exact structural failure points discovered during inspection (explained in plain, clear, professional language)?
       3. The Financial & Operational Reality: What is the hourly cost of downtime, the annual expected loss (ALE), and the realistic worst-case scenario (P90) with capped recovery hours?
       4. The Diagnostic Verdict & Cost of Inaction: What is the definitive conclusion of the current state, and why is maintaining the status quo an unacceptable enterprise risk?
     * Component C: The Diagnostic Triad Table (Operational Strength, Critical Gap, Systemic Bottleneck).

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTIPATTERNS, ZERO DEFECTS.
2. ZERO HARDCODING (Scales to any enterprise 50M€ to 50B€, any vertical, any currency, any locale).
3. 100% TECHNICAL ENGLISH CODEBASE (Zero Spanish in Python code).
4. SPLIT-BRAIN ERADICATION (10-Tower Symmetry).
5. OPENXML EDITORIAL PERFECTION.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 044) in Markdown:
1. Pure AS-IS Editorial Principles: Define the exact boundary rules that eliminate TO-BE / TO-DO contamination while maximizing executive diagnostic value.
2. Re-architected Paragraph 4 (The Diagnostic Verdict & Cost of Inaction):
   - Design the narrative structure and dynamic variables.
   - Craft the bilingual templates for `engine_config/locales.json` in plain, human, professional Spanish and English.
   - Show how it adapts across all 10 capability towers (T1..T10) based on their specific risk posture.
3. Review of the Entire Executive Summary Flow: Verify how Components A, B, and C combine to deliver the ultimate 1-page self-contained briefing.
4. Concrete, production-ready Python code modifications in 100% Technical English.
"""

    print(f"Requesting RFC 044 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_044_PURE_ASIS_EXECUTIVE_ALIGNMENT_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 044 PURE AS-IS EXECUTIVE SUMMARY ALIGNMENT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
