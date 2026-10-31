"""W3C-Compliant Hierarchical Design Token and Theme Engine (RFC-028 / Split-Brain #3).

Eliminates hardcoded styling primitives (RGBColor, Pt, fixed fonts) from business logic
and provides internationalized font stack matrices for CJK, Arabic, and Latin scripts.
"""

from __future__ import annotations

from enum import Enum
import re
from threading import RLock
from typing import ClassVar
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

HEX_COLOR_REGEX = re.compile(r"^#([A-Fa-f0-9]{6})$")


class ScriptType(str, Enum):
    """ISO 15924 Script classifications for international typography."""

    LATIN = "latin"
    CJK = "cjk"          # Chinese, Japanese, Korean
    ARABIC = "arabic"    # RTL scripts (Arabic, Hebrew)
    CYRILLIC = "cyrillic"


class SemanticColorRole(str, Enum):
    """W3C Semantic Color Intents."""

    BRAND_PRIMARY = "brand.primary"
    BRAND_SECONDARY = "brand.secondary"
    BRAND_ACCENT = "brand.accent"
    SURFACE_PRIMARY = "surface.primary"
    SURFACE_SECONDARY = "surface.secondary"
    SURFACE_INVERSE = "surface.inverse"
    SURFACE_BACKGROUND = "surface.background"
    SURFACE_ALT_ROW = "surface.alt_row"
    SURFACE_HEADER = "surface.header"
    TEXT_PRIMARY = "text.primary"
    TEXT_SECONDARY = "text.secondary"
    TEXT_MUTED = "text.muted"
    TEXT_INVERSE = "text.inverse"
    BORDER_DEFAULT = "border.default"
    BORDER_SUBTLE = "border.subtle"
    BORDER_STRONG = "border.strong"
    STATUS_OPTIMAL = "status.optimal"
    STATUS_HIGH = "status.high"
    STATUS_CRITICAL = "status.critical"
    STATUS_WARNING = "status.warning"
    STATUS_SUCCESS = "status.success"
    STATUS_INFO = "status.info"

    # FAIR Risk Heatmap Backgrounds (Matrix Cells)
    RISK_HEATMAP_LOW_BG = "risk.heatmap.low.bg"
    RISK_HEATMAP_MEDIUM_BG = "risk.heatmap.medium.bg"
    RISK_HEATMAP_HIGH_BG = "risk.heatmap.high.bg"
    RISK_HEATMAP_CRITICAL_BG = "risk.heatmap.critical.bg"
    RISK_HEATMAP_EXTREME_BG = "risk.heatmap.extreme.bg"

    # FAIR Risk Heatmap Foregrounds (Contrast-safe text over Heatmap BG)
    RISK_HEATMAP_DARK_TEXT = "risk.heatmap.dark.text"
    RISK_HEATMAP_LIGHT_TEXT = "risk.heatmap.light.text"

    # Data Visualization (Charts / Radar)
    CHART_SERIES_PRIMARY = "chart.series.primary"
    CHART_SERIES_SECONDARY = "chart.series.secondary"
    CHART_GRIDLINE = "chart.gridline"


class TypographyRole(str, Enum):
    """W3C Semantic Typography Intents."""

    DISPLAY = "typography.display"
    HEADING_1 = "typography.heading.h1"
    HEADING_2 = "typography.heading.h2"
    HEADING_3 = "typography.heading.h3"
    HEADING_4 = "typography.heading.h4"
    BODY_REGULAR = "typography.body.regular"
    BODY_STRONG = "typography.body.strong"
    CAPTION = "typography.caption"
    MONOSPACE = "typography.monospace"
    TABLE_HEADER = "typography.table.header"
    TABLE_CELL = "typography.table.cell"


class HexColorToken(BaseModel):
    """Primitive Color Token with format enforcement and RGB extraction."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    value: str = Field(..., description="6-digit hexadecimal color starting with #")

    @field_validator("value")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        if not HEX_COLOR_REGEX.match(v):
            raise ValueError(f"Invalid hex color token: '{v}'. Expected #RRGGBB format.")
        return v.upper()

    @property
    def rgb_tuple(self) -> tuple[int, int, int]:
        """Convert hexadecimal color to integer RGB 3-tuple."""
        hex_str = self.value.lstrip("#")
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))

    @property
    def raw_hex(self) -> str:
        """Return 6-character uppercase hex string without leading hash."""
        return self.value.lstrip("#")


class FontStackToken(BaseModel):
    """Internationalized font family matrix supporting multi-script glyph rendering."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    latin: str = Field(default="Arial")
    cjk: str = Field(default="Noto Sans CJK SC")
    arabic: str = Field(default="Noto Sans Arabic")
    cyrillic: str = Field(default="Arial")
    monospace: str = Field(default="Consolas")

    def resolve_for_script(self, script: ScriptType, is_mono: bool = False) -> str:
        """Resolve primary font family based on script classification."""
        if is_mono:
            return self.monospace
        return getattr(self, script.value)


