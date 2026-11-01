#!/usr/bin/env python3
"""Adversarial Audit & Deep Diagnosis by gemini-4-argon on Risk Ontology, Actuarial Calibration, and Mini-Infographics."""

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
Role: Chief Risk Officer (Open FAIR Fellow), Senior Partner (Industrial Infrastructure & Board Advisory), and Principal Document Typography Architect.

CONTEXT & PROBLEM STATEMENT FROM THE CLIENT/USER:
The user reviewed the generated risks and provided three critical, devastating, and highly accurate critiques:
1. "Estéticamente los riesgos se ven fatal y no se entienden bien tal y como están. Quizás cada riesgo debería ser mucho más como una mini-infografía para que se entienda mejor."
   - The current text blocks with bullets look like dry walls of text. The user wants each risk presented as a high-impact, beautifully designed "mini-infographic card" that an executive or Board member can digest at a single glance.
2. "Me cuesta muchísimo creer las frecuencias y las horas que has estimado, creo que están bastante distorsionados de la realidad."
   - The generated metrics had absurd values like TEF = 4.0 events/year (4 times a year!) and 14 hours of total manufacturing plant stoppage per event.
   - If a real manufacturing enterprise (like Molins, with 15,600 €/hr downtime) suffered 4 blackouts a year lasting 14 hours each (56 hours of stoppage = 873,600 € real losses every single year), the plant would be bankrupt or the CIO fired immediately.
   - The numbers are uncalibrated and destroy consulting credibility in front of any CFO.
3. "Veo que muchos riesgos quizás no son riesgos. Por ejemplo 'Gestión de Densidad Térmica, Puntos Calientes y Flujo de Aire' en realidad solo es un riesgo si se rompen los aires acondicionados, y quizás tampoco lo sea tanto si solo es un rack y no tiene mucha carga. Siguiendo esta lógica, muchos de los riesgos tienen una lógica parecida."
   - The user correctly points out an ontological failure in risk definition: Confusing a VULNERABILITY or ENVIRONMENTAL CONDITION (missing blanking panels, open cable grommets, lack of hot/cold aisle containment, low thermal load in a single rack) with an actual LOSS EVENT.
   - An open hole is a vulnerability, NOT a loss event. It only becomes a loss event if primary cooling fails AND recirculating thermal runaway exceeds ASHRAE limits AND protective thermal trip kills production.

YOUR TASK:
Provide an exhaustive, unvarnished, deep actuarial and architectural diagnosis answering:
1. RISK ONTOLOGY AUDIT:
   - Analyze the 14 current risks. Explain the precise difference between a Vulnerability/Condition and a True Open FAIR Loss Event Scenario.
   - How should scenarios like thermal management, electrical capacity, and monitoring be properly defined so they represent real, conditional business loss events rather than alarmist static vulnerabilities?
2. EMPIRICAL ACTUARIAL CALIBRATION (REAL-WORLD VS FANTASY):
   - What are realistic, defensible statistical frequencies (TEF) and recovery times (MTTR) for industrial/enterprise on-premise IT infrastructure?
   - Differentiate between:
     * Full catastrophic plant blackout (very low frequency: e.g. 0.05 - 0.2 ev/year, 4-8 hours).
     * Partial redundancy loss / degraded mode (moderate frequency: e.g. 0.3 - 0.8 ev/year, 1-3 hours, lower hourly impact).
     * Maintenance friction / operational waste (annualized operational drag).
   - How must the Open FAIR model calibrate TEF, MTTR, and Loss Magnitude so that the numbers are 100% defendable in front of a skeptical CFO?
3. "MINI-INFOGRAPHIC" VISUAL DESIGN ARCHITECTURE:
   - Propose the exact visual layout for a "Mini-Infographic Risk Card" in Microsoft Word (.docx) and PDF:
     * Container framing (callout border, accent header).
     * Visual KPI Badge Row / Tiles (Frecuencia Anual | MTTR | Coste Horario | ALE Anual | Severidad).
     * Two-column or structured 3-part layout:
       1) Escenario Condicional de Riesgo (Qué tiene que pasar para que ocurra la pérdida).
       2) Mecanismo de Impacto Operativo (Efecto real en báscula, ERP, producción).
       3) Fórmula Actuarial y Parámetros Auditables.
4. ROADMAP DE IMPLEMENTACIÓN:
   - Provide a clear, actionable plan to reformulate the risk catalog, recalibrate the numbers to rock-solid real-world physics, and implement the mini-infographic renderer without breaking any tests or mandates (100% Technical English codebase, zero hardcoding).
"""

print(f"Requesting deep risk ontology and infographic audit from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: DEEP DIAGNOSIS ON RISK ONTOLOGY & MINI-INFOGRAPHICS")
print("=" * 80)
print(response.text)
print("=" * 80)
