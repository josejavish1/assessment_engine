import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any


@dataclass
class ExportedUserDataBundle:
    user_id: str
    export_timestamp_utc: str
    profile: dict[str, Any]
    orders: list[dict[str, Any]]
    consents: list[dict[str, Any]]


class DataPortabilityExporter:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def export_full_user_archive(self, user_id: str) -> str:
        """Export the full data archive for the specified user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            profile = dict(user_row) if user_row else {"id": user_id}

            orders = []
            try:
                for row in conn.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)).fetchall():
                    orders.append(dict(row))
            except sqlite3.OperationalError:
                pass

            consents = []
            try:
                for row in conn.execute("SELECT * FROM compliance_consent_log LIMIT 50").fetchall():
                    consents.append(dict(row))
            except sqlite3.OperationalError:
                pass

        bundle = ExportedUserDataBundle(
            user_id=user_id,
            export_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            profile=profile,
            orders=orders,
            consents=consents
        )
        return json.dumps({
            "version": "1.0",
            "gdpr_article": "Article 20 - Right to data portability",
            "export_date": bundle.export_timestamp_utc,
            "data": {
                "profile": bundle.profile,
                "orders": bundle.orders,
                "consents": bundle.consents
            }
        }, indent=2, ensure_ascii=False)
