from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from assessment_engine.application.tools import (
    validate_documentation_governance as validator,
)


def _write_markdown(path: Path, title: str = "Doc", body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "status: Verified",
                "owner: docs-governance",
                "source_of_truth:",
                "  - src/example.py",
                "last_verified_against: 2026-04-30",
                "applies_to:",
                "  - humans",
                "  - ai-agents",
                "doc_type: canonical",
                "diataxis: explanation",
                "verification_mode: code",
                "---",
                "",
                f"# {title}",
                "",
                body,
            ]
        ),
        encoding="utf-8",
    )


def _write_map(path: Path, entries: list[dict]) -> None:
    normalized_entries: list[dict] = []
    for entry in entries:
        normalized = {
            "diataxis": "explanation",
            "verification_mode": "code",
            **entry,
        }
        normalized_entries.append(normalized)

    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "last_reviewed": "2026-04-30",
                "freshness": {"verified_max_age_days": 120},
                "owners": {"docs-governance": {"scope": ["docs/"]}},
                "entries": normalized_entries,
                "automation_rules": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_source_linked_review_requires_matching_doc_change(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(repo_root / "docs/example.md")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "review_when_source_changes": ["src/example.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Example",
            }
        ],
    )

    monkeypatch.setattr(
        validator, "git_changed_files", lambda *_args, **_kwargs: ["src/example.py"]
    )

    errors = validator.validate_documentation_governance(
        repo_root, doc_map, "base", "head"
    )

    assert errors == [
        "docs/example.md: source-linked changes require documentation review in one of: docs/example.md"
    ]


def test_source_linked_review_passes_when_allowed_doc_changes(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(repo_root / "docs/example.md")
    _write_markdown(repo_root / "docs/related.md", title="Related")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "review_when_source_changes": ["src/example.py"],
                "review_paths_on_source_change": ["docs/example.md", "docs/related.md"],
                "last_verified_against": "2026-04-30",
                "notes": "Example",
            },
            {
                "path": "docs/related.md",
                "kind": "document",
                "title": "Related doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Related",
            },
        ],
    )

    monkeypatch.setattr(
        validator,
        "git_changed_files",
        lambda *_args, **_kwargs: ["src/example.py", "docs/related.md"],
    )

    errors = validator.validate_documentation_governance(
        repo_root, doc_map, "base", "head"
    )

    assert errors == []


def test_source_linked_review_configuration_must_reference_real_paths(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(repo_root / "docs/example.md")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "review_when_source_changes": ["src/missing.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Example",
            }
        ],
    )

    errors = validator.validate_documentation_governance(repo_root, doc_map, None, None)

    assert errors == [
        "docs/example.md: review_when_source_changes path does not exist: src/missing.py"
    ]


def test_markdown_link_targets_must_exist(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(repo_root / "docs/example.md", body="[missing](missing.md)")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Example",
            }
        ],
    )

    errors = validator.validate_documentation_governance(repo_root, doc_map, None, None)

    assert any("markdown link target does not exist: missing.md" in e for e in errors)


def test_markdown_anchor_targets_must_exist(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(
        repo_root / "docs/example.md", body="[missing anchor](target.md#nope)"
    )
    _write_markdown(repo_root / "docs/target.md", title="Target", body="## Present")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Example",
            },
            {
                "path": "docs/target.md",
                "kind": "document",
                "title": "Target doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Target",
            },
        ],
    )

    errors = validator.validate_documentation_governance(repo_root, doc_map, None, None)

    assert any(
        "markdown anchor target does not exist: target.md#nope" in e for e in errors
    )


def test_verified_documents_become_stale_after_threshold(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(repo_root / "docs/example.md")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "last_verified_against": "2026-01-01",
                "notes": "Example",
            }
        ],
    )

    errors = validator.validate_documentation_governance(
        repo_root,
        doc_map,
        None,
        None,
        today=date(2026, 6, 26),
    )

    assert any("Verified document is stale" in e for e in errors)


def test_markdown_coverage_requires_map_entry_or_collection(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "src").mkdir()
    (repo_root / "src/example.py").write_text("print('hello')\n", encoding="utf-8")
    _write_markdown(repo_root / "docs/example.md")
    _write_markdown(repo_root / "docs/unmapped.md")

    doc_map = repo_root / "docs/documentation-map.yaml"
    doc_map.parent.mkdir(parents=True, exist_ok=True)
    _write_map(
        doc_map,
        [
            {
                "path": "docs/example.md",
                "kind": "document",
                "title": "Example doc",
                "doc_type": "canonical",
                "status": "Verified",
                "owner": "docs-governance",
                "applies_to": ["humans", "ai-agents"],
                "source_of_truth": ["src/example.py"],
                "last_verified_against": "2026-04-30",
                "notes": "Example",
            }
        ],
    )

    errors = validator.validate_documentation_governance(repo_root, doc_map, None, None)

    assert any(
        "docs/unmapped.md: markdown document is not covered by documentation-map" in e
        for e in errors
    )
