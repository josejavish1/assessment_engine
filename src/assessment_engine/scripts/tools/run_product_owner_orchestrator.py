from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from assessment_engine.prompts.product_owner_prompts import (
    build_product_owner_planner_prompt,
    get_product_owner_planner_instruction,
    render_plan_markdown,
    render_task_prompt,
)
from assessment_engine.scripts.lib.ai_client import call_agent
from assessment_engine.scripts.lib.config_loader import (
    load_policy_file,
    resolve_model_profile_for_role,
)
from assessment_engine.scripts.lib.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
)
from assessment_engine.scripts.lib.product_owner_models import ProductOwnerPlan
from assessment_engine.scripts.lib.runtime_paths import ROOT
from assessment_engine.scripts.lib.text_utils import slugify


def load_orchestrator_policy() -> dict[str, Any]:
    return load_policy_file("orchestrator_policy")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--request")
    plan_parser.add_argument("--request-file")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--request")
    run_parser.add_argument("--request-file")
    run_parser.add_argument("--executor-command")
    run_parser.add_argument("--allow-dirty", action="store_true")
    run_parser.add_argument("--skip-pr", action="store_true")
    run_parser.add_argument("--skip-auto-merge", action="store_true")

    return parser.parse_args(argv)


def resolve_requests_root(policy: dict[str, Any]) -> Path:
    relative = policy.get("paths", {}).get(
        "requests_root", "working/product_owner_requests"
    )
    return ROOT / relative


def load_request_text(args: argparse.Namespace) -> str:
    if args.request and args.request.strip():
        return args.request.strip()
    if args.request_file:
        return Path(args.request_file).read_text(encoding="utf-8").strip()
    raise ValueError("Debes indicar --request o --request-file.")


def create_request_dir(policy: dict[str, Any], request_text: str) -> Path:
    requests_root = resolve_requests_root(policy)
    requests_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    request_slug = slugify(request_text)[:48]
    request_dir = requests_root / f"{timestamp}_{request_slug}"
    request_dir.mkdir(parents=True, exist_ok=False)
    return request_dir


def ensure_clean_worktree(*, allow_dirty: bool) -> None:
    if allow_dirty:
        return
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "No se pudo inspeccionar git status."
        )
    if result.stdout.strip():
        raise RuntimeError(
            "El worktree no está limpio. Usa --allow-dirty solo si entiendes el riesgo."
        )


async def generate_plan(request_text: str, policy: dict[str, Any]) -> dict[str, Any]:
    max_tasks = int(policy.get("planning", {}).get("max_tasks", 5))
    model_profile = resolve_model_profile_for_role("product_owner_planner")
    result = await call_agent(
        model_name=model_profile["model"],
        prompt=build_product_owner_planner_prompt(request_text),
        instruction=get_product_owner_planner_instruction(max_tasks),
        output_schema=ProductOwnerPlan,
    )
    return ProductOwnerPlan.model_validate(result).model_dump(mode="json")


def save_plan_bundle(
    request_dir: Path, request_text: str, plan: dict[str, Any]
) -> None:
    (request_dir / "request.txt").write_text(request_text + "\n", encoding="utf-8")
    (request_dir / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (request_dir / "plan.md").write_text(render_plan_markdown(plan), encoding="utf-8")


def run_git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or f"Fallo ejecutando: {' '.join(args)}"
        )
    return result


def ensure_branch(branch_name: str) -> None:
    run_git_command(["git", "checkout", "-b", branch_name])


def resolve_executor_command(raw_command: str | None) -> str:
    command = (
        raw_command
        or os.environ.get("ASSESSMENT_ORCHESTRATOR_EXECUTOR_CMD", "").strip()
    )
    if not command:
        raise RuntimeError(
            "No hay executor configurado. Usa --executor-command o ASSESSMENT_ORCHESTRATOR_EXECUTOR_CMD."
        )
    return command


def build_executor_args(
    template: str, *, task_prompt_file: Path, attempt: int
) -> list[str]:
    formatted = template.format(
        repo_root=str(ROOT),
        task_prompt_file=str(task_prompt_file),
        attempt=str(attempt),
    )
    return shlex.split(formatted)


