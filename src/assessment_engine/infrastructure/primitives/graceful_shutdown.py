import sqlite3
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
from assessment_engine.infrastructure.config.sre_constants import HEARTBEAT_INTERVAL_SEC

def create_graceful_lifespan(db_path: Path):
    """Create a graceful lifespan context manager configured with the specified database path."""
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        """Manage the startup and shutdown lifespan events for the FastAPI application."""
        yield
        # Shut down cleanly following a SIGTERM signal.
        # Wait for active requests to drain.
        await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)
        # Force an SQLite checkpoint to merge the WAL into the main database file.
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except sqlite3.Error:
            pass
    return app_lifespan