class DimensionToken(BaseModel):
    """Primitive Spatial Token in typographic points (pt)."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    points: float = Field(..., gt=0.0)


class TypographyCompositeToken(BaseModel):
    """W3C Composite Token binding font metrics and semantic colors."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    font_size: DimensionToken
    line_height_multiplier: float = Field(default=1.15, gt=0.5)
    space_before: DimensionToken = Field(default=DimensionToken(points=0.01))
    space_after: DimensionToken = Field(default=DimensionToken(points=4.0))
    is_bold: bool = False
    is_italic: bool = False
    is_uppercase: bool = False
    is_monospace: bool = False
    color_role: SemanticColorRole = SemanticColorRole.TEXT_PRIMARY


class TenantThemeManifest(BaseModel):
    """Complete Multi-Tenant Design System Manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    theme_id: str
    tenant_name: str
    font_stack: FontStackToken
    colors: dict[SemanticColorRole, HexColorToken]
    typography: dict[TypographyRole, TypographyCompositeToken]

    @model_validator(mode="after")
    def validate_complete_token_coverage(self) -> TenantThemeManifest:
        """Ensure every semantic color and typography role is defined without gaps."""
        missing_colors = set(SemanticColorRole) - set(self.colors.keys())
        if missing_colors:
            raise ValueError(f"Theme '{self.theme_id}' is missing color roles: {missing_colors}")
        missing_typo = set(TypographyRole) - set(self.typography.keys())
        if missing_typo:
            raise ValueError(f"Theme '{self.theme_id}' is missing typography roles: {missing_typo}")
        return self


class ThemeRegistry:
    """Thread-safe Central Registry for Tenant Design Systems."""

    _lock: ClassVar[RLock] = RLock()
    _themes: ClassVar[dict[str, TenantThemeManifest]] = {}
    _default_theme_id: ClassVar[str] = "global_enterprise_default"

    @classmethod
    def register_theme(cls, manifest: TenantThemeManifest) -> None:
        """Register a validated tenant theme manifest into the registry."""
        with cls._lock:
            cls._themes[manifest.theme_id] = manifest

    @classmethod
    def get_theme(cls, theme_id: str | None = None) -> TenantThemeManifest:
        """Retrieve theme by ID, falling back to global enterprise default."""
        with cls._lock:
            if cls._default_theme_id not in cls._themes:
                cls._bootstrap_default_theme()
            target_id = theme_id or cls._default_theme_id
            return cls._themes.get(target_id, cls._themes[cls._default_theme_id])

    @classmethod
    def _bootstrap_default_theme(cls) -> None:
        """Bootstrap default corporate theme manifest adhering to Tier-1 design standards."""
        default_colors = {
            SemanticColorRole.BRAND_PRIMARY: HexColorToken(value="#0072BC"),
            SemanticColorRole.BRAND_SECONDARY: HexColorToken(value="#1E293B"),
            SemanticColorRole.BRAND_ACCENT: HexColorToken(value="#0284C7"),
            SemanticColorRole.SURFACE_PRIMARY: HexColorToken(value="#FFFFFF"),
            SemanticColorRole.SURFACE_SECONDARY: HexColorToken(value="#F8FAFC"),
            SemanticColorRole.SURFACE_INVERSE: HexColorToken(value="#0F172A"),
            SemanticColorRole.TEXT_PRIMARY: HexColorToken(value="#0F172A"),
            SemanticColorRole.TEXT_SECONDARY: HexColorToken(value="#334155"),
            SemanticColorRole.TEXT_MUTED: HexColorToken(value="#64748B"),
            SemanticColorRole.TEXT_INVERSE: HexColorToken(value="#FFFFFF"),
            SemanticColorRole.BORDER_DEFAULT: HexColorToken(value="#CBD5E1"),
            SemanticColorRole.BORDER_STRONG: HexColorToken(value="#475569"),
            SemanticColorRole.STATUS_CRITICAL: HexColorToken(value="#DC2626"),
            SemanticColorRole.STATUS_WARNING: HexColorToken(value="#D97706"),
            SemanticColorRole.STATUS_SUCCESS: HexColorToken(value="#16A34A"),
            SemanticColorRole.STATUS_INFO: HexColorToken(value="#2563EB"),
            SemanticColorRole.SURFACE_BACKGROUND: HexColorToken(value="#FFFFFF"),
            SemanticColorRole.SURFACE_ALT_ROW: HexColorToken(value="#F8FAFC"),
            SemanticColorRole.SURFACE_HEADER: HexColorToken(value="#0072BC"),
            SemanticColorRole.BORDER_SUBTLE: HexColorToken(value="#E2E8F0"),
            SemanticColorRole.STATUS_OPTIMAL: HexColorToken(value="#16A34A"),
            SemanticColorRole.STATUS_HIGH: HexColorToken(value="#EA580C"),
            SemanticColorRole.RISK_HEATMAP_LOW_BG: HexColorToken(value="#D9F2D9"),
            SemanticColorRole.RISK_HEATMAP_MEDIUM_BG: HexColorToken(value="#FFFF00"),
            SemanticColorRole.RISK_HEATMAP_HIGH_BG: HexColorToken(value="#FFC000"),
            SemanticColorRole.RISK_HEATMAP_CRITICAL_BG: HexColorToken(value="#FF0000"),
            SemanticColorRole.RISK_HEATMAP_EXTREME_BG: HexColorToken(value="#C00000"),
            SemanticColorRole.RISK_HEATMAP_DARK_TEXT: HexColorToken(value="#000000"),
            SemanticColorRole.RISK_HEATMAP_LIGHT_TEXT: HexColorToken(value="#FFFFFF"),
            SemanticColorRole.CHART_SERIES_PRIMARY: HexColorToken(value="#0072BC"),
            SemanticColorRole.CHART_SERIES_SECONDARY: HexColorToken(value="#0284C7"),
            SemanticColorRole.CHART_GRIDLINE: HexColorToken(value="#E2E8F0"),
        }
        default_typography = {
            TypographyRole.DISPLAY: TypographyCompositeToken(
                font_size=DimensionToken(points=24.0),
                is_bold=True,
                space_after=DimensionToken(points=12.0),
                color_role=SemanticColorRole.BRAND_PRIMARY,
            ),
            TypographyRole.HEADING_1: TypographyCompositeToken(
                font_size=DimensionToken(points=16.0),
                is_bold=True,
                space_before=DimensionToken(points=14.0),
                space_after=DimensionToken(points=6.0),
                color_role=SemanticColorRole.BRAND_PRIMARY,
            ),
            TypographyRole.HEADING_2: TypographyCompositeToken(
                font_size=DimensionToken(points=13.0),
                is_bold=True,
                space_before=DimensionToken(points=10.0),
                space_after=DimensionToken(points=4.0),
                color_role=SemanticColorRole.BRAND_SECONDARY,
            ),
            TypographyRole.HEADING_3: TypographyCompositeToken(
                font_size=DimensionToken(points=11.0),
                is_bold=True,
                space_before=DimensionToken(points=8.0),
                space_after=DimensionToken(points=2.0),
                color_role=SemanticColorRole.TEXT_PRIMARY,
            ),
            TypographyRole.HEADING_4: TypographyCompositeToken(
                font_size=DimensionToken(points=10.0),
                is_bold=True,
                is_italic=True,
                space_before=DimensionToken(points=6.0),
                space_after=DimensionToken(points=2.0),
                color_role=SemanticColorRole.TEXT_SECONDARY,
            ),
            TypographyRole.BODY_REGULAR: TypographyCompositeToken(
                font_size=DimensionToken(points=10.0),
                space_after=DimensionToken(points=4.0),
                color_role=SemanticColorRole.TEXT_PRIMARY,
            ),
            TypographyRole.BODY_STRONG: TypographyCompositeToken(
                font_size=DimensionToken(points=10.0),
                is_bold=True,
                space_after=DimensionToken(points=4.0),
                color_role=SemanticColorRole.TEXT_PRIMARY,
            ),
            TypographyRole.CAPTION: TypographyCompositeToken(
                font_size=DimensionToken(points=8.5),
                is_italic=True,
                space_after=DimensionToken(points=4.0),
                color_role=SemanticColorRole.TEXT_MUTED,
            ),
            TypographyRole.MONOSPACE: TypographyCompositeToken(
                font_size=DimensionToken(points=9.0),
                is_monospace=True,
                space_after=DimensionToken(points=4.0),
                color_role=SemanticColorRole.TEXT_SECONDARY,
            ),
            TypographyRole.TABLE_HEADER: TypographyCompositeToken(
                font_size=DimensionToken(points=9.0),
                is_bold=True,
                space_after=DimensionToken(points=2.0),
                color_role=SemanticColorRole.TEXT_INVERSE,
            ),
            TypographyRole.TABLE_CELL: TypographyCompositeToken(
                font_size=DimensionToken(points=8.5),
                space_after=DimensionToken(points=2.0),
                color_role=SemanticColorRole.TEXT_PRIMARY,
            ),
        }
        cls._themes[cls._default_theme_id] = TenantThemeManifest(
            theme_id=cls._default_theme_id,
            tenant_name="Global Enterprise Standard",
            font_stack=FontStackToken(),
            colors=default_colors,
            typography=default_typography,
        )
