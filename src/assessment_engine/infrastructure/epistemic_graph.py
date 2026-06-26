import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, cast

from pydantic import BaseModel, Field


class GraphEvent(BaseModel):
    """Represents an immutable, bitemporal fact within a knowledge graph.

    This data structure models a single, immutable event or fact. It utilizes
    bitemporal timestamps to enable complete historical state tracking,
    distinguishing between when a fact was recorded (processing time) and when it
    was true in the real world (valid time). This is crucial for systems
    requiring auditability and point-in-time queries.

    Args:
        event_id (str): A unique identifier for the event. Defaults to a UUID
            version 4 string.
        subject (str): The subject of the RDF-like triple, typically an entity
            identifier.
        predicate (str): The relationship or property of the triple.
        object_val (str): The value or object of the triple.
        source (str): The system, process, or authority that generated the event.
        confidence (float): A numerical value representing the certainty of the fact,
            typically normalized between 0.0 and 1.0.
        timestamp (float): The processing timestamp (Unix epoch time) when the
            event was recorded in the system. Defaults to the current time.
        valid_from (float): The start of the validity period (Unix epoch time) for
            the fact in the real world. Defaults to the current time.
        valid_to (Optional[float]): The end of the validity period (Unix epoch
            time). A `None` value indicates the fact is considered valid
            indefinitely or until explicitly superseded. Defaults to `None`.
        metadata (Dict[str, Any]): A dictionary for arbitrary, non-core
            information associated with the event. Defaults to an empty dict.

    Raises:
        pydantic.ValidationError: If input data fails to conform to the model's
            type and validation constraints during instantiation.
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
    r"""['Manages an evolving knowledge graph using Event Sourcing and CQRS patterns.\n\n    This class models facts as subject-predicate-object triples and is designed\n    to handle evolving information where assertions can be updated or contradicted\n    over time. The architecture separates command and query responsibilities:\n\n    -   **Write-Side (Commands)**: New information is captured as immutable\n        `GraphEvent` objects and appended to a persistent, append-only ledger file.\n        This ledger constitutes the definitive history of all changes.\n    -   **Read-Side (Queries)**: For efficient querying, events from the ledger\n        are projected into an in-memory SQLite database, which serves as a\n        materialized view of the graph\'s current state.\n\n    The primary function is to resolve the canonical "truth" for any\n    subject-predicate pair by selecting the object from the source with the\n    highest confidence score that is valid at a specified point in time. This\n    approach provides resilience to noisy or conflicting data sources.\n\n    Attributes:\n        client_id: The unique identifier for this graph instance, used to\n            namespace the persistent event ledger on disk.\n        ledger_path: The `pathlib.Path` object for the append-only event ledger.\n        conn: The `sqlite3.Connection` object for the in-memory database that\n            serves as the read model.', 'Initializes the EpistemicGraph instance and reconstructs its state.\n\n        Sets up the path to the persistent event ledger file based on the client ID,\n        ensuring parent directories exist. It also initializes an in-memory SQLite\n        database and its schema to serve as the read model. If a ledger file\n        already exists, all historical events are replayed to reconstruct the\n        current state of the materialized view.\n\n        Args:\n            client_id: A unique identifier used to namespace the persistent event\n                ledger on disk.\n\n        Raises:\n            PermissionError: If directories for the ledger path cannot be created.\n            sqlite3.Error: If the database cannot be initialized or the schema\n                cannot be created.\n            IOError: If an existing ledger file cannot be read during replay.\n            json.JSONDecodeError: If a line in the ledger file is not valid JSON.', "Creates the 'knowledge' table schema in the in-memory database.", 'Populates the in-memory read model by replaying events from the ledger file.\n\n        This method reads the append-only event ledger from disk, line by line.\n        Each line, representing a serialized `GraphEvent`, is parsed and applied to\n        the in-memory SQLite database. This process reconstructs the materialized\n        view to its current state. The method is idempotent and is typically called\n        during initialization. Corrupted or unparseable lines in the ledger are\n        skipped to ensure robust state recovery.', 'Applies a single graph event to the materialized view in the SQLite database.', "Creates and persists a `GraphEvent` for a new knowledge triple.\n\n        This method constitutes the write-side of the CQRS architecture. It\n        constructs a `GraphEvent` from the provided triple data, appends its\n        serialized JSON representation to the persistent ledger file, and then\n        applies the event to the in-memory materialized view for immediate querying.\n\n        Args:\n            subject: The subject node of the graph triple.\n            predicate: The predicate or relationship of the triple.\n            object_val: The object node of the graph triple.\n            source: The system or document providing this information.\n            confidence: A numerical score representing confidence in the triple's\n                accuracy.\n            timestamp: The POSIX timestamp of when the event occurred. If None,\n                the current system time is used.\n            **kwargs: Additional key-value metadata to store with the event.\n\n        Raises:\n            IOError: If the event cannot be written to the ledger file.\n            FileNotFoundError: If the directory for the ledger file does not exist.", 'Resolves the most authoritative state of the graph for a given point in time.\n\n        For each unique subject-predicate pair, this query identifies the object\n        assertion with the highest confidence score that was valid at `at_timestamp`.\n        If `at_timestamp` is None, it resolves the current state, considering only\n        facts that are presently valid. Ties in confidence are broken by selecting\n        the assertion with the most recent event timestamp.\n\n        Args:\n            at_timestamp: A POSIX timestamp for time-travel queries. If provided,\n                resolves the state of the graph as it was at that moment. If None,\n                resolves the current state.\n\n        Returns:\n            A nested dictionary representing the resolved state of the graph, structured\n            as `{subject: {predicate: {"value": object, "source": source,\n            "confidence": confidence}}}`.\n\n        Raises:\n            sqlite3.Error: If the underlying database query fails.', 'Serializes the currently resolved graph state into a formatted string.\n\n        This method first calls `resolve_truth()` to get the current state of the\n        graph. It then formats this state into a multi-line string with a\n        standardized header and entity-predicate-value structure, suitable for\n        consumption by external systems like Large Language Models.\n\n        Returns:\n            A formatted, multi-line string representing the resolved graph state,\n            or an empty string if the graph contains no resolved facts.']."""

    def __init__(self, client_id: str = "generic"):
        r"""{'docstring': 'Initializes the EpistemicGraph instance.\n\nThis method sets up the graph\'s persistence and in-memory state. It\nestablishes a path to an append-only event ledger file on disk, namespaced\nby the `client_id` (e.g., \'working/my_client/epistemic_ledger.jsonl\'),\nand ensures the parent directories exist. An in-memory SQLite database is\nthen initialized to serve as a read model. Finally, the graph\'s state is\nreconstructed by replaying all events from the ledger file, if it exists.\n\nArgs:\n    client_id (str): A unique identifier used to namespace the persistent event\n        ledger on disk. Defaults to "generic".\n\nRaises:\n    PermissionError: If the directories for the ledger path cannot be\n        created due to filesystem permissions.\n    sqlite3.Error: If the in-memory database or its schema fails to\n        initialize.\n    IOError: If reading from an existing ledger file fails during the replay\n        process.\n    json.JSONDecodeError: If a line in the ledger file contains invalid JSON.'}."""
        self.client_id = client_id
        # Handles the persistence of the append-only event ledger to a durable storage medium.
        self.ledger_path = Path(f"working/{client_id}/epistemic_ledger.jsonl")
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # Implementation of the Read Model as a materialized view, backed by an in-memory SQLite database.
        self.conn = sqlite3.connect(":memory:")
        self._init_db()
        self._replay_ledger()

    def _init_db(self) -> None:
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

    def _replay_ledger(self) -> None:
        """Rebuilds the entire materialized view by replaying all events from the immutable ledger. This is typically used for system initialization or state recovery."""
        if not self.ledger_path.exists():
            return

        with open(self.ledger_path, "r") as f:
            for line in f:
                try:
                    event_data = json.loads(line)
                    event = GraphEvent(**event_data)
                    self._materialize(event)
                except Exception:
                    continue  # To ensure system robustness during ledger reconstruction, corrupted or unparseable event lines are logged and skipped, preventing a full system halt due to isolated data integrity issues.

    def _materialize(self, event: GraphEvent) -> None:
        """Applies a single event to the materialized view, updating the queryable state."""
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
        timestamp: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Records a graph triple event and updates the materialized view.

        This method implements the write-side of a Command Query Responsibility
        Segregation (CQRS) architecture. It serializes the triple and its
        metadata into a `GraphEvent` and appends it to a persistent, immutable
        ledger file. Subsequently, it projects this event into the read-side
        materialized view to enable efficient querying.

        Args:
            subject: The subject node of the graph triple (e.g., "CompanyA").
            predicate: The predicate or relationship of the triple (e.g., "founded_by").
            object_val: The object node of the graph triple (e.g., "PersonX").
            source: The originating system or document for the triple.
            confidence: A numerical score representing confidence in the triple's
                accuracy.
            timestamp: The POSIX timestamp of the event. If None, the current
                system time is used.
            **kwargs: Additional key-value metadata to store with the event.

        Raises:
            pydantic.ValidationError: If the provided arguments fail validation
                during `GraphEvent` instantiation.
            IOError: If an error occurs while writing the event to the ledger file,
                such as a permissions error or a full disk.
            FileNotFoundError: If the directory for the ledger file does not exist.
        """
        # Strict Epistemic Graph Schema Constraints
        normalized_predicate = predicate.upper().strip().replace(" ", "_")

        # System-injected triples must use registered predicates
        if source.upper() in {
            "TOWER_PIPELINE",
            "TOWER_T1",
            "TOWER_T2",
            "TOWER_T3",
            "TOWER_T4",
            "TOWER_T5",
            "ORCHESTRATOR",
        }:
            VALID_SYSTEM_PREDICATES = {
                "BELONGS_TO_TOWER",
                "IDENTIFIED_AS_GAP",
                "IMPACTS_PILLAR",
                "PROPOSES_INITIATIVE",
                "ADDRESSES_PILLAR",
                "REQUIRES_PREREQUISITE",
                "SUPPORTED_BY",
                "VIOLATES",
                "COVERS",
            }
            if normalized_predicate not in VALID_SYSTEM_PREDICATES:
                raise ValueError(
                    f"Graph Schema Violation: System-injected predicate '{predicate}' is not registered. "
                    f"Must be one of: {sorted(list(VALID_SYSTEM_PREDICATES))}"
                )
        else:
            # AI-extracted or custom triples must use uppercase SNAKE_CASE
            import re

            if not re.match(r"^[A-Z0-9_]+$", normalized_predicate):
                raise ValueError(
                    f"Graph Schema Violation: Predicate '{predicate}' must be in uppercase SNAKE_CASE format."
                )

        effective_ts = timestamp if timestamp is not None else time.time()
        event = GraphEvent(
            subject=subject,
            predicate=normalized_predicate,
            object_val=object_val,
            source=source,
            confidence=confidence,
            timestamp=effective_ts,
            **kwargs,
        )

        # Defines the CQRS Write Model, which consists of a persistent, append-only event ledger.
        with open(self.ledger_path, "a") as f:
            f.write(event.model_dump_json() + "\n")

        # Defines the CQRS Read Model, which projects events into an in-memory SQLite database for efficient querying.
        self._materialize(event)

    def resolve_truth(
        self, at_timestamp: Optional[int] = None
    ) -> Dict[str, Dict[str, str]]:
        """Resolves the state of the knowledge graph based on assertion confidence at a specific time.

        For each unique subject-predicate pair, this method identifies the single most
        credible assertion. The resolution process first selects all assertions
        that were temporally valid at the specified `at_timestamp`. From this subset, it
        identifies the assertion(s) with the highest confidence score. If multiple
        assertions share the highest confidence, the one with the most recent creation
        timestamp is chosen as the tie-breaker.

        If `at_timestamp` is `None`, the resolution is limited to assertions that
        have no expiration date (i.e., where `valid_to` is NULL).

        Args:
            at_timestamp: An optional integer Unix timestamp for which to resolve the
                graph's state. If `None`, the resolution is performed only on
                assertions with no `valid_to` timestamp.

        Returns:
            A nested dictionary representing the resolved state of the graph.
            The structure is:
            `{subject: {predicate: {"value": str, "source": str, "confidence": float}}}`.

        Raises:
            A database-specific error (e.g., sqlite3.Error) if the underlying
            database query fails to execute.
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

        resolved: Dict[str, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            subj, pred, obj, src, conf = row
            if subj not in resolved:
                resolved[subj] = {}
            if pred not in resolved[subj]:
                resolved[subj][pred] = {"value": obj, "source": src, "confidence": conf}

        return resolved

    def get_resolved_context_string(self) -> str:
        """Serializes the resolved materialized view into a structured, multi-line string.

        The resulting string is designed for machine parsing, particularly by Large Language Models (LLMs). It begins with a static header, followed by a series of entity blocks. Each block starts with an `ENTIDAD:` line, which is then followed by indented lines for each predicate-value pair associated with that entity. If a value for a predicate is not present in the source data, it defaults to the string "N/A".

        Returns:
            A string containing the formatted representation of the resolved data, or
            an empty string if the materialized view is empty.
        """
        truth = self.resolve_truth()
        if not truth:
            return ""

        lines = ["=== CONTEXTO ESTRATÉGICO RESOLVIDO (ABSOLUTE GROUND TRUTH) ==="]
        for subj, predicates in truth.items():
            lines.append(f"ENTIDAD: {subj}")
            for pred, data_raw in predicates.items():
                data = cast(Dict[str, Any], data_raw)
                val = data.get("value", "N/A")
                lines.append(f"  - {pred}: {val}")
        return "\n".join(lines)
