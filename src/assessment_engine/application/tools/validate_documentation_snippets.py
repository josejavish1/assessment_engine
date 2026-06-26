# golden-path: ignore
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

from assessment_engine.application.tools import (
    validate_documentation_governance as governance,
)

FENCED_BLOCK_RE = re.compile(r"```(?:bash|sh|shell|console)?\n(.*?)```", re.DOTALL)
PYTHON_MODULE_RE = re.compile(r"(?:^|\s)-m\s+([a-zA-Z0-9_\.]+)")
REPO_RELATIVE_HINTS = {".venv", ".github", "bin", "docs", "src", "templates", "tests"}


def should_validate_repo_relative_path(token: str) -> bool:
    normalized = token
    if normalized.startswith("./"):
        normalized = normalized[2:]
    elif normalized.startswith("../"):
        normalized = normalized[3:]
    first_segment = normalized.split("/", 1)[0]
    return first_segment in REPO_RELATIVE_HINTS


def validate_command_flags(repo_root: Path, line: str) -> list[str]:
    errors: list[str] = []

    # Match direct script path, e.g. python src/tools/script.py ...
    script_match = re.search(r"\bpython3?\s+([a-zA-Z0-9_\-/]+\.py)\b", line)
    script_path: Path | None = None
    args_str = ""

    if script_match:
        script_rel = script_match.group(1)
        script_path = repo_root / script_rel
        args_str = line[script_match.end() :]
    else:
        # Match python -m module
        module_match = re.search(r"\bpython3?\s+-m\s+([a-zA-Z0-9_\.]+)\b", line)
        if module_match:
            module_name = module_match.group(1)
            args_str = line[module_match.end() :]
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    script_path = Path(spec.origin)
            except Exception:
                pass

    if script_path and script_path.exists():
        # Only validate local scripts inside repo_root and NOT in .venv
        is_local = False
        try:
            rel_path = script_path.relative_to(repo_root)
            if ".venv" not in rel_path.parts:
                is_local = True
        except ValueError:
            pass

        if is_local:
            # Find all flags used (words starting with - or --)
            flags_used = re.findall(r"\s(-[a-zA-Z0-9_\-]+)", args_str)
            if flags_used:
                try:
                    # Use sys.executable to ensure we run with the active virtual env interpreter
                    res = subprocess.run(
                        [sys.executable, str(script_path), "--help"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=5,
                    )
                    help_text = res.stdout + res.stderr
                    for flag in flags_used:
                        if flag in {"-h", "--help"}:
                            continue
                        if flag not in help_text:
                            errors.append(
                                f"references invalid or non-existent flag '{flag}' for script '{script_path.name}'"
                            )
                except Exception:
                    # Silently skip if script execution fails due to environment requirements
                    pass

    return errors


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

                # Validate command flags on lines running python
                if "python" in stripped:
                    flag_errors = validate_command_flags(repo_root, stripped)
                    for flag_err in flag_errors:
                        errors.append(f"{path}: code block {flag_err}")

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
                        if cleaned.startswith(
                            "./"
                        ) and should_validate_repo_relative_path(cleaned):
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
