#!/usr/bin/env python3
"""Definitive Editorial & Actuarial Implementation Planner via gemini-4-argon.

Consults gemini-4-argon to formulate the detailed, zero-defect implementation
specification (RFC 067) covering all remaining points from USER_OBSERVATIONS_ASIS_TOMO_1.md:
- Point 2: Local Plant (5,000 €/h) vs Consolidated Group (13,061.29 €/h) Downtime Velocity.
- Point 3: CMMI 3.50 Sector Benchmark Methodological Justification & Source Rigor.
- Point 4 & 6: Plain-Language Chapter 3 Restructuring & 224,452 € Emergency Recovery Breakdown.
- Point 5: Mathematical Reconciliation Bridge for 29 Scenarios vs 10 Domain Rows.
- Point 7: Balanced Domain Cards (Observed Strengths + Operational Friction) & Intuitive ALE Labeling.
- Point 8: SPOF Matrix Sorting by Descending Criticality (CRITICAL -> HIGH -> MEDIUM -> LOW).
- Point 9: Canonical 4-Paragraph Legal Liability Disclaimer Unification.
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


def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return f"[File {path.name} not found]"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    observations_md = read_file_safe(
        REPO_ROOT / "docs/architecture/USER_OBSERVATIONS_ASIS_TOMO_1.md"
    )
    rfc_066_md = read_file_safe(
        REPO_ROOT / "docs/architecture/RFC_066_VISUAL_COVER_AND_EXECUTIVE_PERFECTION_ARGON.md"
    )

    prompt = f"""
Role: Principal Enterprise Systems Architect & Senior Advisory Partner at Gartner / McKinsey.

OBJECTIVE:
Formulate the definitive, zero-bug, zero-antipattern implementation blueprint (RFC 067) to execute the complete remediation of Points 2 through 9 for the Consolidated Tomo 1 AS-IS Technical Diagnostic compiler.

CORE MANDATES & LAWS:
1. UNIVERSAL MULTI-TENANT ENTERPRISE SCALABILITY:
   - Must scale cleanly for ANY enterprise in the world (50M$ mid-market to 50B$ global multinational, any vertical: heavy industry, banking, healthcare, retail, utilities).
   - Zero hardcoding of client names, site locations, hardware vendors, or fixed constants in Python code.
2. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, exceptions, and tests MUST be 100% Technical English. Zero Spanish words or characters in Python source files.
   - Natural language content lives strictly in `engine_config/locales.json` across all 6 supported locales (es, en, pt, fr, de, ja) with 100% mathematical symmetry.
   - All language parameters must be mandatory (`doc_lang: str`), no defaults.
   - Zero inline language conditionals (`if doc_lang == "es"` banned).

USER OBSERVATIONS LEDGER:
{observations_md}

RFC 066 VISUAL & ARCHITECTURAL FOUNDATION:
{rfc_066_md[:8000]}

DELIVERABLE REQUIRED:
Produce RFC 067 containing the surgical, exact implementation blueprint for each of the 8 remaining items:

1. Point 2: Local Facility (Plant) vs Consolidated Group Downtime Hourly Rates
   - Exact schema and parameter interpolation in Chapter 1 executive narrative.
   - Transparent architectural explanation separating single-plant physical stoppage from enterprise-wide ERP transaction paralysis.
2. Point 3: CMMI 3.50 Sector Benchmark Source & Methodological Rigor in Chapter 2
   - Methodological justification paragraph: CMMI v2.0 Level 3 + Gartner IT Key Metrics + ISO/IEC comparative baseline.
   - Dynamic parameterization of benchmark score and industry vertical label.
3. Points 4 & 6: Plain-Language Restructuring of Chapter 3 & 224,452 € Emergency Recovery Breakdown
   - Step-by-step narrative structure for IT leaders (not financial actuaries).
   - Concrete, transparent decomposition of the 224,452 € emergency recovery cost into 3 grounded operational buckets:
     * OEM 24x7 emergency engineering intervention out of contract (~42% / 94,270 €).
     * Urgent hardware spot procurement and courier logistics (~33% / 74,069 €).
     * External specialized database recovery and forensic triage services (~25% / 56,113 €).
4. Point 5: Section 3.1 Reconciliation Bridge (29 Scenarios vs 10 Displayed Rows)
   - Exact explanatory bridge paragraph explaining that the 29 Monte Carlo scenarios are aggregated into the 10 technology domain rows.
   - Adding an explicit "Escenarios Evaluados" column in Table 4 whose column sum strictly equals 29.
5. Point 7: Balanced Domain Diagnostic Cards in Chapter 4
   - Renaming "Exposición ALE" to an intuitive business label: "Impacto Económico Anual Estimado (Riesgo Activo)".
   - Structured two-part callout blocks per tower:
     * "Capacidades Operativas y Fortalezas Observadas" (Emerald/Teal accent border).
     * "Límites de Capacidad, Obsolescencia y Puntos de Fricción" (Amber accent border).
   - Enriched 3-column subpillars table: Subpilar | Fortalezas y Controles Activos | Puntos de Fricción y Riesgo.
6. Point 8: Section 4.11 SPOF Matrix Sorting by Descending Criticality
   - Canonical sorting algorithm: `CRÍTICA` -> `ALTA` -> `MEDIA` -> `BAJA`.
7. Point 9: Unified Legal Liability Disclaimer Across All Documents
   - Deprecate custom keys and render canonical `disclaimer_text_1` through `disclaimer_text_4` across all 20 tower annexes and Tomo 1.

Provide exact dictionary keys, exact localized text (English and Spanish), and method-by-method implementation guidance for `tomo_asis_ast_compiler.py`.
"""

    print(f"Requesting RFC 067 implementation plan from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_067_FULL_EDITORIAL_AND_TECHNICAL_REMEDIATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated RFC 067 implementation plan: {out_file}")


if __name__ == "__main__":
    main()
