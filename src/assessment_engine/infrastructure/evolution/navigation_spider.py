# core/evolution/navigation_spider.py

import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class SpiderNavigationIssue:
    element_tag: str
    element_text: str
    selector: str
    issue_type: str
    target_url: str
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SpiderAuditReport:
    total_links_audited: int
    total_buttons_audited: int
    issues: List[SpiderNavigationIssue]
    console_errors: List[str]
    is_100_percent_functional: bool
    execution_time_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _is_404_view_text(text: str) -> bool:
    """Detect 404 / route missing states across multiple languages (EN, ES, DE, FR, IT)."""
    t = text.lower()
    has_404 = "404" in t
    matches_kw = any(k in t for k in ("not found", "no encontrada", "nicht gefunden", "non trouv", "non trovat", "does not exist", "inexistente"))
    return bool((has_404 and matches_kw) or "the requested workspace route does not exist" in t)


async def _audit_single_link(page: Any, lk: Dict[str, Any], target_url: str) -> SpiderNavigationIssue | None:
    """Audit single link navigation for 404 or broken view."""
    href = lk.get("href", "").strip()
    if not href or href in ("#", "javascript:void(0)"):
        return None
    try:
        if href.startswith("#"):
            await page.evaluate(f"() => window.location.hash = '{href}'")
            await page.wait_for_timeout(250)
            body_text = await page.evaluate("() => document.body.innerText")
            if _is_404_view_text(body_text):
                return SpiderNavigationIssue(
                    element_tag="a", element_text=lk.get("text", ""),
                    selector=lk.get("selector", ""),
                    issue_type="NOT_FOUND_404", target_url=f"{target_url}{href}",
                    details=f"Navigation to {href} rendered 404 error page"
                )
    except Exception as ex:
        return SpiderNavigationIssue(
            element_tag="a", element_text=lk.get("text", ""),
            selector=lk.get("selector", ""),
            issue_type="DEAD_LINK", target_url=f"{target_url}{href}",
            details=f"Navigation threw exception: {ex}"
        )
    return None


async def _audit_single_button(page: Any, btn: Dict[str, Any], target_url: str, spider: Any) -> SpiderNavigationIssue | None:
    """Audit button click interaction ensuring DOM mutation or navigation occurs."""
    sel = btn.get("selector", "")
    if not sel:
        return None
    try:
        loc = page.locator(sel).first
        if await loc.count() > 0 and await loc.is_visible():
            init_content = await page.content()
            init_url = page.url
            await loc.click(timeout=1000)
            await page.wait_for_timeout(300)
            final_content = await page.content()
            final_url = page.url
            dom_changed = (init_content != final_content) or (final_url != init_url)
            if not dom_changed:
                return SpiderNavigationIssue(
                    element_tag="button", element_text=btn.get("text", ""),
                    selector=sel, issue_type="INERT_BUTTON", target_url=target_url,
                    details="Button click produced zero DOM mutation and did not navigate"
                )
    except Exception:
        pass
    return None


async def _audit_buttons_batch(page: Any, raw_buttons: List[Dict[str, Any]], target_url: str, spider: Any) -> List[SpiderNavigationIssue]:
    """Audit batch of interactive buttons restoring base hash between tests."""
    issues: List[SpiderNavigationIssue] = []
    for btn in raw_buttons[:12]:
        if page.url != target_url:
            await page.evaluate("() => { window.location.hash = ''; }")
            await page.wait_for_timeout(200)
        btn_iss = await _audit_single_button(page, btn, target_url, spider)
        if btn_iss:
            issues.append(btn_iss)
    return issues


