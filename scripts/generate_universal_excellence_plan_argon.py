#!/usr/bin/env python3
"""Consulting gemini-4-argon for the Comprehensive Task-by-Task Implementation Plan for Deliverable Excellence."""

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
Role: Chief Software Architect (Enterprise Document Engineering) & Global Head of Strategic Advisory.

CONTEXT:
We have audited the rendered AS-IS deliverables (Technical Annexes for Tower 1 Data Center and Tower 2 Hybrid Compute) with executive leadership.
Leadership has provided 12 critical engineering and editorial directives to bring the deliverables to 100% Tier-1 McKinsey/Gartner quality:

1. COVER PAGE:
   - Remove generic filler "Instalación: Perímetro de infraestructura y activos tecnológicos".
   - Remove bureaucratic subtitle "Proyecto: Diagnóstico de Arquitectura, Madurez Operativa y Resiliencia Cuantitativa (O-FAIR)".
   - Move document metadata ("STRATEGIC ADVISORY | Date | Version | Confidential") strictly into the bottom footer of the cover page.

2. TABLE OF CONTENTS:
   - Ensure the TOC is fully automated via native Word OpenXML fields (`w:fldSimple` / `w:instrText` `TOC \\o "1-3" \\h \\z \\u`) with an elegant fallback layout table that updates seamlessly in Word.

3. EXECUTIVE SUMMARY (CHAPTER 1) - AS-IS BOUNDARY PURITY:
   - Remove arbitrary prescription of "wants to reach Level 4 Managed". AS-IS is a diagnostic of current state; target maturity should only be mentioned if driven by mandatory regulatory frameworks (NIS2/DORA).
   - Eradicate TO-BE investment promises ("to neutralize this exposure the modernization program requires X investment of CAPEX..."). AS-IS describes observed exposure; investment belongs to TO-BE roadmap!
   - Add explicit cross-reference directing the reader to Chapter 4 and Appendix B for the forensic actuarial breakdown.

4. METHODOLOGICAL FRAMEWORK (CHAPTER 2):
   - Remove the academic "Three-phase calibration methodology" subsection.
   - Harmonize typography: unify table font sizes across the CMMI scale and capability score tables (headers 9.0 pt bold, data 8.5 pt regular, badges 8.0 pt bold).

5. RISK SECTION (CHAPTER 4) - MINI-INFOGRAPHIC CARD RE-ENGINEERING:
   - Remove the "Resilience & Efficiency Return Hexagon" diagram if present.
   - Decongest card header banner: do not concatenate code, capability, pillar, tier, rank, share in a single wall of text. Shorten and format cleanly.
   - Tone down aggressive colors to an executive, sober palette (muted Slate, Navy, subtle Amber, muted Crimson).
   - Remove repetitive boilerplate: eliminate the static "Evento Amenaza Iniciador" box that repeats identical text across all cards.
   - Replace the TO-BE "Directiva de Mitigación Ejecutiva" with a high-value CFO section: **Actuarial Calculation Breakdown & Justification** explaining the empirical derivation of the numbers (e.g. `SLE = Observed MTTR (2.5h) x Plant Hourly Cost (15,600 €/h) + Parts (6,000 €) = 45,000 €; LEF = 0.36 ev/yr; ALE = SLE x LEF = 16,200 €/yr`).
   - Grounded Realism & Actuarial Calibration: Ensure the baseline payload figures for Tower 1 match the previously agreed industrial plant reality (total tower ALE ~118,500 €/year, SLEs 25,000 € - 45,000 € based on real 2-4 hour recovery, not €1.05M!).
   - Probabilistic Hypothesis Language: Eradicate sensationalist deterministic claims ("this recirculation bursts compressors, skyrockets electric bills, and causes simultaneous collapses..."). Reframe in rigorous actuarial hypothesis language ("Under unmitigated conditions, persistent elevated thermal gradients increase the probability of thermal trip in cooling compressors, potentially causing an estimated operational stoppage of...").
   - Replace confusing jargon "Acoplamiento sistémico estrecho (cascada crítica)" with plain business language (e.g. "Efecto Cascada: Alto (Afecta a múltiples servicios)").

6. CONCLUSIONS (CHAPTER 5) - AS-IS DIAGNOSTIC SYNTHESIS:
   - Remove the Multi-Horizon Modernization Program table (1 Year, 3 Years, 5 Years with CAPEX, ROI, Payback). That belongs exclusively to the TO-BE phase.
   - Transform Chapter 5 into a pure AS-IS Diagnostic Synthesis summarizing current maturity posture, key vulnerabilities, and operational urgency.

7. APPENDICES:
   - Remove Appendix A ("Information Sources Custody Log") entirely.
   - Re-index Appendix B (Open FAIR Methodology) as the single primary technical appendix.

MANDATES:
- Zero bugs, zero problems, zero anti-patterns.
- Zero hardcoding: universal across all enterprises worldwide, all verticals, all target languages (es, en, pt, fr, de, ja), and all currencies.
- 100% Technical English Codebase: Zero Spanish words in Python code, docstrings, comments, or schemas.

YOUR TASK:
Provide an exhaustive, task-by-task engineering implementation plan specifying:
1. Exact file-by-file changes (`payload_to_ast.py`, `docx_compiler.py`, `locales.json`, `blueprint_t1_payload.json`, `blueprint_t2_payload.json`, etc.).
2. The exact data structures, AST node changes, and localization keys to add/modify.
3. Verification plan with automated tests.
"""

print(f"Requesting universal deliverable excellence plan from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: UNIVERSAL DELIVERABLE EXCELLENCE ENGINEERING PLAN")
print("=" * 80)
print(response.text)
print("=" * 80)
