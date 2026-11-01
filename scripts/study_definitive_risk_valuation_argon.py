#!/usr/bin/env python3
"""Definitive Risk Valuation & Modeling Study by gemini-4-argon to Permanently Settle Enterprise Risk Architecture."""

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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = """
Role: Global Head of Risk & Industrial Practice (McKinsey/Oliver Wyman), Open FAIR Master Fellow, and Lead Plant Reliability Director.

CONTEXT & USER'S CRUCIAL DIRECTIVE:
The user has challenged the team with profound, razor-sharp insights that demolish standard consulting clichés:
1. "El coste que está en el índice vs en los riesgos no coincide y me preocupa muchísimo porque se supone que no hay split-brain."
2. "Parece que tenemos como muchos riesgos pero parecen el mismo, en realidad tampoco tengo claro si el riesgo se acumula en estos casos. Se supone que el mismo riesgo no debería acumularse. Hay que pensar bien los riesgos cómo se cuentan porque es clave."
3. "Cada empresa tiene niveles de madurez diferentes y sus riesgos son distintos, ¿no?"
4. "Pero es que esto tampoco tiene que ser así: 'Con CMMI 1.7, no tienes repuestos en stock, no hay mantenimiento predictivo y el contrato con el fabricante es estándar (reacción en 72 horas). Una avería en agosto para la fábrica durante días.' Esa afirmación NO tiene que ser correcta. Una fábrica con CMMI 1.7 en climatización del CPD puede tener un contrato Gold 24/7 de 2-4 horas con Carrier/Schneider, técnicos experimentados y piezas en stock, y saca un 1.7 simplemente porque no tiene sondas IoT o procesos formalizados en una herramienta digital."

THE MANDATE:
Deliver an authoritative, deep, and definitive study that settles FOREVER how the Assessment Engine must value, model, and present risks for any enterprise in the world (from mid-market to Fortune 10, across all towers T1-T6 and verticals).

YOUR STUDY MUST COVER:
1. GROUND-TRUTH INDUSTRIAL REALITY VS CONSULTING FANTASY:
   - Establish what real-world downtime (MTRS) and frequencies actually look like in an enterprise plant (e.g. Molins cement plant or equivalent industrial facility).
   - Why downtime is measured in 1.5 to 4.0 hours (emergency reset, temporary cooldown, manual bypass, dispatch queues), NOT in weeks or arbitrary 14-hour blocks.
   - Clarify the true role of CMMI: process formalization and digital telemetry, NOT basic human or contractual competence.

2. RISK ACCUMULATION, INDEPENDENCE & DEDUPLICATION (HOW TO COUNT RISKS):
   - How to structure the catalog so risks do NOT falsely accumulate or double-count the same outage.
   - Define the definitive model: Should Chapter 4 present:
     * Consolidated Operational Failure Scenarios (e.g. 3 to 4 major failure events per tower), with the granular audit findings embedded inside as root causes / contributing factors?
     * How are SLE (Single Loss Expectancy), LEF (annual frequency), and ALE (annualized expected loss) calculated and attributed without double-counting?

3. THE GROUNDED COUPLING BETWEEN CMMI MATURITY AND OPEN FAIR:
   - How CMMI legitimately modulates risk WITHOUT ivory-tower magic formulas.
   - How moving from AS-IS maturity (e.g. 2.61) to Target maturity (e.g. 4.00) reduces risk and produces a real, defendable ROI and Payback for the Roadmap (Chapter 5).

4. PERMANENT ERADICATION OF SPLIT-BRAIN:
   - Exact mathematical reconciliation across Chapter 1 (Executive Summary), Chapter 4 (Risks), Chapter 5 (Roadmap ROI), and Appendix B (Actuarial Tables).
   - Single-source-of-truth invariant rules.

5. THE DEFINITIVE OPERATIONAL ACTION PLAN:
   - What exact data structure and representation do we implement in the codebase to close this topic permanently?
   - Specific numbers, formulas, and AST card layouts for the baseline deliverable.
"""

print(f"Requesting definitive risk valuation study from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: DEFINITIVE RISK VALUATION & ARCHITECTURE STUDY")
print("=" * 80)
print(response.text)
print("=" * 80)
