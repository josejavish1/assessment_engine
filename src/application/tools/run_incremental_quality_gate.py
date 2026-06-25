from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LIVE_PYTHON_PREFIXES = (
    "src/assessment_engine/",
    "src/application/",
    "src/infrastructure/",
    "src/domain/",
    "src/adapters/",
    "src/ports/",
    "tests/",
    "working/",
)
ZERO_SHA_RE = re.compile(r"^0+$")


def git_changed_files(
    repo_root: Path, base_sha: str | None, head_sha: str | None
) -> list[str]:
    """Computes the list of changed files between two Git commit SHAs.

    This function executes `git diff --name-only` to identify the set of files
    that have been modified between the `base_sha` and `head_sha` commits.
    It explicitly handles the zero SHA (e.g., `000...000`) for `base_sha`,
    a common convention in CI systems for initial commits, by returning an empty list.

    Args:
        repo_root: The file system path to the root of the Git repository.
        base_sha: The starting commit SHA for the diff. If `None`, an empty string,
            or the zero SHA, the function returns an empty list.
        head_sha: The ending commit SHA for the diff. If `None` or an empty string,
            the function returns an empty list.

    Returns:
        A list of file paths, relative to the repository root, that have
        changed between the two commits. An empty list is returned if no files
        have changed or if the input SHAs are invalid for a diff operation.

    Raises:
        RuntimeError: If the underlying `git diff` command returns a non-zero
            exit code. The exception message contains the `stderr` from the
            failed command.
    """
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
    """Filters and normalizes a list of paths to valid, existing Python files.

    This function processes a list of file paths and returns a filtered, sorted,
    and unique list based on several criteria. A path is retained if and only if
    it meets all of the following conditions:

    1.  The path string ends with the ".py" extension.
    2.  The path string starts with one of the prefixes defined in the
        module-level `LIVE_PYTHON_PREFIXES` constant.
    3.  The path, when resolved relative to `repo_root`, corresponds to an
        existing file on the filesystem.

    The final list of paths is returned in alphabetical order.

    Args:
        repo_root: The absolute path to the repository's root directory, used as
            the base for checking file existence.
        paths: A list of string paths to be filtered, each expected to be
            relative to the repository root.

    Returns:
        A sorted list of unique, relative string paths that satisfy all
        filtering criteria.
    """
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
    """Sequentially execute Ruff quality commands against specified files.

    Executes `ruff check` and `ruff format --check` in order for the given
    `target_files`. If any command returns a non-zero exit code, execution
    halts, and that exit code is returned. The standard output and standard
    error from each subprocess are captured and printed to the parent
    process's corresponding streams.

    Args:
        repo_root: The repository root directory from which to execute the Ruff
            commands.
        target_files: A list of file paths to be passed to the Ruff commands for
            analysis.

    Returns:
        The exit code of the first command that fails, or 0 if all commands
        complete successfully.
    """
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
    """Parse command-line arguments for the incremental quality gate script.

    Args:
        argv: A sequence of command-line arguments. If None, `sys.argv[1:]` is
            used.

    Returns:
        An argparse.Namespace object containing the parsed arguments. The object
        exposes the following attributes:
            repo_root (str): The required path to the repository root.
            base_sha (str | None): The base commit SHA for comparison.
            head_sha (str | None): The head commit SHA for comparison.
            path (list[str]): A list of specific file or directory paths to
                analyze. Defaults to an empty list if unspecified.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--path", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run an incremental quality gate on changed Python files.

    This function serves as the main entry point for the script. It identifies
    Python files that have changed between two Git commits or from a provided
    list of paths, and then executes a series of quality checks on them.

    If no relevant Python files are identified as changed, the gate is skipped
    and the function returns a success code.

    Args:
        argv: A list of command-line arguments. If `None`, `sys.argv[1:]` is
            used by the argument parser.

    Returns:
        An integer exit code. A value of 0 indicates success (either all checks
        passed or no files were targeted). A non-zero value indicates a quality
        check failure.
    """
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
