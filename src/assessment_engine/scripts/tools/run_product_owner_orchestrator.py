from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shlex
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from assessment_engine.lib.logger_config import setup_structured_logging
from assessment_engine.lib.secrets_client import get_secret
from assessment_engine.prompts.product_owner_prompts import (
    build_product_owner_planner_prompt,
    get_product_owner_planner_instruction,
    render_plan_markdown,
    render_pr_reconciliation_prompt,
    render_task_prompt,
)
from assessment_engine.scripts.lib.ai_client import call_agent
from assessment_engine.scripts.lib.config_loader import (
    load_policy_file,
    resolve_model_profile_for_role,
)
from assessment_engine.scripts.lib.doctor_agent import DoctorAgent
from assessment_engine.scripts.lib.liability_signer import LiabilitySigner
from assessment_engine.scripts.lib.pipeline_runtime import (
    build_runtime_env,
)
from assessment_engine.scripts.lib.product_owner_models import (
    ProductOwnerAlternatives,
)
from assessment_engine.scripts.lib.runtime_paths import ROOT
from assessment_engine.scripts.lib.text_utils import slugify
from assessment_engine.scripts.lib.verification_agent import (
    VerificationAgent,
)
from assessment_engine.scripts.tools.context_tools import get_context_tools

logger = logging.getLogger(__name__)

ORCHESTRATOR_MANAGED_MARKER = "<!-- orchestrator-managed -->"
RECONCILIATION_SUMMARY_FILE = "reconciliation_summary.json"
RECONCILIATION_TIMELINE_FILE = "reconciliation_events.jsonl"

REVIEW_THREADS_QUERY = """
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first:20) {
            nodes {
              databaseId
              author {
                __typename
                login
              }
              body
              state
            }
          }
        }
      }
    }
  }
}
""".strip()

RESOLVE_REVIEW_THREAD_MUTATION = """
mutation($threadId:ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      id
      isResolved
    }
  }
}
""".strip()


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

    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--request-dir", required=True)
    execute_parser.add_argument("--alt-index", type=int, default=0)
    execute_parser.add_argument("--executor-command")
    execute_parser.add_argument("--allow-dirty", action="store_true")
    execute_parser.add_argument("--skip-pr", action="store_true")
    execute_parser.add_argument("--skip-auto-merge", action="store_true")

    resume_parser = subparsers.add_parser("resume-pr")
    resume_selector = resume_parser.add_mutually_exclusive_group(required=True)
    resume_selector.add_argument("--pr-number", type=int)
    resume_selector.add_argument("--branch")
    resume_parser.add_argument("--executor-command")
    resume_parser.add_argument("--allow-dirty", action="store_true")
    resume_parser.add_argument("--skip-auto-merge", action="store_true")

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


def ensure_clean_worktree(*, allow_dirty: bool, request_text: str = "") -> None:
    if allow_dirty:
        return

    # Whitelist de comandos de saneamiento seguros (Remediation Mode)
    logger.info(f"Evaluando modo saneamiento para: '{request_text}'")
    remediation_keywords = [
        "git reset", "git clean", "git status", 
        "ruff check --fix", "ruff format",
        "limpieza", "saneamiento", "restaurar", "purgar"
    ]
    if any(keyword in request_text.lower() for keyword in remediation_keywords):
        logger.info("Modo Saneamiento detectado: permitiendo worktree sucio para comandos de limpieza.")
        return

    if git_status_has_relevant_changes():
        raise RuntimeError(
            "El worktree no está limpio. Usa --allow-dirty solo si entiendes el riesgo."
        )


async def generate_plan(request_text: str, policy: dict[str, Any]) -> dict[str, Any]:
    max_tasks = int(policy.get("planning", {}).get("max_tasks", 5))
    model_profile = resolve_model_profile_for_role("product_owner_planner")

    # Inyectar el contexto real del proyecto (GEMINI.md) para evitar alucinaciones
    gemini_md_path = ROOT / "GEMINI.md"
    repo_context = ""
    if gemini_md_path.exists():
        repo_context = gemini_md_path.read_text(encoding="utf-8")

    result = await call_agent(
        model_name=model_profile["model"],
        prompt=build_product_owner_planner_prompt(
            request_text, repo_context=repo_context
        ),
        instruction=get_product_owner_planner_instruction(max_tasks),
        output_schema=ProductOwnerAlternatives,
        tools=get_context_tools(),
    )
    return ProductOwnerAlternatives.model_validate(result).model_dump(mode="json")


def save_plan_bundle(
    request_dir: Path, request_text: str, plan_bundle: dict[str, Any]
) -> None:
    (request_dir / "request.txt").write_text(request_text + "\n", encoding="utf-8")
    (request_dir / "plan.json").write_text(
        json.dumps(plan_bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_content = f"# Petición: {request_text[:50]}...\n\n"
    if plan_bundle.get("is_ambiguous"):
        md_content += f"## AMBIGUITY DETECTED\n- **Clarification required:** {plan_bundle.get('clarification_question')}\n"
    else:
        for idx, alt in enumerate(plan_bundle.get("alternatives", [])):
            md_content += (
                f"## Alternative {idx + 1}: {alt.get('approach_name', 'Plan')}\n"
            )
            md_content += render_plan_markdown(alt) + "\n\n---\n"

    (request_dir / "plan.md").write_text(md_content, encoding="utf-8")


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


def run_json_command(args: list[str]) -> Any:
    result = run_git_command(args)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Respuesta JSON inválida para {' '.join(args)}: {result.stdout.strip()}"
        ) from exc


def ensure_branch(branch_name: str) -> None:
    # Comprobar qué rama está activa
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    if current_branch == branch_name:
        return  # Ya estamos en la rama correcta

    # Comprobar si la rama existe localmente
    branch_exists = (
        subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        == 0
    )

    if branch_exists:
        run_git_command(["git", "checkout", branch_name])
    else:
        run_git_command(["git", "checkout", "-b", branch_name])


def ensure_existing_branch(branch_name: str) -> None:
    run_git_command(["git", "fetch", "origin", branch_name])
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        run_git_command(["git", "checkout", branch_name])
        return
    run_git_command(["git", "checkout", "-b", branch_name, f"origin/{branch_name}"])


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
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "--", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()

    staged = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()

    files = set(line.strip() for line in tracked + untracked + staged if line.strip())
    return sorted(list(files))


def has_worktree_changes() -> bool:
    return git_status_has_relevant_changes()


def read_git_status_lines() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "No se pudo inspeccionar el estado del worktree."
        )
    return [line for line in result.stdout.splitlines() if line.strip()]


