"""
Behavioral Telemetry & Friction Aggregator Primitive — GEMA 26 (SOTA 2026).
Companion backend engine for friction_sensor.ts client events.
Stores and analyzes rage clicks, error clicks, form hesitation, scroll milestones, and conversions.
Computes variant friction indices and conversion uplifts for the Darwinian closed loop in SQLite WAL.
Complies with RGPD Art. 5/32 (Zero PII storage). Zero external dependencies ($0.00 cost).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.friction_sensor")

SENSITIVE_KEY_PATTERNS = ("password", "passwd", "token", "secret", "card", "cvv", "credit")


@dataclass
class FrictionEventRecord:
    """Represent a structured behavioral telemetry event."""
    event_id: str
    variant_id: str
    session_id: str
    timestamp: float
    event_type: str                  # rage_click, dead_click, error_click, form_hesitation, scroll_milestone, conversion
    target_selector: str
    viewport_w: int = 1440
    viewport_h: int = 900
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class VariantFrictionSummary:
    """Represent an analytical summary of performance and friction by variant."""
    variant_id: str
    total_events: int
    total_sessions: int
    total_conversions: int
    conversion_rate_pct: float
    total_rage_clicks: int
    total_error_clicks: int
    avg_hesitation_ms: float
    friction_index: float            # 0.0 to 100.0 (lower is better; penalized by rage clicks and errors).
    total_dead_clicks: int = 0
    total_form_abandonments: int = 0


def _sanitize_details(details: dict[str, Any]) -> dict[str, Any]:
    """Filter and strictly redact sensitive keys in details."""
    clean: dict[str, Any] = {}
    for k, v in details.items():
        k_low = k.lower()
        if any(pat in k_low for pat in SENSITIVE_KEY_PATTERNS):
            clean[k] = "[REDACTED]"
        elif isinstance(v, (int, float, bool, str)):
            clean[k] = v
        else:
            clean[k] = str(v)[:100]
    return clean


def _safe_json_loads(raw_json: str) -> dict[str, Any]:
    """Safely parse JSON and return a dictionary."""
    try:
        data = json.loads(raw_json)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def _extract_hesitation_values(rows: list[sqlite3.Row]) -> list[float]:
    """Extract numerical hesitation values without deep nesting."""
    vals: list[float] = []
    for row in rows:
        d = _safe_json_loads(row["details_json"])
        val = d.get("hesitationMs")
        if isinstance(val, (int, float)):
            vals.append(float(val))
    return vals


class FrictionSensorPrimitive:
    """
    Motor de persistencia y agregación de telemetría conductual.
    Alimenta el torneo darwinista emparejando fricción con variantes A/B en SQLite WAL.
    """

    def ensure_table(self, conn: sqlite3.Connection) -> None:
        """Create the friction events table and indexes with PRAGMA journal_mode=WAL and synchronous=NORMAL."""
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS client_friction_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                variant_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                target_selector TEXT NOT NULL,
                viewport_w INTEGER NOT NULL,
                viewport_h INTEGER NOT NULL,
                details_json TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fric_variant ON client_friction_events(variant_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fric_type ON client_friction_events(event_type);")
        conn.commit()

    def record_events_batch(self, db_path: Path, events: list[FrictionEventRecord]) -> int:
        """Insert a batch of friction events atomically into SQLite."""
        if not events:
            return 0

        conn = sqlite3.connect(str(db_path))
        try:
            self.ensure_table(conn)
            rows = [
                (
                    e.event_id,
                    e.variant_id[:32],
                    e.session_id[:64],
                    e.timestamp or time.time(),
                    e.event_type[:32],
                    e.target_selector[:128],
                    e.viewport_w,
                    e.viewport_h,
                    json.dumps(_sanitize_details(e.details), ensure_ascii=False),
                )
                for e in events
            ]
            cur = conn.executemany("""
                INSERT OR IGNORE INTO client_friction_events
                (event_id, variant_id, session_id, timestamp, event_type, target_selector, viewport_w, viewport_h, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, rows)
            conn.commit()
            count = cur.rowcount if cur.rowcount is not None else len(rows)
            logger.info(f"[FrictionSensor] Insertados {count} eventos de fricción para variantes.")
            return count
        finally:
            conn.close()

    def compute_variant_summary(self, db_path: Path, variant_id: str) -> VariantFrictionSummary:
        """Compute the friction and conversion summary for a specific variant."""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            self.ensure_table(conn)

            # 1. Total events and unique sessions.
            cur = conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT session_id) FROM client_friction_events WHERE variant_id = ?",
                (variant_id,),
            )
            total_events, total_sessions = cur.fetchone()

            cur = conn.execute(
                "SELECT event_type, COUNT(*) as cnt FROM client_friction_events WHERE variant_id = ? GROUP BY event_type",
                (variant_id,),
            )
            type_counts = {row["event_type"]: row["cnt"] for row in cur.fetchall()}

            conversions = type_counts.get("conversion", 0)
            rage_clicks = type_counts.get("rage_click", 0)
            dead_clicks = type_counts.get("dead_click", 0)
            error_clicks = type_counts.get("error_click", 0)
            abandonments = type_counts.get("form_abandoned", 0)

            # 3. Mean form hesitation.
            cur = conn.execute(
                "SELECT details_json FROM client_friction_events WHERE variant_id = ? AND event_type = 'form_hesitation'",
                (variant_id,),
            )
            hesitation_vals = _extract_hesitation_values(cur.fetchall())
            avg_hesitation = round(sum(hesitation_vals) / len(hesitation_vals), 1) if hesitation_vals else 0.0

            conv_rate = round((conversions / total_sessions * 100.0), 2) if total_sessions > 0 else 0.0

            # 5. Friction index (0 = optimal, 100 = maximum failure saturation).
            penalty_rage = min(35.0, (rage_clicks * 5.0) + (dead_clicks * 2.5))
            penalty_error = min(35.0, error_clicks * 10.0)
            penalty_hesitation = min(15.0, (avg_hesitation / 5000.0) * 10.0)
            penalty_abandonment = min(15.0, abandonments * 5.0)
            friction_idx = round(min(100.0, penalty_rage + penalty_error + penalty_hesitation + penalty_abandonment), 1)

            return VariantFrictionSummary(
                variant_id=variant_id,
                total_events=total_events,
                total_sessions=total_sessions,
                total_conversions=conversions,
                conversion_rate_pct=conv_rate,
                total_rage_clicks=rage_clicks,
                total_error_clicks=error_clicks,
                avg_hesitation_ms=avg_hesitation,
                friction_index=friction_idx,
                total_dead_clicks=dead_clicks,
                total_form_abandonments=abandonments,
            )
        finally:
            conn.close()

    def compare_variants(
        self, db_path: Path, variant_a: str = "A", variant_b: str = "B"
    ) -> dict[str, Any]:
        """Statistically compare two variants and determine the winner."""
        summary_a = self.compute_variant_summary(db_path, variant_a)
        summary_b = self.compute_variant_summary(db_path, variant_b)

        conv_diff = round(summary_b.conversion_rate_pct - summary_a.conversion_rate_pct, 2)
        fric_diff = round(summary_b.friction_index - summary_a.friction_index, 2)

        winner = "B" if conv_diff > 0.0 or (conv_diff == 0.0 and fric_diff < 0.0) else "A"
        if summary_a.total_sessions < 5 and summary_b.total_sessions < 5:
            winner = "INSUFFICIENT_DATA"

        return {
            "variant_a": asdict(summary_a),
            "variant_b": asdict(summary_b),
            "conversion_uplift_pct": conv_diff,
            "friction_delta": fric_diff,
            "winner": winner,
        }


# Canonical singleton instance.
friction_sensor = FrictionSensorPrimitive()
