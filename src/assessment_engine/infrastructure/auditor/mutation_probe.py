"""
Mutation Testing Probe Primitive — GEMA 54 (ISO/IEC/IEEE 29119 Standard).
Injects deliberate AST mutations into business logic to expose vanity tests.
Verifies that generated test suites actually assert invariants and fail when logic is corrupted.
SOTA 2026: Multi-Operator Mutation Engine:
- ROR (Relational Operator Replacement): >, <, ==, !=, in, not in.
- AOR (Arithmetic Operator Replacement): +, -.
- LCR (Logical Connector Replacement): and, or.
- COR (Constant & Boolean Replacement): True, False.
"""

from __future__ import annotations

import ast
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("assessment_engine.infrastructure.foundry.mutation_probe")


@dataclass
class MutationProbeResult:
    mutant_killed: bool  # True: Test failed against mutated code (legitimate test). False: Vanity test.
    mutation_description: str
    test_output: str


class AstOperatorMutator(ast.NodeTransformer):
    """Mutate syntax in memory by inverting relational, arithmetic, and logical operators."""

    def __init__(self) -> None:
        self.mutated = False
        self.mutation_desc = "No mutation"

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Visit a comparison expression node."""
        if not self.mutated and len(node.ops) == 1:
            op = node.ops[0]
            if isinstance(op, ast.Gt):
                node.ops = [ast.LtE()]
                self.mutated = True
                self.mutation_desc = f"ROR: '>' inverted to '<=' at line {node.lineno}"
            elif isinstance(op, ast.Lt):
                node.ops = [ast.GtE()]
                self.mutated = True
                self.mutation_desc = f"ROR: '<' inverted to '>=' at line {node.lineno}"
            elif isinstance(op, ast.Eq):
                node.ops = [ast.NotEq()]
                self.mutated = True
                self.mutation_desc = f"ROR: '==' inverted to '!=' at line {node.lineno}"
            elif isinstance(op, ast.NotEq):
                node.ops = [ast.Eq()]
                self.mutated = True
                self.mutation_desc = f"ROR: '!=' inverted to '==' at line {node.lineno}"
            elif isinstance(op, ast.In):
                node.ops = [ast.NotIn()]
                self.mutated = True
                self.mutation_desc = f"ROR: 'in' inverted to 'not in' at line {node.lineno}"
            elif isinstance(op, ast.NotIn):
                node.ops = [ast.In()]
                self.mutated = True
                self.mutation_desc = f"ROR: 'not in' inverted to 'in' at line {node.lineno}"
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Visit a binary operation node."""
        # AOR: Arithmetic operators (+ <-> -)
        if not self.mutated:
            if isinstance(node.op, ast.Add):
                node.op = ast.Sub()
                self.mutated = True
                self.mutation_desc = f"AOR: '+' inverted to '-' at line {node.lineno}"
            elif isinstance(node.op, ast.Sub):
                node.op = ast.Add()
                self.mutated = True
                self.mutation_desc = f"AOR: '-' inverted to '+' at line {node.lineno}"
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        """Visit a boolean operation node."""
        # LCR: Logical connectors (and <-> or)
        if not self.mutated:
            if isinstance(node.op, ast.And):
                node.op = ast.Or()
                self.mutated = True
                self.mutation_desc = f"LCR: 'and' inverted to 'or' at line {node.lineno}"
            elif isinstance(node.op, ast.Or):
                node.op = ast.And()
                self.mutated = True
                self.mutation_desc = f"LCR: 'or' inverted to 'and' at line {node.lineno}"
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Visit a constant value node."""
        # COR: Constantes booleanas
        if not self.mutated and isinstance(node.value, bool):
            node.value = not node.value
            self.mutated = True
            self.mutation_desc = f"COR: boolean '{not node.value}' inverted to '{node.value}' at line {node.lineno}"
        return self.generic_visit(node)


class MutationTestingProbe:
    """
    Run mutation test probes.
    """

    @staticmethod
    def audit_test_against_mutation(target_file: Path, test_command: list[str]) -> MutationProbeResult:
        """Run the test against a mutated version of target_file. Unconditionally restore the original file in the finally block."""
        if not target_file.exists():
            return MutationProbeResult(False, "Archivo objetivo no encontrado", "")

        backup = target_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(backup)
            mutator = AstOperatorMutator()
            mutated_tree = mutator.visit(tree)

            if not mutator.mutated:
                return MutationProbeResult(True, "Sin operadores mutables detectados", "N/A")

            target_file.write_text(ast.unparse(mutated_tree), encoding="utf-8")
            res = subprocess.run(test_command, capture_output=True, text=True, timeout=15)

            killed = (res.returncode != 0)
            return MutationProbeResult(
                mutant_killed=killed,
                mutation_description=mutator.mutation_desc,
                test_output=res.stdout + res.stderr
            )
        except subprocess.TimeoutExpired:
            return MutationProbeResult(True, "Timeout detectado (mutante bloqueante matado)", "")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[MutationProbe] Error during mutation of {target_file.name}: {ex}")
            return MutationProbeResult(False, f"Error during mutation: {ex}", "")
        finally:
            target_file.write_text(backup, encoding="utf-8")


MutationTestingProbePrimitive = MutationTestingProbe
mutation_probe = MutationTestingProbe()
