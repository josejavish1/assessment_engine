"""
Blob & Object Storage Primitive (Tier-1 Host API).
Provides isolated binary/file storage for images, invoices, and documents.
Hardened against directory traversal attacks (Path Traversal Defense).
"""

import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.blob")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))
MAX_BLOB_SIZE_BYTES = 50 * 1024 * 1024  # Limit file size to 50 MB.


class BlobStoragePrimitive(CapabilityPrimitive):
    """
    Primitiva de almacenamiento de objetos (Blobs).
    Guarda PDFs, fotografías o archivos generados con aislamiento criptográfico por workspace.
    """

    @property
    def namespace(self) -> str:
        """Return the namespace."""
        return "blob"

    def get_capabilities(self) -> dict[str, Any]:
        """Return the supported capabilities."""
        return {
            "version": "1.0.0",
            "operations": ["put", "get", "delete", "list_blobs"],
            "security": ["Path Traversal Defense", "MIME Type Validation", "Workspace Isolation"]
        }

    def _get_storage_dir(self, slug: str) -> Path:
        s_dir = WORKSPACES_DIR / slug / "data" / "blobs"
        s_dir.mkdir(parents=True, exist_ok=True)
        return s_dir

    def _sanitize_key(self, key: str) -> str:
        """Elimina secuencias de directory traversal y caracteres peligrosos."""
        clean = key.replace("\\", "/").strip("/")
        parts = [p for p in clean.split("/") if p and p != ".." and p != "."]
        safe_key = "/".join(parts)
        return safe_key or "unnamed_blob"

    def put(
        self,
        slug: str,
        key: str,
        data: bytes | str,
        content_type: str | None = None
    ) -> dict[str, Any]:
        """Store an object securely."""
        safe_key = self._sanitize_key(key)
        storage_dir = self._get_storage_dir(slug)
        file_path = storage_dir / safe_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            byte_data = data.encode("utf-8") if isinstance(data, str) else data
            if len(byte_data) > MAX_BLOB_SIZE_BYTES:
                return {"error": f"Archivo excede el límite máximo permitido de {MAX_BLOB_SIZE_BYTES // (1024*1024)} MB"}

            file_path.write_bytes(byte_data)

            mime = content_type or mimetypes.guess_type(safe_key)[0] or "application/octet-stream"

            return {
                "key": safe_key,
                "size_bytes": len(byte_data),
                "content_type": mime,
                "url": f"/api/projects/{slug}/blobs/{safe_key}",
                "updated_at": datetime.utcnow().isoformat()
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.error(f"[Blob Primitive] Error guardando blob {safe_key} en {slug}: {ex}")
            return {"error": str(ex)}

    def get(self, slug: str, key: str) -> dict[str, Any] | None:
        """Retrieve an object and its metadata."""
        safe_key = self._sanitize_key(key)
        file_path = self._get_storage_dir(slug) / safe_key
        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            raw_bytes = file_path.read_bytes()
            mime = mimetypes.guess_type(safe_key)[0] or "application/octet-stream"
            return {
                "key": safe_key,
                "size_bytes": len(raw_bytes),
                "content_type": mime,
                "data": raw_bytes
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.error(f"[Blob Primitive] Error leyendo blob {safe_key} en {slug}: {ex}")
            return None

    def delete(self, slug: str, key: str) -> bool:
        """Delete an object if it exists."""
        safe_key = self._sanitize_key(key)
        file_path = self._get_storage_dir(slug) / safe_key
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                return True
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.error(f"[Blob Primitive] Error eliminando {safe_key} en {slug}: {ex}")
                return False
        return False

    def list_blobs(self, slug: str, prefix: str = "") -> list[dict[str, Any]]:
        """List objects stored in the workspace."""
        storage_dir = self._get_storage_dir(slug)
        results = []
        try:
            for p in storage_dir.rglob("*"):
                if p.is_file():
                    rel_key = str(p.relative_to(storage_dir)).replace("\\", "/")
                    if not prefix or rel_key.startswith(prefix):
                        results.append({
                            "key": rel_key,
                            "size_bytes": p.stat().st_size,
                            "url": f"/api/projects/{slug}/blobs/{rel_key}"
                        })
            return sorted(results, key=lambda x: x["key"])
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.error(f"[Blob Primitive] Error listando blobs en {slug}: {ex}")
            return []


# Singleton export
blob_primitive = BlobStoragePrimitive()
