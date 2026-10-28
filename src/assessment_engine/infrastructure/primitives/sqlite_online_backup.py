"""
SQLite Hot Online Backup Engine — GEMA 75 (SOTA 2026).
Utilizes the official sqlite3_backup C-API for hot, atomic database snapshots.
Creates consistent zero-downtime backups while active read/write queries continue concurrently.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.sqlite_online_backup")


class SQLiteOnlineBackupPrimitive:
    """
    Provide an atomic hot backup engine for SQLite WAL.
    """

    def create_hot_backup(self, source_db: Path, backup_dir: Path) -> dict[str, Any]:
        """Copy the live database to a timestamped backup file."""
        if not source_db.exists():
            return {"status": "error", "message": "Source database not found"}

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target_file = backup_dir / f"{source_db.stem}_backup_{timestamp}.db"

        start_time = time.time()
        source_conn = sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
        dest_conn = sqlite3.connect(str(target_file))

        try:
            source_conn.backup(dest_conn, pages=100)
            elapsed_ms = (time.time() - start_time) * 1000
            file_size_bytes = target_file.stat().st_size

            logger.info(f"[SQLiteBackup] Respaldo en caliente completado: {target_file.name} ({file_size_bytes} bytes en {elapsed_ms:.1f}ms)")
            return {
                "status": "ok",
                "backup_file": str(target_file),
                "file_name": target_file.name,
                "size_bytes": file_size_bytes,
                "elapsed_ms": round(elapsed_ms, 2)
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[SQLiteBackup] Error en respaldo en caliente: {ex}")
            return {"status": "error", "message": str(ex)}
        finally:
            dest_conn.close()
            source_conn.close()


sqlite_online_backup = SQLiteOnlineBackupPrimitive()
