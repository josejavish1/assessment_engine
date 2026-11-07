#!/usr/bin/env python3
"""Executive Editorial Simplification & High-Value Diagnosis Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 078) purging developer jargon, pedantic phrasing,
and confusing metrics across Volume 1 headings and Chapter 1 executive tables.
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
    print(f"Connecting to reasoning engine: {model_name}...")

    prompt = """
Role: Chief Corporate Governance Advisor, Executive Editorial Director, and Senior Partner at McKinsey / Gartner advising Global Fortune 500 Boards, CEOs, CFOs, and CIOs.

CONTEXT & PROBLEM STATEMENT:
In the Assessment Engine's Consolidated AS-IS Diagnostic deliverable (Volume 1 / Tomo 1), an executive reading the deliverable identified several critical editorial, clarity, and value defects:

1. Pedantic and Developer-Centric Jargon in Headings:
   - Several section titles and table headers throughout Volume 1 are unnecessarily verbose, academic, or contaminated with internal software developer jargon.
   - For example:
     * "Eje de Polaridad del Portafolio | Dominio Identificado (SSOT) | Telemetría e Impacto de Gobernanza" -> Terms like "SSOT" (Single Source of Truth) are internal programming jargon completely inappropriate for a Board of Directors or CIO deliverable.
     * "Radiografía de Polaridad y Extremos del Portafolio" -> Verbose and pedantic. Should be clean and direct: "1.1. Áreas Clave: Fortalezas y Puntos Críticos".
     * "Cuantificación Actuarial de Exposición Financiera (Open FAIR™)" -> Inflated. Should be: "1.3. Impacto Económico Estimado del Riesgo".
     * Other headings across Chapters 3, 4, 5 also suffer from unnecessary academic inflation.

2. Confusing and Low-Value Metric Placement in Chapter 1 Table 1.1:
   - In Table 1.1 (Row 1: Maturity Leader), the description currently states:
     "Madurez máxima del portafolio (3,30 / 5.00). Actúa como referencia interna de control y estandarización operativa (30.242 € / año)."
   - Problem: Quoting an annual loss exposure figure like `(30.242 € / año)` inside the maturity leader row is deeply confusing and distracting to an executive reader. Why would a reader care about a minor residual risk amount when learning about the company's strongest technological benchmark?
   - In Row 2 (Financial Risk Concentration) and Row 3 (Modernization Urgency), the text merely repeats numbers and formulaic phrases rather than providing strategic business meaning.

3. The Requirement: Pure Executive Clarity & High-Value Business Diagnosis (Zero Hardcoding):
   - Table 1.1 Headers must be intuitive and business-focused:
     * Axis / Indicator: "Indicador Clave" (Key Indicator)
     * Identified Domain: "Dominio Tecnológico" (Technology Domain)
     * Governance Impact / Diagnosis: "Diagnóstico y Consecuencia de Negocio" (Executive Diagnosis & Business Impact)
   - High-Value Business Takeaway in Column 3:
     * Leader: Focus strictly on architectural maturity, vendor support posture, physical/logical redundancy, and role as operational benchmark across the group. Zero irrelevant risk money quoted.
     * Risk Concentration: Focus on percentage share of total enterprise loss exposure, and link technical failure directly to operational disruption and fulfillment/revenue impact.
     * Modernization Urgency: Focus on low maturity, heavy operational reliance on manual interventions, and lack of automated recovery/contingency.
   - Universal Multi-Tenant Scalability: Zero hardcoded company names ("MOLINS"), domain codes ("T4", "T5"), or vertical nouns ("cemento", "básculas", "camiones"). Must work dynamically for ANY company in the world (banking, retail, logistics, manufacturing, healthcare, SaaS).
   - Document-Wide Heading Simplification: A cohesive, direct heading taxonomy across Volume 1.

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English.
   - Spanish exists strictly as data in `locales.json`.
2. ZERO HARDCODING:
   - No hardcoded client names, domain codes, scores, or vertical nouns in Python code or general catalog templates.
   - All values must be dynamically computed or parameterized.
3. 6-LOCALE MATHEMATICAL SYMMETRY:
   - Symmetrical updates in `locales.json` across `es`, `en`, `pt`, `fr`, `de`, `ja`.
   - Dynamic parameter tokens must match across all languages.
4. SINGLE-PAGE BUDGET PRESERVATION:
   - Changes in text volume must preserve the single-page budget of Chapter 1 (locked strictly on Page 3).

DELIVERABLE:
Generate an authoritative, board-ready architectural blueprint in Markdown:
"RFC 078: Executive Editorial Simplification & Value Diagnosis Governance".

The RFC MUST include:
1. Executive Verdict & Heading Simplification Catalog:
   - Master mapping of current verbose headings to simplified, executive-grade headings across Volume 1.
2. Refactored Table 1.1 Specification (Column headers, parameter signatures, and high-value diagnostic templates across all 6 locales).
3. Codebase Modification Plan (`tomo_asis_ast_compiler.py` and `locales.json`).
4. Automated Quality Gate Test Specification (`tests/unit/test_rfc078_executive_editorial_simplification.py`).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_078_EXECUTIVE_EDITORIAL_SIMPLIFICATION_AND_VALUE_DIAGNOSIS_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 078 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
