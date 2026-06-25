from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
from datetime import date, datetime
from pathlib import Path

import yaml  # type: ignore[import-untyped]

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
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
DEFAULT_COVERAGE_INCLUDE = ["README.md", "AGENTS.md", "CHATGPT.md", "docs/**/*.md"]
DEFAULT_COVERAGE_EXCLUDE = [
    "docs/reference/generated/legacy-gemini/**",
    "docs/strategy/**",
]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def read_front_matter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return None

    front_matter = yaml.safe_load(parts[1]) or {}
    return front_matter if isinstance(front_matter, dict) else None


def path_exists(repo_root: Path, raw_path: str) -> bool:
    return (repo_root / raw_path).exists()


def is_valid_date_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(DATE_RE.match(value))
    if isinstance(value, (date, datetime)):
        return True
    return False


def is_subpath(changed_path: str, required_path: str) -> bool:
    if changed_path == required_path:
        return True
    return changed_path.startswith(required_path.rstrip("/") + "/")


def normalize_repo_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def should_validate_markdown_target(target: str) -> bool:
    stripped = target.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", stripped):
        return False
    return True


def markdown_link_target_path(current_path: Path, target: str) -> Path | None:
    if not should_validate_markdown_target(target):
        return None

    local_target = target.split("#", 1)[0].split("?", 1)[0]
    if not local_target:
        return None
    return (current_path.parent / local_target).resolve()


def validate_markdown_links(
    current_path: Path, entry_path: str, errors: list[str]
) -> None:
    text = current_path.read_text(encoding="utf-8")
    for match in MARKDOWN_LINK_RE.finditer(text):
        target_path = markdown_link_target_path(current_path, match.group(1))
        if target_path is None:
            continue
        if not target_path.exists():
            errors.append(
                f"{entry_path}: markdown link target does not exist: {match.group(1)}"
            )


def is_path_covered_by_entry(path: str, entry_path: str, kind: str) -> bool:
    if kind == "document":
        return path == entry_path
    if kind == "collection":
        return is_subpath(path, entry_path)
    return False


def matches_any_pattern(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def validate_front_matter_fields(
    front_matter: dict, entry_path: str, error_prefix: str, errors: list[str]
) -> None:
    missing_front_matter = sorted(FRONT_MATTER_REQUIRED - set(front_matter))
    if missing_front_matter:
        errors.append(
            f"{entry_path}: {error_prefix} missing fields: "
            + ", ".join(missing_front_matter)
        )
        return

    if front_matter.get("status") not in VALID_STATUSES:
        errors.append(f"{entry_path}: {error_prefix} has invalid status")
    if front_matter.get("doc_type") not in VALID_DOC_TYPES:
        errors.append(f"{entry_path}: {error_prefix} has invalid doc_type")
    if not isinstance(
        front_matter.get("source_of_truth"), list
    ) or not front_matter.get("source_of_truth"):
        errors.append(
            f"{entry_path}: {error_prefix} source_of_truth must be a non-empty list"
        )
    if not isinstance(front_matter.get("applies_to"), list) or not front_matter.get(
        "applies_to"
    ):
        errors.append(
            f"{entry_path}: {error_prefix} applies_to must be a non-empty list"
        )
    if not is_valid_date_value(front_matter.get("last_verified_against", "")):
        errors.append(
            f"{entry_path}: {error_prefix} last_verified_against must use YYYY-MM-DD"
        )


def validate_documentation_coverage(
    repo_root: Path, documentation_map: dict, entries: list[dict], errors: list[str]
) -> None:
    coverage = documentation_map.get("coverage", {})
    include_patterns = coverage.get("include", DEFAULT_COVERAGE_INCLUDE)
    exclude_patterns = coverage.get("exclude", DEFAULT_COVERAGE_EXCLUDE)

    if not isinstance(include_patterns, list) or not include_patterns:
        errors.append(
            "documentation-map.yaml coverage.include must be a non-empty list"
        )
        return
    if not isinstance(exclude_patterns, list):
        errors.append("documentation-map.yaml coverage.exclude must be a list")
        return

    governed_paths: set[str] = set()
    for pattern in include_patterns:
        if not isinstance(pattern, str) or not pattern:
            errors.append(
                "documentation-map.yaml coverage.include entries must be strings"
            )
            continue
        for discovered_path in repo_root.glob(pattern):
            if discovered_path.is_file():
                governed_paths.add(normalize_repo_path(discovered_path, repo_root))

    for governed_path in sorted(governed_paths):
        if matches_any_pattern(governed_path, exclude_patterns):
            continue

        if not any(
            is_path_covered_by_entry(governed_path, entry["path"], entry["kind"])
            for entry in entries
            if isinstance(entry.get("path"), str) and isinstance(entry.get("kind"), str)
        ):
            errors.append(
                f"{governed_path}: markdown document is not covered by documentation-map"
            )
            continue

        absolute_path = repo_root / governed_path
        front_matter = read_front_matter(absolute_path)
        if front_matter is None:
            errors.append(
                f"{governed_path}: covered markdown document is missing YAML front matter"
            )
            continue

        validate_front_matter_fields(
            front_matter, governed_path, "covered markdown front matter", errors
        )
        if front_matter.get("doc_type") in {"canonical", "operational"}:
            validate_markdown_links(absolute_path, governed_path, errors)


def validate_path_list_field(
    repo_root: Path,
    entry_path: str,
    field_name: str,
    raw_value: object,
    errors: list[str],
) -> list[str] | None:
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

        validate_front_matter_fields(front_matter, entry_path, "front matter", errors)
        if doc_type in {"canonical", "operational"}:
            validate_markdown_links(absolute_path, entry_path, errors)


def validate_automation_rules(
    repo_root: Path, rules: list[dict], changed_files: list[str], errors: list[str]
) -> None:
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
    valid_entries: list[dict] = []
    for entry in documentation_map["entries"]:
        if not isinstance(entry, dict):
            errors.append("documentation-map.yaml contains a non-object entry")
            continue
        entry_path = entry.get("path")
        if entry_path in seen_paths:
            errors.append(f"Duplicate documentation-map entry for path: {entry_path}")
            continue
        if not isinstance(entry_path, str):
            errors.append("documentation-map entry path must be a string")
            continue
        seen_paths.add(entry_path)
        validate_entry(repo_root, entry, errors)
        valid_entries.append(entry)

    validate_documentation_coverage(repo_root, documentation_map, valid_entries, errors)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    return parser.parse_args()


def main() -> int:
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
