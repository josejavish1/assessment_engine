from __future__ import annotations

import json
from pathlib import Path

from assessment_engine.domain.schemas.context import AssessmentContext


def test_assessment_context_in_memory_lifecycle(tmp_path: Path):
    """Verify that AssessmentContext maintains in-memory state and checkpoints cleanly."""
    ctx = AssessmentContext(
        client_name="Test Enterprise Corp",
        tower_id="T1",
        case_dir=tmp_path,
        industry="Financial Services",
    )

    # 1. Verify in-memory state mutation without disk writes
    assert ctx.completed_stages == []
    assert not ctx.has_stage("scoring")

    mock_case_input = {"tower": "T1", "parameters": {"cluster_count": 4}}
    mock_findings = {"findings": [{"id": "F-01", "tef": 2.5, "lm": 50000}]}

    ctx.case_input = mock_case_input
    ctx.mark_stage_done("case_input")
    ctx.findings = mock_findings
    ctx.mark_stage_done("findings")

    assert ctx.has_stage("case_input")
    assert ctx.has_stage("findings")
    assert not (tmp_path / "findings.json").exists(), "Should not write to disk implicitly"

    # 2. Verify deterministic checkpointing
    ctx.checkpoint_to_disk()
    assert (tmp_path / "case_input.json").is_file()
    assert (tmp_path / "findings.json").is_file()

    saved_findings = json.loads((tmp_path / "findings.json").read_text(encoding="utf-8"))
    assert saved_findings == mock_findings

    # 3. Verify clean hydration from disk checkpoints
    hydrated = AssessmentContext.hydrate_from_disk(
        client_name="Test Enterprise Corp",
        tower_id="T1",
        case_dir=tmp_path,
    )
    assert hydrated.has_stage("case_input")
    assert hydrated.has_stage("findings")
    assert hydrated.case_input == mock_case_input
    assert hydrated.findings == mock_findings
