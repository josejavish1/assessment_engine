#!/usr/bin/env python3
"""Comprehensive Adversarial Audit Gate across all 18 Remediation Phases via gemini-4-argon.

Evaluates the complete accumulated codebase changes from 6b62972 to HEAD against:
1. Zero Bugs, Flaws, or Antipatterns (Concurrency, Type Safety, Error Handling)
2. Zero Hardcoding (100% Dynamic, Config-Driven, No Magic Numbers)
3. Universal Global Enterprise Applicability (Any company, any vertical, mid-market to Tier-1)
4. 100% Strict English Codebase Mandate (Zero Spanish in code/comments/docstrings/schemas)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

from google.genai import types
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)


class AuditFinding(BaseModel):
    file_path: str = Field(..., description="Path to file where violation occurs")
    line_number: int = Field(..., description="Line number of violation")
    category: str = Field(..., description="Category of issue: BUG, HARDCODING, SPANISH_IN_CODE, or NON_UNIVERSAL")
    technical_critique: str = Field(..., description="Deep architectural and forensic critique")
    mandatory_fix: str = Field(..., description="Concrete code change required to resolve")


class ComprehensiveArgonReport(BaseModel):
    verdict: str = Field(..., description="Must be 'PASS' or 'FAIL'")
    zero_bugs_or_antipatterns: bool = Field(..., description="True if code is completely free of bugs")
    zero_hardcoding_verified: bool = Field(..., description="True if all thresholds/paths/locales are dynamic")
    universal_tier1_enterprise_ready: bool = Field(..., description="True if scales across any company, vertical, and locale")
    strict_english_only_verified: bool = Field(..., description="True if code contains zero Spanish words")
    findings: List[AuditFinding] = Field(default_factory=list, description="List of findings, empty on PASS")
    forensic_executive_summary: str = Field(..., description="Unvarnished forensic assessment")


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    # Extract accumulated diff of all source code files from 6b62972 to current working tree
    cmd = [
        "git",
        "diff",
        "6b62972",
        "--",
        "src/assessment_engine/",
    ]
    diff_proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    diff_text = diff_proc.stdout.strip()

    if not diff_text:
        print("ERROR: Git diff is empty. Nothing to audit.")
        sys.exit(1)

    print(f"Auditing accumulated diff ({len(diff_text)} chars) with {model_name}...")

    system_instruction = (
        "You are the Hostile Principal Systems Architect and Chief Code Auditor (Google Tier-1 / Anthropic Infrastructure grade). "
        "Your sole purpose is to perform a rigorous, uncompromising, forensic code review on the provided changes across all 18 phases. "
        "Do NOT flatter. Do NOT rubber-stamp. Do NOT assume good intentions. "
        "Every single requirement specified by the user MUST be strictly validated."
    )

    user_prompt = f"""
Actúa como Auditor Principal de Código (Google Tier-1 / Anthropic Infrastructure).
Evalúa el diff acumulado de las 18 fases de remediación de la plataforma de evaluación empresarial.

REGLAS NO NEGOCIABLES DEL USUARIO:
"Quiero que hagas una revisión completa de lo que se acaba de programar en las 18 fases y busques bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra, el español solo es el idioma que hablamos tu y yo y uno de los idiomas de la salida de los entregables."

MANDATOS OBLIGATORIOS A AUDITAR:
1. ZERO BUGS O ANTIPATRONES:
   - Concurrencia (condiciones de carrera en async/multiprocessing, serialización thread-safe).
   - Manejo de excepciones (fallo seguro fail-closed, cero silenciamiento con except Exception: pass).
   - Tipado estricto (Pydantic v2, dataclasses inmutables, Protocol ports).
2. ZERO HARDCODING:
   - Cero números mágicos sin configuración de entorno o defaults dinámicos.
   - Cero nombres de empresas hardcodeadas ("Consultora", etc.), monedas fijas o países fijos.
3. APLICABILIDAD UNIVERSAL ENTERPRISE TIER-1:
   - Diseñado para funcionar en cualquier empresa del mundo (Fortune 10 a mediana empresa).
   - Soporta cualquier vertical (Banca, Salud, Energía, Aeroespacial, etc.).
   - Soporta cualquier jurisdicción y normativa (EE.UU., UE, Brasil, Japón, Singapur, Arabia Saudí).
4. 100% INGLÉS TÉCNICO EN EL CÓDIGO (ZERO ESPAÑOL):
   - Ni una sola palabra en español en nombres de variables, funciones, clases, docstrings, comentarios en el código, excepciones, logs o claves de esquemas.
   - El español solo es admisible como datos en diccionarios de internacionalización de salida, jamás en la lógica ni en los comentarios del código.

DIFF ACUMULADO DE LAS 18 FASES:
```diff
{diff_text}
```

Devuelve el reporte forense en el esquema ComprehensiveArgonReport.
Si encuentras CUALQUIER fallo, por leve que sea, emite verdict='FAIL' y lista los hallazgos exactos.
Solo si el código es 100% impecable y cumple los 4 mandatos, emite verdict='PASS' con findings=[].
"""

    response = client.models.generate_content(
        model=model_name,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ComprehensiveArgonReport,
        ),
    )

    if not response.text:
        print("ERROR: Empty response from model.")
        sys.exit(1)

    report = ComprehensiveArgonReport.model_validate_json(response.text)

    print("\n" + "=" * 80)
    print("AUDITORÍA FORENSE COMPLETA: GEMINI-4-ARGON (18 FASES DE REMEDIACIÓN)")
    print("=" * 80)
    print(f"VEREDICTO FINAL:               {report.verdict}")
    print(f"Zero Bugs / Antipatrones:      {report.zero_bugs_or_antipatterns}")
    print(f"Zero Hardcoding Verificado:    {report.zero_hardcoding_verified}")
    print(f"Universal Tier-1 Enterprise:   {report.universal_tier1_enterprise_ready}")
    print(f"100% Strict English Codebase:  {report.strict_english_only_verified}")
    print(f"Total de Hallazgos Críticos:   {len(report.findings)}")
    print("-" * 80)
    print("RESUMEN EJECUTIVO FORENSE:")
    print(report.forensic_executive_summary)
    print("-" * 80)

    if report.findings:
        print("HALLAZGOS DETALLADOS:")
        for idx, f in enumerate(report.findings, start=1):
            print(f"[{idx}] {f.file_path}:{f.line_number} [{f.category}]")
            print(f"    Critique: {f.technical_critique}")
            print(f"    Required Fix: {f.mandatory_fix}")
            print()
    else:
        print("CERTIFICACIÓN: Cero defectos encontrados. El código cumple al 100% con los 4 mandatos.")

    print("=" * 80)

    # Save report to docs
    report_file = REPO_ROOT / "docs" / "architecture" / "ARGON_18_PHASES_GLOBAL_AUDIT.json"
    report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"Reporte persistido en: {report_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
