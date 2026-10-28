"""
Client-Side Crash & Error Telemetry Beacon — GEMA 20 (SOTA 2026).
Captures uncaught browser errors (window.onerror, unhandledrejection) via navigator.sendBeacon.
Stores telemetry events in local SQLite app.db for autonomous agent diagnostics.
Eliminates third-party trackers (Sentry/Datadog) in development and local sovereign mode.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.telemetry_beacon")


class TelemetryBeaconPrimitive:
    """
    Capture client telemetry and errors in SQLite.
    """

    def record_client_error(
        self,
        db_path: Path,
        error_type: str,
        message: str,
        stack_trace: str = "",
        url: str = "",
        user_agent: str = ""
    ) -> dict[str, Any]:
        """Record an error from the user's browser in SQLite."""
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        try:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS client_telemetry_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                error_type TEXT,
                message TEXT,
                stack_trace TEXT,
                url TEXT,
                user_agent TEXT
            );
            """)

            cur.execute("""
            INSERT INTO client_telemetry_errors (timestamp, error_type, message, stack_trace, url, user_agent)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (time.time(), error_type, message[:1000], stack_trace[:2000], url[:500], user_agent[:300]))

            conn.commit()
            error_id = cur.lastrowid
            logger.info(f"[TelemetryBeacon] Error de cliente registrado (#{error_id}): {error_type} - {message[:80]}")
            return {"status": "ok", "error_id": error_id}
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[TelemetryBeacon] Error registrando telemetría: {ex}")
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()

    def get_recent_errors(self, db_path: Path, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve the most recent errors for agent diagnosis."""
        if not db_path.exists():
            return []

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, timestamp, error_type, message, stack_trace, url FROM client_telemetry_errors ORDER BY id DESC LIMIT ?;", (limit,))
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "error_type": r[2],
                    "message": r[3],
                    "stack_trace": r[4],
                    "url": r[5]
                }
                for r in rows
            ]
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return []
        finally:
            conn.close()


telemetry_beacon = TelemetryBeaconPrimitive()
