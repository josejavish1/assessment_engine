"""
SQLite Automated Maintenance Primitive — GEMA 57 (SOTA 2026).
Executes PRAGMA optimize, incremental_vacuum, and WAL checkpoint management
to maintain sub-1ms query latency and prevent database fragmentation over time.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.sqlite_maintenance")


class SQLiteMaintenancePrimitive:
    """
    Perform deterministic SQLite database maintenance in production.
    """

    def run_maintenance(self, db_path: Path) -> dict[str, Any]:
        """Execute index optimization, page reclamation, and WAL checkpointing."""
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA optimize;")

            cur.execute("PRAGMA wal_checkpoint(PASSIVE);")
            checkpoint_info = cur.fetchone()

            cur.execute("PRAGMA auto_vacuum;")
            auto_vac = cur.fetchone()[0]
            if auto_vac == 2:  # Incremental vacuum habilitado
                cur.execute("PRAGMA incremental_vacuum(50);")

            file_size_bytes = db_path.stat().st_size

            logger.info(f"[SQLiteMaintenance] Mantenimiento completado en {db_path.name} ({file_size_bytes} bytes)")
            return {
                "status": "ok",
                "database": db_path.name,
                "size_bytes": file_size_bytes,
                "wal_checkpoint": checkpoint_info
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[SQLiteMaintenance] Error ejecutando mantenimiento: {ex}")
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()


sqlite_maintenance = SQLiteMaintenancePrimitive()
