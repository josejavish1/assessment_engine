"""
Durable Workflow & Execution Primitive (Tier-1 Host API).
Implements the Cloudflare Workflows / Temporal durable execution model:
Memoized step-by-step state checkpointing, durable timers, and asynchronous queue buffering.
"""

import json
import logging
import os
import sqlite3
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.workflow")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))


class DurableWorkflowPrimitive(CapabilityPrimitive):
    """Provide durable workflow and asynchronous queue primitives. Enable agents and automations to pause, wait for external events, and resume after crashes without losing state."""

    @property
    def namespace(self) -> str:
        """Return the namespace of the instance."""
        return "workflow"

    def get_capabilities(self) -> dict[str, Any]:
        """Retrieve a dictionary of supported capabilities."""
        return {
            "version": "1.0.0",
            "operations": [
                "step_do",
                "emit_event",
                "pop_event",
                "push_queue",
                "pop_queue",
                "schedule_task",
                "list_pending_tasks"
            ],
            "paradigm": "Durable Step Memoization (Cloudflare Workflows / Temporal Standard)",
            "crash_resilience": "Persistent WAL Checkpoints"
        }

    def _get_db(self, slug: str) -> sqlite3.Connection:
        db_path = WORKSPACES_DIR / slug / "data" / "workflow_state.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workflow_steps (
                workflow_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                error_msg TEXT,
                completed_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (workflow_id, step_name)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS message_queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS external_events (
                id TEXT PRIMARY KEY,
                event_name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                consumed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                payload_json TEXT DEFAULT '{}',
                run_at TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
        cur.close()
        return conn

    async def step_do(
        self,
        slug: str,
        workflow_id: str,
        step_name: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute a memoized step. If the step already executed successfully in a previous run, return the memoized result without re-running the function."""
        conn = self._get_db(slug)
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT result_json FROM workflow_steps
                WHERE workflow_id = ? AND step_name = ? AND status = 'completed';
            """, (workflow_id, step_name))
            row = cur.fetchone()
            if row:
                # Paso ya completado: replay determinista
                return json.loads(row["result_json"])

            # Execute the function.
            try:
                if asyncio_iscoroutinefunction(func):
                    res = await func(*args, **kwargs)
                else:
                    res = func(*args, **kwargs)

                res_json = json.dumps(res)
                cur.execute("""
                    INSERT INTO workflow_steps (workflow_id, step_name, status, result_json)
                    VALUES (?, ?, 'completed', ?)
                    ON CONFLICT(workflow_id, step_name) DO UPDATE SET
                        status='completed', result_json=excluded.result_json;
                """, (workflow_id, step_name, res_json))
                conn.commit()
                return res
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as step_err:
                cur.execute("""
                    INSERT INTO workflow_steps (workflow_id, step_name, status, error_msg)
                    VALUES (?, ?, 'failed', ?)
                    ON CONFLICT(workflow_id, step_name) DO UPDATE SET
                        status='failed', error_msg=excluded.error_msg;
                """, (workflow_id, step_name, str(step_err)))
                conn.commit()
                raise step_err
        finally:
            conn.close()

    def push_queue(self, slug: str, queue_name: str, payload: dict[str, Any]) -> int:
        """Enqueue a message asynchronously."""
        conn = self._get_db(slug)
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO message_queues (queue_name, payload_json)
                VALUES (?, ?);
            """, (queue_name, json.dumps(payload)))
            conn.commit()
            return cur.lastrowid or 0
        finally:
            conn.close()

    def pop_queue(self, slug: str, queue_name: str) -> dict[str, Any] | None:
        """Atomically dequeue the next pending message from the queue."""
        conn = self._get_db(slug)
        try:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE;")
            cur.execute("""
                SELECT id, payload_json FROM message_queues
                WHERE queue_name = ? AND status = 'pending'
                ORDER BY id ASC LIMIT 1;
            """, (queue_name,))
            row = cur.fetchone()
            if not row:
                conn.commit()
                return None

            msg_id = row["id"]
            cur.execute("UPDATE message_queues SET status = 'processed' WHERE id = ?;", (msg_id,))
            conn.commit()
            return {
                "id": msg_id,
                "payload": json.loads(row["payload_json"])
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            conn.rollback()
            raise
        finally:
            conn.close()

    def emit_event(self, slug: str, event_name: str, payload: dict[str, Any]) -> str:
        """Register an incoming event (webhook, external signal, or callback)."""
        conn = self._get_db(slug)
        ev_id = f"evt_{uuid.uuid4().hex[:10]}"
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO external_events (id, event_name, payload_json)
                VALUES (?, ?, ?);
            """, (ev_id, event_name, json.dumps(payload)))
            conn.commit()
            return ev_id
        finally:
            conn.close()

    def schedule_task(self, slug: str, task_name: str, payload: dict[str, Any], delay_seconds: int = 0) -> str:
        """Schedule a task for future execution."""
        conn = self._get_db(slug)
        task_id = f"tsk_{uuid.uuid4().hex[:10]}"
        run_at = (datetime.utcnow() + timedelta(seconds=delay_seconds)).isoformat()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO scheduled_tasks (id, task_name, payload_json, run_at)
                VALUES (?, ?, ?, ?);
            """, (task_id, task_name, json.dumps(payload), run_at))
            conn.commit()
            return task_id
        finally:
            conn.close()


def asyncio_iscoroutinefunction(func: Any) -> bool:
    """Determine whether the specified object is an asyncio coroutine function."""
    import inspect
    return inspect.iscoroutinefunction(func)


# Singleton export
workflow_primitive = DurableWorkflowPrimitive()
