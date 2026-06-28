import asyncio
import hashlib
import sqlite3
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Attempt to import FastAPI to expose the live REST Webhook server
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Webhook payload schema if FastAPI is used
if FASTAPI_AVAILABLE:
    class EvidencePayload(BaseModel):
        source_url: str = Field(..., description="The source URL or identifier of the streamed evidence.")
        content: str = Field(..., description="The raw text content of the evidence to index.")

class StreamingSentinel:
    """A high-performance real-time Streaming RAG Daemon and Dual-Tier Graph Ingestor.

    Implements the state-of-the-art 2025/2026 'Dual-Tier Storage' paradigm:
    - Layer 1 (Hot): SQLite database in WAL (Write-Ahead Logging) mode acting as a lightweight,
      ACID-compliant transaction broker that can absorb bursts of webhooks/feeds without lock contention.
    - Layer 2 (Cold): Persisted RAG knowledge bases and the Epistemic Graph.

    Advanced capabilities include:
    - Content-Addressable & Semantic Overlap Filtering (Jaccard similarity guardrail against RAG bloat).
    - Dampened Batching Scheduler to prevent token and API exhaustion.
    - Native integrated asynchronous FastAPI Webhook Server for push-based ingestion.
    """

    def __init__(self, client_id: str = "redeia_v3", db_path: Optional[Path] = None) -> None:  # defaults to 'redeia' for backward compatibility
        """Initializes the Streaming Sentinel for a specific client."""
        self.client_id = client_id
        
        # Determine paths relative to repository root
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.client_dir = repo_root / "working" / client_id
        self.client_dir.mkdir(parents=True, exist_ok=True)
        
        if db_path is None:
            self.db_path = self.client_dir / "streaming_queue.db"
        else:
            self.db_path = db_path

        self.conn: Optional[sqlite3.Connection] = None
        
        # Concurrency safety lock for multi-threaded SQLite WAL writes
        import threading
        self.db_lock = threading.Lock()
        
        # Dampening queue and state variables
        self.dampening_buffer: List[str] = []
        self.last_ingest_time: float = 0.0

    def initialize_queue(self) -> None:
        """Initializes the SQLite transactional queue and sets the journal mode to WAL.

        WAL (Write-Ahead Logging) mode allows simultaneous readers and writers, achieving
        extremely high-throughput, low-latency concurrent E/S operations.
        """
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Enforce WAL mode
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")

        # Create queue table
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS streaming_queue (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    source_url TEXT,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                );
            """)
            # Index for fast priority polling
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_created 
                ON streaming_queue(status, created_at);
            """)

    def close(self) -> None:
        """Safely closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    @staticmethod
    def _tokenize_text(text: str) -> Set[str]:
        """Tokenizes and normalizes text for Jaccard semantic overlap calculations."""
        # Lowercase, keep alpha-numeric, split to words
        words = re.findall(r"\w+", text.lower())
        return set(words)

    def _is_semantic_duplicate(self, content: str, existing_fragments: List[Any], threshold: float = 0.80) -> bool:
        """Calculates Jaccard similarity against existing fragments to prevent semantic duplicates."""
        new_tokens = self._tokenize_text(content)
        if not new_tokens:
            return False

        for frag in existing_fragments:
            frag_text = getattr(frag, "content", "") if hasattr(frag, "content") else str(frag)
            frag_tokens = self._tokenize_text(frag_text)
            if not frag_tokens:
                continue

            intersection = new_tokens.intersection(frag_tokens)
            union = new_tokens.union(frag_tokens)
            jaccard_sim = len(intersection) / len(union)

            if jaccard_sim > threshold:
                logger.warning(f"Semantic duplicate detected (Jaccard={jaccard_sim:.4f}). Skipping ingestion.")
                return True
        return False

    def enqueue_evidence(self, source_url: str, content: str) -> str:
        """Computes Content-Addressable Hash and pushes a new evidence item to the transactional queue.

        If the exact same content has already been enqueued or processed, the write is skipped
        to guarantee idempotency and zero-duplicate overhead.
        """
        if not self.conn:
            self.initialize_queue()

        # Compute SHA-256 hash for Content-Addressable Hashing
        hasher = hashlib.sha256()
        hasher.update(content.encode("utf-8"))
        content_hash = hasher.hexdigest()
        
        # Unique identifier based on hash and client
        item_id = hashlib.sha256(f"{self.client_id}:{content_hash}".encode("utf-8")).hexdigest()

        try:
            with self.db_lock:
                with self.conn:
                    self.conn.execute(
                        """
                        INSERT INTO streaming_queue (id, client_id, source_url, content, content_hash)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                        status = CASE WHEN status = 'failed' THEN 'pending' ELSE status END
                        """,
                        (item_id, self.client_id, source_url, content, content_hash)
                    )
            logger.info(f"Enqueued evidence item {item_id} from {source_url} (Delta-Checked).")
            return item_id
        except Exception as e:
            logger.error(f"Failed to enqueue evidence {item_id}: {e}")
            raise

    def process_next_batch(self, batch_size: int = 10) -> int:
        """Fetches and processes the next batch of pending evidences from the queue.

        Integrates with the EvidenceEngine and RaptorEngine to ingest the text fragments,
        applying Jaccard semantic deduplication and scheduling incremental updates.
        """
        if not self.conn:
            self.initialize_queue()

        # 1. Fetch pending items
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, source_url, content, content_hash 
            FROM streaming_queue 
            WHERE status = 'pending' AND client_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self.client_id, batch_size)
        )
        rows = cursor.fetchall()

        if not rows:
            return 0

        logger.info(f"Streaming Sentinel: Processing a delta batch of {len(rows)} elements.")

        # Import RAG and Graph services dynamically to maintain hexagonal isolation
        from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
        from assessment_engine.infrastructure.raptor_engine import RaptorEngine

        # Instanciar EvidenceEngine para la capa "Cold"
        storage_dir = self.client_dir / "redeia"  # defaults to 'redeia' for backward compatibility
        storage_dir.mkdir(parents=True, exist_ok=True)
        evidence_engine = EvidenceEngine(client_id=self.client_id, storage_dir=storage_dir)

        processed_count = 0
        for item_id, source_url, content, content_hash in rows:
            try:
                # Mark as processing
                with self.db_lock:
                    with self.conn:
                        self.conn.execute(
                            "UPDATE streaming_queue SET status = 'processing' WHERE id = ?",
                            (item_id,)
                        )

                # Jaccard Semantic Deduplication check against the cold storage ledger
                if self._is_semantic_duplicate(content, evidence_engine.ledger.fragments, threshold=0.80):
                    with self.db_lock:
                        with self.conn:
                            self.conn.execute(
                                "UPDATE streaming_queue SET status = 'processed', error_message = 'Skipped: Semantic duplicate' WHERE id = ?",
                                (item_id,)
                            )
                    continue

                # Write the text to a physical .txt file under the client's streaming directory
                streaming_dir = storage_dir / "streaming"
                streaming_dir.mkdir(parents=True, exist_ok=True)
                evidence_file = streaming_dir / f"stream_{content_hash[:16]}.txt"
                evidence_file.write_text(content, encoding="utf-8")

                # Ingest file directly into the Evidence Vault (incremental indexing)
                evidence_engine.ingest_file(evidence_file)
                
                # Mark as processed in database
                with self.db_lock:
                    with self.conn:
                        self.conn.execute(
                            """
                            UPDATE streaming_queue 
                            SET status = 'processed', processed_at = ? 
                            WHERE id = ?
                            """,
                            (datetime.now(timezone.utc).isoformat(), item_id)
                        )
                processed_count += 1
                self.dampening_buffer.append(item_id)
                logger.info(f"Successfully processed and indexed evidence item {item_id}.")
            except Exception as e:
                logger.error(f"Error processing evidence item {item_id}: {e}")
                with self.db_lock:
                    with self.conn:
                        self.conn.execute(
                            "UPDATE streaming_queue SET status = 'failed', error_message = ? WHERE id = ?",
                            (str(e), item_id)
                        )

        # 2. Dampened Batching Scheduler for Raptor RAG Tree rebuild
        # We only rebuild the tree when we exceed 5 items or when we hit a silent quiet period.
        if processed_count > 0:
            self.last_ingest_time = datetime.now(timezone.utc).timestamp()

        return processed_count

    def check_and_trigger_dampened_rebuild(self) -> bool:
        """Trigger-check for the Dampened Batching Scheduler.

        Returns True if a rebuild of the Raptor Tree was triggered.
        """
        if not self.dampening_buffer:
            return False

        now = datetime.now(timezone.utc).timestamp()
        time_since_last_ingest = now - self.last_ingest_time
        
        # Trigger rebuild if:
        # - Buffer has more than 5 accumulated new items (Batch threshold).
        # - Or, 10 seconds of silence have passed since the last ingestion (Quiet period threshold).
        if len(self.dampening_buffer) >= 5 or time_since_last_ingest >= 10.0:
            logger.info(f"Dampened Scheduler: Triggering Raptor RAG Tree rebuild for {len(self.dampening_buffer)} items.")
            
            from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
            from assessment_engine.infrastructure.raptor_engine import RaptorEngine

            storage_dir = self.client_dir / "redeia"  # defaults to 'redeia' for backward compatibility
            evidence_engine = EvidenceEngine(client_id=self.client_id, storage_dir=storage_dir)
            raptor = RaptorEngine(client_id=self.client_id, storage_dir=storage_dir)

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(raptor.build_tree(evidence_engine.ledger.fragments))
                else:
                    asyncio.run(raptor.build_tree(evidence_engine.ledger.fragments))
                logger.info("🌲 [RAPTOR] Dynamic Knowledge Tree updated successfully.")
            except Exception as e:
                logger.error(f"Failed to update Raptor Tree dynamically: {e}")

            # Clear the buffer after successful rebuild trigger
            self.dampening_buffer.clear()
            return True

        return False

    async def start_daemon_loop(self, poll_interval_sec: float = 1.0, stop_event: Optional[asyncio.Event] = None) -> None:
        """Starts the infinite asynchronous daemon polling loop with the Dampened Scheduler."""
        logger.info(f"Starting Streaming Sentinel daemon for client {self.client_id}...")
        self.initialize_queue()
        
        while stop_event is None or not stop_event.is_set():
            try:
                # Run the blocking process_next_batch in a background thread to keep event loop free!
                processed = await asyncio.to_thread(self.process_next_batch)
                if processed > 0:
                    logger.info(f"Sentinel Loop: Ingested {processed} new items.")
                
                # Run the blocking check_and_trigger_dampened_rebuild in a background thread!
                await asyncio.to_thread(self.check_and_trigger_dampened_rebuild)
            except Exception as e:
                logger.error(f"Error in Sentinel daemon polling iteration: {e}")
            
            await asyncio.sleep(poll_interval_sec)
        
        logger.info("Streaming Sentinel daemon loop stopped gracefully.")
        self.close()

    def get_fastapi_app(self) -> Any:
        """Returns a configured FastAPI application instance exposing the REST Webhook Endpoint.

        Allows external systems to stream evidence directly via POST /webhook/evidence.
        """
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI and Pydantic are required to run the Webhook Server.")

        app = FastAPI(title=f"Streaming Sentinel Webhook - {self.client_id}")

        @app.post("/webhook/evidence")
        async def receive_evidence(payload: EvidencePayload):
            try:
                # Delegate blocking database write to a background thread to prevent server freezes!
                item_id = await asyncio.to_thread(self.enqueue_evidence, payload.source_url, payload.content)
                return {
                    "status": "success",
                    "item_id": item_id,
                    "message": "Evidence successfully enqueued for continuous ingestion."
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to enqueue evidence: {e}")

        return app
