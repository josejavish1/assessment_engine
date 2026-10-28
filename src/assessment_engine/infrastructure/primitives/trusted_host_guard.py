"""
RFC 7230 Trusted Host Header & Anti-Cache Poisoning Guard — GEMA 62 (SOTA 2026).
Validates HTTP Host / X-Forwarded-Host headers against an authorized domain allowlist.
Prevents password-reset poisoning, cache poisoning, and Server-Side Request Forgery.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.trusted_host_guard")


class TrustedHostGuardPrimitive:
    """
    Validador de cabeceras Host HTTP conforme a RFC 7230.
    """

    def __init__(self, allowed_hosts: list[str] | None = None) -> None:
        self.allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1", "0.0.0.0", "*.local"]

    def is_host_allowed(self, host_header: str) -> bool:
        """Determine whether the received Host header is in the list of authorized hosts."""
        if not host_header:
            return False

        clean_host = host_header.split(":")[0].strip().lower()

        for pattern in self.allowed_hosts:
            pattern = pattern.lower().strip()
            if pattern == "*" or pattern == clean_host:
                return True
            if pattern.startswith("*."):
                suffix = pattern[1:]  # ej. .local
                if clean_host.endswith(suffix):
                    return True
            # Support direct IP addresses.
            if clean_host == pattern:
                return True

        logger.warning(f"[TrustedHostGuard] Cabecera Host sospechosa rechazada: '{host_header}'")
        return False


trusted_host_guard = TrustedHostGuardPrimitive()
