"""Comprehensive AST Mutation Testing Probe per ISO/IEC/IEEE 29119 & GEMA 54.

Empirically evaluates test assertion resilience by injecting first-order syntactic mutants
into critical domain, actuarial, and security modules and asserting that the test suite detects
and neutralizes the corruptions.
"""

from __future__ import annotations

import ast
import ast
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult
from assessment_engine.infrastructure.auditor.mutation_probe import (
    MutationTestingProbe,
)

PYTEST_CMD = [sys.executable, "-m", "pytest"]

CORE_MUTATION_TARGETS: list[tuple[str, str]] = [
    ("src/assessment_engine/mcp_server.py", "tests/unit/test_mcp_server.py"),
    ("src/assessment_engine/domain/cfo_actuarial_gate.py", "tests/unit/test_cfo_actuarial_gate.py"),
    ("src/assessment_engine/domain/framework_urn.py", "tests/unit/test_framework_urn.py"),
    ("src/assessment_engine/domain/actuarial_scale_calibrator.py", "tests/unit/test_actuarial_scale_calibrator.py"),
    ("src/assessment_engine/domain/actuarial_reconciler.py", "tests/unit/test_actuarial_reconciler.py"),
    ("src/assessment_engine/domain/services/score_reconciler.py", "tests/unit/test_score_reconciler.py"),
    ("src/assessment_engine/domain/bayesian_fair_copula_engine.py", "tests/unit/test_bayesian_fair_copula_engine.py"),
    ("src/assessment_engine/infrastructure/rosi_calculator.py", "tests/unit/test_rosi_actuarial_engine.py"),
]


