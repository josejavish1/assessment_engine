"""Unit tests for WCAG 2.1 Contrast Ratio Style Invariants (RFC-026 PR-2)."""

from __future__ import annotations

from assessment_engine.compiler.style_invariants import (
    EXECUTIVE_DARK_CHARCOAL,
    StyleInvariantGuard,
    contrast_ratio,
    relative_luminance,
)


def test_relative_luminance_extremes() -> None:
    # Pure white = 1.0
    assert abs(relative_luminance("FFFFFF") - 1.0) < 1e-4
    # Pure black = 0.0
    assert abs(relative_luminance("000000") - 0.0) < 1e-4


def test_contrast_ratio_black_and_white() -> None:
    # Maximum contrast is 21:1
    cr = contrast_ratio("FFFFFF", "000000")
    assert abs(cr - 21.0) < 0.1


def test_white_on_white_overridden_to_charcoal() -> None:
    # #FFFFFF on #FFFFFF has CR = 1.0, must be overridden to #111827
    safe_fg = StyleInvariantGuard.enforce_safe_foreground("FFFFFF", "FFFFFF")
    assert safe_fg == EXECUTIVE_DARK_CHARCOAL


def test_white_on_none_background_overridden_to_charcoal() -> None:
    # #FFFFFF on None (white) must be overridden to #111827
    safe_fg = StyleInvariantGuard.enforce_safe_foreground("FFFFFF", None)
    assert safe_fg == EXECUTIVE_DARK_CHARCOAL


def test_white_on_dark_navy_preserved() -> None:
    # #FFFFFF on #0F172A has CR ~ 16.5:1, passes contrast and is preserved
    safe_fg = StyleInvariantGuard.enforce_safe_foreground("FFFFFF", "0F172A")
    assert safe_fg == "FFFFFF"
