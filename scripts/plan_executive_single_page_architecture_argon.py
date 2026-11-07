#!/usr/bin/env python3
"""Executive Single-Page Portfolio Snapshot Architecture Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 077) transforming Volume 1 Chapter 1 into a pure,
single-page, zero-redundancy Executive Portfolio Snapshot for Fortune 500 C-suites.
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
In the Assessment Engine's Consolidated AS-IS Diagnostic deliverable (Volume 1 / Tomo 1), Chapter 1 (Executive Summary) currently suffers from three critical architectural and design defects:

1. Redundant Information & Two-Page Sprawl:
   - Chapter 1 currently spans across multiple pages or risks vertical overflow because it stacks:
     (a) Cockpit Table (Global Score, Maturity Band, Annual Exposure ALE).
     (b) Legacy Triad Table ("Capacidad Consolidada", "Limitación de Capacidad", "Cuello de Botella Estructural").
     (c) Headline & Overview Paragraphs.
     (d) Strategic Challenge Bullets.
     (e) 3-Pillar Economic Quantification.
   - The Legacy Triad Table is completely redundant: it describes generic facility, compute memory, and manual support issues in static prose that repeats almost verbatim what the Strategic Bullets say 5 centimeters below it!

2. Semi-Hardcoded Prose & Fragility:
   - In `locales.json`, the triad table descriptions (`tomo_triad_strength_desc`, `tomo_triad_gap_desc`, `tomo_triad_bottleneck_desc`) are static strings assuming on-premise physical datacenters and memory pressure. A cloud-native bank or digital platform would receive irrelevant physical hardware prose.
   - In `tomo_ch1_p1`, the CMMI level string is hardcoded in Spanish (`"(Nivel 2 CMMI — Repetible)"`), which breaks if a client achieves Level 3, 4, or 5.
   - In `tomo_ch1_p1`, the domain count is hardcoded (`"los diez dominios tecnológicos"`), which breaks if a tenant assesses 6, 8, or 12 domains.

3. The Boardroom / CIO Standard: A Pristine Single-Page Executive Snapshot:
   - An executive summary in a flagship Tier-1 advisory deliverable must stand strictly on EXACTLY ONE PAGE (Page 3 of the deliverable, between the TOC on Page 2 and Chapter 2 on Page 4).
   - It must provide 4 visually structured, non-redundant blocks scannable in 30 seconds:
     Block 1: Top Cockpit Strip (Global Score, CMMI Level, Annual Exposure ALE).
     Block 2: Portfolio Polarity & Extremes Radiography (replacing the redundant triad table with pure mathematical domain extremes dynamically computed from SSOT):
       * Maturity Leader Domain: `{leader_code} - {leader_name} ({leader_score} / 5.00)`
       * Financial Risk Concentration: `{top_risk_code} - {top_risk_name} ({top_risk_ale} / year — {top_risk_share_pct}%)`
       * Modernization Urgency / Lowest Maturity: `{lagging_code} - {lagging_name} ({lagging_score} / 5.00)`
     Block 3: Top Strategic Business Challenges (extracted dynamically from `burning_platform`).
     Block 4: Actuarial Financial Quantification (Open FAIR™ 3-pillar breakdown: Annual ALE, Single Worst Incident Outage, Portfolio Crisis P90).

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English.
   - Spanish exists strictly as data in `locales.json`.
2. ZERO HARDCODING:
   - No hardcoded client names ("MOLINS"), domain codes ("T4", "T5"), or scores ("3.30", "2.14") in Python source code.
   - Domain polarity (leader, top risk, lagging domain) MUST be dynamically computed at runtime across any N-domain topology.
3. STRICT SINGLE-PAGE BUDGET (OPENXML / AST DETERMINISM):
   - Chapter 1 MUST fit strictly on Page 3 without overflowing onto Page 4 under standard LibreOffice / Microsoft Word rendering.
   - Define exact point budgets for typography, cell paddings, and spacers.
4. MATHEMATICAL SYMMETRY ACROSS ALL 6 LOCALES:
   - Symmetrical updates in `locales.json` across `es`, `en`, `pt`, `fr`, `de`, `ja`.

DELIVERABLE:
Generate an authoritative, board-ready architectural blueprint in Markdown:
"RFC 077: Executive Single-Page Portfolio Snapshot & Polarity Governance".

The RFC MUST include:
1. Executive Verdict & Layout Determinism Analysis.
2. Dynamic Domain Polarity Algorithms (`_compute_portfolio_polarity_extremes`).
3. Exact Refactored Localization Catalogs for `locales.json` across all 6 locales (es, en, pt, fr, de, ja).
4. Concrete AST Implementation Plan for `tomo_asis_ast_compiler.py` (Block 1, Block 2 Polarity Table, Block 3 Strategic Challenges, Block 4 Financial Quantification).
5. Automated Quality Gate Test Specification (`tests/unit/test_rfc077_executive_snapshot_governance.py`).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_077_EXECUTIVE_SINGLE_PAGE_PORTFOLIO_SNAPSHOT_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 077 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
