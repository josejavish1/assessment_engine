import asyncio
import contextlib
import hashlib
import logging
import os
import re
import signal
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

DEFAULT_CLIENT_ID = "generic_client"
CLIENT_ID_ENV_VAR = "ASSESSMENT_CLIENT_ID"
DEFAULT_POLL_INTERVAL_SEC = 1.0
DEFAULT_BATCH_SIZE = 10
DEFAULT_DRAIN_BATCH_SIZE = 50
DEFAULT_DAMPENING_BATCH_THRESHOLD = 5
DEFAULT_DAMPENING_QUIET_PERIOD_SEC = 10.0
DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD = 0.80
DEFAULT_STALE_LOCK_TIMEOUT_SEC = 300.0
DEFAULT_STOP_WAIT_INTERVAL_SEC = 0.1
DEFAULT_MAX_SOURCE_URL_LENGTH = 2048
DEFAULT_MAX_CONTENT_LENGTH = 5_000_000
DEFAULT_HASH_PREFIX_LENGTH = 16
DEFAULT_TMP_SUFFIX_LENGTH = 8
HTTP_STATUS_INTERNAL_ERROR = 500
HTTP_STATUS_SERVICE_UNAVAILABLE = 503

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
        source_url: str = Field(
            ...,
            max_length=DEFAULT_MAX_SOURCE_URL_LENGTH,
            description="The source URL or identifier of the streamed evidence.",
        )
        content: str = Field(
            ...,
            max_length=DEFAULT_MAX_CONTENT_LENGTH,
            description="The raw text content of the evidence to index (Max 5MB).",
        )


