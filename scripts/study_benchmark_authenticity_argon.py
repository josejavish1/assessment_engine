#!/usr/bin/env python3
"""Consult gemini-4-argon on benchmark authenticity and eradicating consulting bluff in Chapter 2."""

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
Role: Senior Partner at McKinsey / Gartner, Lead Auditor for Enterprise Technology Diligence, and Hardcore Systems Engineering Fellow.

THE USER'S BLUNT CRITIQUE:
The user immediately called out the following paragraph:
"A diferencia de modelos genéricos que aplican un umbral plano artificial, la referencia empleada en este diagnóstico refleja la mediana empírica (P50) del sector industrial manufacturero pesado... calibrada a partir de datos agregados de CMMI v2.0, Gartner IT Key Metrics Data y normas ISO/IEC..."

USER'S REACTION:
"Eso me suena a datos inventados" (That sounds like fabricated / made-up data).

THE ROOT CAUSE OF THE USER'S SKEPTICISM:
1. The user is 100% right. In real-world enterprise due diligence, attributing decimal numbers like 3.80, 3.65, 3.05, 3.25 to "Gartner ITKMD + CMMI" without a traceable primary citation or client-provided dataset smells of standard consulting bluff / pseudo-empirical decoration.
2. If the client CIO, CFO, or auditor asks: "Can you provide the Gartner/CMMI primary dataset report showing that cement industry storage is 3.55 and OT is 3.05?", and you cannot produce that exact commercial document, the entire credibility of the 22-page technical diagnostic collapses.
3. In pure CMMI (Capability Maturity Model Integration):
   - CMMI does NOT publish industry-specific decimals like 3.05 or 3.65 per tower. CMMI is an appraisal framework where **Level 3 (Defined / Standardized)** is the universally recognized baseline for an enterprise operating with formal standards rather than heroics.
   - Or alternatively, an AS-IS diagnostic should stand on its own empirical findings (inventory, risks, maturity scores, CMMI practice areas) without needing external pseudo-benchmarks.

STRATEGIC OPTIONS FOR ARGON TO EVALUATE:
Option 1: Complete Elimination of External Peer Benchmarks from Tomo 1 AS-IS.
- Table 2 shows strictly the forensic AS-IS reality:
  * Tower Code
  * Technological Domain
  * AS-IS Maturity Score (1.00 - 5.00)
  * CMMI Band (Inicial / Repetible / Definido)
  * Practice Area Coverage (% of subpillars formal)
  * Operational State / Risk Exposure (Estable / Deuda Técnica / Riesgo Crítico)
- Radar Chart plots the pure 10-domain AS-IS footprint without external ghost polygons.
- Zero fake citations. 100% empirical, bulletproof truth.

Option 2: Benchmark strictly against the canonical CMMI Standard Baseline: CMMI Level 3 (Defined / Standardized = 3.00).
- Level 3.00 is the formal CMMI threshold where an organization transitions from reactive/heroic (Level 2) to proactive/standardized (Level 3).
- Measuring the gap against 3.00 (Standardized Enterprise Operations) is mathematically and methodologically unassailable: it cites the official CMMI v2.0 specification, not a fabricated industry survey.

Option 3: Retention with specific audit framing (or move entirely to Tomo 2).

DELIVERABLES REQUIRED:
1. Honest, zero-bullshit analysis of why the user's critique is valid.
2. Recommended architectural decision between Option 1 (Pure Forensic AS-IS) and Option 2 (CMMI Level 3.00 Standard Baseline).
3. The exact specification for Table 2, Radar Chart, and Chapter 2 narrative in Tomo 1.
"""

    print(f"Consulting {model_name} on benchmark authenticity...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_BENCHMARK_AUTHENTICITY_DECISION.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated decision report: {out_file}")


if __name__ == "__main__":
    main()
