from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

LIVE_PYTHON_PREFIXES = ("src/assessment_engine/", "tests/")

# Specifies the set of mandatory structural markers for new service and worker entry points.
# This validation step enforces adherence of new components to the prescribed 'Golden Path' architectural template.
GOLDEN_PATH_MARKERS = [
    "# --- START OF BUSINESS LOGIC ---",  # Specifies the set of mandatory structural markers for new worker and endpoint files.
    "# --- ARRANGE ---",  # Specifies the set of mandatory structural markers for new test files.
]


def git_added_files(
    repo_root: Path, base_sha: str | None, head_sha: str | None
) -> list[str]:
    """Extract file paths with an 'Added' status between two Git commits.

    Executes `git diff --name-status <base_sha> <head_sha>` within the specified
    repository and parses the output to identify files that have been added.
    The function returns an empty list without executing the git command if
    either `base_sha` or `head_sha` is `None` or an empty string.

    Args:
        repo_root: The file system path to the root of the Git repository.
        base_sha: The base commit SHA for the diff comparison.
        head_sha: The head commit SHA for the diff comparison.

    Returns:
        A list of file paths, relative to the repository root, that were
        added between the specified commits. Returns an empty list if no
        files were added or if either SHA is not provided.

    Raises:
        RuntimeError: If the underlying `git diff` command returns a non-zero
            exit code, indicating an error during execution.
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
    """Identifies Python service entry points that lack golden path markers.

    Scans a list of Python files to validate their compliance with the golden
    path architecture. The function filters for potential service or worker
    entry points based on file extension and path prefixes, excluding certain
    files like `__init__.py`.

    For each candidate file, it reads the content to check for predefined
    golden path markers. A file is considered non-compliant if it is identified
    as an entry point but does not contain any of the required markers.

    Files can be explicitly exempted from this check by including the pragma
    `golden-path: ignore` (case-insensitive) anywhere within their content.

    Args:
        repo_root: The absolute path to the root of the repository.
        target_files: A list of file paths, relative to `repo_root`, to be
            checked for compliance.

    Returns:
        A list of relative file paths that are non-compliant. A file is
        deemed non-compliant if it is identified as a service entry point,
        lacks a required golden path marker, and is not explicitly ignored
        via a pragma.
    """
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

        # Defines the pragma for explicitly exempting a file from Golden Path validation.
        # Inclusion of this pragma asserts that the file is not a primary service or worker entry point, thus exempting it from structural validation.
        if "golden-path: ignore" in content.lower():
            continue

        has_marker = any(marker in content for marker in GOLDEN_PATH_MARKERS)
        if not has_marker:
            violations.append(rel_path)

    return violations


def main() -> int:
    """Executes the Golden Path architectural fitness function.

    This function serves as the script's main entry point. It orchestrates the
    architectural compliance check by parsing command-line arguments to define
    a git commit range. If base and head SHAs are not provided via arguments,
    it defaults to the range between 'origin/main' and 'HEAD'.

    The core logic identifies all files newly added within this commit range and
    validates their structure against predefined 'Golden Path' templates. If
    any non-compliant files are discovered, the function logs detailed violation
    messages and terminates with a non-zero exit code to signal failure,
    for instance in a CI/CD environment. If all new files are compliant, a
    success message is logged, and the function returns 0.

    Internal exceptions during execution are caught, logged, and also result in a
    non-zero exit code.

    Returns:
        int: An exit code. Returns 0 if all new files are compliant, and 1 if
            violations are found or an internal error occurs.
    """
    parser = argparse.ArgumentParser(
        description="Architectural Fitness Function: Golden Paths"
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--base-sha", type=str)
    parser.add_argument("--head-sha", type=str)

    args, unknown = parser.parse_known_args()

    if not args.base_sha or not args.head_sha:
        #
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
