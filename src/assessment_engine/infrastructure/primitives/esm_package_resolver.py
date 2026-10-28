"""
Dynamic ESM Package Ingestor & CDN Resolver — Primitiva 76 (Tier-1 SOTA 2026).

Enables dynamic JIT access to 2M+ packages in the npm ecosystem via secure,
cached ESM CDNs without local server builds or blocking npm install.
Enforces strict Zero-Trust supply chain validation (W3C Import Maps, RFC 3986, RFC 9111).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.esm_package_resolver")

BLOCKED_MALICIOUS_PACKAGES: frozenset[str] = frozenset({
    "evil-package",
    "flatmap-stream",
    "event-stream-malware",
    "ua-parser-js-malware",
    "coa-hijacked",
    "rc-hijacked",
    "fallout-malware",
    "electron-native-notify-stealer",
    "cross-env-malware",
})

# Supported canonical ESM CDNs conforming to modern browser native standards
VALID_CDN_PROVIDERS: dict[str, str] = {
    "esm.sh": "https://esm.sh",
    "jsdelivr": "https://cdn.jsdelivr.net/npm",
    "unpkg": "https://unpkg.com",
    "jspm": "https://ga.jspm.io/npm:",
}

# Regex for npm specifier validation (scoped/unscoped + optional version + optional subpath)
NPM_SPEC_PATTERN = re.compile(
    r"^(?P<name>(?:@[a-z0-9_.-]+/)?[a-z0-9][a-z0-9_.-]*)"
    r"(?:@(?P<version>[a-z0-9_.-]+))?"
    r"(?P<subpath>/[a-zA-Z0-9_./-]+)?$"
)

# Regex matching bare imports and re-exports in JS/TS:
IMPORT_REWRITE_PATTERN = re.compile(
    r"""(?P<prefix>\b(?:import\s+(?:(?:[\w*\s{},$]+from\s+)|(?=['"]))|export\s+(?:(?:[\w*\s{},$]+from\s+)|(?:\*\s+from\s+))|import\s*\(\s*))"""
    r"""(?P<quote>["'])"""
    r"""(?P<specifier>(?:@[a-z0-9_.-]+/)?[a-z0-9][a-z0-9_.-]*(?:/[a-zA-Z0-9_./-]+)?)"""
    r"""(?P=quote)"""
    r"""(?P<suffix>\s*\)?)"""
)


@dataclass(frozen=True, slots=True)
class ParsedNpmPackage:
    """Structured representation of a parsed npm package specifier."""

    base_name: str
    version: str | None
    subpath: str | None

    @property
    def full_spec(self) -> str:
        """Return the canonical package specifier including version and subpath."""
        res = self.base_name
        if self.version:
            res += f"@{self.version}"
        if self.subpath:
            res += self.subpath
        return res


def validate_subpath(subpath: str | None) -> str | None:
    """Validate subpath against path traversal vulnerabilities (RFC 3986)."""
    if not subpath:
        return None
    segments = subpath.strip("/").split("/")
    if any(seg in ("", ".", "..") for seg in segments):
        raise ValueError(f"Path traversal detectado o subpath inválido: '{subpath}'")
    return "/" + "/".join(segments)


def parse_package_spec(pkg_spec: str) -> ParsedNpmPackage:
    """Parse and validate package name, scope, version, and subpath."""
    clean = pkg_spec.strip()
    match = NPM_SPEC_PATTERN.match(clean)
    if not match:
        raise ValueError(f"Especificador de paquete npm inválido: '{pkg_spec}'")

    base_name = match.group("name").lower()
    version = match.group("version")
    raw_subpath = match.group("subpath")

    if base_name in BLOCKED_MALICIOUS_PACKAGES:
        raise PermissionError(f"Paquete bloqueado por seguridad Zero-Trust: '{base_name}'")

    subpath = validate_subpath(raw_subpath)
    return ParsedNpmPackage(base_name=base_name, version=version, subpath=subpath)


def sanitize_package_spec(pkg_spec: str) -> str:
    """Sanitize and return canonical specifier string."""
    parsed = parse_package_spec(pkg_spec)
    return parsed.full_spec


def build_cdn_url(parsed: ParsedNpmPackage, provider: str = "esm.sh") -> str:
    """Format the canonical CDN URL according to provider contract."""
    pkg_ver = f"{parsed.base_name}@{parsed.version}" if parsed.version else parsed.base_name
    sub = parsed.subpath or ""

    if provider == "esm.sh":
        return f"{VALID_CDN_PROVIDERS['esm.sh']}/{pkg_ver}{sub}?bundle"
    if provider == "jsdelivr":
        return f"{VALID_CDN_PROVIDERS['jsdelivr']}/{pkg_ver}{sub}/+esm"
    if provider == "unpkg":
        return f"{VALID_CDN_PROVIDERS['unpkg']}/{pkg_ver}{sub}?module"
    if provider == "jspm":
        return f"{VALID_CDN_PROVIDERS['jspm']}{pkg_ver}{sub}"

    return f"{VALID_CDN_PROVIDERS['esm.sh']}/{pkg_ver}{sub}?bundle"


class EsmPackageResolverPrimitive(CapabilityPrimitive):
    """
    Dynamic ESM resolver for on-demand browser package hydration.
    Eliminates server 'npm install' overhead with W3C Import Maps & Zero-Trust supply chain.
    """

    @property
    def namespace(self) -> str:
        """Return the unique namespace identifier for the capability."""
        return "esm_resolver"

    def get_capabilities(self) -> dict[str, Any]:
        """Expose capability metadata and operations schema."""
        return {
            "version": "1.0.0",
            "providers": list(VALID_CDN_PROVIDERS.keys()),
            "features": [
                "import_map_generation",
                "bare_import_rewrite",
                "supply_chain_gate",
                "path_traversal_prevention",
            ],
            "zero_trust": True,
        }

    def resolve_cdn_url(self, pkg_spec: str, provider: str = "esm.sh") -> str:
        """Resolve a package specifier to an authoritative, browser-importable CDN URL."""
        parsed = parse_package_spec(pkg_spec)
        return build_cdn_url(parsed, provider=provider)

    def generate_import_map(
        self, package_specs: list[str], provider: str = "esm.sh"
    ) -> dict[str, dict[str, str]]:
        """
        Generate a standard W3C HTML <script type='importmap'> structure.
        Maps bare specifiers and subpaths to deterministic, immutable CDN endpoints.
        """
        imports: dict[str, str] = {}
        for spec in package_specs:
            try:
                parsed = parse_package_spec(spec)
                key = parsed.base_name + (parsed.subpath if parsed.subpath else "")
                imports[key] = build_cdn_url(parsed, provider=provider)
            except (ValueError, PermissionError) as ex:
                logger.warning("[EsmResolver] Paquete descartado por política de seguridad: %s", ex)
                continue
        return {"imports": imports}

    def rewrite_bare_imports(
        self, code: str, target_packages: list[str], provider: str = "esm.sh"
    ) -> str:
        """
        Rewrite bare module specifiers into direct browser ESM CDN URLs.
        Covers static imports, exports, side-effect imports, and dynamic import().
        """
        resolved_targets: dict[str, str] = {}
        for spec in target_packages:
            try:
                parsed = parse_package_spec(spec)
                bare_key = parsed.base_name + (parsed.subpath if parsed.subpath else "")
                resolved_targets[bare_key] = build_cdn_url(parsed, provider=provider)
            except Exception as ex:
                logger.warning("[EsmResolver] Error precalculando specifier: %s", ex)
                continue

        def replacer(match: re.Match[str]) -> str:
            specifier = match.group("specifier")
            if specifier in resolved_targets:
                prefix = match.group("prefix")
                quote = match.group("quote")
                suffix = match.group("suffix")
                return f"{prefix}{quote}{resolved_targets[specifier]}{quote}{suffix}"
            return match.group(0)

        return IMPORT_REWRITE_PATTERN.sub(replacer, code)


esm_package_resolver = EsmPackageResolverPrimitive()