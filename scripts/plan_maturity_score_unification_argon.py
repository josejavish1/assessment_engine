#!/usr/bin/env python3
"""Maturity Score SSOT Unification Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 075) eradicating the maturity score split-brain between
the Consolidated Volume 1 diagnostic report and the Specialist Annex deliverables.
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
Role: Chief Software Architect and Principal Actuarial Systems Auditor at a Top-Tier Global Advisory Firm (McKinsey / Gartner / NTT DATA).

CONTEXT & PROBLEM STATEMENT:
In the Assessment Engine deliverable suite, a severe architectural split-brain defect was uncovered between the Consolidated AS-IS Diagnostic (Volume 1 / Tomo 1) and the Specialist Annexes (T1 to T10):

1. The Split-Brain Defect:
   - In Volume 1 (Chapter 2, Table 2 and Chapter 4 domain cards), Tower 3 (Redes & WAN) is reported with a maturity score of 2.52 / 5.00 (calculated from its 5 pillar scores [3.8, 2.2, 2.3, 2.3, 2.0] / 5 = 2.52).
   - In Specialist Annex 03 (Molins_202610_Anexo_03_Redes_ASIS.docx), the cover page, Chapter 1 executive summary, and Chapter 3 maturity dashboard ALL report a score of 3.00 / 5.00!
   - Investigation reveals that Specialist Annexes T3 through T10 ALL report 3.00 / 5.00, while Volume 1 reports their true mathematical scores:
     * T1: 2.56 in Vol 1 vs 2.61 in Annex 01 (slight weighted vs simple average discrepancy)
     * T2: 2.46 in Vol 1 vs 2.46 in Annex 02
     * T3: 2.52 in Vol 1 vs 3.00 in Annex 03
     * T4: 3.30 in Vol 1 vs 3.00 in Annex 04
     * T5: 2.14 in Vol 1 vs 3.00 in Annex 05
     * T6: 2.80 in Vol 1 vs 3.00 in Annex 06
     * T7: 2.60 in Vol 1 vs 3.00 in Annex 07
     * T8: 2.42 in Vol 1 vs 3.00 in Annex 08
     * T9: 3.14 in Vol 1 vs 3.00 in Annex 09
     * T10: 2.38 in Vol 1 vs 3.00 in Annex 10

2. Root Cause Analysis:
   - In `payload_to_ast.py` (_extract_conversion_context, lines 515-525), the annex compiler searches for a physical file `scoring_output.json` inside the case directory.
   - `scoring_output.json` only exists on disk for T1 and T2. For T3 through T10, this file does NOT exist.
   - When `scoring_output.json` is missing, `payload_to_ast.py` falls back to:
     `blueprint_data.get("executive_summary", {}).get("global_score", "3.0").split()[0]`
   - Because `blueprint_data.get("executive_summary")` is `None` in the hydrated payloads for T3..T10, it evaluated to the hardcoded default string `"3.0"`!
   - This caused every annex from T3 to T10 to display 3.00 / 5.00, creating an unacceptable contradiction with Volume 1.

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English. Zero Spanish words in Python source files.
   - Spanish exists strictly as data in `locales.json`.
2. ZERO HARDCODING:
   - No hardcoded scores (e.g. no `"3.0"`, no static fallback numbers).
   - No hardcoded tenant names (no "Molins", no "Secil"). Must work for ANY multinational enterprise (50M€ to 50B€, any vertical, any currency).
3. SINGLE SOURCE OF TRUTH (SSOT) UNIFICATION:
   - Mathematical scores must be 100% identical between Volume 1 and all Specialist Annexes.
   - Design a unified canonical score calculation in `TowerPayloadHydrator` and ensure both `payload_to_ast.py` and `tomo_asis_ast_compiler.py` consume the exact same score.
   - If weighted scoring exists in `scoring_output.json` or blueprint metadata, both Volume 1 and the Annex must use it; otherwise, both must use the exact weighted/arithmetic average of `pillars_analysis`.
4. THREAD-SAFETY & STATELESS COMPILATION:
   - No global mutable state. Clean, pure functions.

DELIVERABLE:
Generate a comprehensive, board-ready architectural specification in Markdown:
"RFC 075: Maturity Score Single Source of Truth (SSOT) & Cross-Deliverable Convergence".

The RFC MUST include:
1. Executive Verdict & Root Cause Formalization.
2. Production Code Blueprint:
   - Enhancements to `TowerPayloadHydrator.load_and_hydrate_all_towers` to compute and attach canonical scores to every tower payload.
   - Modifications to `payload_to_ast.py` to eradicate the `"3.0"` fallback and resolve scores strictly from SSOT.
   - Modifications to `tomo_asis_ast_compiler.py` to ensure Volume 1 consumes the exact same canonical score.
3. Cross-Deliverable Mathematical Verification Matrix (T1 to T10 expected scores).
4. Automated Quality Gate Test Specification (`tests/unit/test_rfc075_score_convergence.py`).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_075_MATURITY_SCORE_SSOT_UNIFICATION_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 075 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
