#!/usr/bin/env python3
"""Argon-4 Consultation: Architectural Design for 2-Level TOC, Clean Executive Summary Heading, and Universal Diacritics Preservation (RFC 029)."""

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

CONTEXT & USER REQUIREMENTS:
The user has reviewed the latest generated deliverables and requested three specific refinements, alongside a strict architectural directive:

1. REQUIREMENT 1: TWO-LEVEL TABLE OF CONTENTS (2 Levels Only)
   - The user states: "El indice quiero que solo aparezcan 2 niveles no 3 niveles"
   - The Table of Contents must be restricted to 2 hierarchy levels (Chapters and Sections: Levels 1 and 2 only), eliminating sub-subsections (Level 3) from the TOC index.
   - OpenXML instruction must be `TOC \\o "1-2" \\h \\z \\u`.
   - Initial pre-computed fallback entries must filter out any `level > 2`.

2. REQUIREMENT 2: STREAMLINED CHAPTER 1 TITLE ("Resumen Ejecutivo")
   - The user states: "el titulo del apartado 1. '1. Resumen Ejecutivo y Tesis Estratégica' no sería mejor que solo se llamara 'Resumen ejecutivo'?"
   - The title must be streamlined to pure "Resumen Ejecutivo" (and equivalent in other languages: "Executive Summary", "Resumo Executivo", etc.).
   - Since Word's `Heading 1` already provides automatic list numbering, Word will display "1. Resumen Ejecutivo" cleanly without clutter.

3. REQUIREMENT 3: ROOT CAUSE AND UNIVERSAL SOLUTION FOR MISSING SPANISH DIACRITICS / TILDES
   - The user asks: "porque aparecen las palabras en español sin tilde?"
   - Investigation indicates that while static catalog strings in `engine_config/locales.json` have full accents (e.g., 'cómputo', 'diagnóstico', 'exposición'), LLM-synthesized narrative strings in `blueprint_payload.json` and `approved_annex_payload.json` (such as 'saturacion', 'computo', 'mas', 'energia', 'electrica') were generated without tildes because upstream AI prompt registries (`annex_executive_synthesizer.yaml`, `blueprint_pilar_architect_prompt.yaml`) lacked explicit typographic and orthographic diacritic mandates.
   - We need an ironclad, universal solution that:
     a) Enforces strict orthographic diacritics in all AI generation prompts across any target language (e.g. Spanish tildes, French cedillas/accents, German umlauts, Portuguese tildes).
     b) Implements an automated, language-aware post-processing enrichment rule (e.g. within `UniversalPayloadEnricher` or a dedicated text normalization filter) to ensure standard accentuation is restored or preserved prior to AST document compilation without corrupting code identifiers or breaking non-Spanish locales.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless design using clean architectural patterns.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The architecture must scale to ANY company in the world: from a 50-person credit union or regional hospital to a top Global Fortune 10 bank, aerospace manufacturer, or energy conglomerate.
   - Any industry vertical.
   - Any ISO 4217 currency.
   - Any human language (English, Spanish, German, Japanese, Portuguese, French, etc.).
   - Zero hardcoded client names, zero fixed strings in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, class names, method signatures, variables, docstrings, and comments must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 029) in Markdown:
1. Architectural design for Requirement 1 (2-Level TOC in `TOCNode`, `payload_to_ast.py`, and `docx_compiler.py`).
2. Architectural design for Requirement 2 (Key updates in `engine_config/locales.json` and AST mapping for "Resumen Ejecutivo").
3. Forensic root-cause analysis and definitive architectural solution for Requirement 3 (Diacritics & Accents preservation):
   - Upstream prompt governance updates in `annex_executive_synthesizer.yaml` and `blueprint_pilar_architect_prompt.yaml`.
   - Deterministic language-aware diacritics restoration / normalization in `UniversalPayloadEnricher`.
4. Concrete, production-ready Python and YAML code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 029 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_029_TOC_DEPTH_AND_DIACRITICS_GOVERNANCE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 029 ARCHITECTURAL PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
