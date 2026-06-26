from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from assessment_engine.application.tools.run_incremental_quality_gate import (
    git_changed_files,
    normalize_live_python_paths,
)


def run_typecheck(repo_root: Path, target_files: list[str]) -> int:
    """Run the mypy type checker on a list of files.

    Executes `mypy` as a subprocess from the specified repository root directory,
    using the `pyproject.toml` file for configuration. The standard output and
    standard error from the `mypy` process are captured and printed to their
    respective console streams.

    Args:
        repo_root: The path to the repository's root directory, which is used
            as the current working directory for the mypy subprocess.
        target_files: A list of file paths, relative to `repo_root`, to be
            type-checked.

    Returns:
        The exit code from the mypy process. A value of 0 indicates that no
        type errors were found.

    Raises:
        FileNotFoundError: If the Python executable specified by `sys.executable`
            is not found.
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
    r"""{'docstring': 'Parse command-line arguments for an incremental type-checking operation.\n\nArgs:\n    argv: A list of strings representing the command-line arguments. If None,\n        `sys.argv[1:]` is used by the underlying `argparse` library.\n\nReturns:\n    An `argparse.Namespace` object containing the parsed arguments.\n    Attributes include `repo_root` (str), `base_sha` (str | None),\n    `head_sha` (str | None), and `path` (list[str]).'}."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--path", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run an incremental type check on changed Python files.

    Serves as the main entry point for the script. It identifies changed Python
    files and executes a type checker against them. The set of changed files
    is determined either from a user-provided list of paths or by diffing two
    git commits. This list is then filtered to include only existing Python
    source files. If no such files remain after filtering, the check is skipped.

    Args:
        argv: A list of command-line arguments. If `None`, arguments are parsed
            from `sys.argv`.

    Returns:
        An integer exit code. A value of 0 indicates success, including cases
        where the type check passed or was skipped. A non-zero value indicates
        a failure during the type check.

    Raises:
        FileNotFoundError: If the repository root path provided via arguments
            does not exist.
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
