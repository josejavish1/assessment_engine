"""
Dynamic XML Sitemap Generator — GEMA 21 (Sitemaps.org 0.9 / SOTA 2026).
Compiles W3C/Google compliant sitemap.xml files with proper changefreq and priority attributes.
Enables exhaustive crawling of all domain workspace views by search engine spiders.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.sitemap_generator")


class SitemapGeneratorPrimitive:
    """
    Generate dynamic sitemap.xml files conforming to the Sitemaps.org 0.9 protocol.
    """

    def generate_sitemap_xml(self, base_url: str, routes: list[dict[str, Any]] | None = None) -> str:
        """Generate the XML document with the project's public routes. 'routes': [{'path': '/', 'changefreq': 'daily', 'priority': '1.0'}]"""
        base = base_url.rstrip("/")
        today = time.strftime("%Y-%m-%d")

        default_routes = [
            {"path": "", "changefreq": "daily", "priority": "1.0"},
            {"path": "legal/aviso-legal.html", "changefreq": "monthly", "priority": "0.3"},
            {"path": "legal/privacidad.html", "changefreq": "monthly", "priority": "0.3"},
            {"path": "legal/cookies.html", "changefreq": "monthly", "priority": "0.3"},
        ]

        active_routes = routes or default_routes
        xml_entries = []

        for r in active_routes:
            sub = r.get("path", "").lstrip("/")
            loc = f"{base}/{sub}" if sub else base
            freq = r.get("changefreq", "weekly")
            prio = r.get("priority", "0.8")

            xml_entries.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>""")

        body = "\n".join(xml_entries)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>"""


sitemap_generator = SitemapGeneratorPrimitive()
