#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 052 Chapter 3 & 4 Architectural Overhaul, Polymorphic Rotation, Plain-Language Risk Cards & Pure AS-IS Alignment.

Addresses the user's comprehensive feedback:
1. Chapter 3 Polymorphic Rotation: Eradicate identical intro and scorecard prose across towers; eliminate denominator stutter (e.g. '2,46 / 5,00 sobre 5,00').
2. Chapter 4 Executive Title Simplification: Replace academic titles with clear, C-level executive headers.
3. Section 4.1 Domain Contextualization: Explain how the hourly stoppage rate (13,061.29 €/h) uniquely manifests in each technical tower.
4. Section 4.2 Heatmap Legend Table: Provide an explicit decoding table below the 5x5 heatmap so the client knows what each badge (e.g. RVS01) means.
5. Section 4.3 TO-BE Roadmaps Purged: Eradicate 30-90 / 90-180 day project roadmaps from the AS-IS deliverable, transforming 4.3 into a pure AS-IS Risk Concentration Profile.
6. Section 4.4 Plain-Language Risk Cards: Clean card titles, replace cryptic cascade jargon with 'Propagación de Fallo', and provide intuitive, human-readable actuarial breakdowns.
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
Role: Chief Enterprise Architect & Executive Editorial Fellow (Gartner VP / McKinsey Senior Partner / Google Core Infrastructure).

USER CRITIQUE & SYSTEMIC AUDIT DIRECTIVES:
The user delivered a comprehensive critique of Chapter 3 and Chapter 4:

1. Chapter 3 Monolithic Boilerplate & Denominator Stutter:
   - The user noticed that Chapter 3's introduction and the paragraph below the scorecard are 100% identical in both Tower 1 and Tower 2:
     "El presente capítulo ejecuta el diagnóstico técnico de la plataforma tecnológica en Molins, evaluando la infraestructura de {tower_name} bajo tres ejes analíticos... La plataforma alcanza una puntuación global de 2,46 / 5,00 sobre 5,00. Esta valoración refleja una infraestructura funcional para dar soporte a la operativa diaria de Molins. No obstante, persisten dependencias operativas y puntos de fricción técnica que limitan la escalabilidad del dominio y elevan el esfuerzo de mantenimiento de los equipos."
   - Requirement:
     a) Eliminate the denominator stutter: render clean "2,46 sobre 5,0 (Nivel 2 - Repetible)" instead of "2,46 / 5,00 sobre 5,00".
     b) Extend the 3-Archetype Polymorphic Rotation to Chapter 3 (INFRASTRUCTURE_PHYSICAL, COMPUTE_PLATFORMS, SECURITY_GOVERNANCE) so that T1, T2, and T3 have completely distinct introductory framings and scorecard commentary.

2. Chapter 4 Simplified Titles & Subtitles:
   - User critique: The titles are overly academic and awkward for an enterprise client.
   - Requirement: Simplify all titles in Chapter 4:
     * Chapter 4: "4. Evaluación Económica de Riesgos de Infraestructura" / "4. Infrastructure Economic Risk Evaluation"
     * 4.1: "4.1. Coste Estimado por Hora de Inactividad" / "4.1. Estimated Hourly Downtime Cost"
     * 4.2: "4.2. Matriz de Priorización de Riesgos y Mapa de Calor" / "4.2. Risk Prioritization Matrix & Heatmap"
     * 4.3: "4.3. Concentración y Distribución de Riesgos del Dominio" / "4.3. Domain Risk Concentration Profile"
     * 4.4: "4.4. Fichas de Riesgos Técnicos Cuantificados" / "4.4. Quantified Technical Risk Cards"

3. Section 4.1 Domain Contextualization:
   - User critique: Section 4.1 explains the 13,061.29 €/h rate identically across all towers.
   - Requirement: While the authoritative rate is enterprise-wide, the narrative in Section 4.1 must explain how downtime in THAT specific domain manifests into operational paralysis (e.g. kiln/bagging stoppage in T1; SAP/MES transactional paralysis in T2).

4. Section 4.2 Heatmap Legend Table:
   - User critique: The 5x5 heatmap shows codes like RVS01, RVS02 without an explicit legend below it explaining what they mean.
   - Requirement: Add a clean 4-column legend table directly beneath the heatmap:
     [Código | Capacidad y Riesgo Técnico Identificado | Exposición Anual (ALE) | Criticidad]

5. Section 4.3 Pure AS-IS Risk Concentration Profile (Zero TO-BE Roadmaps):
   - User critique: Section 4.3 mentions "quick wins" and "30 a 90 días / 90 a 180 días", which violates the AS-IS boundary by drifting into TO-BE project implementation plans.
   - Requirement: Completely purge all 30-90 day and 90-180 day implementation schedules from Section 4.3. Structure Section 4.3 strictly as an AS-IS financial tier concentration profile:
     - Tier 1 (Riesgos Críticos / Alto Impacto): Total ALE, % of exposure, count.
     - Tier 2 (Riesgos Moderados): Total ALE, % of exposure, count.
     - Tier 3 (Riesgos Residuales / Menores): Total ALE, % of exposure, count.
     Zero prescriptive implementation roadmaps! 100% pure AS-IS actuarial inventory.

6. Section 4.4 Plain-Language Risk Cards:
   - User critique: Risk titles are cluttered (appending pillar name in the title box), "efecto cascada" is cryptic jargon, and the actuarial math breakdown should be explained in plain, accessible language.
   - Requirement:
     a) Title cell: Clean "[ID] Title" without appending pillar name.
     b) Replace "Efecto Cascada (x1.5)" with "Propagación de Fallo: Alta (x1.5)" or "Impacto en Otros Sistemas: Alto".
     c) Replace cryptic math "SLE = MTTR x Rate | ALE = SLE x LEF" with plain, readable executive bullets:
        "• Impacto por Incidencia (SLE): X € (estimado para Y horas de recuperación a Z €/h de afectación operativa)."
        "• Exposición Anualizada (ALE): W €/año (calculada para una frecuencia estimada de 1 fallo cada N años)."

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale in `locales.json`).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 052) in Markdown:
1. Specify the bilingual dictionary updates in `engine_config/locales.json`.
2. Detail the exact Python implementation in `payload_to_ast.py`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 052 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_052_CHAPTER_3_AND_4_PLAIN_LANGUAGE_AND_ASIS_ALIGNMENT_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 052 CHAPTER 3 & 4 OVERHAUL")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
