from __future__ import annotations

import json
import os
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


def test_classify_command_failure_detects_executor_auth() -> None:
    category = orchestrator.classify_command_failure(
        ["gemini", "-p", "prompt"],
        "Please set an Auth method in your settings or specify GEMINI_API_KEY, GOOGLE_GENAI_USE_VERTEXAI, GOOGLE_GENAI_USE_GCA.",
    )

    assert category == "executor_auth"


def test_resolve_resume_selector_prefers_branch() -> None:
    args = orchestrator.parse_args(["resume-pr", "--branch", "feat/test"])

    assert orchestrator.resolve_resume_selector(args) == "feat/test"


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

    assert orchestrator.ORCHESTRATOR_MANAGED_MARKER in body
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
                            "databaseId": 321,
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
    assert pr_state["unresolved_threads"][0]["comments"][0]["database_id"] == 321


def test_ignore_current_reconciliation_check_filters_active_workflow(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_WORKFLOW", "Orchestrator PR Reconciliation")
    monkeypatch.setenv("GITHUB_JOB", "reconcile")

    checks = [
        {
            "name": "reconcile",
            "workflow_name": "Orchestrator PR Reconciliation",
            "status": "IN_PROGRESS",
            "conclusion": "",
            "details_url": "https://github.com/org/repo/actions/runs/12345/job/1",
        },
        {
            "name": "typing",
            "workflow_name": "Incremental Type Check",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
            "details_url": "https://example.test/check",
        },
    ]
    pr_state = {
        "number": 7,
        "url": "https://example.test/pr/7",
        "is_draft": False,
        "mergeable": "MERGEABLE",
        "merge_state_status": "BLOCKED",
        "review_decision": "",
        "checks": checks,
        "failed_checks": [],
        "pending_checks": [
            {
                "name": "reconcile",
                "workflow_name": "Orchestrator PR Reconciliation",
                "status": "IN_PROGRESS",
                "conclusion": "",
                "details_url": "https://github.com/org/repo/actions/runs/12345/job/1",
            },
        ],
        "unresolved_threads": [],
    }

    filtered = orchestrator.ignore_current_reconciliation_check(pr_state)

    assert filtered["checks"] == [checks[1]]
    assert filtered["pending_checks"] == []


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
    summary = json.loads(
        (request_dir / orchestrator.RECONCILIATION_SUMMARY_FILE).read_text(
            encoding="utf-8"
        )
    )
    assert summary["status"] == "merged"


def test_repair_pull_request_allows_noop_when_validations_pass(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    prompt_path = request_dir / "pr_reconciliation_1.md"
    outputs: list[str] = []

    monkeypatch.setattr(
        orchestrator,
        "render_pr_reconciliation_prompt",
        lambda *args, **kwargs: "prompt",
    )
    monkeypatch.setattr(
        orchestrator,
        "build_executor_args",
        lambda template, *, task_prompt_file, attempt: [
            "executor",
            str(task_prompt_file),
        ],
    )
    monkeypatch.setattr(
        orchestrator,
        "run_command",
        lambda command, *, output_path: outputs.append(str(output_path)),
    )
    monkeypatch.setattr(orchestrator, "has_worktree_changes", lambda: False)
    monkeypatch.setattr(
        orchestrator,
        "run_standard_validations",
        lambda request_dir: outputs.append("validated"),
    )
    monkeypatch.setattr(
        orchestrator,
        "create_commit",
        lambda title: pytest.fail("should not commit on noop repair"),
    )
    monkeypatch.setattr(
        orchestrator,
        "push_branch",
        lambda branch_name: pytest.fail("should not push on noop repair"),
    )

    changed = orchestrator.repair_pull_request(
        request_dir,
        {"branch_name": "feat/test-branch", "commit_title": "feat: improve flow"},
        executor_command="executor",
        pr_state={
            "number": 1,
            "url": "https://example.test/pr/1",
            "merge_state_status": "BLOCKED",
            "mergeable": "MERGEABLE",
            "review_decision": "",
            "failed_checks": [],
            "pending_checks": [],
            "unresolved_threads": [],
        },
        round_number=1,
    )

    assert changed is False
    assert prompt_path.read_text(encoding="utf-8") == "prompt"
    assert "validated" in outputs


def test_validate_executor_configuration_rejects_disabled_google_auth_without_keys(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_GCA", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "0")

    with pytest.raises(RuntimeError, match="El executor de Gemini requiere"):
        orchestrator.preflight_executor(
            request_dir,
            "./.github/scripts/orchestrator-gemini-executor.sh {repo_root} {task_prompt_file} {attempt}",
        )


def test_preflight_executor_runs_wrapper_probe(monkeypatch, tmp_path: Path) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "1")
    calls: list[tuple[list[str], Path, str | None]] = []

    def fake_run_command(command: list[str], *, output_path: Path) -> None:
        calls.append(
            (
                command,
                output_path,
                os.environ.get("ORCHESTRATOR_EXECUTOR_PREFLIGHT"),
            )
        )

    monkeypatch.setattr(orchestrator, "run_command", fake_run_command)

    orchestrator.preflight_executor(
        request_dir,
        "./.github/scripts/orchestrator-gemini-executor.sh {repo_root} {task_prompt_file} {attempt}",
    )

    assert calls
    assert calls[0][2] == "1"
    assert calls[0][1].name == "executor_preflight.log"
    assert (
        (request_dir / "executor_preflight_prompt.md")
        .read_text(encoding="utf-8")
        .startswith("Executor preflight.")
    )


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

    def fake_auto_resolve_bot_threads(pr_state: dict[str, object]) -> int:
        call_order.append("resolve")
        return 1

    monkeypatch.setattr(
        orchestrator,
        "auto_resolve_bot_threads",
        fake_auto_resolve_bot_threads,
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


def test_auto_resolve_bot_threads_replies_before_resolving(monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        orchestrator,
        "repository_coordinates",
        lambda: ("josejavish1", "assessment_engine"),
    )

    def fake_run_git_command(args: list[str]):
        calls.append(args)
        return None

    monkeypatch.setattr(orchestrator, "run_git_command", fake_run_git_command)

    resolved = orchestrator.auto_resolve_bot_threads(
        {
            "number": 6,
            "unresolved_threads": [
                {
                    "id": "thread-1",
                    "is_outdated": True,
                    "all_comments_bot": True,
                    "comments": [
                        {
                            "database_id": 987,
                            "author": "chatgpt-codex-connector",
                            "author_type": "Bot",
                            "body": "top-level comment",
                            "state": "SUBMITTED",
                        },
                        {
                            "database_id": 654,
                            "author": "chatgpt-codex-connector",
                            "author_type": "Bot",
                            "body": "reply comment",
                            "state": "SUBMITTED",
                        },
                    ],
                }
            ],
        }
    )

    assert resolved == 1
    assert calls[0][:4] == [
        "gh",
        "api",
        "repos/josejavish1/assessment_engine/pulls/6/comments/987/replies",
        "-f",
    ]
    assert "Automated reconciliation note:" in calls[0][4]
    assert calls[1][:4] == ["gh", "api", "graphql", "-f"]


def test_reconcile_pull_request_waits_for_pending_checks_before_repair(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    plan = {"branch_name": "feat/test-branch", "commit_title": "feat: improve flow"}
    call_order: list[str] = []
    pr_states = iter(
        [
            {
                "number": 13,
                "url": "https://example.test/pr/13",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "BLOCKED",
                "review_decision": "",
                "failed_checks": [],
                "pending_checks": [{"name": "typing"}],
                "unresolved_threads": [{"id": "thread-1", "all_comments_bot": True}],
            },
            {
                "number": 13,
                "url": "https://example.test/pr/13",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "BLOCKED",
                "review_decision": "",
                "failed_checks": [],
                "pending_checks": [],
                "unresolved_threads": [{"id": "thread-1", "all_comments_bot": True}],
            },
            {
                "number": 13,
                "url": "https://example.test/pr/13",
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
                    "max_polls": 4,
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
        lambda *args, **kwargs: pytest.fail(
            "should not repair while checks are pending"
        ),
    )

    def fake_auto_resolve_bot_threads(pr_state: dict[str, object]) -> int:
        call_order.append("resolve")
        return 1

    monkeypatch.setattr(
        orchestrator,
        "auto_resolve_bot_threads",
        fake_auto_resolve_bot_threads,
    )
    monkeypatch.setattr(
        orchestrator,
        "merge_pull_request",
        lambda pr_number, merge_mode: call_order.append(
            f"merge:{pr_number}:{merge_mode}"
        ),
    )
    monkeypatch.setattr(
        orchestrator.time, "sleep", lambda seconds: call_order.append("wait")
    )

    orchestrator.reconcile_pull_request(
        request_dir,
        plan,
        executor_command="executor",
        merge_mode="squash",
    )

    assert call_order == ["wait", "resolve", "merge:13:squash"]


def test_reconcile_pull_request_ignores_its_own_pending_check(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    plan = {"branch_name": "feat/test-branch", "commit_title": "feat: improve flow"}
    calls: list[str] = []

    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_WORKFLOW", "Orchestrator PR Reconciliation")
    monkeypatch.setenv("GITHUB_JOB", "reconcile")
    monkeypatch.setattr(
        orchestrator,
        "load_orchestrator_policy",
        lambda: {
            "pull_request": {
                "post_pr_reconciliation": {
                    "enabled": True,
                    "max_rounds": 1,
                    "poll_interval_seconds": 0,
                    "max_polls": 2,
                    "auto_resolve_bot_threads": True,
                }
            }
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "inspect_pull_request",
        lambda branch_name: {
            "number": 14,
            "url": "https://example.test/pr/14",
            "is_draft": False,
            "mergeable": "MERGEABLE",
            "merge_state_status": "CLEAN",
            "review_decision": "",
            "checks": [
                {
                    "name": "reconcile",
                    "workflow_name": "Orchestrator PR Reconciliation",
                    "status": "IN_PROGRESS",
                    "conclusion": "",
                    "details_url": "https://github.com/org/repo/actions/runs/12345/job/1",
                },
            ],
            "failed_checks": [],
            "pending_checks": [
                {
                    "name": "reconcile",
                    "workflow_name": "Orchestrator PR Reconciliation",
                    "status": "IN_PROGRESS",
                    "conclusion": "",
                    "details_url": "https://github.com/org/repo/actions/runs/12345/job/1",
                },
            ],
            "unresolved_threads": [],
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "merge_pull_request",
        lambda pr_number, merge_mode: calls.append(f"merge:{pr_number}:{merge_mode}"),
    )
    monkeypatch.setattr(
        orchestrator.time,
        "sleep",
        lambda seconds: pytest.fail(
            "should not wait on the current reconciliation check"
        ),
    )

    orchestrator.reconcile_pull_request(
        request_dir,
        plan,
        executor_command="executor",
        merge_mode="squash",
    )

    assert calls == ["merge:14:squash"]


def test_reconcile_pull_request_syncs_when_branch_is_behind(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    plan = {"branch_name": "feat/test-branch", "commit_title": "feat: improve flow"}
    call_order: list[str] = []
    pr_states = iter(
        [
            {
                "number": 12,
                "title": "Improve flow",
                "url": "https://example.test/pr/12",
                "head_ref": "feat/test-branch",
                "base_ref": "main",
                "is_draft": False,
                "mergeable": "MERGEABLE",
                "merge_state_status": "BEHIND",
                "review_decision": "",
                "failed_checks": [],
                "pending_checks": [],
                "unresolved_threads": [],
            },
            {
                "number": 12,
                "title": "Improve flow",
                "url": "https://example.test/pr/12",
                "head_ref": "feat/test-branch",
                "base_ref": "main",
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
        "sync_branch_with_base",
        lambda request_dir, plan, *, base_branch: call_order.append(
            f"sync:{base_branch}"
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "merge_pull_request",
        lambda pr_number, merge_mode: call_order.append(
            f"merge:{pr_number}:{merge_mode}"
        ),
    )

    orchestrator.reconcile_pull_request(
        request_dir,
        plan,
        executor_command="executor",
        merge_mode="squash",
    )

    assert call_order == ["sync:main", "merge:12:squash"]


def test_resume_pull_request_reuses_branch_and_runs_reconciliation(
    monkeypatch, tmp_path: Path
) -> None:
    request_dir = tmp_path / "request"
    plan = {
        "request_title": "Resume PR #6",
        "branch_name": "po-pr-sandbox",
        "pr_title": "Promote sandbox baseline",
        "commit_title": "fix: address PR feedback",
        "validation_plan": ["pytest"],
        "tasks": [],
    }
    args = orchestrator.parse_args(
        [
            "resume-pr",
            "--pr-number",
            "6",
            "--executor-command",
            "executor",
        ]
    )
    calls: list[str] = []

    monkeypatch.setattr(orchestrator, "ensure_clean_worktree", lambda **kwargs: None)
    monkeypatch.setattr(
        orchestrator,
        "inspect_pull_request",
        lambda selector: {
            "number": 6,
            "title": "Promote sandbox baseline",
            "url": "https://example.test/pr/6",
            "head_ref": "po-pr-sandbox",
            "base_ref": "main",
            "is_draft": False,
            "mergeable": "MERGEABLE",
            "merge_state_status": "BLOCKED",
            "review_decision": "",
            "failed_checks": [],
            "pending_checks": [],
            "unresolved_threads": [],
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "ensure_existing_branch",
        lambda branch_name: calls.append(f"checkout:{branch_name}"),
    )
    monkeypatch.setattr(
        orchestrator,
        "create_request_dir",
        lambda policy, request_text: request_dir,
    )
    monkeypatch.setattr(
        orchestrator,
        "prepare_resume_plan",
        lambda policy, pr_state: plan,
    )
    monkeypatch.setattr(orchestrator, "save_plan_bundle", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        orchestrator, "resolve_executor_command", lambda raw: "executor"
    )
    monkeypatch.setattr(
        orchestrator,
        "reconcile_pull_request",
        lambda request_dir, plan, *, executor_command, merge_mode, allow_merge: (
            calls.append(f"reconcile:{merge_mode}:{allow_merge}")
        ),
    )

    result = orchestrator.resume_pull_request(args, policy={"pull_request": {}})

    assert result == request_dir
    assert calls == ["checkout:po-pr-sandbox", "reconcile:squash:True"]


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


def test_main_resume_pr_skips_plan_generation(monkeypatch, tmp_path: Path) -> None:
    request_dir = tmp_path / "request"
    args = orchestrator.parse_args(
        ["resume-pr", "--branch", "po-pr-sandbox", "--executor-command", "executor"]
    )
    monkeypatch.setattr(orchestrator, "parse_args", lambda argv=None: args)
    monkeypatch.setattr(orchestrator, "load_orchestrator_policy", lambda: {})
    monkeypatch.setattr(
        orchestrator,
        "resume_pull_request",
        lambda parsed_args, *, policy: request_dir,
    )

    assert orchestrator.main(["resume-pr", "--branch", "po-pr-sandbox"]) == 0


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
        lambda request_dir, plan, *, executor_command, merge_mode, allow_merge: (
            calls.append(f"reconcile:{merge_mode}:{allow_merge}")
        ),
    )

    orchestrator.execute_plan(
        request_dir,
        plan,
        executor_command="executor",
        skip_pr=False,
        skip_auto_merge=False,
    )

    assert calls == ["branch", "commit", "pr", "reconcile:squash:True"]
