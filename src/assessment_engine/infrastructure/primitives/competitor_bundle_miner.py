# core/primitives/competitor_bundle_miner.py

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import re
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.competitor_bundle_miner")

NPM_MODULE_REGEX = re.compile(
    r"node_modules/(?:(@[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)|([a-zA-Z0-9_\-]+))/"
)
LICENSE_REGEX = re.compile(r"@license\s+([a-zA-Z0-9_\-@\/]+)", re.IGNORECASE)
ENDPOINT_REGEX = re.compile(r'["\'](/(?:api|v[0-9]+|trpc|graphql)/[a-zA-Z0-9_\-\/\.]+)["\']')


def extract_npm_packages(js_content: str) -> list[str]:
    """Extract npm package names agnostically from bundle paths and license banners."""
    if not js_content:
        return []
    packages: set[str] = set()
    for scoped, normal in NPM_MODULE_REGEX.findall(js_content):
        pkg = scoped or normal
        if pkg and not pkg.startswith((".", "_", "@types")):
            packages.add(pkg)

    for lic in LICENSE_REGEX.findall(js_content):
        clean_lic = lic.strip()
        if clean_lic and len(clean_lic) > 2 and not clean_lic.startswith((".", "_")):
            packages.add(clean_lic)

    return sorted(list(packages))


def extract_js_endpoints(js_content: str) -> list[str]:
    """Extract and sanitize internal API endpoints found in JavaScript source code."""
    if not js_content:
        return []
    matches = ENDPOINT_REGEX.findall(js_content)
    clean_endpoints: set[str] = set()
    for m in matches:
        if len(m) > 4 and not m.endswith((".js", ".css", ".png", ".jpg", ".svg", ".woff", ".woff2")):
            norm = re.sub(r"/[0-9a-fA-F-]{16,}", "/:id", m)
            norm = re.sub(r"/\d+", "/:id", norm)
            clean_endpoints.add(norm)
    return sorted(list(clean_endpoints))


def scan_js_code(js_content: str) -> dict[str, Any]:
    """Scan JavaScript content for third-party packages and API endpoints agnostically."""
    if not js_content:
        return {"libraries": [], "endpoints": []}

    found_packages = extract_npm_packages(js_content)
    endpoints = extract_js_endpoints(js_content)

    return {
        "libraries": found_packages,
        "endpoints": endpoints,
    }


def scan_bundle_directory(bundles_dir: Path) -> dict[str, Any]:
    """Scan a directory containing downloaded .js bundles."""
    if not bundles_dir.is_dir():
        return {"libraries": [], "endpoints": [], "total_bytes": 0}

    all_libs: set[str] = set()
    all_endpoints: set[str] = set()
    total_bytes = 0

    for js_path in bundles_dir.glob("*.js"):
        try:
            content = js_path.read_text(encoding="utf-8", errors="ignore")
            total_bytes += len(content)
            scan_res = scan_js_code(content)
            all_libs.update(scan_res["libraries"])
            all_endpoints.update(scan_res["endpoints"])
        except OSError as ex:
            logger.debug(f"[BundleMiner] Error leyendo bundle {js_path.name}: {ex}")

    return {
        "libraries": sorted(list(all_libs)),
        "endpoints": sorted(list(all_endpoints)),
        "total_bytes": total_bytes,
    }


def download_static_bundles(
    bundle_urls: list[str],
    output_dir: Path,
    max_bundles: int = 5,
    timeout_sec: float = 6.0,
) -> list[str]:
    """Safely download static bundles for offline forensic AST inspection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files: list[str] = []

    for url in bundle_urls[:max_bundles]:
        parsed = urllib.parse.urlparse(url)
        clean_name = Path(parsed.path).name or "bundle.js"
        if not clean_name.endswith(".js"):
            clean_name = f"{clean_name}.js"
        safe_name = re.sub(r"[^\w\-.]", "_", clean_name)
        out_file = output_dir / safe_name

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Autonomuos-Forensic-Scraper/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                content = resp.read()
                out_file.write_bytes(content)
                downloaded_files.append(str(out_file))
        except Exception as ex:
            logger.debug(f"[BundleMiner] Fallo descarga de {url}: {ex}")

    return downloaded_files


async def mine_javascript_bundles(
    bundle_urls: list[str],
    max_bundles: int = 4,
    timeout_sec: float = 3.0,
    max_bytes_per_bundle: int = 100_000,
) -> dict[str, list[str]]:
    """
    Fetch up to max_bundles directly into memory and scan for structural packages and endpoints.

    Zero-Disk architecture: does not write to the file system, avoiding ephemeral disk pollution.
    """
    if not bundle_urls:
        return {"libraries": [], "endpoints": []}

    detected_libs: set[str] = set()
    detected_endpoints: set[str] = set()

    def _fetch_and_scan(url: str) -> dict[str, Any]:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Autonomuos-Forensic-Scraper/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                raw_bytes = resp.read(max_bytes_per_bundle)
                content = raw_bytes.decode("utf-8", errors="ignore")
                return scan_js_code(content)
        except Exception as ex:
            logger.debug(f"[BundleMiner] Fallo en escaneo en memoria de {url}: {ex}")
            return {"libraries": [], "endpoints": []}

    loop = asyncio.get_running_loop()
    tasks = [
        loop.run_in_executor(None, _fetch_and_scan, u)
        for u in bundle_urls[:max_bundles]
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, dict):
            detected_libs.update(res.get("libraries", []))
            detected_endpoints.update(res.get("endpoints", []))

    return {
        "libraries": sorted(list(detected_libs)),
        "endpoints": sorted(list(detected_endpoints)),
    }
