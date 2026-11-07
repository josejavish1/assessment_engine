#!/usr/bin/env python3
"""Executive Actuarial Realism & Governance Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 074) resolving the actuarial interpretation of single-incident
outages versus cumulative portfolio tail risk in Chapter 1 and Chapter 3.
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
Role: Chief Actuarial Auditor, Principal Systems Architect, and Senior Partner at Gartner / McKinsey advising Corporate Boards, CEOs, CFOs, and CIOs.

CONTEXT & PROBLEM STATEMENT:
In the Assessment Engine's Consolidated AS-IS deliverable (Tomo 1), an executive reading the current financial diagnostic identified two severe credibility defects that threaten board acceptance:

1. Table 3 (Domain Exposure & Severe Event Table) Header & Total Row Fallacy:
   - Header Defect: The column is titled "Coste ante Incidente Grave (P95)". The acronym "(P95)" adds confusing technical jargon to a high-level executive table where the rest of the report evaluates the 90th percentile (P90).
   - Actuarial Summation Fallacy: In the TOTAL row of Table 3, the column "Coste ante Incidente Grave" currently sums the worst-case values of all 10 domains to display "2.291.040 €".
     In actuarial risk modeling (Open FAIR™, Solvency II, Basel III), percentiles and worst-case single incident losses (SLE) CANNOT be summed linearly (VaR is sub-additive under independence, and linear summation implies an apocalyptic correlation rho=1 where every domain collapses simultaneously on the exact same day).
     Any CFO or Chief Risk Officer (CRO) reading this will conclude the report is inflating risk artificially to scare the board into approving IT modernization budgets.

2. Chapter 1 Executive Summary Narrative Clarity:
   - The executive summary must clearly differentiate three distinct business dimensions without condescending or overly colloquial language ("goteo", "paternalistic framing"):
     (a) Annual Average Exposure (ALE): The baseline annual friction, uncontracted overtime, and routine outage losses.
     (b) Single Major Incident Outage: The direct operational cost of a single critical outage in the most exposed domain (e.g., T5 factory stoppage).
     (c) Adverse Annual Crisis Scenario (Portfolio P90): The annual cumulative tail risk if multiple severe incidents accumulate across different platforms throughout a difficult year.

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python source code, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English.
   - Spanish and other languages exist strictly as data inside `engine_config/locales.json`.
2. ZERO HARDCODING:
   - No hardcoded client names ("MOLINS"), domain codes ("T5"), or monetary figures ("515.485 €", "2.291.040 €") in Python source.
   - The compiler must dynamically compute the maximum single domain incident (`worst_incident_cost`, `worst_incident_domain`, `worst_incident_code`) from `domain_topology` andSSOT telemetry.
3. MULTI-TENANT UNIVERSAL SCALABILITY:
   - Must scale seamlessly from a 50M€ manufacturing plant to a 50B€ multinational bank, across any currency (EUR, USD, GBP, JPY, etc.) and locale.
4. MATHEMATICAL SYMMETRY:
   - All translation key changes in `locales.json` must be synchronized across all 6 supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`).

DELIVERABLE:
Generate a rigorous, board-level architectural specification in Markdown:
"RFC 074: Executive Actuarial Realism, Single-Incident Transparency & Chapter 1/3 Governance".

The RFC MUST include:
1. Executive Verdict & Actuarial Problem Analysis.
2. Production Code Blueprint for `tomo_asis_ast_compiler.py`:
   - How `worst_incident_cost` and `worst_incident_domain` are dynamically computed across active domains.
   - How Table 3 header is cleaned (removing P95) and how the TOTAL row displays the maximum single incident instead of a false linear sum.
   - How the explanatory footnote is formatted beneath Table 3.
3. Full Localization Catalog Dictionaries for `locales.json` across all 6 locales (es, en, pt, fr, de, ja).
4. Validation & Quality Gates (assertions preventing hardcoded brands, ensuring mathematical symmetry, and verifying single-incident transparency).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_074_EXECUTIVE_ACTUARIAL_REALISM_AND_GOVERNANCE_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 074 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
