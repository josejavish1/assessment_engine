#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a phased, zero-defect Master Plan for remediating the 4 Tribunal flaws."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Actuarial Arbiter, and Master of Design Patterns.

USER DIRECTIVE & ARCHITECTURAL CHALLENGE:
"Para cada uno de los 4 puntos que me has dicho --> lo único es antes de ponernos a programar hay que pensar bien como lo vamos a abordar y en cuantas fases para garantizar que queda sin errores y que vamos aer 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra... aumentar la calidad de los entregables al 100% y quiero lo piense gemini-4-argon que lo haga sin bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial. Pídeselo a gemini-4-argon en inglés."

THE PROBLEM TO SOLVE - THE 4 CRITICAL TRIBUNAL FLAWS:
The World Expert Tribunal rejected the financial sections of the otherwise stellar technical report due to 4 fatal flaws:
1. **Ghosts of Copy-Paste in Crisis Scenarios (P90):** T3 (Networks) and T10 (Plant OT) P90 paragraphs carry residual boilerplate text mentioning "storage" or "databases".
2. **ALE Misalignment Between Section 1 and Section 4.3:** Internal arithmetic inconsistency where Section 1 executive summary quotes an old ALE, and Section 4.3 calculates a new one.
3. **False Cloud Narrative in On-Premise Domains (T4 & T8):** The Open FAIR methodology text for Capital Inefficiency assumes public cloud waste (AWS/Azure) when the technical diagnostic clearly states the client is 85% On-Premise HCI (SimpliVity).
4. **Flat Hourly Downtime Rate Ignoring Granularity:** T10 (Plant OT) uses a generic corporate hourly downtime rate instead of an archetype-aware or factory-specific buffering rate.

YOUR MANDATE:
Design a definitive, zero-defect Master Plan to systematically remediate these 4 flaws. The solution must be mathematically pure, structurally sound, and globally universal.

SPECIFIC DESIGN DIMENSIONS TO ADDRESS:
1. **Flaw 1 (P90 Boilerplate):** How will we dynamically inject the correct, localized P90 crisis trigger text mapped to the specific domain (e.g., "core network partition" for T3, "weighbridge SCADA halt" for T10) via `locales.json` without hardcoding?
2. **Flaw 2 (ALE Alignment):** How will the AST compiler enforce a Single Source of Truth (SSOT) for the calibrated ALE value so that Section 1, Section 4.3, and Table 5 strictly point to the exact same memory reference?
3. **Flaw 3 (Context-Aware Methodology):** How will the GoF Strategy Pattern in `actuarial_receptors.py` dynamically toggle between a "Cloud-Native FinOps" narrative and an "On-Premise Infrastructure Waste" narrative based on the macroeconomic `cloud_intensity_gamma` threshold?
4. **Flaw 4 (Granular Downtime):** How will the Availability Outage strategy leverage the `buffering_elasticity_beta` to render a narrative that explains physical silo buffering for heavy industry vs. immediate transaction loss for digital banking?
5. **Execution Phasing:** Break down the implementation into strict, verifiable phases (Phase 1, Phase 2, etc.).

Constraints:
- 100% Technical English for the response and proposed code constructs.
- No code implementation yet; provide the detailed, step-by-step Master Plan and architectural specifications.
- Must be globally universal for ANY company, ANY vertical, and ANY currency/language.
- NO client names hardcoded.

Deliver your architectural plan now.
"""

def main() -> None:
    print(f"Submitting 4-Flaw Remediation Master Plan request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    plan_report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_4_FLAWS_REMEDIATION_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(plan_report, encoding="utf-8")

    print(f"\nMaster Plan written to: {out_file}\n")
    print("=" * 80)
    print(plan_report[:3500])
    if len(plan_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