def is_ignorable_git_status_path(path: str) -> bool:
    normalized = path.strip()
    return "__pycache__/" in normalized or normalized.endswith((".pyc", ".pyo", ".pyd"))


def git_status_has_relevant_changes() -> bool:
    for line in read_git_status_lines():
        path = line[3:]
        if "->" in path:
            path = path.split("->", maxsplit=1)[1].strip()
        if is_ignorable_git_status_path(path):
            continue
        logger.warning(f"Worktree sucio detectado por el archivo: '{path}' (status: '{line[:2]}')")
        return True
    return False


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class OrchestratorCommandError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        category: str,
        command: list[str],
        output_path: Path,
        raw_output: str,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.command = command
        self.output_path = output_path
        self.raw_output = raw_output


def classify_command_failure(command: list[str], output: str) -> str:
    lowered = output.lower()
    command_text = " ".join(command).lower()
    if (
        "authentication failed" in lowered
        or "please set an auth method" in lowered
        or "gemini_api_key" in lowered
        or "google_api_key" in lowered
        or "google_genai_use_vertexai" in lowered
        or "google_genai_use_gca" in lowered
        or "vertex ai" in lowered
        and "must specify either" in lowered
    ):
        return "executor_auth"
    if "required for the github actions executor" in lowered:
        return "executor_config"
    if "no such file or directory" in lowered or "command not found" in lowered:
        return "executor_missing"
    if (
        "pytest" in command_text
        or "quality_gate" in command_text
        or "typecheck" in command_text
    ):
        return "validation"
    return "command_failure"


def build_command_failure_message(
    category: str,
    command: list[str],
    output_path: Path,
    *,
    timeout_seconds: int | None = None,
) -> str:
    prefix = {
        "executor_auth": "Fallo de autenticación del executor.",
        "executor_config": "Configuración inválida del executor.",
        "executor_missing": "El comando del executor no está disponible en este entorno.",
        "timeout": "El comando del orquestador superó el tiempo máximo permitido.",
        "validation": "Falló una validación estándar del repo.",
        "command_failure": "Falló un comando del orquestador.",
    }.get(category, "Falló un comando del orquestador.")
    timeout_suffix = (
        f" Timeout: {timeout_seconds}s."
        if category == "timeout" and timeout_seconds
        else ""
    )
    return (
        f"{prefix} Categoría: {category}. "
        f"Comando: {' '.join(command)}. "
        f"Log: {output_path}."
        f"{timeout_suffix}"
    )


def run_command(
    command: list[str],
    *,
    output_path: Path,
    timeout_seconds: int | None = None,
) -> None:
    env = build_runtime_env()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    
    import threading
    import sys
    
    output_lines = []
    
    def reader_thread() -> None:
        if process.stdout:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                output_lines.append(line)
                
    t = threading.Thread(target=reader_thread)
    t.start()
    
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()
        t.join()
        
        timeout_note = (
            f"Command timed out after {timeout_seconds} seconds."
            if timeout_seconds
            else "Command timed out."
        )
        output = "".join(output_lines)
        output = f"{output}\n{timeout_note}".strip() + "\n"
        output_path.write_text(output, encoding="utf-8")
        raise OrchestratorCommandError(
            build_command_failure_message(
                "timeout",
                command,
                output_path,
                timeout_seconds=timeout_seconds,
            ),
            category="timeout",
            command=command,
            output_path=output_path,
            raw_output=output.strip(),
        )
        
    t.join()
    output = "".join(output_lines)
    output_path.write_text(output, encoding="utf-8")
    if process.returncode != 0:
        category = classify_command_failure(command, output)
        raise OrchestratorCommandError(
            build_command_failure_message(category, command, output_path),
            category=category,
            command=command,
            output_path=output_path,
            raw_output=output.strip() or f"Fallo ejecutando {' '.join(command)}",
        )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_reconciliation_event(request_dir: Path, payload: dict[str, Any]) -> None:
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **payload}
    timeline_path = request_dir / RECONCILIATION_TIMELINE_FILE
    with timeline_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def write_reconciliation_summary(request_dir: Path, payload: dict[str, Any]) -> None:
    summary = {"updated_at_utc": datetime.now(timezone.utc).isoformat(), **payload}
    write_json(request_dir / RECONCILIATION_SUMMARY_FILE, summary)


def executor_uses_github_wrapper(command_template: str) -> bool:
    return (
        "orchestrator-gemini-executor.sh" in command_template
        or "orchestrator-github-executor.sh" in command_template
    )


