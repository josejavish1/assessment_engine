import sqlite3
import time
from typing import Dict


class EpistemicGraph:
    """
    Tier-1 Epistemic Knowledge Graph (In-Memory SQLite).
    Resolves data conflicts mathematically via confidence and temporal weighting.
    """

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                UNIQUE(subject, predicate, source)
            )
        """)
        self.conn.commit()

    def inject_triple(
        self,
        subject: str,
        predicate: str,
        object_val: str,
        source: str,
        confidence: float,
        timestamp: int = None,
    ):
        if timestamp is None:
            timestamp = int(time.time())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge (subject, predicate, object, source, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                subject.upper(),
                predicate.upper(),
                object_val,
                source.upper(),
                float(confidence),
                int(timestamp),
            ),
        )
        self.conn.commit()

    def resolve_truth(self) -> Dict[str, Dict[str, str]]:
        """
        Returns the mathematically resolved truth.
        Groups by Subject and Predicate, taking the Object with the highest confidence.
        If confidence is equal, takes the most recent timestamp.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT subject, predicate, object, source, confidence
            FROM knowledge k1
            WHERE confidence = (
                SELECT MAX(confidence)
                FROM knowledge k2
                WHERE k1.subject = k2.subject AND k1.predicate = k2.predicate
            )
            ORDER BY subject, predicate, timestamp DESC
        """)

        resolved = {}
        # We might have multiple rows if confidence and timestamp are identical,
        # but the loop naturally takes the first one we encounter per predicate.
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
