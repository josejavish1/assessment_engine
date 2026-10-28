"""
SEO Canonical URL Guard Primitive — GEMA 65 (SOTA 2026).
Injects rel="canonical" tags to prevent Google search cannibalization and duplicate content penalties.
Normalizes URLs by stripping tracking query params (?ref=, ?utm_source=, ?fbclid=).
"""

from __future__ import annotations

import logging
import urllib.parse

logger = logging.getLogger("assessment_engine.infrastructure.primitives.canonical_urls")


class CanonicalURLsPrimitive:
    """
    Normalize canonical URLs to prevent SEO cannibalization.
    """

    TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid", "gclid"}

    def normalize_canonical_url(self, raw_url: str) -> str:
        """Remove marketing parameters and hash fragments to consolidate the canonical URL."""
        parsed = urllib.parse.urlparse(raw_url)
        queries = urllib.parse.parse_qsl(parsed.query)

        clean_queries = [(k, v) for k, v in queries if k.lower() not in self.TRACKING_PARAMS]
        clean_query_str = urllib.parse.urlencode(clean_queries)

        clean_path = parsed.path.rstrip("/") or "/"
        canonical = urllib.parse.urlunparse((
            parsed.scheme or "https",
            parsed.netloc,
            clean_path,
            "",
            clean_query_str,
            ""  # Quitar hash
        ))
        return canonical

    def generate_canonical_tag(self, raw_url: str) -> str:
        """Genera la etiqueta HTML <link rel="canonical">."""
        canon = self.normalize_canonical_url(raw_url)
        return f'<link rel="canonical" href="{canon}" />'


canonical_urls = CanonicalURLsPrimitive()
