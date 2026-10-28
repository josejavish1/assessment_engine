"""
Dynamic Open Graph SVG Social Card Generator — GEMA 16 (W3C SVG / SOTA 2026).
Renders 1200x630px high-resolution Open Graph social preview cards.
Generates vector SVG graphics optimized for rich WhatsApp, Twitter/X, and LinkedIn previews.
Zero external headless browser or canvas binary dependencies needed.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.social_card_generator")


class SocialCardGeneratorPrimitive:
    """
    Generate Open Graph social cards in native vector SVG format.
    """

    def generate_svg_card(
        self,
        title: str,
        subtitle: str,
        primary_color: str = "#0D9488",
        bg_color: str = "#0F172A"
    ) -> str:
        """Generate a 1200x630 Open Graph card in native SVG format."""
        clean_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean_subtitle = subtitle.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_color}"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{primary_color}"/>
      <stop offset="100%" stop-color="#38BDF8"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="1200" height="630" fill="url(#bgGrad)"/>

  <!-- Decorative Accent Bar -->
  <rect x="80" y="80" width="8" height="120" rx="4" fill="url(#accentGrad)"/>

  <!-- Brand Badge -->
  <rect x="110" y="80" width="180" height="36" rx="18" fill="{primary_color}" opacity="0.2"/>
  <text x="130" y="104" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="700" fill="{primary_color}" letter-spacing="2">VERIFIED SAAS</text>

  <!-- Main Title -->
  <text x="110" y="160" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="52" font-weight="800" fill="#F8FAFC">{clean_title}</text>

  <!-- Subtitle -->
  <text x="110" y="220" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="400" fill="#94A3B8">{clean_subtitle}</text>

  <!-- Bottom Tech Proof -->
  <line x1="80" y1="520" x2="1120" y2="520" stroke="#334155" stroke-width="1"/>
  <text x="80" y="565" font-family="monospace" font-size="16" fill="#64748B">SOTA 2026 ARCHITECTURE &bull; SQLITE WAL &bull; W3C PWA READY</text>
</svg>"""

    def generate_meta_tags(self, title: str, description: str, image_url: str = "/og-image.svg") -> str:
        """Genera las etiquetas meta Open Graph y Twitter Cards correspondientes."""
        return (
            f'<meta property="og:type" content="website">\n'
            f'<meta property="og:title" content="{title}">\n'
            f'<meta property="og:description" content="{description}">\n'
            f'<meta property="og:image" content="{image_url}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:title" content="{title}">\n'
            f'<meta name="twitter:description" content="{description}">\n'
            f'<meta name="twitter:image" content="{image_url}">'
        )


social_card_generator = SocialCardGeneratorPrimitive()