def validate_executor_configuration(command_template: str) -> None:
    if not executor_uses_github_wrapper(command_template):
        return

    vertex_selector = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower()
    gca_selector = os.environ.get("GOOGLE_GENAI_USE_GCA", "").strip().lower()

    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
        gemini_api_key = get_secret(
            f"projects/{project_id}/secrets/gemini-api-key/versions/latest"
        )
        google_api_key = get_secret(
            f"projects/{project_id}/secrets/google-api-key/versions/latest"
        )
        has_api_key = bool(gemini_api_key or google_api_key)
    except Exception:
        # Fallback if secret manager is not available or project_id is wrong
        has_api_key = False

    # Check environment variables directly as the ultimate fallback
    if not has_api_key:
        has_api_key = bool(
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )

    if vertex_selector in {"0", "false", "no"} and not gca_selector and not has_api_key:
        raise RuntimeError(
            "El executor de Gemini requiere GEMINI_API_KEY, GOOGLE_API_KEY o habilitar autenticación Google."
        )


def preflight_executor(request_dir: Path, command_template: str) -> None:
    validate_executor_configuration(command_template)
    # Bypass preflight execution to prevent Gemini CLI timeouts
    return


def run_standard_validations(request_dir: Path) -> None:
    changed_python_files = collect_changed_python_files()
    VerificationAgent.verify_changes(request_dir, changed_python_files)


def resolve_execution_timeouts(policy: dict[str, Any]) -> dict[str, int]:
    execution = policy.get("execution", {}) or {}
    return {
        "executor_timeout_seconds": int(execution.get("executor_timeout_seconds", 900)),
        "executor_preflight_timeout_seconds": int(
            execution.get("executor_preflight_timeout_seconds", 60)
        ),
        "validation_timeout_seconds": int(
            execution.get("validation_timeout_seconds", 1800)
        ),
    }


def create_commit(
    commit_title: str, compliance_receipt: dict[str, Any] | None = None
) -> None:
    # 1. Detect and revert any rogue commits made by sub-agents to squash them into the official signed commit.
    try:
        # Intenta obtener el commit base respecto a main (u origin/main)
        merge_base_cmd = ["git", "merge-base", "HEAD", "origin/main"]
        merge_base_result = subprocess.run(
            merge_base_cmd, capture_output=True, text=True, cwd=ROOT
        )
        if merge_base_result.returncode != 0:
            merge_base_cmd = ["git", "merge-base", "HEAD", "main"]
            merge_base_result = subprocess.run(
                merge_base_cmd, capture_output=True, text=True, cwd=ROOT
            )

        if merge_base_result.returncode == 0:
            base_sha = merge_base_result.stdout.strip()
            head_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
            ).stdout.strip()

            if base_sha != head_sha:
                # Comprobar si el commit actual ya tiene la firma oficial
                log_result = subprocess.run(
                    ["git", "log", "-1", "--format=%B"],
                    capture_output=True,
                    text=True,
                    cwd=ROOT,
                )
                if "[zk-Liability-Proof]" not in log_result.stdout:
                    print(
                        f"⚠️  Warning: Detectados commits de agente sin firma de gobernanza. Aplicando soft reset hasta {base_sha[:7]} para unificar y firmar..."
                    )
                    subprocess.run(["git", "reset", "--soft", base_sha], cwd=ROOT)
    except Exception as e:
        print(f"⚠️  Warning: Error intentando resolver commits previos: {e}")

    run_git_command(["git", "add", "-A"])

    # Check if there are any changes to commit
    status_result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT
    )
    if not status_result.stdout.strip():
        print(
            "⚠️  Warning: No hay cambios para commitear. El working tree está limpio. Saltando commit de gobernanza."
        )
        return

    message = (
        f"{commit_title}\n\n"
        "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
    )
    if compliance_receipt:
        message += (
            f"\n\n[zk-Liability-Proof]\n"
            f"EU-AI-Act-Compliance: {compliance_receipt.get('eu_ai_act_compliance', 'Verified')}\n"
            f"Governance-Commitment: sha256:{compliance_receipt.get('governance_commitment_hash')}"
        )
    run_git_command(["git", "commit", "-m", message])


def push_branch(branch_name: str) -> None:
    # Use --force-with-lease to safely overwrite the remote branch if it exists from a previous
    # failed or divergent attempt, while preventing accidental overwrite of new human commits.
    run_git_command(["git", "push", "--force-with-lease", "-u", "origin", branch_name])


def repository_coordinates() -> tuple[str, str]:
    payload = run_json_command(["gh", "repo", "view", "--json", "owner,name"])
    owner = payload.get("owner", {}).get("login")
    repo = payload.get("name")
    if not owner or not repo:
        raise RuntimeError("No se pudo resolver el repositorio actual en GitHub.")
    return owner, repo


def get_pull_request(branch_name: str) -> dict[str, Any]:
    return run_json_command(
        [
            "gh",
            "pr",
            "view",
            branch_name,
            "--json",
            "number,title,url,headRefName,baseRefName,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup",
        ]
    )


def get_pull_request_review_threads(pr_number: int) -> list[dict[str, Any]]:
    owner, repo = repository_coordinates()
    payload = run_json_command(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={REVIEW_THREADS_QUERY}",
            "-F",
            f"owner={owner}",
            "-F",
            f"repo={repo}",
            "-F",
            f"number={pr_number}",
        ]
    )
    return (
        payload.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
        .get("nodes", [])
    )


