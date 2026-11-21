"""Architectural Fitness Function: Enforces Tier-1 Documentation Invariants.

This test suite guarantees that documentation in docs/ maintains world-class Tier-1
software engineering standards by construction:
1. 100% Pure Technical English across all Markdown files in docs/ (zero Spanish stopwords or phrases).
2. Strict kebab-case filename convention across all docs/ subdirectories.
3. Deterministic index navigation: every subdirectory in docs/ must contain a local README.md.
4. Agentic optimization and high Shannon information density (tables, models, or code blocks in every document).
5. 100% Technical English metadata in docs/documentation-map.yaml.
6. Zero broken internal relative Markdown links across docs/.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
DOC_MAP_PATH = DOCS_DIR / "documentation-map.yaml"

STRICT_SPANISH_REGEX = re.compile(
    r"\b(el|la|los|las|del|para|como|una|este|esta|estos|estas|"
    r"sus|pero|sobre|entre|cuando|donde|quien|también|además|"
    r"según|diseño|arquitectura|guía|código|verificación)\b",
    re.IGNORECASE,
)

BANNED_CONVERSATIONAL_FLUFF = [
    re.compile(r"\ben\s+este\s+documento\b", re.IGNORECASE),
    re.compile(r"\bcomo\s+se\s+mencion[oó]\b", re.IGNORECASE),
    re.compile(r"\ba\s+continuaci[oó]n\b", re.IGNORECASE),
    re.compile(r"\bpor\s+lo\s+tanto\b", re.IGNORECASE),
]


def test_docs_all_markdown_in_pure_technical_english() -> None:
    """Asserts that all Markdown documentation files contain zero Spanish prose or stopwords."""
    violations = {}

    for doc in sorted(DOCS_DIR.rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        spanish_matches = STRICT_SPANISH_REGEX.findall(text)
        fluff_matches = [
            pat.pattern for pat in BANNED_CONVERSATIONAL_FLUFF if pat.search(text)
        ]

        if spanish_matches or fluff_matches:
            rel_path = str(doc.relative_to(REPO_ROOT))
            violations[rel_path] = {
                "words": list(set(spanish_matches)),
                "fluff": fluff_matches,
            }

    assert not violations, (
        f"Detected non-English tokens or Spanish prose in documentation:\n{violations}"
    )


def test_docs_strict_kebab_case_naming() -> None:
    """Asserts that all documentation files adhere strictly to kebab-case naming."""
    allowed_uppercase_stems = {"README", "SYSTEM_ARCHITECTURE"}
    violations = []

    for doc in sorted(DOCS_DIR.rglob("*.md")):
        stem = doc.stem
        if stem in allowed_uppercase_stems:
            continue

        # Valid kebab-case: lowercase letters, numbers, hyphens only
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", stem):
            rel_path = str(doc.relative_to(REPO_ROOT))
            violations.append(rel_path)

    assert not violations, (
        f"Non-standard file names detected in docs/ (must use strict kebab-case.md):\n{violations}"
    )


def test_docs_subdirectories_have_local_readme_index() -> None:
    """Asserts that every direct subdirectory under docs/ contains a local README.md index."""
    missing_indices = []

    for subdir in sorted(DOCS_DIR.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith((".", "_")):
            readme_path = subdir / "README.md"
            if not readme_path.exists():
                missing_indices.append(str(subdir.relative_to(REPO_ROOT)))

    assert not missing_indices, (
        f"Missing local README.md index in subdirectories:\n{missing_indices}"
    )


def test_docs_documentation_map_pure_technical_english() -> None:
    """Asserts that documentation-map.yaml contains zero Spanish text in notes or titles."""
    assert DOC_MAP_PATH.exists(), f"Missing documentation map: {DOC_MAP_PATH}"
    data = yaml.safe_load(DOC_MAP_PATH.read_text(encoding="utf-8"))

    violations = []
    for entry in data.get("entries", []):
        note = entry.get("notes", "")
        title = entry.get("title", "")
        for text, field in [(note, "notes"), (title, "title")]:
            matches = STRICT_SPANISH_REGEX.findall(text)
            if matches:
                violations.append((entry.get("path"), field, matches))

    assert not violations, (
        f"Detected Spanish prose in documentation-map.yaml metadata:\n{violations}"
    )


def test_docs_agent_optimization_structural_density() -> None:
    """Asserts that every canonical document contains structured tables, schemas, or code blocks."""
    unstructured_docs = []

    for doc in sorted(DOCS_DIR.rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        # Check for structural markers: Markdown table row, fenced code block, or LaTeX math block
        has_table = "\n|" in text or "\r\n|" in text
        has_code = "```" in text
        has_math = "$$" in text

        if not (has_table or has_code or has_math):
            rel_path = str(doc.relative_to(REPO_ROOT))
            unstructured_docs.append(rel_path)

    assert not unstructured_docs, (
        f"Documentation lacking structured tables/schemas (insufficient Shannon density for AI agents):\n{unstructured_docs}"
    )


def test_docs_zero_broken_internal_markdown_links() -> None:
    """Asserts that all relative Markdown links in docs/ point to physically existing files."""
    link_regex = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken_links = []

    for doc in sorted(DOCS_DIR.rglob("*.md")):
        content = doc.read_text(encoding="utf-8")
        links = link_regex.findall(content)

        for text, target in links:
            # Skip external URLs, local anchors, mailto
            if (
                target.startswith(("http://", "https://", "mailto:", "#"))
                or not target.strip()
            ):
                continue

            target_file = target.split("#")[0]
            if not target_file:
                continue

            resolved = (doc.parent / target_file).resolve()
            if not resolved.exists():
                rel_path = str(doc.relative_to(REPO_ROOT))
                broken_links.append((rel_path, target))

    assert not broken_links, (
        f"Broken internal relative links detected in docs/:\n{broken_links}"
    )
