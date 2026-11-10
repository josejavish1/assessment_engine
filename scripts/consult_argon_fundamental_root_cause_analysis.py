#!/usr/bin/env python3
"""Deep architectural root cause analysis by gemini-4-argon: Why does the engine fail to achieve Sobresaliente universally?"""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

THE USER'S DEEP FRUSTRATION & CORE QUESTION:
"No conseguimos avanzar y la verdad es que estoy bastante frustrado. Siempre me dicen nota 5,5 2,5 3,5. Nosotros tenemos que implementar algo que nos lleve a todas las Torres a nivel excelente (>8.5 / 10), pero sin hardcodear nada y no puede estar hardcodeado a esta industria. Esa nota la saca porque hay algo que no está haciendo bien o algo que no está teniendo en cuenta en el código.
Ten en cuenta que nosotros deberíamos para cualquier empresa del mundo (tienes varios ejemplos aquí como una de Brasil, otra de Reino Unido, Molins en España) de cualquier sector con cualquier tipo de madurez, deberíamos poder llegar en todas a SOBRESALIENTE EN LA PRIMERA ITERACIÓN, y no lo estamos consiguiendo.
Tiene que haber algún error de fondo. Y no sé por qué ni qué está pasando ni cómo lo podemos terminar de conseguir.
Estamos utilizando Molins como un ejemplo, pero es muy importante que no hardcodeemos nada para que salga perfecto solo para este cliente. Tienes que encontrar EL ORIGEN DEL PROBLEMA que estamos teniendo, pero que se resuelva para CUALQUIER EMPRESA DEL MUNDO. Esa es la clave."

YOUR MANDATE:
Perform a deep, systemic Root Cause Analysis (RCA) of the entire platform:
1. **WHAT IS THE DEEP ROOT CAUSE OF THE LOW GRADES (5.5, 2.5, 3.5)?**
   - Trace the exact pipeline:
     Client Answers / Transcripts -> Blueprint Synthesis -> Actuarial Calibration Engine -> Strategy Pattern Receptors -> AST Document Compiler -> Word DOCX.
   - Where does the pipeline lose quality?
   - Why do external auditors perceive the reports as a "half-authentic, half-generic consulting template"?
2. **THE 3 SYSTEMIC ROOT CAUSES IN THE ENGINE:**
   Analyze:
   - **Root Cause A (The Flawed Actuarial Attenuation / Double-Omega Compression):**
     Look at how `UniversalActuarialCalibrationEngine` attenuates risk by multiplying revenue by `omega` (0.10), then IT spend by 1.8%, then severity by 4.5%, compressing a 1.14B€ company's risk to 30.000 €! Why this makes the CFO business case collapse for ANY company on earth.
   - **Root Cause B (The Fragmented Static Catalogues vs Deep Synthesis):**
     Why is T4 mapped to `CAPITAL_INEFFICIENCY` in `taxonomy_actuarial_archetypes.json`? Why is `DORA` hardcoded in `locales.json`? Why is `Retraso_Time_to_Market` hardcoded in `PRODUCTIVITY_TOIL`?
     Why does the system rely on rigid static text templates instead of a dynamic, ontology-driven semantic synthesizer?
   - **Root Cause C (The Disconnect Between Technical Telemetry and Financial Loss Physics):**
     Why are RTOs, technical health checks, and financial figures generated in isolated silos instead of being derived from a unified Epistemic Dependency Graph?
3. **THE UNIVERSAL ARCHITECTURAL SOLUTION (ZERO HARDCODING):**
   - How must the engine be restructured so that ANY tenant (Brazil hospital, UK bank, Spain cement, German CNC, Singapore airline) achieves a genuine **Sobresaliente (>8.5 / 10)** in the first pass?
   - Provide the concrete, definitive, end-to-end design.

Respond in 100% Technical English with supreme executive authority and mathematical clarity.
"""

def main() -> None:
    print(f"Submitting Deep Root Cause Analysis to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_DEEP_SYSTEMIC_ROOT_CAUSE_ANALYSIS.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nRoot Cause Analysis written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
