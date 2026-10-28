"""
Audit and enforce cyclomatic and bimodal complexity constraints.
Calculates McCabe Cyclomatic Complexity V(G) per IEEE 29119 and SonarSource
Cognitive Complexity (CoC) per S3776 to prevent both spaghetti code and
artificial fragmentation (Goodhart's Law).
"""
from __future__ import annotations

import ast
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.probes.ast_complexity import calc_cognitive_complexity

logger = logging.getLogger("assessment_engine.infrastructure.evolution.complexity_guard")

DEFAULT_MAX_CYCLOMATIC_COMPLEXITY = 10


@dataclass(frozen=True)
class ComplexityViolation:
    """Raise when cyclomatic or cognitive complexity exceeds the maximum allowed threshold."""
    function_name: str
    lineno: int
    complexity: int
    max_allowed: int
    details: str
    rule_id: str = "CYCLOMATIC_COMPLEXITY_EXCEEDED"

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance into a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class ComplexityReport:
    """Represent a cyclomatic and cognitive complexity audit report."""
    passed: bool
    max_complexity: int
    functions_audited: int
    violations: list[ComplexityViolation]
    function_complexities: dict[str, int]
    max_cognitive_complexity: int = 0
    max_nesting_depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance into a dictionary."""
        return {
            "passed": self.passed,
            "max_complexity": self.max_complexity,
            "functions_audited": self.functions_audited,
            "violations": [v.to_dict() for v in self.violations],
            "function_complexities": self.function_complexities,
            "max_cognitive_complexity": self.max_cognitive_complexity,
            "max_nesting_depth": self.max_nesting_depth,
        }


def _traverse_node_complexity(node: ast.AST) -> int:
    """Count decision points without descending into nested functions or classes."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return 0

    count = 0
    if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.IfExp)):
        count += 1
    elif isinstance(node, ast.BoolOp):
        count += max(0, len(node.values) - 1)
    elif hasattr(ast, "Match") and isinstance(node, ast.Match):
        count += 1
    elif isinstance(node, ast.comprehension):
        count += len(node.ifs)

    for child in ast.iter_child_nodes(node):
        count += _traverse_node_complexity(child)

    return count


