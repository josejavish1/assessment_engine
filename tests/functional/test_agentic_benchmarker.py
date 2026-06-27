# golden-path: ignore
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from assessment_engine.infrastructure.agentic_benchmarker import (
    AgenticRageBenchmarker,
    FactExtractionOutput,
    VerificationOutput,
)


@pytest.mark.asyncio
async def test_rage_benchmarker_full_flow(tmp_path: Path):
    """Verify the entire RAGE benchmarker flow using Semantic VCR playback.

    This is an elite SOTA test harness that reads real agent responses from a
    semantic cassette JSON file and replays them dynamically, eliminating fragile,
    traditional mock-heavy stubs.
    """
    # 1. --- ARRANGE ---
    # Setup the isolated sandbox directory structure for the test
    working_dir = tmp_path / "working"
    working_dir.mkdir(parents=True, exist_ok=True)

    # Resolve paths for the Semantic VCR cassette
    repo_root = Path(__file__).resolve().parents[2]
    cassette_path = repo_root / "tests/functional/cassettes/rage_benchmarker_flow.json"
    
    assert cassette_path.exists(), "The Semantic VCR cassette is missing!"
    with open(cassette_path, "r", encoding="utf-8") as f:
        cassette_data = json.load(f)

    # Setup dummy local snapshots to simulate downloaded PDF evidence
    snapshots_dir = tmp_path / "evidence_snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Write dummy content representing verified evidence for each evaluated tower
    for tower_id in ["T1", "T4", "T5", "T6"]:
        ext_key = f"{tower_id}_Extraction"
        quote = cassette_data[ext_key]["verbatim_quote"]
        snapshot_file = snapshots_dir / f"mock_report_{tower_id}.pdf"
        snapshot_file.write_text(f"Evidence context: {quote}", encoding="utf-8")

    # Mock the EvidenceSnapshotter behavior to return our sandboxed snapshot paths
    mock_snapshot_meta = {
        "status": "verified",
        "local_snapshot": "",  # To be dynamically updated in our mock implementation
        "content_hash": "abc123hash"
    }

    async def mock_capture_snapshot_impl(url, **kwargs):
        # Dynamically match which tower we are capturing for by looking at the URL
        # e.g., mapping URL to our dummy local sandbox files
        tower_id = "T6"
        for t in ["T1", "T4", "T5", "T6"]:
            if f"_{t.lower()}_" in url or f"/{t.lower()}_" in url:
                tower_id = t
                break
        
        meta = dict(mock_snapshot_meta)
        meta["local_snapshot"] = str(snapshots_dir / f"mock_report_{tower_id}.pdf")
        return meta

    # Semantic VCR: Intercept run_agent and return cassette-based data dynamically
    async def mock_run_agent_impl(app, user_id, message, schema=None, **kwargs):
        if schema == FactExtractionOutput:
            # Extract tower ID from user_id (e.g. "rage_research_T1")
            tower_id = user_id.replace("rage_research_", "")
            ext_key = f"{tower_id}_Extraction"
            return cassette_data[ext_key]
            
        elif schema == VerificationOutput:
            # Resolve the correct tower by finding which verbatim quote is in the prompt
            resolved_tower_id = "T6"
            for t in ["T1", "T4", "T5", "T6"]:
                ext_key = f"{t}_Extraction"
                quote = cassette_data[ext_key]["verbatim_quote"]
                if quote in message:
                    resolved_tower_id = t
                    break
                    
            ver_key = f"{resolved_tower_id}_Verification"
            return cassette_data[ver_key]
            
        return {}

    # 2. --- ACT ---
    # Run the benchmarker within our mocked environment
    with (
        patch("assessment_engine.infrastructure.agentic_benchmarker.run_agent", new_callable=AsyncMock) as mock_run,
        patch("assessment_engine.infrastructure.agentic_benchmarker.EvidenceSnapshotter.capture_snapshot", new_callable=AsyncMock) as mock_capture,
        patch("assessment_engine.infrastructure.agentic_benchmarker.AdkApp")
    ):
        mock_run.side_effect = mock_run_agent_impl
        mock_capture.side_effect = mock_capture_snapshot_impl

        benchmarker = AgenticRageBenchmarker(
            client_id="test_client",
            working_dir=working_dir,
            model_name="gemini-2.5-pro"
        )

        snapshot = await benchmarker.run_rage_evaluation("critical_infrastructure")

    # 3. --- ASSERT ---
    # Validate the final RAGE snapshot output integrity and score metrics
    assert snapshot.client_id == "test_client"
    assert snapshot.industry == "critical_infrastructure"
    assert "T1" in snapshot.snapshots
    assert "T4" in snapshot.snapshots
    assert "T5" in snapshot.snapshots
    assert "T6" in snapshot.snapshots

    # T1: 85.0% controls completed -> Dynamic Score 4.5
    t1_snap = snapshot.snapshots["T1"]
    assert t1_snap.framework_id == "google_dora"
    assert t1_snap.extracted_metric_value == 85.0
    assert t1_snap.dynamic_score == 4.5
    assert t1_snap.verification_status == "verified"
    assert "mock_report_T1.pdf" in t1_snap.local_snapshot_path

    # T6: 65.0% adoption controls -> Dynamic Score 4.5
    t6_snap = snapshot.snapshots["T6"]
    assert t6_snap.framework_id == "ens_alta"
    assert t6_snap.extracted_metric_value == 65.0
    assert t6_snap.dynamic_score == 4.5
    assert t6_snap.verification_status == "verified"
    assert "mock_report_T6.pdf" in t6_snap.local_snapshot_path
