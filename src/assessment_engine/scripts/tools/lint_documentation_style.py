# golden-path: ignore
from __future__ import annotations

import argparse
import re
from pathlib import Path

from assessment_engine.scripts.tools import (
    validate_documentation_governance as governance,
)


BANNED_HYPE_PATTERNS = [
    re.compile(r"\bSOTA\b", re.IGNORECASE),
    re.compile(r"Top Mundial", re.IGNORECASE),
    re.compile(r"\b100%\s+perfect", re.IGNORECASE),
    re.compile(r"\bc[oó]digo perfecto\b", re.IGNORECASE),
    re.compile(r"\bInterfaz Gr[aá]fica Definitiva\b", re.IGNORECASE),
]


def lint_documentation_style(repo_root: Path, documentation_map_path: Path) -> list[str]:
    documentation_map = governance.load_yaml(documentation_map_path)
    errors: list[str] = []

    for entry in documentation_map.get("entries", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") != "document":
            continue
        if entry.get("status") != "Verified":
            continue

        path = entry.get("path")
        if not isinstance(path, str) or not path.endswith(".md"):
            continue
        absolute_path = repo_root / path
        if not absolute_path.exists():
            continue

        text = absolute_path.read_text(encoding="utf-8")
        for pattern in BANNED_HYPE_PATTERNS:
            if pattern.search(text):
                errors.append(
                    f"{path}: Verified documentation contains hype or future-marketing language matching /{pattern.pattern}/"
                )
        if "roadmap" in path.lower() and entry.get("status") == "Verified":
            errors.append(f"{path}: roadmap documents cannot remain Verified")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = lint_documentation_style(
        repo_root=Path(args.repo_root).resolve(),
        documentation_map_path=Path(args.documentation_map).resolve(),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation style lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
