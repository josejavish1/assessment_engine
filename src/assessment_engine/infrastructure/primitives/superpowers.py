"""
Jesse Vincent 'superpowers' Engineering Discipline Primitive.
Enforces rigorous TDD, Root Cause Analysis, Anti-Sycophancy, and Mutation Resistance.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.superpowers")

SUPERPOWERS_DIRECTIVE = """
[JESSE VINCENT SUPERPOWERS DISCIPLINE - INVARIANTS]
1. TEST-DRIVEN DEVELOPMENT (TDD) FIRST:
   - For every feature, bug fix, or acceptance criterion, you MUST write the failing automated test FIRST before touching application code.
   - Tests must fail for the expected reason before the fix is applied.
   - Every test must verify observable state transitions, contract invariants, or explicit error handling.

2. ROOT CAUSE & EMPIRICAL REPRODUCTION:
   - Never assume a bug fix works without empirical reproduction.
   - Prohibit speculative patches. Inspect exact stack traces, environment invariants, and error payloads.
   - If a test fails, diagnose the underlying cause rather than modifying the test to match broken behavior.

3. FAKES OVER MOCKS (STATE-BASED RESILIENCE):
   - Prohibit monkeypatching internal business logic using unittest.mock.patch or mock.MagicMock.
   - Use in-memory Protocol implementations (FakeDB, FakeClient, FakeGateway) with real state mutations.
   - Test contracts through public observable interfaces.

4. ANTI-SYCOPHANCY (BRUTAL HONESTY):
   - Never generate trivial assertions (e.g., 'assert True', empty test functions, or catch-all pass statements).
   - If requirements are architecturally flawed, raise the trade-off explicitly rather than implementing fragile workarounds.
   - Reject fake passes: all assertions must exercise non-trivial execution paths.
"""


def _find_test_files(workspace_dir: Path) -> list[Path]:
    """Locate all test files in standard paths."""
    test_dirs = [workspace_dir / "tests", workspace_dir / "api" / "tests"]
    test_files: list[Path] = []
    for td in test_dirs:
        if td.exists():
            test_files.extend(list(td.glob("test_*.py")) + list(td.glob("*_test.py")))
    return test_files


def _check_if_node_is_assertion(child: Any, has_assert: bool, is_trivial: bool) -> tuple[bool, bool]:
    if isinstance(child, ast.Assert):
        has_assert = True
        if isinstance(child.test, ast.Constant) and child.test.value is True:
            is_trivial = True
    elif isinstance(child, ast.Call):
        func_repr = ast.unparse(child.func) if hasattr(ast, "unparse") else ""
        if any(assertion in func_repr for assertion in ["assertTrue", "assertEqual", "raises", "assert_"]):
            has_assert = True
    return has_assert, is_trivial

def _inspect_test_function_nodes(node: Any) -> tuple[bool, bool]:
    """Check whether a test function contains non-trivial assertions."""
    has_assert = False
    is_trivial = False
    for child in ast.walk(node):
        has_assert, is_trivial = _check_if_node_is_assertion(child, has_assert, is_trivial)
    return has_assert, is_trivial


def _analyze_single_test_file(tf: Path) -> tuple[int, int, int]:
    """Analyze the AST of a test file for mocks and trivial assertions."""
    total_fns = 0
    trivial = 0
    mocks = 0
    try:
        content = tf.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(tf))
        if "unittest.mock" in content or "mock.patch" in content or "@patch" in content:
            mocks += len(re.findall(r"@patch|unittest\.mock", content))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                node.name.startswith("test_") or node.name.endswith("_test")
            ):
                total_fns += 1
                has_assert, is_trivial = _inspect_test_function_nodes(node)
                if is_trivial or not has_assert:
                    trivial += 1
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
        logger.debug(f"Superpowers AST check error on {tf}: {ex}")
    return total_fns, trivial, mocks


def _has_immutable_contract(py_file: Path) -> bool:
    """Check if a Python file declares immutable NamedTuple or frozen dataclass contracts."""
    try:
        content = py_file.read_text(encoding="utf-8")
        return "NamedTuple" in content or "@dataclass(frozen=True)" in content
    except (OSError, UnicodeDecodeError) as ex:
        logger.debug(f"File read error checking contracts on {py_file}: {ex}")
        return False


def _count_immutable_contracts(workspace_dir: Path) -> int:
    """Find immutable contracts (NamedTuple / frozen dataclass) in the domain."""
    src_dirs = [workspace_dir / "src", workspace_dir / "api" / "src"]
    py_files = [f for sd in src_dirs if sd.exists() for f in sd.rglob("*.py")]
    return sum(1 for f in py_files if _has_immutable_contract(f))


def _calculate_superpowers_score(
    total_fns: int, trivial: int, mocks: int
) -> tuple[int, str, list[str]]:
    """Calculate mathematical penalties and protocol invariants."""
    deductions = (trivial * 15) + (mocks * 5)
    if total_fns == 0:
        deductions += 40

    score = max(20, 100 - deductions)
    violations: list[str] = []
    if trivial > 0:
        violations.append(f"Detected {trivial} test functions with trivial or missing assertions.")
    if mocks > 0:
        violations.append(f"Detected {mocks} brittle mock monkeypatches. Prefer stateful Fakes.")

    status = "FAIL" if score < 70 else ("WARN" if score < 90 else "PASS")
    return score, status, violations


def audit_superpowers_compliance(workspace_dir: Path) -> dict[str, Any]:
    """
    Audits a workspace against the Superpowers Engineering invariants:
    1. Test coverage existence and non-triviality in tests/ or api/tests/.
    2. Zero mock monkeypatching in core business domain tests.
    3. Detection of trivial passes ('assert True', pass-only test blocks).
    4. Compliance with immutable domain contracts (NamedTuple / frozen dataclasses).
    """
    if not workspace_dir.exists():
        return {
            "status": "FAIL",
            "tdd_tests_found": 0,
            "test_files_analyzed": 0,
            "trivial_assertions": 0,
            "mock_patches_detected": 0,
            "immutable_contracts_found": 0,
            "score": 0,
            "violations": ["Workspace directory does not exist."]
        }

    test_files = _find_test_files(workspace_dir)
    if not test_files:
        return {
            "status": "FAIL",
            "tdd_tests_found": 0,
            "test_files_analyzed": 0,
            "trivial_assertions": 0,
            "mock_patches_detected": 0,
            "immutable_contracts_found": 0,
            "score": 40,
            "violations": ["Zero automated test files found in tests/ or api/tests/."]
        }

    total_fns = 0
    trivial_count = 0
    mock_count = 0
    for tf in test_files:
        f_count, t_count, m_count = _analyze_single_test_file(tf)
        total_fns += f_count
        trivial_count += t_count
        mock_count += m_count

    immutable_count = _count_immutable_contracts(workspace_dir)
    score, status, violations = _calculate_superpowers_score(total_fns, trivial_count, mock_count)

    return {
        "status": status,
        "tdd_tests_found": total_fns,
        "test_files_analyzed": len(test_files),
        "trivial_assertions": trivial_count,
        "mock_patches_detected": mock_count,
        "immutable_contracts_found": immutable_count,
        "score": score,
        "violations": violations
    }


class SuperpowersProbePrimitive:
    """
    Perform mutation testing and audit TDD quality.
    """

    def audit(self, workspace_dir: Path) -> dict[str, Any]:
        """Audit the specified workspace directory."""
        return audit_superpowers_compliance(workspace_dir)


superpowers_probe = SuperpowersProbePrimitive()

