#!/usr/bin/env python3
"""Consult gemini-4-argon: Does a top world expert of Open FAIR approve this UATCE plan?"""

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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = """You are 'gemini-4-argon', Fellow of the Open FAIR Institute, Principal Peer Reviewer for the Open Group Security Forum, and co-author of enterprise Quantitative Risk Management (QRM) standards.

USER'S PIERCING INQUIRY:
"¿Esto qué plan lo aprueba un top expert de FAIR?" (Does a top world expert of FAIR approve this plan?)

THE CONTEXT:
We proposed the Universal Actuarial Telemetry Calibration Engine (UATCE), which introduces 4 macroeconomic scaling functions (Omega_perimeter, Beta_buffering, Gamma_cloud, Theta_regulatory) mapped to 6 operational archetypes to calibrate Loss Magnitude (LM) and Loss Event Frequency (LEF) across diverse global industries.

YOUR MANDATE:
Deliver an unvarnished, peer-reviewed evaluation from the perspective of a world authority on Open FAIR (e.g., Jack Jones, author of "Measuring and Managing Information Risk: A FAIR Approach", Douglas Hubbard, or a Lead Arbiter at the Open Group):
1. DOES AN OPEN FAIR TOP EXPERT APPROVE THIS?
   - Answer unequivocally: YES, NO, or CONDITIONALLY.
2. WHICH COMPONENTS OF THE PLAN ARE 100% CANONICAL OPEN FAIR?
   - How does this map to the canonical FAIR ontology (Primary Loss: Productivity, Response, Replacement; Secondary Loss: Fines/Judgments, Competitive Advantage, Reputation)?
   - How does this relate to FAIR-CAM (Control Analytics Model) and FAIR-MAM (Materiality Analytics Model)?
3. WHAT WOULD A TOP FAIR PURIST CRITIQUE OR DEMAND?
   - Purists often insist that every risk must be a discrete Threat-Asset-Effect scenario rather than an econometric top-down distribution. How does this plan honor discrete bottom-up finding scenarios while using macroeconomic scalars only for boundary calibration?
4. THE FINAL VERDICT:
   - What is the definitive judgment on whether this architecture qualifies as Tier-1 Open FAIR compliant before an institutional board of examiners?

Respond in 100% Technical English with supreme academic and professional rigor.
"""

def main() -> None:
    print(f"Submitting Open FAIR Expert Evaluation to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_OPEN_FAIR_EXPERT_APPROVAL_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nVerdict written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:3500])
    if len(ruling) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
