# golden-path: ignore
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_runbook_commands_dry_runs(tmp_path: Path):
    # Retrieve the absolute repo root
    repo_root = Path(__file__).resolve().parents[2]

    # We will run these documented, safe operational commands in our isolated sandbox
    commands = [
        [
            "src/assessment_engine/application/tools/validate_documentation_governance.py",
            "--repo-root",
            str(repo_root),
            "--documentation-map",
            str(repo_root / "docs/documentation-map.yaml"),
            "--today",
            "2026-06-26",
        ],
        [
            "src/assessment_engine/application/tools/validate_documentation_snippets.py",
            "--repo-root",
            str(repo_root),
            "--documentation-map",
            str(repo_root / "docs/documentation-map.yaml"),
        ],
        [
            "src/assessment_engine/application/tools/lint_documentation_style.py",
            "--repo-root",
            str(repo_root),
            "--documentation-map",
            str(repo_root / "docs/documentation-map.yaml"),
        ],
        [
            "src/assessment_engine/application/tools/validate_contracts_schemas.py",
            "--repo-root",
            str(repo_root),
            "--documentation-map",
            str(repo_root / "docs/documentation-map.yaml"),
        ],
        [
            "src/assessment_engine/application/tools/regenerate_smoke_artifacts.py",
            "--dry-run",
        ],
        [
            "src/assessment_engine/application/tools/build_documentation_health_report.py",
            "--repo-root",
            str(repo_root),
            "--documentation-map",
            str(repo_root / "docs/documentation-map.yaml"),
            "--today",
            "2026-06-26",
            "--output",
            str(tmp_path / "health-report.json"),
        ],
        [
            "src/assessment_engine/application/tools/build_docs_site.py",
            "--repo-root",
            str(repo_root),
            "--documentation-map",
            str(repo_root / "docs/documentation-map.yaml"),
            "--output-dir",
            str(tmp_path / "site"),
        ],
    ]

    for cmd_args in commands:
        script_relative_path = cmd_args[0]
        script_absolute_path = repo_root / script_relative_path

        # Build the complete argument list using active Python interpreter
        full_args = [sys.executable, str(script_absolute_path)] + cmd_args[1:]

        # Run inside the isolated temporal directory with proper python path
        res = subprocess.run(
            full_args,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(repo_root / "src")},
            timeout=15,
        )
        assert res.returncode == 0, (
            f"Documented runbook command failed: {' '.join(full_args)}\n"
            f"stdout: {res.stdout}\n"
            f"stderr: {res.stderr}"
        )
