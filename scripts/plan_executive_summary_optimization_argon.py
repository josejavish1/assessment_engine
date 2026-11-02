#!/usr/bin/env python3
"""Argon-4 Forensic Audit: Executive Summary Polish & TOC Real-Page Pre-Calculation (RFC 038)."""

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
Role: Principal Actuarial Systems Architect & Chief Compiler Engineer (Google Tier-1 / Anthropic Core Infrastructure / MIT Actuarial Fellow).

CRITICAL INCIDENT & USER CRITIQUE:
The user reviewed the deliverables and was deeply upset with the state of Chapter 1 (Resumen Ejecutivo) and the persistent Table of Contents discrepancy between Tower 1 and Tower 2:

1. EXECUTIVE SUMMARY (CHAPTER 1) REGRESSION:
   - The user writes:
     "PERO QUE HA PASADO EN EL PUNTO 1 MENUDA CAGADA HEMOS IDO DE MAL EN PEOR, LEELO ENTERO, PORQUE ES QUE AHORA ES HORRIBLE ANALIZALO TU Y DIME QUE VES TANTO EN LA TORRE 1 COMO EN LA TORRE 2, QUE DECEPCIÓN ESTOY MUY MAL."
   - Forensic Analysis of what went wrong:
     In our attempt to justify the 10,000 €/h rate and site weighting, we injected an unreadable, pedantic, 116-word paragraph in Chapter 1 that:
     a) Leaked a raw variable token: `(default_perimeter_name)`!
     b) Dumped repetitive, bureaucratic calculations: "Partiendo de una facturación anual consolidada verificada de 1.000.000.000 €, el motor aplica un Factor de Ponderación Operativa del Perímetro del 100,00%... Esto establece una Base de Facturación Expuesta Efectiva de 1.000.000.000 €."
     c) Dumped long, ugly benchmark strings: "Gartner Cross-Industry Operational Continuity Benchmark (0,0010%)".
     d) Transformed an Executive Summary (meant for the CEO, Board, and CIO) into an aggressive mathematical audit defense!
   - How should Chapter 1 read?
     An Executive Summary must be elegant, high-signal, punchy, and McKinsey/Gartner grade:
     - 4 multi-clause analytical paragraphs of 40-55 words each:
       * P1 (Operational Health & Maturity): Score, band, daily operational reality.
       * P2 (Business Exposure & Downtime Rate): Translating technical findings to business impact via the validated rate of 10,000 €/h, without formulas or raw variable leaks.
       * P3 (Annual Loss vs Tail Risk in Hours): Translating ALE (14.1h in T1, 10.1h in T2) and P90 stress (116.8h in T1, 67.5h in T2) into downtime disruption.
       * P4 (Remediation Value): Clear ROI on operational stability and risk mitigation.
     - All detailed perimeter formulas, headcount derivations, and Monte Carlo mathematics belong in Chapter 4 or the Appendices, NOT in the Executive Summary!

2. TABLE OF CONTENTS DIVERGENCE BETWEEN T1 AND T2:
   - The user writes:
     "y por cierto, sigue pasando el mismo error, en la torre 1 se acutalizan las páginsa del índice al abrir pero la torre 2, no creo que hay un bug o un splitbrain que no debería estar porque si está bien o mal para uno debería estarlo apra todos."
   - Forensic Analysis of what went wrong:
     Both T1 and T2 have identical XML: `<w:updateFields w:val="true"/>` and `w:dirty="true"`.
     However, Microsoft Word on Windows SUPPRESSES the update prompt when a second document is opened in an existing `WINWORD.EXE` process!
     As a result, if the user opens T1 first, Word updates T1; but when they open T2 next, Word does not prompt to update T2, leaving the hardcoded fallback page numbers from `locales.json` (`Pág. 10`, `Pág. 18`, `Pág. 20`, `Pág. 22`) visible!
   - Architectural Solution:
     We must PRE-CALCULATE the true physical page numbers of every heading dynamically (either via AST page-break accounting or headless LibreOffice layout sync) and inject the REAL physical page numbers directly into the static TOC XML entries in DOCX!
     This guarantees that even if Word suppresses the prompt, or in Word Online / mobile viewers where fields do not auto-update, the Table of Contents displays 100% ACCURATE PAGE NUMBERS on both T1 and T2! Zero split-brain!

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless mathematical and architectural design.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - Works across all 10 towers (T1..T10), all tiers, all languages, and all verticals.
   - Zero hardcoded client names or strings in Python logic.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, and docstrings must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 038) in Markdown:
1. Executive Summary Redesign: Provide the exact, elegant, high-signal narrative templates for `locales.json` in Spanish and English (purging all formula dumps, raw variable tokens like `default_perimeter_name`, and repetitive math).
2. Dynamic TOC Real-Page Resolution: Show how to dynamically compute and write the exact physical page numbers into the TOC `<w:sdt>` entries so T1 and T2 are 100% consistent regardless of Word's update prompt behavior.
3. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 038 Executive Summary Polish & TOC Real-Page Sync from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_038_EXECUTIVE_SUMMARY_POLISH_AND_TOC_REAL_PAGES_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 038 EXECUTIVE SUMMARY POLISH & TOC REAL-PAGES")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
