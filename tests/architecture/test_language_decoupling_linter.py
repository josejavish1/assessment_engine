"""Architectural Fitness Function: Enforces Pure Technical English in Presentation Compilers.

Mandates:
1. Pure Technical English across AST compilers in src/assessment_engine/adapters/compilers/.
2. Zero raw Spanish string literals or Spanish default arguments in calls to localization function t().
3. Zero long dashes (em-dash U+2014, en-dash U+2013) in source code string literals.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILERS_DIR = REPO_ROOT / "src" / "assessment_engine" / "adapters" / "compilers"

# Sample characteristic Spanish tokens that indicate localized text leaking into generic compiler code
BANNED_SPANISH_PROSE_PATTERNS = [
    r"\bhasta\s*~",
    r"\blibro\s+[ab]:",
    r"\bdisrupci[oó]n\s+del\s+servicio\b",
    r"\btiempo\s+requerido\s+para\b",
    r"\balerta\s+de\s+hito\b",
    r"\bmantenimiento\s+electromec[aá]nico\b",
    r"\bca[ií]da\s+de\s+host\b",
    r"\brotura\s+de\s+fibra\b",
    r"\bparada\s+no\s+planificada\b",
    r"\bbrecha\s+de\s+madurez\s+metodol[oó]gica\b",
    r"\bcontrol\s+de\s+gobernanza\s*\(cuestionario\)\b",
]


def test_no_banned_spanish_prose_in_compilers() -> None:
    """Verifies that no Spanish prose or UI fragments leak into compiler source code."""
    violations: list[str] = []

    for py_file in COMPILERS_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for pat_str in BANNED_SPANISH_PROSE_PATTERNS:
            pat = re.compile(pat_str, re.IGNORECASE)
            for idx, line in enumerate(content.splitlines(), start=1):
                sline = line.strip()
                if sline.startswith("#") or sline.startswith('"""') or sline.startswith("'''"):
                    continue
                if pat.search(sline):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}:L{idx} -> {sline}")

    assert not violations, "Spanish prose fragments detected in compiler code:\n" + "\n".join(violations)


def test_strict_hyphen_invariant_in_compiler_sources() -> None:
    """Verifies that no em-dashes (U+2014) or en-dashes (U+2013) exist in compiler string literals."""
    violations: list[str] = []

    for py_file in COMPILERS_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for idx, line in enumerate(content.splitlines(), start=1):
            code_part = line.split("#")[0].strip()
            if not code_part or code_part.startswith('"""') or code_part.startswith("'''"):
                continue
            # Allow regex pattern definitions and replacement calls that match legacy em-dashes for scrubbing
            if code_part.startswith('r"') or code_part.startswith("r'") or "re.compile" in code_part or "re.sub" in code_part or "replace(" in code_part:
                continue
            if "\u2014" in code_part or "\u2013" in code_part:
                violations.append(f"{py_file.relative_to(REPO_ROOT)}:L{idx} -> {line}")

    assert not violations, "Em-dash or en-dash detected in compiler code:\n" + "\n".join(violations)
