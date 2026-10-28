"""
Build and clone workspace scaffolding, decoupled from workspace.py via the Strangler Fig pattern. Provides:
- ensure_workspace_scaffold: Hardlink cloning from templates/golden_polyglot_starter, polyglot .gitignore configuration, GitHub Actions workflows, and Git repository initialization.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.foundry.components.scaffold_builder")


def _unlink_editable_files(workspace_dir: Path) -> None:
    for editable_path in [
        workspace_dir / "web" / "src" / "App.tsx",
        workspace_dir / "api" / "src" / "domain_routes.py",
        workspace_dir / "web" / "dist" / "index.html"
    ]:
        if editable_path.exists():
            try:
                content = editable_path.read_text(encoding="utf-8")
                editable_path.unlink()
                editable_path.write_text(content, encoding="utf-8")
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as unlink_err:# noqa: BLE001
                logger.debug(f"Unlink note: {unlink_err}")

def _clone_starter_hardlink(workspace_dir: Path, templates_dir: Path) -> None:
    starter_dir = templates_dir / "golden_polyglot_starter"
    if starter_dir.exists() and not (workspace_dir / "api").exists() and not (workspace_dir / "src").exists():
        try:
            subprocess.run(["cp", "-al", f"{starter_dir}/.", f"{workspace_dir}/"], check=False, capture_output=True)
            for db_file in workspace_dir.glob("*.db*"):
                try:
                    db_file.unlink(missing_ok=True)
                except OSError:
                    pass
            _unlink_editable_files(workspace_dir)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as scaffold_err:# noqa: BLE001
            logger.debug(f"Scaffold copy note: {scaffold_err}")

def ensure_workspace_scaffold(workspace_dir: Path, templates_dir: Path) -> None:
    """Initialize the enterprise repository structure and Git baseline."""
    workspace_dir.mkdir(parents=True, exist_ok=True)

    _clone_starter_hardlink(workspace_dir, templates_dir)

    (workspace_dir / "docs").mkdir(exist_ok=True)
    (workspace_dir / "scripts").mkdir(exist_ok=True)
    (workspace_dir / "tests").mkdir(exist_ok=True)
    (workspace_dir / "tests" / "autopsy").mkdir(parents=True, exist_ok=True)
    (workspace_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

    gitignore_path = workspace_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(
            "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.venv/\nvenv/\n.pytest_cache/\n.coverage\nhtmlcov/\n.mypy_cache/\n.ruff_cache/\n\n"
            "# Rust\ntarget/\nCargo.lock\n\n"
            "# Go\nbin/\n*.exe\nvendor/\n\n"
            "# Node\nnode_modules/\ndist/\n\n"
            "# Logs, Sessions & SQLite Storage\n*.log\n*.tmp\n*.db\n*.db-shm\n*.db-wal\n*.sqlite\n*.sqlite3\n.adk_sessions.db\n.env\n",
            encoding="utf-8"
        )

    ci_path = workspace_dir / ".github" / "workflows" / "ci.yml"
    if not ci_path.exists():
        ci_path.write_text(
            "name: Quality Gate CI\non: [push, pull_request]\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Run Quality Gate Verification\n        run: bash scripts/verify.sh\n",
            encoding="utf-8"
        )

    git_dir = workspace_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=workspace_dir, capture_output=True, check=False)
        subprocess.run(["git", "config", "user.name", "Autonomuos Engine"], cwd=workspace_dir, capture_output=True, check=False)
        subprocess.run(["git", "config", "user.email", "engine@autonomuos.dev"], cwd=workspace_dir, capture_output=True, check=False)
        subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True, check=False)
        subprocess.run(["git", "commit", "-m", "chore: initial repository scaffold"], cwd=workspace_dir, capture_output=True, check=False)
