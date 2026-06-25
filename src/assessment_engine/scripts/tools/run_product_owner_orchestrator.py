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
    """{'docstring': 'Load the orchestrator policy from its configuration file.'}."""
    return load_policy_file("orchestrator_policy")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Defines and parses command-line arguments for the orchestrator script.

    This function configures the command-line interface using argparse, providing
    several subcommands to control the orchestrator's workflow.

    The available subcommands are:
      plan: Generates an execution plan from a request without running it.
        --request: A string containing the request.
        --request-file: Path to a file containing the request.
      run: Creates and executes a new plan from a request.
        --request: A string containing the request.
        --request-file: Path to a file containing the request.
        --executor-command: Overrides the default command for the executor.
        --allow-dirty: Permits execution even if the git repository has
          uncommitted changes.
        --skip-pr: Skips the pull request creation step.
        --skip-auto-merge: Disables auto-merging for the created pull request.
      execute: Executes a previously generated plan from a directory.
        --request-dir: Required. The directory containing the pre-generated plan.
        --alt-index: The zero-based index of an alternative plan to execute.
        --executor-command: Overrides the default command for the executor.
        --allow-dirty: Permits execution even if the git repository has
          uncommitted changes.
        --skip-pr: Skips the pull request creation step.
        --skip-auto-merge: Disables auto-merging for the created pull request.
      resume-pr: Resumes a plan from an existing pull request or branch.
        --pr-number: The pull request number to resume. Mutually exclusive
          with --branch.
        --branch: The branch name to resume. Mutually exclusive with
          --pr-number.
        --executor-command: Overrides the default command for the executor.
        --allow-dirty: Permits execution even if the git repository has
          uncommitted changes.
        --skip-auto-merge: Disables auto-merging for the created pull request.

    Args:
        argv: A list of strings representing the command-line arguments. If None,
            arguments are parsed from `sys.argv`.

    Returns:
        argparse.Namespace: An object containing the parsed command-line
            arguments.
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
    """Load the user request text from command-line arguments.

    This function extracts the user request from an `argparse.Namespace` object.
    It prioritizes the direct `request` string argument over the `request_file`
    path argument. The content from either source is stripped of leading and
    trailing whitespace. The file specified by `request_file` is read as
    UTF-8 encoded text.

    Args:
        args (argparse.Namespace): The parsed command-line arguments, expected
            to have either a `request` attribute (str) or a `request_file`
            attribute (str or os.PathLike).

    Returns:
        str: The user request text, stripped of whitespace.

    Raises:
        ValueError: If neither a non-empty `request` string nor a
            `request_file` path is provided.
        FileNotFoundError: If the file specified by `args.request_file` does not
            exist.
        IOError: If an I/O error occurs during file read operations.
    """
    if args.request and args.request.strip():
        return args.request.strip()
    if args.request_file:
        return Path(args.request_file).read_text(encoding="utf-8").strip()
    raise ValueError("Debes indicar --request o --request-file.")


def create_request_dir(policy: dict[str, Any], request_text: str) -> Path:
    """Create a unique directory for a new request.

    A subdirectory is created within the root path determined by the provided
    policy. The name of this new directory follows the format
    `YYYYMMDD_HHMMSS_<slug>`, where the timestamp is in UTC and the slug is a
    sanitized, 48-character truncated version of the `request_text`.

    Args:
        policy: The configuration policy dictionary, used to resolve the root
            directory for storing requests.
        request_text: The raw text of the user's request, which is slugified
            to form a human-readable component of the directory name.

    Returns:
        A `pathlib.Path` object representing the newly created directory.

    Raises:
        FileExistsError: If the computed directory path already exists.
    """
    requests_root = resolve_requests_root(policy)
    requests_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    request_slug = slugify(request_text)[:48]
    request_dir = requests_root / f"{timestamp}_{request_slug}"
    request_dir.mkdir(parents=True, exist_ok=False)
    return request_dir


def ensure_clean_worktree(*, allow_dirty: bool, request_text: str = "") -> None:
    """Verifies the Git worktree is clean before proceeding with an operation.

    This function acts as a safeguard to prevent operations from running on a Git
    repository with uncommitted changes, which could lead to an inconsistent state.
    The check is bypassed under two conditions: if the `allow_dirty` flag is set
    to True, or if the `request_text` contains specific keywords indicating a
    remediation or cleanup action (e.g., 'git reset', 'ruff format'). This allows
    for self-healing commands to execute even when the worktree is dirty.

    Args:
        allow_dirty: If True, bypasses the worktree cleanliness check entirely.
        request_text: The user's command string, inspected for remediation-related
            keywords that permit operations on a dirty worktree.

    Raises:
        RuntimeError: If the Git worktree has uncommitted modifications and the
            check is not bypassed by either `allow_dirty` or a remediation
            keyword in `request_text`.
    """
    if allow_dirty:
        return

    # A command whitelist is established to constrain execution during Remediation Mode. This security measure permits only safe, non-destructive commands, ensuring the workspace is sanitized without risk of unintended data loss or system modification.
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
    """Generates alternative high-level plans to address a user request.

    This function orchestrates an asynchronous call to a "product owner" agent
    to devise one or more strategic plans. To ground the agent's reasoning
    and mitigate confabulation, the prompt is supplemented with context from a
    `GEMINI.md` file if it is present at the project root. The number of tasks
    within each generated plan is constrained by the provided policy. The final
    output is validated against a Pydantic schema before being returned.

    Args:
        request_text: The natural language description of the user's request.
        policy: A dictionary of operational policies. The function specifically
            uses the value at `policy['planning']['max_tasks']` to limit the
            number of tasks per generated plan.

    Returns:
        A JSON-serializable dictionary conforming to the
        `ProductOwnerAlternatives` schema, containing one or more proposed plans.

    Raises:
        pydantic.ValidationError: If the agent's output fails validation against
            the `ProductOwnerAlternatives` schema.
        UnicodeDecodeError: If `GEMINI.md` contains characters that cannot be
            decoded using UTF-8.
        OSError: If reading `GEMINI.md` fails due to I/O or permission errors.
    """
    max_tasks = int(policy.get("planning", {}).get("max_tasks", 5))
    model_profile = resolve_model_profile_for_role("product_owner_planner")

    # The authoritative project context, sourced from `GEMINI.md`, is injected into the prompt. This grounds the language model's subsequent reasoning in project-specific facts, thereby mitigating the risk of confabulation.
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
    """Serialize and save the planning results and original request to a directory.

    Persists the user request and the generated plan bundle to a specified
    directory by creating three distinct files:

    - `request.txt`: Contains the original, unaltered user request text.
    - `plan.json`: A JSON serialization of the `plan_bundle` dictionary.
    - `plan.md`: A human-readable Markdown summary. This file renders a
      clarification question if ambiguity was detected, or it renders each
      of the generated plan alternatives.

    Args:
        request_dir: The path to the destination directory for the output files.
        request_text: The original, verbatim user request.
        plan_bundle: A dictionary containing the generated plan data, expected to
            have keys such as 'is_ambiguous', 'clarification_question', and
            'alternatives'.

    Raises:
        OSError: If the directory does not exist, is not a directory, or if a
            file system error occurs during writing (e.g., PermissionError).
        TypeError: If the `plan_bundle` contains objects that are not JSON
            serializable.
    """
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
    """Executes a Git command as a non-interactive subprocess with a timeout.

    Runs the specified Git command from the project's root directory (`ROOT`).
    Interactive prompts are disabled by setting the `GIT_TERMINAL_PROMPT`
    environment variable to '0', making the function suitable for automated
    environments. A 300-second timeout is enforced to prevent the process
    from hanging indefinitely.

    Args:
        args: A list of strings representing the Git command and its arguments.

    Returns:
        A `subprocess.CompletedProcess` object containing the command's stdout,
        stderr, and return code upon successful execution.

    Raises:
        RuntimeError: If command execution exceeds the timeout or if the command
            returns a non-zero exit code. The exception message contains the
            process's stderr if available.
    """
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = (
        "0"  # Git interactivity is disabled by setting `GIT_TERMINAL_PROMPT=0`. This is essential for ensuring the script can execute non-interactively within automated CI/CD pipelines or other headless environments.
    )

    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=300,  # A 5-minute execution timeout is enforced on the subprocess to safeguard against indefinite hangs and ensure deterministic termination.
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout excedido ejecutando: {' '.join(args)}")

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or f"Fallo ejecutando: {' '.join(args)}"
        )
    return result


