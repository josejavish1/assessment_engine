"""
Canonical Security, Cryptography & Defense Engine — System 03 (Tier-1 SOTA 2026).
Consolidated security suite matching OWASP ASVS Level 2:
1. Column-level authenticated AES-128-CBC encryption (Fernet + PBKDF2-100k).
2. Time-bounded, tamper-evident Signed URLs with HMAC-SHA256 signatures.
3. Cryptographic Double-Submit stateless HMAC anti-CSRF protection.
4. Anti-Stored XSS rich text sanitizer with strict allowlist.
5. RFC 7230 Host header and anti-cache poisoning validator.
6. Zero-friction OWASP OAT-017 anti-spam honeypot form fields.
7. Sliding-window in-memory IP rate limiter and abuse shield.
8. Immutable append-only audit trail ledger in app.db.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import sqlite3
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from cryptography.fernet import Fernet

logger = logging.getLogger("assessment_engine.infrastructure.primitives.security")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))


def resolve_secret(env_var_name: str, fallback_len: int = 32) -> str:
    """Resolve a cryptographic secret from environment variables. In production (APP_ENV=production), fail fast if the variable is not injected.
In development/test environments, generate a secure random in-memory token (secrets.token_hex)."""
    val = os.environ.get(env_var_name)
    if val:
        return val
    if os.environ.get("APP_ENV") == "production":
        raise RuntimeError(
            f"CRITICAL SECURITY CONFIGURATION FAILURE: "
            f"Variable de entorno obligatoria '{env_var_name}' no declarada en entorno de producción."
        )
    return secrets.token_hex(fallback_len)


class SecurityEngine:
    """
    Provide canonical security, cryptography, and immutable auditing.
    """

    ALLOWED_TAGS = {"p", "b", "i", "strong", "em", "u", "ul", "ol", "li", "span", "br", "h1", "h2", "h3", "h4", "table", "tr", "td", "th", "tbody", "thead"}
    HONEYPOT_NAME = "_hp_website_verification"

    def __init__(self, master_secret: str | None = None) -> None:
        self.master_secret = master_secret or resolve_secret("MASTER_ENCRYPTION_SECRET")
        self.secret_bytes = self.master_secret.encode("utf-8")
        self._requests: dict[str, list[float]] = {}
        self.allowed_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "*.local", "*.autonomuos.app"]

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt the specified plaintext string."""
        from assessment_engine.infrastructure.primitives.column_encryption import column_encryption
        return column_encryption.encrypt_field(plaintext)

    def decrypt_field(self, token: str) -> str:
        """Decrypt the specified token into its original plaintext string."""
        from assessment_engine.infrastructure.primitives.column_encryption import column_encryption
        return column_encryption.decrypt_field(token)

    def generate_signed_url(self, base_url: str, resource_path: str, user_scope: str = "public", validity_seconds: int = 3600) -> str:
        """Generate a signed URL for a resource path with a specified scope and validity period."""
        from assessment_engine.infrastructure.primitives.signed_urls import signed_urls
        return signed_urls.generate_signed_url(base_url, resource_path, user_scope, validity_seconds)

    def verify_signed_url(self, resource_path: str, query_params: dict[str, str], expected_scope: str = "public") -> tuple[bool, str]:
        """Verify the signature, validity, and scope of a signed URL."""
        from assessment_engine.infrastructure.primitives.signed_urls import signed_urls
        return signed_urls.verify_signed_url(resource_path, query_params, expected_scope)

    def generate_csrf_token(self, session_id: str, ttl_seconds: int = 3600) -> str:
        """Generate a timed CSRF token bound to the specified session ID."""
        from assessment_engine.infrastructure.primitives.csrf_hmac_guard import csrf_hmac_guard
        return csrf_hmac_guard.generate_token(session_id, ttl_seconds)

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate the given CSRF token against the specified session ID."""
        from assessment_engine.infrastructure.primitives.csrf_hmac_guard import csrf_hmac_guard
        return csrf_hmac_guard.validate_token(token, session_id)

    def sanitize_html(self, raw_html: str) -> str:
        """Sanitize the provided raw HTML string to remove unsafe elements."""
        from assessment_engine.infrastructure.primitives.html_sanitizer import html_sanitizer
        return html_sanitizer.sanitize(raw_html)

    def is_host_allowed(self, host_header: str) -> bool:
        """Determine whether the specified host header is allowed."""
        from assessment_engine.infrastructure.primitives.trusted_host_guard import trusted_host_guard
        return trusted_host_guard.is_host_allowed(host_header)

    def generate_honeypot_html(self) -> str:
        """Generate HTML markup for a hidden honeypot spam prevention field."""
        from assessment_engine.infrastructure.primitives.honeypot_antispam import honeypot_antispam
        return honeypot_antispam.generate_honeypot_input_html()

    def is_spam_submission(self, form_data: dict[str, Any]) -> bool:
        """Determine whether the provided form data indicates a spam submission."""
        from assessment_engine.infrastructure.primitives.honeypot_antispam import honeypot_antispam
        return honeypot_antispam.is_spam(form_data)

    def check_rate_limit(self, client_key: str, limit: int = 60, window_seconds: float = 60.0) -> tuple[bool, int, float]:
        """Check whether a client request falls within the specified rate limit window."""
        from assessment_engine.infrastructure.primitives.rate_limiter import rate_limiter
        return rate_limiter.is_allowed(client_key, limit, window_seconds)

    def record_audit_event(self, slug: str, actor_id: str, action: str, entity_type: str, entity_id: str, payload_diff: dict[str, Any] | None = None, ip_address: str = "127.0.0.1") -> dict[str, Any]:
        """Record an audit log entry detailing an action performed on an entity."""
        from assessment_engine.infrastructure.primitives.audit_trail import audit_trail
        db_path = WORKSPACES_DIR / slug / "app.db"
        return audit_trail.record_event(db_path, actor_id, action, entity_type, entity_id, payload_diff, ip_address)


# Implement the consolidated canonical singleton.
security_engine = SecurityEngine()
