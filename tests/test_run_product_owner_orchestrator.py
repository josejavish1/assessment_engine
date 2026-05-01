from __future__ import annotations

from pathlib import Path

import pytest

from assessment_engine.scripts.tools import (
    run_product_owner_orchestrator as orchestrator,
)


def test_load_request_text_prefers_inline_request() -> None:
    args = orchestrator.parse_args(
        ["plan", "--request", "Need a stronger global report"]
    )

    assert orchestrator.load_request_text(args) == "Need a stronger global report"


def test_load_request_text_reads_file(tmp_path: Path) -> None:
    request_file = tmp_path / "request.txt"
    request_file.write_text("Need better docs\n", encoding="utf-8")

    args = orchestrator.parse_args(["plan", "--request-file", str(request_file)])

    assert orchestrator.load_request_text(args) == "Need better docs"


def test_resolve_executor_command_rejects_missing_executor(monkeypatch) -> None:
    monkeypatch.delenv("ASSESSMENT_ORCHESTRATOR_EXECUTOR_CMD", raising=False)

    with pytest.raises(RuntimeError, match="No hay executor configurado"):
        orchestrator.resolve_executor_command(None)


def test_build_executor_args_supports_placeholders() -> None:
    args = orchestrator.build_executor_args(
        "agent --workspace {repo_root} --task {task_prompt_file} --attempt {attempt}",
        task_prompt_file=Path("/tmp/task.md"),
        attempt=2,
    )

    assert "--workspace" in args
    assert "/tmp/task.md" in args
    assert "2" in args


def test_create_pr_body_includes_spec_and_tasks() -> None:
    plan = {
        "problem": "Need stronger review",
        "value_expected": "Safer merges",
        "in_scope": ["PR workflow"],
        "out_of_scope": ["pipeline refactor"],
        "source_of_truth": ["docs/operations/agentic-development-workflow.md"],
        "invariants": ["keep main protected"],
        "validation_plan": ["pytest tests/ -q"],
        "tasks": [{"id": "task-1", "title": "Update PR template"}],
    }

    body = orchestrator.create_pr_body(plan)

    assert "## Change spec" in body
    assert "Update PR template" in body
    assert "keep main protected" in body
