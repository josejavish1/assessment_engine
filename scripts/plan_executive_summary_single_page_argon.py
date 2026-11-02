#!/usr/bin/env python3
"""Argon-4 Consultation: Architectural Design for Single-Heading Executive Summary (RFC 032).

Addresses:
1. Elimination of subsections 1.1 and 1.2 to preserve Chapter 1 as a single, cohesive '1. Resumen Ejecutivo'.
2. Elimination of the separate 1.2 financial table; instead, seamlessly integrate the credible CIO-level financial justification directly into the narrative prose.
3. Definitive resolution of the 'Repeatable' vs 'Repetible' split-brain and missing accents.
4. Complete eradication of the archaic word 'fabril' across all narrative layers.
5. Preserving the high-impact visual components: Executive KPI Scorecard Table and Diagnostic Triad Table (Strength, Gap, Bottleneck).
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

CONTEXT & USER DIRECTIVE FOR CHAPTER 1 ("RESUMEN EJECUTIVO"):
The user has reviewed the latest deliverable and issued the following instructions:

1. REMOVE SUBHEADINGS 1.1 AND 1.2:
   - "No generaría el subpunto 1.1. y 1.2, es un resumen ejecutivo, es decir, solo mantendría el punto 1. resumen ejecutivo. De hecho todo el contenido del punto 1.2 entero eliminaba todo"
   - An Executive Summary should be a single, cohesive brief on a single page under one main heading: "1. Resumen Ejecutivo" (or "1. Executive Summary").
   - Eliminate Subheadings 1.1 and 1.2 and the separate financial breakdown table.

2. EMBED CREDIBLE FINANCIAL JUSTIFICATION INTO THE NARRATIVE PROSE FOR THE CIO:
   - "lo que creo es que hay que explicar de alguna forma de donde salen esos 141K y el 1.1M€ es decir, es que yo veo a un CIO que solo se va leer la primera hoja, y va a querer saber en esa lectura de donde salen esos números aunque sea de forma resumida y justificada para que el se los pueda creer."
   - A CIO reading Page 1 will want to know where the numbers come from in credible, plain business language:
     - The Expected Annual Loss (ALE, e.g. 141K€ / 101K€/year) represents recurring operational friction derived from the evaluated failure frequencies (cooling, power telemetry, hypervisor contention) multiplied by the hourly downtime cost of 10,000 €/h.
     - The severe stress scenario (P90 tail risk, e.g. 1.17M€ / 675K€) represents the financial impact of prolonged concurrent failures during peak dispatch and logistics windows.
   - This explanation must be woven directly and credibly into the second paragraph of the executive narrative.

3. RESOLVE "REPEATABLE" VS "DEFINIDA" & MISSING ACCENTS IN CACHED PAYLOADS:
   - The user noted: "en el segundo parrafo en un documento dice 'El diagnóstico sitúa la madurez de la torre en 2.6 sobre 5.0, clasificada en banda Definida.' y en otro dice 'La evaluacion situa la madurez de la torre en 2.5 dentro de la banda Repeatable' no se porque en el segundo hay una palabra en inglés al final y en el primero no, ¿split brain? ¿algún error?"
   - In `approved_annex_t2.template_payload.json`, the cached string contained unaccented text ('computo', 'evaluacion situa', 'perdida', 'mas') and English 'Repeatable'.
   - The compiler and enricher must ensure that:
     a) Language-specific band names always resolve to the localized term ('Repetible' in Spanish, 'Repeatable' in English).
     b) Any cached unaccented words or English band names in incoming payloads are sanitized/normalized upon ingestion.
     c) The JSON payload on disk is updated with clean, properly accented Spanish text.

4. COMPLETE ERADICATION OF "FABRIL":
   - "te veo que usas mucho la palabra fabril no se si español de españa se usa, pero recuerda tiene que estar en un lenguaje sencillo y español de españa cuando así se te pida porque puede ser español de sudamerica."
   - The archaic adjective "fabril" must be completely removed from all text, replaced with natural contemporary European Spanish: "de planta", "operativa industrial", "en las fábricas", "centros productivos".

5. POLISHED EXECUTIVE SUMMARY PAGE 1 STRUCTURE:
   - Heading 1: "1. Resumen Ejecutivo"
   - Component A: Executive KPI Scorecard Table (Score Actual | Banda de Madurez | Exposición Anual Estimada)
   - Component B: High-Impact Executive Headline (bold) + 3 Fluid MECE Narrative Paragraphs:
     * Paragraph 1: Strategic Context & Platform Situation.
     * Paragraph 2: Maturity Diagnostic & Credible Financial Risk Justification (explaining the 141K ALE and 1.1M P90 origin in plain C-level language).
     * Paragraph 3: Consequences of Inaction & Regulatory/Licensing Urgency (NIS2, ISO 27001, VMware 2027).
   - Component C: Executive Diagnostic Triad Table (Fortaleza Estructural Principal | Brecha Arquitectónica Principal | Cuello de Botella Operativo).
   - Component D: Subtle Forensic Cross-Reference to Chapter 4 for detailed actuarial tables.
   - Pacing: Page break immediately following Chapter 1 so the entire Executive Summary forms an immaculate, self-contained 1-page brief!

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless design using clean architectural patterns.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - Works for any enterprise size, any vertical, any currency, and any language.
   - Dynamic currency and locale formatting.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, and docstrings must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 032) in Markdown:
1. Redesign of `payload_to_ast.py` (`_build_executive_summary_and_scope`) implementing the 1-page single-heading architecture (eliminating subheadings 1.1 and 1.2).
2. Specification for the credible CIO financial justification woven directly into Paragraph 2 of the narrative prose.
3. Clean payload update and dynamic sanitizer ensuring zero occurrences of 'Repeatable' or 'fabril' in Spanish deliverables.
4. Production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 032 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_032_EXECUTIVE_SUMMARY_SINGLE_PAGE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 032 ARCHITECTURAL PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
