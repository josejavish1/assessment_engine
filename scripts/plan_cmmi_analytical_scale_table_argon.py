#!/usr/bin/env python3
"""CMMI Analytical Maturity Scale Table Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 079) integrating Section 2.2 ("Escala Analítica de Madurez CMMI")
as a compact, high-value 5-level operational control reference table on Page 5 of Volume 1.
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
Role: Chief Corporate Governance Advisor, Executive Editorial Director, and Principal Systems Architect advising Global Fortune 500 Boards, CEOs, CFOs, and CIOs.

CONTEXT & PROBLEM STATEMENT:
In the Assessment Engine's Consolidated AS-IS Diagnostic deliverable (Volume 1 / Tomo 1), Chapter 2 evaluates the organization's technological maturity across 10 domains under standard CMMI (scoring from 1.00 to 5.00).

Currently, Chapter 2 suffers from a major pedagogical omission and layout asymmetry:
1. Pedagogical Omission: The report assigns scores (e.g., 2.64 / 5.00, 3.30, 2.14) and labels ("Nivel 2 (Repetible)", "Nivel 3 (Definido)"), but NOWHERE in the entire document is the analytical scale or operational control criteria explained. A C-suite reader has no objective reference to understand what separates Level 2 from Level 3, or what criteria are required to achieve Level 4 or Level 5.
2. Layout Asymmetry on Page 5:
   - Page 4 cleanly hosts Chapter 2 Heading, introductory paragraphs, Table 2 (10-Domain CMMI Evaluation Table), and methodological notes.
   - Page 5 hosts Figure 2.1 (10-axis Radar Chart) and two paragraphs analyzing the "two-speed architecture" (corporate core at Level 3 vs operational plants at Level 2).
   - However, the bottom half of Page 5 is completely empty whitespace because Chapter 3 starts on Page 6.

THE SOLUTION: SECTION 2.2 ON PAGE 5
To provide complete pedagogical closure and utilize Page 5 perfectly without breaking Table 2 on Page 4 or overflowing onto Page 6:
- Introduce Section 2.2 at the bottom of Page 5, immediately following the radar chart interpretation paragraphs:
  * Section Subheading: "2.2. Escala Analítica de Madurez CMMI" (and localized equivalents).
  * Introductory sentence explaining the continuous 0.8-interval analytical scale (1.00 to 5.00).
  * Compact 5-row reference table mapping:
    - Level 1 — Initial (1.00 - 1.80): Reactive, ad-hoc practices, total dependence on individual heroics of key staff.
    - Level 2 — Repeatable (1.80 - 2.60): Basic operational practices established at tactical level, with inconsistencies and silos between sites.
    - Level 3 — Defined (2.60 - 3.40): Formalized, documented, and standardized processes applied consistently enterprise-wide.
    - Level 4 — Managed (3.40 - 4.20): Quantitatively measured capabilities, telemetry, predictive control, full IT governance alignment.
    - Level 5 — Optimized (4.20 - 5.00): Operational excellence, advanced automation, continuous systematic improvement cycles.

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English.
   - Spanish exists strictly as data in `locales.json`.
2. ZERO HARDCODING:
   - No hardcoded client names ("MOLINS"), domain codes ("T4", "T5"), or vertical nouns in Python code or catalog templates.
   - The table must be universal for ANY enterprise in the world (banking, retail, manufacturing, utilities, logistics, health).
3. 6-LOCALE MATHEMATICAL SYMMETRY:
   - Symmetrical updates in `locales.json` across `es`, `en`, `pt`, `fr`, `de`, `ja`.
   - Numeric intervals (1.00 - 1.80, etc.) must be dynamically formatted or symmetrically declared.
4. STRICT PAGE 5 LAYOUT CONTAINMENT:
   - Page budget: Radar image height (max 220 pt), 2 paragraphs (~90 pt), Section 2.2 heading (~24 pt), intro (~22 pt), 5-row table (~110 pt), spacers (~30 pt) = ~496 pt <= 630 pt printable canvas.
   - Chapter 2 concludes strictly on Page 5 with a clean `PageBreakNode()`.
   - Chapter 3 starts strictly on Page 6.

DELIVERABLE:
Generate an authoritative, board-ready architectural blueprint in Markdown:
"RFC 079: CMMI Analytical Maturity Scale Table & Page 5 Balance Governance".

The RFC MUST include:
1. Executive Verdict & Layout Determinism Budget for Page 5.
2. Exact 6-Locale Localization Catalog for Section 2.2 across `es`, `en`, `pt`, `fr`, `de`, `ja`.
3. AST Construction Plan in `tomo_asis_ast_compiler.py` (`_build_chapter_2_maturity_radiography`).
4. Automated Quality Gate Test Specification (`tests/unit/test_rfc079_cmmi_scale_table.py`).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_079_CMMI_ANALYTICAL_SCALE_TABLE_GOVERNANCE_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 079 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
