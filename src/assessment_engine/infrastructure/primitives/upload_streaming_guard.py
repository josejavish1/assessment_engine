"""
Anti-OOM Streaming Chunked Upload Guard — GEMA 46 (RFC 7578 / SOTA 2026).
Streams multipart file uploads directly to temporary disk storage in 64KB chunks.
Enforces strict maximum payload size boundaries without consuming server heap RAM.
Prevents Out-Of-Memory denial of service crashes.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.primitives.upload_streaming_guard")


class UploadStreamingGuardPrimitive:
    """
    Stream file uploads directly to disk to prevent memory exhaustion.
    """

    def __init__(self, max_bytes: int = 50 * 1024 * 1024, chunk_size: int = 64 * 1024) -> None:
        self.max_bytes = max_bytes
        self.chunk_size = chunk_size

    async def save_stream_to_disk(
        self,
        stream_chunks: AsyncGenerator[bytes, None],
        destination_path: Path
    ) -> tuple[bool, int, str]:
        """Read chunks from the asynchronous stream and write them directly to disk. Returns: (success, total_bytes, error_or_path)"""
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        total_written = 0

        try:
            with open(destination_path, "wb") as f:
                async for chunk in stream_chunks:
                    total_written += len(chunk)
                    if total_written > self.max_bytes:
                        # Abort and delete partial file if the limit is exceeded.
                        f.close()
                        destination_path.unlink(missing_ok=True)
                        logger.warning(f"[UploadGuard] Subida rechazada: Superó el límite de {self.max_bytes} bytes")
                        return False, total_written, f"Payload Too Large: Exceeded {self.max_bytes} bytes"
                    f.write(chunk)

            logger.info(f"[UploadGuard] Archivo guardado de forma segura ({total_written} bytes): {destination_path.name}")
            return True, total_written, str(destination_path)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            destination_path.unlink(missing_ok=True)
            logger.error(f"[UploadGuard] Error escribiendo archivo en disco: {ex}")
            return False, total_written, str(ex)


upload_streaming_guard = UploadStreamingGuardPrimitive()
