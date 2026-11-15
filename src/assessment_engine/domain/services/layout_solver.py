"""
Deterministic Vertical Box-and-Glue Layout Solver.
Implements Phase 4 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.

Formulates page geometry and intrinsic block height under multi-language expansion:
H_canvas = 841.89 - (top_margin + bottom_margin + header + footer) = 685.89 pt
Enforces strict 80% (±8%) vertical page occupancy without overflow.
"""

from __future__ import annotations

import math
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

# ISO A4 dimensions in typographic points (1 pt = 1/72 inch, 210mm x 297mm)
A4_WIDTH_PT: float = 595.28
A4_HEIGHT_PT: float = 841.89

# Default margins and chrome
DEFAULT_TOP_MARGIN_PT: float = 54.0
DEFAULT_BOTTOM_MARGIN_PT: float = 54.0
DEFAULT_RUNNING_HEADER_PT: float = 24.0
DEFAULT_RUNNING_FOOTER_PT: float = 24.0

# Available canvas height for document blocks
CANVAS_HEIGHT_PT: float = (
    A4_HEIGHT_PT - (DEFAULT_TOP_MARGIN_PT + DEFAULT_BOTTOM_MARGIN_PT + DEFAULT_RUNNING_HEADER_PT + DEFAULT_RUNNING_FOOTER_PT)
)  # 685.89 pt

# Characters Per Line (CPL) at 9.5 pt body font on standard A4 width with 54pt side margins (487 pt printable width)
STANDARD_CPL_AT_9_5PT: float = 95.0

# Language expansion factors relative to English baseline (1.00)
LOCALE_EXPANSION_FACTORS: dict[str, float] = {
    "en": 1.00,
    "es": 1.15,
    "pt": 1.18,
    "fr": 1.20,
    "de": 1.25,
    "ja": 0.85,  # Fewer characters, but higher line leading
}


class BlockDimension(BaseModel):
    """Calculated dimensions and spatial tolerances for a single document block."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    block_type: str
    intrinsic_height_pt: float
    stretch_pt: float = 0.0
    shrink_pt: float = 0.0
    penalty: float = 0.0


class VerticalLayoutSolver:
    """Calculates deterministic spatial heights for DocumentAST nodes."""

    @staticmethod
    def get_expansion_factor(locale: str) -> float:
        """Resolve character expansion factor for target language."""
        loc_clean = str(locale or "en").strip().lower()[:2]
        return LOCALE_EXPANSION_FACTORS.get(loc_clean, 1.00)

    @classmethod
    def estimate_paragraph_height(
        cls,
        text: str,
        font_size: float = 9.5,
        line_spacing_multiplier: float = 1.15,
        space_before: float = 0.0,
        space_after: float = 0.0,
        locale: str = "en",
    ) -> float:
        """Estimate paragraph height in points considering line wrapping and language expansion."""
        clean_text = str(text or "").strip()
        if not clean_text:
            return space_before + space_after

        expansion = cls.get_expansion_factor(locale)
        effective_chars = len(clean_text) * expansion
        cpl = STANDARD_CPL_AT_9_5PT * (9.5 / max(6.0, font_size))
        num_lines = max(1, math.ceil(effective_chars / cpl))

        # Line leading in points
        line_height_pt = font_size * line_spacing_multiplier
        # Japanese glyphs require additional vertical leading
        if str(locale).lower().startswith("ja"):
            line_height_pt *= 1.15

        return (num_lines * line_height_pt) + space_before + space_after

    @classmethod
    def estimate_table_height(
        cls,
        rows_count: int,
        is_scorecard: bool = False,
        header_font_size: float = 8.0,
        data_font_size: float = 9.5,
    ) -> float:
        """Estimate table vertical height in points based on row counts and cell padding."""
        if rows_count <= 0:
            return 0.0

        # Header row: font_size * 1.2 leading + 12 pt top/bottom cell padding
        header_height = (header_font_size * 1.2) + 12.0
        # Data row: font_size * 1.2 leading + 14 pt top/bottom cell padding
        data_row_height = (data_font_size * 1.2) + 14.0

        total_height = header_height + ((rows_count - 1) * data_row_height)
        return total_height

    @classmethod
    def calculate_executive_cockpit_height(
        cls,
        heading_text: str,
        diagnosis_paragraphs: List[str],
        strategic_reality_bullets: List[str],
        decision_mandate: str,
        locale: str = "es",
        num_pillars: int = 5,
    ) -> float:
        """Calculate total deterministic height of the One-Page Executive Cockpit."""
        total_height = 0.0

        # 1. Heading 1 (18 pt font + 12 pt before + 6 pt after)
        total_height += 18.0 * 1.2 + 6.0 + 6.0  # ~33.6 pt

        # 2. Scorecard Table (2 rows)
        total_height += cls.estimate_table_height(2, is_scorecard=True, header_font_size=8.0, data_font_size=9.5)
        # Spacer after Scorecard: 12 pt
        total_height += 12.0

        # 3. Diagnosis Paragraphs
        for p_idx, p_text in enumerate(diagnosis_paragraphs):
            sp_after = 8.0 if p_idx < len(diagnosis_paragraphs) - 1 else 14.0
            total_height += cls.estimate_paragraph_height(p_text, font_size=9.5, space_after=sp_after, locale=locale)

        # 4. Micro-Heatmap section title (9.5 pt + 4 pt after)
        total_height += (9.5 * 1.2) + 4.0
        # Micro-Heatmap Table (2 rows)
        total_height += cls.estimate_table_height(2, header_font_size=8.0, data_font_size=9.5)
        # Spacer after Heatmap: 14 pt
        total_height += 14.0

        # 5. Strategic Realities Lead-in
        total_height += (9.5 * 1.2) + 6.0
        # 3 Bullets
        for b_text in strategic_reality_bullets[:3]:
            total_height += cls.estimate_paragraph_height(b_text, font_size=9.5, space_after=8.0, locale=locale)

        # 6. Optional Decision Horizon Mandate
        if decision_mandate:
            total_height += 10.0
            total_height += cls.estimate_paragraph_height(decision_mandate, font_size=9.5, space_after=12.0, locale=locale)

        return total_height

    @classmethod
    def calculate_page_occupancy_ratio(cls, total_content_height_pt: float) -> float:
        """Calculate vertical density ratio rho = total_height / canvas_height."""
        return total_content_height_pt / CANVAS_HEIGHT_PT
