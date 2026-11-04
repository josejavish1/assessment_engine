#!/usr/bin/env python3
"""Adversarial Strategic Audit on Industry Benchmarks and AS-IS vs TO-BE Separation via gemini-4-argon."""

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
Role: Advisory Partner at Gartner / McKinsey, Principal Enterprise Systems Architect, and Lead Author of Multi-Tenant IT Diligence Frameworks.

CONTEXT & CRITICAL STRATEGIC INQUIRY:
The user is reviewing `Molins_202610_Tomo_1_Diagnostico_ASIS.docx` (Tomo 1: AS-IS Technical Diagnostic) and has raised two fundamental ontological and methodological doubts regarding Chapter 2:

DOUBT 1: THE FLAT UNIFORM 3.50 BENCHMARK
"Tengo serias dudas de cuando hablamos de la referencia del sector que ponemos siempre 3,5. ¿Es defendible que todas las torres tengan una referencia de sector con la misma puntuación? Eso cambia mucho..."
- In Chapter 2 (Table 2 and Radar Chart), every single technological domain (T1 to T10) currently shows an identical industry benchmark of 3.50.
- Is a uniform flat 3.50 across all 10 domains defensible to a CIO / Board, or does it smell of an amateurish, synthetic constant?
- How should a Tier-1 IT benchmarking practice structure industry benchmarks (e.g., Data Center & Facilities in heavy manufacturing is typically ~3.80 - 4.00, while OT Continuity / Plant Shopfloor is ~3.20, and Cybersecurity is ~3.40)?

DOUBT 2: DELIVERABLE SCOPE & CANNIBALIZATION (AS-IS vs TO-BE)
"Pero es que me llega hasta una segunda duda que creo que es incluso previa: ¿Es correcto poner aquí [en el Tomo 1 AS-IS] esta información [benchmark y objetivos], o es mejor en el TO-BE?"
- Tomo 1 is titled: "Tomo 1: Diagnóstico de Situación Actual (AS-IS)".
- Tomo 2 is titled: "Tomo 2: Arquitectura Objetivo y Plan de Transformación (TO-BE / Roadmap)".
- Currently in Tomo 1 Chapter 2, we show:
  * AS-IS Score
  * Objetivo H1 (Forward-looking Transformation Target)
  * Gap to Target
  * Industry Benchmark
  * Radar Chart with AS-IS vs Objetivo H1 vs Benchmark.
- Does showing "Objetivo H1" inside Tomo 1 violate separation of concerns and cannibalize Tomo 2?
- What is the exact best-practice boundary between Tomo 1 (AS-IS) and Tomo 2 (TO-BE)?

YOUR ADVERSARIAL STRATEGIC REPORT MUST DELIVER:
1. Forensic Evaluation of Doubt 1 (Flat 3.50 Benchmark):
   - Theoretical and practical critique.
   - Domain-specific benchmark profile calibration for heavy industrial / manufacturing enterprises across all 10 domains.
   - Dynamic data-binding architecture (e.g. `industry_profiles/heavy_manufacturing.json`).
2. Forensic Evaluation of Doubt 2 (AS-IS vs TO-BE Boundary):
   - What belongs strictly in Tomo 1 (AS-IS) vs Tomo 2 (TO-BE)?
   - Should "Objetivo H1" be removed from Tomo 1?
   - Should an external industry benchmark remain in Tomo 1 as a diagnostic yardstick, or should Tomo 1 only show AS-IS?
3. Actionable Architectural Recommendations:
   - Specific recommendations for Table 2, Radar Chart, and Chapter 2 narrative in Tomo 1.
   - Specific recommendations for what to reserve for Tomo 2.
"""

    print(f"Consulting {model_name} on benchmark defensibility and AS-IS vs TO-BE scope...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_BENCHMARK_AND_ASIS_TOBE_STRATEGY.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated strategic report: {out_file}")


if __name__ == "__main__":
    main()
