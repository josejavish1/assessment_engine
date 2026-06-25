from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
from datetime import date, datetime
from pathlib import Path

import yaml  #

VALID_STATUSES = {"Verified", "Needs Review", "Draft", "Deprecated"}
VALID_DOC_TYPES = {"canonical", "operational", "reference_generated", "archived"}
VALID_KINDS = {"document", "collection"}
FRONT_MATTER_REQUIRED = {
    "status",
    "owner",
    "source_of_truth",
    "last_verified_against",
    "applies_to",
    "doc_type",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_yaml(path: Path) -> dict:
    r"""{'docstring': 'Safely loads and parses a YAML file from a given path.\n\nArgs:\n    path: The `pathlib.Path` object pointing to the YAML file to load.\n\nReturns:\n    The parsed content of the YAML file. An empty dictionary is returned if\n    the parsed data is falsy (e.g., the file is empty or contains\n    `null`, `0`, or an empty string).\n\nRaises:\n    FileNotFoundError: If the file at the specified path does not exist.\n    yaml.YAMLError: If the file contains invalid YAML syntax.'}."""
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def read_front_matter(path: Path) -> dict | None:
    """Parses YAML front matter from the beginning of a text file.

    The front matter is defined as a YAML document enclosed between `---`
    delimiters at the very start of the file. This function extracts and parses
    this block into a dictionary.

    Args:
        path (pathlib.Path): The file system path to the file to read.

    Returns:
        dict | None: A dictionary of the parsed front matter. Returns None if the
            file does not begin with a valid `---` delimited block or if the
            parsed content is not a dictionary.

    Raises:
        FileNotFoundError: If the file at `path` cannot be found.
        yaml.YAMLError: If the front matter block contains malformed YAML.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return None

    front_matter = yaml.safe_load(parts[1]) or {}
    return front_matter if isinstance(front_matter, dict) else None


def path_exists(repo_root: Path, raw_path: str) -> bool:
    """Check if a given path exists relative to the repository root."""
    return (repo_root / raw_path).exists()


def is_valid_date_value(value: object) -> bool:
    """Return True if the object is a date, datetime, or 'YYYY-MM-DD' string."""
    if isinstance(value, str):
        return bool(DATE_RE.match(value))
    if isinstance(value, (date, datetime)):
        return True
    return False


def is_subpath(changed_path: str, required_path: str) -> bool:
    """Determine if a path is a subpath of, or identical to, another path."""
    if changed_path == required_path:
        return True
    return changed_path.startswith(required_path.rstrip("/") + "/")


def matches_any_pattern(path: str, patterns: list[str]) -> bool:
    """Determine if a path matches any of the provided glob patterns."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def validate_path_list_field(
    repo_root: Path,
    entry_path: str,
    field_name: str,
    raw_value: object,
    errors: list[str],
) -> list[str] | None:
    r"""{'docstring': "Validates a configuration value is a non-empty list of existing paths.\n\n    Verifies that the provided `raw_value` is a non-empty list of non-empty\n    strings. Each string element is subsequently checked to ensure it corresponds\n    to a path that exists relative to the `repo_root`.\n\n    If any validation step fails, a formatted error message is appended to the\n    `errors` list, and the function returns `None`.\n\n    Args:\n        repo_root: The absolute path to the repository's root directory, which\n            serves as the base for path existence checks.\n        entry_path: The source path of the configuration entry being validated,\n            used to provide context in error messages.\n        field_name: The key name of the field being validated, used to provide\n            context in error messages.\n        raw_value: The object from the configuration data to be validated.\n        errors: A list that accumulates validation error message strings.\n\n    Returns:\n        The original list of path strings if all validation passes, otherwise `None`."}."""
    if not isinstance(raw_value, list) or not raw_value:
        errors.append(f"{entry_path}: {field_name} must be a non-empty list")
        return None

    normalized: list[str] = []
    for item in raw_value:
        if not isinstance(item, str) or not item.strip():
            errors.append(
                f"{entry_path}: {field_name} entries must be non-empty strings"
            )
            return None
        if not path_exists(repo_root, item):
            errors.append(f"{entry_path}: {field_name} path does not exist: {item}")
            return None
        normalized.append(item)

    return normalized


