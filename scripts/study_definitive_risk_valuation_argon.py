#!/usr/bin/env python3
"""Consult gemini-4-argon on strategic value of Chapter 3 Section 3.2 (Anatomy of a Major Incident)."""

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
Role: Advisory Partner, Senior Technology Strategy Director at Gartner / McKinsey, and Fortune 500 CIO.

CONTEXT & INQUIRY:
In Tomo 1 (Consolidated AS-IS Technical Diagnostic), Chapter 3 addresses Economic Impact and Actuarial Risk Analysis.
The chapter currently flows as follows:
- 3.1 The Cost of Inaction: Annualized Financial Exposure by Domain (Table 4: 916,416 € ALE across 10 domains, Table 5: 3-tier portfolio breakdown).
- 3.2 Anatomy of a Major Incident: What Happens during a Critical Outage? (Hypothetical single outage of 17.3 hours costing 450,000 €, split into 225,548 € direct downtime and 224,452 € emergency recovery: OEM support 94k, Spot hardware 74k, Database forensics 56k).
- 3.3 5x5 Open FAIR Heatmap Matrix (Mosaic of 29 scenarios).
- 3.4 Top 5 Systemic Risk Cards (Each card has SLE, LEF, and ALE).
- 3.5 Annual Portfolio Tail Risk & 3-Year Outlook (P90 = 2.29 M€/yr, 3Y cumulative = 2.75 M€ expected, 6.10 M€ VaR).

THE USER'S QUESTION:
"Realmente el punto 3.2 aporta valor o se puede eliminar?" (Does Section 3.2 really add value, or can/should it be eliminated?)

STRATEGIC ANALYSIS REQUIRED:
1. Executive Cognitive Load & Narrative Cohesion:
   - Does introducing a single hypothetical 450k € incident in Section 3.2 confuse the board between annual expected loss (ALE 916k €) and a single event?
   - Does it distract from the 5 discrete risk cards (which already contain SLE values of 205k €, 316k €, 340k €)?
2. Pros & Cons of:
   - Keeping Section 3.2 as is.
   - Eliminating Section 3.2 entirely from Tomo 1 (transferring emergency recovery concepts to technical annexes where deep incident simulations belong).
   - Merging the emergency recovery cost concept into the Executive Summary or the Top Risk Cards without a dedicated standalone 17.3-hour hypothetical section.
3. Unambiguous Recommendation:
   - Provide a definitive, clear recommendation for Tomo 1. If eliminated, what is the exact resulting chapter structure and narrative flow?
"""

    print(f"Consulting {model_name} on Section 3.2 strategic viability...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_STRATEGIC_ASSESSMENT_SECTION_3_2.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated strategic recommendation: {out_file}")


if __name__ == "__main__":
    main()