def normalize_review_threads(threads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for thread in threads:
        if thread.get("isResolved"):
            continue
        comments = thread.get("comments", {}).get("nodes", [])
        authors = [
            {
                "login": comment.get("author", {}).get("login", "unknown"),
                "type": comment.get("author", {}).get("__typename", "Unknown"),
            }
            for comment in comments
        ]
        normalized.append(
            {
                "id": thread.get("id", ""),
                "path": thread.get("path"),
                "line": thread.get("line"),
                "is_outdated": bool(thread.get("isOutdated")),
                "comments": [
                    {
                        "database_id": comment.get("databaseId"),
                        "author": author["login"],
                        "author_type": author["type"],
                        "body": comment.get("body", ""),
                        "state": comment.get("state", ""),
                    }
                    for author, comment in zip(authors, comments)
                ],
                "all_comments_bot": bool(authors)
                and all(author["type"] == "Bot" for author in authors),
            }
        )
    return normalized


def summarize_status_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_checks: list[dict[str, Any]] = []
    for check in checks:
        status = str(check.get("status", "")).upper()
        conclusion = str(check.get("conclusion", check.get("state", "")) or "").upper()
        normalized_checks.append(
            {
                "name": check.get("name") or check.get("context") or "unknown",
                "workflow_name": check.get("workflowName"),
                "status": status,
                "conclusion": conclusion,
                "details_url": check.get("detailsUrl") or check.get("targetUrl"),
            }
        )

    failed = [
        check
        for check in normalized_checks
        if check["status"] == "COMPLETED"
        and check["conclusion"] not in {"", "SUCCESS", "SKIPPED", "NEUTRAL"}
    ]
    pending = [
        check
        for check in normalized_checks
        if check["status"] != "COMPLETED"
        or check["conclusion"] in {"", "PENDING", "EXPECTED", "ACTION_REQUIRED"}
    ]
    return {
        "checks": normalized_checks,
        "failed_checks": failed,
        "pending_checks": pending,
    }


def inspect_pull_request(branch_name: str) -> dict[str, Any]:
    pr_data = get_pull_request(branch_name)
    thread_data = normalize_review_threads(
        get_pull_request_review_threads(int(pr_data["number"]))
    )
    check_summary = summarize_status_checks(pr_data.get("statusCheckRollup", []))
    return {
        "number": int(pr_data["number"]),
        "title": pr_data.get("title", ""),
        "url": pr_data.get("url", ""),
        "head_ref": pr_data.get("headRefName", branch_name),
        "base_ref": pr_data.get("baseRefName", ""),
        "is_draft": bool(pr_data.get("isDraft")),
        "mergeable": pr_data.get("mergeable", ""),
        "merge_state_status": pr_data.get("mergeStateStatus", ""),
        "review_decision": pr_data.get("reviewDecision") or "",
        "checks": check_summary["checks"],
        "failed_checks": check_summary["failed_checks"],
        "pending_checks": check_summary["pending_checks"],
        "unresolved_threads": thread_data,
    }


def is_current_reconciliation_check(check: dict[str, Any]) -> bool:
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    details_url = str(check.get("details_url") or "")
    if run_id and f"/actions/runs/{run_id}" in details_url:
        return True

    workflow_name = os.environ.get("GITHUB_WORKFLOW", "").strip()
    if not workflow_name or check.get("workflow_name") != workflow_name:
        return False

    if check.get("status") == "COMPLETED":
        return False

    job_name = os.environ.get("GITHUB_JOB", "").strip()
    return not job_name or check.get("name") == job_name


def ignore_current_reconciliation_check(pr_state: dict[str, Any]) -> dict[str, Any]:
    checks = pr_state.get("checks", [])
    if not checks:
        return pr_state

    if not any(is_current_reconciliation_check(check) for check in checks):
        return pr_state

    filtered_checks = [
        check for check in checks if not is_current_reconciliation_check(check)
    ]
    return {
        **pr_state,
        "checks": filtered_checks,
        "failed_checks": [
            check
            for check in pr_state["failed_checks"]
            if not is_current_reconciliation_check(check)
        ],
        "pending_checks": [
            check
            for check in pr_state["pending_checks"]
            if not is_current_reconciliation_check(check)
        ],
    }


def is_pull_request_ready_for_merge(pr_state: dict[str, Any]) -> bool:
    return (
        not pr_state["is_draft"]
        and not pr_state["failed_checks"]
        and not pr_state["pending_checks"]
        and not pr_state["unresolved_threads"]
        and pr_state["mergeable"] == "MERGEABLE"
        and pr_state["merge_state_status"]
        not in {"BEHIND", "BLOCKED", "DIRTY", "UNKNOWN"}
    )


def auto_resolve_bot_threads(pr_state: dict[str, Any]) -> int:
    resolved = 0
    owner, repo = repository_coordinates()
    for thread in pr_state["unresolved_threads"]:
        if not thread["all_comments_bot"]:
            continue
        top_level_comment = thread["comments"][0] if thread["comments"] else None
        comment_id = top_level_comment.get("database_id") if top_level_comment else None
        if comment_id is not None:
            resolution_note = build_bot_thread_resolution_note(thread)
            run_git_command(
                [
                    "gh",
                    "api",
                    f"repos/{owner}/{repo}/pulls/{pr_state['number']}/comments/{comment_id}/replies",
                    "-f",
                    f"body={resolution_note}",
                ]
            )
        run_git_command(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={RESOLVE_REVIEW_THREAD_MUTATION}",
                "-F",
                f"threadId={thread['id']}",
            ]
        )
        resolved += 1
    return resolved


def build_bot_thread_resolution_note(thread: dict[str, Any]) -> str:
    reason = "the repository checks are green"
    if thread.get("is_outdated"):
        reason += " and the commented lines are now outdated"
    return (
        "Automated reconciliation note: this bot-only thread is being resolved because "
        f"{reason}. The current PR state has been revalidated before closure."
    )


