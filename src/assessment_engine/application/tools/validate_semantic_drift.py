# golden-path: ignore
from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from assessment_engine.application.tools import (
    validate_documentation_governance as governance,
)


def get_modified_py_files(repo_root: Path) -> list[str]:
    modified = set()

    # 1. Try diffing against origin/main (typical PR workflow)
    try:
        res = subprocess.run(
            ["git", "diff", "origin/main...HEAD", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        modified.update(res.stdout.splitlines())
    except Exception:
        pass

    # 2. Try diffing against HEAD~1 (commits on local branches)
    if not modified:
        try:
            res = subprocess.run(
                ["git", "diff", "HEAD~1", "--name-only"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            modified.update(res.stdout.splitlines())
        except Exception:
            pass

    # 3. Fallback to uncommitted changes
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        modified.update(res.stdout.splitlines())
    except Exception:
        pass

    return [f.strip() for f in modified if f.strip().endswith(".py")]


def get_git_diff(repo_root: Path, file_path: str) -> str:
    try:
        # First try diffing committed changes
        res = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--", file_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        diff = res.stdout.strip()
        if diff:
            return diff
    except Exception:
        pass

    # Fallback to current workspace modifications
    try:
        res = subprocess.run(
            ["git", "diff", "--", file_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return ""


def query_gemini_api(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "ERROR: Empty response from model"
    except urllib.error.HTTPError as e:
        return f"ERROR: HTTPError {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"ERROR: {e}"


def check_semantic_drift(
    repo_root: Path,
    documentation_map_path: Path,
    api_key: str,
) -> tuple[list[str], str]:
    documentation_map = governance.load_yaml(documentation_map_path)
    modified_py = get_modified_py_files(repo_root)

    if not modified_py:
        return [], "No modified Python files detected in this changeset."

    warnings: list[str] = []
    report_lines: list[str] = ["# AI Semantic Drift Audit Report\n"]

    for py_file in modified_py:
        abs_py_path = repo_root / py_file
        if not abs_py_path.exists():
            continue

        # Find dependent documents in the map
        for entry in documentation_map.get("entries", []):
            if not isinstance(entry, dict) or entry.get("kind") != "document":
                continue
            path = entry.get("path")
            if not isinstance(path, str):
                continue
            abs_md_path = repo_root / path
            if not abs_md_path.exists():
                continue

            sources = entry.get("source_of_truth", [])
            is_dependent = False
            for src in sources:
                resolved_src = (abs_md_path.parent / src).resolve()
                if resolved_src == abs_py_path:
                    is_dependent = True
                    break

            if not is_dependent:
                continue

            # We found a match! Retrieve diff and compare
            diff_text = get_git_diff(repo_root, py_file)
            if not diff_text:
                continue

            md_content = abs_md_path.read_text(encoding="utf-8")

            prompt = f"""You are a principal software architect and staff technical writer.
Compare the following git diff showing recent changes to a Python code file with the corresponding high-level Markdown documentation file that lists this script as its source of truth.

Determine if the code changes introduce any "semantic drift" (outdated descriptions, removed layers, or conceptual inconsistencies) in the documentation.
If the modifications are purely stylistic, refactoring, or type stubs that do not change the core architecture, respond STRICTLY with 'NO_DRIFT'.

Otherwise, provide a clear, professional architectural review listing:
1. The drifted concepts or sections in the Markdown file.
2. The exact correction or diff suggestions in Markdown.

--- PYTHON CODE DIFF ({py_file}) ---
{diff_text}

--- MARKDOWN DOCUMENTATION ({path}) ---
{md_content}
"""

            print(f"Auditing semantic drift for: {path} against {py_file}...")
            ai_response = query_gemini_api(api_key, prompt).strip()

            if "NO_DRIFT" not in ai_response:
                warn_msg = f"Detected semantic drift in documentation file '{path}' caused by changes in '{py_file}'"
                warnings.append(warn_msg)

                report_lines.append(f"## ⚠️ Drift Detected in `{path}`")
                report_lines.append(f"- **Trigger File:** `{py_file}`")
                report_lines.append("\n### Audit Findings:")
                report_lines.append(ai_response)
                report_lines.append("\n---\n")

    if not warnings:
        report_lines.append("## ✅ Audit passed cleanly. No semantic drift detected.")

    return warnings, "\n".join(report_lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    parser.add_argument("--output-report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print(
            "WARNING: GEMINI_API_KEY is not defined. Skipping semantic drift validation."
        )
        return 0

    repo_root = Path(args.repo_root).resolve()
    documentation_map = Path(args.documentation_map).resolve()

    warnings, report = check_semantic_drift(repo_root, documentation_map, api_key)

    if args.output_report:
        out_path = Path(args.output_report).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Semantic drift report written to: {out_path}")

    if warnings:
        print("\n=== SEMANTIC DRIFT WARNINGS ===")
        for warn in warnings:
            print(f"WARN: {warn}")
        # Return 0 (non-blocking) or 1 (blocking). In SOTA workflows, we can treat this as non-blocking warnings
        # but output report is uploaded to review. Let's print warnings and pass.
        return 0

    print("AI Semantic drift validation passed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