def compute_mccabe_complexity(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Calculate McCabe Cyclomatic Complexity: V(G) = 1 + decision points. Isolated to the given function level (excluding nested functions)."""
    complexity = 1
    for child in ast.iter_child_nodes(fn_node):
        complexity += _traverse_node_complexity(child)
    return complexity


def _evaluate_function_complexity(
    fn_name: str,
    stmt: ast.FunctionDef | ast.AsyncFunctionDef,
    max_allowed: int,
    bimodal: bool,
) -> tuple[int, int, int, list[ComplexityViolation]]:
    """Evaluate V(G), CoC, and nesting depth for a single function."""
    comp = compute_mccabe_complexity(stmt)
    violations: list[ComplexityViolation] = []
    coc = 0
    max_nesting = 0

    if not bimodal:
        if comp > max_allowed:
            violations.append(
                ComplexityViolation(
                    function_name=fn_name,
                    lineno=stmt.lineno,
                    complexity=comp,
                    max_allowed=max_allowed,
                    details=f"La función '{fn_name}' tiene V(G)={comp}, superando el límite de {max_allowed}",
                    rule_id="CYCLOMATIC_COMPLEXITY_EXCEEDED",
                )
            )
        return comp, coc, max_nesting, violations

    coc, max_nesting = calc_cognitive_complexity(stmt)

    if max_nesting > 3:
        violations.append(
            ComplexityViolation(
                function_name=fn_name,
                lineno=stmt.lineno,
                complexity=comp,
                max_allowed=max_allowed,
                details=f"Anidamiento excesivo en '{fn_name}': {max_nesting} niveles de profundidad (límite <= 3)",
                rule_id="DEEP_NESTING_EXCEEDED",
            )
        )

    if coc > 15:
        violations.append(
            ComplexityViolation(
                function_name=fn_name,
                lineno=stmt.lineno,
                complexity=comp,
                max_allowed=max_allowed,
                details=f"Sobrecarga cognitiva en '{fn_name}': CoC={coc} (límite <= 15)",
                rule_id="COGNITIVE_OVERLOAD_EXCEEDED",
            )
        )

    if comp > 14:
        violations.append(
            ComplexityViolation(
                function_name=fn_name,
                lineno=stmt.lineno,
                complexity=comp,
                max_allowed=14,
                details=f"La función '{fn_name}' tiene V(G)={comp}, superando el límite de 14",
                rule_id="CYCLOMATIC_COMPLEXITY_EXCEEDED",
            )
        )
    elif comp > 10 and not (max_nesting <= 2 and coc <= 15):
        violations.append(
            ComplexityViolation(
                function_name=fn_name,
                lineno=stmt.lineno,
                complexity=comp,
                max_allowed=10,
                details=f"La función '{fn_name}' tiene V(G)={comp}, superando el límite de 10",
                rule_id="CYCLOMATIC_COMPLEXITY_EXCEEDED",
            )
        )

    return comp, coc, max_nesting, violations


def audit_code_complexity(
    code: str,
    max_allowed: int = DEFAULT_MAX_CYCLOMATIC_COMPLEXITY,
    bimodal: bool = False,
) -> ComplexityReport:
    """Audit a Python code string and evaluate V(G) and CoC for each function and method."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"[ComplexityGuard] Error sintáctico al auditar complejidad: {e}")
        return ComplexityReport(
            passed=False,
            max_complexity=999,
            functions_audited=0,
            violations=[
                ComplexityViolation(
                    function_name="<module>",
                    lineno=e.lineno or 1,
                    complexity=999,
                    max_allowed=max_allowed,
                    details=f"Error sintáctico: {e.msg}",
                    rule_id="PYTHON_SYNTAX_ERROR",
                )
            ],
            function_complexities={},
        )

    complexities: dict[str, int] = {}
    violations: list[ComplexityViolation] = []
    global_max_coc = 0
    global_max_nesting = 0

    def _inspect_body(body: list[ast.stmt], prefix: str = "") -> None:
        nonlocal global_max_coc, global_max_nesting
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_name = f"{prefix}{stmt.name}"
                comp, coc, max_nest, fn_viols = _evaluate_function_complexity(
                    fn_name, stmt, max_allowed, bimodal
                )
                complexities[fn_name] = comp
                if coc > global_max_coc:
                    global_max_coc = coc
                if max_nest > global_max_nesting:
                    global_max_nesting = max_nest
                violations.extend(fn_viols)
                # Auditar funciones internas anidadas
                _inspect_body(stmt.body, prefix=f"{fn_name}.")
            elif isinstance(stmt, ast.ClassDef):
                cls_name = f"{prefix}{stmt.name}."
                _inspect_body(stmt.body, prefix=cls_name)

    _inspect_body(tree.body)

    max_c = max(complexities.values()) if complexities else 1
    passed = len(violations) == 0

    return ComplexityReport(
        passed=passed,
        max_complexity=max_c,
        functions_audited=len(complexities),
        violations=violations,
        function_complexities=complexities,
        max_cognitive_complexity=global_max_coc,
        max_nesting_depth=global_max_nesting,
    )


def audit_file_complexity(
    file_path: Path | str,
    max_allowed: int = DEFAULT_MAX_CYCLOMATIC_COMPLEXITY,
    bimodal: bool = False,
) -> ComplexityReport:
    """Audit the cyclomatic complexity of a Python file on disk."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    code = p.read_text(encoding="utf-8")
    return audit_code_complexity(code, max_allowed=max_allowed, bimodal=bimodal)


class ComplexityGuard:
    """Provide an interface for cyclomatic and bimodal complexity auditing."""

    @staticmethod
    def compute_complexity(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """Compute the cyclomatic complexity of a function node."""
        return compute_mccabe_complexity(fn_node)

    @staticmethod
    def audit_code(
        code: str,
        max_allowed: int = DEFAULT_MAX_CYCLOMATIC_COMPLEXITY,
        bimodal: bool = False,
    ) -> ComplexityReport:
        """Audit Python source code for cyclomatic and cognitive complexity."""
        return audit_code_complexity(code, max_allowed=max_allowed, bimodal=bimodal)

    @staticmethod
    def audit_code_bimodal(code: str) -> ComplexityReport:
        """Audit Python source code with bimodal tolerance (V(G) <= 14 when flat, CoC <= 15, nesting <= 3)."""
        return audit_code_complexity(code, bimodal=True)

    @staticmethod
    def audit_file(
        file_path: Path | str,
        max_allowed: int = DEFAULT_MAX_CYCLOMATIC_COMPLEXITY,
        bimodal: bool = False,
    ) -> ComplexityReport:
        """Audit a Python file for cyclomatic and cognitive complexity."""
        return audit_file_complexity(file_path, max_allowed=max_allowed, bimodal=bimodal)


complexity_guard = ComplexityGuard()

__all__ = [
    "DEFAULT_MAX_CYCLOMATIC_COMPLEXITY",
    "ComplexityGuard",
    "ComplexityReport",
    "ComplexityViolation",
    "audit_code_complexity",
    "audit_file_complexity",
    "complexity_guard",
    "compute_mccabe_complexity",
]
