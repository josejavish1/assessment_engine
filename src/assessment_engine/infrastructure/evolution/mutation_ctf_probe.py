"""
Execute mutation testing via AST manipulation. Inject first-order mutants (FOM) via AST to detect weak or empty assertions. Require generated tests to kill logic corruptions with a mutation score >= 0.80 (80% kill rate) conforming to ISO/IEC/IEEE 29119.
"""
from __future__ import annotations


import ast
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.evolution.mutation_ctf_probe")

DEFAULT_MIN_MUTATION_SCORE = 0.80
DEFAULT_MAX_MUTANTS = 5


@dataclass
class MutationProbeResult:
    """Represent the canonical result of a mutation test run."""
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    mutation_score: float  # killed / total (debe ser >= 0.80)
    survived_details: list[str] = field(default_factory=list)
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance into a dictionary."""
        return asdict(self)


class MutationSiteCollector(ast.NodeVisitor):
    """Collect all potential mutation points from the AST."""

    def __init__(self) -> None:
        self.sites: list[dict[str, Any]] = []
        self._counter = 0

    def visit_Compare(self, node: ast.Compare) -> None:
        """Visit a comparison expression node."""
        if len(node.ops) != 1:
            self.generic_visit(node)
            return

        op = node.ops[0]
        op_map = {
            ast.Gt: (ast.LtE(), "'>' invertido a '<='"),
            ast.Lt: (ast.GtE(), "'<' invertido a '>='"),
            ast.GtE: (ast.Lt(), "'>=' invertido a '<'"),
            ast.LtE: (ast.Gt(), "'<=' invertido a '>'"),
            ast.Eq: (ast.NotEq(), "'==' invertido a '!='"),
            ast.NotEq: (ast.Eq(), "'!=' invertido a '=='"),
            ast.In: (ast.NotIn(), "'in' invertido a 'not in'"),
            ast.NotIn: (ast.In(), "'not in' invertido a 'in'"),
            ast.Is: (ast.IsNot(), "'is' invertido a 'is not'"),
            ast.IsNot: (ast.Is(), "'is not' invertido a 'is'"),
        }

        mutated_info = op_map.get(type(op))
        if mutated_info:
            mutated_op, desc_suffix = mutated_info
            self.sites.append({
                "id": self._counter,
                "lineno": node.lineno,
                "type": "Compare",
                "replacement": mutated_op,
                "desc": f"ROR: {desc_suffix} en línea {node.lineno}",
            })
            self._counter += 1

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Visit a binary operation node."""
        mutated_op = None
        desc = ""
        if isinstance(node.op, ast.Add):
            mutated_op = ast.Sub()
            desc = f"AOR: '+' invertido a '-' en línea {node.lineno}"
        elif isinstance(node.op, ast.Sub):
            mutated_op = ast.Add()
            desc = f"AOR: '-' invertido a '+' en línea {node.lineno}"
        elif isinstance(node.op, ast.Mult):
            mutated_op = ast.FloorDiv()
            desc = f"AOR: '*' invertido a '//' en línea {node.lineno}"

        if mutated_op is not None:
            self.sites.append({
                "id": self._counter,
                "lineno": node.lineno,
                "type": "BinOp",
                "replacement": mutated_op,
                "desc": desc,
            })
            self._counter += 1

        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Visit a boolean operation node."""
        mutated_op = None
        desc = ""
        if isinstance(node.op, ast.And):
            mutated_op = ast.Or()
            desc = f"LCR: 'and' invertido a 'or' en línea {node.lineno}"
        elif isinstance(node.op, ast.Or):
            mutated_op = ast.And()
            desc = f"LCR: 'or' invertido a 'and' en línea {node.lineno}"

        if mutated_op is not None:
            self.sites.append({
                "id": self._counter,
                "lineno": node.lineno,
                "type": "BoolOp",
                "replacement": mutated_op,
                "desc": desc,
            })
            self._counter += 1

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit a constant value node."""
        if isinstance(node.value, bool):
            self.sites.append({
                "id": self._counter,
                "lineno": node.lineno,
                "type": "Constant",
                "replacement": not node.value,
                "desc": f"COR: booleano '{node.value}' invertido a '{not node.value}' en línea {node.lineno}",
            })
            self._counter += 1
        self.generic_visit(node)


class SingleMutantInjector(ast.NodeTransformer):
    """Inject exactly one mutation into the AST by its numeric ID."""

    def __init__(self, target_id: int, replacement: Any) -> None:
        self.target_id = target_id
        self.replacement = replacement
        self._current_id = 0

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Transform a comparison expression node."""
        if len(node.ops) == 1 and type(node.ops[0]) in (
            ast.Gt, ast.Lt, ast.GtE, ast.LtE, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Is, ast.IsNot
        ):
            if self._current_id == self.target_id:
                node.ops = [self.replacement]
            self._current_id += 1
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Transform a binary operation node."""
        if type(node.op) in (ast.Add, ast.Sub, ast.Mult):
            if self._current_id == self.target_id:
                node.op = self.replacement
            self._current_id += 1
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        """Transform a boolean operation node."""
        if type(node.op) in (ast.And, ast.Or):
            if self._current_id == self.target_id:
                node.op = self.replacement
            self._current_id += 1
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Transform a constant value node."""
        if isinstance(node.value, bool):
            if self._current_id == self.target_id:
                node.value = self.replacement
            self._current_id += 1
        return self.generic_visit(node)


def run_mutation_ctf(
    target_file: Path | str,
    test_target: Path | str | list[str],
    max_mutants: int = DEFAULT_MAX_MUTANTS,
    min_score: float = DEFAULT_MIN_MUTATION_SCORE,
    timeout_seconds: int = 15,
    work_dir: Path | str | None = None,
) -> MutationProbeResult:
    """Execute the CTF mutation protocol (RFC-015): 1. Locate comparators and operators in target_file.
