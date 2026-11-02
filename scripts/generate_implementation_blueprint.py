#!/usr/bin/env python3
"""Generates the Master Implementation Blueprint by gemini-4-argon for each of the 8 individual tasks."""

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
Role: Principal Systems Architect & Master Craftsman (Clean Code, Hexagonal Architecture, ISO/IEC 29500 OpenXML Expert).

CONTEXT & USER DIRECTIVE:
The user has directed:
"Quiero que para cada tarea de forma individual incluido lo que hemos hablado, gemini-4-argon haga un análisis en profundidad de cómo resolver cada problema manteniendo el código como una obra de arte. Y una vez acabe empiece a implementarlo 1 a 1 y que cuando vaya acabando de implementar cada 1 haga el control que siempre hacemos para verificar que todo cumple."

THE 8 TASKS TO DESIGN WITH SURGICAL PERFECTION:
1. Task 1: Cover Page Hygiene & Native Bottom Footer Metadata (clean title/subtitle, remove filler, anchor metadata to section.first_page_footer).
2. Task 2: Native Word OpenXML Table of Contents with Dynamic Update (w:fldSimple / w:instrText TOC \\o "1-3" \\h \\z \\u, updateFields=true, clean fallback table).
3. Task 3: Chapter 1 (Executive Summary) AS-IS Purity & Actuarial Cross-Reference (strip premature Level 4 target unless regulatory; strip TO-BE CAPEX/ROI promises; add explicit cross-reference to Chapter 4 & Appendix A).
4. Task 4: Chapter 2 (Methodological Framework) Streamlining & Table Typography Harmonization (remove 3-phase calibration; unify tables to 9.0pt bold headers, 8.5pt regular cells, 8.0pt bold badges).
5. Task 5: Pre-Flight Actuarial CFO Audit Gate & Grounded Realism (neuro-symbolic validator enforcing 1.5-4.0h downtime floors, revenue ceilings, zero double-counting, hypothesis language; recalibrate Tower 1 baseline data to 118,500 EUR/yr).
6. Task 6: Chapter 4 (Risk Section) Mini-Infographic Card Re-Engineering (remove hexagon diagram; decongest card header; executive muted palette; eliminate threat boilerplate; replace TO-BE mitigation directive with Actuarial Derivation Formula box [SLE = MTTR x Hourly Cost + Parts]; plain language Cascade Effect; probabilistic hypothesis tone).
7. Task 7: Chapter 5 (Conclusions) Transformation into Pure AS-IS Diagnostic Synthesis (remove multi-horizon CAPEX/ROI/Payback table; build structural maturity posture summary, critical vulnerability concentration matrix, operational urgency).
8. Task 8: Appendices Cleanup & Single Technical Appendix (remove Custody Log entirely; re-index Open FAIR Methodology as the single primary Appendix A).

MANDATES FOR EVERY SINGLE TASK:
- Clean Code as a Work of Art: SRP (Single Responsibility Principle), explicit typing, immutable data structures, no god functions.
- 100% Technical English Codebase: Zero Spanish words in Python code, docstrings, comments, or schemas. Spanish is strictly localized output data in `locales.json`.
- Zero Hardcoding: Completely parameterized and universal for any enterprise (50-person to Fortune 10), any industry vertical, any currency, and any target locale (es, en, pt, fr, de, ja).
- Fail-Fast & Boundary Safety: Strict ISO/IEC 29500 OpenXML element sequence (`CT_TblPr` and `CT_TcPr`), zero division guards, no unhandled exceptions.

YOUR OUTPUT MUST PROVIDE:
For each of the 8 tasks:
A. Architectural Analysis & Problem Decomposition.
B. Exact Code Modifications (Classes, Methods, AST Nodes, OpenXML Elements).
C. Universal Localization Keys (`locales.json` schema updates).
D. Verification Oracle (Specific pytest test cases and structural assertions).
"""

print(f"Requesting Master Implementation Blueprint from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: MASTER IMPLEMENTATION BLUEPRINT (CODE AS A WORK OF ART)")
print("=" * 80)
print(response.text)
print("=" * 80)

output_file = REPO_ROOT / "docs" / "architecture" / "MASTER_IMPLEMENTATION_BLUEPRINT.md"
output_file.write_text(response.text, encoding="utf-8")
print(f"\nSaved blueprint to: {output_file}")
