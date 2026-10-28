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
