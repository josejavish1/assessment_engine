#!/usr/bin/env python3
"""Consult gemini-4-argon on pure forensic AS-IS Chapter 2 architecture and prose enrichment."""

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
Role: Advisory Partner at McKinsey / Gartner, Lead Auditor for Enterprise Technology Diligence, and Senior Enterprise Architect.

MANDATE FROM LEADERSHIP:
The user has issued a decisive, zero-bullshit mandate for Chapter 2 (Maturity Radiography):
1. Completely eradicate all references to external "industry/sector benchmarks" (Mediana P50, Gartner ITKMD, fake external decimals). Unless we have primary empirical client survey datasets, inventing external peer decimals damages technical credibility.
2. Completely remove the callout box `Metodología de Calibración de la Referencia Sectorial`.
3. Redesign Table 2 (Table of Capability Maturity) to be 100% forensic, internally consistent, and audit-proof:
   - Column 1: Código (T1–T10)
   - Column 2: Área Tecnológica Evaluada
   - Column 3: Madurez AS-IS (1.00 – 5.00)
   - Column 4: Nivel CMMI (Nivel 1 Inicial, Nivel 2 Repetible, Nivel 3 Definido)
   - Column 5: Estado Operativo (e.g. Operación Estandarizada, Deuda Técnica Moderada, Riesgo Operativo Alto)
   - Column 6: Factor Focal de Diagnóstico (Concise core technical observation for that tower)
4. Redesign Figure 2.1 (Polar Radar Chart):
   - Single authentic series: Molins AS-IS footprint in corporate solid blue (#0072BC) with filled area, showing the exact shape of the enterprise capabilities over the CMMI Level 1 to 5 grid. Zero external ghost polygons.
5. Enrich the professional executive narrative prose in Chapter 2:
   - Deepen the strategic explanation of the 2.55 consolidated score (Level 2 - Repeatable).
   - Articulate the dual reality of the enterprise:
     * Standardized Foundations: Domains like Storage (3.30) and Digital Workplace (3.10) have reached Level 3 (Defined), functioning with documented standards, stable vendors, and predictable service levels.
     * Operational Bottlenecks: Plant continuity (2.10), Core applications (2.40), and Weighbridge / Dispatch logistics (2.40) remain at Level 2 (Repeatable), where operations succeed through technical staff heroics, reactive incident response, and legacy point-to-point configurations.
   - Explain how this asymmetry creates latent operational risk that directly links to the financial exposure detailed in Chapter 3.

NON-NEGOTIABLE LAWS:
- 100% Technical English Codebase: Zero Spanish in Python code, docstrings, or variables.
- Multi-Tenant & Multi-Locale: All natural language string updates must be symmetric across all 6 locales (es, en, pt, fr, de, ja).
- Zero Hardcoding: Dynamic binding via `locales.json` and DocumentAST nodes.

DELIVERABLES:
1. Exact column definitions and row mapping for forensic Table 2.
2. Exact enriched narrative prose across all 6 locales for Chapter 2 (`tomo_ch2_summary_p1`, `tomo_ch2_summary_p2`, `tomo_ch2_intro`).
3. Complete implementation blueprint for `tomo_asis_ast_compiler.py` and `generate_global_radar_chart.py`.
"""

    print(f"Consulting {model_name} on Chapter 2 pure forensic architecture...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_070_PURE_FORENSIC_CHAPTER_2_ARCHITECTURE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated RFC 070 specification: {out_file}")


if __name__ == "__main__":
    main()
