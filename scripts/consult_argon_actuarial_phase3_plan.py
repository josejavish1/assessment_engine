#!/usr/bin/env python3
"""Consult gemini-4-argon for Phase 3: Mathematical Tower-Level Sub-Additivity and Physical Ceiling (ALE < SLE)."""

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

PROMPT = """You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

THE SITUATION:
We are implementing Phase 3 of our Quantitative Risk Engine (Open FAIR + FAIR-CAM).
We have successfully eliminated keyword scraping, removed fixed-hour tables from code and JSON, and derived RTO continuously from CMMI maturity:
RTO(M) = 1.0 + 23.0 * ((5.0 - M) / 4.0)^1.35.

However, an actuarial anomaly was detected in our latest multi-tower compilation:
In towers with multiple severe findings (e.g., T5 Operational Continuity with 5 findings, or T2 Compute with 6 findings), linearly summing the raw finding ALEs results in:
- T5: ALE = 422,886 EUR/yr vs Worst Crisis SLE = 323,683 EUR (ALE > SLE!)
- T2: ALE = 366,850 EUR/yr vs Worst Crisis SLE = 290,042 EUR (ALE > SLE!)
- T7: ALE = 105,072 EUR/yr vs Worst Crisis SLE = 102,721 EUR (ALE > SLE!)

ANOMALY ANALYSIS:
In actuarial risk theory, an enterprise component cannot lose more in an expected annual ordinary loss (ALE) than its single catastrophic wipeout cost (SLE_max). When multiple vulnerabilities exist on the same physical infrastructure (e.g. SimpliVity cluster or electrical supply), they share fate; multiple concurrent disruptions saturate at the maximum loss of the platform.

USER MANDATES:
1. Zero Hardcoding: The solution must scale dynamically for ANY company ($20M SMB to $500B+ Global Tier-1) across ANY vertical. No client names, no fixed numbers, no magic multipliers.
2. 100% Technical English Codebase: Zero Spanish words, tokens, comments, docstrings, or regex in any `.py` file. Localization is strictly delegated to `locales.json`.
3. Actuarial Realism & Proof: In EVERY tower, the Annual Ordinary Impact (ALE) MUST be strictly less than the Worst Crisis Event (SLE_max): 0 < ALE_Tower < SLE_max.
4. "Think before coding": Provide a profound, zero-error, multi-phase architectural execution plan before modifying any code.

YOUR TASK:
Analyze this situation and provide a structured, phased execution plan for Phase 3:
1. Mathematical Model: Formulate the exact mathematical mechanism to couple multiple finding ALEs within a tower (e.g., concave exponential saturation: ALE_eff = SLE_max * (1 - exp(- sum(ALE_k) / SLE_max)), or harmonic/copula saturation). Prove that this mathematically guarantees ALE_Tower < SLE_max across all domains.
2. Step-by-Step Implementation Steps: Detail how this will be integrated into `TowerPayloadHydrator` and `tomo_asis_ast_compiler.py` while preserving Hamilton largest remainder cent-level exact sum conservation.
3. Quality Gate Probes: Specify automated test assertions to certify that for 100% of towers, ALE < SLE_max.

Provide the response strictly in 100% Technical English, formatted with YAML front matter for documentation governance.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon for Phase 3 Architectural Plan...")
    response = client.models.generate_content(model=model, contents=PROMPT)

    out_file = REPO_ROOT / "docs/architecture/ARGON_PHASE3_ACTUARIAL_SATURATION_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    front_matter = (
        "---\n"
        "status: Verified\n"
        "owner: docs-governance\n"
        "source_of_truth:\n"
        "- docs/README.md\n"
        "last_verified_against: 2026-11-08\n"
        "applies_to:\n"
        "- gemini\n"
        "- architecture\n"
        "doc_type: operational\n"
        "diataxis: reference\n"
        "verification_mode: editorial\n"
        "---\n"
    )
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {out_file.name})")
    print("=" * 80)


if __name__ == "__main__":
    main()
