"""
Cryptographic Double-Submit HMAC Anti-CSRF Guard — GEMA 63 (OWASP ASVS Level 2 / SOTA 2026).
Generates cryptographically signed stateless CSRF tokens tied to session IDs.
Validates state-changing HTTP requests (POST, PUT, DELETE, PATCH) against CSRF attacks.
Zero in-memory server state required.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time

logger = logging.getLogger("assessment_engine.infrastructure.primitives.csrf_hmac_guard")


class CSRFHMACGuardPrimitive:
    """
    Provide stateless anti-CSRF protection using HMAC.
    """

    def __init__(self, secret_key: str = "autonomuos-csrf-master-secret-key-32") -> None:
        self.secret_key = secret_key.encode("utf-8")

    def generate_token(self, session_id: str, ttl_seconds: int = 3600) -> str:
        """Generate a signed CSRF token with a timestamp and session_id."""
        nonce = secrets.token_hex(8)
        expires_at = int(time.time()) + ttl_seconds
        payload = f"{session_id}:{expires_at}:{nonce}"
        signature = hmac.new(self.secret_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{payload}:{signature}"

    def validate_token(self, token: str, session_id: str) -> bool:
        """Verify the validity and cryptographic signature of the CSRF token."""
        if not token:
            return False

        parts = token.split(":")
        if len(parts) != 4:
            return False

        t_session_id, t_expires_str, nonce, signature = parts

        if not hmac.compare_digest(t_session_id, session_id):
            logger.warning("[CSRF] Discrepancia en ID de sesión en token CSRF")
            return False

        # Validate expiration.
        try:
            expires_at = int(t_expires_str)
            if time.time() > expires_at:
                logger.warning("[CSRF] Token CSRF expirado")
                return False
        except ValueError:
            return False

        # Validar firma HMAC
        expected_payload = f"{t_session_id}:{expires_at}:{nonce}"
        expected_sig = hmac.new(self.secret_key, expected_payload.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            logger.warning("[CSRF] Firma criptográfica HMAC de token CSRF inválida")
            return False

        return True


csrf_hmac_guard = CSRFHMACGuardPrimitive()
