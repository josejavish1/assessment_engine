#!/usr/bin/env python3
"""Static audit script to inventory internationalization (i18n) leaks

and inline linguistic branching anti-patterns in assessment engine.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src" / "assessment_engine"

# Internal file exclusions that do not generate customer-facing documents
EXCLUDED_FILES = {
    "__init__.py",
    "i18n.py",
}

# Inline language branching patterns
INLINE_LANG_PATTERNS = [
    re.compile(r"\b(doc_lang|lang|meta_lang|target_lang|locale|base_loc)\s*==\s*[\"'][a-zA-Z_\-]+[\"']"),
    re.compile(r"\b(doc_lang|lang|meta_lang|target_lang|locale|base_loc)\s*!=\s*[\"'][a-zA-Z_\-]+[\"']"),
    re.compile(r"\b(doc_lang|lang|meta_lang|target_lang|locale|base_loc)\s+in\s+\[.*?\]"),
    re.compile(r"\b(doc_lang|lang|meta_lang|target_lang|locale|base_loc)\s+not\s+in\s+\[.*?\]"),
    re.compile(r"if\s+.*?(doc_lang|lang|meta_lang)\b.*?else"),
]

# DOCX call patterns with direct string literals
LITERAL_CALL_PATTERNS = [
    re.compile(r"add_heading_paragraph\s*\(\s*doc\s*,\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"add_heading\s*\(\s*doc\s*,\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"add_body_paragraph\s*\(\s*doc\s*,\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"add_run\s*\(\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"set_cell_text\s*\([^,]+,\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"HeadingNode\s*\(\s*text\s*=\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"ParagraphNode\s*\(\s*text\s*=\s*[\"']([^\"']{4,})[\"']"),
    re.compile(r"CellNode\s*\(\s*text\s*=\s*[\"']([^\"']{4,})[\"']"),
]


def audit_file(file_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Analyzes a file for language anti-patterns and hardcoded literals."""
    inline_conditionals: list[dict[str, Any]] = []
    hardcoded_literals: list[dict[str, Any]] = []

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        print(f"Error reading {file_path}: {exc}")
        return {"inline_conditionals": [], "hardcoded_literals": []}

    for lineno, line in enumerate(lines, start=1):
        s_line = line.strip()
        if not s_line or s_line.startswith("#"):
            continue

        # Check inline language branching
        for pattern in INLINE_LANG_PATTERNS:
            if pattern.search(line):
                inline_conditionals.append({
                    "line": lineno,
                    "snippet": s_line,
                    "pattern": pattern.pattern,
                })
                break

        # Check literal calls
        for pattern in LITERAL_CALL_PATTERNS:
            match = pattern.search(line)
            if match:
                literal_val = match.group(1).strip()
                # Skip technical tokens and punctuation
                if len(literal_val) > 3 and not literal_val.startswith(("{", "%", "[")):
                    hardcoded_literals.append({
                        "line": lineno,
                        "snippet": s_line,
                        "literal": literal_val,
                    })
                    break

    return {
        "inline_conditionals": inline_conditionals,
        "hardcoded_literals": hardcoded_literals,
    }


def run_audit() -> dict[str, Any]:
    results: dict[str, Any] = {
        "total_files_scanned": 0,
        "files_with_inline_conditionals": 0,
        "files_with_hardcoded_literals": 0,
        "total_inline_conditionals": 0,
        "total_hardcoded_literals": 0,
        "details": {},
    }

    for file_path in sorted(SRC_DIR.rglob("*.py")):
        if file_path.name in EXCLUDED_FILES:
            continue
        # Skip tests and test data
        if "tests" in file_path.parts:
            continue

        rel_path = file_path.relative_to(ROOT).as_posix()
        file_res = audit_file(file_path)

        c_len = len(file_res["inline_conditionals"])
        l_len = len(file_res["hardcoded_literals"])

        results["total_files_scanned"] += 1
        if c_len > 0:
            results["files_with_inline_conditionals"] += 1
            results["total_inline_conditionals"] += c_len
        if l_len > 0:
            results["files_with_hardcoded_literals"] += 1
            results["total_hardcoded_literals"] += l_len

        if c_len > 0 or l_len > 0:
            results["details"][rel_path] = file_res

    return results


def main() -> None:
    results = run_audit()
    print("=" * 80)
    print(" INTERNATIONALIZATION (i18n) AUDIT CENSUS: LEAKS AND ANTI-PATTERNS")
    print("=" * 80)
    print(f"Files scanned:                     {results['total_files_scanned']}")
    print(f"Files with inline conditionals:    {results['files_with_inline_conditionals']}")
    print(f"Total inline conditionals:         {results['total_inline_conditionals']}")
    print(f"Files with hardcoded DOCX strings: {results['files_with_hardcoded_literals']}")
    print(f"Total report string literals:      {results['total_hardcoded_literals']}")
    print("-" * 80)

    # Rank by impact
    ranked = sorted(
        results["details"].items(),
        key=lambda x: len(x[1]["inline_conditionals"]) + len(x[1]["hardcoded_literals"]),
        reverse=True,
    )

    print("\n[TOP FILES BY LINGUISTIC DEBT]:")
    for file_path, data in ranked:
        c_count = len(data["inline_conditionals"])
        l_count = len(data["hardcoded_literals"])
        print(f" - {file_path:60} | Ternaries: {c_count:3} | Literals: {l_count:3}")

    # Save JSON report
    out_json = ROOT / "audit_i18n_census.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed report exported to: {out_json}")


if __name__ == "__main__":
    main()
