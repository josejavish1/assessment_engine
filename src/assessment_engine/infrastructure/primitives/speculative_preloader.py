"""
Preload routes predictively using W3C Speculation Rules and Google Chrome Labs Quicklink.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger("assessment_engine.infrastructure.primitives.speculative_preloader")


@dataclass
class PreloadRulesConfig:
    excluded_keywords: tuple[str, ...] = ("logout", "delete", "admin", "api")
    eagerness: str = "moderate"


class SpeculativePreloader:
    @staticmethod
    def get_w3c_speculation_rules_html() -> str:
        """
        Inject native W3C Speculation Rules for Chromium, Edge, and Chrome browsers.
        """
        rules = {
            "prerender": [
                {
                    "source": "document",
                    "where": {
                        "and": [
                            {"href_matches": "/*"},
                            {"not": {"href_matches": "/*logout*"}},
                            {"not": {"href_matches": "/*admin*"}},
                            {"not": {"href_matches": "/api/*"}},
                        ]
                    },
                    "eagerness": "moderate",
                }
            ]
        }
        return f'<script type="speculationrules">\n{json.dumps(rules, indent=2)}\n</script>'

    @staticmethod
    def get_pointer_hover_fallback_js() -> str:
        """
        Provide a JavaScript fallback for Safari and browsers lacking native speculationrules support.
        """
        return """
        <script>
        document.addEventListener('pointerenter', function(e) {
            const link = e.target.closest('a[href]');
            if (!link || !link.href.startsWith(window.location.origin)) return;
            if (link.href.includes('logout') || link.href.includes('admin')) return;
            const prefetch = document.createElement('link');
            prefetch.rel = 'prefetch';
            prefetch.href = link.href;
            document.head.appendChild(prefetch);
        }, { capture: true, passive: true });
        </script>
        """


class SpeculativePreloaderPrimitive:
    """
    Inject predictive prerendering rules compliant with W3C Speculation Rules.
    """

    def generate_speculation_rules_tag(self, target_hrefs: list[str] | None = None) -> str:
        """Generate the <script type="speculationrules"> block with moderate interaction matching."""
        rules = {
            "prerender": [
                {
                    "source": "list",
                    "urls": target_hrefs or ["/", "/#view=admin", "/#view=client"],
                    "eagerness": "moderate",
                }
            ]
        }

        return f'<script type="speculationrules">\n{json.dumps(rules, indent=2)}\n</script>'


speculative_preloader = SpeculativePreloaderPrimitive()
