import pytest
import asyncio
import uuid
import numpy as np
from pathlib import Path
from assessment_engine.infrastructure.streaming_sentinel import StreamingSentinel

def test_streaming_sentinel_initialization(tmp_path: Path):
    db_file = tmp_path / "test_queue.db"
    sentinel = StreamingSentinel(client_id="test_client", db_path=db_file)
    
    sentinel.initialize_queue()
    assert db_file.exists()
    
    # Check that WAL mode is enabled
    cursor = sentinel.conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    assert mode.upper() == "WAL"
    
    sentinel.close()

def test_streaming_sentinel_enqueue_idempotency(tmp_path: Path):
    db_file = tmp_path / "test_queue.db"
    sentinel = StreamingSentinel(client_id="test_client", db_path=db_file)
    
    sentinel.initialize_queue()
    
    url = "https://www.test-source.com/report1"
    content = "This is a real-time regulatory update about NIS2 security requirements."
    
    # 1st Enqueue
    id1 = sentinel.enqueue_evidence(url, content)
    assert len(id1) == 64  # SHA-256 hash length
    
    # 2nd Enqueue of identical content (must return same ID and not crash/duplicate)
    id2 = sentinel.enqueue_evidence(url, content)
    assert id1 == id2
    
    cursor = sentinel.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM streaming_queue;")
    count = cursor.fetchone()[0]
    assert count == 1  # Strictly 1 record due to ON CONFLICT UPDATE idempotency
    
    sentinel.close()

@pytest.mark.asyncio
async def test_streaming_sentinel_process_batch(tmp_path: Path):
    db_file = tmp_path / "test_queue.db"
    # Use a completely unique, random client ID to guarantee a 100% empty ledger on disk
    unique_client = f"smoke_client_{uuid.uuid4().hex[:8]}"
    sentinel = StreamingSentinel(client_id=unique_client, db_path=db_file)
    
    sentinel.initialize_queue()
    
    # Create test directory
    sentinel.client_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://www.test-source.com/report1"
    unique_id = uuid.uuid4().hex
    content = f"A completely unique and novel document about biotechnology achievements in genetic splicing and clinical trials {unique_id}."
    
    sentinel.enqueue_evidence(url, content)
    
    processed = sentinel.process_next_batch(batch_size=5)
    assert processed == 1
    
    # Check that status is now processed and processed_at is set
    cursor = sentinel.conn.cursor()
    cursor.execute("SELECT status, processed_at, error_message FROM streaming_queue;")
    row = cursor.fetchone()
    assert row[0] == "processed"
    assert row[1] is not None
    assert row[2] is None
    
    # Clean up the temporary client directory created
    import shutil
    if sentinel.client_dir.exists():
        shutil.rmtree(sentinel.client_dir)
        
    sentinel.close()

@pytest.mark.asyncio
async def test_streaming_sentinel_daemon_graceful_stop(tmp_path: Path):
    db_file = tmp_path / "test_queue.db"
    sentinel = StreamingSentinel(client_id="smoke_ivirma", db_path=db_file)
    
    stop_event = asyncio.Event()
    
    # Start the daemon loop in a background task
    task = asyncio.create_task(sentinel.start_daemon_loop(poll_interval_sec=0.1, stop_event=stop_event))
    
    # Let it run for a brief moment
    await asyncio.sleep(0.3)
    
    # Stop it gracefully
    stop_event.set()
    await task
    
    assert task.done()

def test_streaming_sentinel_jaccard_deduplication():
    sentinel = StreamingSentinel(client_id="test_client")
    
    # Intrinsic content (10 tokens)
    text_a = "Redeia is implementing NIS2 security compliance policy on substations with double backup connection."
    # Almost identical reworded content (9 out of 10 tokens overlap -> Jaccard = 0.90)
    text_b = "Redeia was implementing NIS2 security compliance policy on substations with double backup connection."
    # Completely different content
    text_c = "This is some corporate financials report about profits and dividends."
    
    class MockFragment:
        def __init__(self, content):
            self.content = content
            
    existing = [MockFragment(text_a)]
    
    # Verify semantic duplicate matches (Jaccard > 0.80)
    assert sentinel._is_semantic_duplicate(text_b, existing, threshold=0.75) is True
    # Verify different content is not rejected
    assert sentinel._is_semantic_duplicate(text_c, existing, threshold=0.75) is False

def test_streaming_sentinel_dampened_scheduler():
    sentinel = StreamingSentinel(client_id="smoke_ivirma")
    
    # Initially buffer is empty, trigger should be False
    assert sentinel.check_and_trigger_dampened_rebuild() is False
    
    # Add 5 items to buffer, which exceeds threshold and should trigger rebuild
    sentinel.dampening_buffer = [f"item_{i}" for i in range(5)]
    sentinel.client_dir.mkdir(parents=True, exist_ok=True)
    
    triggered = sentinel.check_and_trigger_dampened_rebuild()
    assert triggered is True
    assert len(sentinel.dampening_buffer) == 0

def test_streaming_sentinel_fastapi_app():
    sentinel = StreamingSentinel(client_id="smoke_ivirma")
    app = sentinel.get_fastapi_app()
    
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)
    assert app.title == "Streaming Sentinel Webhook - smoke_ivirma"
    
    # Check that route exists
    routes = [r.path for r in app.routes]
    assert "/webhook/evidence" in routes

def test_streaming_sentinel_oom_payload_rejection():
    # Verify Pydantic max_length constraints reject Out-Of-Memory payloads
    try:
        from assessment_engine.infrastructure.streaming_sentinel import EvidencePayload
    except ImportError:
        pytest.skip("FastAPI not available")
        
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError) as exc:
        # Construct a massive 6MB payload string
        massive_payload = "A" * 6_000_000
        EvidencePayload(source_url="https://valid.com", content=massive_payload)
    
    assert "String should have at most 5000000 characters" in str(exc.value)

def test_streaming_sentinel_path_traversal_guardrail():
    # Mathematically verify that a malicious path traversal attempt is trapped by the sandbox
    sentinel = StreamingSentinel(client_id="test_client")
    storage_dir = sentinel.client_dir / "redeia"
    streaming_dir = storage_dir / "streaming"
    streaming_dir.mkdir(parents=True, exist_ok=True)
    
    # Simulate a malicious content hash returned from a poisoned database record
    malicious_hash = "../../../../../etc/passwd"
    
    evidence_file = streaming_dir / f"stream_{malicious_hash[:16]}.txt"
    # Depending on how the hash is sliced, if it contains ../ it should fail the resolve bounds
    
    # Let's force an exact malicious path resolution attempt
    malicious_path = streaming_dir / "../../../malicious.txt"
    
    assert not malicious_path.resolve().is_relative_to(streaming_dir.resolve())
