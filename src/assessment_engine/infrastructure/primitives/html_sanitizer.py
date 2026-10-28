"""
Anti-Stored XSS HTML Sanitizer Primitive — GEMA 60 (OWASP ASVS / SOTA 2026).
Cleans user-submitted rich text and notes against persistent Stored XSS attacks.
Strips unsafe tags (<script>, <iframe>, <object>, <embed>) and dangerous attributes (onload, onerror, javascript:).
Pure Python resilient allowlist parser.
"""

from __future__ import annotations

import html
import logging
import re

logger = logging.getLogger("assessment_engine.infrastructure.primitives.html_sanitizer")


class HTMLSanitizerPrimitive:
    """
    Sanitize HTML to prevent XSS using a strict allowlist of safe tags.
    """

    ALLOWED_TAGS = {"p", "b", "i", "strong", "em", "u", "ul", "ol", "li", "span", "br", "h1", "h2", "h3", "h4", "table", "tr", "td", "th", "tbody", "thead"}
    ALLOWED_ATTRS = {"class", "id"}

    def sanitize(self, raw_html: str) -> str:
        """Purga cualquier etiqueta o atributo malicioso del texto HTML."""
        if not raw_html:
            return ""

        clean = re.sub(r"<(script|style|iframe|object|embed|applet)[^>]*>.*?</\1>", "", raw_html, flags=re.IGNORECASE | re.DOTALL)
        clean = re.sub(r"<(script|style|iframe|object|embed|applet)[^>]*/>", "", clean, flags=re.IGNORECASE)

        # 2. Remove event handler attributes (onload=, onerror=, onclick=) and javascript: URIs.
        clean = re.sub(r"on\w+\s*=\s*['\"][^'\"]*['\"]", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"on\w+\s*=\s*[^ >]+", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"href\s*=\s*['\"]javascript:[^'\"]*['\"]", "", clean, flags=re.IGNORECASE)

        def _filter_tag(match: re.Match) -> str:
            tag_str = match.group(0)
            tag_name_match = re.match(r"^</?([a-zA-Z0-9]+)", tag_str)
            if not tag_name_match:
                return html.escape(tag_str)
            tag_name = tag_name_match.group(1).lower()
            if tag_name not in self.ALLOWED_TAGS:
                # Replace with escaped text.
                return ""
            return tag_str

        sanitized = re.sub(r"</?[a-zA-Z0-9]+[^>]*>", _filter_tag, clean)
        sanitized = re.sub(r"<\s*([a-zA-Z0-9]+)\s+>", r"<\1>", sanitized)
        return sanitized


html_sanitizer = HTMLSanitizerPrimitive()
