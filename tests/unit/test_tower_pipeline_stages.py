"""Tests for tower pipeline stages and orchestration utilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from assessment_engine.application.run_tower_pipeline import (
    PipelineConfig,
    _stage_case_input_and_short_circuit,
    slugify,
)


def test_slugify_normalization():
    """Verify that slugify normalizes accent marks, whitespace, and special characters."""
    assert slugify("Redeia Corporación S.A.") == "redeia_corporacion_s_a"
    assert slugify("ÁÉÍÓÚ ñ") == "aeiou_n"
    assert slugify("") == "client"


@pytest.mark.asyncio
async def test_short_circuit_on_empty_answers(tmp_path: Path):
    """Verify that _stage_case_input_and_short_circuit terminates execution early when answers are empty."""
    case_dir = tmp_path / "T1"
    case_dir.mkdir(parents=True, exist_ok=True)
    case_input_file = case_dir / "case_input.json"
    case_input_file.write_text(json.dumps({"answers": []}), encoding="utf-8-sig")

    cfg = PipelineConfig(
        args=argparse.Namespace(client="TestClient"),
        tower_id="T1",
        client_slug="testclient",
        python_bin="python3",
        env={},
        case_dir=case_dir,
        context_path=str(tmp_path / "context.docx"),
        responses_path=str(tmp_path / "responses.xlsx"),
        payload_path=case_dir / "annex.json",
        output_docx=case_dir / "annex.docx",
        output_asis_docx=case_dir / "asis.docx",
        blueprint_payload_path=case_dir / "blueprint.json",
        output_blueprint_docx=case_dir / "blueprint.docx",
        force=False,
    )

    should_stop = await _stage_case_input_and_short_circuit(cfg)
    assert should_stop is True


@pytest.mark.asyncio
async def test_short_circuit_bypassed_with_answers(tmp_path: Path):
    """Verify that _stage_case_input_and_short_circuit continues execution when valid answers exist."""
    case_dir = tmp_path / "T1"
    case_dir.mkdir(parents=True, exist_ok=True)
    case_input_file = case_dir / "case_input.json"
    case_input_file.write_text(
        json.dumps({"answers": [{"kpi_id": "T1.P1.K1.PR1", "value": 4}]}),
        encoding="utf-8-sig",
    )

    cfg = PipelineConfig(
        args=argparse.Namespace(client="TestClient"),
        tower_id="T1",
        client_slug="testclient",
        python_bin="python3",
        env={},
        case_dir=case_dir,
        context_path=str(tmp_path / "context.docx"),
        responses_path=str(tmp_path / "responses.xlsx"),
        payload_path=case_dir / "annex.json",
        output_docx=case_dir / "annex.docx",
        output_asis_docx=case_dir / "asis.docx",
        blueprint_payload_path=case_dir / "blueprint.json",
        output_blueprint_docx=case_dir / "blueprint.docx",
        force=False,
    )

    should_stop = await _stage_case_input_and_short_circuit(cfg)
    assert should_stop is False


def test_parse_and_prepare_pipeline_arguments():
    """Verify CLI argument parsing and configuration path initialization."""
    from assessment_engine.application.run_tower_pipeline import _parse_and_prepare_pipeline

    cfg = _parse_and_prepare_pipeline([
        "--tower", "T2",
        "--client", "Iberdrola Renovable",
        "--context-file", "ctx.docx",
        "--responses-file", "resp.xlsx",
    ])
    assert cfg.tower_id == "T2"
    assert cfg.client_slug == "iberdrola_renovable"
    assert "T2" in str(cfg.case_dir)
    assert cfg.output_docx.suffix == ".docx"
    assert cfg.payload_path.suffix == ".json"


@pytest.mark.asyncio
async def test_run_step_async_execution():
    """Verify that run_step_async executes a real non-blocking subprocess successfully."""
    import sys
    from assessment_engine.application.run_tower_pipeline import run_step_async

    cmd = [sys.executable, "-c", "import sys; sys.exit(0)"]
    # Should complete without error
    await run_step_async(cmd, env={}, step_name="Test Subprocess")


@pytest.mark.asyncio
async def test_stage_scoring_and_qualitative_chain_mock(tmp_path: Path):
    """Verify that _stage_scoring_and_qualitative_chain triggers pipeline stages when files are absent."""
    from unittest.mock import AsyncMock, patch
    from assessment_engine.application.run_tower_pipeline import _stage_scoring_and_qualitative_chain

    case_dir = tmp_path / "T1"
    case_dir.mkdir(parents=True, exist_ok=True)

    cfg = PipelineConfig(
        args=argparse.Namespace(client="TestClient"),
        tower_id="T1",
        client_slug="testclient",
        python_bin="python3",
        env={},
        case_dir=case_dir,
        context_path=str(tmp_path / "context.docx"),
        responses_path=str(tmp_path / "responses.xlsx"),
        payload_path=case_dir / "annex.json",
        output_docx=case_dir / "annex.docx",
        output_asis_docx=case_dir / "asis.docx",
        blueprint_payload_path=case_dir / "blueprint.json",
        output_blueprint_docx=case_dir / "blueprint.docx",
        force=True,
    )

    with patch(
        "assessment_engine.application.run_tower_pipeline.run_step_async",
        new_callable=AsyncMock,
    ) as mock_step:
        # Pre-create findings to avoid polling loop
        (case_dir / "findings.json").write_text("{}", encoding="utf-8")
        await _stage_scoring_and_qualitative_chain(cfg)
        assert mock_step.call_count >= 3


@pytest.mark.asyncio
async def test_stage_evidence_and_benchmarks_mock(tmp_path: Path):
    """Verify that _stage_evidence_and_benchmarks executes evidence ledger and benchmark stages."""
    from unittest.mock import AsyncMock, patch
    from assessment_engine.application.run_tower_pipeline import _stage_evidence_and_benchmarks

    case_dir = tmp_path / "T1"
    case_dir.mkdir(parents=True, exist_ok=True)

    cfg = PipelineConfig(
        args=argparse.Namespace(client="TestClient"),
        tower_id="T1",
        client_slug="testclient",
        python_bin="python3",
        env={},
        case_dir=case_dir,
        context_path=str(tmp_path / "context.docx"),
        responses_path=str(tmp_path / "responses.xlsx"),
        payload_path=case_dir / "annex.json",
        output_docx=case_dir / "annex.docx",
        output_asis_docx=case_dir / "asis.docx",
        blueprint_payload_path=case_dir / "blueprint.json",
        output_blueprint_docx=case_dir / "blueprint.docx",
        force=True,
    )

    with patch(
        "assessment_engine.application.run_tower_pipeline.run_step_async",
        new_callable=AsyncMock,
    ) as mock_step:
        # Pre-create evidence ledger so wait loop exits immediately
        (case_dir / "evidence_ledger.json").write_text("{}", encoding="utf-8")
        await _stage_evidence_and_benchmarks(cfg)
        assert mock_step.call_count >= 1
