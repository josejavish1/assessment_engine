import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GraphEvent(BaseModel):
    """
    Tier-1 Sovereign Graph Event.
    Enables Bitemporal tracking and immutability.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    predicate: str
    object_val: str
    source: str
    confidence: float
    timestamp: float = Field(default_factory=lambda: time.time())
    valid_from: float = Field(default_factory=lambda: time.time())
    valid_to: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EpistemicGraph:
    """
    Tier-1 Sovereign Epistemic Graph (V3).
    Implements Bitemporal CQRS with persistent Ledger and Materialized View.
    """

    def __init__(self, client_id: str = "generic"):
        self.client_id = client_id
        # Sovereign Ledger Persistence
        self.ledger_path = Path(f"working/{client_id}/epistemic_ledger.jsonl")
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # Read Model (Materialized View in Memory SQLite)
        self.conn = sqlite3.connect(":memory:")
        self._init_db()
        self._replay_ledger()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE knowledge (
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp REAL NOT NULL,
                valid_from REAL NOT NULL,
                valid_to REAL,
                event_id TEXT PRIMARY KEY
            )
        """)
        self.conn.commit()

    def _replay_ledger(self):
        """Reconstructs the materialized view from the immutable ledger."""
        if not self.ledger_path.exists():
            return

        with open(self.ledger_path, "r") as f:
            for line in f:
                try:
                    event_data = json.loads(line)
                    event = GraphEvent(**event_data)
                    self._materialize(event)
                except Exception:
                    continue  # Robustness: skip corrupted lines

    def _materialize(self, event: GraphEvent):
        """Projects an event into the materialized view."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge
            (subject, predicate, object, source, confidence, timestamp, valid_from, valid_to, event_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.subject.upper(),
                event.predicate.upper(),
                event.object_val,
                event.source.upper(),
                float(event.confidence),
                event.timestamp,
                event.valid_from,
                event.valid_to,
                event.event_id,
            ),
        )
        self.conn.commit()

    def inject_triple(
        self,
        subject: str,
        predicate: str,
        object_val: str,
        source: str,
        confidence: float,
        timestamp: float = None,
        **kwargs,
    ):
        """
        Injects a triple as an immutable event and materializes it.
        """
        event = GraphEvent(
            subject=subject,
            predicate=predicate,
            object_val=object_val,
            source=source,
            confidence=confidence,
            timestamp=timestamp if timestamp is not None else time.time(),
            metadata=kwargs,
        )

        # 1. Write Model: Persistent Ledger (Append-Only)
        with open(self.ledger_path, "a") as f:
            f.write(event.model_dump_json() + "\n")

        # 2. Read Model: Project to SQLite
        self._materialize(event)

    def resolve_truth(
        self, at_timestamp: Optional[int] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Returns the mathematically resolved truth.
        Supports Time-Travel via at_timestamp.
        """
        cursor = self.conn.cursor()

        time_filter = "AND valid_to IS NULL"
        if at_timestamp:
            time_filter = f"AND valid_from <= {at_timestamp} AND (valid_to IS NULL OR valid_to > {at_timestamp})"

        query = f"""
            SELECT subject, predicate, object, source, confidence
            FROM knowledge k1
            WHERE 1=1 {time_filter} AND confidence = (
                SELECT MAX(confidence)
                FROM knowledge k2
                WHERE k1.subject = k2.subject AND k1.predicate = k2.predicate
                AND k2.valid_from <= COALESCE(?, 9999999999)
                AND (k2.valid_to IS NULL OR k2.valid_to > COALESCE(?, 0))
            )
            ORDER BY subject, predicate, timestamp DESC
        """

        cursor.execute(query, (at_timestamp, at_timestamp))

        resolved = {}
        for row in cursor.fetchall():
            subj, pred, obj, src, conf = row
            if subj not in resolved:
                resolved[subj] = {}
            if pred not in resolved[subj]:
                resolved[subj][pred] = {"value": obj, "source": src, "confidence": conf}

        return resolved

    def get_resolved_context_string(self) -> str:
        """Serializes the absolute truth into a string for the LLM context."""
        truth = self.resolve_truth()
        if not truth:
            return ""

        lines = ["=== CONTEXTO ESTRATÉGICO RESOLVIDO (ABSOLUTE GROUND TRUTH) ==="]
        for subj, predicates in truth.items():
            lines.append(f"ENTIDAD: {subj}")
            for pred, data in predicates.items():
                lines.append(f"  - {pred}: {data['value']}")
        return "\n".join(lines)
