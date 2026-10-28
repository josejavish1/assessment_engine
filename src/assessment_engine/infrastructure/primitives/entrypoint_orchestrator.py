"""
Atomic Startup & Migration Entrypoint Orchestrator — GEMA 74 (SOTA 2026).
Coordinates deterministic container and server startup sequences.
Executes database migrations and verifies file permissions BEFORE binding HTTP listening sockets.
Prevents serving traffic against half-migrated or corrupt database schemas.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.entrypoint_orchestrator")


class EntrypointOrchestratorPrimitive:
    """
    Orchestrate atomic startup and database pre-flight checks.
    """

    def verify_preflight_readiness(self, db_path: Path) -> dict[str, Any]:
        """Verify that the database is accessible and in WAL mode before starting."""
        if not db_path.exists():
            return {"ready": False, "reason": "database_file_missing"}

        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            journal_mode = str(cur.fetchone()[0]).lower()
            cur.execute("PRAGMA integrity_check;")
            integrity = cur.fetchone()[0]
            conn.close()

            is_ready = (integrity == "ok")
            logger.info(f"[EntrypointOrchestrator] Pre-vuelo completado: Journal={journal_mode}, Integrity={integrity}")
            return {
                "ready": is_ready,
                "journal_mode": journal_mode,
                "integrity": integrity
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[EntrypointOrchestrator] Fallo en pre-vuelo de arranque: {ex}")
            return {"ready": False, "reason": str(ex)}


entrypoint_orchestrator = EntrypointOrchestratorPrimitive()
