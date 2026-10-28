"""
Column & Field-Level Encryption Primitive — GEMA 40 (SOTA 2026).
Implements AES-128-CBC authenticated symmetric encryption (Fernet specification)
with PBKDF2-HMAC-SHA256 key derivation (100,000 rounds) and per-record random salting.
Protects sensitive PII (microchips, medical notes, credit cards) at rest in SQLite.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
from typing import Any
from cryptography.fernet import Fernet, InvalidToken
from assessment_engine.infrastructure.primitives.security import resolve_secret

logger = logging.getLogger("assessment_engine.infrastructure.primitives.column_encryption")


class ColumnEncryptionPrimitive:
    """
    Provide column-level symmetric encryption compliant with banking standards.
    """

    def __init__(self, master_secret: str | None = None) -> None:
        self.master_secret = master_secret or resolve_secret("MASTER_ENCRYPTION_SECRET")

    def _derive_fernet_key(self, salt_bytes: bytes) -> bytes:
        """Derive a 32-byte Fernet-compatible key using PBKDF2-HMAC-SHA256."""
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            self.master_secret.encode("utf-8"),
            salt_bytes,
            100000,
            dklen=32
        )
        return base64.urlsafe_b64encode(derived)

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a plaintext value and return a serialized 'v1:salt:token' token."""
        if plaintext is None or plaintext == "":
            return ""

        salt = secrets.token_bytes(16)
        fernet_key = self._derive_fernet_key(salt)
        f = Fernet(fernet_key)

        encrypted_bytes = f.encrypt(plaintext.encode("utf-8"))
        salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
        cipher_b64 = encrypted_bytes.decode("utf-8")

        return f"v1:{salt_b64}:{cipher_b64}"

    def decrypt_field(self, encrypted_token: str) -> str:
        """Decrypt a token previously encrypted with the master key."""
        if not encrypted_token or not encrypted_token.startswith("v1:"):
            return encrypted_token

        try:
            parts = encrypted_token.split(":", 2)
            if len(parts) != 3:
                return encrypted_token

            _, salt_b64, cipher_b64 = parts
            salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
            fernet_key = self._derive_fernet_key(salt)
            f = Fernet(fernet_key)

            decrypted_bytes = f.decrypt(cipher_b64.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except (InvalidToken, RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.warning(f"[ColumnEncryption] Error descifrando campo: {ex}")
            return ""


column_encryption = ColumnEncryptionPrimitive()
