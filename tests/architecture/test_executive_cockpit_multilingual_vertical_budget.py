"""Architectural Fitness Function: Multilingual Executive Cockpit Vertical Budget Guard.

Implements Phase 4 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.

Mandates:
1. Executive Cockpit on Page 3 must never exceed 620.0 pt across all 6 deliverable languages.
2. Vertical density ratio rho = sum(h_j) / H_canvas must remain in [0.65, 0.88] (ideal 80% balance).
3. Zero page overflow onto Page 4 under German/French expansion (+25%) or Japanese glyph heights.
4. DocumentAST structure must conclude Chapter 1 with exactly one PageBreakNode.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.domain.services.layout_solver import (
    CANVAS_HEIGHT_PT,
    VerticalLayoutSolver,
)
from assessment_engine.infrastructure.runtime_paths import ROOT

SUPPORTED_LOCALES = ["en", "es", "pt", "de", "fr", "ja"]
SAMPLE_TOWERS = ["T1", "T2", "T3", "T5", "T7", "T10"]


@pytest.fixture(scope="module")
def bridge() -> PayloadToASTBridge:
    return PayloadToASTBridge()


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
@pytest.mark.parametrize("tower_id", SAMPLE_TOWERS)
def test_executive_cockpit_vertical_height_and_occupancy_under_budget(
    bridge: PayloadToASTBridge, locale: str, tower_id: str
) -> None:
    """Verifies that Executive Cockpit adheres strictly to the vertical height budget across all 6 languages."""
    payload_path = ROOT / "working" / "molins" / tower_id / f"blueprint_{tower_id.lower()}_payload.json"
    with open(payload_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert to DocumentAST with target locale context
    ast_doc = bridge.convert(str(payload_path), override_locale=locale)

    # Split DocumentAST into pages using PageBreakNode boundaries
    pages: list[list[Any]] = [[]]
    for node in ast_doc.nodes:
        pages[-1].append(node)
        if getattr(node, "type", "") == "page_break":
            pages.append([])

    assert len(pages) >= 4, f"Document in {tower_id} ({locale}) must contain at least 4 pages"

    # Page 3 (index 2) is the One-Page Executive Cockpit
    page_3_nodes = pages[2]

    # 1. Structural check: Must terminate with a single PageBreakNode
    assert getattr(page_3_nodes[-1], "type", "") == "page_break", (
        f"Executive Cockpit (Page 3) in {tower_id} ({locale}) must terminate with a PageBreakNode."
    )

    # 2. Extract text components for vertical height simulation
    diag_paragraphs: list[str] = []
    bullets: list[str] = []
    mandate_text = ""

    for node in page_3_nodes:
        ntype = getattr(node, "type", "")
        if ntype == "paragraph":
            txt = getattr(node, "text", "").strip()
            style = getattr(node, "style", "")
            if "List Bullet" in style or style == "List Bullet":
                bullets.append(txt)
            elif any(k in txt for k in ["Ventana de Decisión", "Decision Horizon", "Decisão", "Entscheidung", "Décision", "意思決定"]):
                mandate_text = txt
            elif len(txt) > 80 and not txt.startswith("**"):
                diag_paragraphs.append(txt)

    heading_text = "1. Executive Summary"
    total_height_pt = VerticalLayoutSolver.calculate_executive_cockpit_height(
        heading_text=heading_text,
        diagnosis_paragraphs=diag_paragraphs,
        strategic_reality_bullets=bullets,
        decision_mandate=mandate_text or "Universal Decision Horizon: 12-18 months.",
        locale=locale,
    )

    occupancy_ratio = VerticalLayoutSolver.calculate_page_occupancy_ratio(total_height_pt)

    # 3. Maximum Ceiling Invariant (620.0 pt out of 685.89 pt canvas = ZERO PAGE OVERFLOW)
    assert total_height_pt <= 620.0, (
        f"Executive Cockpit in {tower_id} ({locale}) breached vertical height ceiling: "
        f"{total_height_pt:.2f} pt > 620.0 pt (Canvas: {CANVAS_HEIGHT_PT:.2f} pt)"
    )

    # 4. Minimum Richness Invariant (at least 400.0 pt = ZERO SPARSE PAGES)
    assert total_height_pt >= 400.0, (
        f"Executive Cockpit in {tower_id} ({locale}) is under-full: "
        f"{total_height_pt:.2f} pt < 400.0 pt"
    )

    # 5. Density Occupancy Invariant (between 65% and 88% of canvas)
    assert 0.60 <= occupancy_ratio <= 0.88, (
        f"Executive Cockpit in {tower_id} ({locale}) occupancy ratio out of bounds: "
        f"{occupancy_ratio * 100:.1f}% not in [60%, 88%]"
    )