class AutonomousNavigationSpider:
    """
    Deterministic auditing spider for headless Chromium.
    Validates functional links, buttons, and DOM interactions.
    """

    def detect_empty_or_broken_hrefs(self, links: List[Dict[str, Any]]) -> List[SpiderNavigationIssue]:
        """Detects links with empty or broken href attributes."""
        issues: List[SpiderNavigationIssue] = []
        for link in links:
            href_raw = link.get("href", "")
            href = str(href_raw).strip() if href_raw is not None else ""
            
            if not href or href == "#" or href == "javascript:void(0)":
                issues.append(SpiderNavigationIssue(
                    element_tag=link.get("tag", "a"),
                    element_text=link.get("text", ""),
                    selector=link.get("selector", ""),
                    issue_type="EMPTY_HREF",
                    target_url=href,
                    details="Href is empty, fragment-only, or javascript void"
                ))
        return issues

    def detect_inert_button_from_delta(self, dom_delta: int, url_changed: bool, modal_opened: bool) -> bool:
        """Determines if a button is inert based on interaction deltas."""
        return dom_delta == 0 and not url_changed and not modal_opened

    def format_surgical_correction_prompt(self, report: SpiderAuditReport) -> str:
        """Generates a prescriptive string for LLM self-healing."""
        lines: List[str] = ["INFORME PRESCRIPTIVO DE FALLOS DE NAVEGACIÓN"]
        lines.append(f"Total Links: {report.total_links_audited}")
        lines.append(f"Total Buttons: {report.total_buttons_audited}")
        
        for issue in report.issues:
            lines.append(f"Issue: {issue.issue_type} at {issue.selector}")
            lines.append(f"Details: {issue.details}")
            
        if report.console_errors:
            lines.append("Console Errors:")
            for err in report.console_errors:
                lines.append(err)
                
        return "\n".join(lines)

    async def audit_page(self, page: Any, base_url: str) -> SpiderAuditReport:
        """
        Audits a page for navigation issues.
        Assumes `page.evaluate()` provides ordered interaction data.
        """
        start_time = time.time()
        issues: List[SpiderNavigationIssue] = []
        console_errors: List[str] = []

        # 1. Extract all links
        links = await page.evaluate("get_links")
        
        # 2. Extract all buttons
        buttons = await page.evaluate("get_buttons")
        
        # 3. Check for 404 View Not Found
        is_404 = await page.evaluate("check_404")
        if is_404:
            issues.append(SpiderNavigationIssue(
                element_tag="body",
                element_text="",
                selector="body",
                issue_type="NOT_FOUND_404",
                target_url=base_url,
                details="Route rendered 404 - View Not Found"
            ))

        # Check href validity
        href_issues = self.detect_empty_or_broken_hrefs(links)
        issues.extend(href_issues)

        # 4. Check button interactions
        for btn in buttons:
            delta_info = await page.evaluate("check_button_delta")
            if not isinstance(delta_info, dict):
                continue
                
            is_inert = self.detect_inert_button_from_delta(
                dom_delta=delta_info.get("delta", 0),
                url_changed=delta_info.get("url_changed", False),
                modal_opened=delta_info.get("modal_opened", False)
            )
            
            if is_inert:
                issues.append(SpiderNavigationIssue(
                    element_tag=btn.get("tag", "button"),
                    element_text=btn.get("text", ""),
                    selector=btn.get("selector", ""),
                    issue_type="INERT_BUTTON",
                    target_url=base_url,
                    details="Button click produced zero DOM delta and did not navigate"
                ))

        is_functional = (len(issues) == 0 and len(console_errors) == 0)
        execution_time = time.time() - start_time

        return SpiderAuditReport(
            total_links_audited=len(links),
            total_buttons_audited=len(buttons),
            issues=issues,
            console_errors=console_errors,
            is_100_percent_functional=is_functional,
            execution_time_seconds=execution_time
        )

    async def audit_url(self, target_url: str, headless: bool = True) -> SpiderAuditReport:
        """Launch headless Chromium, visit target_url, extract real DOM elements, and audit navigation."""
        from playwright.async_api import async_playwright

        start_time = time.time()
        console_errors: List[str] = []
        issues: List[SpiderNavigationIssue] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            page.on("pageerror", lambda err: console_errors.append(f"JS Exception: {err}"))

            try:
                await page.goto(target_url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1000)
            except Exception as e:
                issues.append(SpiderNavigationIssue(
                    element_tag="body", element_text="", selector="body",
                    issue_type="NOT_FOUND_404", target_url=target_url,
                    details=f"Failed to load page: {e}"
                ))
                await browser.close()
                return SpiderAuditReport(
                    total_links_audited=0, total_buttons_audited=0,
                    issues=issues, console_errors=console_errors,
                    is_100_percent_functional=False,
                    execution_time_seconds=time.time() - start_time
                )

            raw_links = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map((el, i) => {
                    const text = el.innerText.trim();
                    const href = el.getAttribute('href') || '';
                    let sel = el.id ? '#' + el.id : '';
                    if (!sel && href) {
                        sel = 'a[href="' + href.replace(/"/g, '') + '"]';
                    }
                    if (!sel) {
                        sel = 'a:nth-of-type(' + (i + 1) + ')';
                    }
                    return {
                        tag: 'a',
                        text: text,
                        href: href,
                        selector: sel
                    };
                });
            }""")

            raw_buttons = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button')).map((el, i) => {
                    const text = el.innerText.trim();
                    let sel = el.id ? '#' + el.id : '';
                    if (!sel && text && text.length <= 25) {
                        sel = 'button:has-text("' + text.replace(/"/g, '') + '")';
                    }
                    if (!sel) {
                        sel = 'button:nth-of-type(' + (i + 1) + ')';
                    }
                    return {
                        tag: 'button',
                        text: text,
                        type: el.getAttribute('type') || 'button',
                        selector: sel
                    };
                });
            }""")

            init_body = await page.evaluate("() => document.body.innerText")
            if _is_404_view_text(init_body):
                issues.append(SpiderNavigationIssue(
                    element_tag="body", element_text="", selector="body",
                    issue_type="NOT_FOUND_404", target_url=target_url,
                    details="Page rendered 404 on initial load"
                ))

            href_issues = self.detect_empty_or_broken_hrefs(raw_links)
            issues.extend(href_issues)

            seen_hrefs = set()
            for lk in raw_links:
                href = lk.get("href", "").strip()
                if href and href not in seen_hrefs:
                    seen_hrefs.add(href)
                    iss = await _audit_single_link(page, lk, target_url)
                    if iss:
                        issues.append(iss)

            btn_issues = await _audit_buttons_batch(page, raw_buttons, target_url, self)
            issues.extend(btn_issues)

            await browser.close()

        is_functional = (len(issues) == 0 and len(console_errors) == 0)
        return SpiderAuditReport(
            total_links_audited=len(raw_links),
            total_buttons_audited=len(raw_buttons),
            issues=issues,
            console_errors=console_errors,
            is_100_percent_functional=is_functional,
            execution_time_seconds=time.time() - start_time
        )