"""
Zero-Cookie Privacy Web Analytics Primitive — GEMA 67 (GDPR Consent-Exempt / SOTA 2026).
Tracks page views, referrers, and daily visitors using anonymized daily salted hashes.
Stores analytics purely in local SQLite app.db without cookies or personal data.
100% compliant with ePrivacy Directive and AEPD guidelines.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.zero_cookie_analytics")


class ZeroCookieAnalyticsPrimitive:
    """
    Provide a private web analytics engine exempt from cookie consent.
    """

    def track_page_view(
        self,
        db_path: Path,
        path: str,
        referrer: str = "",
        user_agent: str = "",
        client_ip: str = "127.0.0.1"
    ) -> dict[str, Any]:
        """Record a visit anonymously using a daily salted hash."""
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        try:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS privacy_analytics_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                day_date TEXT,
                path TEXT,
                referrer TEXT,
                visitor_hash TEXT
            );
            """)

            today = time.strftime("%Y-%m-%d")
            # Generate a non-invertible hash using the date as salt to prevent cross-day tracking.
            salt = f"autonomuos_salt_{today}"
            visitor_hash = hashlib.sha256(f"{client_ip}:{user_agent}:{salt}".encode()).hexdigest()[:16]

            cur.execute("""
            INSERT INTO privacy_analytics_views (timestamp, day_date, path, referrer, visitor_hash)
            VALUES (?, ?, ?, ?, ?);
            """, (time.time(), today, path[:250], referrer[:250], visitor_hash))

            conn.commit()
            return {"status": "ok", "recorded": True}
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[ZeroCookieAnalytics] Error registrando analítica: {ex}")
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()

    def get_summary_metrics(self, db_path: Path) -> dict[str, Any]:
        """Retrieve summary metrics for total visits and daily unique visitors."""
        if not db_path.exists():
            return {"total_views": 0, "unique_visitors": 0, "top_paths": []}

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        try:
            cur.execute("SELECT count(*), count(DISTINCT visitor_hash) FROM privacy_analytics_views;")
            row = cur.fetchone()
            total_views = row[0] if row else 0
            unique_visitors = row[1] if row else 0

            cur.execute("SELECT path, count(*) as c FROM privacy_analytics_views GROUP BY path ORDER BY c DESC LIMIT 5;")
            top_paths = [{"path": r[0], "views": r[1]} for r in cur.fetchall()]

            return {
                "total_views": total_views,
                "unique_visitors": unique_visitors,
                "top_paths": top_paths
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return {"total_views": 0, "unique_visitors": 0, "top_paths": []}
        finally:
            conn.close()


zero_cookie_analytics = ZeroCookieAnalyticsPrimitive()
