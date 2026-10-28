"""
Implement prescriptive refactoring and AST surgery for the Autonomous Product Director.
Decoupled from autonomous_product_director.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

import ast
import logging
from typing import Any

from .director_models import FOWLER_RECIPE_BOOK, PrescriptiveRecipe

logger = logging.getLogger("assessment_engine.infrastructure.evolution.director_refactor")


class FunctionNodeReplacer(ast.NodeTransformer):
    """Replace a function with its updated version and insert helper functions."""

    def __init__(
        self,
        target_function_name: str,
        new_node: ast.FunctionDef | ast.AsyncFunctionDef,
        helper_nodes: list[ast.AST] | None = None,
    ) -> None:
        self.target_name = target_function_name
        self.new_node = new_node
        self.helper_nodes = helper_nodes or []
        self.replaced = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        """Visit a function definition node."""
        if node.name == self.target_name:
            self.replaced = True
            return [*self.helper_nodes, self.new_node]
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        """Visit an asynchronous function definition node."""
        if node.name == self.target_name:
            self.replaced = True
            return [*self.helper_nodes, self.new_node]
        return node


def _extract_function_node(
    tree: ast.AST, name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find FunctionDef or AsyncFunctionDef matching name in AST."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _parse_helper_nodes(helper_code: str) -> tuple[list[ast.AST], str | None]:
    """Parse helper function AST nodes."""
    if not helper_code.strip():
        return [], None
    try:
        h_tree = ast.parse(helper_code)
        nodes = [item for item in h_tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        return nodes, None
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        return [], f"Error parseando funciones auxiliares: {ex}"


class PrescriptiveRefactoringEngine:
    """Execute prescriptive refactorings and AST transformations.
Translate audit findings into Fowler recipes and perform node-level modifications."""

    def get_recipe_for_rule(self, rule_id: str, target_symbol: str) -> PrescriptiveRecipe:
        """Retrieve the formal refactoring recipe based on the violated audit rule."""
        template = FOWLER_RECIPE_BOOK.get(rule_id, {
            "pattern": "Clean Code Refactoring",
            "instructions": ("Refactorizar el bloque reduciendo complejidad y asegurando contratos tipados.",),
            "forbidden": ("Prohibido alterar la firma pública de la función ni eliminar aserciones de prueba.",),
        })

        return PrescriptiveRecipe(
            rule_id=rule_id,
            target_symbol=target_symbol,
            recommended_pattern=template["pattern"],
            actionable_instructions=template["instructions"],
            forbidden_actions=template["forbidden"],
        )

    def extract_function_code(self, source_code: str, func_name: str) -> tuple[str | None, int, int]:
        """Locate and extract the exact source code of a function from the source text."""
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                    lines = source_code.splitlines()
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if node.end_lineno is not None else start_line + 1
                    fn_code = "\n".join(lines[start_line:end_line])
                    return fn_code, node.lineno, end_line
        except SyntaxError:
            pass
        return None, 0, 0

    def apply_surgical_surgery(
        self,
        original_code: str,
        target_func_name: str,
        refactored_func_code: str,
        helper_code: str = "",
    ) -> tuple[bool, str, str]:
        """Replace a function AST node:
1. Validate that the replacement code compiles.
2. Verify that original signature arguments are not mutated.
3. Insert helpers and replace the node in the complete AST.
4. Verify the syntax of the resulting in-memory file."""
        try:
            orig_tree = ast.parse(original_code)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            return False, original_code, f"Error parseando código original: {ex}"

        orig_func = _extract_function_node(orig_tree, target_func_name)
        if not orig_func:
            return False, original_code, f"Función objetivo '{target_func_name}' no localizada en el AST."

        try:
            new_tree = ast.parse(refactored_func_code)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            return False, original_code, f"Error de sintaxis en el código refactorizado: {ex}"

        new_func = _extract_function_node(new_tree, target_func_name)
        if not new_func:
            return False, original_code, f"La función refactorizada no define '{target_func_name}'."

        orig_args = [a.arg for a in orig_func.args.args]
        new_args = [a.arg for a in new_func.args.args]
        if orig_args != new_args:
            return (
                False,
                original_code,
                f"Violación de Firma AST: Los argumentos mutaron de {orig_args} a {new_args}.",
            )

        helper_nodes, err = _parse_helper_nodes(helper_code)
        if err:
            return False, original_code, err

        replacer = FunctionNodeReplacer(target_func_name, new_func, helper_nodes)
        transformed_tree = replacer.visit(orig_tree)
        if not replacer.replaced:
            return False, original_code, f"Fallo al sustituir el nodo '{target_func_name}'."

        ast.fix_missing_locations(transformed_tree)
        new_full_code = ast.unparse(transformed_tree)

        try:
            compile(new_full_code, "<surgical_memory>", "exec")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            return False, original_code, f"Error de compilación en el código resultante: {ex}"

        return True, new_full_code, "Cirugía AST completada exitosamente sin rotura de contratos."