2. Inject up to max_mutants mutations one by one on disk.
3. Run pytest against test_target for each mutant in the worktree sandbox.
4. If pytest returns != 0 -> Mutant KILLED (rigorous test).
5. If pytest returns == 0 -> Mutant SURVIVED (weak test).
6. Unconditionally restore the original file."""
    target_p = Path(target_file).resolve()
    if not target_p.exists():
        logger.error(f"[MutationCTF] Archivo objetivo no encontrado: {target_p}")
        return MutationProbeResult(
            total_mutants=0,
            killed_mutants=0,
            survived_mutants=0,
            mutation_score=0.0,
            survived_details=[f"Archivo no encontrado: {target_p}"],
            passed=False,
        )

    # Determine the execution root directory (supports ephemeral Git worktrees).
    if work_dir:
        work_root = Path(work_dir).resolve()
    else:
        work_root = target_p.parent
        for parent in [target_p] + list(target_p.parents):
            if (parent / "core").is_dir() or (parent / "pytest.ini").is_file():
                work_root = parent
                break

    if isinstance(test_target, list):
        test_cmd = test_target
    else:
        test_p = Path(test_target).resolve()
        test_cmd = [sys.executable, "-B", "-m", "pytest", str(test_p), "-q"]

    original_code = target_p.read_text(encoding="utf-8")

    try:
        base_tree = ast.parse(original_code)
    except SyntaxError as e:
        logger.error(f"[MutationCTF] Error sintáctico en {target_p}: {e}")
        return MutationProbeResult(
            total_mutants=0,
            killed_mutants=0,
            survived_mutants=0,
            mutation_score=0.0,
            survived_details=[f"Error sintáctico: {e}"],
            passed=False,
        )

    collector = MutationSiteCollector()
    collector.visit(base_tree)
    sites = collector.sites

    if not sites:
        logger.info(f"[MutationCTF] No se detectaron operadores mutables en {target_p.name}")
        return MutationProbeResult(
            total_mutants=0,
            killed_mutants=0,
            survived_mutants=0,
            mutation_score=1.0,
            survived_details=[],
            passed=True,
        )

    if len(sites) > max_mutants:
        indices = [int(i * (len(sites) - 1) / (max_mutants - 1)) for i in range(max_mutants)]
        selected_sites = [sites[idx] for idx in sorted(set(indices))]
    else:
        selected_sites = sites

    total_mutants = len(selected_sites)
    killed = 0
    survived = 0
    survived_details: list[str] = []

    try:
        for site in selected_sites:
            fresh_tree = ast.parse(original_code)
            injector = SingleMutantInjector(target_id=site["id"], replacement=site["replacement"])
            mutated_tree = injector.visit(fresh_tree)
            mutated_code = ast.unparse(mutated_tree)

            # Write mutant to disk and purge bytecode cache to force recompilation.
            target_p.write_text(mutated_code, encoding="utf-8")
            shutil.rmtree(target_p.parent / "__pycache__", ignore_errors=True)

            # Ejecutar tests contra el mutante
            env = {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": f"{work_root}:{os.environ.get('PYTHONPATH', '')}",
            }
            try:
                res = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                    cwd=str(work_root),
                    env=env,
                )
                if res.returncode != 0:
                    killed += 1
                else:
                    survived += 1
                    survived_details.append(site["desc"])
            except subprocess.TimeoutExpired:
                killed += 1
    finally:
        target_p.write_text(original_code, encoding="utf-8")

    score = round(killed / max(1, total_mutants), 2)
    passed = score >= min_score

    return MutationProbeResult(
        total_mutants=total_mutants,
        killed_mutants=killed,
        survived_mutants=survived,
        mutation_score=score,
        survived_details=survived_details,
        passed=passed,
    )


class MutationCtfProbe:
    """Provide a facade for the mutation testing probe."""

    @staticmethod
    def audit_file(
        target_file: Path | str,
        test_target: Path | str | list[str],
        max_mutants: int = DEFAULT_MAX_MUTANTS,
        min_score: float = DEFAULT_MIN_MUTATION_SCORE,
    ) -> MutationProbeResult:
        """Audit the specified file."""
        return run_mutation_ctf(
            target_file=target_file,
            test_target=test_target,
            max_mutants=max_mutants,
            min_score=min_score,
        )


mutation_ctf_probe = MutationCtfProbe()

__all__ = [
    "DEFAULT_MAX_MUTANTS",
    "DEFAULT_MIN_MUTATION_SCORE",
    "MutationCtfProbe",
    "MutationProbeResult",
    "MutationSiteCollector",
    "SingleMutantInjector",
    "mutation_ctf_probe",
    "run_mutation_ctf",
]
