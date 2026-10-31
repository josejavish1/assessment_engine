# golden-path: ignore
"""Architectural Fitness Function: Enforces Clean Architecture dependency rules via AST inspection.

Guarantees zero infrastructure, adapter, or application imports inside the Domain layer.
"""
from __future__ import annotations

import ast
from pathlib import Path
import pytest

DOMAIN_DIR = Path("src/assessment_engine/domain")
FORBIDDEN_PACKAGES = {
    "assessment_engine.infrastructure",
    "assessment_engine.adapters",
    "assessment_engine.application",
    "requests",
    "httpx",
}


def get_domain_python_files() -> list[Path]:
    if not DOMAIN_DIR.exists():
        return []
    return [p for p in DOMAIN_DIR.rglob("*.py") if "__pycache__" not in str(p)]


@pytest.mark.parametrize("file_path", get_domain_python_files())
def test_domain_layer_has_zero_forbidden_dependencies(file_path: Path) -> None:
    source_code = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source_code, filename=str(file_path))

    rel_parts = file_path.relative_to(DOMAIN_DIR).parts
    max_safe_relative_level = len(rel_parts)  # Depth inside domain directory

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in FORBIDDEN_PACKAGES:
                    if alias.name == forbidden or alias.name.startswith(f"{forbidden}."):
                        violations.append(f"Line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            # Check absolute imports
            if node.module:
                for forbidden in FORBIDDEN_PACKAGES:
                    if node.module == forbidden or node.module.startswith(f"{forbidden}."):
                        violations.append(f"Line {node.lineno}: from {node.module} import ...")
            # Check relative imports escaping domain
            if node.level and node.level > max_safe_relative_level:
                violations.append(
                    f"Line {node.lineno}: relative import level {node.level} escapes domain directory"
                )

    assert not violations, (
        f"Clean Architecture Violation in {file_path}:\n" + "\n".join(violations)
    )
