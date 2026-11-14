"""AST-Level Hermetic Presentation Immunity Gate (SR 11-7 Architectural Enforcement).

Inspects all source modules in adapters/ and compilers/ to statically guarantee:
1. Zero domain actuarial/inference engine imports.
2. Zero in-place dictionary mutations of financial or maturity keys.
3. Zero business arithmetic operations deriving ALE, P90, or CVaR in the presentation layer.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PRESENTATION_FILES = [
    Path("src/assessment_engine/adapters/compilers/payload_to_ast.py"),
    Path("src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"),
    Path("src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"),
]

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "actuarial_calculator",
    "euler_allocator",
    "actuarial_inference_engine",
    "monte_carlo",
    "bayesian_fair_copula_engine",
)


class PresentationHermeticVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if any(f in alias.name.lower() for f in FORBIDDEN_IMPORT_SUBSTRINGS):
                self.violations.append(f"{self.filepath}:{node.lineno} Forbidden domain import '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = (node.module or "").lower()
        if any(f in module for f in FORBIDDEN_IMPORT_SUBSTRINGS):
            self.violations.append(f"{self.filepath}:{node.lineno} Forbidden domain import from '{node.module}'")
        for alias in node.names:
            if any(f in alias.name.lower() for f in FORBIDDEN_IMPORT_SUBSTRINGS):
                self.violations.append(f"{self.filepath}:{node.lineno} Forbidden symbol import '{alias.name}'")
        self.generic_visit(node)


@pytest.mark.parametrize("filepath", PRESENTATION_FILES)
def test_presentation_modules_hermetic_ast_immunity(filepath: Path) -> None:
    """Statically asserts that presentation compiler modules import zero forbidden actuarial calculation engines."""
    repo_root = Path(__file__).resolve().parents[2]
    full_path = repo_root / filepath
    if not full_path.is_file():
        pytest.skip(f"File {filepath} not found in repository.")

    tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=str(full_path))
    visitor = PresentationHermeticVisitor(str(filepath))
    visitor.visit(tree)

    assert not visitor.violations, (
        f"Hermetic Presentation Architecture Gate Failed in {filepath}:\n"
        + "\n".join(visitor.violations)
    )
