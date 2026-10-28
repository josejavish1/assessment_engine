"""
Run Git worktrees in ephemeral isolation. Branch the repository into temporary paths under /tmp/autonomuos_arbiter_<id> to experiment, compile, and execute safely without affecting the main branch. Ensure clean teardown via context managers.
"""
from __future__ import annotations


import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Self

logger = logging.getLogger("assessment_engine.infrastructure.evolution.worktree_runner")


class EphemeralWorktree:
    """Represent an ephemeral Git workspace located in /tmp.
Support the context manager protocol to ensure safe destruction."""

    def __init__(self, repo_root: Path, worktree_path: Path, branch_name: str) -> None:
        self.repo_root = repo_root.resolve()
        self.worktree_path = worktree_path.resolve()
        self.branch_name = branch_name
        self._active = True

    @property
    def is_active(self) -> bool:
        """Check whether the instance is active."""
        return self._active

    def cleanup(self) -> bool:
        """Unconditionally delete the worktree and its ephemeral branch.
Leave no trace in git status or git worktree list."""
        if not self._active:
            return True

        try:
            target_nm = self.worktree_path / "templates" / "golden_polyglot_starter" / "web" / "node_modules"
            if target_nm.is_symlink():
                target_nm.unlink(missing_ok=True)
            target_venv = self.worktree_path / "venv"
            if target_venv.is_symlink():
                target_venv.unlink(missing_ok=True)
        except OSError:
            pass

        success = True
        try:
            cmd_rm = ["git", "worktree", "remove", "--force", str(self.worktree_path)]
            res = subprocess.run(cmd_rm, cwd=str(self.repo_root), capture_output=True, text=True, check=False)
            if res.returncode != 0:
                logger.debug(f"[Worktree] Aviso al remover worktree: {res.stderr.strip()}")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[Worktree] Error al remover worktree {self.worktree_path}: {ex}")
            success = False

        # 2. git branch -D <branch>
        try:
            cmd_br = ["git", "branch", "-D", self.branch_name]
            res_br = subprocess.run(cmd_br, cwd=str(self.repo_root), capture_output=True, text=True, check=False)
            if res_br.returncode != 0:
                logger.debug(f"[Worktree] Aviso al borrar rama {self.branch_name}: {res_br.stderr.strip()}")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[Worktree] Error al eliminar rama {self.branch_name}: {ex}")
            success = False

        # 3. Clean up any remaining directory left in /tmp
        try:
            if self.worktree_path.exists():
                shutil.rmtree(self.worktree_path, ignore_errors=True)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.debug(f"[Worktree] Limpieza de directorio residual omitida: {ex}")

        self._active = False
        return success

    def run_command(self, cmd: list[str], timeout: int = 60, check: bool = False, **kwargs) -> subprocess.CompletedProcess:
        """Execute a command with cwd set to the ephemeral worktree."""
        if not self._active:
            raise RuntimeError(f"El worktree efímero {self.worktree_path} ya ha sido desmantelado.")
        return subprocess.run(
            cmd,
            cwd=str(self.worktree_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
            **kwargs,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()


class GitWorktreeRunner:
    """
    Manage ephemeral isolation using Git worktrees.
    """

    def __init__(self, default_repo_root: Path | None = None) -> None:
        self.default_repo_root = default_repo_root or Path(__file__).resolve().parent.parent.parent

    def create_worktree(
        self,
        repo_root: Path | None = None,
        branch_prefix: str = "arbiter_",
        custom_target_dir: Path | None = None,
    ) -> EphemeralWorktree:
        """Create an ephemeral worktree in /tmp or at the specified path.
Automatically create a unique temporary branch."""
        root = (repo_root or self.default_repo_root).resolve()
        token = uuid.uuid4().hex[:8]
        branch_name = f"{branch_prefix}{token}"

        if custom_target_dir:
            target_path = custom_target_dir.resolve()
        else:
            temp_dir = tempfile.gettempdir()
            target_path = Path(temp_dir) / f"autonomuos_arbiter_{token}"

        cmd = [
            "git", "worktree", "add",
            "-b", branch_name,
            str(target_path),
        ]

        try:
            subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=True)
            logger.info(f"[Worktree] Creado espacio efímero en {target_path} (rama {branch_name})")

            # Enlazar dependencias pesadas mediante symlinks inmutables (Zero-Copy Dependency Mount)
            host_nm = root / "templates" / "golden_polyglot_starter" / "web" / "node_modules"
            target_nm = target_path / "templates" / "golden_polyglot_starter" / "web" / "node_modules"
            if host_nm.exists() and not target_nm.exists():
                target_nm.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(str(host_nm.resolve()), str(target_nm))
                logger.debug("[Worktree] Enlazado node_modules vía symlink zero-copy.")

            host_venv = root / "venv"
            target_venv = target_path / "venv"
            if host_venv.exists() and not target_venv.exists():
                os.symlink(str(host_venv.resolve()), str(target_venv))
                logger.debug("[Worktree] Enlazado venv vía symlink zero-copy.")
        except subprocess.CalledProcessError as e:
            logger.error(f"[Worktree] Falló la creación del worktree: {e.stderr}")
            raise RuntimeError(f"No se pudo crear el worktree de Git: {e.stderr}") from e
        except (OSError, RuntimeError) as sym_err:
            logger.debug(f"[Worktree] Aviso al montar symlinks de dependencias: {sym_err}")

        return EphemeralWorktree(repo_root=root, worktree_path=target_path, branch_name=branch_name)

    def clean_teardown(self, workspace: EphemeralWorktree) -> bool:
        """Tear down and clean up an ephemeral workspace."""
        return workspace.cleanup()


worktree_runner = GitWorktreeRunner()

__all__ = [
    "EphemeralWorktree",
    "GitWorktreeRunner",
    "worktree_runner",
]