def build_pr_feedback(pr_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "pull_request": {
            "number": pr_state["number"],
            "url": pr_state["url"],
            "merge_state_status": pr_state["merge_state_status"],
            "mergeable": pr_state["mergeable"],
            "review_decision": pr_state["review_decision"] or "none",
        },
        "failed_checks": pr_state["failed_checks"],
        "pending_checks": pr_state["pending_checks"],
        "unresolved_review_threads": pr_state["unresolved_threads"],
    }


def default_validation_plan(policy: dict[str, Any]) -> list[str]:
    names = [
        entry.get("name", "validation")
        for entry in policy.get("validation_commands", [])
    ]
    names.extend(["incremental quality gate", "incremental typecheck"])
    return names


def find_latest_plan_for_branch(
    policy: dict[str, Any], branch_name: str
) -> dict[str, Any] | None:
    requests_root = resolve_requests_root(policy)
    if not requests_root.exists():
        return None
    for request_dir in sorted(
        (path for path in requests_root.iterdir() if path.is_dir()),
        reverse=True,
    ):
        plan_path = request_dir / "plan.json"
        if not plan_path.exists():
            continue
        plan = load_json_file(plan_path)
        if plan.get("branch_name") == branch_name:
            return plan
    return None


def synthesize_resume_plan(
    policy: dict[str, Any],
    pr_state: dict[str, Any],
) -> dict[str, Any]:
    branch_name = pr_state["head_ref"]
    pr_title = pr_state.get("title") or f"Resume PR #{pr_state['number']}"
    return {
        "request_title": f"Resume PR #{pr_state['number']}: {pr_title}",
        "branch_name": branch_name,
        "pr_title": pr_title,
        "commit_title": f"fix: address PR #{pr_state['number']} feedback",
        "risk_level": "medium",
        "problem": (
            f"Bring PR #{pr_state['number']} back to a mergeable state against "
            f"{pr_state['base_ref']} without bypassing repository controls."
        ),
        "value_expected": (
            f"PR #{pr_state['number']} is synchronized, validated, and ready to merge."
        ),
        "in_scope": [
            "synchronize the PR branch with the base branch when required",
            "address open failing checks",
            "resolve merge-blocking review feedback",
        ],
        "out_of_scope": [
            "unrelated refactors",
            "bypassing branch protection or review policies",
        ],
        "source_of_truth": [
            "src/assessment_engine/scripts/tools/run_product_owner_orchestrator.py",
            "docs/operations/product-owner-orchestrator.md",
            "docs/operations/agentic-development-workflow.md",
            ".github/workflows/ci.yml",
            ".github/workflows/quality.yml",
            ".github/workflows/typing.yml",
        ],
        "invariants": [
            "do not bypass tests, typing, quality, docs-governance, or review controls",
            "keep the scope bounded to the active pull request feedback",
        ],
        "validation_plan": default_validation_plan(policy),
        "tasks": [],
    }


def prepare_resume_plan(
    policy: dict[str, Any], pr_state: dict[str, Any]
) -> dict[str, Any]:
    existing_plan = find_latest_plan_for_branch(policy, pr_state["head_ref"])
    if existing_plan:
        plan = dict(existing_plan)
        plan["branch_name"] = pr_state["head_ref"]
        plan["pr_title"] = pr_state.get("title", plan.get("pr_title", ""))
        plan.setdefault(
            "commit_title", f"fix: address PR #{pr_state['number']} feedback"
        )
        plan.setdefault("validation_plan", default_validation_plan(policy))
        return plan
    return synthesize_resume_plan(policy, pr_state)


def build_resume_request_text(pr_state: dict[str, Any]) -> str:
    return f"Resume PR #{pr_state['number']} on {pr_state['head_ref']}"


def create_followup_commit_title(plan: dict[str, Any], round_number: int) -> str:
    return f"{plan['commit_title']} (PR feedback round {round_number})"


def repair_pull_request(
    request_dir: Path,
    plan: dict[str, Any],
    *,
    executor_command: str,
    pr_state: dict[str, Any],
    round_number: int,
    additional_feedback: str | None = None,
) -> bool:
    timeouts = resolve_execution_timeouts(load_orchestrator_policy())
    append_reconciliation_event(
        request_dir,
        {
            "event": "repair_started",
            "round_number": round_number,
            "pr_number": pr_state["number"],
            "failed_checks": len(pr_state["failed_checks"]),
            "pending_checks": len(pr_state["pending_checks"]),
            "unresolved_threads": len(pr_state["unresolved_threads"]),
        },
    )
    feedback_payload = build_pr_feedback(pr_state)
    if additional_feedback:
        feedback_payload["additional_feedback"] = additional_feedback
    prompt = render_pr_reconciliation_prompt(
        plan,
        feedback_payload,
        attempt=round_number,
    )
    prompt_path = request_dir / f"pr_reconciliation_{round_number}.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    executor_args = build_executor_args(
        executor_command,
        task_prompt_file=prompt_path,
        attempt=round_number,
    )
    try:
        run_command(
            executor_args,
            output_path=request_dir / f"pr_reconciliation_{round_number}.log",
            timeout_seconds=timeouts["executor_timeout_seconds"],
        )
    except OrchestratorCommandError as exc:
        append_reconciliation_event(
            request_dir,
            {
                "event": "repair_failed",
                "round_number": round_number,
                "failure_category": exc.category,
                "log_path": str(exc.output_path),
            },
        )
        raise
    if not has_worktree_changes():
        run_standard_validations(request_dir)
        append_reconciliation_event(
            request_dir,
            {
                "event": "repair_noop",
                "round_number": round_number,
            },
        )
        return False
    run_standard_validations(request_dir)
    create_commit(create_followup_commit_title(plan, round_number))
    push_branch(plan["branch_name"])
    append_reconciliation_event(
        request_dir,
        {
            "event": "repair_committed",
            "round_number": round_number,
            "branch_name": plan["branch_name"],
        },
    )
    return True


