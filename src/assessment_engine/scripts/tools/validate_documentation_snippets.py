# golden-path: ignore
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

from assessment_engine.scripts.tools import (
    validate_documentation_governance as governance,
)


FENCED_BLOCK_RE = re.compile(r"```(?:bash|sh|shell|console)?\n(.*?)```", re.DOTALL)
PYTHON_MODULE_RE = re.compile(r"(?:^|\s)-m\s+([a-zA-Z0-9_\.]+)")
REPO_RELATIVE_HINTS = {".venv", ".github", "bin", "docs", "src", "templates", "tests"}


def should_validate_repo_relative_path(token: str) -> bool:
    normalized = token.lstrip("./")
    first_segment = normalized.split("/", 1)[0]
    return first_segment in REPO_RELATIVE_HINTS


def validate_documentation_snippets(
    repo_root: Path, documentation_map_path: Path
) -> list[str]:
    documentation_map = governance.load_yaml(documentation_map_path)
    errors: list[str] = []

    for entry in documentation_map.get("entries", []):
        if not isinstance(entry, dict) or entry.get("kind") != "document":
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path.endswith(".md"):
            continue
        absolute_path = repo_root / path
        if not absolute_path.exists():
            continue

        text = absolute_path.read_text(encoding="utf-8")
        for block in FENCED_BLOCK_RE.findall(text):
            for line in block.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                module_match = PYTHON_MODULE_RE.search(stripped)
                if module_match:
                    module_name = module_match.group(1)
                    if importlib.util.find_spec(module_name) is None:
                        errors.append(
                            f"{path}: code block references missing Python module '{module_name}'"
                        )

                for token in stripped.split():
                    cleaned = token.strip("()[]'\"`,")
                    if cleaned.startswith(("./", "../")):
                        candidates = [(absolute_path.parent / cleaned).resolve()]
                        if cleaned.startswith("./") and should_validate_repo_relative_path(
                            cleaned
                        ):
                            candidates.append((repo_root / cleaned[2:]).resolve())
                        if any(candidate.exists() for candidate in candidates):
                            continue
                        if not should_validate_repo_relative_path(cleaned):
                            continue
                        errors.append(
                            f"{path}: code block references missing local path '{cleaned}'"
                        )
                    elif cleaned.startswith(
                        ("src/", ".github/", "docs/", "tests/", "templates/", "bin/")
                    ):
                        if not (repo_root / cleaned).exists():
                            errors.append(
                                f"{path}: code block references missing repo path '{cleaned}'"
                            )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_documentation_snippets(
        repo_root=Path(args.repo_root).resolve(),
        documentation_map_path=Path(args.documentation_map).resolve(),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation snippet validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
