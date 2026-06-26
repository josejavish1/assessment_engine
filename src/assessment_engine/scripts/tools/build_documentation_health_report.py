# golden-path: ignore
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

from assessment_engine.scripts.tools import (
    validate_documentation_governance as governance,
)


def build_documentation_health_report(
    repo_root: Path,
    documentation_map_path: Path,
    output_path: Path,
    today: date,
) -> None:
    documentation_map = governance.load_yaml(documentation_map_path)
    entries = [
        entry for entry in documentation_map.get("entries", []) if isinstance(entry, dict)
    ]

    status_counts = Counter(entry.get("status") for entry in entries)
    doc_type_counts = Counter(entry.get("doc_type") for entry in entries)
    diataxis_counts = Counter(entry.get("diataxis") for entry in entries)
    verification_mode_counts = Counter(entry.get("verification_mode") for entry in entries)

    covered_paths: set[str] = set()
    collection_only: list[str] = []
    for entry in entries:
        path = entry.get("path")
        kind = entry.get("kind")
        if not isinstance(path, str) or not isinstance(kind, str):
            continue
        if kind == "document":
            covered_paths.add(path)

    include_patterns = documentation_map.get("coverage", {}).get(
        "include", governance.DEFAULT_COVERAGE_INCLUDE
    )
    exclude_patterns = documentation_map.get("coverage", {}).get(
        "exclude", governance.DEFAULT_COVERAGE_EXCLUDE
    )

    discovered_docs: list[str] = []
    for pattern in include_patterns:
        for discovered_path in repo_root.glob(pattern):
            if discovered_path.is_file():
                normalized = governance.normalize_repo_path(discovered_path, repo_root)
                if governance.matches_any_pattern(normalized, exclude_patterns):
                    continue
                discovered_docs.append(normalized)

    discovered_docs = sorted(set(discovered_docs))
    missing_entries = [path for path in discovered_docs if path not in covered_paths]

    stale_verified: list[dict[str, object]] = []
    verified_max_age_days = documentation_map.get("freshness", {}).get(
        "verified_max_age_days", governance.DEFAULT_VERIFIED_MAX_AGE_DAYS
    )
    for entry in entries:
        if entry.get("status") != "Verified":
            continue
        raw_value = entry.get("last_verified_against")
        if not isinstance(raw_value, str):
            continue
        verified_date = date.fromisoformat(raw_value)
        age_days = (today - verified_date).days
        if age_days > verified_max_age_days:
            stale_verified.append(
                {
                    "path": entry.get("path"),
                    "age_days": age_days,
                    "verified_max_age_days": verified_max_age_days,
                }
            )

    for doc_path in discovered_docs:
        if doc_path in covered_paths:
            continue
        if any(
            entry.get("kind") == "collection"
            and isinstance(entry.get("path"), str)
            and governance.is_subpath(doc_path, entry["path"])
            for entry in entries
        ):
            collection_only.append(doc_path)

    report = {
        "generated_on": today.isoformat(),
        "summary": {
            "entry_count": len(entries),
            "covered_document_count": len(discovered_docs),
            "missing_explicit_entries": len(missing_entries),
            "collection_only_documents": len(collection_only),
        },
        "status_counts": dict(status_counts),
        "doc_type_counts": dict(doc_type_counts),
        "diataxis_counts": dict(diataxis_counts),
        "verification_mode_counts": dict(verification_mode_counts),
        "stale_verified": stale_verified,
        "missing_entries": missing_entries,
        "collection_only_documents": collection_only,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    stale_lines = (
        [f"- `{item['path']}`: `{item['age_days']}` days" for item in stale_verified]
        if stale_verified
        else ["- none"]
    )
    output_path.with_suffix(".md").write_text(
        "\n".join(
            [
                "# Documentation health report",
                "",
                f"- generated_on: `{today.isoformat()}`",
                f"- entry_count: `{len(entries)}`",
                f"- covered_document_count: `{len(discovered_docs)}`",
                f"- missing_explicit_entries: `{len(missing_entries)}`",
                f"- collection_only_documents: `{len(collection_only)}`",
                "",
                "## Status counts",
                "",
                *[f"- `{key}`: `{value}`" for key, value in sorted(status_counts.items())],
                "",
                "## Stale verified",
                "",
                *stale_lines,
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--today", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_documentation_health_report(
        repo_root=Path(args.repo_root).resolve(),
        documentation_map_path=Path(args.documentation_map).resolve(),
        output_path=Path(args.output).resolve(),
        today=date.fromisoformat(args.today),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