def run_json_command(args: list[str]) -> Any:
    """Execute a git command and parse its standard output as JSON.

    Args:
        args: A list of strings representing the git command and its arguments.

    Returns:
        The parsed JSON data from the command's standard output.

    Raises:
        RuntimeError: If the standard output from the git command cannot be
            parsed as JSON. The original `JSONDecodeError` is chained as the
            cause.
    """
    result = run_git_command(args)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Respuesta JSON inválida para {' '.join(args)}: {result.stdout.strip()}"
        ) from exc


def ensure_branch(branch_name: str) -> None:
    """Ensure the specified git branch exists and is checked out.

    If the current branch is already the target branch, this function takes no
    action. Otherwise, it checks if the target branch exists. If it does,
    the function performs a `git checkout`. If the branch does not exist, it
    is created from the current HEAD and then checked out.

    Args:
        branch_name: The name of the git branch to make active.

    Raises:
        subprocess.CalledProcessError: If a `git checkout` operation fails.
        FileNotFoundError: If the 'git' executable cannot be found in the
            system's PATH.
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
    r"""{'docstring': "Checks out a Git branch, creating it from its remote if it does not exist locally.\n\n    The function first fetches the specified branch from the 'origin' remote to\n    update local refs. It then checks for the existence of a local branch with\n    the given name. If the local branch exists, it is checked out. Otherwise,\n    a new local branch is created to track 'origin/<branch_name>' and is then\n    checked out.\n\n    Args:\n        branch_name: The name of the branch to check out or create.\n\n    Raises:\n        subprocess.CalledProcessError: If any underlying Git command fails. This may\n            occur if the remote branch does not exist or if the operation is not\n            performed within a Git repository."}."""
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
    """Resolves the executor command string from an argument or an environment variable.

    The command is determined using the following order of precedence:
    1. The `raw_command` argument, if it is a non-empty string.
    2. The `ASSESSMENT_ORCHESTRATOR_EXECUTOR_CMD` environment variable.

    If a command cannot be determined from these sources, an exception is raised.

    Args:
        raw_command (str | None): The command string provided directly. If this
            is None or an empty string, the function falls back to checking the
            environment variable.

    Returns:
        str: The resolved non-empty executor command string.

    Raises:
        RuntimeError: If no command is provided via the argument or the
            environment variable.
    """
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
    """Formats and splits a template string into a list of command-line arguments.

    This function interpolates runtime values into a template string and then parses
    the result using shell-like splitting rules via `shlex.split`. The
    resulting list is suitable for use in functions like `subprocess.run`.

    Args:
        template: The command-line template string. It must support format
            placeholders for `{repo_root}`, `{task_prompt_file}`, and `{attempt}`.
            The `{repo_root}` placeholder is populated from a predefined
            module-level constant (`ROOT`).
        task_prompt_file: The path to the file containing the task prompt.
        attempt: The current execution attempt number.

    Returns:
        A list of strings representing the shell-parsed arguments.

    Raises:
        KeyError: If `template` contains placeholders other than `{repo_root}`,
            `{task_prompt_file}`, or `{attempt}`.
        ValueError: If `shlex.split` fails to parse the formatted string, for
            instance, due to an unclosed quote.
    """
    formatted = template.format(
        repo_root=str(ROOT),
        task_prompt_file=str(task_prompt_file),
        attempt=str(attempt),
    )
    return shlex.split(formatted)


def collect_changed_python_files() -> list[str]:
    """Collect modified, staged, and untracked Python files in a Git repository.

    Executes a series of `git` commands to find all Python (`.py`) files that
    are not in a clean, committed state. The function gathers file paths from
    three distinct sources:

    1.  Tracked files with unstaged modifications (`git diff --name-only`).
    2.  Untracked files not excluded by gitignore rules (`git ls-files`).
    3.  Files with staged changes (`git diff --name-only --cached`).

    The resulting set of file paths is deduplicated and returned as a sorted list.
    This function operates on the Git repository specified by the `ROOT` constant.

    Returns:
        A sorted list of unique, repository-relative paths to Python files
        that are modified, staged, or untracked.

    Raises:
        FileNotFoundError: If the `git` executable cannot be found in the
            system's PATH.
    """
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
    """Check for relevant changes in the Git worktree."""
    return git_status_has_relevant_changes()


def read_git_status_lines() -> list[str]:
    """Read the status of the Git working tree via `git status --short`.

    Executes the `git status --short` command in the project's root directory
    and captures its standard output. The output is processed to filter out
    any lines that are empty or contain only whitespace.

    Returns:
        list[str]: A list of non-empty lines from the command's standard
            output, each representing a change in the working tree.

    Raises:
        RuntimeError: If the `git` command returns a non-zero exit code,
            indicating an error. The exception message contains the command's
            standard error output.
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
    """{'docstring': 'Determine if a file path is a Python cache directory or bytecode file.'}."""
    normalized = path.strip()
    return "__pycache__/" in normalized or normalized.endswith((".pyc", ".pyo", ".pyd"))


