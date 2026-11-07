#!/usr/bin/env python3
"""Executive Continuity Narrative Governance Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 076) purging methodological clutter from Volume 1 Chapter 1
and establishing pure executive-level operational continuity narrative governance.
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
In the Assessment Engine's Consolidated AS-IS Diagnostic deliverable (Volume 1 / Tomo 1), an executive reading Chapter 1 (Executive Summary) identified a severe editorial defect in Bullet 1:

Current Defective Text (Bullet 1 Body in `tomo_ch1_continuity_bullet_body`):
"Para efectos de gobierno financiero y priorización de inversiones, el modelo distingue dos umbrales de impacto horario: (1) Impacto Operativo en Centro Local (5.000 €/h), que cuantifica el coste de la paralización en una única planta o sede operativa; y (2) Impacto Corporativo Consolidado (13.061,29 €/h), que refleja la tasa de pérdida agregada cuando una caída en los sistemas centrales detiene simultáneamente la operativa de todo el grupo."

Executive Critique:
1. Methodological Noise in Executive Summary: An executive summary for the Board of Directors, CEO, CFO, and CIO should NOT explain the modeling mechanics or calibration thresholds of the simulation tool. Explaining "el modelo distingue dos umbrales" and quoting literal rates with unrounded decimals ("13.061,29 €/h") breaks executive pacing and distracts leadership from the operational reality.
2. Wrong Placement: The detailed hourly rates (local facility outage vs consolidated core downtime) belong naturally in Chapter 3 (Section 3.1: The Cost of Inaction) and in the technical domain annexes, where actuarial derivation is detailed with formulas and charts.
3. Lack of Strategic Clarity: Bullet 1 should focus strictly on the operational business risk: operational facilities and distributed branch sites depend on legacy single points of failure (unrouted communication links, hardware at end-of-support), creating an operational asymmetry where central IT has safeguards but edge/plant outages immediately freeze operational fulfillment and revenue delivery.
4. Universal Scalability: The text must be 100% tenant-agnostic and vertical-agnostic (applicable to manufacturing, mining, logistics, retail, banking, utilities). No hardcoding of specific client names ("MOLINS"), specific industry nouns ("cemento", "básculas", "camiones"), or static currency amounts.

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English.
   - Spanish exists strictly as data in `locales.json`.
2. ZERO HARDCODING:
   - No hardcoded client names, facility types, or specific industry jargon in Python source code.
3. UNIVERSAL MULTI-TENANT SCALABILITY:
   - The bullet must resonate with a manufacturing conglomerate, a retail chain, an energy utility, or a financial holding.
4. MATHEMATICAL SYMMETRY ACROSS ALL 6 LOCALES:
   - Symmetrical updates in `locales.json` across `es`, `en`, `pt`, `fr`, `de`, `ja`.
   - Dynamic parameters (if any) must match across all languages.

DELIVERABLE:
Generate a board-ready architectural blueprint in Markdown:
"RFC 076: Executive Narrative Realism & Operational Continuity Governance".

The RFC MUST include:
1. Executive Verdict & Editorial Flaw Analysis.
2. Refactored Localization Dictionaries for `tomo_ch1_continuity_bullet_title` and `tomo_ch1_continuity_bullet_body` across all 6 locales (es, en, pt, fr, de, ja), written in sober, high-level C-suite language.
3. Codebase Modification Plan: Changes in `tomo_asis_ast_compiler.py` and `locales.json` to ensure clean compilation without unused variable warnings.
4. Automated Quality Gate Test Specification (`tests/unit/test_rfc076_executive_continuity_narrative.py`).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_076_EXECUTIVE_CONTINUITY_NARRATIVE_GOVERNANCE_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 076 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
