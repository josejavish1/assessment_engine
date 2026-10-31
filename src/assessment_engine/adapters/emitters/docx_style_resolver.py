"""Translates W3C Semantic Design Tokens into OpenXML/Word primitives at compile time (RFC-028).

Eliminates hardcoded RGBColor and Pt calls across compilers and ensures full CJK / RTL font resolution.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from assessment_engine.domain.theme_registry import (
    ScriptType,
    SemanticColorRole,
    TenantThemeManifest,
    ThemeRegistry,
    TypographyRole,
)

logger = logging.getLogger(__name__)


class DocxStyleResolver:
    """Translates W3C Semantic Tokens into OpenXML primitives at compile time."""

    _default_resolver: ClassVar[DocxStyleResolver | None] = None

    def __init__(self, theme: TenantThemeManifest, language_code: str = "en") -> None:
        """Initialize style resolver with active tenant theme manifest and locale code."""
        self.theme = theme
        self.language_code = str(language_code).strip().lower().split("_")[0].split("-")[0]
        self.script = self._resolve_script(self.language_code)

    @classmethod
    def get_default(cls, language_code: str = "en") -> DocxStyleResolver:
        """Retrieve default singleton instance of DocxStyleResolver."""
        if cls._default_resolver is None:
            theme = ThemeRegistry.get_theme()
            cls._default_resolver = cls(theme=theme, language_code=language_code)
        return cls._default_resolver

    @staticmethod
    def _resolve_script(lang_base: str) -> ScriptType:
        """Classify ISO language into primary script category."""
        if lang_base in ("ja", "zh", "ko"):
            return ScriptType.CJK
        if lang_base in ("ar", "he", "fa", "ur"):
            return ScriptType.ARABIC
        if lang_base in ("ru", "uk", "bg", "sr"):
            return ScriptType.CYRILLIC
        return ScriptType.LATIN

    def apply_paragraph_typography(self, paragraph: Any, role: TypographyRole) -> None:
        """Apply spatial spacing and line-height tokens to a DOCX paragraph."""
        typo_token = self.theme.typography.get(role)
        if not typo_token:
            return
        pf = paragraph.paragraph_format
        pf.space_before = Pt(typo_token.space_before.points)
        pf.space_after = Pt(typo_token.space_after.points)
        pf.line_spacing = typo_token.line_height_multiplier

    def apply_run_typography(
        self,
        run: Any,
        role: TypographyRole,
        color_override: SemanticColorRole | None = None,
    ) -> None:
        """Apply font metrics, semantic color, and multi-script font stack to a DOCX run."""
        typo_token = self.theme.typography.get(role)
        if not typo_token:
            return

        color_role = color_override or typo_token.color_role
        hex_token = self.theme.colors.get(color_role)

        # 1. Dimensions & Formatting Weights
        run.font.size = Pt(typo_token.font_size.points)
        run.font.bold = typo_token.is_bold
        run.font.italic = typo_token.is_italic
        run.font.all_caps = typo_token.is_uppercase

        # 2. Semantic Color Resolution
        if hex_token:
            r, g, b = hex_token.rgb_tuple
            run.font.color.rgb = RGBColor(r, g, b)

        # 3. Multi-Script OpenXML Font Matrix (Latin, Cyrillic, CJK, and RTL/Arabic)
        font_stack = self.theme.font_stack
        primary_font = font_stack.resolve_for_script(
            self.script, is_mono=typo_token.is_monospace
        )

        run.font.name = primary_font
        try:
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                rPr.insert(0, rFonts)

            rFonts.set(qn("w:ascii"), primary_font)
            rFonts.set(qn("w:hAnsi"), primary_font)
            rFonts.set(
                qn("w:eastAsia"),
                font_stack.monospace if typo_token.is_monospace else font_stack.cjk,
            )
            rFonts.set(
                qn("w:cs"),
                font_stack.monospace if typo_token.is_monospace else font_stack.arabic,
            )

            if self.script == ScriptType.ARABIC and rPr.find(qn("w:rtl")) is None:
                rPr.append(OxmlElement("w:rtl"))
        except Exception as ex:
            logger.debug("Failed setting OpenXML rFonts XML element: %s", ex)

    def apply_run_style(
        self,
        run: Any,
        typo_role: TypographyRole = TypographyRole.BODY_REGULAR,
        color_role: SemanticColorRole | None = None,
        bold_override: bool | None = None,
    ) -> None:
        """Convenience method applying typography, color, and optional bold override."""
        self.apply_run_typography(run, role=typo_role, color_override=color_role)
        if bold_override is not None:
            run.font.bold = bold_override

    def resolve_rgb(self, role: SemanticColorRole) -> RGBColor:
        """Return native docx RGBColor instance for semantic role."""
        r, g, b = self.resolve_rgb_tuple(role)
        return RGBColor(r, g, b)

    def resolve_hex(self, role: SemanticColorRole) -> str:
        """Alias for resolve_hex_string returning raw hex string."""
        return self.resolve_hex_string(role)

    def resolve_pt(self, role: TypographyRole) -> Pt:
        """Return native docx Pt dimension for typography role."""
        typo_token = self.theme.typography.get(role)
        if typo_token:
            return Pt(typo_token.font_size.points)
        return Pt(10.0)

    def resolve_hex_string(self, role: SemanticColorRole) -> str:
        """Return raw 6-character hex string for OpenXML shading and borders."""
        token = self.theme.colors.get(role) or ThemeRegistry.get_theme().colors[role]
        return token.raw_hex

    def resolve_rgb_tuple(self, role: SemanticColorRole) -> tuple[int, int, int]:
        """Return integer RGB 3-tuple for semantic role."""
        token = self.theme.colors.get(role) or ThemeRegistry.get_theme().colors[role]
        return token.rgb_tuple
