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


def test_inspect_pull_request_combines_checks_and_threads(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "get_pull_request",
        lambda branch_name: {
            "number": 7,
            "url": "https://example.test/pr/7",
            "headRefName": branch_name,
            "baseRefName": "main",
            "isDraft": False,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "BLOCKED",
            "reviewDecision": "",
            "statusCheckRollup": [
                {
                    "name": "quality",
                    "workflowName": "Incremental Quality Gate",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "detailsUrl": "https://example.test/check",
                }
            ],
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "get_pull_request_review_threads",
        lambda pr_number: [
            {
                "id": "thread-1",
                "isResolved": False,
                "isOutdated": False,
                "path": "src/file.py",
                "line": 10,
                "comments": {
                    "nodes": [
                        {
                            "author": {
                                "__typename": "Bot",
                                "login": "chatgpt-codex-connector",
                            },
                            "body": "Fix the path filtering.",
                            "state": "SUBMITTED",
                        }
                    ]
                },
            }
        ],
    )

    pr_state = orchestrator.inspect_pull_request("feat/test-branch")

    assert pr_state["number"] == 7
    assert pr_state["failed_checks"][0]["name"] == "quality"
    assert pr_state["unresolved_threads"][0]["all_comments_bot"] is True


def test_reconcile_pull_request_repairs_then_merges(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    plan = {"branch_name": "feat/test-branch", "commit_title": "feat: improve flow"}
    call_order: list[str] = []
    pr_states = iter(
        [
            {
                "number": 9,
                "url": "https://example.test/pr/9",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "BLOCKED",
                "review_decision": "",
                "failed_checks": [{"name": "typing"}],
                "pending_checks": [],
                "unresolved_threads": [],
            },
            {
                "number": 9,
                "url": "https://example.test/pr/9",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "CLEAN",
                "review_decision": "",
                "failed_checks": [],
                "pending_checks": [],
                "unresolved_threads": [],
            },
        ]
    )

    monkeypatch.setattr(
        orchestrator,
        "load_orchestrator_policy",
        lambda: {
            "pull_request": {
                "post_pr_reconciliation": {
                    "enabled": True,
                    "max_rounds": 2,
                    "poll_interval_seconds": 0,
                    "max_polls": 3,
                    "auto_resolve_bot_threads": True,
                }
            }
        },
    )
    monkeypatch.setattr(
        orchestrator, "inspect_pull_request", lambda branch_name: next(pr_states)
    )
    monkeypatch.setattr(
        orchestrator,
        "repair_pull_request",
        lambda *args, **kwargs: call_order.append("repair"),
    )
    monkeypatch.setattr(
        orchestrator,
        "merge_pull_request",
        lambda pr_number, merge_mode: call_order.append(
            f"merge:{pr_number}:{merge_mode}"
        ),
    )
    monkeypatch.setattr(orchestrator.time, "sleep", lambda seconds: None)

    orchestrator.reconcile_pull_request(
        request_dir,
        plan,
        executor_command="executor",
        merge_mode="squash",
    )

    assert call_order == ["repair", "merge:9:squash"]


def test_reconcile_pull_request_auto_resolves_bot_threads(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    plan = {"branch_name": "feat/test-branch", "commit_title": "feat: improve flow"}
    call_order: list[str] = []
    pr_states = iter(
        [
            {
                "number": 11,
                "url": "https://example.test/pr/11",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "BLOCKED",
                "review_decision": "",
                "failed_checks": [],
                "pending_checks": [],
                "unresolved_threads": [
                    {
                        "id": "thread-1",
                        "all_comments_bot": True,
                        "comments": [],
                    }
                ],
            },
            {
                "number": 11,
                "url": "https://example.test/pr/11",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "CLEAN",
                "review_decision": "",
                "failed_checks": [],
                "pending_checks": [],
                "unresolved_threads": [],
            },
        ]
    )

    monkeypatch.setattr(
        orchestrator,
        "load_orchestrator_policy",
        lambda: {
            "pull_request": {
                "post_pr_reconciliation": {
                    "enabled": True,
                    "max_rounds": 1,
                    "poll_interval_seconds": 0,
                    "max_polls": 3,
                    "auto_resolve_bot_threads": True,
                }
            }
        },
    )
    monkeypatch.setattr(
        orchestrator, "inspect_pull_request", lambda branch_name: next(pr_states)
    )
    monkeypatch.setattr(
        orchestrator,
        "auto_resolve_bot_threads",
        lambda pr_state: call_order.append("resolve") or 1,
    )
    monkeypatch.setattr(
        orchestrator,
        "merge_pull_request",
        lambda pr_number, merge_mode: call_order.append(
            f"merge:{pr_number}:{merge_mode}"
        ),
    )
    monkeypatch.setattr(orchestrator.time, "sleep", lambda seconds: None)

    orchestrator.reconcile_pull_request(
        request_dir,
        plan,
        executor_command="executor",
        merge_mode="squash",
    )

    assert call_order == ["resolve", "merge:11:squash"]


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
    monkeypatch.setattr(
        orchestrator, "resolve_executor_command", lambda raw: "executor"
    )
    monkeypatch.setattr(orchestrator, "execute_plan", lambda *args, **kwargs: None)

    assert orchestrator.main(["run", "--request", "Need stronger governance"]) == 0
    assert call_order[:2] == ["ensure_clean_worktree", "create_request_dir"]


def test_execute_plan_runs_reconciliation_before_auto_merge(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    plan = {
        "branch_name": "feat/test-branch",
        "commit_title": "feat: safer auto merge",
        "tasks": [],
    }
    calls: list[str] = []

    monkeypatch.setattr(
        orchestrator,
        "load_orchestrator_policy",
        lambda: {
            "execution": {"max_attempts_per_task": 3},
            "pull_request": {
                "auto_merge_enabled": True,
                "auto_merge_mode": "squash",
            },
        },
    )
    monkeypatch.setattr(
        orchestrator, "ensure_branch", lambda branch_name: calls.append("branch")
    )
    monkeypatch.setattr(
        orchestrator, "create_commit", lambda title: calls.append("commit")
    )
    monkeypatch.setattr(
        orchestrator,
        "create_pr",
        lambda plan, request_dir, *, skip_auto_merge: calls.append("pr"),
    )
    monkeypatch.setattr(
        orchestrator,
        "reconcile_pull_request",
        lambda request_dir, plan, *, executor_command, merge_mode: calls.append(
            f"reconcile:{merge_mode}"
        ),
    )

    orchestrator.execute_plan(
        request_dir,
        plan,
        executor_command="executor",
        skip_pr=False,
        skip_auto_merge=False,
    )

    assert calls == ["branch", "commit", "pr", "reconcile:squash"]