def git_changed_files(
    repo_root: Path, base_sha: str | None, head_sha: str | None
) -> list[str]:
    """Compute the list of files changed between two Git commits.

    Executes `git diff --name-only` to generate a list of file paths modified
    between two commits. This function handles invalid or special-case SHAs,
    such as a null `base_sha` for an initial commit, by returning an empty list.

    Args:
        repo_root: The path to the root of the Git repository.
        base_sha: The base commit SHA for the comparison. An empty list is
            returned if this is `None`, an empty string, or the null SHA (a
            string of all zeros).
        head_sha: The head commit SHA for the comparison. An empty list is
            returned if this is `None` or an empty string.

    Returns:
        A list of file paths relative to the repository root that were modified
        between the base and head commits.

    Raises:
        RuntimeError: If the underlying `git diff` command returns a non-zero exit
            code. The error message will contain the `stderr` from the command.
    """
    if not base_sha or not head_sha:
        return []
    if re.fullmatch(r"0+", base_sha):
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


def validate_entry(repo_root: Path, entry: dict, errors: list[str]) -> None:
    """Validates a single documentation governance entry against a comprehensive ruleset.

    This function performs several checks, including:
    - Presence of all required fields in the entry.
    - Adherence of field values (e.g., 'status', 'kind') to predefined allowed sets.
    - Type correctness for fields such as lists and booleans.
    - Existence of file system paths specified in the entry, resolved relative to
      the repository root.
    - For Markdown documents, it validates the presence and content of the YAML
      front matter and ensures its consistency with the governance entry.

    All discovered validation failures are appended as descriptive strings to the
    `errors` list.

    Args:
        repo_root: The absolute path to the repository root, used as a base for
            resolving relative paths.
        entry: A dictionary representing the documentation governance entry to
            validate.
        errors: A list to which validation error strings will be appended.
            This list is modified in-place.
    """
    required = {
        "path",
        "kind",
        "title",
        "doc_type",
        "status",
        "owner",
        "applies_to",
        "source_of_truth",
        "last_verified_against",
        "notes",
    }
    missing = sorted(required - set(entry))
    if missing:
        errors.append(
            f"Entry {entry.get('path', '<unknown>')} is missing fields: {', '.join(missing)}"
        )
        return

    entry_path = entry["path"]
    kind = entry["kind"]
    status = entry["status"]
    doc_type = entry["doc_type"]
    applies_to = entry["applies_to"]
    source_of_truth = entry["source_of_truth"]
    last_verified_against = entry["last_verified_against"]

    if kind not in VALID_KINDS:
        errors.append(f"{entry_path}: invalid kind '{kind}'")
    if status not in VALID_STATUSES:
        errors.append(f"{entry_path}: invalid status '{status}'")
    if doc_type not in VALID_DOC_TYPES:
        errors.append(f"{entry_path}: invalid doc_type '{doc_type}'")
    if not isinstance(applies_to, list) or not applies_to:
        errors.append(f"{entry_path}: applies_to must be a non-empty list")
    if not isinstance(source_of_truth, list) or not source_of_truth:
        errors.append(f"{entry_path}: source_of_truth must be a non-empty list")
    if not is_valid_date_value(last_verified_against):
        errors.append(f"{entry_path}: last_verified_against must use YYYY-MM-DD")

    absolute_path = repo_root / entry_path
    if not absolute_path.exists():
        errors.append(f"{entry_path}: mapped path does not exist")
        return

    if kind == "document" and not absolute_path.is_file():
        errors.append(f"{entry_path}: expected a file for kind=document")
    if kind == "collection" and not absolute_path.is_dir():
        errors.append(f"{entry_path}: expected a directory for kind=collection")

    for truth_path in source_of_truth:
        if not path_exists(repo_root, truth_path):
            errors.append(
                f"{entry_path}: source_of_truth path does not exist: {truth_path}"
            )

    enforce_on_source_changes = entry.get("enforce_on_source_changes")
    if enforce_on_source_changes is not None and not isinstance(
        enforce_on_source_changes, bool
    ):
        errors.append(f"{entry_path}: enforce_on_source_changes must be a boolean")

    if "review_when_source_changes" in entry:
        validate_path_list_field(
            repo_root=repo_root,
            entry_path=entry_path,
            field_name="review_when_source_changes",
            raw_value=entry["review_when_source_changes"],
            errors=errors,
        )

    if "review_paths_on_source_change" in entry:
        validate_path_list_field(
            repo_root=repo_root,
            entry_path=entry_path,
            field_name="review_paths_on_source_change",
            raw_value=entry["review_paths_on_source_change"],
            errors=errors,
        )

    if (
        absolute_path.is_file()
        and absolute_path.suffix == ".md"
        and entry_path != ".github/pull_request_template.md"
    ):
        front_matter = read_front_matter(absolute_path)
        if front_matter is None:
            errors.append(
                f"{entry_path}: markdown document is missing YAML front matter"
            )
            return

        missing_front_matter = sorted(FRONT_MATTER_REQUIRED - set(front_matter))
        if missing_front_matter:
            errors.append(
                f"{entry_path}: front matter missing fields: {', '.join(missing_front_matter)}"
            )
            return

        if front_matter.get("status") not in VALID_STATUSES:
            errors.append(f"{entry_path}: front matter has invalid status")
        if front_matter.get("doc_type") not in VALID_DOC_TYPES:
            errors.append(f"{entry_path}: front matter has invalid doc_type")
        if not isinstance(
            front_matter.get("source_of_truth"), list
        ) or not front_matter.get("source_of_truth"):
            errors.append(
                f"{entry_path}: front matter source_of_truth must be a non-empty list"
            )
        if not isinstance(front_matter.get("applies_to"), list) or not front_matter.get(
            "applies_to"
        ):
            errors.append(
                f"{entry_path}: front matter applies_to must be a non-empty list"
            )
        if not is_valid_date_value(front_matter.get("last_verified_against", "")):
            errors.append(
                f"{entry_path}: front matter last_verified_against must use YYYY-MM-DD"
            )


