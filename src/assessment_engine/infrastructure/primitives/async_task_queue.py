"""
SQLite-Backed Background Task & Job Queue Primitive — GEMA 33 (SqliteHuey / SOTA 2026).
Enqueues asynchronous tasks in local SQLite app.db for background execution.
Tracks pending, running, completed, and failed job states with retry counts.
Zero external Redis or Celery infrastructure required.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.async_task_queue")


class AsyncTaskQueuePrimitive:
    """
    Manage an SQLite-persisted background task queue.
    """

    def enqueue_job(
        self,
        db_path: Path,
        job_type: str,
        payload: dict[str, Any],
        max_retries: int = 3
    ) -> dict[str, Any]:
        """Enqueue a new job in SQLite."""
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        try:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS background_task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at REAL,
                job_type TEXT,
                payload_json TEXT,
                status TEXT, -- 'pending', 'running', 'completed', 'failed'
                retries_left INT,
                error_msg TEXT
            );
            """)

            cur.execute("""
            INSERT INTO background_task_queue (created_at, job_type, payload_json, status, retries_left, error_msg)
            VALUES (?, ?, ?, 'pending', ?, '');
            """, (time.time(), job_type, json.dumps(payload, ensure_ascii=False), max_retries))

            conn.commit()
            job_id = cur.lastrowid
            logger.info(f"[AsyncTaskQueue] Trabajo #{job_id} ({job_type}) encolado.")
            return {"status": "ok", "job_id": job_id}
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()

    def fetch_next_job(self, db_path: Path) -> dict[str, Any] | None:
        """Dequeue the next pending job from the queue."""
        if not db_path.exists():
            return None

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, job_type, payload_json, retries_left FROM background_task_queue WHERE status = 'pending' ORDER BY id ASC LIMIT 1;")
            row = cur.fetchone()
            if not row:
                return None

            job_id, job_type, payload_str, retries = row
            cur.execute("UPDATE background_task_queue SET status = 'running' WHERE id = ?;", (job_id,))
            conn.commit()

            return {
                "job_id": job_id,
                "job_type": job_type,
                "payload": json.loads(payload_str),
                "retries_left": retries
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return None
        finally:
            conn.close()

    def mark_completed(self, db_path: Path, job_id: int) -> bool:
        """Mark a job as successfully completed."""
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        try:
            cur.execute("UPDATE background_task_queue SET status = 'completed' WHERE id = ?;", (job_id,))
            conn.commit()
            return True
        finally:
            conn.close()


async_task_queue = AsyncTaskQueuePrimitive()
