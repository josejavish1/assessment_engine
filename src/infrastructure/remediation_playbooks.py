import logging

#
import subprocess
from typing import NamedTuple

logger = logging.getLogger(__name__)


class RemediationResult(NamedTuple):
    """Represents the outcome of a remediation action."""

    success: bool
    message: str


def check_git_status() -> RemediationResult:
    """Verify the git working directory is clean.

    Executes `git status --porcelain` to check for staged modifications,
    uncommitted changes, or untracked files. A clean worktree results in
    empty standard output from this command.

    The function handles execution failures of the git command (e.g., if not
    run within a git repository) by catching `subprocess.CalledProcessError`
    and returning a failure result containing the error message from stderr.

    Returns:
        RemediationResult: An object detailing the outcome. The `success`
            attribute is `True` if the worktree is clean, and `False`
            otherwise. The `message` attribute provides context, such as the
            output of `git status` if the tree is dirty or the stderr content
            if the subprocess command fails.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            return RemediationResult(False, f"Worktree is dirty:\n{result.stdout}")
        return RemediationResult(True, "Worktree is clean.")
    except subprocess.CalledProcessError as e:
        return RemediationResult(False, f"Git status failed: {e.stderr}")


def clean_workspace() -> RemediationResult:
    r"""{'docstring': "Resets the git working directory to the `HEAD` commit.\n\n    Executes `git reset --hard HEAD` and `git clean -fd` to discard all\n    uncommitted changes and remove all untracked files and directories.\n    This is a destructive operation that results in the permanent loss of\n    any work not yet committed.\n\n    This function must be executed from within a valid git repository.\n\n    Returns:\n        RemediationResult: An object representing the operation's outcome.\n            The `success` attribute is True if the repository was cleaned\n            successfully, or False if a git command failed. The `message`\n            attribute contains a confirmation upon success or the captured\n            stderr content upon failure.\n\n    Raises:\n        FileNotFoundError: If the `git` executable is not found in the system's\n            PATH."}."""
    try:
        #
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"], check=True, capture_output=True
        )
        #
        subprocess.run(["git", "clean", "-fd"], check=True, capture_output=True)
        return RemediationResult(True, "Workspace cleaned successfully.")
    except subprocess.CalledProcessError as e:
        return RemediationResult(False, f"Cleanup failed: {e.stderr}")
