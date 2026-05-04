import logging
import subprocess
from typing import NamedTuple

logger = logging.getLogger(__name__)


class RemediationResult(NamedTuple):
    success: bool
    message: str


def check_git_status() -> RemediationResult:
    """Checks if the git working tree is clean."""
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
    """Performs a radical cleaning of the workspace."""
    try:
        # Reset tracked files
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"], check=True, capture_output=True
        )
        # Clean untracked files and directories
        subprocess.run(["git", "clean", "-fd"], check=True, capture_output=True)
        return RemediationResult(True, "Workspace cleaned successfully.")
    except subprocess.CalledProcessError as e:
        return RemediationResult(False, f"Cleanup failed: {e.stderr}")