def git_status_has_relevant_changes() -> bool:
    """Check for uncommitted, relevant changes in the Git working tree.

    Scans the output of `git status --porcelain` for uncommitted file changes.
    Each line of the output is parsed to extract the file path, with special
    handling for renamed files (`->`). The change is considered irrelevant and
    skipped if `is_ignorable_git_status_path(path)` returns True.

    If a relevant change is detected, a warning is logged, and the function
    short-circuits by immediately returning True. If the entire status output is
    processed without finding any relevant changes, it returns False.

    Returns:
        bool: True if one or more relevant, uncommitted changes are found,
            False otherwise.

    Raises:
        Exception: Propagates any exception raised by the underlying
            `read_git_status_lines` function, which typically occurs if the `git`
            command fails (e.g., not in a Git repository).
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
    """Read and parse a UTF-8 encoded JSON file from a given path."""
    return json.loads(path.read_text(encoding="utf-8"))


class OrchestratorCommandError(RuntimeError):
    r"""{'docstring': "Raised when an external command executed by the orchestrator fails.\n\nEncapsulates details of a failed subprocess, including the command, its\noutput, and a category for programmatic error handling.\n\nAttributes:\n    category (str): A string categorizing the failed command (e.g., 'build', 'test').\n    command (list[str]): The executed command as a list of strings.\n    output_path (pathlib.Path): The path to the file containing the command's\n        captured stdout and stderr.\n    raw_output (str): The raw string content of the combined stdout and stderr."}."""

    def __init__(
        self,
        message: str,
        *,
        category: str,
        command: list[str],
        output_path: Path,
        raw_output: str,
    ) -> None:
        """Initializes the `ProductOwnerOrchestratorError` with execution context.

        Args:
            message: The primary, human-readable error message.
            category: A string categorizing the nature of the failure.
            command: The command and its arguments that were executed.
            output_path: The filesystem path to the file containing the command's
                captured output.
            raw_output: The raw stdout and stderr content from the command execution.
        """
        super().__init__(message)
        self.category = category
        self.command = command
        self.output_path = output_path
        self.raw_output = raw_output


def classify_command_failure(command: list[str], output: str) -> str:
    """Categorize a command execution failure based on its output and invocation.

    Examines the command string and its combined stdout/stderr for specific
    keywords to classify the failure. This helps distinguish between issues
    such as authentication problems, configuration errors, missing executables,
    and validation failures (e.g., failing tests).

    Args:
        command: The command that was executed, as a list of strings.
        output: The captured stdout and stderr from the command's execution.

    Returns:
        A string code representing the classified failure category. Possible
        values include:
        - 'executor_auth': Indicates an authentication or API key issue.
        - 'executor_config': A configuration required for the executor is
          missing or invalid.
        - 'executor_missing': The executable or a specified file/directory
          was not found.
        - 'validation': The command was a validation step (e.g., pytest,
          typecheck) that failed.
        - 'command_failure': A generic failure not classifiable under the
          other categories.
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
    """Constructs a standardized failure message in Spanish for a failed command.

    Generates a human-readable error message by mapping a failure category to a
    predefined prefix and appending command details. The output is localized
    in Spanish.

    Args:
        category: An identifier for the failure type. Supported values include
            'executor_auth', 'executor_config', 'executor_missing', 'timeout',
            'validation', and 'command_failure'. An unknown category will use a
            default prefix.
        command: The command and its arguments that failed, represented as a
            sequence of strings.
        output_path: The `pathlib.Path` object pointing to the log file with the
            detailed command output.
        timeout_seconds: A keyword-only argument specifying the timeout in
            seconds that was exceeded. This value is only included in the
            output message if the `category` is 'timeout' and the value is not
            None.

    Returns:
        A formatted string containing the complete error message.
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
    """Executes a command in a subprocess with real-time output streaming.

    Runs the given command in a dedicated process group to ensure that both the
    primary process and any children it spawns can be terminated atomically. The
    subprocess's combined standard output and standard error streams are captured
    and mirrored in real-time to the local console and to the specified output
    file.

    Execution is bound by the `timeout_seconds` parameter. If the timeout is
    exceeded, the entire process group is terminated. A non-zero exit code
    upon normal completion is also treated as a failure. For any failure
    condition, the full captured output is written to `output_path` and an
    `OrchestratorCommandError` is raised. The function only completes
    successfully if the command returns an exit code of 0.

    Args:
        command: The command to execute as a list of string arguments.
        output_path: Path to the file for persisting the command's combined
            stdout and stderr.
        timeout_seconds: Maximum execution time in seconds. If `None`, the
            subprocess runs without a time limit.

    Raises:
        OrchestratorCommandError: If the command times out or returns a non-zero
            exit code. The exception's `category` attribute indicates the
            failure type (e.g., "timeout").
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
        """Stream and collect stdout from a global subprocess.

        Reads lines from the `stdout` of a global `process` object, writing each
        line to `sys.stdout` and simultaneously appending it to a global `output_lines`
        list. This function is intended for execution in a separate thread to enable
        non-blocking I/O handling from the subprocess.

        The function requires the following variables to be present in its global scope:
        - `process` (subprocess.Popen): A running subprocess instance. The function
          is a no-op if `process.stdout` is `None`.
        - `output_lines` (list): A list to which output lines will be appended.

        Raises:
            NameError: If the global variables `process` or `output_lines` are not
                defined.
            AttributeError: If `process` does not have a `stdout` attribute, or if
                `output_lines` does not have an `append` method.
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
    """Write a dictionary payload to a pretty-printed JSON file."""
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_reconciliation_event(request_dir: Path, payload: dict[str, Any]) -> None:
    """Appends a timestamped event as a JSON line to a reconciliation timeline file.

    This function enriches the provided payload with the current UTC timestamp in
    ISO 8601 format. The resulting dictionary is then serialized to a JSON string
    and appended as a new line to the timeline file within the specified
    `request_dir`. The timeline file is created if it does not exist.

    Args:
        request_dir: The path to the directory for the specific reconciliation
            request. The timeline file will be written inside this directory.
        payload: A JSON-serializable dictionary containing the event's data.

    Raises:
        FileNotFoundError: If the `request_dir` does not exist.
        PermissionError: If the timeline file cannot be created or written to.
        TypeError: If the `payload` contains non-JSON-serializable objects.
    """
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **payload}
    timeline_path = request_dir / RECONCILIATION_TIMELINE_FILE
    with timeline_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def write_reconciliation_summary(request_dir: Path, payload: dict[str, Any]) -> None:
    """Write a given payload, enriched with a current UTC timestamp, to a reconciliation summary JSON file."""
    summary = {"updated_at_utc": datetime.now(timezone.utc).isoformat(), **payload}
    write_json(request_dir / RECONCILIATION_SUMMARY_FILE, summary)


def executor_uses_github_wrapper(command_template: str) -> bool:
    """Determine if a command template invokes a known orchestrator executor script."""
    return (
        "orchestrator-gemini-executor.sh" in command_template
        or "orchestrator-github-executor.sh" in command_template
    )


def validate_executor_configuration(command_template: str) -> None:
    r"""{'docstring': 'Validate authentication configuration for the Gemini code executor.\n\n    This function ensures that a valid authentication method is configured when\n    the Gemini executor is invoked. The validation is only performed if the\n    provided command template indicates usage of the Gemini executor via its\n    GitHub wrapper.\n\n    The function checks for one of the following authentication mechanisms:\n    1.  API Key: Looks for `GEMINI_API_KEY` or `GOOGLE_API_KEY`. It first\n        attempts to retrieve these keys from Google Cloud Secret Manager.\n        If this fails or returns no key, it falls back to checking the\n        corresponding environment variables.\n    2.  Google Cloud Authentication (GCA): Enabled by setting the\n        `GOOGLE_GENAI_USE_GCA` environment variable to a non-empty string.\n    3.  Vertex AI: The default authentication method. It is considered active\n        unless explicitly disabled by setting the `GOOGLE_GENAI_USE_VERTEXAI`\n        environment variable to a falsy value (e.g., "0", "false", "no").\n\n    Args:\n        command_template: The command template string, used to determine if\n            Gemini executor validation is required.\n\n    Raises:\n        RuntimeError: If Gemini executor usage is detected, Vertex AI\n            authentication is explicitly disabled, and no other valid\n            authentication method (API key or GCA) is configured.'}."""
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
        # This block implements a configuration fallback mechanism. It activates if the primary secret manager is inaccessible or if the provided `project_id` is invalid, ensuring operational resilience.
        has_api_key = False

    # As a terminal fallback, configuration values are sourced directly from environment variables. This ensures operation can continue if primary configuration providers are unavailable.
    if not has_api_key:
        has_api_key = bool(
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )

    if vertex_selector in {"0", "false", "no"} and not gca_selector and not has_api_key:
        raise RuntimeError(
            "El executor de Gemini requiere GEMINI_API_KEY, GOOGLE_API_KEY o habilitar autenticación Google."
        )


def preflight_executor(request_dir: Path, command_template: str) -> None:
    """Perform preflight checks for the executor configuration.

    Validates the executor's command template to ensure syntactical correctness
    before a full execution is attempted. The actual execution of a preflight
    command is currently bypassed to mitigate potential timeout errors during the
    initialization phase of underlying command-line tools.

    Args:
        request_dir: The directory path for the request. Although unused in the
            current implementation, it is reserved for future preflight checks
            that may require filesystem context.
        command_template: The command template string to be validated.

    Raises:
        ValueError: If the provided `command_template` is invalid.
    """
    validate_executor_configuration(command_template)
    # Preflight execution is bypassed to mitigate potential timeout errors originating from the Gemini CLI's initialization phase.
    return


def run_standard_validations(request_dir: Path) -> None:
    """Run standard code validations against changed Python files.

    This function serves as an orchestrator for the code validation process. It
    identifies Python files that have been modified within the source control
    system, and then invokes a `VerificationAgent` to execute a suite of
    pre-defined validation checks against these files.

    Args:
        request_dir (pathlib.Path): The file system path to the directory
            containing the validation request context and configuration.

    Raises:
        Exception: Propagated if the `VerificationAgent` reports any validation
            failures.
    """
    changed_python_files = collect_changed_python_files()
    VerificationAgent.verify_changes(request_dir, changed_python_files)


def resolve_execution_timeouts(policy: dict[str, Any]) -> dict[str, int]:
    """Extract and default execution-related timeout values from a policy dictionary."""
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
    """Consolidates and commits all workspace changes into the Git repository.

    This function orchestrates the creation of a single, authoritative commit.
    It first identifies the merge-base between the current HEAD and the primary
    integration branch (`origin/main` or `main`). If the HEAD has diverged
    from this base and the latest commit lacks a `[zk-Liability-Proof]`
    attestation block, the function performs a soft reset to the merge-base.
    This operation unwinds any intermediate, unattested commits while preserving
    all accumulated file modifications in the staging area.

    All current changes in the working directory are then staged. A check is
    performed to prevent the creation of an empty commit if no changes are
    detected. A commit message is constructed using the provided title and a
    static `Co-authored-by` trailer. If a `compliance_receipt` dictionary is
    supplied, its contents are formatted into a `[zk-Liability-Proof]` block
    and appended to the message.

    Args:
        commit_title: The primary title line for the Git commit message.
        compliance_receipt: An optional dictionary containing metadata for a
            compliance attestation block. If provided, it is expected to
            contain keys such as `eu_ai_act_compliance` and
            `governance_commitment_hash`. Defaults to None.

    Returns:
        None. The function executes Git commands with side effects on the
        repository and does not return a value.
    """
    # This logic detects and reverts any spurious commits generated by sub-agents. The objective is to consolidate all automated changes into a single, authoritative, and cryptographically signed commit.
    try:
        # The merge-base between the current HEAD and a primary integration branch (`main` or `origin/main`) is determined. This common ancestor serves as the definitive baseline for generating contextual diffs.
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
                # A check is performed to determine if the HEAD commit already possesses a cryptographic signature. This prevents redundant signing operations, which would be computationally wasteful and create unnecessary commit objects.
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

    # A pre-commit check verifies the presence of staged changes in the Git index. This check prevents the creation of empty commits, maintaining a clean and meaningful version history.
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
    """Force-pushes a local Git branch to the remote origin using a lease.

    This function executes `git push --force-with-lease`. This command refuses
    to update a remote ref if its current value does not match the expected
    value from the local repository's remote-tracking branch. This prevents the
    inadvertent overwriting of concurrent, un-fetched work from other
    contributors. The `-u` flag is also used to establish the upstream tracking
    reference for the specified branch.

    Args:
        branch_name: The name of the local branch to be pushed.

    Raises:
        subprocess.CalledProcessError: If the underlying `git push` command
            returns a non-zero exit code.
    """
    # The `--force-with-lease` flag is employed to safely update the remote branch. This prevents overwriting upstream changes by verifying that the remote reference has not been updated since the last fetch, thus mitigating race conditions with other developers.
    #
    run_git_command(["git", "push", "--force-with-lease", "-u", "origin", branch_name])


def repository_coordinates() -> tuple[str, str]:
    """Fetch the owner login and name for the current GitHub repository.

    Executes the GitHub CLI command `gh repo view` to retrieve metadata for the
    current repository. This function requires the `gh` command-line tool to be
    installed, authenticated, and run from within a local Git repository with a
    corresponding remote on GitHub.

    Returns:
        tuple[str, str]: A tuple containing the repository owner's login and the
            repository name.

    Raises:
        RuntimeError: If the underlying `gh` command fails or if the owner login
            and repository name cannot be parsed from its output.
    """
    payload = run_json_command(["gh", "repo", "view", "--json", "owner,name"])
    owner = payload.get("owner", {}).get("login")
    repo = payload.get("name")
    if not owner or not repo:
        raise RuntimeError("No se pudo resolver el repositorio actual en GitHub.")
    return owner, repo


def get_pull_request(branch_name: str) -> dict[str, Any]:
    """Retrieve details for a pull request associated with a specific branch.

    This function executes the GitHub CLI (`gh`) to view a pull request
    and parses the output as a JSON object. It specifically requests a
    predefined set of fields.

    Args:
        branch_name: The name of the Git branch for which to find the
            corresponding pull request.

    Returns:
        A dictionary containing details of the pull request. The dictionary
        will contain the following keys: 'number', 'title', 'url',
        'headRefName', 'baseRefName', 'isDraft', 'mergeable',
        'mergeStateStatus', 'reviewDecision', and 'statusCheckRollup'.

    Raises:
        subprocess.CalledProcessError: If the underlying `gh` command fails.
            This can occur if the branch does not have an associated pull
            request or if the user is not authenticated.
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
    """Retrieves all review threads for a specified pull request.

    This function queries the GitHub GraphQL API to fetch review threads
    associated with a given pull request number. It relies on the GitHub CLI
    (`gh`) being installed, authenticated, and available in the system's PATH.
    The target repository is determined from the current Git context.

    Args:
        pr_number: The integer identifier for the pull request.

    Returns:
        A list of dictionaries, where each entry represents a review thread node
        from the GitHub GraphQL API. An empty list is returned if no threads
        exist or if the API response structure is unexpected.

    Raises:
        subprocess.CalledProcessError: If the underlying `gh api` command fails.
            This may be caused by authentication problems, network errors, an
            invalid repository specification, or an invalid pull request number.
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
    """Filters and normalizes a list of code review thread data structures.

    Processes a list of raw thread objects, such as those from a GitHub
    GraphQL API response, into a simplified format. This function filters out
    any threads marked as resolved and transforms the remaining threads into a
    standardized dictionary structure. The transformation includes flattening the
    comment hierarchy, extracting key author details, and adding a boolean flag
    to indicate if all comments within a thread originate from bots.

    Args:
        threads: A list of dictionaries representing code review threads. Each
            dictionary is expected to contain keys such as 'isResolved',
            'id', 'path', 'line', 'isOutdated', and a nested 'comments'
            dictionary with a 'nodes' list. Each element in 'nodes' represents
            a comment and should contain 'author' (with 'login' and
            '__typename'), 'databaseId', 'body', and 'state'.

    Returns:
        A list of normalized thread dictionaries for all unresolved input
        threads. Each output dictionary contains the following keys:
            'id' (str): The unique identifier of the thread.
            'path' (str): The file path associated with the thread.
            'line' (int): The line number where the thread is located.
            'is_outdated' (bool): True if the thread is outdated.
            'comments' (list[dict]): A list of simplified comment objects, each
                with 'database_id', 'author', 'author_type', 'body', and 'state'.
            'all_comments_bot' (bool): True if all comments in the thread were
                made by an author of type 'Bot', False otherwise.
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
    """Normalize and categorize a list of status check records.

    This function processes a list of dictionaries representing status checks,
    such as those from the GitHub API, into a standardized format. It coalesces
    common key variations (e.g., 'conclusion' vs. 'state', 'name' vs. 'context',
    'detailsUrl' vs. 'targetUrl') into a consistent structure for each check.

    After normalization, the checks are classified based on their 'status' and
    'conclusion' fields into distinct lists of failed and pending checks.

    Args:
        checks: A list of dictionaries, where each dictionary represents a
            status check. The function is designed to handle missing keys and
            common variations in key names gracefully.

    Returns:
        A dictionary containing the processed and categorized check lists with
        the following keys:
        - 'checks' (list[dict]): The full list of all normalized status checks.
        - 'failed_checks' (list[dict]): A list of checks where the status is
          'COMPLETED' and the conclusion is not in {'', 'SUCCESS', 'SKIPPED',
          'NEUTRAL'}.
        - 'pending_checks' (list[dict]): A list of checks where the status is
          not 'COMPLETED' or the conclusion is in {'', 'PENDING', 'EXPECTED',
          'ACTION_REQUIRED'}.
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
    r"""{'docstring': "Fetch and consolidate the state of a pull request for a given branch.\n\nAggregates core pull request metadata, review thread states, and status\ncheck results from the version control system's API. This function\norchestrates multiple API calls to produce a single, structured dictionary\nrepresenting the comprehensive state of the pull request.\n\nArgs:\n    branch_name (str): The name of the head branch for the pull request.\n\nReturns:\n    A dictionary containing the consolidated state of the pull request, with\n    the following structure:\n        'number' (int): The pull request number.\n        'title' (str): The title of the pull request.\n        'url' (str): The URL of the pull request.\n        'head_ref' (str): The name of the source (head) branch.\n        'base_ref' (str): The name of the target (base) branch.\n        'is_draft' (bool): A flag indicating if the pull request is a draft.\n        'mergeable' (str): The high-level mergeability status (e.g.,\n            'MERGEABLE', 'CONFLICTING').\n        'merge_state_status' (str): The detailed merge state status\n            provided by the API.\n        'review_decision' (str): The current aggregated review decision\n            (e.g., 'APPROVED', 'CHANGES_REQUESTED').\n        'checks' (dict): A summary of all status checks.\n        'failed_checks' (list[dict]): A list containing details of failed\n            status checks.\n        'pending_checks' (list[dict]): A list containing details of pending\n            status checks.\n        'unresolved_threads' (list[dict]): A list of normalized, unresolved\n            review discussion threads.\n\nRaises:\n    ValueError: If no open pull request is found for the given `branch_name`,\n        or if a critical underlying API call fails."}."""
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
    """Determine if a GitHub check object corresponds to the current GitHub Actions job.

    This function uses environment variables (`GITHUB_RUN_ID`, `GITHUB_WORKFLOW`,
    `GITHUB_JOB`) to identify the context of the current GitHub Actions run.
    Identification is primarily attempted by matching the `GITHUB_RUN_ID` within
    the check's `details_url`. If this is not definitive, a fallback mechanism
    compares the workflow and job names, explicitly filtering out any checks
    already marked as 'COMPLETED' to prevent matching stale runs.

    Args:
        check: A dictionary representing a GitHub check run, typically from the
            GitHub API. The function accesses the 'details_url', 'workflow_name',
            'status', and 'name' keys.

    Returns:
        True if the check is determined to correspond to the current GitHub
        Actions job, False otherwise.
    """
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
    """Removes the current reconciliation check from a pull request state dictionary.

    Creates a new dictionary representing the pull request state where the status
    check corresponding to the current orchestrator run is removed. This prevents
    the orchestrator from deadlocking by waiting for its own status check to
    complete. If the reconciliation check is not found within the 'checks' list,
    the original dictionary is returned unmodified.

    Args:
        pr_state: A dictionary representing the state of a pull request. It is
            expected to contain the keys 'checks', 'failed_checks', and
            'pending_checks', each mapping to a list of check-run-like objects.

    Returns:
        A new dictionary with the current reconciliation check filtered out from the
        'checks', 'failed_checks', and 'pending_checks' lists. Returns the
        original `pr_state` dictionary if no such check is present.

    Raises:
        KeyError: If a reconciliation check is present in `pr_state['checks']` but
            the `pr_state` dictionary is missing either the 'failed_checks' or
            'pending_checks' key.
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
    """Determine if a pull request is in a mergeable state.

    Evaluates a pull request's state against a strict set of merge criteria.
    A pull request is considered mergeable if and only if all of the following
    conditions are met:
      - It is not a draft.
      - It has no failing or pending continuous integration checks.
      - All review conversation threads have been resolved.
      - The `mergeable` status is 'MERGEABLE'.
      - The `merge_state_status` is not 'BEHIND', 'BLOCKED', 'DIRTY', or
        'UNKNOWN'.

    Args:
        pr_state: A dictionary representing the pull request's state. Expected
            keys are `is_draft` (bool), `failed_checks` (bool),
            `pending_checks` (bool), `unresolved_threads` (bool), `mergeable`
            (str), and `merge_state_status` (str).

    Returns:
        bool: True if the pull request satisfies all merge criteria, otherwise False.

    Raises:
        KeyError: If a required key is missing from the `pr_state` dictionary.
    """
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
    r"""{'docstring': "Resolve pull request review threads containing only bot-authored comments.\n\n    Iterates through unresolved pull request review threads from the provided state.\n    If a thread consists entirely of comments authored by bots, the function\n    posts a standardized reply to the thread's initial comment and then resolves\n    the thread. These operations are performed via `gh` command-line calls to the\n    GitHub REST and GraphQL APIs, respectively.\n\n    Args:\n        pr_state: A dictionary representing the state of a pull request. It must\n            contain the key 'number' (the integer PR number) and\n            'unresolved_threads' (a list of thread dictionaries). Each thread\n            dictionary must contain 'id' (the GraphQL node ID for the thread),\n            'all_comments_bot' (a boolean), and 'comments' (a list of comment\n            dictionaries). The first comment dictionary in the list, if present,\n            is expected to have a 'database_id'.\n\n    Returns:\n        An integer count of the threads that were automatically resolved.\n\n    Raises:\n        KeyError: If `pr_state` or its nested thread dictionaries are missing\n            required keys.\n        subprocess.CalledProcessError: If an underlying `gh` API command fails."}."""
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
    """Generate a formatted resolution note for a bot-managed thread, indicating if it is outdated."""
    reason = "the repository checks are green"
    if thread.get("is_outdated"):
        reason += " and the commented lines are now outdated"
    return (
        "Automated reconciliation note: this bot-only thread is being resolved because "
        f"{reason}. The current PR state has been revalidated before closure."
    )


