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
    """Executes the mypy type checker as a subprocess on a list of files.

    Invokes `mypy` using the current Python executable (`sys.executable`), with
    `repo_root` set as the current working directory. This ensures that mypy uses
    the `pyproject.toml` configuration file located at the repository root.
    Standard output and standard error from the mypy process are captured and
    forwarded to the corresponding streams of the parent process.

    Args:
        repo_root: The path to the repository root directory. This is used as
            the working directory for the mypy command.
        target_files: A list of file paths to be checked by mypy. These paths
            should typically be relative to `repo_root`.

    Returns:
        The integer exit code from the mypy subprocess. An exit code of 0
        indicates that no type errors were found.
    """
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
    """Parse command-line arguments for an incremental type check.

    Args:
        argv: An optional list of string arguments to parse. If None, `argparse`
            defaults to `sys.argv[1:]`.

    Returns:
        An `argparse.Namespace` object with the following attributes:
          repo_root (str): The path to the repository root.
          base_sha (str | None): The base commit SHA for comparison.
          head_sha (str | None): The head commit SHA for comparison.
          path (list[str]): A list of specific file or directory paths to check.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--path", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run an incremental type check on changed Python files.

    Parses command-line arguments to identify a set of target Python files
    and executes a type checker against them. The target files are determined
    by either an explicit list of paths provided via arguments or by computing
    the diff between two specified git revisions. If no Python files are
    identified in the change set, the check is skipped.

    Args:
        argv: A list of command-line arguments, typically from `sys.argv`.
            If None, arguments are parsed from the command line automatically.

    Returns:
        An integer exit code. 0 indicates that the type check passed or was
        skipped, while a non-zero value indicates a failure.
    """
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    changed_files = args.path or git_changed_files(
        repo_root, args.base_sha, args.head_sha
    )
    target_files = normalize_live_python_paths(repo_root, changed_files)

    if not target_files:
        print("Incremental type check skipped: no live Python files changed.")
        return 0

    print("Incremental type check targets:")
    for path in target_files:
        print(f"- {path}")

    return run_typecheck(repo_root, target_files)


if __name__ == "__main__":
    raise SystemExit(main())
