from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from assessment_engine.scripts.tools.run_incremental_quality_gate import (
    git_changed_files,
    normalize_live_python_paths,
)


def run_typecheck(repo_root: Path, target_files: list[str]) -> int:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            "pyproject.toml",
            *target_files,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--path", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    changed_files = args.path or git_changed_files(
        repo_root, args.base_sha, args.head_sha
    )
    target_files = normalize_live_python_paths(changed_files)

    if not target_files:
        print("Incremental type check skipped: no live Python files changed.")
        return 0

    print("Incremental type check targets:")
    for path in target_files:
        print(f"- {path}")

    return run_typecheck(repo_root, target_files)


if __name__ == "__main__":
    raise SystemExit(main())
