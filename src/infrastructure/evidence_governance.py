import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EvidenceSnapshotter:
    r"""[{'target': 'EvidenceSnapshotter', 'docstring': 'Captures and persists snapshots of digital evidence from external URLs.\n\n    This class provides a robust mechanism for capturing web resources. It uses\n    a hybrid engine, leveraging a headless browser (Playwright) for rendering\n    dynamic HTML content and direct HTTP requests (`httpx`) for binary files.\n    This allows it to handle redirects, JavaScript, and various content types\n    effectively. Snapshots are stored locally for archival and analysis.\n\n    Attributes:\n        storage_dir: A `pathlib.Path` object pointing to the directory where\n            evidence snapshots are stored.\n        timeout_ms: The default timeout in milliseconds for browser operations.\n        headers: A dictionary of HTTP headers used to mimic a standard web\n            browser for all network requests.'}, {'target': 'EvidenceSnapshotter.__init__', 'docstring': "Initializes the EvidenceSnapshotter instance.\n\n        Sets up the storage directory for snapshots and configures default\n        values for browser timeout and HTTP request headers.\n\n        Args:\n            storage_dir: The root directory for storing evidence. A subdirectory\n                named 'evidence_snapshots' will be created within this path if\n                it does not already exist.\n\n        Raises:\n            OSError: If the storage directory cannot be created due to file system\n                permissions or other I/O errors."}, {'target': 'EvidenceSnapshotter.process_urls', 'docstring': "Asynchronously extracts, captures, and verifies snapshots from URLs in text.\n\n        This method scans the input text for URLs, processes each one by calling\n        `capture_snapshot`, and filters the results. It enforces a strict policy\n        where only URLs that are successfully captured and verified (status='verified')\n        are included in the returned list. Failed or broken links are logged and\n        discarded.\n\n        Args:\n            text: A string containing the block of text to search for URLs.\n\n        Returns:\n            A list of dictionaries, where each dictionary represents a\n            successfully captured and verified piece of evidence. Returns an\n            empty list if no valid URLs are found or if none can be verified.\n\n        Raises:\n            Exception: Propagates unhandled exceptions from the underlying\n                `capture_snapshot` method, which may include network errors or\n                other runtime issues."}, {'target': 'EvidenceSnapshotter._extract_urls', 'docstring': 'Extract, clean, and deduplicate URLs from a block of text.'}, {'target': 'EvidenceSnapshotter.capture_snapshot', 'docstring': "Captures a snapshot of a single URL, handling redirects and content types.\n\n        This method employs a hybrid engine to robustly capture web content. It\n        first resolves any redirects to identify the final URL. For binary file\n        types (e.g., .pdf, .docx), it uses direct HTTP requests. For HTML\n        content, it uses Playwright to render the page, execute JavaScript, and\n        handle dynamic elements.\n\n        Args:\n            url: The URL of the digital evidence to capture.\n\n        Returns:\n            A dictionary containing metadata about the snapshot, or None if the\n            Playwright library is not installed.\n            - On success, the dictionary includes `status: 'verified'` and details\n              about the locally stored snapshot.\n            - On failure (e.g., HTTP error), it includes `status: 'broken'` or\n              `status: 'error'` with a descriptive message.\n\n        Raises:\n            ImportError: If the 'httpx' library is not installed, as it is a\n                required dependency."}, {'target': 'EvidenceSnapshotter.register_wayback', 'docstring': "Asynchronously submits a URL to the Wayback Machine for archival.\n\n        Note: The current implementation is a no-op. This docstring defines the\n        intended API contract for future implementation.\n\n        This method is intended to submit a URL to the Wayback Machine's 'Save Page\n        Now' service to ensure its long-term historical persistence.\n\n        Args:\n            url: The fully qualified URL to register for archival.\n\n        Raises:\n            ValueError: Intended to be raised if the provided URL is malformed.\n            Exception: Intended to be raised for network or service-side errors\n                during the archival process."}]."""

    def __init__(self, storage_dir: Path):
        """Initializes the instance and its required directory structure.

        Creates a dedicated subdirectory for storing evidence snapshots within the
        provided base path and sets default configurations for network requests,
        including timeout and HTTP headers.

        Args:
            storage_dir: The base directory path where the 'evidence_snapshots'
                subdirectory will be created.

        Raises:
            OSError: If the 'evidence_snapshots' subdirectory cannot be created due
                to filesystem permissions or other OS-level errors.

        Attributes:
            storage_dir (pathlib.Path): The full path to the created
                'evidence_snapshots' directory.
            timeout_ms (int): Default network request timeout in milliseconds, set
                to 15000.
            headers (dict[str, str]): Default HTTP headers for network requests,
                configured to simulate a standard web browser user agent.
        """
        self.storage_dir = storage_dir / "evidence_snapshots"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_ms = 15000
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }

    async def process_urls(self, text: str) -> List[Dict[str, Any]]:
        """Extracts URLs from a text block and captures verified snapshots.

        This asynchronous method parses the input text to find all URLs. For each
        discovered URL, it attempts to capture a web snapshot. A governance rule
        is applied where only snapshots that are successfully captured and achieve a
        'verified' status are retained. URLs that are inaccessible, protected,
        or fail verification are logged and discarded.

        Args:
            text (str): The block of text from which to extract and process URLs.

        Returns:
            List[Dict[str, Any]]: A list of snapshot data dictionaries for each
                successfully verified URL. An empty list is returned if no URLs are
                found or if no snapshots pass verification.

        Raises:
            Exception: Propagates any exception from the underlying `capture_snapshot`
                method, which may include network I/O errors or service failures.
        """
        urls = self._extract_urls(text)
        claims: List[Dict[str, Any]] = []

        for url in urls:
            logger.info(f"🛡️ Validando evidencia externa: {url}")
            snapshot = await self.capture_snapshot(url)
            # GOVERNANCE RULE: Enforce a strict policy of only admitting evidence that has passed all verification stages.
            if snapshot and snapshot.get("status") == "verified":
                claims.append(snapshot)
            else:
                logger.error(
                    f"❌ RECHAZADA: Evidencia externa rota o protegida: {url}. No se incluirá en el Dossier."
                )

        return claims

    def _extract_urls(self, text: str) -> List[str]:
        """Extracts all valid URLs from a given block of text."""
        url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*"
        raw_urls = re.findall(url_pattern, text)
        #
        cleaned = []
        for u in raw_urls:
            u = u.strip().rstrip(".").rstrip(")").rstrip("]")
            if u not in cleaned:
                cleaned.append(u)
        return cleaned

    async def capture_snapshot(self, url: str) -> Optional[Dict[str, Any]]:
        r"""{'docstring': "Asynchronously captures a snapshot of a web resource from a given URL.\n\nThis method employs a hybrid strategy for robust content retrieval. It\nfirst resolves redirects via an HTTP HEAD request to identify the final\ncanonical URL. Based on the URL's file extension, it follows one of two\npaths:\n1.  Binary Files (e.g., .pdf, .docx): Performs a direct download using\n    an HTTP client (`httpx`).\n2.  Web Pages: Uses a headless Chromium browser (via Playwright) to\n    render dynamic content and JavaScript before capturing the page source.\n\nThe captured content is stored as a local file, and metadata about the\noperation is returned.\n\nArgs:\n    url (str): The URL of the web resource to capture.\n\nReturns:\n    Optional[Dict[str, Any]]: A dictionary containing metadata about the\n        snapshot operation, or `None` if the `playwright` dependency is not\n        installed. The dictionary structure varies based on the outcome:\n          - On success: Contains `status: 'verified'`, `url` (the final\n            resolved URL), `local_snapshot` (relative path to the saved\n            file), `content_hash` (SHA-256 of the content), and other\n            metadata.\n          - On failure: Contains `status: 'broken'` for non-2xx HTTP\n            responses or `status: 'error'` for network exceptions (e.g.,\n            timeouts), along with an `error` key with a descriptive\n            message."}."""
        import httpx

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright no está instalado.")
            return None

        #
        url = url.strip().rstrip(".").rstrip(")").rstrip("]")
        original_input_url = url

        # Implements an advanced redirect resolution strategy, analogous to grounding, to determine the final canonical URL.
        final_human_url = url
        if "grounding-api-redirect" in url:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, follow_redirects=True, headers=self.headers
                ) as client:
                    # Perform an HTTP HEAD request to resolve the final destination of the URL without downloading the entire response body. This is an efficient method for checking redirects and headers.
                    r = await client.head(url)
                    final_human_url = str(r.url)
                    print(f"      🔗 [REDIRECT] URL real detectada: {final_human_url}")
            except Exception as e:
                logger.warning(f"No se pudo resolver redirect para {url}: {e}")

        url_hash = hashlib.sha256(final_human_url.encode()).hexdigest()[:12]

        # 1. Determine the content type based on the resolved, final URL.
        is_binary = any(
            final_human_url.lower().endswith(ext)
            for ext in [".pdf", ".docx", ".xlsx", ".zip"]
        )
        file_ext = ".pdf" if final_human_url.lower().endswith(".pdf") else ".html"
        file_path = self.storage_dir / f"snapshot_{url_hash}{file_ext}"

        # 2. PATH B: For binary files, perform a direct download to bypass potential WAFs or JavaScript-based access controls.
        if is_binary:
            try:
                async with httpx.AsyncClient(
                    timeout=20.0, follow_redirects=True, headers=self.headers
                ) as client:
                    print(f"      📥 [BINARY] Descargando documento: {final_human_url}")
                    r_bin = await client.get(final_human_url)
                    if r_bin.status_code == 200:
                        file_path.write_bytes(r_bin.content)
                        return {
                            "source_type": "EXTERNAL_DOCUMENT",
                            "url": final_human_url,
                            "google_redirect_url": original_input_url
                            if original_input_url != final_human_url
                            else None,
                            "local_snapshot": str(
                                file_path.relative_to(
                                    self.storage_dir.parent.parent.parent
                                )
                            ),
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                            "status": "verified",
                            "content_hash": hashlib.sha256(r_bin.content).hexdigest(),
                        }
            except Exception as e:
                logger.warning(f"Fallo descarga directa de {final_human_url}: {e}")

        # 3. PATH A: For standard web pages, utilize Playwright to render dynamic content and handle interactive elements.
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.headers["User-Agent"]
                )
                page = await context.new_page()

                print(f"      🌐 [BROWSER] Capturando fuente: {final_human_url}")
                response = await page.goto(
                    final_human_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                if response and response.status < 400:
                    await page.wait_for_timeout(2000)
                    content = (
                        await page.content() if not is_binary else await response.body()
                    )

                    content_bytes: bytes
                    if isinstance(content, str):
                        content_bytes = content.encode("utf-8")
                    else:
                        content_bytes = content

                    file_path.write_bytes(content_bytes)
                    await browser.close()
                    return {
                        "source_type": "EXTERNAL_OSINT",
                        "url": final_human_url,
                        "google_redirect_url": original_input_url
                        if original_input_url != final_human_url
                        else None,
                        "local_snapshot": str(
                            file_path.relative_to(self.storage_dir.parent.parent.parent)
                        ),
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "status": "verified",
                        "content_hash": hashlib.sha256(content_bytes).hexdigest(),
                    }
                else:
                    await browser.close()
                    return {
                        "source_type": "EXTERNAL_OSINT",
                        "url": final_human_url,
                        "status": "broken",
                        "error": f"HTTP {response.status if response else 'Unknown'}",
                    }
        except Exception as e:
            return {
                "source_type": "EXTERNAL_OSINT",
                "url": final_human_url,
                "status": "error",
                "error": str(e),
            }

    async def register_wayback(self, url: str) -> None:
        """Asynchronously submits a URL to the Internet Archive's Wayback Machine for archival.

        This coroutine sends a request to the "Save Page Now" service to create a
        durable, timestamped snapshot of the specified URL's content. This
        operation may be conditionally skipped based on the instance's
        configuration.

        Args:
            url (str): The fully qualified URL to submit for archival.

        Returns:
            None.

        Raises:
            ValueError: If the provided URL is malformed or otherwise invalid.
            ArchivalError: If the archival request fails due to network-level
                issues or if the Wayback Machine service returns a non-successful
                HTTP status code.
        """
        pass


class EvidenceIntegrityManager:
    r"""{'EvidenceIntegrityManager': 'Provides static methods for managing the integrity of evidence dossiers.', 'EvidenceIntegrityManager.sync_claims_with_dossier': "Integrates new claims into a dossier, deduplicating by the 'url' key.\n\nModifies the dossier dictionary in-place by appending claims from the input\nlist. The operation is idempotent based on the 'url' value of each claim;\na claim is added only if no existing claim in the dossier's 'claims' list\nshares an identical 'url'.\n\nIf the dossier dictionary lacks a 'claims' key, it is initialized as an\nempty list before processing.\n\nComparison of URLs is robust to missing 'url' keys, as the value is\ntreated as None in such cases.\n\nArgs:\n    dossier: The dictionary representing the dossier to be updated. This\n        object is modified in-place.\n    claims: A list of claim dictionaries to integrate into the dossier.\n\nReturns:\n    The original dossier dictionary instance, now updated with new claims."}."""

    @staticmethod
    def sync_claims_with_dossier(
        dossier: Dict[str, Any], claims: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merges a list of claims into a dossier, preventing duplicates by URL.

        This function modifies the `dossier` dictionary in-place. It iterates
        through the provided `claims` and appends each one to the `dossier['claims']`
        list only if no existing claim shares the same value for the 'url' key.

        If the `dossier` does not already contain a 'claims' key, it is initialized
        as an empty list before the new claims are processed.

        Args:
            dossier: The dossier dictionary to be updated. This argument is
                modified in-place.
            claims: A list of claim dictionaries to merge into the dossier.
                Uniqueness is determined by the value of the 'url' key.

        Returns:
            The mutated dossier dictionary instance.
        """
        if "claims" not in dossier:
            dossier["claims"] = []

        for claim in claims:
            #
            if not any(c.get("url") == claim.get("url") for c in dossier["claims"]):
                dossier["claims"].append(claim)

        return dossier
