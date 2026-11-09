"""Comprehensive AST Mutation Testing Probe per ISO/IEC/IEEE 29119 & GEMA 54.

Empirically evaluates test assertion resilience by injecting first-order syntactic mutants
into critical domain, actuarial, and security modules and asserting that the test suite detects
and neutralizes the corruptions.
"""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys
from typing import Any

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
    """Locate all potential mutation points in the AST."""

    def __init__(self) -> None:
        self.mutation_points: list[dict[str, Any]] = []
        self._counter = 0

    def visit_Compare(self, node: ast.Compare) -> None:
        """Visit comparison nodes to register potential comparison inversion mutants."""
        if len(node.ops) == 1:
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
        if isinstance(node.value, bool):
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

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Transform target comparison node by injecting the mutant operator."""
        if len(node.ops) == 1 and type(node.ops[0]) in (
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
        if isinstance(node.value, bool):
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


def run_mutation_gate_probe(target_dir: Path, mutants_per_module: int = 4) -> ProbeResult:
    """Execute comprehensive AST mutation testing across core business targets."""
    findings: list[AuditFinding] = []
    total_mutants = 0
    killed_mutants = 0

    for target_rel, test_rel in CORE_MUTATION_TARGETS:
        target_path = target_dir / target_rel
        test_path = target_dir / test_rel

        if not target_path.exists() or not test_path.exists():
            continue

        try:
            original_code = target_path.read_text(encoding="utf-8")
        except OSError:
            continue

        mutants = generate_first_order_mutants(original_code, max_mutants=mutants_per_module)
        if not mutants:
            continue

        try:
            for mutated_code, desc, lineno in mutants:
                target_path.write_text(mutated_code, encoding="utf-8")
                total_mutants += 1

                cmd = [*PYTEST_CMD, str(test_path), "-q", "--tb=no"]
                res = subprocess.run(
                    cmd,
                    cwd=str(target_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )

                if res.returncode != 0:
                    killed_mutants += 1
                else:
                    findings.append(
                        AuditFinding(
                            category="MUTATION",
                            severity="HIGH",
                            file_path=target_rel,
                            line_number=lineno,
                            rule_id="MUT-SURVIVED",
                            message=f"Mutant in '{target_path.name}' survived ({desc}): test suite failed to catch corruption.",
                            recommendation="Strengthen unit test assertions over boundary conditions and state transitions.",
                        )
                    )
        finally:
            target_path.write_text(original_code, encoding="utf-8")

    if total_mutants == 0:
        score = 100.0
        passed = True
    else:
        score = round((killed_mutants / total_mutants) * 100.0, 1)
        passed = score >= 80.0

    return ProbeResult(
        probe_name="Mutation Testing Score (ISO/IEC/IEEE 29119 & GEMA 54)",
        score_pct=score,
        passed=passed,
        metrics={
            "mutants_tested": total_mutants,
            "mutants_killed": killed_mutants,
            "mutants_survived": total_mutants - killed_mutants,
            "mutation_score_pct": score,
            "target_modules_count": len(CORE_MUTATION_TARGETS),
        },
        findings=findings,
    )
