import logging

#
import subprocess
from typing import NamedTuple

logger = logging.getLogger(__name__)


class RemediationResult(NamedTuple):
    """Represent the outcome of a remediation action with a success flag and message."""

    success: bool
    message: str


def check_git_status() -> RemediationResult:
    """Verify that the Git working tree is clean.

    Executes `git status --porcelain` to check for uncommitted modifications
    or untracked files. The state of the local repository is determined by
    parsing the standard output of this command.

    Returns:
        RemediationResult: An object representing the outcome. The `success`
            attribute is `True` if the working tree is clean. It is `False` if
            there are uncommitted changes, untracked files, or if the command
            fails (e.g., not a Git repository). The `message` attribute
            provides a descriptive status.

    Raises:
        FileNotFoundError: If the 'git' executable cannot be found in the
            system's PATH.
        subprocess.CalledProcessError: If the 'git' command returns a non-zero
            exit code, which is caught and handled internally, not raised.
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
    """Reset the Git working directory to a clean, last-committed state.

    This function performs a destructive cleanup by executing two Git commands:
    1. `git reset --hard HEAD`: Discards all staged and unstaged changes to
       tracked files, resetting the index and working tree to match the `HEAD`
       commit.
    2. `git clean -fd`: Removes all untracked files and directories from the
       working tree.

    This operation is irreversible and will result in the loss of any
    uncommitted work. It does not remove files ignored by Git unless the
    `-x` option is used with `git clean`, which is not the case here.

    Returns:
        RemediationResult: An object indicating the outcome. If successful, the
            `success` attribute is True. On failure, `success` is False and the
            `message` attribute contains the stderr from the failed Git command.
    """
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
