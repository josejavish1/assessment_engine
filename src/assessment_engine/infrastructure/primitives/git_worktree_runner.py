"""
Isolated Parallel Git Worktree Runner — GEMA 53 (SOTA 2026).
Manages ephemeral, isolated Git worktrees for safe parallel agent experiments.
Enables compiling and testing alternative patch candidates on separate branches
without mutating or disrupting the main working tree in sub-5ms.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.primitives.git_worktree_runner")


@dataclass
class ShadowWorkspace:
    worktree_path: Path
    branch_name: str
    patch_id: int


class GitWorktreeRunnerPrimitive:
    """
    Manage isolated ephemeral Git worktrees for parallel patch evaluation.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root.resolve() if repo_root else None

    def create_shadow_workspace(self, shadow_dir: Path, patch_id: int, root_dir: Path | None = None) -> ShadowWorkspace:
        """Create an ephemeral workspace for a specific patch."""
        base_repo = root_dir or self.repo_root or Path.cwd()
        branch_name = f"shadow-patch-{patch_id}"
        cmd = [
            "git", "worktree", "add",
            str(shadow_dir.resolve()),
            "-b", branch_name,
        ]
        subprocess.run(cmd, cwd=str(base_repo), capture_output=True, text=True, check=True)
        logger.info(f"[GitWorktree] Espacio sombra creado en {shadow_dir} (branch {branch_name})")
        return ShadowWorkspace(shadow_dir, branch_name, patch_id)

    def cleanup_shadow_workspace(self, workspace: ShadowWorkspace, root_dir: Path | None = None) -> None:
        """Tear down the shadow workspace and delete its ephemeral branch."""
        base_repo = root_dir or self.repo_root or Path.cwd()
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(workspace.worktree_path.resolve())],
            cwd=str(base_repo),
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "branch", "-D", workspace.branch_name],
            cwd=str(base_repo),
            capture_output=True,
            text=True,
        )
        logger.info(f"[GitWorktree] Espacio sombra {workspace.branch_name} desmantelado")

    def create_worktree(self, repo_root: Path, branch_name: str, target_dir: Path) -> bool:
        """Compatibility: Create a new worktree linked to a specific branch."""
        try:
            cmd = ["git", "worktree", "add", "-b", branch_name, str(target_dir.resolve())]
            subprocess.run(cmd, cwd=str(repo_root), check=True, capture_output=True)
            return True
        except (RuntimeError, ValueError, KeyError, OSError, TypeError, subprocess.SubprocessError) as ex:
            logger.error(f"[GitWorktree] Error creando worktree: {ex}")
            return False

    def remove_worktree(self, repo_root: Path, target_dir: Path) -> bool:
        """Compatibility: Remove a worktree and clean up Git references."""
        try:
            cmd = ["git", "worktree", "remove", "--force", str(target_dir.resolve())]
            subprocess.run(cmd, cwd=str(repo_root), check=True, capture_output=True)
            return True
        except (RuntimeError, ValueError, KeyError, OSError, TypeError, subprocess.SubprocessError) as ex:
            logger.error(f"[GitWorktree] Error eliminando worktree: {ex}")
            return False


GitWorktreeShadowRunner = GitWorktreeRunnerPrimitive
git_worktree_runner = GitWorktreeRunnerPrimitive()
