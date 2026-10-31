#!/usr/bin/env python3
"""Exhaustive Adversarial Code and Content Audit via gemini-4-argon (100% Technical English)."""

from __future__ import annotations

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


class SectionValueAudit(BaseModel):
    section_name: str = Field(..., description="Name of the chapter or section")
    earns_its_place: bool = Field(..., description="True if content provides high executive/technical value")
    zero_redundancy: bool = Field(..., description="True if no duplicate information from other sections")
    narrative_coherence: str = Field(..., description="Evaluation of narrative flow and logical connection")
    critique_or_optimization: str = Field(..., description="Actionable critique to maximize signal-to-noise ratio")


class CodeAuditFinding(BaseModel):
    file_path: str = Field(..., description="File path where violation occurs")
    line_number: int = Field(..., description="Line number")
    category: str = Field(..., description="BUG, HARDCODING, SPANISH_IN_CODE, or NON_UNIVERSAL")
    severity: str = Field(..., description="CRITICAL, MAJOR, or MINOR")
    technical_critique: str = Field(..., description="Deep forensic explanation")
    mandatory_fix: str = Field(..., description="Concrete code or configuration change required")


class FullSystemArgonAudit(BaseModel):
    verdict: str = Field(..., description="Must be 'PASS' or 'FAIL'")
    zero_bugs_or_antipatterns: bool = Field(..., description="True if code is completely free of bugs")
    zero_hardcoding_verified: bool = Field(..., description="True if universal across all company tiers and verticals")
    universal_tier1_enterprise_ready: bool = Field(..., description="True if ready for mid-market to Fortune 10 across any vertical")
    strict_english_only_verified: bool = Field(..., description="True if Python source code contains zero Spanish words")
    content_value_and_narrative_sound: bool = Field(..., description="True if every section earns its place with zero fluff")
    section_audits: List[SectionValueAudit] = Field(..., description="Section-by-section value audit")
    findings: List[CodeAuditFinding] = Field(default_factory=list, description="Code audit findings, empty on PASS")
    forensic_executive_summary: str = Field(..., description="Comprehensive forensic synthesis")


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    payload_to_ast_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
    ast_appendices_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/ast_appendices_builder.py").read_text(encoding="utf-8")
    locales_code = (REPO_ROOT / "engine_config/locales.json").read_text(encoding="utf-8")

    diff_cmd = ["git", "diff", "ac8aae0", "HEAD", "--", "src/", "engine_config/"]
    diff_text = subprocess.run(diff_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

    prompt = f"""
Role: Chief Technology Officer, Principal Compiler Architect & Senior McKinsey Strategy Partner.

OBJECTIVE:
Perform an exhaustive, adversarial, dual-track audit of the Assessment Engine codebase and generated deliverable structure:
Track 1: Architectural Code Quality, Bugs, Anti-Patterns, Universal Zero-Hardcoding, and 100% Strict English Codebase.
Track 2: Section-by-Section Value Audit: Does every single page and section earn its place? Is there any fluff, repetition, or broken narrative thread?

USER'S MANDATES & STRATEGIC PRINCIPLES:
1. CODE HYGIENE & PURITY:
   - Zero Spanish words anywhere in Python source code (identifiers, comments, docstrings, exceptions).
   - Zero hardcoding: Must serve ANY company in the world (from a mid-market firm to a Fortune 10 global conglomerate), in any industry vertical (Banking, Energy, Healthcare, Tech, Manufacturing, Retail), in any language, and using any ISO 4217 currency.
   - Zero magic constants (no unscaled monetary thresholds, no fixed capex, no fixed ratios).
   - Fail-fast enforcement: no silent exception swallowing, full type safety.
2. CONTENT VALUE & NARRATIVE FLOW (EVERY SPACE MUST EARN ITS PLACE):
   - Evaluate the narrative thread across all chapters:
     * Cover & Table of Contents (Pages 1-2)
     * Chapter 1: Executive Summary & Financial Exposure (Page 3)
     * Chapter 2: Objective, Scope, Factory Perimeter, Frameworks, 3 Outcomes, 3 Phases, CMMI Scale, Pillar Weights (Pages 4-5)
     * Chapter 3: Technological Diagnosis, Radar Chart, Scorecard, Pillar Table, Cross-Cutting Debt (Pages 6-9)
     * Chapter 4: FAIR Quantitative Risk Heatmap, RoRE Value Hexagon, Risk Portfolios, Detailed Finding Cards (Pages 10-17)
     * Chapter 5: Conclusions, Transformation Paradigm, Next Steps, Multi-Horizon Stochastic Inaction Table (Page 18)
     * Appendix A: Chain of Custody & Evidence Registry (Page 19)
     * Appendix B: Quantitative Risk Modeling Methodology (Open FAIR, TEF/LM Scales, Monte Carlo) (Pages 20-21)
     * Appendix C: Abbreviations Glossary & Legal Disclaimer (Page 22)
   - Ensure ZERO duplicate information between Chapter 2, Chapter 4, and Appendices.
   - Ensure high executive signal-to-noise ratio.

FULL SOURCE: payload_to_ast.py ({len(payload_to_ast_code)} chars):
```python
{payload_to_ast_code}
```

FULL SOURCE: ast_appendices_builder.py ({len(ast_appendices_code)} chars):
```python
{ast_appendices_code}
```

RECENT CHANGESET (ac8aae0..HEAD):
```diff
{diff_text}
```

SAMPLE LOCALIZATION EXCERPT (locales.json keys related to recent chapters):
```json
{locales_code[:15000]}
```

Return your unvarnished audit conforming strictly to the FullSystemArgonAudit Pydantic schema.
"""

    print(f"Executing comprehensive dual-track audit with {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=FullSystemArgonAudit,
        ),
    )

    report = FullSystemArgonAudit.model_validate_json(response.text)

    print("\n" + "=" * 80)
    print("AUDITORÍA DUAL FORENSE: GEMINI-4-ARGON (CÓDIGO Y NARRATIVA CONSULTORA)")
    print("=" * 80)
    print(f"VEREDICTO FINAL:                      {report.verdict}")
    print(f"Zero Bugs / Antipatrones:             {report.zero_bugs_or_antipatterns}")
    print(f"Zero Hardcoding Verificado:           {report.zero_hardcoding_verified}")
    print(f"Universal Tier-1 Enterprise:          {report.universal_tier1_enterprise_ready}")
    print(f"100% Strict English Codebase:         {report.strict_english_only_verified}")
    print(f"Contenido de Alto Valor / Hilo Claro: {report.content_value_and_narrative_sound}")
    print(f"Total de Hallazgos en Código:         {len(report.findings)}")
    print("-" * 80)
    print("RESUMEN EJECUTIVO FORENSE:")
    print(report.forensic_executive_summary)
    print("-" * 80)
    print("EVALUACIÓN SECCIÓN A SECCIÓN (CADA ESPACIO GANA SU LUGAR):")
    for s in report.section_audits:
        status = "GANA SU LUGAR" if s.earns_its_place else "REVISAR VALOR"
        dedup = "SIN DUPLICIDAD" if s.zero_redundancy else "HAY REDUNDANCIA"
        print(f"• [{s.section_name}] -> {status} | {dedup}")
        print(f"    Coherencia: {s.narrative_coherence}")
        print(f"    Optimización: {s.critique_or_optimization}")
        print()

    if report.findings:
        print("-" * 80)
        print("HALLAZGOS DETALLADOS EN CÓDIGO:")
        for idx, f in enumerate(report.findings, start=1):
            print(f"[{idx}] {f.file_path}:{f.line_number} [{f.category}] (Severity: {f.severity})")
            print(f"    Critique: {f.technical_critique}")
            print(f"    Required Fix: {f.mandatory_fix}")
            print()
    else:
        print("-" * 80)
        print("CERTIFICACIÓN DE CÓDIGO: Cero defectos encontrados. El código cumple al 100% con los mandatos.")

    print("=" * 80)


if __name__ == "__main__":
    main()
