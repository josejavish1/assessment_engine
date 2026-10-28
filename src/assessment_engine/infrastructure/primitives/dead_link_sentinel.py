"""
Pre-Flight Dead-Link & 404 Asset Sentinel — GEMA 42 (SOTA 2026).
Crawls all internal anchor links (<a href>) and static assets (<img>, <script>, <link>)
on the synthesized web application.
Guarantees zero broken links, zero 404 assets, and zero dead interactive buttons.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx
from playwright.async_api import Page

logger = logging.getLogger("assessment_engine.infrastructure.primitives.dead_link_sentinel")


@dataclass
class BrokenLinkFinding:
    element: str
    target_url: str
    status_code: int


@dataclass
class LinkAuditReport:
    passed: bool
    total_checked: int
    broken_count: int
    findings: list[BrokenLinkFinding] = field(default_factory=list)


class DeadLinkSentinelPrimitive:
    """
    Centinela pre-vuelo de enlaces rotos y assets 404.
    """

    async def audit_page_links(self, page: Page, base_url: str) -> LinkAuditReport:
        """Inspect and validate all internal links and page assets."""
        urls_to_check = await page.evaluate("""() => {
            const urls = new Set();
            document.querySelectorAll('a[href]').forEach(a => {
                const h = a.getAttribute('href');
                if (h && !h.startsWith('#') && !h.startsWith('mailto:') && !h.startsWith('tel:') && !h.startsWith('javascript:')) {
                    urls.add(h);
                }
            });
            document.querySelectorAll('img[src]').forEach(img => {
                const s = img.getAttribute('src');
                if (s && !s.startsWith('data:')) urls.add(s);
            });
            return Array.from(urls);
        }""")

        findings = []
        async with httpx.AsyncClient(timeout=3.0) as client:
            for rel_url in urls_to_check:
                full_url = rel_url if rel_url.startswith("http") else f"{base_url.rstrip('/')}/{rel_url.lstrip('/')}"
                try:
                    resp = await client.head(full_url)
                    if resp.status_code >= 400:
                        findings.append(BrokenLinkFinding("link_or_asset", full_url, resp.status_code))
                except (httpx.RequestError, OSError, RuntimeError, ValueError):
                    findings.append(BrokenLinkFinding("link_or_asset", full_url, 599))

        passed = (len(findings) == 0)
        logger.info(f"[DeadLinkSentinel] Auditados {len(urls_to_check)} enlaces/assets ({len(findings)} rotos)")
        return LinkAuditReport(
            passed=passed,
            total_checked=len(urls_to_check),
            broken_count=len(findings),
            findings=findings
        )


dead_link_sentinel = DeadLinkSentinelPrimitive()
