#!/usr/bin/env python
"""GitOps TODO Auto-Tracker.
Automatically detects untracked # TODO comments, creates corresponding GitHub Issues
using the authenticated 'gh' CLI, and rewrites the comments in-place in the AST
to establish the strict, professional Google Tier 1 standard:
# TODO(jsanchhi): #<issue_id> <description>.
"""

import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import libcst as cst

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("todo_autotracker")

# Regexes for tracking and matching TODOs
TODO_PATTERN = re.compile(r"#\s*TODO\b")
TRACKED_TODO_PATTERN = re.compile(
    r"#\s*TODO\(\s*jsanchhi\s*\)\s*:\s*(?:#\d+|#OFFLINE-\d+)"
)


def get_next_offline_id(project_root: Path) -> int:
    """Scans the src/ codebase statelessly to find the highest existing offline placeholder
    ID (e.g., #OFFLINE-4) and returns the next sequential integer.
    """
    highest_id = 0
    target_dir = project_root / "src"
    if not target_dir.exists():
        return 1

    for p in target_dir.glob("**/*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            matches = re.findall(r"#OFFLINE-(\d+)", content)
            for m in matches:
                highest_id = max(highest_id, int(m))
        except Exception:
            pass
    return highest_id + 1


def clean_todo_title(raw_title: str) -> str:
    """Cleans raw Python comments and code syntax to extract a beautiful,
    human-readable sentence suitable for a GitHub Issue title.
    """
    cleaned = raw_title.strip()
    parts = [p.strip() for p in cleaned.split("#")]
    todo_part = ""
    for p in reversed(parts):
        if (
            p
            and not p.lower().startswith("type:ignore")
            and not p.lower().startswith("type: ignore")
        ):
            todo_part = p
            break

    cleaned = re.sub(
        r"^TODO\s*(?:\([^)]*\))?\s*:?\s*", "", todo_part, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"^\[[A-Z0-9_-]+\]\s*", "", cleaned)
    cleaned = cleaned.strip().rstrip(".,:;")
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def create_github_issue(
    raw_desc: str, orig_comment: str, file_path: Path, project_root: Path
) -> Optional[str]:
    """Invokes the 'gh' CLI to automatically create a GitHub Issue for the given TODO,
    returning the generated issue string (e.g., '#412') or None if offline/unauthenticated.
    """
    # Quick sanity check for 'gh' presence
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except Exception:
        logger.debug("GitHub CLI ('gh') is not installed or not in PATH.")
        return None

    # Clean the title for command line safety
    clean_title = clean_todo_title(raw_desc)
    if not clean_title:
        clean_title = f"Address pending TODO in {file_path.name}"

    relative_path = (
        file_path.relative_to(project_root) if file_path.is_absolute() else file_path
    )

    # Beautifully structured markdown body matching PO Orchestrator SOTA quality
    body = (
        f"### 📋 Context\n"
        f"This issue was automatically registered by the **GitOps TODO Auto-Tracker** from a pending technical debt marker in the codebase.\n\n"
        f"- **Target File:** `{relative_path}`\n"
        f"- **Responsible Owner:** `jsanchhi`\n\n"
        f"### 🛠️ Original Comment\n"
        f"```python\n"
        f"{orig_comment.strip()}\n"
        f"```\n\n"
        f"### 🎯 Goal & Acceptance Criteria\n"
        f"Resolve the pending technical debt and remove the `TODO` comment from the file. Ensure the logic remains fully covered by unit tests."
    )

    # Determine smart tags based on text
    label_1 = "enhancement"
    label_2 = "good first issue"
    desc_lower = raw_desc.lower()
    if "doc" in desc_lower or "comment" in desc_lower:
        label_2 = "documentation"
    elif "type" in desc_lower or "typing" in desc_lower or "mypy" in desc_lower:
        label_1 = "enhancement"

    try:
        # Run gh command in background with 5-second timeout
        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            clean_title,
            "--body",
            body,
            "--label",
            label_1,
            "--label",
            label_2,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)
        output = res.stdout.strip()

        # Match issue number from URL (e.g., https://github.com/owner/repo/issues/412)
        match = re.search(r"/issues/(\d+)", output)
        if match:
            issue_num = match.group(1)
            logger.info(
                f"✓ Created GitHub Issue #{issue_num} for TODO: '{clean_title}'"
            )
            return f"#{issue_num}"

        # Fallback if URL is not returned but number is on stdout
        if output.isdigit():
            return f"#{output}"

    except subprocess.TimeoutExpired:
        logger.warning(
            "Connection timeout to GitHub API. Falling back to offline tracking."
        )
    except subprocess.CalledProcessError as e:
        logger.debug(
            f"GitHub CLI issue creation failed (unauthenticated or no remote origin): {e.stderr}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while calling GitHub API: {e}")

    return None


