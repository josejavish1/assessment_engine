"""Unit tests for the PersistentJobStore finite state machine and TTL garbage collection."""

import json
import time
from pathlib import Path

import pytest

from assessment_engine import mcp_server
from assessment_engine.mcp_server import (
    JobState,
    PersistentJobStore,
    _PersistentResultMapProxy,
    _PersistentStatusMapProxy,
)


def test_sqlite_wal_mode_and_persistence_across_restarts(tmp_path: Path) -> None:
    """Verifies that jobs.db operates in WAL mode and survives store re-instantiation."""
    db_file = tmp_path / "jobs.db"
    store_1 = PersistentJobStore(db_path=db_file, ttl_seconds=86400)

    with store_1._connect() as conn:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert str(mode).lower() == "wal"

    created = store_1.create_job(job_id="job-persist-1")
    assert created.state == JobState.PENDING

    running = store_1.transition_state("job-persist-1", JobState.RUNNING)
    assert running.state == JobState.RUNNING

    # Simulate process restart by instantiating a brand new store on the same DB file.
    store_2 = PersistentJobStore(db_path=db_file, ttl_seconds=86400)
    recovered = store_2.get_job("job-persist-1")
    assert recovered is not None
    assert recovered.state == JobState.RUNNING

    completed = store_2.transition_state(
        "job-persist-1", JobState.COMPLETED, result="done"
    )
    assert completed.state == JobState.COMPLETED
    assert completed.result == "done"


def test_finite_state_machine_enforces_valid_transitions(tmp_path: Path) -> None:
    """Verifies strict enforcement of PENDING -> RUNNING -> COMPLETED | FAILED."""
    db_file = tmp_path / "jobs.db"
    store = PersistentJobStore(db_path=db_file, ttl_seconds=86400)

    store.create_job(job_id="job-fsm-1")

    # Direct PENDING -> COMPLETED must be rejected.
    with pytest.raises(ValueError, match="Invalid job state transition"):
        store.transition_state("job-fsm-1", JobState.COMPLETED)

    store.transition_state("job-fsm-1", JobState.RUNNING)
    store.transition_state("job-fsm-1", JobState.COMPLETED, result="ok")

    # Terminal COMPLETED -> RUNNING or FAILED must be rejected.
    with pytest.raises(ValueError, match="Invalid job state transition"):
        store.transition_state("job-fsm-1", JobState.RUNNING)
    with pytest.raises(ValueError, match="Invalid job state transition"):
        store.transition_state("job-fsm-1", JobState.FAILED)


def test_ttl_garbage_collection_on_initialization(tmp_path: Path) -> None:
    """Verifies that jobs older than 24 hours are purged upon server/store initialization."""
    db_file = tmp_path / "jobs.db"
    store = PersistentJobStore(db_path=db_file, ttl_seconds=86400)

    store.create_job(job_id="expired-job")
    store.create_job(job_id="active-job")

    expired_ts = time.time() - 90000
    with store._connect() as conn:
        conn.execute(
            "UPDATE jobs SET created_at = ?, updated_at = ? WHERE job_id = ?;",
            (expired_ts, expired_ts, "expired-job"),
        )

    # Re-initializing the store triggers TTL eviction automatically.
    reinitialized_store = PersistentJobStore(db_path=db_file, ttl_seconds=86400)
    assert reinitialized_store.get_job("expired-job") is None
    assert reinitialized_store.get_job("active-job") is not None


def test_legacy_mapping_proxies_and_status_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies backwards compatibility with job_status/job_results dicts and MCP status tools."""
    db_file = tmp_path / "jobs.db"
    test_store = PersistentJobStore(db_path=db_file, ttl_seconds=86400)
    monkeypatch.setattr(mcp_server, "_JOB_STORE", test_store)
    monkeypatch.setattr(
        mcp_server, "job_status", _PersistentStatusMapProxy(test_store)
    )
    monkeypatch.setattr(
        mcp_server, "job_results", _PersistentResultMapProxy(test_store)
    )

    mcp_server.job_status["legacy-job"] = "running"
    mcp_server.job_results["legacy-job"] = "initial output"
    assert json.loads(mcp_server.check_plan_status("legacy-job")) == {
        "status": "running",
        "state": "RUNNING",
    }

    mcp_server.job_results["legacy-job"] = "final plan output"
    mcp_server.job_status["legacy-job"] = "completed"

    plan_status = json.loads(mcp_server.check_plan_status("legacy-job"))
    assert plan_status["status"] == "completed"
    assert plan_status["state"] == "COMPLETED"
    assert plan_status["result"] == "final plan output"

    exec_status = json.loads(mcp_server.check_execution_status("legacy-job"))
    assert exec_status["status"] == "completed"
    assert exec_status["state"] == "COMPLETED"
    assert exec_status["result"] == "final plan output"
