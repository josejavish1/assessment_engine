#!/usr/bin/env python3
"""Consult gemini-4-argon: Is taxonomy_actuarial_archetypes.json correct for all companies in the world?"""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

THE USER'S BRILLIANT & CRITICAL QUESTION:
"Pero tengo una duda de taxonomy_actuarial_archetypes.json: cada empresa es diferente en el mundo, ¿eso de taxonomy_actuarial_archetypes.json es correcto para todas las empresas del mundo?"
(Each company in the world is different: is taxonomy_actuarial_archetypes.json correct for all companies in the world?)

ANSWER THIS WITH PROFOUND TECHNICAL CLARITY AND HONESTY:
1. **THE HONEST TRUTH:** Can a static JSON file with fixed constants (e.g. default_perimeter_ratio=0.62, it_spend_ratio=0.016, beta=0.35) be universally "correct" for every single company on Earth?
   - Answer: NO, not if used as deterministic, rigid constants! That is the very definition of a heuristic anti-pattern.
2. **WHAT `taxonomy_actuarial_archetypes.json` ACTUALLY IS IN RIGOROUS ACTUARIAL SCIENCE:**
   - Explain the concept of **Empirical Bayesian Priors (Conjugate Priors)**.
   - How in Open FAIR, actuarial tables (like insurance mortality tables or industry failure rates) serve as the *a priori* distribution when zero telemetry is provided.
3. **HOW THE PLATFORM GENERALIZES TO ANY COMPANY IN THE WORLD (THE BAYESIAN TELEMETRY OVERRIDE):**
   - Explain how a world-class engine uses Bayesian updating:
     $$\text{Posterior Risk} = \text{Prior (from Archetype JSON)} \ \otimes \ \text{Likelihood (Tenant Empirical Telemetry)}$$
   - Show how a tenant's explicit telemetry (Revenue, EBITDA margin, actual cloud spend, measured RTO, verified FTEs, observed findings) dynamically updates and overrides the prior.
   - If a company provides detailed financials (e.g. Starling Bank or Molins), the static JSON prior gives way to the exact, empirical physical telemetry.
4. **EXECUTIVE SYNTHESIS:**
   Explain why having declarative sector priors is necessary (you cannot start from a blank sheet of paper), but why the dynamic telemetry override ensures that NO company is ever forced into an artificial cookie-cutter box.

Respond in 100% Technical English with supreme executive authority and pedagogical clarity.
"""

def main() -> None:
    print(f"Submitting Archetypes Universality Inquiry to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_TAXONOMY_ARCHETYPES_UNIVERSALITY_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nUniversality Ruling written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