def validate_automation_rules(
    repo_root: Path, rules: list[dict], changed_files: list[str], errors: list[str]
) -> None:
    r"""{'docstring': "Validate documentation governance rules against a set of changed files.\n\n    This function enforces documentation policies by checking a set of rules\n    against a list of changed files. It operates in two stages: rule schema\n    validation and rule application.\n\n    First, it validates the structural integrity of each rule, ensuring that\n    required keys (`name`, `when_changed`, `require_review_of`) are present,\n    that list values are non-empty, and that specified documentation paths\n    exist within the repository.\n\n    Second, it applies the rule logic. If any changed file matches a source\n    pattern in a rule's `when_changed` list, the function then verifies that at\n    least one of the changed files is also located within one of the\n    corresponding `require_review_of` documentation directories.\n\n    Failures from either stage are collected as descriptive strings and appended\n    to the `errors` list argument. The function does not raise exceptions for\n    validation failures.\n\n    Args:\n        repo_root: The absolute path to the root of the repository.\n        rules: A list of rule dictionaries to be validated and applied. Each\n            dictionary must contain:\n            - name (str): A human-readable identifier for the rule.\n            - when_changed (list[str]): A non-empty list of file glob patterns.\n            - require_review_of (list[str]): A non-empty list of directory paths\n              relative to `repo_root`.\n        changed_files: A list of repository-relative file paths that have been\n            modified.\n        errors: An output list to which validation error messages are appended.\n            This argument is modified in-place.\n\n    Returns:\n        None. The function operates via side effect on the `errors` list."}."""
    for rule in rules:
        required = {"name", "when_changed", "require_review_of"}
        missing = sorted(required - set(rule))
        if missing:
            errors.append(
                f"Automation rule {rule.get('name', '<unknown>')} is missing: {', '.join(missing)}"
            )
            continue

        name = rule["name"]
        when_changed = rule["when_changed"]
        require_review_of = rule["require_review_of"]

        if not isinstance(when_changed, list) or not when_changed:
            errors.append(
                f"Automation rule {name}: when_changed must be a non-empty list"
            )
            continue
        if not isinstance(require_review_of, list) or not require_review_of:
            errors.append(
                f"Automation rule {name}: require_review_of must be a non-empty list"
            )
            continue

        for path in require_review_of:
            if not (repo_root / path).exists():
                errors.append(
                    f"Automation rule {name}: require_review_of path does not exist: {path}"
                )

        if not changed_files:
            continue

        if not any(
            matches_any_pattern(changed, when_changed) for changed in changed_files
        ):
            continue

        if any(
            any(
                is_subpath(changed, required_path)
                for required_path in require_review_of
            )
            for changed in changed_files
        ):
            continue

        errors.append(
            f"Automation rule {name}: changed files require documentation review in one of: "
            + ", ".join(require_review_of)
        )


