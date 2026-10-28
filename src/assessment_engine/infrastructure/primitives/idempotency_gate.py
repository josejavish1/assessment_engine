# Autonomuos Module: core/primitives/idempotency_gate.py
"""
Provide ASGI middleware for HTTP request idempotency. Protect mutating HTTP methods (POST, PUT, PATCH) against duplicate execution by atomically storing responses by 'Idempotency-Key' in SQLite WAL.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("assessment_engine.infrastructure.primitives.idempotency_gate")


class IdempotencyGate:
    """Manage SQLite persistence for idempotent responses."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def init_table(self) -> None:
        """Create the idempotency records table if it does not exist."""
        with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_records (
                idempotency_key TEXT PRIMARY KEY,
                status_code INTEGER NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

    def get_cached_response(self, key: str) -> Optional[tuple[int, dict[str, Any]]]:
        """Retrieve the stored status code and JSON payload for a given key."""
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                cursor = conn.execute(
                    "SELECT status_code, response_json FROM idempotency_records WHERE idempotency_key = ?;",
                    (key,)
                )
                row = cursor.fetchone()
                if row:
                    return row[0], json.loads(row[1])
        except (sqlite3.OperationalError, json.JSONDecodeError) as ex:
            logger.debug(f"[IdempotencyGate] Error consultando caché: {ex}")
        return None

    def store_response(self, key: str, status_code: int, response_data: dict[str, Any]) -> None:
        """Store the response atomically in SQLite WAL."""
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO idempotency_records VALUES (?, ?, ?, ?);",
                    (key, status_code, json.dumps(response_data, ensure_ascii=False), datetime.now(timezone.utc).isoformat())
                )
        except sqlite3.OperationalError as ex:
            logger.debug(f"[IdempotencyGate] Error almacenando respuesta: {ex}")


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware ASGI para FastAPI/Starlette que intercepta peticiones con cabecera
    'Idempotency-Key' o 'X-Idempotency-Key' y devuelve respuestas almacenadas previamente.
    """

    def __init__(self, app: Any, db_path: Path | str | None = None) -> None:
        super().__init__(app)
        resolved_path = Path(db_path) if db_path else Path("app.db")
        self.gate = IdempotencyGate(resolved_path)
        try:
            self.gate.init_table()
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.debug(f"[IdempotencyMiddleware] Initial table creation deferred: {ex}")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Dispatch the incoming request to the next endpoint and return the response."""
        # Audit mutating methods only.
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = (
            request.headers.get("Idempotency-Key") or
            request.headers.get("X-Idempotency-Key") or
            ""
        ).strip()

        if not idempotency_key:
            return await call_next(request)

        cached = self.gate.get_cached_response(idempotency_key)
        if cached:
            status_code, body_dict = cached
            logger.info(f"[Idempotency] HIT para clave '{idempotency_key}' (Status: {status_code})")
            return Response(
                content=json.dumps(body_dict, ensure_ascii=False).encode("utf-8"),
                status_code=status_code,
                media_type="application/json",
                headers={
                    "X-Idempotency-Hit": "true",
                    "X-Idempotency-Key": idempotency_key
                }
            )

        response = await call_next(request)

        if 200 <= response.status_code < 400:
            body_chunks = [chunk async for chunk in response.body_iterator]
            body_bytes = b"".join(body_chunks)

            try:
                parsed_json = json.loads(body_bytes.decode("utf-8"))
                self.gate.store_response(idempotency_key, response.status_code, parsed_json)
                logger.info(f"[Idempotency] STORE para clave '{idempotency_key}' (Status: {response.status_code})")
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass  # Do not cache if the response is not valid JSON.

            headers = dict(response.headers)
            headers["X-Idempotency-Hit"] = "false"
            headers["X-Idempotency-Key"] = idempotency_key

            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type
            )

        return response
