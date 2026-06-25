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
    """Computes the set of changed file paths between two Git commit SHAs.

    Invokes `git diff --name-only <base_sha> <head_sha>` within the specified
    repository. This function is designed for incremental quality gates and
    handles cases where a diff is not meaningful by returning an empty list.
    This occurs if either SHA is invalid, or if `base_sha` is the zero-SHA
    (which represents the empty tree parent of an initial commit).

    Args:
        repo_root: The file system path to the root of the Git repository.
        base_sha: The base commit SHA for the diff comparison.
        head_sha: The head commit SHA for the diff comparison.

    Returns:
        A list of file paths, relative to `repo_root`, that were changed
        between the base and head commits. Returns an empty list if no
        meaningful diff can be computed.

    Raises:
        RuntimeError: If the underlying `git` process exits with a non-zero
            status code. The error message will contain the process's stderr.
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
    r"""{'docstring': 'Filter and normalize a list of paths to valid, live Python source files.\n\n    Filters an iterable of file paths, retaining only those that meet specific\n    criteria for being considered a "live" Python source file. The criteria are:\n    \n    1.  The path must have a \'.py\' extension.\n    2.  The path must begin with one of the prefixes specified in the global\n        `LIVE_PYTHON_PREFIXES` constant.\n    3.  The path must resolve to an existing file on the filesystem when\n        combined with the `repo_root`.\n\n    The resulting set of valid paths is returned as a sorted list, ensuring\n    uniqueness and a deterministic order.\n\n    Args:\n        repo_root: The absolute path to the repository\'s root directory, as a\n            `pathlib.Path` object.\n        paths: A list of file paths to filter, typically relative to `repo_root`.\n\n    Returns:\n        A sorted list of unique, valid paths to live Python source files.'}."""
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
    r"""{'docstring': "Execute a sequence of code quality commands on a list of source files.\n\nThis function serially executes `ruff check` and `ruff format --check`\nagainst the provided files. Commands are run with the repository root as the\ncurrent working directory.\n\nExecution short-circuits on the first command that returns a non-zero exit\ncode. The standard output and standard error from each command are printed to\nthe console upon its completion.\n\nArgs:\n    repo_root: The absolute path to the repository's root directory, used as\n        the current working directory for subprocesses.\n    target_files: A list of file paths to be inspected by the quality commands.\n\nReturns:\n    The integer exit code of the first command that fails, or 0 if all\n    commands succeed.\n\nRaises:\n    FileNotFoundError: If the Python interpreter specified by `sys.executable`\n        cannot be located."}."""
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
        argv: A list of command-line arguments to parse. If None, arguments are
            read from `sys.argv`.

    Returns:
        An `argparse.Namespace` object containing the following attributes:
          repo_root (str): The required path to the repository root.
          base_sha (str | None): The optional commit SHA of the base for
            comparison.
          head_sha (str | None): The optional commit SHA of the head revision.
          path (list[str]): A list of specific file or directory paths to
            analyze, which may be empty.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--path", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the incremental quality gate on changed Python files.

    This function serves as the main entry point for the script. It identifies
    a set of target Python files based on command-line arguments, either from
    an explicit list of paths or by computing a git diff between two revisions.
    The file list is filtered to retain only existing Python source files.

    If no target files are found, the function reports this and exits with a
    success code. Otherwise, it executes a series of quality checks against
    the identified files.

    Args:
        argv: A list of command-line arguments. If `None`, arguments are parsed
            from `sys.argv`.

    Returns:
        An integer exit code. A value of 0 indicates that all quality checks
        passed or that no relevant files were changed. A non-zero value
        indicates a quality check failure.
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
