"""
High-density HTTP payload compression primitive (RFC 7932).
Provides Brotli compression (with Gzip fallback) for HTML, JS, CSS, and JSON payloads.
Achieves up to 26% higher compression density than standard Gzip.
"""

from __future__ import annotations

import gzip
import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.brotli_compression")

try:
    import brotli  # type: ignore
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False


class BrotliCompressionPrimitive:
    """High-density compression engine for HTTP responses and static bundles."""

    def compress_payload(self, raw_data: bytes | str, quality: int = 4) -> tuple[bytes, str]:
        """Compress payload data using Brotli with fallback to Gzip."""
        if isinstance(raw_data, str):
            raw_data = raw_data.encode("utf-8")

        if len(raw_data) < 256:
            # Payload too small to compress efficiently
            return raw_data, "identity"

        if HAS_BROTLI:
            try:
                compressed = brotli.compress(raw_data, quality=quality)
                return compressed, "br"
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.debug(f"Brotli compression fallback: {ex}")

        compressed = gzip.compress(raw_data, compresslevel=6)
        return compressed, "gzip"

    def decompress_payload(self, compressed_data: bytes, encoding: str) -> bytes:
        """Decompress payload bytes according to Content-Encoding header."""
        if encoding == "br" and HAS_BROTLI:
            return brotli.decompress(compressed_data)
        if encoding == "gzip":
            return gzip.decompress(compressed_data)
        return compressed_data


brotli_compression = BrotliCompressionPrimitive()
