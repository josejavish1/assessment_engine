# golden-path: ignore
from __future__ import annotations

from pathlib import Path

from assessment_engine.application.tools import (
    validate_documentation_snippets as v_snippets,
)


def test_should_validate_repo_relative_path():
    assert v_snippets.should_validate_repo_relative_path("./src/domain") is True
    assert v_snippets.should_validate_repo_relative_path(".venv/lib") is True
    assert v_snippets.should_validate_repo_relative_path("docs/contracts") is True
    assert v_snippets.should_validate_repo_relative_path("some_unrelated_dir") is False


def test_validate_command_flags(tmp_path: Path):
    # Create a mock local python script with argparse
    script = tmp_path / "mock_script.py"
    script.write_text(
        """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--repo-root")
parser.add_argument("--today")
parser.parse_args()
        """,
        encoding="utf-8",
    )

    # Test valid flags
    errors = v_snippets.validate_command_flags(
        tmp_path, "python mock_script.py --repo-root . --today 2026-06-26"
    )
    assert len(errors) == 0

    # Test invalid flag
    errors = v_snippets.validate_command_flags(
        tmp_path, "python mock_script.py --invalid-flag 123"
    )
    assert len(errors) == 1
    assert "references invalid or non-existent flag '--invalid-flag'" in errors[0]


def test_validate_documentation_snippets_with_mock_md(tmp_path: Path):
    # Mock documentation map
    doc_map_path = tmp_path / "doc_map.yaml"
    doc_map_path.write_text(
        """
entries:
  - path: docs/mock_doc.md
    kind: document
        """,
        encoding="utf-8",
    )

    # Mock markdown document
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    md_doc = docs_dir / "mock_doc.md"
    md_doc.write_text(
        """
# Onboarding

```bash
python src/assessment_engine/application/tools/validate_documentation_governance.py --repo-root . --today 2026-06-26
```
        """,
        encoding="utf-8",
    )

    # Let's verify that a valid local run passes
    # Wait, we need to pass the real repo root so it can find the real tools script
    real_repo_root = Path(__file__).resolve().parents[2]
    errors = v_snippets.validate_documentation_snippets(
        real_repo_root, real_repo_root / "docs/documentation-map.yaml"
    )
    # All snippets in the real repo should pass cleanly!
    assert len(errors) == 0