def validate_source_linked_review(
    entries: list[dict], changed_files: list[str], errors: list[str]
) -> None:
    r"""{'docstring': "Validate that modifications to source files trigger a documentation review.\n\n    Enforces a governance rule requiring documentation reviews for source code\n    changes. This function iterates through each documentation entry\n    configuration to determine if source-change validation is enabled, typically\n    via the `enforce_on_source_changes` or `review_when_source_changes` keys.\n\n    If validation is enabled for an entry, the function identifies the set of\n    source directories to monitor, using `review_when_source_changes` if\n    present, otherwise falling back to `source_of_truth`. It also identifies\n    the documentation paths that must be reviewed, using\n    `review_paths_on_source_change` or defaulting to the entry's primary `path`.\n\n    The function then checks if any path in `changed_files` is a subpath of a\n    monitored source directory. If a match is found, it ensures that at least one\n    path in `changed_files` is also a subpath of a required documentation review\n    path. If this condition is not met, a descriptive error is appended to the\n    `errors` list.\n\n    Args:\n        entries: A list of documentation entry configurations. Each dictionary\n            represents a documentation entity and may contain the following keys:\n            `path` (str): The primary path to the documentation file.\n            `enforce_on_source_changes` (bool): If true, enables this check.\n            `review_when_source_changes` (list[str]): A list of source file or\n                directory paths that trigger a documentation review upon change.\n                This overrides `source_of_truth` for this specific check.\n            `source_of_truth` (list[str]): A fallback list of source paths if\n                `review_when_source_changes` is not provided but the check is\n                enabled.\n            `review_paths_on_source_change` (list[str]): A list of documentation\n                paths that must be modified if a linked source file changes.\n                Defaults to a list containing only the main entry `path`.\n        changed_files: A list of repository-relative file paths that have been\n            modified in the current changeset.\n        errors: An output list to which validation error messages are appended.\n            This list is modified in-place."}."""
    if not changed_files:
        return

    for entry in entries:
        entry_path = entry.get("path")
        if not entry_path:
            continue

        enforce_on_source_changes = entry.get("enforce_on_source_changes")
        review_when_source_changes = entry.get("review_when_source_changes")

        if review_when_source_changes is None and not enforce_on_source_changes:
            continue

        effective_review_sources = (
            review_when_source_changes
            if review_when_source_changes is not None
            else entry.get("source_of_truth")
        )
        effective_review_paths = entry.get(
            "review_paths_on_source_change", [entry_path]
        )

        if (
            not isinstance(effective_review_sources, list)
            or not effective_review_sources
        ):
            continue
        if not isinstance(effective_review_paths, list) or not effective_review_paths:
            continue

        source_change_detected = any(
            is_subpath(changed, review_source)
            for changed in changed_files
            for review_source in effective_review_sources
        )
        if not source_change_detected:
            continue

        documentation_review_detected = any(
            is_subpath(changed, review_path)
            for changed in changed_files
            for review_path in effective_review_paths
        )
        if documentation_review_detected:
            continue

        errors.append(
            f"{entry_path}: source-linked changes require documentation review in one of: "
            + ", ".join(effective_review_paths)
        )


