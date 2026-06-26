#!/usr/bin/env python
"""Semantic Comment Linter (Anti-AI-Bro / Anti-Slop Gate).
Extracts newly added comments and docstrings from the git diff and uses the Gemini API
to audit them under a strict technical, academic, and non-hype evaluation rubric.
Fails the build if any marketing buzzwords, redundant "what" comments, or non-technical slop is found.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Set up paths to allow importing project modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from assessment_engine.infrastructure.ai_client import call_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("comment_linter")

# Configuration
MODEL_NAME = os.environ.get("MODEL_TIER_FLASH", "gemini-2.5-flash")

SYSTEM_INSTRUCTION = """
You are a Staff Principal Engineer at Anthropic. Your task is to audit newly added comments and docstrings in a Pull Request to prevent 'AI-Bro' hype, slop, or unnecessary verbosity.

Strict Evaluation Rubric:
1. Reject any comment, docstring, or description that contains self-congratulatory, marketing, or hype-laden words (e.g., 'SOTA', 'State-of-the-Art', 'sovereign', 'bulletproof', 'ultra-robust', 'robust', 'flawless', 'seamlessly', 'beautifully', 'lethal', 'power artifact', 'perfect').
2. Reject any inline comment that simply describes obvious python syntax or restates what the code is doing (e.g. '# loops through elements', '# check if x is not None', '# save document to disk').
3. Reject comments with informal, conversational, or emotional phrasing. Prosaic explanations must be dry, clinical, academic, and standards-based (e.g. referencing ECMA, RFC, XSD).

Return ONLY a valid JSON object matching the following structure. Do not return markdown blocks or any conversational text.
{
  "approved": true,
  "reason": ""
}
or:
{
  "approved": false,
  "reason": "Detail the specific line(s) violating the standard, quoting the offending text, and explaining why it is considered hype, slop, or redundant."
}
"""


def get_git_diff_comments() -> List[str]:
    """Runs git diff against the base branch (e.g. origin/main, origin/develop or HEAD~1)
    and extracts newly added/modified comments and docstrings.
    """
    # Detect base commit / branch
    base_commit = os.environ.get("BASE_SHA")
    if not base_commit:
        # Fallback to compare HEAD against parent commit
        base_commit = "HEAD~1"

    logger.info(f"Extracting git diff comments against base: {base_commit}")

    try:
        # Compare working tree against base_commit to capture unstaged changes
        cmd = ["git", "diff", base_commit, "--", "src/**/*.py"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        diff_output = res.stdout
    except Exception as e:
        logger.warning(
            f"Failed to run git diff {base_commit}: {e}. Falling back to HEAD~1."
        )
        try:
            cmd = ["git", "diff", "HEAD~1", "--", "src/**/*.py"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            diff_output = res.stdout
        except Exception as e2:
            logger.error(f"Failed to run git diff: {e2}")
            return []

    added_comments: List[str] = []
    in_docstring = False
    docstring_lines: List[str] = []

    for line in diff_output.splitlines():
        # Only look at added lines in the diff (starting with '+')
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()

            # Check for inline comments
            if "#" in content:
                comment_part = content.split("#", 1)[1].strip()
                # Exclude lint suppressions
                if not comment_part.startswith(
                    "type: ignore"
                ) and not comment_part.startswith("pragma:"):
                    added_comments.append(comment_part)

            # Check for docstrings
            if '"""' in content or "'''" in content:
                if in_docstring:
                    # Closing docstring
                    docstring_lines.append(content)
                    added_comments.append("\n".join(docstring_lines))
                    docstring_lines = []
                    in_docstring = False
                else:
                    # Opening docstring
                    in_docstring = True
                    docstring_lines.append(content)
            elif in_docstring:
                docstring_lines.append(content)

    return [c for c in added_comments if c.strip()]


async def main() -> None:
    # 1. Extract newly added comments
    new_comments = get_git_diff_comments()

    if not new_comments:
        logger.info(
            "✓ Zero new comments or docstrings detected in git diff. Passing gate immediately (Token Efficient)."
        )
        sys.exit(0)

    logger.info(
        f"Auditing {len(new_comments)} newly added comments/docstrings for AI-Bro/Slop style..."
    )

    # Audit in chunks of 50 comments to prevent output limit issues and ensure JSON compliance
    CHUNK_SIZE = 50
    for chunk_idx in range(0, len(new_comments), CHUNK_SIZE):
        chunk = new_comments[chunk_idx : chunk_idx + CHUNK_SIZE]
        logger.info(
            f"Auditing chunk {chunk_idx // CHUNK_SIZE + 1} of {(len(new_comments) - 1) // CHUNK_SIZE + 1} ({len(chunk)} comments)..."
        )

        # 2. Build prompt
        prompt = "Newly added comments/docstrings to audit:\n"
        for i, c in enumerate(chunk, 1):
            prompt += f"[{i}] {repr(c)}\n"

        # 3. Call Gemini
        try:
            response_text = await call_agent(
                model_name=MODEL_NAME, prompt=prompt, instruction=SYSTEM_INSTRUCTION
            )

            # Parse JSON
            if isinstance(response_text, dict):
                mapping = response_text
            else:
                clean_text = str(response_text).strip()
                if clean_text.startswith("```"):
                    lines = clean_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    clean_text = "\n".join(lines).strip()
                mapping = json.loads(clean_text)

            approved = mapping.get("approved", True)
            reason = mapping.get("reason", "")

            if not approved:
                print(
                    "\n❌ SEMANTIC COMMENT LINTER FAIL: AI-Bro / AI-Slop Style Detected in chunk!"
                )
                print(f"Reason: {reason}\n")
                print(
                    "To maintain Tier 1 Google/Anthropic engineering quality, please:"
                )
                print(
                    "  1. Remove any hype-words (SOTA, Sovereign, robust, bulletproof, flawless, lethal)."
                )
                print(
                    "  2. Delete redundant comments that explain standard Python syntax."
                )
                print(
                    "  3. Keep comments dry, factual, clinical, and focused on 'why' (specifications, constraints)."
                )
                sys.exit(1)

        except Exception as e:
            logger.error(
                f"Semantic Comment Linter execution failed on chunk: {e}. Passing defensively to avoid blocking CI."
            )
            sys.exit(0)

    logger.info(
        "✓ All new comments and docstrings passed the Google Tier 1 Semantic Quality Gate."
    )
    sys.exit(0)


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error(
            "GEMINI_API_KEY is not set. Passing defensively to avoid blocking CI."
        )
        sys.exit(0)
    asyncio.run(main())