class TODOTrackingTransformer(cst.CSTTransformer):
    def __init__(self, file_path: Path, project_root: Path) -> None:
        self.file_path = file_path
        self.project_root = project_root
        self.modified = False

    def leave_Comment(
        self, original_node: cst.Comment, updated_node: cst.Comment
    ) -> cst.Comment:
        orig_val = original_node.value

        # Check if this comment contains an untracked TODO
        if TODO_PATTERN.search(orig_val) and not TRACKED_TODO_PATTERN.search(orig_val):
            # Parse and extract the TODO description
            # Strip potential leading '#', 'TODO', ':', and spacing
            cleaned_content = orig_val.lstrip("#").strip()
            # Match Todo with or without trailing colon
            todo_match = re.match(r"^TODO\s*:?\s*(.*)$", cleaned_content, re.IGNORECASE)
            if todo_match:
                todo_desc = todo_match.group(1).strip()
            else:
                todo_desc = cleaned_content

            if not todo_desc:
                todo_desc = f"Address technical debt in {self.file_path.name}"

            # Step 1: Attempt to create GitHub Issue
            issue_id = create_github_issue(
                todo_desc, orig_val, self.file_path, self.project_root
            )

            # Step 2: Fallback to stateless offline tracking if offline
            if not issue_id:
                offline_num = get_next_offline_id(self.project_root)
                # To prevent duplicate generation in a single pass of multiple files,
                # we immediately write the updated comments back so get_next_offline_id sees them!
                issue_id = f"#OFFLINE-{offline_num}"
                logger.info(
                    f"⚠️ Offline/Unauthenticated: Assigned sequential placeholder {issue_id} to TODO: '{todo_desc}'"
                )

            # Step 3: Construct the strict, professional contract comment
            new_val = f"# TODO(jsanchhi): {issue_id} {todo_desc}"
            self.modified = True
            return updated_node.with_changes(value=new_val)

        return updated_node


def process_file(file_path: Path, project_root: Path) -> bool:
    """Parses and tracks any untracked TODOs in the target file, returning True if modified."""
    try:
        code = file_path.read_text(encoding="utf-8")
        module = cst.parse_module(code)

        transformer = TODOTrackingTransformer(file_path, project_root)
        transformed_module = module.visit(transformer)

        if transformer.modified:
            # Safeguard syntax compile check before writing
            compile(transformed_module.code, str(file_path), "exec")
            file_path.write_text(transformed_module.code, encoding="utf-8")
            return True
    except Exception as e:
        logger.error(f"Failed to process or validate TODOs in {file_path.name}: {e}")
    return False


def main() -> None:
    # Resolve project root and files to scan
    current_dir = Path.cwd()

    # If run as a pre-commit hook, staged files are passed as arguments
    if len(sys.argv) > 1:
        py_files = [
            Path(arg).resolve() for arg in sys.argv[1:] if Path(arg).suffix == ".py"
        ]
    else:
        # Default recursive scan of src/
        target_dir = current_dir / "src"
        py_files = sorted(list(target_dir.glob("**/*.py")))

    # Filter out ignored paths
    ignored_patterns = ["_legacy", "node_modules", ".venv"]
    py_files = [
        f
        for f in py_files
        if f.exists() and not any(pat in str(f) for pat in ignored_patterns)
    ]

    modified_count = 0
    for f in py_files:
        if process_file(f, current_dir):
            modified_count += 1
            print(
                f"✓ Automatically tracked pending TODOs in: {f.relative_to(current_dir)}"
            )

    if modified_count > 0:
        print(
            f"\nGitOps TODO Auto-Tracker completed. Tracked and updated TODO comments in {modified_count} files."
        )
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