@dataclass(frozen=True)
class SentinelConfig:
    """Operational configuration parameters for StreamingSentinel."""

    poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC
    batch_size: int = DEFAULT_BATCH_SIZE
    drain_batch_size: int = DEFAULT_DRAIN_BATCH_SIZE
    dampening_batch_threshold: int = DEFAULT_DAMPENING_BATCH_THRESHOLD
    dampening_quiet_period_sec: float = DEFAULT_DAMPENING_QUIET_PERIOD_SEC
    semantic_similarity_threshold: float = DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD
    stale_lock_timeout_sec: float = DEFAULT_STALE_LOCK_TIMEOUT_SEC
    stop_wait_interval_sec: float = DEFAULT_STOP_WAIT_INTERVAL_SEC


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
    - Python 3.11+ Structured Concurrency via asyncio.TaskGroup and POSIX signal interception.
    """

    def __init__(  # noqa: PLR0913
        self,
        client_id: str = DEFAULT_CLIENT_ID,
        db_path: Optional[Path] = None,
        poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC,
        batch_size: int = DEFAULT_BATCH_SIZE,
        drain_batch_size: int = DEFAULT_DRAIN_BATCH_SIZE,
        dampening_batch_threshold: int = DEFAULT_DAMPENING_BATCH_THRESHOLD,
        dampening_quiet_period_sec: float = DEFAULT_DAMPENING_QUIET_PERIOD_SEC,
        semantic_similarity_threshold: float = DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD,
        stale_lock_timeout_sec: float = DEFAULT_STALE_LOCK_TIMEOUT_SEC,
        config: Optional[SentinelConfig] = None,
    ) -> None:
        """Initializes the Streaming Sentinel for a specific client."""
        if client_id == DEFAULT_CLIENT_ID:
            client_id = os.environ.get(CLIENT_ID_ENV_VAR, DEFAULT_CLIENT_ID)
        self.client_id = client_id

        resolved_config = config or SentinelConfig(
            poll_interval_sec=poll_interval_sec,
            batch_size=batch_size,
            drain_batch_size=drain_batch_size,
            dampening_batch_threshold=dampening_batch_threshold,
            dampening_quiet_period_sec=dampening_quiet_period_sec,
            semantic_similarity_threshold=semantic_similarity_threshold,
            stale_lock_timeout_sec=stale_lock_timeout_sec,
        )
        self.config = resolved_config
        self.poll_interval_sec = resolved_config.poll_interval_sec
        self.batch_size = resolved_config.batch_size
        self.drain_batch_size = resolved_config.drain_batch_size
        self.dampening_batch_threshold = resolved_config.dampening_batch_threshold
        self.dampening_quiet_period_sec = resolved_config.dampening_quiet_period_sec
        self.semantic_similarity_threshold = (
            resolved_config.semantic_similarity_threshold
        )
        self.stale_lock_timeout_sec = resolved_config.stale_lock_timeout_sec
        self.stop_wait_interval_sec = resolved_config.stop_wait_interval_sec

        # Determine paths relative to repository root
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.client_dir = repo_root / "working" / self.client_id
        self.client_dir.mkdir(parents=True, exist_ok=True)

        if db_path is None:
            self.db_path = self.client_dir / "streaming_queue.db"
        else:
            self.db_path = db_path

        self.conn: Optional[sqlite3.Connection] = None

        # Concurrency safety lock for multi-threaded SQLite WAL writes
        self.db_lock = threading.Lock()

        # Dampening queue and state variables
        self.dampening_buffer: List[str] = []
        self.last_ingest_time: float = 0.0

        # Structured concurrency & graceful shutdown state
        self._accepting_ingress: bool = True
        self._stop_event: Optional[asyncio.Event] = None
        self._task_group: Optional[asyncio.TaskGroup] = None
        self._daemon_task: Optional[asyncio.Task[None]] = None
        self._previous_signal_handlers: Dict[int, Any] = {}
        self._previous_loop_handlers: Dict[int, Any] = {}
        self._loop_signal_registered: Set[int] = set()

    def _require_connection(self) -> sqlite3.Connection:
        """Returns the active SQLite connection or raises RuntimeError if uninitialized."""
        if self.conn is None:
            raise RuntimeError(
                f"StreamingSentinel ({self.client_id}) SQLite connection is not initialized."
            )
        return self.conn

    async def __aenter__(self) -> "StreamingSentinel":
        """Enters the asynchronous context manager with structured concurrency and signal interception."""
        self._accepting_ingress = True
        self._stop_event = asyncio.Event()
        self.initialize_queue()
        self._register_signal_handlers()

        self._task_group = asyncio.TaskGroup()
        await self._task_group.__aenter__()
        self._daemon_task = self._task_group.create_task(
            self._run_daemon_worker(
                poll_interval_sec=self.poll_interval_sec,
                stop_event=self._stop_event,
            ),
            name=f"sentinel_daemon_{self.client_id}",
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Exits the asynchronous context manager, draining queues and flushing SQLite transactions."""
        self._accepting_ingress = False
        if self._stop_event is not None:
            self._stop_event.set()

        try:
            if self._task_group is not None:
                await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self._task_group = None
            self._daemon_task = None
            await asyncio.to_thread(self._drain_and_flush_sync)
            self._restore_signal_handlers()
            self.close()

    def _handle_shutdown_signal(self, sig_num: int, frame: Any = None) -> None:
        """Callback invoked upon receiving SIGINT or SIGTERM; chains any prior handlers."""
        sig_name = signal.Signals(sig_num).name
        logger.info(
            f"Streaming Sentinel received {sig_name}: halting ingress and initiating graceful drain."
        )
        self._accepting_ingress = False
        if self._stop_event is not None:
            self._stop_event.set()

        # Chain to any previously registered asyncio loop signal handler (e.g. ASGI server)
        prev_loop_handle = self._previous_loop_handlers.get(sig_num)
        if prev_loop_handle is not None:
            runner = getattr(prev_loop_handle, "_run", None)
            if callable(runner):
                try:
                    runner()
                except Exception as e:
                    logger.debug(
                        f"Chained loop signal handler for {sig_name} raised: {e}"
                    )
            return

        # Otherwise chain to any previously registered standard callable signal handler
        prev_handler = self._previous_signal_handlers.get(sig_num)
        if callable(prev_handler) and prev_handler not in (
            signal.SIG_DFL,
            signal.SIG_IGN,
        ):
            try:
                prev_handler(sig_num, frame)
            except Exception as e:
                logger.debug(f"Chained signal handler for {sig_name} raised: {e}")

    def _register_signal_handlers(self) -> None:
        """Registers POSIX signal handlers (SIGINT, SIGTERM) while preserving and chaining existing handlers."""
        if threading.current_thread() is not threading.main_thread():
            return

        loop = asyncio.get_running_loop()
        loop_handlers = getattr(loop, "_signal_handlers", None)

        for sig in (signal.SIGINT, signal.SIGTERM):
            sig_int = int(sig)
            try:
                prev_sig = signal.getsignal(sig)
                self._previous_signal_handlers[sig_int] = prev_sig
            except (ValueError, OSError):
                self._previous_signal_handlers[sig_int] = signal.SIG_DFL

            if isinstance(loop_handlers, dict) and sig_int in loop_handlers:
                self._previous_loop_handlers[sig_int] = loop_handlers[sig_int]

            try:
                loop.add_signal_handler(sig, self._handle_shutdown_signal, sig_int)
                self._loop_signal_registered.add(sig_int)
            except (NotImplementedError, RuntimeError, ValueError):
                try:

                    def _sync_handler(
                        signum: int,
                        frame: Any,
                        _loop: asyncio.AbstractEventLoop = loop,
                    ) -> None:
                        _loop.call_soon_threadsafe(
                            self._handle_shutdown_signal, signum, frame
                        )

                    signal.signal(sig, _sync_handler)
                except (ValueError, OSError):
                    pass

    def _restore_signal_handlers(self) -> None:
        """Restores previous POSIX and event loop signal handlers upon context exit."""
        if threading.current_thread() is not threading.main_thread():
            return

        try:
            loop = asyncio.get_running_loop()
            for sig_int in list(self._loop_signal_registered):
                sig_enum = signal.Signals(sig_int)
                with contextlib.suppress(NotImplementedError, RuntimeError, ValueError):
                    loop.remove_signal_handler(sig_enum)
                prev_loop_handle = self._previous_loop_handlers.get(sig_int)
                if prev_loop_handle is not None:
                    callback = getattr(prev_loop_handle, "_callback", None)
                    args = getattr(prev_loop_handle, "_args", ())
                    if callable(callback):
                        with contextlib.suppress(
                            NotImplementedError, RuntimeError, ValueError
                        ):
                            loop.add_signal_handler(sig_enum, callback, *args)
        except RuntimeError:
            pass
        finally:
            self._loop_signal_registered.clear()
            self._previous_loop_handlers.clear()

        for sig_int, prev_handler in list(self._previous_signal_handlers.items()):
            if prev_handler is not None:
                with contextlib.suppress(ValueError, OSError, TypeError):
                    signal.signal(signal.Signals(sig_int), prev_handler)
        self._previous_signal_handlers.clear()

    def _drain_and_flush_sync(self) -> None:
        """Synchronously drains remaining pending items and flushes SQLite WAL to disk."""
        if not self.conn:
            return

        logger.info(
            f"Streaming Sentinel ({self.client_id}): Draining pending queue before exit..."
        )
        while True:
            try:
                processed = self.process_next_batch(batch_size=self.drain_batch_size)
                if processed <= 0:
                    break
            except Exception as e:
                logger.error(f"Error while draining queue on shutdown: {e}")
                break

        if self.dampening_buffer:
            try:
                self.last_ingest_time = 0.0
                self.check_and_trigger_dampened_rebuild()
            except Exception as e:
                logger.error(f"Error flushing dampened rebuild on shutdown: {e}")

        self.flush_sqlite()

    def flush_sqlite(self) -> None:
        """Flushes active SQLite transactions and checkpoints the WAL journal to disk."""
        if not self.conn:
            return
        try:
            with self.db_lock:
                conn = self._require_connection()
                if conn.in_transaction:
                    conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                conn.commit()
            logger.info(
                f"Streaming Sentinel ({self.client_id}): Flushed SQLite WAL transactions to disk."
            )
        except Exception as e:
            logger.warning(f"Failed to flush SQLite transactions during shutdown: {e}")

    def initialize_queue(self) -> None:
        """Initializes the SQLite transactional queue and sets the journal mode to WAL.

        WAL (Write-Ahead Logging) mode allows simultaneous readers and writers, achieving
        extremely high-throughput, low-latency concurrent I/O operations.
        """
        with self.db_lock:
            if self.conn is not None:
                return
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

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
        """Safely flushes and closes the database connection."""
        if self.conn:
            self.flush_sqlite()
            with self.db_lock:
                if self.conn:
                    self.conn.close()
                    self.conn = None

    @contextlib.contextmanager
    def _acquire_process_lock(self):
        """OS-Level Distributed Mutex for Multi-Worker concurrency safety.
        Uses an atomic directory creation to ensure only one worker across the entire
        operating system can execute RAG file I/O operations simultaneously.
        """
        lock_dir = self.client_dir / ".sentinel_lock"
        has_lock = False
        try:
            lock_dir.mkdir(exist_ok=False)
            has_lock = True
        except FileExistsError:
            # Check for stale locks (e.g., if a worker crashed mid-operation)
            try:
                if lock_dir.stat().st_mtime < time.time() - self.stale_lock_timeout_sec:
                    lock_dir.rmdir()
                    lock_dir.mkdir(exist_ok=False)
                    has_lock = True
            except OSError:
                has_lock = False

        try:
            yield has_lock
        finally:
            if has_lock:
                try:
                    lock_dir.rmdir()
                except OSError:
                    pass

    @staticmethod
    def _tokenize_text(text: str) -> Set[str]:
        """Tokenizes and normalizes text for Jaccard semantic overlap calculations."""
        words = re.findall(r"\w+", text.lower())
        return set(words)

    def _is_semantic_duplicate(
        self,
        content: str,
        existing_fragments: List[Any],
        threshold: Optional[float] = None,
    ) -> bool:
        """Calculates Jaccard similarity against existing fragments to prevent semantic duplicates."""
        effective_threshold = (
            threshold if threshold is not None else self.semantic_similarity_threshold
        )
        new_tokens = self._tokenize_text(content)
        if not new_tokens:
            return False

        for frag in existing_fragments:
            frag_text = (
                getattr(frag, "content", "") if hasattr(frag, "content") else str(frag)
            )
            frag_tokens = self._tokenize_text(frag_text)
            if not frag_tokens:
                continue

            intersection = new_tokens.intersection(frag_tokens)
            union = new_tokens.union(frag_tokens)
            jaccard_sim = len(intersection) / len(union)

            if jaccard_sim > effective_threshold:
                logger.warning(
                    f"Semantic duplicate detected (Jaccard={jaccard_sim:.4f}). Skipping ingestion."
                )
                return True
        return False

    def enqueue_evidence(self, source_url: str, content: str) -> str:
        """Computes Content-Addressable Hash and pushes a new evidence item to the transactional queue.

        If the exact same content has already been enqueued or processed, the write is skipped
        to guarantee idempotency and zero-duplicate overhead.
        """
        if not self._accepting_ingress:
            raise RuntimeError(
                "StreamingSentinel is shutting down and no longer accepting ingress evidence."
            )

        if not self.conn:
            self.initialize_queue()

        # Compute SHA-256 hash for Content-Addressable Hashing
        hasher = hashlib.sha256()
        hasher.update(content.encode("utf-8"))
        content_hash = hasher.hexdigest()

        # Unique identifier based on hash and client
        item_id = hashlib.sha256(
            f"{self.client_id}:{content_hash}".encode("utf-8")
        ).hexdigest()

        try:
            with self.db_lock:
                conn = self._require_connection()
                conn.execute(
                    """
                    INSERT INTO streaming_queue (id, client_id, source_url, content, content_hash)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                    status = CASE WHEN status = 'failed' THEN 'pending' ELSE status END
                    """,
                    (item_id, self.client_id, source_url, content, content_hash),
                )
                conn.commit()
            logger.info(
                f"Enqueued evidence item {item_id} from {source_url} (Delta-Checked)."
            )
            return item_id
        except Exception as e:
            logger.error(f"Failed to enqueue evidence {item_id}: {e}")
            raise

    def process_next_batch(self, batch_size: Optional[int] = None) -> int:
        """Fetches and processes the next batch of pending evidences from the queue.

        Integrates with the EvidenceEngine and RaptorEngine to ingest the text fragments,
        applying Jaccard semantic deduplication and scheduling incremental updates.
        """
        effective_batch_size = batch_size if batch_size is not None else self.batch_size
        if not self.conn:
            self.initialize_queue()

        # 1. Fetch pending items
        with self.db_lock:
            conn = self._require_connection()
            with contextlib.closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT id, source_url, content, content_hash
                    FROM streaming_queue
                    WHERE status = 'pending' AND client_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (self.client_id, effective_batch_size),
                )
                rows = cursor.fetchall()

        if not rows:
            return 0

        logger.info(
            f"Streaming Sentinel: Processing a delta batch of {len(rows)} elements."
        )

        # Import RAG and Graph services dynamically to maintain hexagonal isolation
        from assessment_engine.infrastructure.evidence_engine import EvidenceEngine

        with self._acquire_process_lock() as has_lock:
            if not has_lock:
                logger.info(
                    "Another worker process holds the OS sentinel lock. Skipping this polling interval."
                )
                return 0

            # Instantiate EvidenceEngine for cold storage layer using tenant-scoped directory
            storage_dir = self.client_dir
            storage_dir.mkdir(parents=True, exist_ok=True)
            evidence_engine = EvidenceEngine(
                client_id=self.client_id, storage_dir=storage_dir
            )

            processed_count = 0
            for item_id, _source_url, content, content_hash in rows:
                try:
                    # Atomic Multi-Worker Claiming: Verify the status is still 'pending' before updating
                    with self.db_lock:
                        conn = self._require_connection()
                        cursor = conn.execute(
                            "UPDATE streaming_queue SET status = 'processing' WHERE id = ? AND status = 'pending'",
                            (item_id,),
                        )
                        conn.commit()
                        if cursor.rowcount == 0:
                            continue

                    # Jaccard Semantic Deduplication check against the cold storage ledger
                    if self._is_semantic_duplicate(
                        content,
                        evidence_engine.ledger.fragments,
                        threshold=self.semantic_similarity_threshold,
                    ):
                        with self.db_lock:
                            conn = self._require_connection()
                            conn.execute(
                                "UPDATE streaming_queue SET status = 'processed', error_message = 'Skipped: Semantic duplicate' WHERE id = ?",
                                (item_id,),
                            )
                            conn.commit()
                        continue

                    # Write the text to a physical .txt file under the client's streaming directory
                    streaming_dir = storage_dir / "streaming"
                    streaming_dir.mkdir(parents=True, exist_ok=True)

                    hash_prefix = content_hash[:DEFAULT_HASH_PREFIX_LENGTH]
                    evidence_file = streaming_dir / f"stream_{hash_prefix}.txt"

                    # Defense-in-Depth: Path Traversal (Local File Inclusion) Guardrail
                    if not evidence_file.resolve().is_relative_to(
                        streaming_dir.resolve()
                    ):
                        raise ValueError(
                            f"Critical Security Alert: Path traversal blocked. Resolved path {evidence_file} escapes sandbox bounds."
                        )

                    tmp_suffix = uuid.uuid4().hex[:DEFAULT_TMP_SUFFIX_LENGTH]
                    tmp_evidence = (
                        streaming_dir / f"stream_{hash_prefix}.{tmp_suffix}.tmp"
                    )
                    try:
                        tmp_evidence.write_text(content, encoding="utf-8")
                        tmp_evidence.replace(evidence_file)
                    except Exception:
                        if tmp_evidence.exists():
                            tmp_evidence.unlink()
                        raise

                    # Ingest file directly into the Evidence Vault (incremental indexing)
                    evidence_engine.ingest_file(evidence_file)

                    # Mark as processed in database
                    with self.db_lock:
                        conn = self._require_connection()
                        conn.execute(
                            """
                            UPDATE streaming_queue
                            SET status = 'processed', processed_at = ?
                            WHERE id = ?
                            """,
                            (datetime.now(timezone.utc).isoformat(), item_id),
                        )
                        conn.commit()
                    processed_count += 1
                    self.dampening_buffer.append(item_id)
                    logger.info(
                        f"Successfully processed and indexed evidence item {item_id}."
                    )
                except Exception as e:
                    logger.error(f"Error processing evidence item {item_id}: {e}")
                    with self.db_lock:
                        conn = self._require_connection()
                        conn.execute(
                            "UPDATE streaming_queue SET status = 'failed', error_message = ? WHERE id = ?",
                            (str(e), item_id),
                        )
                        conn.commit()

        # 2. Dampened Batching Scheduler timestamp update
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

        if (
            len(self.dampening_buffer) >= self.dampening_batch_threshold
            or time_since_last_ingest >= self.dampening_quiet_period_sec
        ):
            logger.info(
                f"Dampened Scheduler: Triggering Raptor RAG Tree rebuild for {len(self.dampening_buffer)} items."
            )

            from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
            from assessment_engine.infrastructure.raptor_engine import RaptorEngine

            storage_dir = self.client_dir
            storage_dir.mkdir(parents=True, exist_ok=True)
            evidence_engine = EvidenceEngine(
                client_id=self.client_id, storage_dir=storage_dir
            )
            raptor = RaptorEngine(client_id=self.client_id, storage_dir=storage_dir)

            try:
                asyncio.run(raptor.build_tree(evidence_engine.ledger.fragments))
                logger.info("[RAPTOR] Dynamic Knowledge Tree updated successfully.")
            except Exception as e:
                logger.error(f"Failed to update Raptor Tree dynamically: {e}")

            # Clear the buffer after successful rebuild trigger
            self.dampening_buffer.clear()

            # Execute WAL Checkpoint during quiet period to prevent unbounded disk bloat
            try:
                if self.conn:
                    with self.db_lock:
                        conn = self._require_connection()
                        conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
                        logger.info(
                            "Streaming Sentinel: Executed PRAGMA wal_checkpoint(PASSIVE) to prevent disk bloat."
                        )
            except Exception as e:
                logger.warning(f"Failed to execute WAL checkpoint: {e}")

            return True

        return False

    async def _run_daemon_worker(
        self, poll_interval_sec: float, stop_event: asyncio.Event
    ) -> None:
        """Internal structured concurrency worker loop for polling and dampened rebuilds."""
        self.poll_interval_sec = poll_interval_sec
        logger.info(
            f"Starting Streaming Sentinel daemon worker for client {self.client_id}..."
        )
        try:
            while not stop_event.is_set():
                try:
                    processed = await asyncio.to_thread(self.process_next_batch)
                    if processed > 0:
                        logger.info(f"Sentinel Loop: Ingested {processed} new items.")

                    await asyncio.to_thread(self.check_and_trigger_dampened_rebuild)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in Sentinel daemon polling iteration: {e}")

                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=self.poll_interval_sec
                    )
                except asyncio.TimeoutError:
                    pass
        except asyncio.CancelledError:
            logger.info(
                f"Streaming Sentinel daemon worker for {self.client_id} received cancellation; draining cleanly."
            )
            raise

    async def _coordinate_with_active_daemon(
        self, stop_event: Optional[asyncio.Event]
    ) -> None:
        """Coordinates an external stop_event with the active TaskGroup daemon worker without duplicating tasks."""
        if stop_event is not None:
            while (
                not stop_event.is_set()
                and (self._stop_event is None or not self._stop_event.is_set())
                and (self._daemon_task is None or not self._daemon_task.done())
            ):
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=self.stop_wait_interval_sec
                    )
                except asyncio.TimeoutError:
                    pass
            if self._stop_event is not None:
                self._stop_event.set()

        if self._daemon_task is not None:
            await self._daemon_task

    async def start_daemon_loop(
        self,
        poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC,
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        """Starts the asynchronous daemon polling loop using Python 3.11+ structured concurrency.

        Preserves backwards compatibility when invoked directly or inside an active context
        manager while guaranteeing single-worker TaskGroup anchoring, signal handling,
        queue draining, and WAL transaction flushing.
        """
        self.poll_interval_sec = poll_interval_sec
        if self._task_group is not None:
            # Already inside `async with StreamingSentinel() as sentinel:`; coordinate with existing task
            await self._coordinate_with_active_daemon(stop_event)
            return

        async with self:
            await self._coordinate_with_active_daemon(stop_event)

        logger.info("Streaming Sentinel daemon loop stopped gracefully.")

    def get_fastapi_app(self) -> Any:
        """Returns a configured FastAPI application instance exposing the REST Webhook Endpoint.

        Allows external systems to stream evidence directly via POST /webhook/evidence.
        The FastAPI application automatically manages the lifecycle of the background daemon loop
        using structured concurrency (`async with self:`).
        """
        if not FASTAPI_AVAILABLE:
            raise RuntimeError(
                "FastAPI and Pydantic are required to run the Webhook Server."
            )

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with self:
                logger.info(
                    "FastAPI Lifespan: Streaming Sentinel structured TaskGroup started."
                )
                yield
                logger.info(
                    "FastAPI Lifespan: Shutting down and draining Streaming Sentinel..."
                )
            logger.info("FastAPI Lifespan: Background daemon stopped safely.")

        app = FastAPI(
            title=f"Streaming Sentinel Webhook - {self.client_id}", lifespan=lifespan
        )

        @app.post("/webhook/evidence")
        async def receive_evidence(payload: EvidencePayload):
            if not self._accepting_ingress:
                raise HTTPException(
                    status_code=HTTP_STATUS_SERVICE_UNAVAILABLE,
                    detail="Streaming Sentinel is shutting down and draining queues; ingress rejected.",
                )
            try:
                item_id = await asyncio.to_thread(
                    self.enqueue_evidence, payload.source_url, payload.content
                )
                return {
                    "status": "success",
                    "item_id": item_id,
                    "message": "Evidence successfully enqueued for continuous ingestion.",
                }
            except Exception as e:
                raise HTTPException(
                    status_code=HTTP_STATUS_INTERNAL_ERROR,
                    detail=f"Failed to enqueue evidence: {e}",
                )

        return app
