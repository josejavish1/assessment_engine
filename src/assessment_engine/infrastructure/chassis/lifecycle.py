"""
Manage process lifecycle, graceful termination, and Kubernetes probes (RFC 016 - Phase 3).
Implement /livez, /readyz, /startupz, and SIGTERM/SIGINT handling with a grace period.
"""
from __future__ import annotations

import asyncio
import os
import signal
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from assessment_engine.infrastructure.chassis.structured_logger import get_structured_logger

logger = get_structured_logger("process_lifecycle")


class ProcessLifecycleManager:
    """Manage the ASGI server lifecycle."""

    def __init__(self, drain_timeout_seconds: float = 10.0) -> None:
        self.drain_timeout_seconds = drain_timeout_seconds
        self._is_started: bool = False
        self._is_ready: bool = False
        self._is_shutting_down: bool = False
        self._shutdown_hooks: list[Callable[[], Any]] = []

    @property
    def is_started(self) -> bool:
        """Return whether the instance has started."""
        return self._is_started

    @property
    def is_ready(self) -> bool:
        """Return whether the instance is ready."""
        return self._is_ready and not self._is_shutting_down

    @property
    def is_shutting_down(self) -> bool:
        """Return whether the instance is shutting down."""
        return self._is_shutting_down

    def mark_started(self) -> None:
        """Mark the instance as started."""
        self._is_started = True
        logger.info("process_startup_completed", timestamp=datetime.now(UTC).isoformat())

    def mark_ready(self) -> None:
        """Mark the instance as ready."""
        self._is_ready = True
        logger.info("process_readiness_achieved", timestamp=datetime.now(UTC).isoformat())

    def register_shutdown_hook(self, hook: Callable[[], Any]) -> None:
        """Register a hook to execute during graceful shutdown."""
        self._shutdown_hooks.append(hook)

    async def initiate_graceful_shutdown(self) -> None:
        """Initiate safe shutdown: disable readiness and execute hooks."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        logger.warning(
            "graceful_shutdown_initiated",
            drain_timeout_s=self.drain_timeout_seconds,
            timestamp=datetime.now(UTC).isoformat()
        )

        # Execute registered cleanup hooks (close pools, flush logs, etc.).
        for hook in self._shutdown_hooks:
            try:
                res = hook()
                if asyncio.iscoroutine(res):
                    await asyncio.wait_for(res, timeout=self.drain_timeout_seconds)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.error("shutdown_hook_failed", hook=repr(hook), error=str(ex))

        logger.info("graceful_shutdown_hooks_completed")

    def install_signal_handlers(self) -> None:
        """Install SIGTERM and SIGINT handlers in the main event loop."""
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s))
                )
            logger.info("lifecycle_signal_handlers_installed")
        except (NotImplementedError, RuntimeError):
            # En Windows o hilos secundarios add_signal_handler puede no estar disponible
            pass

    async def _handle_signal(self, sig: signal.Signals) -> None:
        logger.warning("termination_signal_received", signal=sig.name)
        await self.initiate_graceful_shutdown()


    def check_liveness(self) -> dict[str, Any]:
        """Check process and event loop responsiveness (/livez probe)."""
        return {
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat(),
            "pid": os.getpid()
        }

    def check_startup(self) -> dict[str, Any]:
        """Check that full initialization has completed (/startupz probe)."""
        if not self._is_started:
            raise HTTPException(status_code=503, detail="Application still initializing.")
        return {
            "status": "started",
            "timestamp": datetime.now(UTC).isoformat()
        }

    def check_readiness(self, workspace_path: Path | None = None, db_path: Path | None = None) -> dict[str, Any]:
        """Check that the node is ready to process traffic (/readyz probe)."""
        if self._is_shutting_down:
            raise HTTPException(status_code=503, detail="Server is draining connections.")
        if not self._is_ready:
            raise HTTPException(status_code=503, detail="Server is not ready for traffic.")

        if workspace_path and not workspace_path.exists():
            raise HTTPException(status_code=503, detail="Workspaces directory is unavailable.")

        # Check SQLite WAL status if a path is provided.
        if db_path and db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path), timeout=0.2)
                conn.execute("PRAGMA quick_check(1);").fetchall()
                conn.close()
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as err:
                raise HTTPException(status_code=503, detail=f"SQLite WAL contention error: {err}") from err

        return {
            "status": "ready",
            "timestamp": datetime.now(UTC).isoformat()
        }


lifecycle_manager = ProcessLifecycleManager()
