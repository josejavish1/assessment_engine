"""Architectural Fitness Gate: Prohibits binary docx template manipulation and Split-Brain #1.

RFC-026 Invariant I:
- All deliverable document generation must pass through DocumentAST and DocxCompiler.
- Binary placeholder replacement engines are deprecated and forbidden.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src" / "assessment_engine"


def _collect_production_python_files() -> List[Path]:
    return [
        p for p in SRC_DIR.rglob("*.py")
        if "adapters/render_tower_annex_from_template.py" not in str(p)
    ]


def test_no_forbidden_binary_template_mutators_in_core() -> None:
    """Verify that domain and application layers never import or invoke legacy binary template mutators."""
    forbidden_terms = {
        "replace_simple_placeholder",
        "replace_cell_placeholder",
    }

    violations = []
    # Test application and domain layers strictly
    target_dirs = [SRC_DIR / "domain", SRC_DIR / "application"]
    for d in target_dirs:
        for py_file in d.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id in forbidden_terms:
                        violations.append(f"{py_file.relative_to(REPO_ROOT)}:{node.lineno} - Forbidden call to legacy template mutator '{node.id}'")
            except SyntaxError:
                pass

    assert not violations, "Split-Brain #1 Violation Detected:\n" + "\n".join(violations)
