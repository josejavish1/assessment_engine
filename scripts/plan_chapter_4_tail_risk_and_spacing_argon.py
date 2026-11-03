#!/usr/bin/env python3
"""Argon-4 Consultation: Code Audit, Page 3 Spacing, Formula Simplification & Section 4.3 P90 Deepening (RFC 058)."""

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
Role: Chief Systems Architect & Principal Actuary (Tier-1 Management Consulting / Google Core Infrastructure).

USER'S REVIEW & DIRECTIVES:
The user delivered three specific requirements:

1. Mandatory Comprehensive Code Review:
   - Perform an exhaustive forensic code review of all recent implementations (`DynamicCustodyResolver`, `ast_table_builders.py`, `payload_to_ast.py`, `locales.json`).
   - Check strictly for:
     a) Zero bugs or edge-case failures.
     b) Zero hardcoding (scales across any global enterprise from mid-market to Top Tier 1 worldwide, any vertical, any currency).
     c) 100% Technical English codebase (not a single Spanish word in Python code, docstrings, identifiers, or logs).

2. Executive Summary (Page 3) Vertical Spacing Optimization:
   - User feedback:
     "en el '1. Resumen Ejecutivo' me encanta pero quizás como la idea es que ocupe una sola página y nos sobra espacio, quizás podríamos por ejemplo separar las tablas primera y segunda del resumen ejecutivo, entre cada párrafo dar un enter para que se vea más espacioso."
   - Requirement:
     Currently, Page 3 has ~268pt of empty void at the bottom because we compressed it too much.
     Formulate the exact vertical spacing budget for Page 3 on an A4 canvas (698pt printable height) so the page looks balanced, spacious, and elegant without ever overflowing onto Page 4:
     - Spacer between Table 1 (KPI) and Table 2 (Diagnostic Triad).
     - Spacer between Table 2 and Headline.
     - Paragraph vertical rhythm (`space_after` between 6pt and 8pt).

3. Section 4.1 Formula Simplification:
   - User directive:
     "En el punto 4.1 podemos sustituir 'R_hourly, est = C_op, est (Lucro Cesante Base) + C_sla, est (Penalizaciones Contractuales) + C_rec, est (Brigadas y Recuperación)' por simplemente 'R_hourly, est = C_op, est + C_sla, est + C_rec, est'"
   - Requirement:
     Replace the verbose formula string with the clean mathematical formula across `engine_config/locales.json` in all locales.

4. Section 4.3 P90 Tail Risk Disaster Scenario Deepening:
   - User directive:
     "También me pregunto si en el punto 4.3 deberíamos hablar y profundizar sobre lo que se dice en el resumen ejecutivo que no viene en ningún otro sitio: 'Ante una caída crítica simultánea de clústeres, el restablecimiento de los servicios clave requeriría hasta 15,5 horas, elevando la contingencia máxima proyectada a 325.000 € con soporte de emergencia del fabricante.' Esto que te he puesto arriba es un ejemplo, aplica para todas las torres."
   - Requirement:
     Currently, Section 4.3 presents the ALE concentration tiers, but lacks detailed technical grounding for the P90 stress scenario cited in Chapter 1.
     Design an authoritative actuarial callout / subsection in Section 4.3 titled:
     "Escenario Adverso de Contingencia Máxima y Resiliencia Extrema (P90)" / "P90 Adverse Contingency & Extreme Resilience Scenario".
     This section will detail:
     a) Compound failure trigger (e.g. simultaneous cluster degradation, dual power path loss).
     b) Asymptotic physical recovery window (e.g. 15.5h in T2, 17.3h in T1) calibrated by `OperationalTailRiskEngine`.
     c) Financial loss composition: Direct operational stoppage loss + contingent secondary disaster expenditures (emergency vendor support, express parts replacement, technical triage).
     This bridges Chapter 1 and Chapter 4 with 100% mathematical and narrative consistency across all 10 capability towers.

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale in `locales.json`).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 058) in Markdown:
1. Deliver the forensic code audit verdict on recent changes.
2. Detail the exact OpenXML vertical point budget for Page 3.
3. Specify the localized formula updates for Section 4.1.
4. Detail the Section 4.3 P90 Tail Risk subsection architecture and schema integration.
5. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 058 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_058_PAGE3_SPACING_FORMULA_AND_P90_DEEPENING_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 058 ARCHITECTURAL BLUEPRINT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
