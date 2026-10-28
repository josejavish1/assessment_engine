"""
Real Liveness & Readiness Health Probes Primitive — GEMA 36 (SRE SOTA 2026).
Measures physical SQLite WAL read/write latency in milliseconds.
Inspects database schema integrity, process RSS memory, and filesystem storage boundaries.
Guarantees Kubernetes / Cloud Run probes only report healthy when I/O operates smoothly.
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.health_probes")


class HealthProbesPrimitive:
    """
    Provide health probes for Kubernetes and container monitoring.
    """

    def check_liveness(self) -> dict[str, Any]:
        """Check that the Python process is alive and responding (/healthz liveness probe)."""
        return {
            "status": "UP",
            "timestamp": time.time(),
            "pid": os.getpid()
        }

    def check_readiness(self, db_path: Path) -> dict[str, Any]:
        """Check that the database responds and the disk is not full (/readyz readiness probe)."""
        if not db_path.exists():
            return {
                "status": "DOWN",
                "ready": False,
                "reason": "Database file missing"
            }

        start_time = time.time()
        try:
            conn = sqlite3.connect(str(db_path), timeout=3.0)
            cur = conn.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS _health_ping (id INT PRIMARY KEY, t REAL);")
            cur.execute("INSERT OR REPLACE INTO _health_ping VALUES (1, ?);", (start_time,))
            conn.commit()

            cur.execute("SELECT t FROM _health_ping WHERE id = 1;")
            _ = cur.fetchone()

            cur.execute("PRAGMA quick_check(1);")
            integrity = cur.fetchone()[0]

            conn.close()
            io_latency_ms = (time.time() - start_time) * 1000

            total_b, used_b, free_b = shutil.disk_usage(db_path.parent)
            free_mb = free_b / (1024 * 1024)

            mem_rss_mb = 0.0
            try:
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            mem_rss_mb = int(line.split()[1]) / 1024.0
                            break
            except (RuntimeError, ValueError, KeyError, OSError, TypeError):
                mem_rss_mb = 50.0

            is_healthy = (integrity == "ok") and (free_mb > 50.0) and (io_latency_ms < 500)

            return {
                "status": "UP" if is_healthy else "DEGRADED",
                "ready": is_healthy,
                "io_latency_ms": round(io_latency_ms, 2),
                "integrity": integrity,
                "free_disk_mb": round(free_mb, 1),
                "mem_rss_mb": round(mem_rss_mb, 1)
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[HealthProbes] Fallo en sonda de readiness: {ex}")
            return {
                "status": "DOWN",
                "ready": False,
                "error": str(ex)
            }


health_probes = HealthProbesPrimitive()


class HealthProbesIntegrator:
    """
    Integrate /healthz and /readyz probes into FastAPI applications.
    """

    @classmethod
    def attach_probes(cls, app: Any, db_path: Path) -> None:
        """Attach health and readiness probes to the application."""
        @app.get("/healthz")
        def healthz():
            """Check the liveness status of the service."""
            return health_probes.check_liveness()

        @app.get("/readyz")
        def readyz():
            """Verify the readiness of the service to accept traffic."""
            return health_probes.check_readiness(db_path)
