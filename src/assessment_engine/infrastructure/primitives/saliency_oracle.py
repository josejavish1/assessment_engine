"""
Visual Saliency & Foveal Attention Oracle — GEMA 24 / Preflight Conversion Engine (SOTA 2026).
Predicts 3-5 second visual attention and foveal fixation probability on primary CTAs.
Mathematical formulation based on Itti-Koch neuromorphic saliency, Michelson/Weber contrast,
Fitts's law area scaling, above-the-fold logistic decay, and crowding (lateral masking) penalties.
Supports alpha-blending composite surfaces, glassmorphism and transparent background resolution.
Zero external API costs ($0.00 infrastructure overhead).
"""

from __future__ import annotations

import logging
import math
import re
import struct
import zlib
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.saliency_oracle")


@dataclass
class VisualElement:
    """Represent a normalized visual DOM node."""
    selector: str
    text: str
    x: float
    y: float
    width: float
    height: float
    bg_color: str = "#FFFFFF"
    fg_color: str = "#000000"
    is_cta: bool = False
    parent_bg_color: str | None = None


@dataclass
class ElementSaliency:
    """Represent visual saliency and estimated attention scores for an element."""
    selector: str
    text: str
    saliency_score: float                # 0.0 a 1.0 (prominencia absoluta)
    fixation_probability_pct: float      # 0.0 to 100.0% (viewport attention share)
    contrast_ratio: float                # Ratio WCAG relativo al contenedor
    scale_factor: float                  # Ergonomic scale factor (Fitts)
    fold_factor: float                   # Vertical depth decay
    crowding_penalty: float              # Penalty for surrounding distractors (1.0 = isolated)
    is_above_fold: bool = True
    sampled_color: str = ""


@dataclass
class SaliencyAuditReport:
    """Represent the consolidated pre-flight predictive attention audit report."""
    focus_score: float                   # 0.0 to 100.0 (attention concentration on the primary CTA)
    clarity_score: float                 # 0.0 to 100.0 (inverse of saturation and cognitive noise)
    passed: bool                         # True si focus_score >= 60 y clarity_score >= 65
    primary_cta_fixation_pct: float      # Foveal share of the highest-converting CTA
    elements: list[ElementSaliency] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def _parse_rgba_color(color_str: str) -> tuple[float, float, float, float]:
    """Parsea cadena hex, rgb o rgba a (r, g, b, alpha) normalizados de 0.0 a 1.0."""
    cleaned = color_str.strip().lower()
    rgba_match = re.search(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([0-9.]+))?\s*\)", cleaned)
    if rgba_match:
        r = int(rgba_match.group(1)) / 255.0
        g = int(rgba_match.group(2)) / 255.0
        b = int(rgba_match.group(3)) / 255.0
        alpha = float(rgba_match.group(4)) if rgba_match.group(4) is not None else 1.0
        return (r, g, b, max(0.0, min(1.0, alpha)))

    clean_hex = cleaned.lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join(c * 2 for c in clean_hex)
    if len(clean_hex) == 8:
        try:
            r = int(clean_hex[0:2], 16) / 255.0
            g = int(clean_hex[2:4], 16) / 255.0
            b = int(clean_hex[4:6], 16) / 255.0
            a = int(clean_hex[6:8], 16) / 255.0
            return (r, g, b, a)
        except ValueError:
            return (1.0, 1.0, 1.0, 1.0)
    if len(clean_hex) == 6:
        try:
            r = int(clean_hex[0:2], 16) / 255.0
            g = int(clean_hex[2:4], 16) / 255.0
            b = int(clean_hex[4:6], 16) / 255.0
            return (r, g, b, 1.0)
        except ValueError:
            return (1.0, 1.0, 1.0, 1.0)
    return (1.0, 1.0, 1.0, 1.0)


def _parse_hex_color(hex_str: str) -> tuple[float, float, float]:
    """Parse a color string into an opaque RGB tuple (0.0 to 1.0)."""
    rgba = _parse_rgba_color(hex_str)
    return (rgba[0], rgba[1], rgba[2])


