#!/usr/bin/env python3
"""Argon-4 Consultation: Architectural Design for Executive Summary Optimization (RFC 030).

Addresses:
1. Natural, fluid C-level executive prose (eliminating stilted, robotic cadence).
2. Multilingual maturity band localization bug (resolving 'Repeatable' vs 'Repetible').
3. Dedicated, plain-language Financial Exposure & Operational Risk section.
4. Natural European Spanish vocabulary (replacing stiff archaic 'fabril' with natural plant/operations terms).
5. Executive visual summary architecture: high-impact scorecards and executive triad table (Strength, Gap, Bottleneck).
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
Role: Principal Systems Architect, Chief Compiler Engineer & Executive Editorial Director (Tier-1 Management Consulting / McKinsey / Gartner).

CONTEXT & USER CRITIQUE OF CHAPTER 1 ("RESUMEN EJECUTIVO"):
The user performed an editorial review of Chapter 1 across Tower 1 (Data Center) and Tower 2 (Compute) and delivered 5 critical observations:

1. CRITIQUE 1: ROBOTIC / MECHANICAL PROSE
   - "el texto suena como muy robot quizás un resumen ejecutivo con algo más de prosa se entendiría mejor."
   - The current prompt in `annex_executive_synthesizer.yaml` enforces rigid, artificial constraints:
     "STRICTLY PROHIBITED from writing sentences longer than 25 words. Average sentence length must be 15 to 18 words."
     This forces the LLM to output choppy, telegraphic, stilted sentences that sound robotic and lack fluid narrative cadence.
   - We need elegant, persuasive, cohesive C-level executive prose that explains the operational reality with strategic depth and natural transitions.

2. CRITIQUE 2: SPLIT-BRAIN LANGUAGE ANOMALY IN MATURITY BAND ("Definida" vs "Repeatable")
   - "en el segundo parrafo en un documento dice 'El diagnóstico sitúa la madurez de la torre en 2.6 sobre 5.0, clasificada en banda Definida.' y en otro dice 'La evaluacion situa la madurez de la torre en 2.5 dentro de la banda Repeatable' no se porque en el segundo hay una palabra en inglés al final y en el primero no, ¿split brain? ¿algún error?"
   - Forensic Root Cause: In `run_executive_annex_synthesizer.py` line 227:
     `build_executive_handover` calls `derive_maturity_band(average(scores))` without passing `locale=doc_lang`.
     `derive_maturity_band` defaults to `locale=None` -> English!
     For T2, it passed `"global_band": "Repeatable"` into the LLM prompt. The LLM transcribed the exact English token "Repeatable" into the Spanish text!
   - This must be fixed at the root: `derive_maturity_band` must be strictly parameterized with the target document locale (`doc_lang`).

3. CRITIQUE 3: FINANCIAL EXPOSURE DESERVES A DEDICATED SUBSECTION IN ACCESSIBLE LANGUAGE
   - "cuando empieza a hablar de Exposición financiera creo que eso merece un apartado nuevo, y creo que habría que explicarlo mucho más y en un lenguaje sencillo."
   - Currently, ALE and P90 metrics are jammed into the middle of Paragraph 2 using dense acronyms (ALE, P90, Open FAIR).
   - Financial exposure should be presented with high-level clarity: a distinct subsection (e.g. 1.2 "Exposición Financiera y Riesgo Operativo") explaining in plain C-level financial language what these figures mean (annual operational friction vs worst-case failure), grounding them in tangible business consequences.

4. CRITIQUE 4: OVERUSE OF ARCHAIC / STIFF VOCABULARY ("fabril")
   - "te veo que usas mucho la palabra fabril no se si español de españa se usa, pero recuerda tiene que estar en un lenguaje sencillo y español de españa cuando así se te pida porque puede ser español de sudamerica."
   - The prompt encouraged naming physical facilities, causing the model to repeatedly inject "fabril" ("operativa fabril", "pesaje fabril", "contingencia fabril"). In modern European Spanish (Castilian), "fabril" is archaic and bookish.
   - Natural executive Castilian Spanish uses: "operaciones de planta", "instalaciones productivas", "entornos industriales", "operativa de fabricación".

5. CRITIQUE 5: FORCED "PRINCIPALES IMPACTOS" VS HIGH-IMPACT EXECUTIVE CARDS & TRIAD TABLE
   - "y luego al final habla de principales impacto de negocio pero suena hay como forzado no se entiende bien que quiere decir.... antes decias cosas en una tabla claramente 'SCORE ACTUAL BANDA DE MADUREZ 2.6 / 5.0 Definido' y en otra table 'Fortaleza principal ... Brecha principal ... Cuello de botella ...' no se ¿como podemos dejar de forma optima el resumen ejecutivo?"
   - Raw bullet lists of business impacts feel tacked on.
   - C-level executives need visual structure:
     a) An Executive Snapshot Key Metrics Card / Block (Score Actual, Banda de Madurez, Exposición Anual Esperada).
     b) An Executive Triad Table (Fortaleza Principal, Brecha Estructural Principal, Cuello de Botella Operativo).
     c) Clear narrative sections that tell the story seamlessly.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless design using clean architectural patterns.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The architecture must scale to ANY company in the world: from a mid-market manufacturing plant to a top Global Fortune 10 financial institution.
   - Any industry vertical.
   - Any ISO 4217 currency.
   - Any human language (English, Spanish, German, Japanese, Portuguese, French, etc.).
   - Zero hardcoded client names, zero fixed strings in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, class names, method signatures, variables, docstrings, and comments must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 030) in Markdown:
1. Redesign Chapter 1 ("Executive Summary") structure and visual layout:
   - Executive Narrative (Situation & Diagnostic Thesis).
   - Dedicated Financial Exposure Subsection (plain language, clear explanation of annualized expected loss vs concurrent stress scenario).
   - Visual KPI Snapshot Table / Cards (Score, Band, Expected Financial Exposure).
   - Executive Triad Table (Primary Strength, Primary Structural Gap, Primary Operational Bottleneck).
2. Surgical fix for the `derive_maturity_band` locale propagation bug in `run_executive_annex_synthesizer.py`.
3. Upstream prompt rewrite in `annex_executive_synthesizer.yaml`:
   - Replace mechanical 15-word sentence constraints with fluid, cohesive Tier-1 McKinsey/Gartner executive prose guidelines.
   - Enforce contemporary, natural European Spanish phrasing (banning archaic terms like "fabril" in favor of natural industrial/plant operations terms).
4. Document compiler AST updates in `payload_to_ast.py` to render the polished Chapter 1 layout.
5. Complete, production-ready Python and YAML code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 030 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_030_EXECUTIVE_SUMMARY_OPTIMIZATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 030 ARCHITECTURAL PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
