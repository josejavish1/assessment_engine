"""Deterministic POSIX path and filename builder for assessment deliverables."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from assessment_engine.infrastructure.artifacts.domain import (
    ArtifactContext,
    InvalidArtifactTokenError,
)


class ArtifactPathResolver:
    """Stateless deterministic builder enforcing strict POSIX standards on filenames."""

    @classmethod
    def sanitize_token(cls, raw_token: str, max_length: int = 64) -> str:
        """Sanitizes raw strings into strict POSIX lowercase tokens ([a-z0-9_]+).

        Normalizes NFKD to strip diacritics, strips non-alphanumerics, collapses
        multiple underscores into one, and limits total length. Supports non-Latin
        scripts (CJK, Arabic, Cyrillic) via deterministic SHA-256 fallback.
        """
        if not raw_token or not str(raw_token).strip():
            raise InvalidArtifactTokenError("Artifact token cannot be empty or blank.")

        raw_str = str(raw_token).strip()
        normalized = unicodedata.normalize("NFKD", raw_str).encode("ascii", "ignore").decode("ascii")
        cleaned = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")

        if not cleaned:
            # Deterministic ASCII fallback for non-Latin scripts (CJK, Arabic, Cyrillic, Hebrew)
            if re.search(r"\w", raw_str, flags=re.UNICODE):
                token_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:10]
                cleaned = f"tok_{token_hash}"
            else:
                raise InvalidArtifactTokenError(
                    f"Token '{raw_token}' yielded an empty POSIX string after sanitization."
                )

        return cleaned[:max_length].rstrip("_")

    @classmethod
    def build_logical_key(cls, ctx: ArtifactContext) -> str:
        """Constructs unique logical identifier for the deliverable across versions."""
        unit_token = cls.sanitize_token(ctx.domain_unit_id)
        doc_token = ctx.doc_type.value
        loc_token = cls.sanitize_token(ctx.locale)
        ext_token = ctx.extension.value
        return f"{unit_token}::{doc_token}::{loc_token}::{ext_token}"

    @classmethod
    def build_physical_filename(
        cls, ctx: ArtifactContext, version: int, sha256_full: str
    ) -> str:
        """Constructs deterministic POSIX physical filename.

        Pattern: {tenant}_{period}_{unit}_{doc_type}_{locale}_v{version:03d}_{sha12}.{ext}
        """
        if version < 1:
            raise ValueError(f"Version must be a positive integer >= 1, got {version}.")
        if not sha256_full or len(str(sha256_full).strip()) < 12:
            raise ValueError("A valid SHA-256 checksum is required to build physical filename.")

        tenant = cls.sanitize_token(ctx.tenant_id, max_length=32)
        period = cls.sanitize_token(ctx.period, max_length=16)
        unit = cls.sanitize_token(ctx.domain_unit_id, max_length=32)
        doc_type = ctx.doc_type.value
        locale = cls.sanitize_token(ctx.locale, max_length=8)
        version_str = f"v{version:03d}"
        sha_short = str(sha256_full).strip().lower()[:12]
        ext = ctx.extension.value

        return f"{tenant}_{period}_{unit}_{doc_type}_{locale}_{version_str}_{sha_short}.{ext}"