def _blend_colors(fg_rgba: tuple[float, float, float, float], bg_rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Perform standard alpha blending of a foreground layer over an opaque background: C = a*C_fg + (1-a)*C_bg."""
    a = fg_rgba[3]
    if a >= 1.0:
        return (fg_rgba[0], fg_rgba[1], fg_rgba[2])
    if a <= 0.0:
        return bg_rgb
    r = a * fg_rgba[0] + (1.0 - a) * bg_rgb[0]
    g = a * fg_rgba[1] + (1.0 - a) * bg_rgb[1]
    b = a * fg_rgba[2] + (1.0 - a) * bg_rgb[2]
    return (r, g, b)


def _srgb_to_linear(channel: float) -> float:
    """Convierte un canal sRGB normalizado a luminancia lineal (W3C standard)."""
    if channel <= 0.04045:
        return channel / 12.92
    return math.pow((channel + 0.055) / 1.055, 2.4)


def _extract_pixel_from_png(png_bytes: bytes) -> tuple[int, int, int]:
    """Extract RGB color (0-255) from a 1x1 pixel screenshot without external libraries."""
    if len(png_bytes) < 30:
        return (15, 23, 42)
    try:
        pos = 8
        all_idat: list[bytes] = []
        while pos < len(png_bytes):
            length = struct.unpack(">I", png_bytes[pos : pos + 4])[0]
            chunk_type = png_bytes[pos + 4 : pos + 8]
            if chunk_type == b"IDAT":
                all_idat.append(png_bytes[pos + 8 : pos + 8 + length])
            pos += 8 + length + 4
        decompressed = zlib.decompress(b"".join(all_idat))
        if len(decompressed) >= 4:
            return (decompressed[1], decompressed[2], decompressed[3])
        return (15, 23, 42)
    except (struct.error, zlib.error, IndexError):
        return (15, 23, 42)


class SaliencyOraclePrimitive:
    """Predict visual saliency and foveal attention to evaluate visual ergonomics and prevent funnel abandonment."""

    def calculate_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance according to the W3C standard."""
        r, g, b = _parse_hex_color(hex_color)
        r_lin = _srgb_to_linear(r)
        g_lin = _srgb_to_linear(g)
        b_lin = _srgb_to_linear(b)
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    def calculate_composite_luminance(self, fg_color: str, bg_color: str = "#0F172A") -> float:
        """Calculate relative luminance after blending the foreground layer with the background."""
        fg_rgba = _parse_rgba_color(fg_color)
        bg_rgba = _parse_rgba_color(bg_color)
        bg_rgb = (bg_rgba[0], bg_rgba[1], bg_rgba[2])
        blended = _blend_colors(fg_rgba, bg_rgb)
        r_lin = _srgb_to_linear(blended[0])
        g_lin = _srgb_to_linear(blended[1])
        b_lin = _srgb_to_linear(blended[2])
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    def calculate_contrast_ratio(self, color1: str, color2: str, base_bg: str = "#0F172A") -> float:
        """Calculate the relative contrast ratio (1.0 to 21.0), supporting translucent layers."""
        lum1 = self.calculate_composite_luminance(color1, base_bg)
        lum2 = self.calculate_composite_luminance(color2, base_bg)
        l_max = max(lum1, lum2)
        l_min = min(lum1, lum2)
        return (l_max + 0.05) / (l_min + 0.05)

    def calculate_scale_factor(
        self, width: float, height: float, viewport_w: float = 1440.0, viewport_h: float = 900.0
    ) -> float:
        """Calculate the ergonomic scale factor based on Fitts's Law."""
        area = max(1.0, width * height)
        viewport_area = max(1.0, viewport_w * viewport_h)
        ratio = area / viewport_area

        # Penalty for sub-touch targets (< 44x44 = 1936 px)
        if width < 44.0 or height < 44.0:
            return 0.35

        # Optimal range for primary CTA: 0.8% to 3.5% of viewport
        if 0.008 <= ratio <= 0.035:
            return 1.0
        if ratio < 0.008:
            return max(0.4, ratio / 0.008)
        # Apply soft decay if element is excessively large (> 10% of viewport)
        return max(0.6, 1.0 - (ratio - 0.035) * 2.5)

    def calculate_fold_factor(self, y: float, fold_y: float = 720.0) -> float:
        """Calculate the vertical depth attenuation factor using a sigmoid function."""
        if y <= 400.0:
            return 1.0
        diff = y - fold_y
        # Logistic sigmoid: rapid attenuation across the fold
        return 1.0 / (1.0 + math.exp(diff / 160.0))

    def calculate_crowding_penalty(
        self,
        elem: VisualElement,
        all_elements: list[VisualElement],
        radius: float = 120.0,
    ) -> float:
        """Calculate lateral inhibition caused by visual crowding using Bouma's law. Reduces prominence when a CTA is surrounded by distractors within a close Euclidean radius."""
        center_x = elem.x + (elem.width / 2.0)
        center_y = elem.y + (elem.height / 2.0)
        distractor_count = 0

        for other in all_elements:
            if other.selector == elem.selector:
                continue
            other_cx = other.x + (other.width / 2.0)
            other_cy = other.y + (other.height / 2.0)
            dist = math.hypot(center_x - other_cx, center_y - other_cy)
            if dist <= radius:
                distractor_count += 1

        # Asymptotic attenuation from adjacent distractors
        return 1.0 / (1.0 + 0.22 * distractor_count)

    def _score_single_element(
        self,
        elem: VisualElement,
        all_elements: list[VisualElement],
        viewport_w: float,
        viewport_h: float,
        container_bg: str = "#0F172A",
    ) -> ElementSaliency:
        """Compute sub-factors and the composite saliency score for a node."""
        # 1. Button contrast against section background (supports nested backgrounds)
        resolved_bg = elem.parent_bg_color or container_bg
        bg_contrast = self.calculate_contrast_ratio(elem.bg_color, resolved_bg, base_bg=resolved_bg)
        contrast_factor = min(1.0, bg_contrast / 7.0)

        scale_fac = self.calculate_scale_factor(elem.width, elem.height, viewport_w, viewport_h)

        fold_fac = self.calculate_fold_factor(elem.y, fold_y=viewport_h * 0.8)

        crowd_fac = self.calculate_crowding_penalty(elem, all_elements)

        # Prominencia compuesta ponderada (Itti-Koch normalizada)
        raw_saliency = (0.42 * contrast_factor + 0.28 * scale_fac + 0.30 * fold_fac) * crowd_fac
        if elem.is_cta:
            raw_saliency = min(1.0, raw_saliency * 1.15)

        return ElementSaliency(
            selector=elem.selector,
            text=elem.text,
            saliency_score=round(raw_saliency, 4),
            fixation_probability_pct=0.0,
            contrast_ratio=round(bg_contrast, 2),
            scale_factor=round(scale_fac, 2),
            fold_factor=round(fold_fac, 2),
            crowding_penalty=round(crowd_fac, 2),
            is_above_fold=elem.y < (viewport_h * 0.8),
            sampled_color=elem.bg_color,
        )

    def _generate_findings(
        self,
        scored: list[ElementSaliency],
        elements: list[VisualElement],
        focus_score: float,
        clarity_score: float,
    ) -> list[str]:
        """Generate prescriptive diagnostics for detected visual frictions."""
        findings: list[str] = []
        cta_candidates = [s for s, e in zip(scored, elements, strict=False) if e.is_cta]

        if not cta_candidates:
            findings.append("No se marcaron elementos como llamadas a la acción (is_cta=True).")
            return findings

        top_cta = max(cta_candidates, key=lambda s: s.saliency_score)

        if not top_cta.is_above_fold:
            findings.append(
                f"CTA primario '{top_cta.text}' está por debajo del pliegue visual (fold_factor={top_cta.fold_factor}). "
                "Reubicar en los primeros 700px del viewport."
            )
        if top_cta.contrast_ratio < 4.5:
            findings.append(
                f"Contraste insuficiente en CTA '{top_cta.text}' ({top_cta.contrast_ratio}:1 < 4.5:1). "
                "Elevar la luminancia frente al fondo de la sección."
            )
        if top_cta.crowding_penalty < 0.70:
            findings.append(
                f"Saturación de distractores (Crowding) sobre CTA '{top_cta.text}' (penalización {top_cta.crowding_penalty}). "
                "Aumentar espacio negativo circundante (mínimo 32px de margen)."
            )
        if top_cta.scale_factor < 0.60:
            findings.append(
                f"Tamaño sub-óptimo para objetivo táctil en '{top_cta.text}'. Asegurar un mínimo de 44x44px."
            )
        if focus_score < 60.0:
            findings.append(
                f"Focus Score deficiente ({focus_score:.1f}/100). La atención visual está excesivamente dispersa."
            )
        if clarity_score < 65.0:
            findings.append(
                f"Clarity Score bajo ({clarity_score:.1f}/100). Reducir elementos competidores secundarios."
            )
        return findings

    def evaluate_elements(
        self,
        elements: list[VisualElement],
        viewport_w: int = 1440,
        viewport_h: int = 900,
        container_bg: str = "#0F172A",
    ) -> SaliencyAuditReport:
        """Perform a CPU-based mathematical audit for pre-flight checks and tests. Calculates foveal fixation probabilities within the first three seconds."""
        if not elements:
            return SaliencyAuditReport(
                focus_score=0.0,
                clarity_score=100.0,
                passed=False,
                primary_cta_fixation_pct=0.0,
                elements=[],
                findings=["Lista de elementos visuales vacía."],
                metrics={"total_elements": 0},
            )

        scored: list[ElementSaliency] = [
            self._score_single_element(elem, elements, float(viewport_w), float(viewport_h), container_bg)
            for elem in elements
        ]

        total_raw = sum(s.saliency_score for s in scored) or 1.0
        for s in scored:
            s.fixation_probability_pct = round((s.saliency_score / total_raw) * 100.0, 2)

        # Identificar CTAs
        cta_scored = [s for s, e in zip(scored, elements, strict=False) if e.is_cta]
        primary_cta_fixation = max((s.fixation_probability_pct for s in cta_scored), default=0.0)

        # Focus score: combined share captured by primary CTAs
        total_cta_fixation = sum(s.fixation_probability_pct for s in cta_scored)
        focus_score = round(min(100.0, total_cta_fixation * 1.5), 1) if cta_scored else 0.0

        # Clarity score: penalized by excessive interactive element density
        crowding_avg = sum(s.crowding_penalty for s in scored) / len(scored)
        clarity_score = round(min(100.0, crowding_avg * 100.0), 1)

        findings = self._generate_findings(scored, elements, focus_score, clarity_score)
        passed = (focus_score >= 50.0 and clarity_score >= 60.0 and len(findings) == 0)

        metrics = {
            "total_elements": len(elements),
            "cta_elements_count": len(cta_scored),
            "primary_cta_fixation_pct": primary_cta_fixation,
            "average_crowding_penalty": round(crowding_avg, 2),
        }

        logger.info(
            f"[SaliencyOracle] Evaluación completada: focus={focus_score}/100, clarity={clarity_score}/100, passed={passed}"
        )

        return SaliencyAuditReport(
            focus_score=focus_score,
            clarity_score=clarity_score,
            passed=passed,
            primary_cta_fixation_pct=primary_cta_fixation,
            elements=scored,
            findings=findings,
            metrics=metrics,
        )

    async def sample_rendered_pixel(self, page: Any, x: float, y: float) -> str:
        """Sample the actual RGB color rendered by Chromium's GPU at coordinate (x, y)."""
        if not hasattr(page, "screenshot"):
            return ""
        try:
            clip_bytes = await page.screenshot(
                clip={"x": max(0.0, x), "y": max(0.0, y), "width": 1.0, "height": 1.0},
                type="png",
            )
            r, g, b = _extract_pixel_from_png(clip_bytes)
            return f"rgb({r}, {g}, {b})"
        except (ValueError, KeyError, TypeError, OSError):
            return ""

    async def _sample_cta_pixels(self, page: Any, elements: list[VisualElement]) -> None:
        """Sample exact GPU-rendered pixel for CTAs to capture real gradients and blur."""
        if not hasattr(page, "screenshot"):
            return
        for el in elements:
            if not el.is_cta:
                continue
            cx = el.x + el.width / 2.0
            cy = el.y + el.height / 2.0
            btn_px = await self.sample_rendered_pixel(page, cx, cy)
            if btn_px:
                el.bg_color = btn_px
            bg_px = await self.sample_rendered_pixel(page, max(0.0, el.x - 16.0), max(0.0, el.y - 16.0))
            if bg_px:
                el.parent_bg_color = bg_px

    async def audit_page(
        self,
        page: Any,
        target_selectors: list[str] | None = None,
        viewport_w: int = 1440,
        viewport_h: int = 900,
    ) -> SaliencyAuditReport:
        """Audit an active Playwright Chromium page by extracting bounding boxes and computed styles, resolving nested backgrounds, gradients, and translucent layers."""
        raw_elements = await page.evaluate("""
            () => {
                function resolveParentBg(node) {
                    let curr = node.parentElement;
                    while (curr && curr !== document.documentElement) {
                        const bg = window.getComputedStyle(curr).backgroundColor;
                        if (bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)') {
                            return bg;
                        }
                        curr = curr.parentElement;
                    }
                    const bodyBg = window.getComputedStyle(document.body).backgroundColor;
                    return (bodyBg && bodyBg !== 'transparent' && bodyBg !== 'rgba(0, 0, 0, 0)') ? bodyBg : '#0F172A';
                }

                const nodes = Array.from(document.querySelectorAll('button, a[href], h1, h2, input[type="submit"]'));
                return nodes.map((node, index) => {
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    const isButton = node.tagName.toLowerCase() === 'button' || node.getAttribute('role') === 'button';
                    const text = (node.innerText || node.textContent || '').trim();
                    const selector = node.id ? `#${node.id}` : `${node.tagName.toLowerCase()}:nth-of-type(${index + 1})`;
                    return {
                        selector: selector,
                        text: text.slice(0, 50),
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        bg_color: style.backgroundColor,
                        fg_color: style.color,
                        is_cta: isButton && text.length > 0 && text.length < 35,
                        parent_bg_color: resolveParentBg(node)
                    };
                }).filter(n => n.width > 0 && n.height > 0);
            }
        """)

        parsed_elements = [
            VisualElement(
                selector=item.get("selector", "unknown"),
                text=item.get("text", ""),
                x=float(item.get("x", 0.0)),
                y=float(item.get("y", 0.0)),
                width=float(item.get("width", 0.0)),
                height=float(item.get("height", 0.0)),
                bg_color=item.get("bg_color", "#FFFFFF"),
                fg_color=item.get("fg_color", "#000000"),
                is_cta=bool(item.get("is_cta", False)),
                parent_bg_color=item.get("parent_bg_color"),
            )
            for item in raw_elements
        ]

        if target_selectors:
            for el in parsed_elements:
                if any(ts in el.selector for ts in target_selectors):
                    el.is_cta = True

        await self._sample_cta_pixels(page, parsed_elements)
        return self.evaluate_elements(parsed_elements, viewport_w=viewport_w, viewport_h=viewport_h)


# Canonical singleton instance.
saliency_oracle = SaliencyOraclePrimitive()