def collect_changed_python_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo inspeccionar git diff.")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def run_command(command: list[str], *, output_path: Path) -> None:
    env = build_runtime_env()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    output_path.write_text(output, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(output.strip() or f"Fallo ejecutando {' '.join(command)}")


def run_standard_validations(request_dir: Path) -> None:
    policy = load_orchestrator_policy()
    python_bin = resolve_python_bin()
    validation_commands = [
        [python_bin if token == "python" else token for token in entry["command"]]
        for entry in policy.get("validation_commands", [])
    ]

    changed_python_files = collect_changed_python_files()
    quality_command = [
        python_bin,
        "src/assessment_engine/scripts/tools/run_incremental_quality_gate.py",
        "--repo-root",
        ".",
    ]
    typing_command = [
        python_bin,
        "src/assessment_engine/scripts/tools/run_incremental_typecheck.py",
        "--repo-root",
        ".",
    ]
    for path in changed_python_files:
        quality_command.extend(["--path", path])
        typing_command.extend(["--path", path])

    validation_commands.extend([quality_command, typing_command])

    for index, command in enumerate(validation_commands, start=1):
        run_command(command, output_path=request_dir / f"validation_{index}.log")


def create_commit(commit_title: str) -> None:
    run_git_command(["git", "add", "-A"])
    message = (
        f"{commit_title}\n\n"
        "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
    )
    run_git_command(["git", "commit", "-m", message])


def create_pr_body(plan: dict[str, Any]) -> str:
    sections = [
        "## Summary",
        f"- {plan['problem']}",
        f"- {plan['value_expected']}",
        "",
        "## Change spec",
        f"- Problem: {plan['problem']}",
        f"- In scope: {', '.join(plan.get('in_scope', []))}",
        f"- Out of scope: {', '.join(plan.get('out_of_scope', []))}",
        f"- Source of truth: {', '.join(plan.get('source_of_truth', []))}",
        f"- Invariants to preserve: {', '.join(plan.get('invariants', []))}",
        f"- Validation plan: {', '.join(plan.get('validation_plan', []))}",
        "",
        "## Tasks",
    ]
    sections.extend(
        [f"- [{task['id']}] {task['title']}" for task in plan.get("tasks", [])]
    )
    sections.append("")
    sections.append("## Governance checks")
    sections.append("- [x] Planned from a minimal explicit spec")
    sections.append("- [x] Scoped as bounded iterative tasks")
    sections.append("- [x] Validation and canonical documentation considered")
    return "\n".join(sections) + "\n"


def create_pr(
    plan: dict[str, Any], request_dir: Path, *, skip_auto_merge: bool
) -> None:
    policy = load_orchestrator_policy()
    pr_body_path = request_dir / "pr_body.md"
    pr_body_path.write_text(create_pr_body(plan), encoding="utf-8")
    base_branch = policy.get("pull_request", {}).get("base_branch", "main")

    run_git_command(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            plan["branch_name"],
            "--title",
            plan["pr_title"],
            "--body-file",
            str(pr_body_path),
        ]
    )

    if skip_auto_merge or not policy.get("pull_request", {}).get(
        "auto_merge_enabled", True
    ):
        return

    merge_mode = policy.get("pull_request", {}).get("auto_merge_mode", "squash")
    run_git_command(
        ["gh", "pr", "merge", "--auto", f"--{merge_mode}", "--delete-branch"]
    )


def execute_plan(
    request_dir: Path,
    plan: dict[str, Any],
    *,
    executor_command: str,
    skip_pr: bool,
    skip_auto_merge: bool,
) -> None:
    policy = load_orchestrator_policy()
    max_attempts = int(policy.get("execution", {}).get("max_attempts_per_task", 3))

    ensure_branch(plan["branch_name"])

    for task in plan.get("tasks", []):
        feedback: str | None = None
        for attempt in range(1, max_attempts + 1):
            task_prompt = render_task_prompt(
                plan, task, attempt=attempt, validation_feedback=feedback
            )
            task_prompt_path = request_dir / f"{task['id']}_attempt_{attempt}.md"
            task_prompt_path.write_text(task_prompt, encoding="utf-8")

            executor_args = build_executor_args(
                executor_command,
                task_prompt_file=task_prompt_path,
                attempt=attempt,
            )
            try:
                run_command(
                    executor_args,
                    output_path=request_dir / f"{task['id']}_executor_{attempt}.log",
                )
                run_standard_validations(request_dir)
                break
            except Exception as exc:
                feedback = str(exc)
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"La tarea {task['id']} agotó sus reintentos: {exc}"
                    ) from exc
        else:
            raise RuntimeError(f"No se pudo completar la tarea {task['id']}.")

    create_commit(plan["commit_title"])
    if not skip_pr:
        create_pr(plan, request_dir, skip_auto_merge=skip_auto_merge)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    policy = load_orchestrator_policy()
    request_text = load_request_text(args)
    request_dir = create_request_dir(policy, request_text)

    plan = asyncio.run(generate_plan(request_text, policy))
    save_plan_bundle(request_dir, request_text, plan)

    if args.command == "plan":
        print(f"Plan generado en {request_dir}")
        return 0

    ensure_clean_worktree(allow_dirty=args.allow_dirty)
    executor_command = resolve_executor_command(args.executor_command)
    execute_plan(
        request_dir,
        plan,
        executor_command=executor_command,
        skip_pr=args.skip_pr,
        skip_auto_merge=args.skip_auto_merge,
    )
    print(f"Orquestación completada en {request_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