def validate_documentation_governance(
    repo_root: Path,
    documentation_map_path: Path,
    base_sha: str | None,
    head_sha: str | None,
) -> list[str]:
    """Validates documentation governance by comparing Git changes against a map file.

    This function orchestrates the end-to-end validation of documentation
    governance. The process involves several sequential stages:
    1.  Loading and performing structural validation on the documentation map
        YAML file, ensuring the presence and correct types of top-level keys
        like 'entries' and 'owners'.
    2.  Iterating through each entry in the map, validating its schema and
        checking for duplicate path definitions.
    3.  Identifying the set of files modified between the provided base and head
        Git SHAs.
    4.  Applying 'automation_rules' from the map against the set of changed
        files.
    5.  Enforcing 'source-linked review' rules based on the defined ownership
        for modified documentation paths.

    All discovered validation failures are aggregated and returned.

    Args:
        repo_root: The absolute path to the root of the Git repository.
        documentation_map_path: The path to the documentation-map.yaml
            configuration file.
        base_sha: The base Git commit SHA for comparison. If None, the
            comparison is performed against the working tree.
        head_sha: The head Git commit SHA for comparison. If None, defaults to the
            current repository HEAD.

    Returns:
        A list of strings, each describing a distinct validation error. An
        empty list indicates that all governance checks passed.

    Raises:
        FileNotFoundError: If `documentation_map_path` does not exist.
        yaml.YAMLError: If the documentation map file contains invalid YAML syntax.
    """
    errors: list[str] = []
    documentation_map = load_yaml(documentation_map_path)

    if "entries" not in documentation_map or not isinstance(
        documentation_map["entries"], list
    ):
        return ["documentation-map.yaml must define an entries list"]

    if "owners" not in documentation_map or not isinstance(
        documentation_map["owners"], dict
    ):
        errors.append("documentation-map.yaml must define owners")

    seen_paths: set[str] = set()
    for entry in documentation_map["entries"]:
        if not isinstance(entry, dict):
            errors.append("documentation-map.yaml contains a non-object entry")
            continue
        entry_path = entry.get("path")
        if entry_path in seen_paths:
            errors.append(f"Duplicate documentation-map entry for path: {entry_path}")
            continue
        seen_paths.add(entry_path)  #
        validate_entry(repo_root, entry, errors)

    changed_files = git_changed_files(repo_root, base_sha, head_sha)
    validate_automation_rules(
        repo_root,
        documentation_map.get("automation_rules", []),
        changed_files,
        errors,
    )
    validate_source_linked_review(documentation_map["entries"], changed_files, errors)

    return errors


def parse_args() -> argparse.Namespace:
    """Parse and return the defined command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    return parser.parse_args()


def main() -> int:
    """Executes the main entry point for the documentation governance CLI.

    This function orchestrates the validation process by parsing command-line
    arguments, resolving repository and documentation map paths, and then
    invoking the core `validate_documentation_governance` logic. Any resulting
    validation errors are printed to standard output.

    Returns:
        int: An exit code. `0` for successful validation, `1` if errors are
            found.
    """
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    documentation_map_path = Path(args.documentation_map).resolve()

    errors = validate_documentation_governance(
        repo_root=repo_root,
        documentation_map_path=documentation_map_path,
        base_sha=args.base_sha,
        head_sha=args.head_sha,
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Documentation governance validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
