"""
Structural AST Rewriting Engine — GEMA 02 (SOTA 2026).
Applies pattern-based syntax tree transformations to Python, TypeScript, and JavaScript code.
Integrates native 'ast-grep' in Rust with a deterministic Python AST fallback engine.
Enforces pre-flight syntax verification via py_compile with automatic in-memory rollback.
Zero regex fragility.
"""

from __future__ import annotations

import ast
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("assessment_engine.infrastructure.primitives.ast_rewriter")


@dataclass
class AstRewriteResult:
    success: bool
    modified_files: list[str]
    diff_output: str
    error_message: Optional[str] = None


class PythonPatternTransformer(ast.NodeTransformer):
    """Transform Python AST for deterministic structural replacements."""

    def __init__(self, target_pattern: str, replacement_pattern: str) -> None:
        self.target_pattern = target_pattern
        self.replacement_pattern = replacement_pattern
        self.mutated = False

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Visit a Call AST node."""
        # Reemplazo de llamadas a funciones: ej. old_fn(args) -> new_fn(args)
        if isinstance(node.func, ast.Name) and node.func.id == self.target_pattern:
            node.func.id = self.replacement_pattern
            self.mutated = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == self.target_pattern:
            node.func.attr = self.replacement_pattern
            self.mutated = True
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Visit a FunctionDef AST node."""
        if node.name == self.target_pattern:
            node.name = self.replacement_pattern
            self.mutated = True
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        """Visit an AsyncFunctionDef AST node."""
        if node.name == self.target_pattern:
            node.name = self.replacement_pattern
            self.mutated = True
        return self.generic_visit(node)


class ASTRewriterPrimitive:
    """
    Motor de reescritura estructural mediante AST (ast-grep + Python AST Engine).
    """

    def __init__(self) -> None:
        self.binary = self._detect_ast_grep()

    def _detect_ast_grep(self) -> Optional[str]:
        for bin_name in ("ast-grep", "sg"):
            path = shutil.which(bin_name)
            if path:
                # Validate that the executable is ast-grep and not the shadow-utils 'sg' binary.
                try:
                    res = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=2)
                    if "ast-grep" in res.stdout.lower() or "ast-grep" in res.stderr.lower():
                        return path
                except (subprocess.SubprocessError, OSError):
                    pass
        return None

    def is_available(self) -> bool:
        """Check whether the native Rust ast-grep binary is available."""
        return self.binary is not None

    def _run_ast_grep_native(self, file_path: Path, language: str, pattern: str, rewrite: str, backup: str) -> AstRewriteResult:
        cmd: list[str] = [
            str(self.binary), "run", "--lang", language, "--pattern", pattern, "--rewrite", rewrite, "--update-all", str(file_path.resolve()),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if language == "python":
                val = subprocess.run(["python3", "-m", "py_compile", str(file_path)], capture_output=True, text=True)
                if val.returncode != 0:
                    file_path.write_text(backup, encoding="utf-8")
                    return AstRewriteResult(False, [], "", f"Syntax Error tras ast-grep: {val.stderr}")
            return AstRewriteResult(True, [str(file_path)], res.stdout)
        except subprocess.CalledProcessError as e:
            file_path.write_text(backup, encoding="utf-8")
            return AstRewriteResult(False, [], "", e.stderr or str(e))

    def _run_python_fallback(self, file_path: Path, pattern: str, rewrite: str, backup: str) -> AstRewriteResult:
        try:
            tree = ast.parse(backup)
            transformer = PythonPatternTransformer(pattern, rewrite)
            modified_tree = transformer.visit(tree)
            if not transformer.mutated:
                return AstRewriteResult(False, [], "", f"Patrón '{pattern}' no localizado en el árbol AST.")
            ast.fix_missing_locations(modified_tree)
            new_code = ast.unparse(modified_tree)
            file_path.write_text(new_code, encoding="utf-8")
            val = subprocess.run(["python3", "-m", "py_compile", str(file_path)], capture_output=True, text=True)
            if val.returncode != 0:
                file_path.write_text(backup, encoding="utf-8")
                return AstRewriteResult(False, [], "", f"Syntax Error: {val.stderr}")
            return AstRewriteResult(True, [str(file_path)], "AST transformation applied successfully")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            file_path.write_text(backup, encoding="utf-8")
            return AstRewriteResult(False, [], "", f"Error en transformación AST: {ex}")

    def rewrite_file(
        self, file_path: Path, language: str, pattern: str, rewrite: str,
    ) -> AstRewriteResult:
        """Rewrite a file on disk using ast-grep (if available) or the deterministic Python AST engine."""
        if not file_path.exists():
            return AstRewriteResult(False, [], "", f"Archivo {file_path} no existe")

        backup = file_path.read_text(encoding="utf-8")
        if self.is_available() and self.binary:
            return self._run_ast_grep_native(file_path, language, pattern, rewrite, backup)

        if language == "python":
            return self._run_python_fallback(file_path, pattern, rewrite, backup)

        return AstRewriteResult(False, [], "", f"ast-grep no disponible para el lenguaje '{language}'")

    def rename_function_in_code(self, source_code: str, old_func: str, new_func: str) -> str:
        """Rename a function and its calls directly in memory (compatibility alias)."""
        try:
            tree = ast.parse(source_code)
            transformer = PythonPatternTransformer(old_func, new_func)
            modified_tree = transformer.visit(tree)
            ast.fix_missing_locations(modified_tree)
            return ast.unparse(modified_tree)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[ASTRewriter] Error en transformación AST en memoria: {ex}")
            return source_code


ast_rewriter = ASTRewriterPrimitive()
