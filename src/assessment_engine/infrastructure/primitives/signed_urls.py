"""
Cryptographic Signed URL & Ephemeral Access Primitive — GEMA 37 (SOTA 2026).
Generates tamper-evident, time-bounded download and streaming URLs using HMAC-SHA256.
Ties access grants to specific resource paths, user scopes, and expiration epochs.
Protects sensitive private blobs (medical records, invoices, exports) against unauthorized URL enumeration.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
import urllib.parse
from typing import Any
from assessment_engine.infrastructure.primitives.security import resolve_secret

logger = logging.getLogger("assessment_engine.infrastructure.primitives.signed_urls")


class SignedURLsPrimitive:
    """
    Generate and validate cryptographically signed URLs using HMAC-SHA256.
    """

    def __init__(self, signing_secret: str | None = None) -> None:
        secret = signing_secret or resolve_secret("URL_SIGNING_SECRET")
        self.secret_bytes = secret.encode("utf-8")

    def generate_signed_url(
        self,
        base_url: str,
        resource_path: str,
        user_scope: str = "public",
        validity_seconds: int = 3600
    ) -> str:
        """Build a URL with an HMAC-SHA256 signature and expiration parameter."""
        clean_path = "/" + resource_path.lstrip("/")
        expires_at = int(time.time()) + validity_seconds

        canonical_msg = f"{clean_path}:{expires_at}:{user_scope}".encode("utf-8")
        signature = hmac.new(self.secret_bytes, canonical_msg, hashlib.sha256).hexdigest()

        query_params = {
            "expires": str(expires_at),
            "scope": user_scope,
            "sig": signature
        }

        base = base_url.rstrip("/")
        full_url = f"{base}{clean_path}?{urllib.parse.urlencode(query_params)}"
        return full_url

    def verify_signed_url(
        self,
        resource_path: str,
        query_params: dict[str, str],
        expected_scope: str = "public"
    ) -> tuple[bool, str]:
        """Verify that the signed URL is valid and has not expired.
Return (is_valid, error_reason)."""
        sig = query_params.get("sig")
        expires_str = query_params.get("expires")
        scope = query_params.get("scope", "public")

        if not sig or not expires_str:
            return False, "Parámetros de firma o expiración ausentes"

        try:
            expires_at = int(expires_str)
            if time.time() > expires_at:
                logger.warning(f"[SignedURLs] Enlace expirado para {resource_path}")
                return False, "El enlace temporal ha caducado"
        except ValueError:
            return False, "Parámetro de expiración inválido"

        if expected_scope != "*" and scope != expected_scope:
            return False, "Ámbito de usuario no autorizado para este recurso"

        clean_path = "/" + resource_path.lstrip("/")
        canonical_msg = f"{clean_path}:{expires_at}:{scope}".encode("utf-8")
        expected_sig = hmac.new(self.secret_bytes, canonical_msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(sig, expected_sig):
            logger.warning(f"[SignedURLs] Firma HMAC inválida detectada en {resource_path}")
            return False, "Firma de autenticación inválida o manipulada"

        return True, "OK"


signed_urls = SignedURLsPrimitive()