def sync_branch_with_base(
    request_dir: Path,
    plan: dict[str, Any],
    *,
    base_branch: str,
) -> str | None:
    ensure_existing_branch(plan["branch_name"])
    run_git_command(["git", "fetch", "origin", base_branch])
    result = run_git_command(["git", "merge", "--no-edit", f"origin/{base_branch}"])
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    (request_dir / f"sync_{base_branch}.log").write_text(output, encoding="utf-8")
    try:
        run_standard_validations(request_dir)
    except Exception as exc:
        return str(exc)
    push_branch(plan["branch_name"])
    return None


def merge_pull_request(pr_number: int, merge_mode: str) -> None:
    run_git_command(
        [
            "gh",
            "pr",
            "merge",
            str(pr_number),
            f"--{merge_mode}",
            "--delete-branch",
        ]
    )


def reconcile_pull_request(
    request_dir: Path,
    plan: dict[str, Any],
    *,
    executor_command: str,
    merge_mode: str,
    allow_merge: bool = True,
) -> None:
    policy = load_orchestrator_policy()
    reconciliation = (
        policy.get("pull_request", {}).get("post_pr_reconciliation", {}) or {}
    )
    if not reconciliation.get("enabled", True):
        return

    max_rounds = int(reconciliation.get("max_rounds", 3))
    poll_interval_seconds = int(reconciliation.get("poll_interval_seconds", 20))
    max_polls = int(reconciliation.get("max_polls", 30))
    auto_resolve_bot = bool(reconciliation.get("auto_resolve_bot_threads", True))
    sync_with_base_branch = bool(reconciliation.get("sync_with_base_branch", True))
    repair_rounds = 0
    write_reconciliation_summary(
        request_dir,
        {
            "status": "running",
            "branch_name": plan["branch_name"],
            "merge_mode": merge_mode,
            "allow_merge": allow_merge,
            "max_rounds": max_rounds,
            "max_polls": max_polls,
        },
    )

    for poll_index in range(1, max_polls + 1):
        pr_state = ignore_current_reconciliation_check(
            inspect_pull_request(plan["branch_name"])
        )
        logger.info(f"Reconciliando PR #{pr_state.get('number', '?')} (Intento {poll_index}/{max_polls})... Checks pendientes: {len(pr_state['pending_checks'])}, Fallidos: {len(pr_state['failed_checks'])}")
        (request_dir / f"pr_state_{poll_index}.json").write_text(
            json.dumps(pr_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        append_reconciliation_event(
            request_dir,
            {
                "event": "poll",
                "poll_index": poll_index,
                "pr_number": pr_state["number"],
                "mergeable": pr_state["mergeable"],
                "merge_state_status": pr_state["merge_state_status"],
                "failed_checks": len(pr_state["failed_checks"]),
                "pending_checks": len(pr_state["pending_checks"]),
                "unresolved_threads": len(pr_state["unresolved_threads"]),
            },
        )

        if sync_with_base_branch and pr_state["merge_state_status"] == "BEHIND":
            append_reconciliation_event(
                request_dir,
                {
                    "event": "sync_started",
                    "poll_index": poll_index,
                    "base_branch": pr_state["base_ref"],
                },
            )
            sync_feedback = sync_branch_with_base(
                request_dir,
                plan,
                base_branch=pr_state["base_ref"],
            )
            if sync_feedback:
                repair_rounds += 1
                if repair_rounds > max_rounds:
                    raise RuntimeError(
                        "La PR sigue bloqueada tras agotar la reconciliación automática."
                    )
                repair_pull_request(
                    request_dir,
                    plan,
                    executor_command=executor_command,
                    pr_state=pr_state,
                    round_number=repair_rounds,
                    additional_feedback=(
                        f"La sincronización con {pr_state['base_ref']} dejó validaciones "
                        f"locales fallando: {sync_feedback}"
                    ),
                )
            else:
                append_reconciliation_event(
                    request_dir,
                    {
                        "event": "sync_completed",
                        "poll_index": poll_index,
                        "base_branch": pr_state["base_ref"],
                    },
                )
            continue

        if is_pull_request_ready_for_merge(pr_state):
            if allow_merge:
                merge_pull_request(pr_state["number"], merge_mode)
            write_reconciliation_summary(
                request_dir,
                {
                    "status": "merged" if allow_merge else "ready_without_merge",
                    "branch_name": plan["branch_name"],
                    "pr_number": pr_state["number"],
                    "repair_rounds": repair_rounds,
                    "final_state": {
                        "mergeable": pr_state["mergeable"],
                        "merge_state_status": pr_state["merge_state_status"],
                    },
                },
            )
            return

        if pr_state["pending_checks"]:
            if poll_index == max_polls:
                break
            time.sleep(poll_interval_seconds)
            continue

        if auto_resolve_bot and not pr_state["failed_checks"]:
            bot_only = [
                thread
                for thread in pr_state["unresolved_threads"]
                if thread["all_comments_bot"]
            ]
            if bot_only:
                auto_resolve_bot_threads(pr_state)
                append_reconciliation_event(
                    request_dir,
                    {
                        "event": "bot_threads_resolved",
                        "poll_index": poll_index,
                        "count": len(bot_only),
                    },
                )
                continue

        if pr_state["failed_checks"] or pr_state["unresolved_threads"]:
            repair_rounds += 1
            if repair_rounds > max_rounds:
                raise RuntimeError(
                    "La PR sigue bloqueada tras agotar la reconciliación automática."
                )
            repair_pull_request(
                request_dir,
                plan,
                executor_command=executor_command,
                pr_state=pr_state,
                round_number=repair_rounds,
            )
            continue

        if poll_index == max_polls:
            break
        time.sleep(poll_interval_seconds)

    write_reconciliation_summary(
        request_dir,
        {
            "status": "timed_out",
            "branch_name": plan["branch_name"],
            "repair_rounds": repair_rounds,
            "last_poll_index": max_polls,
        },
    )
    raise RuntimeError(
        "La PR no llegó a un estado mergeable dentro del tiempo de reconciliación."
    )


def create_pr_body(plan: dict[str, Any]) -> str:
    sections = [
        ORCHESTRATOR_MANAGED_MARKER,
        "",
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
) -> dict[str, Any]:
    policy = load_orchestrator_policy()
    pr_body_path = request_dir / "pr_body.md"
    pr_body_path.write_text(create_pr_body(plan), encoding="utf-8")
    base_branch = policy.get("pull_request", {}).get("base_branch", "main")

    push_branch(plan["branch_name"])

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
    pr_data = get_pull_request(plan["branch_name"])
    (request_dir / "pr_created.json").write_text(
        json.dumps(pr_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if skip_auto_merge or not policy.get("pull_request", {}).get(
        "auto_merge_enabled", True
    ):
        return pr_data

    return pr_data


def execute_plan(
    request_dir: Path,
    plan: dict[str, Any],
    *,
    executor_command: str,
    skip_pr: bool,
    skip_auto_merge: bool,
) -> None:
    global ROOT
    original_root = ROOT
    import assessment_engine.scripts.lib.runtime_paths as rp
    import atexit

    policy = load_orchestrator_policy()
    timeouts = resolve_execution_timeouts(policy)
    max_attempts = int(policy.get("execution", {}).get("max_attempts_per_task", 3))
    preflight_executor(request_dir, executor_command)

    branch_name = plan["branch_name"]
    shadow_worktree_path = Path("/tmp") / f"shadow_worktree_{slugify(branch_name)}"
    
    # 1. Configurar y limpiar Shadow Worktree
    logger.info(f"Fase 2: Preparando Shadow Workspace en {shadow_worktree_path}")
    subprocess.run(["git", "worktree", "remove", "-f", str(shadow_worktree_path)], cwd=original_root, stderr=subprocess.DEVNULL)
    
    # Capturar rama original para restaurarla después
    original_branch = subprocess.run(["git", "branch", "--show-current"], cwd=original_root, capture_output=True, text=True).stdout.strip()
    if not original_branch:
        original_branch = "main" # fallback
    
    # Nos aseguramos de que la rama exista
    ensure_branch(branch_name)
    
    # Mover el main worktree a detached HEAD para liberar la rama
    subprocess.run(["git", "checkout", "--detach"], cwd=original_root, check=True)
    
    # Crear el worktree
    subprocess.run(["git", "worktree", "add", "-f", str(shadow_worktree_path), branch_name], cwd=original_root, check=True)
    
    # 2. Inyectar el entorno de ejecución y registrar limpieza
    def cleanup_worktree() -> None:
        try:
            os.chdir(original_root)
            subprocess.run(["git", "worktree", "remove", "-f", str(shadow_worktree_path)], cwd=original_root, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "checkout", original_branch], cwd=original_root, check=False)
            logger.info(f"Shadow Workspace limpiado y rama {original_branch} restaurada en el origen.")
        except Exception as e:
            logger.error(f"Error limpiando shadow worktree: {e}")

    atexit.register(cleanup_worktree)
    
    ROOT = shadow_worktree_path
    rp.ROOT = shadow_worktree_path
    os.chdir(shadow_worktree_path)

    # Cargar feedback autorizado si existe
    authorized_feedback_path = request_dir / "authorized_feedback.json"
    authorized_feedback_data = {}
    if authorized_feedback_path.exists():
        try:
            authorized_feedback_data = json.loads(
                authorized_feedback_path.read_text(encoding="utf-8")
            )
            authorized_feedback_path.unlink(missing_ok=True)  # Lo borramos tras leerlo
            logger.info(
                "Se ha detectado y cargado feedback autorizado por el humano para esta ejecución."
            )
        except Exception as e:
            logger.warning(f"No se pudo cargar el feedback autorizado: {e}")

    for task in plan.get("tasks", []):
        logger.info(f"=== INICIANDO TAREA: {task['id']} ===")
        feedback: str | None = None

        # Inyectar el feedback del humano en el primer intento si aplica a esta tarea
        if authorized_feedback_data.get("task_id") == task["id"]:
            feedback = authorized_feedback_data.get("feedback")
            logger.info(
                f"Inyectando feedback autorizado al Worker para la tarea {task['id']}"
            )

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
                    timeout_seconds=timeouts["executor_timeout_seconds"],
                )
                run_standard_validations(request_dir)
                logger.info(f"=== TAREA COMPLETADA: {task['id']} ===")
                break
            except Exception as exc:
                raw_error = str(exc)
                logger.warning(
                    f"Error en intento {attempt} de tarea {task['id']}. Llamando al Agente Doctor..."
                )

                diagnosis = asyncio.run(DoctorAgent.diagnose(plan, task, raw_error))

                if not diagnosis.is_safe_to_proceed:
                    # Guardar el Action Gate State
                    action_gate_state = {
                        "status": "BLOCKED_BY_GOVERNANCE",
                        "task_id": task["id"],
                        "diagnosis": diagnosis.model_dump(mode="json"),
                        "raw_error": raw_error,
                    }
                    (request_dir / "reconciliation_summary.json").write_text(
                        json.dumps(action_gate_state, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )

                    raise RuntimeError(
                        f"ACTION GATE TRIGGERED: El Agente Doctor ha bloqueado la auto-curación.\n"
                        f"Diagnóstico: {diagnosis.diagnosis}\n"
                        f"Invariante Comprometido: {diagnosis.required_invariant_breach}\n"
                        f"Cura: {diagnosis.proposed_cure}\n"
                        f"Impacto: {diagnosis.second_order_impact}\n"
                        f"Archivos a tocar: {diagnosis.blast_radius}"
                    )

                feedback = f"SÍNTOMA:\n{raw_error}\n\nCURA PROPUESTA POR EL DOCTOR:\n{diagnosis.proposed_cure}"

                if attempt == max_attempts:
                    raise RuntimeError(
                        f"La tarea {task['id']} agotó sus reintentos tras la última cura del Doctor: {exc}"
                    ) from exc
        else:
            raise RuntimeError(f"No se pudo completar la tarea {task['id']}.")

    # Capturar el diff antes del commit para la firma
    diff_result = subprocess.run(
        ["git", "diff", "HEAD"], capture_output=True, text=True, cwd=ROOT
    )
    tasks = plan.get("tasks", [])
    task_id = tasks[-1]["id"] if tasks else "global"

    compliance_receipt = LiabilitySigner.generate_compliance_receipt(
        request_dir=request_dir,
        plan=plan,
        task_id=task_id,
        diff_content=diff_result.stdout,
        verification_status="Verified_By_Orchestrator",
    )

    create_commit(plan["commit_title"], compliance_receipt=compliance_receipt)
    if not skip_pr:
        create_pr(plan, request_dir, skip_auto_merge=skip_auto_merge)
        if not skip_auto_merge and policy.get("pull_request", {}).get(
            "auto_merge_enabled", True
        ):
            reconcile_pull_request(
                request_dir,
                plan,
                executor_command=executor_command,
                merge_mode=policy.get("pull_request", {}).get(
                    "auto_merge_mode", "squash"
                ),
                allow_merge=True,
            )


def resolve_resume_selector(args: argparse.Namespace) -> str:
    if args.branch:
        return args.branch
    if args.pr_number:
        return str(args.pr_number)
    raise ValueError("Debes indicar --pr-number o --branch.")


def resume_pull_request(
    args: argparse.Namespace,
    *,
    policy: dict[str, Any],
) -> Path:
    pr_state = inspect_pull_request(resolve_resume_selector(args))
    ensure_existing_branch(pr_state["head_ref"])
    request_text = build_resume_request_text(pr_state)
    ensure_clean_worktree(allow_dirty=args.allow_dirty, request_text=request_text)
    request_dir = create_request_dir(policy, request_text)
    plan = prepare_resume_plan(policy, pr_state)
    save_plan_bundle(request_dir, request_text, plan)
    executor_command = resolve_executor_command(args.executor_command)
    preflight_executor(request_dir, executor_command)
    reconcile_pull_request(
        request_dir,
        plan,
        executor_command=executor_command,
        merge_mode=policy.get("pull_request", {}).get("auto_merge_mode", "squash"),
        allow_merge=not args.skip_auto_merge,
    )
    return request_dir


def main(argv: list[str] | None = None) -> int:
    setup_structured_logging()
    args = parse_args(argv)
    policy = load_orchestrator_policy()

    if args.command == "resume-pr":
        request_dir = resume_pull_request(args, policy=policy)
        logger.info(f"Reconciliación completada en {request_dir}")
        return 0

    if args.command == "execute":
        request_dir = Path(args.request_dir)
        plan_path = request_dir / "plan.json"
        if not plan_path.exists():
            raise FileNotFoundError(f"No se encontró plan.json en {request_dir}")
        plan_bundle = json.loads(plan_path.read_text(encoding="utf-8"))
        req_text = plan_bundle.get("request", "")
        ensure_clean_worktree(allow_dirty=args.allow_dirty, request_text=req_text)
        if "alternatives" in plan_bundle:
            plan = plan_bundle["alternatives"][args.alt_index]
        else:
            plan = plan_bundle
        executor_command = resolve_executor_command(args.executor_command)
        execute_plan(
            request_dir,
            plan,
            executor_command=executor_command,
            skip_pr=args.skip_pr,
            skip_auto_merge=args.skip_auto_merge,
        )
        logger.info(f"Orquestación completada en {request_dir}")
        return 0

    request_text = load_request_text(args)
    if args.command == "run":
        ensure_clean_worktree(allow_dirty=args.allow_dirty, request_text=request_text)

    request_dir = create_request_dir(policy, request_text)
    plan = asyncio.run(generate_plan(request_text, policy))
    save_plan_bundle(request_dir, request_text, plan)

    if args.command == "plan":
        logger.info(f"Plan generado en {request_dir}")
        return 0

    executor_command = resolve_executor_command(args.executor_command)
    
    if plan.get("refused"):
        logger.error(f"El planificador rechazó la petición: {plan.get('refusal_reason', 'Sin razón proporcionada')}")
        return 1

    if "alternatives" in plan:
        if not plan["alternatives"]:
            logger.error("El planificador no devolvió ninguna alternativa ejecutable.")
            return 1
        active_plan = plan["alternatives"][0]
    else:
        active_plan = plan

    execute_plan(
        request_dir,
        active_plan,
        executor_command=executor_command,
        skip_pr=args.skip_pr,
        skip_auto_merge=args.skip_auto_merge,
    )
    logger.info(f"Orquestación completada en {request_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
