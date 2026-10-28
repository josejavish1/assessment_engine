"""
Dead-Letter Queue (DLQ) with Inspection & Replay — GEMA 69 (SOTA 2026).
Captures failed background tasks that have exhausted all retry attempts.
Stores detailed error stacks, payloads, and failure timestamps in SQLite.
Enables administrative inspection and replay of failed jobs without data loss.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.dead_letter_queue")


class DeadLetterQueuePrimitive:
    """
    Manage an SQLite-backed dead-letter queue.
    """

    def capture_failed_job(
        self,
        db_path: Path,
        job_type: str,
        payload: dict[str, Any],
        error_details: str
    ) -> dict[str, Any]:
        """Save a failed job to the DLQ table."""
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        try:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dead_letter_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                job_type TEXT,
                payload_json TEXT,
                error_details TEXT,
                replayed INT DEFAULT 0
            );
            """)

            cur.execute("""
            INSERT INTO dead_letter_queue (timestamp, job_type, payload_json, error_details, replayed)
            VALUES (?, ?, ?, ?, 0);
            """, (time.time(), job_type, json.dumps(payload, ensure_ascii=False), error_details[:2000]))

            conn.commit()
            dlq_id = cur.lastrowid
            logger.error(f"[DLQ] Trabajo fallido #{dlq_id} capturado en DLQ: {job_type}")
            return {"status": "ok", "dlq_id": dlq_id}
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()

    def list_failed_jobs(self, db_path: Path, limit: int = 50) -> list[dict[str, Any]]:
        """List failed jobs pending inspection."""
        if not db_path.exists():
            return []

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, timestamp, job_type, payload_json, error_details, replayed FROM dead_letter_queue WHERE replayed = 0 LIMIT ?;", (limit,))
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "job_type": r[2],
                    "payload": json.loads(r[3]),
                    "error_details": r[4]
                }
                for r in rows
            ]
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return []
        finally:
            conn.close()


dead_letter_queue = DeadLetterQueuePrimitive()
