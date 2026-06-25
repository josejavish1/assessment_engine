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
from typing import Any, cast

from application.tools.context_tools import get_context_tools
from domain.prompts.product_owner_prompts import (
    build_product_owner_planner_prompt,
    get_product_owner_planner_instruction,
    render_plan_markdown,
    render_pr_reconciliation_prompt,
    render_task_prompt,
)
from infrastructure.ai_client import call_agent
from infrastructure.config_loader import (
    load_policy_file,
    resolve_model_profile_for_role,
)
from infrastructure.doctor_agent import DoctorAgent
from infrastructure.liability_signer import LiabilitySigner
from infrastructure.logger_config import setup_structured_logging
from infrastructure.pipeline_runtime import (
    build_runtime_env,
)
from infrastructure.product_owner_models import (
    ProductOwnerAlternatives,
)
from infrastructure.runtime_paths import ROOT
from infrastructure.secrets_client import get_secret
from infrastructure.text_utils import slugify
from infrastructure.verification_agent import (
    VerificationAgent,
)

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
    """Load the 'orchestrator_policy' configuration."""
    return load_policy_file("orchestrator_policy")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the Product Owner orchestrator.

    Configures and parses command-line arguments for orchestrating software
    development tasks. This function defines the primary command-line interface,
    which is structured around several distinct sub-commands:

    - `plan`: Generates an execution plan for a given feature or bug request.
      Requires either `--request` (a string) or `--request-file` (a path).
    - `run`: Generates a plan and immediately executes it. Accepts the same
      request arguments as `plan`, along with execution control flags like
      `--executor-command`, `--allow-dirty`, `--skip-pr`, and
      `--skip-auto-merge`.
    - `execute`: Executes a previously generated plan from a specified request
      directory (`--request-dir`). Supports selecting an alternative plan via
      `--alt-index` and accepts the same execution control flags as `run`.
    - `resume-pr`: Resumes an execution process based on an existing pull
      request (`--pr-number`) or branch (`--branch`). It also accepts
      execution control flags like `--executor-command`, `--allow-dirty`,
      and `--skip-auto-merge`.

    Args:
        argv: A list of string arguments to parse. If None, defaults to
            `sys.argv[1:]`.

    Returns:
        An `argparse.Namespace` object containing the parsed command-line
        arguments and their values.
    """
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
    """Resolve the absolute path to the requests root directory from a policy dictionary."""
    relative = policy.get("paths", {}).get(
        "requests_root", "working/product_owner_requests"
    )
    return ROOT / relative


def load_request_text(args: argparse.Namespace) -> str:
    r"""{'docstring': 'Load user request text from parsed command-line arguments.\n\n    The function attempts to retrieve the request text from the `request`\n    attribute of the provided namespace. If this attribute is absent or contains\n    only whitespace, it falls back to reading the content from the file path\n    specified in the `request_file` attribute.\n\n    Args:\n        args: An `argparse.Namespace` object containing the parsed arguments.\n            It is expected to have either a `request` attribute (a string) or\n            a `request_file` attribute (a path to a text file).\n\n    Returns:\n        The user request text, stripped of leading and trailing whitespace.\n\n    Raises:\n        ValueError: If `args.request` is effectively empty and\n            `args.request_file` is not provided.\n        FileNotFoundError: If `args.request_file` specifies a path that does\n            not exist.'}."""
    if args.request and args.request.strip():
        return args.request.strip()
    if args.request_file:
        return Path(args.request_file).read_text(encoding="utf-8").strip()
    raise ValueError("Debes indicar --request o --request-file.")


def create_request_dir(policy: dict[str, Any], request_text: str) -> Path:
    """Creates a unique directory for storing request-specific artifacts.

    The directory path is constructed by combining a root path resolved from the
    `policy` dictionary, a UTC timestamp in `YYYYMMDD_HHMMSS` format, and a
    slugified, truncated version of the `request_text`. This ensures that each
    directory has a unique, chronologically sortable, and human-readable name.

    Args:
        policy: The application policy configuration dictionary, used to resolve
            the root storage directory for all requests.
        request_text: The raw user request text, which is slugified to form a
            component of the directory name.

    Returns:
        A `pathlib.Path` object representing the path to the newly created
        directory.

    Raises:
        FileExistsError: If a directory with the exact generated name already
            exists. This is highly improbable due to the timestamp component.
        OSError: If the directory cannot be created due to filesystem errors,
            such as insufficient permissions.
    """
    requests_root = resolve_requests_root(policy)
    requests_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    request_slug = slugify(request_text)[:48]
    request_dir = requests_root / f"{timestamp}_{request_slug}"
    request_dir.mkdir(parents=True, exist_ok=False)
    return request_dir


def ensure_clean_worktree(*, allow_dirty: bool, request_text: str = "") -> None:
    """Ensure the Git worktree is clean before executing a command.

    This function acts as a safeguard to prevent operations from running on a
    repository with uncommitted changes, which could lead to an inconsistent
    state. The check is bypassed if the `allow_dirty` flag is True, or if the
    `request_text` contains keywords associated with cleanup or remediation
    actions (e.g., "git reset", "ruff format"). This exception allows the
    system to perform corrective actions even when the worktree is not clean.

    The actual detection of a dirty worktree is delegated to the
    `git_status_has_relevant_changes` function.

    Args:
        allow_dirty: If True, bypasses the worktree cleanliness check entirely.
        request_text: The user's command string, inspected to detect
            remediation commands that are permitted to run on a dirty
            worktree.

    Raises:
        RuntimeError: If the Git worktree has uncommitted changes, `allow_dirty`
            is False, and the request is not a remediation command.
    """
    if allow_dirty:
        return

    # Defines a whitelist of idempotent, non-destructive commands authorized for execution during system remediation.
    logger.info(f"Evaluando modo saneamiento para: '{request_text}'")
    remediation_keywords = [
        "git reset",
        "git clean",
        "git status",
        "ruff check --fix",
        "ruff format",
        "limpieza",
        "saneamiento",
        "restaurar",
        "purgar",
    ]
    if any(keyword in request_text.lower() for keyword in remediation_keywords):
        logger.info(
            "Modo Saneamiento detectado: permitiendo worktree sucio para comandos de limpieza."
        )
        return

    if git_status_has_relevant_changes():
        raise RuntimeError(
            "El worktree no está limpio. Usa --allow-dirty solo si entiendes el riesgo."
        )


async def generate_plan(request_text: str, policy: dict[str, Any]) -> dict[str, Any]:
    """Orchestrates a language model to generate a structured development plan.

    This coroutine invokes a planner agent to decompose a natural language request
    into a structured development plan. The agent's response is grounded by
    project context from a `GEMINI.md` file, if one exists in the project root.
    The agent's model profile is resolved based on the 'product_owner_planner'
    role, and the maximum number of tasks in the plan can be constrained via
    the policy.

    Args:
        request_text: The high-level natural language request for a feature or
            change.
        policy: A dictionary containing configuration. The key path
            `planning.max_tasks` (integer) can be used to limit the number of
            generated tasks. Defaults to 5 if not specified.

    Returns:
        A JSON-serializable dictionary representing one or more alternative
        development plans, conforming to the `ProductOwnerAlternatives` schema.

    Raises:
        pydantic.ValidationError: If the language model's output fails to
            validate against the `ProductOwnerAlternatives` schema.
    """
    max_tasks = int(policy.get("planning", {}).get("max_tasks", 5))
    model_profile = resolve_model_profile_for_role("product_owner_planner")

    # Injects the authoritative project context from `GEMINI.md` to ground the language model and mitigate the risk of confabulation.
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
    r"""{'docstring': "Save the planning results to disk in multiple formats.\n\nThis function serializes the provided plan bundle and its corresponding user\nrequest into a specified directory. It creates three distinct files:\n- `request.txt`: The verbatim original user request.\n- `plan.json`: The raw `plan_bundle` dictionary, serialized to JSON.\n- `plan.md`: A human-readable summary of the plan(s) in Markdown format.\n\nArgs:\n    request_dir: The target directory for the output files.\n    request_text: The original user request text.\n    plan_bundle: A dictionary containing the structured plan. The dictionary\n        structure determines the output, representing either an ambiguous\n        request (containing 'is_ambiguous' and 'clarification_question'\n        keys) or a set of execution plans (containing an 'alternatives' key).\n\nRaises:\n    OSError: If an error occurs during file I/O operations, such as a\n        permissions error or if the disk is full."}."""
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
    """Executes a Git command as a non-interactive subprocess.

    This function wraps `subprocess.run` to execute a Git command with a
    300-second timeout from the project's root directory (`ROOT`). It sets the
    `GIT_TERMINAL_PROMPT` environment variable to "0", disabling interactive
    prompts to ensure suitability for automated environments like CI/CD pipelines.

    Args:
        args: A list of strings representing the Git command and its arguments.

    Returns:
        A `subprocess.CompletedProcess` object containing the result of the
        command execution. This is only returned if the command completes
        successfully with an exit code of 0.

    Raises:
        RuntimeError: If the command returns a non-zero exit code or if the
            execution timeout of 300 seconds is exceeded. The exception
            message will contain the contents of stderr, if available.
    """
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = (
        "0"  # Disables interactive Git prompts to facilitate non-interactive execution within automated CI/CD environments.
    )

    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=300,  # A 5-minute timeout is enforced to prevent indefinite blocking of the operation.
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout excedido ejecutando: {' '.join(args)}")

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or f"Fallo ejecutando: {' '.join(args)}"
        )
    return result


def run_json_command(args: list[str]) -> Any:
    """Executes a Git command and parses its standard output as JSON.

    Args:
        args: The sequence of strings constituting the Git command to execute.

    Returns:
        The Python object deserialized from the command's standard output.

    Raises:
        RuntimeError: If the standard output from the command is not valid JSON.
    """
    result = run_git_command(args)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Respuesta JSON inválida para {' '.join(args)}: {result.stdout.strip()}"
        ) from exc


def ensure_branch(branch_name: str) -> None:
    """Ensure a specific git branch exists and is the current working branch.

    This function first queries for the current active branch. If the current
    branch matches the target `branch_name`, no action is taken. Otherwise, it
    determines if a branch with the given name already exists locally. If it
    exists, the function checks it out. If it does not exist, a new branch is
    created from the current HEAD and then checked out.

    Args:
        branch_name: The name of the git branch to create or switch to.

    Raises:
        subprocess.CalledProcessError: If any of the underlying git commands fail.
    """
    #
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    if current_branch == branch_name:
        return  #

    #
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
    """Checks out a git branch, creating a local tracking branch if one does not exist.

    This function ensures a specified git branch is checked out in the local
    repository. It first fetches the branch information from the 'origin' remote.
    If a local branch with the same name already exists, it is checked out.
    Otherwise, a new local branch is created to track the corresponding remote
    branch (e.g., `origin/my-branch`) and is then checked out.

    Args:
        branch_name (str): The name of the git branch to ensure is checked out.

    Raises:
        subprocess.CalledProcessError: If an underlying git command fails, for
            example, if the specified branch does not exist on the 'origin'
            remote.
    """
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
    """Resolve the executor command, prioritizing the direct argument over an environment variable."""
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
    r"""{'docstring': "Constructs a list of command-line arguments from a template string.\n\n    Formats a template string with runtime values and parses it into a list\n    suitable for subprocess execution. This function substitutes placeholders for the\n    repository root path (`repo_root`), the task prompt file path\n    (`task_prompt_file`), and the current attempt number (`attempt`). The\n    resulting string is then parsed using shell-like splitting rules via\n    `shlex.split` to correctly handle quoted arguments.\n\n    Args:\n        template: The command-line template string. It may contain the format\n            placeholders `{repo_root}`, `{task_prompt_file}`, and `{attempt}`.\n        task_prompt_file: The path to the file containing the task prompt.\n        attempt: The current execution attempt number.\n\n    Returns:\n        A list of strings representing the shell-parsed arguments.\n\n    Raises:\n        KeyError: If `template` contains a format placeholder that is not one of\n            'repo_root', 'task_prompt_file', or 'attempt'.\n        ValueError: If the formatted command string contains an unclosed quote,\n            which is an error condition for `shlex.split`."}."""
    formatted = template.format(
        repo_root=str(ROOT),
        task_prompt_file=str(task_prompt_file),
        attempt=str(attempt),
    )
    return shlex.split(formatted)


def collect_changed_python_files() -> list[str]:
    r"""{'docstring': "Aggregate paths of modified, staged, and untracked Python files.\n\nScans the git repository at the project's ROOT directory to identify Python\nfiles (`*.py`) that are not in a clean, unmodified state. It achieves this\nby executing three distinct git commands to cover all non-pristine file\nstates:\n\n1.  **Modified (Unstaged):** Files with changes in the working directory\n    that have not been staged (`git diff --name-only`).\n2.  **Staged:** Files with changes added to the git index for the next\n    commit (`git diff --name-only --cached`).\n3.  **Untracked:** New files not tracked by git, excluding those specified\n    in `.gitignore` (`git ls-files --others --exclude-standard`).\n\nThe file paths gathered from these commands are combined, deduplicated,\nand returned as a single sorted list.\n\nReturns:\n    A sorted list of unique, relative file paths for all Python files\n    that are modified, staged, or untracked.\n\nRaises:\n    FileNotFoundError: If the `git` executable is not found in the\n        system's PATH."}."""
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
    """Check if the Git worktree has any uncommitted changes."""
    return git_status_has_relevant_changes()


def read_git_status_lines() -> list[str]:
    """Read the short-form status of the Git working tree.

    Executes `git status --short` in the project's root directory to retrieve
    a concise summary of repository changes.

    Returns:
        list[str]: A list of non-empty lines from the command's standard output.

    Raises:
        RuntimeError: If the `git` command returns a non-zero exit code,
            indicating an execution failure (e.g., not a git repository).
    """
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
    """Return whether a given path is a Python bytecode cache artifact."""
    normalized = path.strip()
    return "__pycache__/" in normalized or normalized.endswith((".pyc", ".pyo", ".pyd"))


def git_status_has_relevant_changes() -> bool:
    """Check for non-ignorable changes in the Git working tree.

    Parses the output of a porcelain-format `git status` command line by line.
    For each detected change, the file path is extracted, correctly handling
    renames by using the destination path. Each path is then evaluated by the
    `is_ignorable_git_status_path` helper to filter out irrelevant modifications.
    If a relevant (non-ignorable) change is found, a warning is logged with
    details of the file, and the function short-circuits.

    Returns:
        True if at least one non-ignorable change is present in the working
        tree, False otherwise.
    """
    for line in read_git_status_lines():
        path = line[3:]
        if "->" in path:
            path = path.split("->", maxsplit=1)[1].strip()
        if is_ignorable_git_status_path(path):
            continue
        logger.warning(
            f"Worktree sucio detectado por el archivo: '{path}' (status: '{line[:2]}')"
        )
        return True
    return False


def load_json_file(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file from a given path."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


class OrchestratorCommandError(RuntimeError):
    r"""[{'identifier': 'run_product_owner_orchestrator.OrchestratorCommandError', 'docstring': "Indicates a failure during the execution of an orchestrated subprocess command.\n\nThis exception is raised when a command invoked via a subprocess returns a\nnon-zero exit code. It encapsulates the context of the failure, including\nthe command itself, its output, and a categorized failure type to facilitate\nprogrammatic handling and debugging.\n\nAttributes:\n    category (str): A string categorizing the failure (e.g., 'build', 'test').\n    command (list[str]): The command and its arguments that resulted in failure.\n    output_path (pathlib.Path): The filesystem path to the file containing the\n        complete stdout and stderr from the command execution.\n    raw_output (str): A string containing the captured raw stdout and stderr\n        from the failed command."}, {'identifier': 'run_product_owner_orchestrator.OrchestratorCommandError.__init__', 'docstring': "Initializes the OrchestratorCommandError instance.\n\nArgs:\n    message (str): A high-level error message summarizing the failure. This\n        message is passed to the parent `RuntimeError` constructor.\n    category (str): The category of the command that failed (e.g., 'build').\n    command (list[str]): The command and arguments that were executed as a list\n        of strings.\n    output_path (pathlib.Path): The path to the log file containing the command's\n        output.\n    raw_output (str): The complete, raw captured stdout and stderr from the\n        subprocess as a single string."}]."""

    def __init__(
        self,
        message: str,
        *,
        category: str,
        command: list[str],
        output_path: Path,
        raw_output: str,
    ) -> None:
        """Initializes the exception with details of a failed command execution.

        Args:
            message: The primary, human-readable error message.
            category: A string categorizing the type of failure.
            command: The command and its arguments that failed to execute.
            output_path: The filesystem path to the output file associated with the
                failed command.
            raw_output: The captured stdout and stderr from the command execution.
        """
        super().__init__(message)
        self.category = category
        self.command = command
        self.output_path = output_path
        self.raw_output = raw_output


def classify_command_failure(command: list[str], output: str) -> str:
    """Classify a command execution failure based on the command and its output.

    Analyzes the executed command and its resulting output string for specific
    keywords and patterns to determine a root cause category. This classification
    facilitates automated routing and error handling. The function identifies
    authentication failures (e.g., missing API keys), executor-specific
    configuration issues, missing executables or files, and failures
    originating from code validation tools.

    Args:
        command: The command that was executed, as a list of string arguments.
        output: The captured stdout or stderr from the command execution.

    Returns:
        A string representing the classified failure category. Possible values
        are: 'executor_auth', 'executor_config', 'executor_missing',
        'validation', or the default 'command_failure'.
    """
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
    """Constructs a human-readable command failure message in Spanish.

    Args:
        category: The failure category, which determines the message prefix.
            Supported categories include 'executor_auth', 'executor_config',
            'executor_missing', 'timeout', 'validation', and 'command_failure'.
        command: The command that failed, as a list of its string components.
        output_path: The filesystem path to the log file containing the
            command's output.
        timeout_seconds: A keyword-only argument specifying the timeout in
            seconds that was exceeded. This value is only appended to the
            message if the category is 'timeout'.

    Returns:
        A formatted string in Spanish detailing the command failure.
    """
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
    """Executes a shell command, streaming its output and capturing results.

    Runs the specified command in a subprocess with a custom environment configured
    for the application runtime. The subprocess's `stdout` and `stderr` streams
    are merged and read by a background thread, which allows for real-time
    printing to the console while simultaneously capturing the complete output.

    Upon termination (successful or otherwise), the full captured output is written
    to the file specified by `output_path`. The subprocess is started in a new
    process session, enabling reliable termination of the entire process group
    via `os.killpg` in case of a timeout. This mechanism ensures that no
    orphaned child processes are left behind.

    Failures, such as a non-zero exit code or a timeout, result in a categorized
    `OrchestratorCommandError` being raised, which includes detailed context
    about the failure.

    Args:
        command: The command and its arguments to execute as a list of strings.
        output_path: The file path where the complete command output will be
            written.
        timeout_seconds: The maximum execution time in seconds. If the command
            exceeds this duration, it is terminated. If `None`, no timeout is
            enforced.

    Returns:
        None.

    Raises:
        OrchestratorCommandError: If the command returns a non-zero exit code or
            if it exceeds the specified `timeout_seconds`.
    """
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

    import sys
    import threading

    output_lines = []

    def reader_thread() -> None:
        """Continuously reads lines from a global subprocess's stdout stream.

        This function is designed to be executed in a dedicated thread to monitor
        the output of a running subprocess. It relies on two global variables:
        `process`, which must be an active `subprocess.Popen` object, and
        `output_lines`, a list used to accumulate the output.

        The function iterates through the lines from the `process.stdout` stream in a
        blocking manner. Each line is immediately written and flushed to
        `sys.stdout` for real-time display, and also appended to the global
        `output_lines` list for later access. The function terminates when the
        subprocess's stdout stream is closed.

        Raises:
            NameError: If the global variables `process` or `output_lines` are not
                defined in the execution scope.
        """
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
    """Serialize and write a dictionary to a file as formatted JSON."""
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_reconciliation_event(request_dir: Path, payload: dict[str, Any]) -> None:
    r"""{'docstring': "Appends a JSON-serialized event to a reconciliation timeline file.\n\nConstructs an event object by augmenting the provided payload with an ISO 8601\nformatted UTC timestamp under the 'timestamp_utc' key. The complete event is\nthen serialized to a JSON string and appended as a new line to the timeline\nfile, effectively creating a JSON Lines (JSONL) formatted log. The file is\nnamed according to the `RECONCILIATION_TIMELINE_FILE` constant and will be\ncreated within `request_dir` if it does not already exist.\n\nArgs:\n    request_dir: The path to the directory where the timeline file resides\n        or will be created.\n    payload: The event data to be recorded. Must be composed of\n        JSON-serializable types.\n\nRaises:\n    FileNotFoundError: If the `request_dir` path does not exist or does not\n        point to a directory.\n    TypeError: If the `payload` contains objects that cannot be serialized\n        by `json.dumps`."}."""
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **payload}
    timeline_path = request_dir / RECONCILIATION_TIMELINE_FILE
    with timeline_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def write_reconciliation_summary(request_dir: Path, payload: dict[str, Any]) -> None:
    """Write a timestamped reconciliation summary payload to a specified directory."""
    summary = {"updated_at_utc": datetime.now(timezone.utc).isoformat(), **payload}
    write_json(request_dir / RECONCILIATION_SUMMARY_FILE, summary)


def executor_uses_github_wrapper(command_template: str) -> bool:
    """Check if the command template contains a known GitHub executor script."""
    return (
        "orchestrator-gemini-executor.sh" in command_template
        or "orchestrator-github-executor.sh" in command_template
    )


def validate_executor_configuration(command_template: str) -> None:
    """Validate the authentication configuration for a Gemini-based executor.

    Performs a pre-flight check to ensure that necessary authentication
    credentials are configured before invoking a Gemini-based executor. This
    validation is only triggered if the provided `command_template` indicates
    the use of the Gemini GitHub wrapper.

    The function assesses the environment for a valid authentication method in a
    specific order of precedence:
    1.  Google Cloud service-based authentication (Vertex AI or GCA),
        controlled by the `GOOGLE_GENAI_USE_VERTEXAI` and
        `GOOGLE_GENAI_USE_GCA` environment variables.
    2.  An API key (`gemini-api-key` or `google-api-key`) retrieved from
        Google Secret Manager. The project is inferred from the
        `GOOGLE_CLOUD_PROJECT` environment variable.
    3.  An API key provided directly via the `GEMINI_API_KEY` or
        `GOOGLE_API_KEY` environment variables.

    If service-based authentication is explicitly disabled and no API key can be
    found through either Secret Manager or environment variables, an exception
    is raised.

    Args:
        command_template: The command template string that invokes the executor.
            Validation is skipped if this template does not use the Gemini GitHub
            wrapper.

    Raises:
        RuntimeError: If service-based authentication is disabled and an API key
            cannot be located in either Google Secret Manager or the
            corresponding environment variables.
    """
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
        # Implements a fallback routine to handle scenarios where the secret manager is inaccessible or the `project_id` is incorrectly configured.
        has_api_key = False

    # Direct environment variable access is used as the final fallback mechanism for configuration parameter retrieval.
    if not has_api_key:
        has_api_key = bool(
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )

    if vertex_selector in {"0", "false", "no"} and not gca_selector and not has_api_key:
        raise RuntimeError(
            "El executor de Gemini requiere GEMINI_API_KEY, GOOGLE_API_KEY o habilitar autenticación Google."
        )


def preflight_executor(request_dir: Path, command_template: str) -> None:
    """Perform preflight validation of the executor configuration.

    Validates the executor's command template prior to execution. Other potential
    preflight checks are bypassed to prevent client timeouts during long-running
    operations.

    Args:
        request_dir: The path to the directory containing request data. This
            argument is currently unused.
        command_template: The command template string to be validated.

    Raises:
        ValueError: If the `command_template` is invalid or contains disallowed
            placeholders.
    """
    validate_executor_configuration(command_template)
    # Preflight checks are bypassed to prevent Gemini CLI timeouts that may occur during extended operations.
    return


def run_standard_validations(request_dir: Path) -> None:
    """Execute standard validations on changed Python files.

    Identifies Python source files modified within the current version control
    context and subsequently invokes the `VerificationAgent` to validate these
    changes. The validation is performed against the provided request directory.

    Args:
        request_dir: The file system path to the directory containing the request
            context against which changes are validated.

    Raises:
        Exception: If the changes fail the validation checks or if a critical
            error occurs during the file collection or verification process.
    """
    changed_python_files = collect_changed_python_files()
    VerificationAgent.verify_changes(request_dir, changed_python_files)


def resolve_execution_timeouts(policy: dict[str, Any]) -> dict[str, int]:
    """Resolve execution timeouts from a policy dictionary, applying default values."""
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
    r"""{'docstring': "Squash un-proofed commits and create a new, consolidated commit.\n\n    This function consolidates all file changes and prior commits on the current\n    branch into a single, new commit. It first identifies the common ancestor\n    commit between the current `HEAD` and `origin/main` (falling back to `main`).\n    If commits exist on the current branch that lack a `[zk-Liability-Proof]`\n    block in their message, the branch's `HEAD` is soft-reset to the common\n    ancestor. This action unstages all intermediate changes, preparing them to\n    be included in the new, unified commit.\n\n    All current working directory changes are then staged (`git add -A`). If the\n    staging area is empty after this operation, the function logs a warning and\n    exits without creating a commit.\n\n    A new commit is created using the provided title. A `Co-authored-by` credit\n    for 'Copilot' is automatically appended. If a `compliance_receipt` dictionary\n    is provided, its contents are formatted and appended within a\n    `[zk-Liability-Proof]` block for governance and compliance tracking.\n\n    Args:\n        commit_title: The subject line for the Git commit message.\n        compliance_receipt: An optional dictionary containing compliance metadata.\n            If provided, it is embedded in the commit message. Expected keys\n            include 'eu_ai_act_compliance' and 'governance_commitment_hash'.\n\n    Returns:\n        This function operates via side effects on the local Git repository and\n        does not return a value.\n\n    Raises:\n        Exception: If an underlying Git command fails during execution, which may\n            prevent the commit operation from completing successfully."}."""
    # Detects and reverts any commits made by sub-agents to ensure all changes are consolidated into a single, officially signed commit.
    try:
        # Determines the base commit by establishing a common ancestor with the `main` or `origin/main` branch.
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
                # Verifies if the current commit is already officially signed, thereby preventing redundant signing operations.
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

    # Verifies that staged changes exist in the index before initiating the commit operation.
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
    run_git_command(["git", "commit", "--no-gpg-sign", "-m", message])


def push_branch(branch_name: str) -> None:
    """Pushes a specified local branch to the 'origin' remote repository.

    This function utilizes `git push --force-with-lease` to update the remote
    branch. This is a safer alternative to a standard force push, as it will
    abort the operation if the remote branch contains commits that are not present
    in the local repository's remote-tracking branch, thus preventing the loss of
    concurrent work. The `-u` (`--set-upstream`) flag is used to establish a
    tracking relationship between the local and remote branches.

    Args:
        branch_name: The name of the local branch to be pushed.

    Raises:
        RuntimeError: If the underlying `git push` command returns a non-zero
            exit code, which may occur due to lease rejection, network errors,
            or authentication failures.
    """
    # Utilizes `--force-with-lease` to safely update the remote branch, which may exist from a prior failed or divergent execution. This strategy prevents the overwriting of new commits pushed by other collaborators.
    #
    run_git_command(["git", "push", "--force-with-lease", "-u", "origin", branch_name])


def repository_coordinates() -> tuple[str, str]:
    """Retrieves the owner and name for the current GitHub repository.

    This function executes the GitHub CLI (`gh repo view`) to obtain repository
    metadata. It requires `gh` to be installed, authenticated, and executed from
    within a local git repository that has a remote configured on GitHub.

    Returns:
        A tuple containing the repository owner's login and the repository name.

    Raises:
        RuntimeError: If the `gh` command fails, its output cannot be parsed,
            or the owner and name cannot be extracted from the returned data.
    """
    payload = run_json_command(["gh", "repo", "view", "--json", "owner,name"])
    owner = payload.get("owner", {}).get("login")
    repo = payload.get("name")
    if not owner or not repo:
        raise RuntimeError("No se pudo resolver el repositorio actual en GitHub.")
    return owner, repo


def get_pull_request(branch_name: str) -> dict[str, Any]:
    """Fetches details for a GitHub pull request using the `gh` CLI.

    This function executes the `gh pr view` command to retrieve metadata for a
    pull request associated with the specified head branch.

    Args:
        branch_name: The name of the head branch for the target pull request.

    Returns:
        A dictionary containing the pull request details, populated with the
        following keys: 'number', 'title', 'url', 'headRefName', 'baseRefName',
        'isDraft', 'mergeable', 'mergeStateStatus', 'reviewDecision', and
        'statusCheckRollup'.

    Raises:
        Exception: If the underlying `gh` command fails. This may occur if a pull
            request for the given branch does not exist, if GitHub
            authentication fails, or if the `gh` CLI is not installed or
            properly configured.
    """
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
    """Fetch all review threads for a specified GitHub pull request.

    This function executes a GraphQL query via the 'gh' command-line tool
    to retrieve all review threads from the GitHub API. The query targets the
    pull request number provided within the repository context derived from
    the local environment.

    Args:
        pr_number (int): The number of the target pull request.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, where each dictionary
        represents a review thread node as returned by the GitHub GraphQL
        API. An empty list is returned if the pull request contains no
        review threads or if the specified pull request number does not
        exist in the repository.

    Raises:
        subprocess.CalledProcessError: If the underlying 'gh api graphql'
            command fails to execute successfully, for instance due to
            authentication issues or malformed queries.
    """
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
    """Filters and normalizes a list of raw code review thread objects.

    This function processes a list of dictionaries representing code review
    threads, such as those from a GitHub GraphQL API response. It discards any
    threads that are marked as resolved (`isResolved` is True). For the
    remaining unresolved threads, it transforms the data into a simplified and
    consistent format.

    The transformation extracts essential thread metadata (ID, path, line)
    and comment details (ID, author, body, state). A boolean flag,
    `all_comments_bot`, is added to each normalized thread to indicate if all
    of its comments were authored by bots.

    Args:
        threads: A list of dictionaries, where each dictionary represents a raw
            review thread. Each thread is expected to contain keys such as
            `isResolved`, `id`, `path`, `line`, `isOutdated`, and a nested
            `comments` dictionary. The `comments` dictionary is expected to
            contain a `nodes` key with a list of comment objects. Each comment
            should have `databaseId`, `body`, `state`, and a nested `author`
            dictionary with `login` and `__typename`.

    Returns:
        A list of dictionaries, where each dictionary represents a single
        unresolved and normalized review thread. Each dictionary contains the
        keys: 'id', 'path', 'line', 'is_outdated', 'comments', and
        'all_comments_bot'. The 'comments' value is a list of simplified
        comment dictionaries.
    """
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
    """Normalizes and categorizes a list of status check records.

    This function processes a list of status check dictionaries, often sourced
    from disparate version control system APIs which may have inconsistent schemas
    (e.g., GitHub's Checks API vs. Statuses API). It creates a unified
    representation by normalizing key fields, coalescing 'conclusion' with
    'state', 'name' with 'context', and 'detailsUrl' with 'targetUrl'. All
    string-based status and conclusion values are uppercased for consistent
    matching.

    After normalization, the checks are filtered into 'failed' and 'pending'
    categories based on their status and conclusion fields.

    Args:
        checks: A list of dictionaries, where each dictionary represents a raw
            status check record from a VCS API.

    Returns:
        A dictionary with three keys:
        - 'checks': The complete list of all normalized check dictionaries.
        - 'failed_checks': A list of checks with a 'COMPLETED' status and a
          conclusion that is not 'SUCCESS', 'SKIPPED', or 'NEUTRAL'.
        - 'pending_checks': A list of checks that either do not have a
          'COMPLETED' status or have a conclusion indicating an unresolved
          state (e.g., 'PENDING', 'ACTION_REQUIRED').
    """
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
    """Aggregate and summarize key details for a specified pull request.

    Retrieves pull request metadata, review threads, and status check rollups
    associated with the provided branch name. The function aggregates and
    normalizes this information from various data sources into a single,
    structured dictionary.

    Args:
        branch_name (str): The name of the head branch for which to inspect the
            corresponding pull request.

    Returns:
        dict[str, Any]: A dictionary containing normalized pull request data.
            This includes core metadata (`number`, `title`, `url`), branch
            references (`head_ref`, `base_ref`), state information (`is_draft`,
            `mergeable`, `merge_state_status`, `review_decision`), a summary of
            status checks (`checks`, `failed_checks`, `pending_checks`), and a
            list of unresolved review threads (`unresolved_threads`).

    Raises:
        ValueError: If no pull request is found for the given `branch_name` or
            if a failure occurs during an underlying data-fetching operation.
    """
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
    r"""{'docstring': "Determine if a GitHub check run corresponds to the current GitHub Actions job.\n\n    Identifies the current job by comparing standard GitHub Actions environment\n    variables (`GITHUB_RUN_ID`, `GITHUB_WORKFLOW`, `GITHUB_JOB`) against\n    attributes of the provided check run. A primary check matches the run ID\n    from the 'details_url' for an exact identification. If this fails (e.g.,\n    the URL is not yet populated), a fallback mechanism matches based on the\n    workflow and job name for checks that are not yet 'COMPLETED'.\n\n    This function is designed to operate within a GitHub Actions runner\n    environment.\n\n    Args:\n        check: A dictionary representing a GitHub check run from the GitHub API.\n            Expected keys include 'details_url', 'workflow_name', 'status',\n            and 'name'.\n\n    Returns:\n        bool: True if the check run corresponds to the currently executing\n            GitHub Actions job, otherwise False."}."""
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
    """Filter out the current reconciliation check from the PR state.

    Prevents the orchestrator from processing its own status check, which could
    result in an infinite loop. This function identifies and removes any check
    matching `is_current_reconciliation_check` from the 'checks',
    'failed_checks', and 'pending_checks' lists within the `pr_state`.

    Args:
        pr_state: A dictionary representing the state of a pull request's CI
            checks. It is expected to contain lists of check objects
            (dictionaries). While the 'checks' key is optional, the
            'failed_checks' and 'pending_checks' keys must be present if a
            reconciliation check is found within the 'checks' list.

    Returns:
        A new dictionary with the reconciliation check filtered from the relevant
        check lists. If no reconciliation check is found in the 'checks' list,
        the original `pr_state` dictionary object is returned unmodified.

    Raises:
        KeyError: If a reconciliation check is present in the 'checks' list,
            but the `pr_state` dictionary is missing either the 'failed_checks'
            or 'pending_checks' key.
    """
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
    r"""{'docstring': "Determine if a pull request is ready to be merged based on its state.\n\nA pull request is considered ready if it is not a draft, has no failing or\npending status checks, no unresolved review threads, a 'MERGEABLE' state,\nand a merge status that is not 'BEHIND', 'BLOCKED', 'DIRTY', or 'UNKNOWN'.\n\nArgs:\n    pr_state: A dictionary representing the pull request's state. It must\n        contain the keys 'is_draft', 'failed_checks', 'pending_checks',\n        'unresolved_threads', 'mergeable', and 'merge_state_status'.\n\nReturns:\n    True if the pull request meets all merge criteria, False otherwise.\n\nRaises:\n    KeyError: If any of the required state keys are missing from `pr_state`."}."""
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
    """Resolve pull request review threads composed exclusively of bot comments.

    Iterates through unresolved review threads within a given pull request state.
    For each thread where all comments are authored by bots, this function
    posts an explanatory reply and subsequently resolves the thread using the
    GitHub API via the 'gh' command-line tool.

    Args:
        pr_state: A dictionary representing the state of a GitHub pull request.
            Expected to contain the following structure:
            - 'number' (int): The pull request identifier.
            - 'unresolved_threads' (list[dict]): A list of unresolved review
              threads. Each thread dictionary must contain:
              - 'id' (str): The GraphQL node ID of the thread.
              - 'all_comments_bot' (bool): True if all comments in the
                thread are from bots; otherwise, False.
              - 'comments' (list[dict]): A list of comments where the first
                comment's 'database_id' is used for posting a reply.

    Returns:
        The total number of review threads that were automatically resolved.

    Raises:
        KeyError: If `pr_state` or any of its nested thread objects are
            missing required keys.
        Exception: Propagates exceptions from the underlying 'gh' command execution,
            typically indicating a failure due to API errors, authentication
            issues, or network problems.
    """
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
    """Construct an automated resolution note for a bot thread based on repository checks and outdated status."""
    reason = "the repository checks are green"
    if thread.get("is_outdated"):
        reason += " and the commented lines are now outdated"
    return (
        "Automated reconciliation note: this bot-only thread is being resolved because "
        f"{reason}. The current PR state has been revalidated before closure."
    )


def build_pr_feedback(pr_state: dict[str, Any]) -> dict[str, Any]:
    """Transforms raw pull request state data into a structured feedback dictionary.

    This function reshapes a flat dictionary of pull request state into a nested
    dictionary suitable for internal processing. It renames 'unresolved_threads' to
    'unresolved_review_threads' and provides a default value of "none" for
    'review_decision' if the source value is falsy.

    Args:
        pr_state: A dictionary containing the raw state of a pull request as
            fetched from a source like the GitHub API. Expected keys include
            'number', 'url', 'merge_state_status', 'mergeable',
            'review_decision', 'failed_checks', 'pending_checks', and
            'unresolved_threads'.

    Returns:
        A dictionary summarizing the pull request's status with a nested
        'pull_request' object and top-level keys for checks and threads. The
        'unresolved_threads' key from the input is renamed to
        'unresolved_review_threads'.

    Raises:
        KeyError: If `pr_state` is missing one of the required keys.
    """
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
    """Extract validation command names from a policy and append default quality gates."""
    names = [
        entry.get("name", "validation")
        for entry in policy.get("validation_commands", [])
    ]
    names.extend(["incremental quality gate", "incremental typecheck"])
    return names


def find_latest_plan_for_branch(
    policy: dict[str, Any], branch_name: str
) -> dict[str, Any] | None:
    r"""["Finds the most recent plan associated with a specific git branch.\n\n    Scans a requests root directory for subdirectories, which are assumed to be\n    named in a chronologically sortable manner. The function searches these\n    subdirectories in reverse-chronological order for a 'plan.json' file.\n\n    For each 'plan.json' found, it attempts to parse the file into a\n    ProductOwnerAlternatives data model. If the first alternative within the\n    parsed plan corresponds to the specified `branch_name`, that alternative's\n    data is returned as a dictionary. Errors during file reading or JSON\n    validation for a given plan are logged and suppressed, and the search\n    continues.\n\n    Args:\n        policy: A configuration dictionary used by the `resolve_requests_root`\n            function to determine the root path containing request plan\n            directories.\n        branch_name: The exact name of the git branch for which to find the\n            latest plan.\n\n    Returns:\n        A dictionary representing the data of the first alternative from the\n        most recent plan found for the specified branch. Returns None if the\n        requests root directory does not exist, no plan file contains a\n        matching branch name, or if all candidate plan files are unparseable."]."""
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
        try:
            plan_bundle = ProductOwnerAlternatives.model_validate_json(
                plan_path.read_text(encoding="utf-8")
            )
            if (
                plan_bundle.alternatives
                and plan_bundle.alternatives[0].branch_name == branch_name
            ):
                return plan_bundle.alternatives[0].model_dump(mode="json")
        except Exception as e:
            logger.debug(f"Error validating plan {plan_path}: {e}")
            continue
    return None


def synthesize_resume_plan(
    policy: dict[str, Any],
    pr_state: dict[str, Any],
) -> dict[str, Any]:
    """Synthesize a structured plan to resume work on an existing pull request.

    Constructs a plan dictionary that provides the necessary context and parameters
    for an automated system to bring a pull request to a mergeable state. The
    plan defines metadata, scope, invariants, and validation criteria based on the
    provided pull request state and operational policy.

    Args:
        policy: A dictionary of policy configurations used to generate the
            default validation plan.
        pr_state: A dictionary representing the pull request's current state.
            Must contain 'head_ref', 'number', and 'base_ref' keys. May
            optionally contain a 'title' key.

    Returns:
        A dictionary representing the synthesized execution plan. The structure
        includes keys such as 'request_title', 'branch_name', 'pr_title',
        'commit_title', 'problem', 'in_scope', 'out_of_scope', 'invariants',
        and 'validation_plan'.

    Raises:
        KeyError: If `pr_state` is missing a required key ('head_ref',
            'number', or 'base_ref').
    """
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
    """Prepare an execution plan to resume work on a pull request.

    This function attempts to retrieve a pre-existing execution plan associated
    with the pull request's head branch. If a plan is found, it is updated
    with current pull request details (e.g., title, branch name) and
    augmented with default values for any missing fields, such as the commit
    title or validation plan. If no existing plan is located, a new plan is
    synthesized from the provided pull request state.

    Args:
        policy: A dictionary containing configuration parameters that guide the
            plan generation and modification process.
        pr_state: A dictionary representing the state of the pull request. Must
            contain 'head_ref' (the branch name) and 'number'. The 'title' key
            is used if present.

    Returns:
        A dictionary representing the execution plan, which will be either the
        updated pre-existing plan or a newly synthesized one.

    Raises:
        KeyError: If `pr_state` is missing the required 'head_ref' or 'number'
            keys.
    """
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
    """Format a resume request string using a pull request's number and head reference."""
    return f"Resume PR #{pr_state['number']} on {pr_state['head_ref']}"


def create_followup_commit_title(plan: dict[str, Any], round_number: int) -> str:
    """Format a commit title to include the pull request feedback round number."""
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
    r"""{'docstring': "Orchestrates a single round of automated pull request repair.\n\n    This function coordinates one attempt to fix a pull request by generating and\n    applying code changes based on its current state. It constructs a detailed\n    prompt from failed CI checks and unresolved review threads, then invokes an\n    external AI agent executor to produce code modifications. If the executor\n    generates changes, this function commits them to the pull request's branch and\n    pushes the update. The process, including prompts and outcomes, is logged\n    as reconciliation events in the specified request directory.\n\n    Args:\n        request_dir: The path to the working directory for the request, used for\n            storing prompts, logs, and other artifacts.\n        plan: A dictionary containing the original execution plan, including details\n            such as the target branch name.\n        executor_command: The command-line string used to invoke the external AI\n            agent executor.\n        pr_state: A dictionary representing the current state of the pull request,\n            detailing failed checks, pending checks, and unresolved review threads.\n        round_number: The integer representing the current iteration number of the\n            repair attempt.\n        additional_feedback: An optional string containing extra context or\n            instructions to be included in the prompt for the AI agent.\n\n    Returns:\n        A boolean indicating whether new code changes were generated, committed,\n        and pushed. `True` if modifications were applied, `False` if the\n        executor produced no changes (a no-op).\n\n    Raises:\n        OrchestratorCommandError: If the executor command fails due to a non-zero\n            exit code, timeout, or other execution error."}."""
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
    """Synchronize a feature branch with a base branch by merging updates.

    This function orchestrates a sequence of Git operations to update a feature
    branch with the latest changes from a specified base branch. It ensures the
    local repository is up-to-date, performs a non-interactive merge, validates
    the result, and pushes the changes to the remote repository.

    The process involves the following steps:
    1.  Checks out the local feature branch specified by `plan['branch_name']`.
    2.  Fetches the latest state of `base_branch` from the 'origin' remote.
    3.  Merges `origin/{base_branch}` into the current branch using a
        non-interactive (`--no-edit`) strategy.
    4.  Logs the combined stdout and stderr from the merge command to a file
        named `sync_{base_branch}.log` within `request_dir`.
    5.  Executes a standard suite of code validations against the merged state.
    6.  If validations pass, pushes the updated local branch to its 'origin'
        remote counterpart.

    Args:
        request_dir: The absolute path to the working directory for the current
            request, used for storing operation logs and other artifacts.
        plan: A dictionary containing operational parameters. Must include the
            key 'branch_name', which specifies the feature branch to update.
        base_branch: The name of the branch to merge updates from (e.g., 'main').

    Returns:
        None on successful synchronization and push. If post-merge validations
        fail, returns a string containing the error message from the exception.

    Raises:
        subprocess.CalledProcessError: If any underlying Git command (e.g., fetch,
            merge, push) fails. This is typically due to network issues,
            repository access problems, or unresolvable merge conflicts.
    """
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
    """Merge a pull request with a specified strategy and delete the source branch."""
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
    """Monitors and reconciles a pull request through a poll-and-repair loop.

    This function polls the state of a pull request, attempting to automatically
    resolve blocking issues based on a configurable policy. The reconciliation
    process handles several common scenarios:
    - If the branch is behind its base, it attempts to sync.
    - If status checks are failing or comments are unresolved, it invokes a
      self-repair command.
    - If the only unresolved comments are from bots, it resolves them automatically.

    The loop continues until the pull request is in a mergeable state, at which
    point it is merged, or until polling or repair limits are exceeded.

    Args:
        request_dir: The working directory for storing state files, logs, and
            reconciliation summaries.
        plan: A dictionary containing the execution plan, which must include the
            `branch_name` key for the target pull request.
        executor_command: The command string used to invoke a self-repair
            process when status checks fail or comments are unresolved.
        merge_mode: The merge strategy to employ (e.g., 'squash', 'rebase',
            'merge') once the pull request is ready.
        allow_merge: If True, merges the pull request upon successful
            reconciliation. If False, the function exits once the PR is ready
            without performing the merge.

    Returns:
        None.

    Raises:
        RuntimeError: If the pull request cannot be made mergeable within the
            configured maximum number of repair rounds or polling attempts.
    """
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
    """Constructs a markdown-formatted pull request body from a plan dictionary.

    The generated body is prepended with a machine-readable marker and structured
    into sections for Summary, Change Spec, Tasks, and Governance Checks.

    Args:
        plan: A dictionary representing the project plan. The dictionary is
            expected to conform to the following schema:
            - `problem` (str): A description of the problem being solved.
            - `value_expected` (str): The expected value or outcome of the change.
            - `in_scope` (list[str], optional): Items considered in scope.
            - `out_of_scope` (list[str], optional): Items considered out of scope.
            - `source_of_truth` (list[str], optional): Canonical documentation or
              data sources.
            - `invariants` (list[str], optional): System invariants to preserve.
            - `validation_plan` (list[str], optional): The plan for validating
              the change.
            - `tasks` (list[dict], optional): A list of task dictionaries, where
              each dictionary must contain 'id' and 'title' keys.

    Returns:
        A multi-line string containing the formatted markdown pull request body,
        terminated with a newline character.

    Raises:
        KeyError: If `plan` is missing the required 'problem' or
            'value_expected' keys.
    """
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
    r"""{'docstring': "Orchestrates the creation of a GitHub pull request using the `gh` CLI.\n\n    This function automates the process of opening a pull request. It constructs\n    the PR body from the plan, writes it to a file, pushes the specified branch\n    to the remote origin, and then executes the `gh pr create` command. The\n    metadata of the successfully created pull request is then retrieved and\n    serialized to a JSON file within the request directory. The function also\n    consults an orchestrator policy to determine the base branch and to check\n    for an auto-merge setting, which can be explicitly bypassed.\n\n    Args:\n        plan: A dictionary defining the pull request. Must contain\n            'branch_name' and 'pr_title' keys.\n        request_dir: The file system path to a directory where artifacts, such\n            as the PR body file (`pr_body.md`) and the created PR's metadata\n            (`pr_created.json`), will be stored.\n        skip_auto_merge: If True, explicitly bypasses the auto-merge logic,\n            even if it is enabled in the orchestrator policy.\n\n    Returns:\n        A dictionary containing the JSON response data for the created pull\n        request as returned by the GitHub API via the `gh` CLI.\n\n    Raises:\n        KeyError: If the `plan` dictionary lacks the required 'branch_name'\n            or 'pr_title' keys.\n        subprocess.CalledProcessError: If any of the underlying `git` or `gh`\n            shell commands fail.\n        IOError: If writing the pull request body or metadata files to\n            `request_dir` fails."}."""
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
    r"""{'docstring': "Orchestrates the execution of a multi-task development plan in an isolated Git worktree.\n\n    This function manages the end-to-end execution of development tasks defined\n    in a plan. It creates a temporary Git worktree to isolate file system\n    operations and prevent interference with the main repository state. For each\n    task, it invokes an external executor command.\n\n    If a task fails, a retry mechanism is initiated. A diagnostic agent\n    analyzes the failure and provides corrective feedback for subsequent\n    attempts. A governance 'Action Gate' can terminate the process if a critical\n    execution invariant is violated. Upon successful completion of all tasks,\n    changes are committed with a generated compliance receipt. Optionally, a pull\n    request can be created and automatically merged.\n\n    A cleanup handler ensures the temporary worktree is removed and the original\n    Git state is restored, regardless of success or failure.\n\n    Args:\n        request_dir: Path to a directory for storing execution artifacts, such as\n            prompts, logs, and state files.\n        plan: A dictionary defining the development plan. Must contain the keys\n            'branch_name', 'commit_title', and a 'tasks' list.\n        executor_command: The command string used to invoke the external process\n            that executes each development task.\n        skip_pr: If True, prevents the creation of a pull request after the\n            changes have been successfully committed.\n        skip_auto_merge: If True, disables the automatic merging of the created\n            pull request, overriding any configured policies.\n\n    Returns:\n        None\n\n    Raises:\n        RuntimeError: If a task exhausts all retry attempts or if the governance\n            'Action Gate' is triggered by a diagnostic agent, halting execution.\n        subprocess.CalledProcessError: If a critical Git command fails during\n            the worktree setup or other repository operations.\n        KeyError: If the `plan` dictionary is missing a required key, such as\n            'branch_name' or 'commit_title'."}."""
    global ROOT
    original_root = ROOT
    import atexit

    import infrastructure.runtime_paths as rp

    policy = load_orchestrator_policy()
    timeouts = resolve_execution_timeouts(policy)
    max_attempts = int(policy.get("execution", {}).get("max_attempts_per_task", 3))
    preflight_executor(request_dir, executor_command)

    branch_name = plan["branch_name"]
    shadow_worktree_path = Path("/tmp") / f"shadow_worktree_{slugify(branch_name)}"

    # Initializes and prepares a shadow worktree to isolate Git operations from the primary working directory.
    logger.info(f"Fase 2: Preparando Shadow Workspace en {shadow_worktree_path}")
    subprocess.run(
        ["git", "worktree", "remove", "-f", str(shadow_worktree_path)],
        cwd=original_root,
        stderr=subprocess.DEVNULL,
    )

    # Captures the current branch name for state restoration upon successful or failed execution.
    original_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=original_root,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not original_branch:
        original_branch = "main"  #

    #
    ensure_branch(branch_name)

    # Transitions the primary worktree to a detached HEAD state. This releases the lock on the current branch, making it available for checkout and modification within the shadow worktree.
    subprocess.run(["git", "checkout", "--detach"], cwd=original_root, check=True)

    #
    subprocess.run(
        ["git", "worktree", "add", "-f", str(shadow_worktree_path), branch_name],
        cwd=original_root,
        check=True,
    )

    # Injects the runtime environment context and registers associated cleanup handlers to ensure resource release.
    def cleanup_worktree() -> None:
        """Clean up the Git shadow worktree and restore the original repository state.

        Performs a best-effort cleanup of resources created for a temporary Git
        worktree. This function is typically registered as a cleanup handler to be
        executed upon script completion or error.

        The cleanup sequence is as follows:
        1.  The current working directory is changed back to the original repository root.
        2.  The `git worktree remove -f` command is executed to forcefully delete the
            shadow worktree directory.
        3.  The `git checkout` command is run to restore the original branch in the
            main repository.

        This function depends on the `original_root`, `shadow_worktree_path`, and
        `original_branch` global variables, which must be populated before it is called.
        Exceptions encountered during the cleanup process are caught and logged to prevent
        the cleanup itself from crashing the application.

        Returns:
            None
        """
        try:
            os.chdir(original_root)
            subprocess.run(
                ["git", "worktree", "remove", "-f", str(shadow_worktree_path)],
                cwd=original_root,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "checkout", original_branch], cwd=original_root, check=False
            )
            logger.info(
                f"Shadow Workspace limpiado y rama {original_branch} restaurada en el origen."
            )
        except Exception as e:
            logger.error(f"Error limpiando shadow worktree: {e}")

    atexit.register(cleanup_worktree)

    ROOT = shadow_worktree_path
    rp.ROOT = shadow_worktree_path
    os.chdir(shadow_worktree_path)

    # Loads authorized human feedback associated with the current task, if such feedback exists.
    authorized_feedback_path = request_dir / "authorized_feedback.json"
    authorized_feedback_data = {}
    if authorized_feedback_path.exists():
        try:
            authorized_feedback_data = json.loads(
                authorized_feedback_path.read_text(encoding="utf-8")
            )
            authorized_feedback_path.unlink(
                missing_ok=True
            )  # The file is deleted immediately post-read to maintain a clean filesystem state and prevent residual artifacts.
            logger.info(
                "Se ha detectado y cargado feedback autorizado por el humano para esta ejecución."
            )
        except Exception as e:
            logger.warning(f"No se pudo cargar el feedback autorizado: {e}")

    for task in plan.get("tasks", []):
        logger.info(f"=== INICIANDO TAREA: {task['id']} ===")
        feedback: str | None = None

        # Injects human-provided feedback into the initial execution context if the feedback is pertinent to the current task.
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
                    # Persists the Action Gate state to a durable store to ensure operational continuity across process restarts.
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

    # Captures the pre-commit diff, which serves as the input for generating the commit signature.
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
    """Resolve the resume selector from parsed command-line arguments.

    Determines the unique identifier for resuming an operation based on the
    provided command-line arguments. The branch name is prioritized over the
    pull request number if both are specified.

    Args:
        args: The `argparse.Namespace` object containing the parsed command-line
            arguments. The namespace is expected to contain either a `branch`
            (str) or a `pr_number` (int) attribute.

    Returns:
        The branch name if present, otherwise the string representation of the
        pull request number.

    Raises:
        ValueError: If neither the `branch` nor `pr_number` attribute is
            present in the `args` namespace.
    """
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
    """Resume and reconcile an existing pull request based on a given policy.

    Orchestrates the resumption of a specified pull request. This process involves
    fetching the current state of the pull request, validating the local git
    repository environment, and creating a dedicated directory for operational
    artifacts. An execution plan is generated based on the provided policy and the
    pull request state. This plan is then applied using an external executor,
    which updates the branch and may merge the pull request if configured.

    Args:
        args: The parsed command-line arguments namespace. Must contain
            attributes for the pull request selector, `allow_dirty`,
            `executor_command`, and `skip_auto_merge`.
        policy: A dictionary defining the operational policy. The function inspects
            nested keys, such as `policy['pull_request']['auto_merge_mode']`,
            to control merge behavior.

    Returns:
        The path to the request directory created to store artifacts for this
        operation.

    Raises:
        ValueError: If the pull request specified by the selector cannot be found
            or if its corresponding local head branch does not exist.
        RuntimeError: If the git worktree is not clean and `args.allow_dirty` is
            False.
        FileNotFoundError: If the specified `args.executor_command` path does not
            correspond to an executable file.
    """
    pr_state = inspect_pull_request(resolve_resume_selector(args))
    ensure_existing_branch(pr_state["head_ref"])
    request_text = build_resume_request_text(pr_state)
    ensure_clean_worktree(allow_dirty=args.allow_dirty, request_text=request_text)
    request_dir = create_request_dir(policy, request_text)
    plan = prepare_resume_plan(policy, pr_state)
    plan_bundle = ProductOwnerAlternatives(alternatives=[cast(Any, plan)]).model_dump(
        mode="json"
    )
    save_plan_bundle(request_dir, request_text, plan_bundle)
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
    """Orchestrate the product owner AI from planning to execution.

    Serves as the main entry point for the command-line interface, handling
    argument parsing and dispatching to the appropriate workflow based on the
    specified command. The primary workflows are:

    - `run`: Generates a plan from a user request and executes the first
      plan alternative.
    - `plan`: Generates an execution plan from a user request and saves it
      to a directory without executing it.
    - `execute`: Executes a previously generated plan from a specified
      directory, optionally targeting a specific plan alternative.
    - `resume-pr`: Resumes an existing pull request process, typically for
      reconciliation after manual code changes.

    Args:
        argv: A list of command-line arguments. If None, arguments are parsed
            from `sys.argv`.

    Returns:
        An integer exit code: 0 for success, 1 for failures such as an
        ambiguous plan, a refusal to act, or other errors.

    Raises:
        FileNotFoundError: If the 'execute' command is used and the `plan.json`
            file is not found in the specified request directory.
    """
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

        plan_bundle_model = ProductOwnerAlternatives.model_validate_json(
            plan_path.read_text(encoding="utf-8")
        )
        plan_bundle = plan_bundle_model.model_dump(mode="json")

        if plan_bundle.get("is_ambiguous"):
            logger.error(
                f"Petición ambigua. Pregunta del planificador: {plan_bundle.get('clarification_question', 'Sin pregunta')}"
            )
            return 1

        if plan_bundle.get("refused"):
            logger.error(
                f"El planificador rechazó la petición: {plan_bundle.get('refusal_reason', 'Sin razón proporcionada')}"
            )
            return 1

        request_file = request_dir / "request.txt"
        if request_file.exists():
            req_text = request_file.read_text(encoding="utf-8").strip()
        else:
            # Provides a fallback mechanism to maintain compatibility with legacy request directory structures.
            req_text = plan_bundle.get("alternatives", [{}])[0].get("request_title", "")

        ensure_clean_worktree(allow_dirty=args.allow_dirty, request_text=req_text)
        if "alternatives" in plan_bundle:
            if not plan_bundle["alternatives"]:
                logger.info("El plan no contiene alternativas ejecutables.")
                return 0
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

    if plan.get("is_ambiguous"):
        logger.error(
            f"Petición ambigua. Pregunta del planificador: {plan.get('clarification_question', 'Sin pregunta')}"
        )
        return 1

    if plan.get("refused"):
        logger.error(
            f"El planificador rechazó la petición: {plan.get('refusal_reason', 'Sin razón proporcionada')}"
        )
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