class DiscreteMutantCollector(ast.NodeVisitor):
    """Locate all potential mutation points in executable statements."""

    def __init__(self) -> None:
        self.mutation_points: list[dict[str, Any]] = []
        self._counter = 0
        self._in_func = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._in_func += 1
        self.generic_visit(node)
        self._in_func -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._in_func += 1
        self.generic_visit(node)
        self._in_func -= 1

    def visit_Compare(self, node: ast.Compare) -> None:
        """Visit comparison nodes to register potential comparison inversion mutants."""
        if self._in_func > 0 and len(node.ops) == 1:
            op = node.ops[0]
            mutated_op = None
            desc = ""
            if isinstance(op, ast.Gt):
                mutated_op = ast.LtE()
                desc = f"Invert '>' to '<=' at line {node.lineno}"
            elif isinstance(op, ast.Lt):
                mutated_op = ast.GtE()
                desc = f"Invert '<' to '>=' at line {node.lineno}"
            elif isinstance(op, ast.Eq):
                mutated_op = ast.NotEq()
                desc = f"Invert '==' to '!=' at line {node.lineno}"
            elif isinstance(op, ast.NotEq):
                mutated_op = ast.Eq()
                desc = f"Invert '!=' to '==' at line {node.lineno}"
            elif isinstance(op, ast.In):
                mutated_op = ast.NotIn()
                desc = f"Invert 'in' to 'not in' at line {node.lineno}"
            elif isinstance(op, ast.NotIn):
                mutated_op = ast.In()
                desc = f"Invert 'not in' to 'in' at line {node.lineno}"

            if mutated_op:
                self.mutation_points.append(
                    {
                        "id": self._counter,
                        "lineno": node.lineno,
                        "type": "Compare",
                        "replacement": mutated_op,
                        "desc": desc,
                    }
                )
                self._counter += 1

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant nodes to register potential boolean inversion mutants."""
        if self._in_func > 0 and isinstance(node.value, bool):
            self.mutation_points.append(
                {
                    "id": self._counter,
                    "lineno": node.lineno,
                    "type": "Boolean",
                    "replacement": not node.value,
                    "desc": f"Invert boolean '{node.value}' to '{not node.value}' at line {node.lineno}",
                }
            )
            self._counter += 1
        self.generic_visit(node)


class SingleMutantInjector(ast.NodeTransformer):
    """Inject exactly one mutation into the AST for the specified ID."""

    def __init__(self, target_id: int, replacement: Any) -> None:
        self.target_id = target_id
        self.replacement = replacement
        self._current_id = 0
        self._in_func = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self._in_func += 1
        res = self.generic_visit(node)
        self._in_func -= 1
        return res

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self._in_func += 1
        res = self.generic_visit(node)
        self._in_func -= 1
        return res

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Transform target comparison node by injecting the mutant operator."""
        if self._in_func > 0 and len(node.ops) == 1 and type(node.ops[0]) in (
            ast.Gt,
            ast.Lt,
            ast.Eq,
            ast.NotEq,
            ast.In,
            ast.NotIn,
        ):
            if self._current_id == self.target_id:
                node.ops = [self.replacement]
            self._current_id += 1
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Transform target boolean constant node by injecting the inverted boolean."""
        if self._in_func > 0 and isinstance(node.value, bool):
            if self._current_id == self.target_id:
                node.value = self.replacement
            self._current_id += 1
        return self.generic_visit(node)


def generate_first_order_mutants(
    source_code: str, max_mutants: int = 4
) -> list[tuple[str, str, int]]:
    """Generate independent syntactic variants from the source code."""
    try:
        base_tree = ast.parse(source_code)
    except SyntaxError:
        return []

    collector = DiscreteMutantCollector()
    collector.visit(base_tree)

    selected = collector.mutation_points[:max_mutants]
    mutants: list[tuple[str, str, int]] = []

    for point in selected:
        tree_copy = ast.parse(source_code)
        injector = SingleMutantInjector(point["id"], point["replacement"])
        mutated_tree = injector.visit(tree_copy)
        ast.fix_missing_locations(mutated_tree)

        try:
            mutated_code = ast.unparse(mutated_tree)
            mutants.append((mutated_code, point["desc"], point["lineno"]))
        except (ValueError, SyntaxError) as err:
            logger.debug("Failed to unparse mutant %s: %s", point["desc"], err)

    return mutants


def _discover_mutation_targets(target_dir: Path) -> list[tuple[Path, Path]]:
    """Dynamically discover all Python files in the domain layer and map to their tests."""
    targets = []
    domain_dir = target_dir / "src/assessment_engine/domain"
    tests_dir = target_dir / "tests/unit"
    
    if not domain_dir.exists() or not tests_dir.exists():
        return targets

    for src_file in domain_dir.rglob("*.py"):
        if src_file.name == "__init__.py":
            continue
        test_filename = f"test_{src_file.name}"
        # Search for corresponding test file in tests/unit recursively
        test_files = list(tests_dir.rglob(test_filename))
        if test_files:
            targets.append((src_file, test_files[0]))
    return targets


def run_mutation_gate_probe(target_dir: Path, mutants_per_module: int = 4) -> ProbeResult:
    """Execute comprehensive AST mutation testing across core business targets."""
    findings: list[AuditFinding] = []
    total_mutants = 0
    killed_mutants = 0
    timeout_killed_mutants = 0

    dynamic_targets = _discover_mutation_targets(target_dir)

    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as temp_workspace_str:
        temp_workspace = Path(temp_workspace_str) / "repo"
        # Clone repo state to a disposable temp directory, excluding heavy unneeded dirs
        shutil.copytree(
            target_dir,
            temp_workspace,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", "__pycache__", "workspaces", "node_modules",
                ".pytest_cache", ".mypy_cache", ".ruff_cache", "business_command_center"
            )
        )

        for target_path_orig, test_path_orig in dynamic_targets:
            if not target_path_orig.exists() or not test_path_orig.exists():
                continue

            try:
                target_rel = str(target_path_orig.relative_to(target_dir))
            except ValueError:
                target_rel = str(target_path_orig)

            try:
                original_code = target_path_orig.read_text(encoding="utf-8")
            except OSError:
                continue

            mutants = generate_first_order_mutants(original_code, max_mutants=mutants_per_module)
            if not mutants:
                continue

            target_path_isolated = temp_workspace / target_rel
            try:
                test_path_isolated = temp_workspace / str(test_path_orig.relative_to(target_dir))
            except ValueError:
                test_path_isolated = test_path_orig

            for mutated_code, desc, lineno in mutants:
                target_path_isolated.write_text(mutated_code, encoding="utf-8")
                total_mutants += 1

                cmd = [*PYTEST_CMD, str(test_path_isolated), "-q", "--tb=no"]
                env = os.environ.copy()
                env["PYTHONPATH"] = str(temp_workspace / "src")

                try:
                    res = subprocess.run(
                        cmd,
                        cwd=str(temp_workspace),
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=15,
                    )

                    if res.returncode != 0:
                        killed_mutants += 1
                    else:
                        findings.append(
                            AuditFinding(
                                category="Testing & Verification",
                                severity="HIGH",
                                file_path=target_rel,
                                line_number=lineno,
                                rule_id="MUT-SURVIVED",
                                message=f"Mutant in '{target_path_orig.name}' survived ({desc}): test suite failed to catch corruption.",
                                recommendation="Strengthen unit test assertions over boundary conditions and state transitions.",
                            )
                        )
                except subprocess.TimeoutExpired:
                    # Mutants causing infinite loops or execution hangs are killed by timeout per ISO/IEC/IEEE 29119
                    timeout_killed_mutants += 1
                    killed_mutants += 1

    if total_mutants == 0:
        score = 100.0
        passed = True
    else:
        score = round((killed_mutants / total_mutants) * 100.0, 1)
        passed = score >= 85.0

    return ProbeResult(
        probe_name="Mutation Testing Score (ISO/IEC/IEEE 29119 & GEMA 54)",
        score_pct=score,
        passed=passed,
        metrics={
            "mutants_tested": total_mutants,
            "mutants_killed_by_test_failure": killed_mutants - timeout_killed_mutants,
            "mutants_killed_by_timeout": timeout_killed_mutants,
            "mutants_survived": total_mutants - killed_mutants,
            "mutation_score_pct": score,
            "target_modules_count": len(dynamic_targets),
        },
        findings=findings,
    )
