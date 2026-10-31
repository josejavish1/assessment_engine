"""WCAG 2.1 Relative Luminance and Contrast Ratio Enforcement for AST Document Synthesis.

Adheres strictly to Invariant II of RFC-026:
- Zero invisible white-on-white text.
- Formal WCAG 2.1 relative luminance and contrast ratio calculations.
- Automatic fallback to Executive Dark Charcoal (#111827) on light/unspecified backgrounds.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

EXECUTIVE_DARK_CHARCOAL: str = "111827"
EXECUTIVE_NAVY_DARK: str = "0F172A"
PURE_WHITE: str = "FFFFFF"


def _parse_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Parse 6-character hex string into normalized RGB float components [0.0, 1.0]."""
    clean_hex = hex_color.strip().lstrip("#").upper()
    if len(clean_hex) != 6:
        clean_hex = EXECUTIVE_DARK_CHARCOAL
    try:
        r = int(clean_hex[0:2], 16) / 255.0
        g = int(clean_hex[2:4], 16) / 255.0
        b = int(clean_hex[4:6], 16) / 255.0
        return r, g, b
    except ValueError:
        return 0.067, 0.094, 0.153  # Fallback to #111827


def relative_luminance(hex_color: str) -> float:
    """Compute exact WCAG 2.1 relative luminance for an sRGB color."""
    r, g, b = _parse_rgb(hex_color)

    def channel_linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_lin = channel_linear(r)
    g_lin = channel_linear(g)
    b_lin = channel_linear(b)

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Compute the WCAG 2.1 contrast ratio between two hex colors (range [1.0, 21.0])."""
    lum_a = relative_luminance(hex_a)
    lum_b = relative_luminance(hex_b)
    l_light = max(lum_a, lum_b)
    l_dark = min(lum_a, lum_b)
    return (l_light + 0.05) / (l_dark + 0.05)


class StyleInvariantGuard:
    """Enforces typographic and contrast invariants during AST document lowering."""

    @staticmethod
    def enforce_safe_foreground(
        fg_hex: str,
        bg_hex: Optional[str] = None,
        min_contrast: float = 4.5,
    ) -> str:
        """Verify that foreground color achieves at least `min_contrast` against background.

        If background is None, 'auto', or 'clear', it is treated as pure white (#FFFFFF).
        If the combination yields contrast below `min_contrast` (e.g. #FFFFFF on #FFFFFF),
        this function safely overrides the foreground to Executive Dark Charcoal (#111827).
        """
        clean_fg = fg_hex.strip().lstrip("#").upper()
        clean_bg = bg_hex.strip().lstrip("#").upper() if bg_hex and bg_hex.lower() not in ("auto", "clear", "none") else PURE_WHITE

        cr = contrast_ratio(clean_fg, clean_bg)
        if cr >= min_contrast:
            return clean_fg

        # Contrast violated (e.g., white text on white/light background)
        logger.warning(
            "WCAG 2.1 Contrast Violation: #%s on #%s yields CR=%.2f:1 (required %.1f:1). Overriding to #%s.",
            clean_fg,
            clean_bg,
            cr,
            min_contrast,
            EXECUTIVE_DARK_CHARCOAL,
        )
        return EXECUTIVE_DARK_CHARCOAL
