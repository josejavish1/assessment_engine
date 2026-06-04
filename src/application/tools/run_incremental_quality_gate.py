from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LIVE_PYTHON_PREFIXES = ("src/assessment_engine/", "tests/", "working/")
ZERO_SHA_RE = re.compile(r"^0+$")


def git_changed_files(
    repo_root: Path, base_sha: str | None, head_sha: str | None
) -> list[str]:
    if not base_sha or not head_sha:
        return []
    if ZERO_SHA_RE.fullmatch(base_sha):
        return []

    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-only", base_sha, head_sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not compute changed files.")

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def normalize_live_python_paths(repo_root: Path, paths: list[str]) -> list[str]:
    return sorted(
        {
            path
            for path in paths
            if path.endswith(".py")
            and path.startswith(LIVE_PYTHON_PREFIXES)
            and (repo_root / path).is_file()
        }
    )


def run_quality_commands(repo_root: Path, target_files: list[str]) -> int:
    commands = [
        [sys.executable, "-m", "ruff", "check", *target_files],
        [sys.executable, "-m", "ruff", "format", "--check", *target_files],
    ]

    for command in commands:
        result = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        if result.returncode != 0:
            return result.returncode

    return 0


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
    target_files = normalize_live_python_paths(repo_root, changed_files)

    if not target_files:
        print("Incremental quality gate skipped: no live Python files changed.")
        return 0

    print("Incremental quality gate targets:")
    for path in target_files:
        print(f"- {path}")

    return run_quality_commands(repo_root, target_files)


if __name__ == "__main__":
    raise SystemExit(main())
