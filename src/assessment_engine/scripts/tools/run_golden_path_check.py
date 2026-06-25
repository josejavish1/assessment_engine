from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

LIVE_PYTHON_PREFIXES = ("src/assessment_engine/", "tests/")

# These constants define mandatory structural markers. Their presence in new service and worker files is enforced to ensure adherence to standardized architectural templates.
# The presence of these markers serves as a programmatic assertion that a given file's structure conforms to a standardized Golden Path template, ensuring architectural consistency.
GOLDEN_PATH_MARKERS = [
    "# --- START OF BUSINESS LOGIC ---",  # A pragma used to demarcate code blocks or configuration sections specific to asynchronous worker processes or synchronous API endpoints.
    "# --- ARRANGE ---",  # A pragma used to demarcate code blocks or configuration sections that are exclusively relevant to the test execution environment.
]


def git_added_files(
    repo_root: Path, base_sha: str | None, head_sha: str | None
) -> list[str]:
    """Retrieve a list of file paths added between two Git commits.

    Executes `git diff --name-status` between the provided base and head
    commit SHAs to identify all newly added files. The function parses the
    standard output of the git command, filtering for lines that indicate an
    'Added' status ('A').

    If either `base_sha` or `head_sha` is None or an empty string, an empty
    list is returned immediately without invoking the git process.

    Args:
        repo_root: The absolute path to the root of the Git repository.
        base_sha: The base commit SHA for the diff comparison.
        head_sha: The head commit SHA for the diff comparison.

    Returns:
        A list of file paths, relative to the repository root, that were
        added between the two specified commits.

    Raises:
        RuntimeError: If the underlying `git diff` command returns a non-zero
            exit code. The error message contains the standard error output
            from the git command.
    """
    if not base_sha or not head_sha:
        return []

    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-status", base_sha, head_sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not compute changed files.")

    added_files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[0].startswith("A"):
            added_files.append(parts[1].strip())

    return added_files


def check_golden_path_compliance(repo_root: Path, target_files: list[str]) -> list[str]:
    r"""{'docstring': 'Validate Python source files for golden path compliance markers.\n\n    Scans a list of target files to enforce standardized structure. The function\n    filters the input to consider only Python source files (i.e., those ending\n    in `.py`, not `__init__.py`, and located within specific application\n    directories).\n\n    A file is considered compliant if its content contains at least one of the\n    predefined golden path markers or an explicit `golden-path: ignore` pragma.\n    Files that meet neither of these criteria are reported as violations. This\n    check is primarily intended for core service and worker modules.\n\n    Args:\n        repo_root: The absolute path to the root of the repository.\n        target_files: A list of file paths, relative to `repo_root`, to be\n            evaluated for compliance.\n\n    Returns:\n        A list of relative paths for all files that failed the compliance\n        check. Returns an empty list if no violations are found.'}."""
    violations = []
    for rel_path in target_files:
        if not rel_path.endswith(".py") or rel_path.endswith("__init__.py"):
            continue
        if not rel_path.startswith(LIVE_PYTHON_PREFIXES):
            continue

        file_path = repo_root / rel_path
        if not file_path.is_file():
            continue

        content = file_path.read_text(encoding="utf-8")

        # A pragma that provides an explicit exclusion mechanism for this check, intended for files that are not primary services or workers (e.g., helpers, data models, constants).
        # Validation is bypassed if the `IGNORE_GOLDEN_PATH_CHECK` pragma is detected, serving as an explicit declaration that the file's purpose does not align with the primary service or worker templates.
        if "golden-path: ignore" in content.lower():
            continue

        has_marker = any(marker in content for marker in GOLDEN_PATH_MARKERS)
        if not has_marker:
            violations.append(rel_path)

    return violations


def main() -> int:
    """Executes the Golden Path architectural fitness function from the command line.

    This function serves as the main entry point for a script that checks for
    compliance with 'Golden Path' templates. It identifies all files newly added
    within a specified Git commit range and verifies they adhere to official
    project templates, ensuring architectural consistency.

    The script is typically executed in a CI/CD environment where base and head
    commit SHAs are provided. When run locally without these arguments, it
    defaults to comparing the current state (HEAD) against the `origin/main`
    branch.

    The function parses the following command-line arguments:

    Args:
        --repo-root: The path to the repository root directory. Defaults to the
            current working directory.
        --base-sha: The base Git commit SHA for the diff comparison. If not
            provided, defaults to 'origin/main'.
        --head-sha: The head Git commit SHA for the diff comparison. If not
            provided, defaults to 'HEAD'.

    Returns:
        int: An exit code. Returns 0 on success, indicating either no new files
            were detected or all new files are compliant. Returns 1 if compliance
            violations are found or if an unexpected error occurs.
    """
    parser = argparse.ArgumentParser(
        description="Architectural Fitness Function: Golden Paths"
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--base-sha", type=str)
    parser.add_argument("--head-sha", type=str)

    args, unknown = parser.parse_known_args()

    if not args.base_sha or not args.head_sha:
        # Configures the diff operation to compare the current state against the `origin/main` branch when the script is executed in a local development environment.
        args.base_sha = "origin/main"
        args.head_sha = "HEAD"

    try:
        added_files = git_added_files(args.repo_root, args.base_sha, args.head_sha)
        violations = check_golden_path_compliance(args.repo_root, added_files)

        if violations:
            logger.error(
                "\n[ERROR] FITNESS FUNCTION FAILED: Golden Path violation detected."
            )
            logger.error(
                "Los siguientes archivos nuevos no parecen usar las plantillas oficiales:"
            )
            for v in violations:
                logger.error(f"  - {v}")
            logger.error(
                "\nAcción requerida: NUNCA crees archivos Python desde cero para lógica de negocio o tests."
            )
            logger.error(
                "DEBES usar las plantillas en 'templates/golden_paths/' que contienen los bloques"
            )
            logger.error(
                "estructurales requeridos (ej. '# --- START OF BUSINESS LOGIC ---' o '# --- ARRANGE ---').\n"
            )
            return 1

        if added_files:
            logger.info(
                "Architectural fitness check passed. %d new files comply with Golden Paths.",
                len(added_files),
            )
        return 0

    except Exception as e:
        logger.exception("Error executing fitness function: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
