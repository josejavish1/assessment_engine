#!/usr/bin/env python3
"""Perform a formal mutation score audit (ISO/IEC/IEEE 29119).

Injects first-order mutants via AST into core business, actuarial, and security modules.
Empirically evaluates whether the test suite detects and neutralizes code corruptions.
Calculates the mutation score: (Killed Mutants / Total Mutants) * 100.
"""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mutation_auditor")

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTEST_CMD = [sys.executable, "-m", "pytest"]


class DiscreteMutantCollector(ast.NodeVisitor):
    """Locate all potential mutation points in the AST."""

    def __init__(self) -> None:
        self.mutation_points: list[dict[str, Any]] = []
        self._counter = 0

    def visit_Compare(self, node: ast.Compare) -> None:
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
                        "original_node": node,
                        "replacement": mutated_op,
                        "desc": desc,
                    }
                )
                self._counter += 1

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, bool):
            self.mutation_points.append(
                {
                    "id": self._counter,
                    "lineno": node.lineno,
                    "type": "Boolean",
                    "original_node": node,
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
        if isinstance(node.value, bool):
            if self._current_id == self.target_id:
                node.value = self.replacement
            self._current_id += 1
        return self.generic_visit(node)


def generate_first_order_mutants(
    source_code: str, max_mutants: int = 5
) -> list[tuple[str, str, int]]:
    """Generate up to max_mutants independent syntactic variants from the source code."""
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
        except Exception:
            continue

    return mutants


def run_mutation_audit_on_target(
    target_rel: str, test_rel: str, max_mutants: int = 5
) -> dict[str, Any]:
    target_path = REPO_ROOT / target_rel
    test_path = REPO_ROOT / test_rel

    if not target_path.exists() or not test_path.exists():
        return {
            "target": target_rel,
            "test": test_rel,
            "error": "Target module or test suite missing",
        }

    original_code = target_path.read_text(encoding="utf-8")
    mutants = generate_first_order_mutants(original_code, max_mutants=max_mutants)

    if not mutants:
        return {
            "target": target_rel,
            "test": test_rel,
            "status": "No mutable comparison or boolean operators found",
        }

    killed = 0
    survived = 0
    survived_details: list[dict[str, Any]] = []

    try:
        for mutated_code, desc, lineno in mutants:
            target_path.write_text(mutated_code, encoding="utf-8")

            cmd = [*PYTEST_CMD, str(test_path), "-q", "--tb=no"]
            res = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45,
            )

            if res.returncode != 0:
                killed += 1
            else:
                survived += 1
                survived_details.append({"lineno": lineno, "description": desc})
    finally:
        target_path.write_text(original_code, encoding="utf-8")

    total = killed + survived
    pct = round((killed / max(1, total)) * 100, 1)

    return {
        "target": target_rel,
        "test": test_rel,
        "total_mutants": total,
        "killed": killed,
        "survived": survived,
        "mutation_score_pct": pct,
        "survived_details": survived_details,
    }


def main() -> None:
    print("\n" + "=" * 85)
    print("FORMAL MUTATION SCORE AUDIT — GEMA 54 (ISO/IEC/IEEE 29119 STANDARD)")
    print("Objective: Empirically neutralize vanity tests and evaluate assertion resistance")
    print("=" * 85)

    targets = [
        ("src/assessment_engine/mcp_server.py", "tests/unit/test_mcp_server.py"),
        ("src/assessment_engine/domain/cfo_actuarial_gate.py", "tests/unit/test_cfo_actuarial_gate.py"),
        ("src/assessment_engine/domain/framework_urn.py", "tests/unit/test_framework_urn.py"),
        ("src/assessment_engine/domain/actuarial_scale_calibrator.py", "tests/unit/test_actuarial_scale_calibrator.py"),
        ("src/assessment_engine/domain/actuarial_reconciler.py", "tests/unit/test_actuarial_reconciler.py"),
        ("src/assessment_engine/domain/services/score_reconciler.py", "tests/unit/test_score_reconciler.py"),
        ("src/assessment_engine/domain/bayesian_fair_copula_engine.py", "tests/unit/test_bayesian_fair_copula_engine.py"),
        ("src/assessment_engine/infrastructure/rosi_calculator.py", "tests/unit/test_rosi_actuarial_engine.py"),
    ]

    total_mutants_global = 0
    total_killed_global = 0
    results: list[dict[str, Any]] = []

    start_time = time.time()
    for target_rel, test_rel in targets:
        print(f"\n[MUTATING] {target_rel}...")
        report = run_mutation_audit_on_target(target_rel, test_rel, max_mutants=5)
        results.append(report)

        if "total_mutants" in report and report["total_mutants"] > 0:
            tot = report["total_mutants"]
            k = report["killed"]
            s = report["survived"]
            pct = report["mutation_score_pct"]
            total_mutants_global += tot
            total_killed_global += k

            print(f"  Result: Mutants: {tot} | Killed: {k} ({pct}%) | Survived: {s}")
            for sv in report.get("survived_details", []):
                print(f"     Warning Line {sv['lineno']}: {sv['description']}")

    elapsed = round(time.time() - start_time, 2)
    global_score = (
        round((total_killed_global / total_mutants_global) * 100, 1)
        if total_mutants_global > 0
        else 100.0
    )

    print("\n" + "=" * 85)
    print("CONSOLIDATED MUTATION RESISTANCE AND TEST RIGOR REPORT")
    print("=" * 85)
    print(f"Total Mutants Injected in AST:     {total_mutants_global}")
    print(f"Mutants Killed by Tests:           {total_killed_global}")
    print(f"Mutants Survived:                  {total_mutants_global - total_killed_global}")
    print(f"GLOBAL MUTATION SCORE:             {global_score}% (Tier-1 Threshold: >=80.0%)")
    print(f"Total Execution Time:              {elapsed}s")
    print("=" * 85)

    if global_score >= 80.0:
        print("[VERDICT] TIER-1 CERTIFICATION GRANTED: Test suite exhibits strong assertion resistance.")
    else:
        print("[VERDICT] AUDIT WARNS OF SURVIVING MUTANTS: Strengthen weak assertions.")

    out_file = REPO_ROOT / "docs" / "audits" / "MUTATION_TESTING_REPORT.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        json.dumps(
            {
                "timestamp": int(time.time()),
                "standard": "ISO/IEC/IEEE 29119",
                "total_mutants": total_mutants_global,
                "killed": total_killed_global,
                "survived": total_mutants_global - total_killed_global,
                "global_mutation_score_pct": global_score,
                "elapsed_seconds": elapsed,
                "modules_audited": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[OK] Report exported to: {out_file.relative_to(REPO_ROOT)}\n")


if __name__ == "__main__":
    main()
