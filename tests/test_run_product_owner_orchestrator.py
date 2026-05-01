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


def test_push_branch_uses_origin_and_sets_upstream(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run_git_command(args: list[str]):
        calls.append(args)
        return None

    monkeypatch.setattr(orchestrator, "run_git_command", fake_run_git_command)

    orchestrator.push_branch("feat/test-branch")

    assert calls == [["git", "push", "-u", "origin", "feat/test-branch"]]


def test_main_checks_clean_worktree_before_creating_request_dir(monkeypatch) -> None:
    call_order: list[str] = []

    monkeypatch.setattr(
        orchestrator,
        "load_orchestrator_policy",
        lambda: {"paths": {"requests_root": "working/product_owner_requests"}},
    )
    monkeypatch.setattr(
        orchestrator,
        "load_request_text",
        lambda args: "Need stronger governance",
    )

    def fake_ensure_clean_worktree(*, allow_dirty: bool) -> None:
        call_order.append("ensure_clean_worktree")

    def fake_create_request_dir(policy, request_text):
        call_order.append("create_request_dir")
        return Path("/tmp/request-dir")

    monkeypatch.setattr(
        orchestrator, "ensure_clean_worktree", fake_ensure_clean_worktree
    )
    monkeypatch.setattr(orchestrator, "create_request_dir", fake_create_request_dir)
    def fake_asyncio_run(coro):
        coro.close()
        return {"tasks": []}

    monkeypatch.setattr(orchestrator.asyncio, "run", fake_asyncio_run)
    monkeypatch.setattr(orchestrator, "save_plan_bundle", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator, "resolve_executor_command", lambda raw: "executor")
    monkeypatch.setattr(orchestrator, "execute_plan", lambda *args, **kwargs: None)

    assert orchestrator.main(["run", "--request", "Need stronger governance"]) == 0
    assert call_order[:2] == ["ensure_clean_worktree", "create_request_dir"]