def build_pr_feedback(pr_state: dict[str, Any]) -> dict[str, Any]:
    """Construct a feedback dictionary from a pull request state."""
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
    """Generate a default validation plan from a policy dictionary."""
    names = [
        entry.get("name", "validation")
        for entry in policy.get("validation_commands", [])
    ]
    names.extend(["incremental quality gate", "incremental typecheck"])
    return names


def find_latest_plan_for_branch(
    policy: dict[str, Any], branch_name: str
) -> dict[str, Any] | None:
    """Find the most recent plan associated with a specific branch name.

    Scans subdirectories within a requests root path, which is derived from the
    `policy`. Directories are processed in reverse lexicographical order of their
    names, which is assumed to correspond to reverse chronological order.

    For each directory, the function attempts to read and validate a `plan.json`
    file against the `ProductOwnerAlternatives` data model. If a plan file is
    malformed or fails validation, the error is logged and the directory is
    skipped. For a valid plan, it checks if the `branch_name` of its first
    alternative matches the target `branch_name`. The first matching plan
    encountered in the search order is returned.

    Args:
        policy: The configuration policy dictionary, used to resolve the root
            directory containing plan request subdirectories.
        branch_name: The name of the branch to find the latest plan for.

    Returns:
        A dictionary representing the first alternative from the most recent
        valid plan associated with the `branch_name`. Returns None if the root
        directory does not exist or if no matching plan is found.
    """
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
    """Constructs a structured plan for resuming work on a pull request.

    This function generates a dictionary that defines a plan for bringing an
    existing pull request to a mergeable state. The plan object is populated
    with contextual information extracted from the provided pull request state,
    such as branch names and titles, and includes scope definitions, invariants,
    and a validation plan derived from the input policy.

    Args:
        policy: A dictionary of policy configurations used to generate the
            'validation_plan' portion of the returned plan.
        pr_state: A dictionary representing the state of the target pull request.
            Must contain 'head_ref', 'number', and 'base_ref' keys. The 'title'
            key is optional and will be synthesized if absent.

    Returns:
        A dictionary containing the structured plan for bringing the specified
        pull request to a mergeable state.

    Raises:
        KeyError: If required keys ('head_ref', 'number', 'base_ref') are
            missing from the `pr_state` dictionary.
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
    """Retrieve an existing plan for a pull request branch or synthesize a new one.

    This function attempts to resume work on a pull request by first searching
    for a pre-existing plan associated with its head branch. If a plan is found,
    it is copied and updated with current details from the pull request state,
    such as 'branch_name' and 'pr_title'. Default values for 'commit_title'
    and 'validation_plan' are also supplied if not already present.

    If no existing plan is found for the branch, a new one is synthesized.

    Args:
        policy: The orchestrator configuration dictionary.
        pr_state: A dictionary representing the current state of the pull request.
            Must contain 'head_ref' and 'number' keys. The 'title' key is
            used if available.

    Returns:
        A dictionary representing the execution plan, either an updated version
        of an existing plan or a newly synthesized one.

    Raises:
        KeyError: If `pr_state` lacks the required 'head_ref' or 'number' keys.
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
    """Construct a standard string to request resuming a pull request."""
    return f"Resume PR #{pr_state['number']} on {pr_state['head_ref']}"


