import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from assessment_engine.infrastructure.agentic_benchmarker import (
    AgenticRageBenchmarker,
    FactExtractionOutput,
    VerificationOutput,
)


@pytest.mark.asyncio
async def test_rage_benchmarker_full_flow(tmp_path):
    # Setup mock returns
    mock_extraction = FactExtractionOutput(
        extracted_value=65.0,
        verbatim_quote="El 65% de las utilities están certificadas en ENS Categoría Alta",
        source_url="https://example.com/ens_report.pdf",
        justification="Se verificó el 65% de adopción.",
    )
    mock_verification = VerificationOutput(is_verified=True, critique="Confirmado")

    # Mock EvidenceSnapshotter capture_snapshot
    mock_snapshot_meta = {
        "status": "verified",
        "local_snapshot": str(tmp_path / "evidence_snapshots/mock_ens_report.pdf"),
        "content_hash": "abc123hash",
    }

    # Write dummy content to the mock snapshot file so verifier can read it
    snapshots_dir = tmp_path / "evidence_snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_file = snapshots_dir / "mock_ens_report.pdf"
    snapshot_file.write_text("El 65% de las utilities están certificadas en ENS Categoría Alta", encoding="utf-8")

    with patch(
        "assessment_engine.infrastructure.agentic_benchmarker.run_agent"
    ) as mock_run, patch(
        "assessment_engine.infrastructure.agentic_benchmarker.EvidenceSnapshotter.capture_snapshot",
        new_callable=AsyncMock,
    ) as mock_capture:

        # Configure mock_run to return the extraction and verification for each of the 4 evaluated towers (T1, T4, T5, T6)
        mock_run.side_effect = [
            # T1
            mock_extraction, mock_verification,
            # T4
            mock_extraction, mock_verification,
            # T5
            mock_extraction, mock_verification,
            # T6
            mock_extraction, mock_verification,
        ]
        mock_capture.return_value = mock_snapshot_meta

        # Instantiate Benchmarker with temporary directory
        benchmarker = AgenticRageBenchmarker(
            client_id="test_client", working_dir=tmp_path, model_name="mock-model"
        )

        # Run evaluation against "critical_infrastructure"
        snapshot = await benchmarker.run_rage_evaluation("critical_infrastructure")

        # Assertions
        assert snapshot.client_id == "test_client"
        assert snapshot.industry == "critical_infrastructure"
        assert "T6" in snapshot.snapshots

        t6_snap = snapshot.snapshots["T6"]
        assert t6_snap.framework_id == "ens_alta"
        assert t6_snap.extracted_metric_value == 65.0
        assert t6_snap.dynamic_score == 4.5  # 65.0 >= 60.0 matches score 4.5
        assert t6_snap.verification_status == "verified"
        assert t6_snap.evidence_source_url == "https://example.com/ens_report.pdf"
        assert "mock_ens_report.pdf" in t6_snap.local_snapshot_path
