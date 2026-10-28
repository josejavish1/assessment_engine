"""Unit tests for commercial and global assessment pipeline orchestration."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

from assessment_engine.application.run_commercial_pipeline import main as main_commercial_pipeline
from assessment_engine.application.run_global_pipeline import main as main_global_pipeline


def test_run_commercial_pipeline_mock_execution(monkeypatch):
    """Verify that run_commercial_pipeline orchestrates refinement and report rendering steps."""
    monkeypatch.setenv("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "1")

    with patch(
        "assessment_engine.application.run_commercial_pipeline.run_module_step"
    ) as mock_step:
        main_commercial_pipeline(["run_commercial", "TestClient"])
        assert mock_step.call_count == 2
        # First call is commercial refiner, second is commercial renderer
        call1_args = mock_step.call_args_list[0][0][0]
        call2_args = mock_step.call_args_list[1][0][0]
        assert "run_commercial_refiner" in " ".join(call1_args)
        assert "render_commercial_report" in " ".join(call2_args)


def test_run_commercial_pipeline_missing_args():
    """Verify CLI argument error handling."""
    with pytest.raises(SystemExit) as exc_info:
        main_commercial_pipeline(["run_commercial"])
    assert exc_info.value.code == 1


def test_run_global_pipeline_mock_execution(monkeypatch):
    """Verify that run_global_pipeline orchestrates all 6 global assessment subprocesses."""
    monkeypatch.setenv("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "1")

    with patch(
        "assessment_engine.application.run_global_pipeline.run_module_step"
    ) as mock_step:
        main_global_pipeline(["run_global", "TestClient"])
        # Expect 7 stages: build payload, export graph, refine payload, radar chart, roadmap, docx report, lineage portal
        assert mock_step.call_count == 7


def test_run_global_pipeline_missing_args():
    """Verify CLI argument error handling for global pipeline."""
    with pytest.raises(SystemExit) as exc_info:
        main_global_pipeline(["run_global"])
    assert exc_info.value.code == 1