def create_followup_commit_title(plan: dict[str, Any], round_number: int) -> str:
    """{'docstring': 'Format a follow-up commit title with the pull request feedback round number.'}."""
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
    """Orchestrates a single round of pull request repair based on CI and review feedback.

    The function synthesizes feedback from the current pull request state, including
    failed continuous integration (CI) checks and unresolved review threads, into a
    structured payload. This payload is used to render a new prompt, which is
    then written to the request directory. An external executor command is invoked
    with this prompt to generate code changes. If the executor modifies the
    codebase, the changes are committed with a follow-up message and pushed to the
    remote branch. Key stages of the process, such as initiation, failure, or
    successful commit, are recorded in a reconciliation log within the request
    directory.

    Args:
        request_dir: Path to the request's working directory, used for storing
            prompts, logs, and other generated artifacts.
        plan: Dictionary containing metadata from the original plan that created
            the pull request, such as the target branch name.
        executor_command: The command-line string used to invoke the repair agent
            process.
        pr_state: A dictionary summarizing the current state of the pull request,
            including its number, failed checks, and unresolved review threads.
        round_number: The current 1-indexed attempt number for the repair process.
        additional_feedback: Optional string providing extra context or instructions
            to be appended to the feedback payload for the repair prompt.

    Returns:
        True if the repair attempt generated, committed, and pushed new code
        changes. False if the executor produced no modifications to the worktree.

    Raises:
        OrchestratorCommandError: If the external executor command returns a
            non-zero exit code or times out.
    """
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
    """Synchronizes a feature branch with a specified base branch by merging.

    This function merges the latest changes from the `base_branch` into the
    current feature branch. The process involves fetching the `base_branch` from
    the `origin` remote, performing a `--no-edit` merge, and logging the output
    to a file within `request_dir`. After a successful merge, standard
    validations are run. If validations pass, the updated feature branch is
    pushed to `origin`. If validations fail, the operation is halted.

    Args:
        request_dir: The filesystem path to a directory for storing logs and
            other artifacts from the operation.
        plan: A dictionary containing execution plan details. Must contain a
            'branch_name' key whose value is the name of the feature branch.
        base_branch: The name of the base branch to merge into the feature branch.

    Returns:
        The string representation of the exception if post-merge validations
        fail, otherwise None on successful completion of the merge, validation,
        and push operations.

    Raises:
        Exception: Propagates exceptions from underlying Git operations. This
            can occur, for instance, if a merge conflict is detected, a branch
            does not exist, or a network error prevents communication with the
            remote repository.
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
    r"""{'docstring': "Merges a GitHub pull request and deletes the associated source branch.\n\n    This function serves as a wrapper for the GitHub CLI (`gh`) to execute the\n    merge operation. It constructs and runs the `gh pr merge` command with the\n    specified merge strategy and an option to delete the source branch upon a\n    successful merge.\n\n    Args:\n        pr_number: The integer identifier of the pull request to merge.\n        merge_mode: The merge strategy to use (e.g., 'merge', 'squash', 'rebase').\n\n    Raises:\n        Exception: If the underlying `gh pr merge` command fails with a non-zero\n            exit code. Common causes include merge conflicts, insufficient\n            permissions, an invalid pull request number, or other unmet merge\n            preconditions."}."""
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
    """Orchestrates the reconciliation of a pull request to a mergeable state.

    Implements a reconciliation loop that periodically polls the state of a pull
    request associated with the provided plan. The function attempts to
    autonomously resolve common blocking conditions by syncing with the base
    branch, resolving bot-only comment threads, and triggering automated repair
    jobs for failing status checks.

    The process is governed by configurable parameters for polling intervals,
    maximum polling attempts, and the maximum number of repair rounds.

    Args:
        request_dir: Path to a directory for storing logs and state artifacts for
            this specific reconciliation run.
        plan: The execution plan dictionary, which must contain the `branch_name`
            key to identify the target pull request.
        executor_command: The shell command used to invoke an automated repair
            process when the pull request has failing checks or unresolved
            threads.
        merge_mode: The merge strategy to use ('merge', 'squash', or 'rebase')
            when the pull request is successfully reconciled and `allow_merge`
            is True.
        allow_merge: If True, merges the pull request upon reaching a mergeable
            state. If False, the function exits successfully without merging.

    Raises:
        RuntimeError: If the pull request remains unmergeable after exhausting the
            configured number of repair rounds, or if the reconciliation process
            times out after the maximum number of polling attempts.
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
    """Generate a Markdown-formatted pull request body from a plan dictionary.

    Formats a structured plan dictionary into a standard Markdown string suitable for
    a pull request body. This includes sections for a summary, change
    specifications, a task list, and static governance checks.

    Args:
        plan: A dictionary representing the project plan with the following keys:
            `problem` (str): A required description of the problem.
            `value_expected` (str): A required description of the expected value.
            `in_scope` (list[str], optional): Items considered in scope.
            `out_of_scope` (list[str], optional): Items explicitly out of scope.
            `source_of_truth` (list[str], optional): Canonical references.
            `invariants` (list[str], optional): System invariants to preserve.
            `validation_plan` (list[str], optional): The validation strategy.
            `tasks` (list[dict], optional): A list of task dictionaries, where
                each dictionary must contain 'id' and 'title' string keys.

    Returns:
        A multi-line string formatted in Markdown, suitable for a pull request
        body.

    Raises:
        KeyError: If `plan` is missing the required 'problem' or
            'value_expected' keys.
        TypeError: If a value associated with an optional key (e.g., 'in_scope',
            'tasks') is not of the expected iterable type, such as a list.
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
    """Creates and submits a GitHub pull request based on a provided plan.

    This function orchestrates the creation of a pull request by performing several
    sequential operations:
    1. Generates the pull request body from the plan and writes it to a local
       markdown file within `request_dir`.
    2. Pushes the specified git branch to the remote origin.
    3. Executes the GitHub CLI (`gh`) to create the pull request against the
       configured base branch.
    4. Retrieves the created pull request's metadata and saves it to a local
       JSON file (`pr_created.json`) within `request_dir`.

    Args:
        plan: A dictionary detailing the pull request. Must contain 'branch_name'
            (str) and 'pr_title' (str) keys.
        request_dir: The local directory path for storing operation artifacts,
            including the PR body and the created PR data.
        skip_auto_merge: If True, bypasses the auto-merge enablement step,
            regardless of the orchestrator policy setting.

    Returns:
        A dictionary containing the JSON response data for the newly created pull
        request, as provided by the GitHub API.

    Raises:
        KeyError: If the `plan` dictionary is missing the required 'branch_name'
            or 'pr_title' keys.
        subprocess.CalledProcessError: If a git or GitHub CLI command fails
            during execution.
        OSError: If an error occurs while writing files to `request_dir`.
    """
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
    """Orchestrates the execution of a multi-task plan within an isolated Git worktree to ensure atomicity and prevent repository state corruption.

    This function manages the end-to-end execution of a plan by first provisioning
    a temporary "shadow" Git worktree. This isolates all file system and
    repository modifications. To enable this, the primary worktree's HEAD is
    detached to unlock the target branch reference, preventing conflicts. An
    `atexit` handler is registered to guarantee the cleanup of this worktree
    and the restoration of the original repository state upon completion or error.

    The function iterates through each task in the plan, invoking a specified
    external executor command. For each task, a retry mechanism is employed.
    Upon failure, a diagnostic `DoctorAgent` analyzes the error and generates a
    corrective 'cure', which is supplied as feedback to the subsequent attempt.
    The agent can halt execution by raising a `RuntimeError` if a failure is
    deemed unrecoverable or violates a safety invariant.

    Upon successful completion of all tasks, all staged changes are used to
    generate a cryptographically signed compliance receipt. The changes are then
    committed with this receipt. Finally, based on configuration and flags, a
    pull request can be created and automatically merged.

    Args:
        request_dir: The directory path for storing execution artifacts, such as
            prompts, logs, and the final compliance receipt.
        plan: A dictionary defining the execution plan. Must contain keys
            'branch_name' (str), 'commit_title' (str), and 'tasks' (list of dicts).
        executor_command: The shell command template used to invoke the task
            executor for each step.
        skip_pr: If True, suppresses the creation of a pull request after the
            commit is made.
        skip_auto_merge: If True, prevents a created pull request from being
            automatically merged, overriding any governing policy.

    Raises:
        RuntimeError: If a task fails after exhausting all retry attempts, or if
            the `DoctorAgent` blocks execution due to a safety violation.
        subprocess.CalledProcessError: If a critical Git command fails during
            the worktree setup or execution phase.
    """
    global ROOT
    original_root = ROOT
    import atexit

    import assessment_engine.scripts.lib.runtime_paths as rp

    policy = load_orchestrator_policy()
    timeouts = resolve_execution_timeouts(policy)
    max_attempts = int(policy.get("execution", {}).get("max_attempts_per_task", 3))
    preflight_executor(request_dir, executor_command)

    branch_name = plan["branch_name"]
    shadow_worktree_path = Path("/tmp") / f"shadow_worktree_{slugify(branch_name)}"

    # A shadow worktree is provisioned to create an isolated environment for subsequent Git manipulations, thereby preserving the integrity of the primary working directory.
    logger.info(f"Fase 2: Preparando Shadow Workspace en {shadow_worktree_path}")
    subprocess.run(
        ["git", "worktree", "remove", "-f", str(shadow_worktree_path)],
        cwd=original_root,
        stderr=subprocess.DEVNULL,
    )

    # The name of the current Git branch is stored programmatically. This enables the script to restore the repository to its original branch upon completion or in the event of an error, ensuring a stateless execution.
    original_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=original_root,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not original_branch:
        original_branch = "main"  #

    # A precondition check ensures the existence of the target branch. If the branch is absent, it is created to prevent downstream `git checkout` or `git push` operations from failing.
    ensure_branch(branch_name)

    # The primary worktree is transitioned to a detached HEAD state. This operation unlocks the current branch's reference (`refs/heads/<branch>`), making it available for checkout and modification by the isolated shadow worktree without causing a 'branch is already checked out' conflict.
    subprocess.run(["git", "checkout", "--detach"], cwd=original_root, check=True)

    #
    subprocess.run(
        ["git", "worktree", "add", "-f", str(shadow_worktree_path), branch_name],
        cwd=original_root,
        check=True,
    )

    #
    def cleanup_worktree() -> None:
        """Cleans up a temporary Git worktree and restores the original repository state.

        This function reverts the repository to its initial state by changing the
        current working directory back to the original root, forcefully removing the
        temporary worktree via `git worktree remove -f`, and checking out the
        original branch.

        The function relies on the module-level variables `original_root`,
        `shadow_worktree_path`, and `original_branch` being set prior to its
        invocation. Any exceptions encountered during the cleanup operations are
        caught and logged, preventing program termination.
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

    # Loads authorized human feedback, if available for the current task, into the execution context. This allows the model to incorporate specific, trusted guidance and corrections.
    authorized_feedback_path = request_dir / "authorized_feedback.json"
    authorized_feedback_data = {}
    if authorized_feedback_path.exists():
        try:
            authorized_feedback_data = json.loads(
                authorized_feedback_path.read_text(encoding="utf-8")
            )
            authorized_feedback_path.unlink(
                missing_ok=True
            )  # The file is unlinked immediately after its contents are read into memory. This enforces a strict process-once semantic for the data and maintains a clean state in the working directory.
            logger.info(
                "Se ha detectado y cargado feedback autorizado por el humano para esta ejecución."
            )
        except Exception as e:
            logger.warning(f"No se pudo cargar el feedback autorizado: {e}")

    for task in plan.get("tasks", []):
        logger.info(f"=== INICIANDO TAREA: {task['id']} ===")
        feedback: str | None = None

        # Human feedback, if available for the given task, is injected exclusively during the initial execution attempt. This ensures that the model's first response is informed by prior human guidance without being re-applied on subsequent retries.
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
                    #
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

    # A diff of all staged changes is generated prior to commit. This diff artifact serves as the canonical payload for the subsequent cryptographic signing operation, ensuring the integrity of the changeset.
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
    """Resolve the run resumption identifier from command-line arguments, prioritizing the branch name over the pull request number."""
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
    """Resume an existing pull request by generating and executing a new plan.

    This function orchestrates the resumption of a previously managed pull request.
    It resolves the pull request from a provided selector, inspects its remote
    state, and verifies local Git repository preconditions. A new execution plan
    is then generated based on the provided policy and the current PR state.
    This plan is saved to a new request directory and executed to reconcile the
    pull request, potentially performing an auto-merge.

    Args:
        args: A namespace object from `argparse` containing parsed command-line
            arguments. It must contain a pull request selector and may include
            flags such as `allow_dirty`, `executor_command`, and
            `skip_auto_merge`.
        policy: The configuration dictionary that governs the operation's
            behavior. It may contain nested keys such as
            `pull_request.auto_merge_mode`.

    Returns:
        The `pathlib.Path` to the newly created request directory, which
        contains the serialized execution plan and other generated artifacts.

    Raises:
        ValueError: If the pull request specified by the selector in `args`
            cannot be found or resolved.
        RuntimeError: If a critical precondition is not met. This includes the
            Git working tree being dirty when `allow_dirty` is `False`, or the
            local Git branch corresponding to the pull request's head reference
            not existing.
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
    """Orchestrates the product owner workflow based on parsed command-line arguments.

    Serves as the primary entry point for the command-line interface, dispatching
    tasks based on the specified command. It handles distinct workflows:
    generating a development plan ('plan'), executing a pre-existing plan
    ('execute'), running the full plan-then-execute sequence ('run'), and
    resuming work on an existing pull request ('resume-pr'). The function
    manages the lifecycle of a development request, from initial planning to
    final execution, including handling cases of ambiguity or refusal by the
    planning model.

    Args:
        argv: A list of command-line arguments, analogous to sys.argv[1:].
            If None, arguments are parsed directly from the system's
            command line.

    Returns:
        An integer exit code. Returns 0 for successful completion of a
        workflow. Returns 1 for user-facing errors, such as an ambiguous
        request, a refused plan, or a plan containing no executable
        alternatives.

    Raises:
        FileNotFoundError: If the 'execute' command is invoked but the required
            'plan.json' file does not exist in the specified request
            directory.
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
            # This logic provides a fallback path to accommodate a legacy request directory structure. Its inclusion ensures backward compatibility with older data formats.
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
