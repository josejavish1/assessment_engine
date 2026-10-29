"""
Protect AST signatures and prevent regressions across public APIs. Extract a baseline ModuleSignatureSnapshot from a module or code tree and audit interface regressions, including missing functions, mutated arguments, broken async, stripped return types, and removed classes.
"""
from __future__ import annotations


import ast
import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .ast_signature_models import (
    CognitiveArbiterReport,
    FunctionSignature,
    ModuleSignatureSnapshot,
    SignatureViolation,
    VerdictStatus,
)

logger = logging.getLogger("assessment_engine.infrastructure.evolution.ast_signature_guard")


def _extract_func_sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionSignature:
    """Extract the canonical signature from an ast.FunctionDef or ast.AsyncFunctionDef node."""
    posonly = tuple(arg.arg for arg in getattr(node.args, "posonlyargs", []))
    regular_args = tuple(arg.arg for arg in node.args.args)
    all_args = posonly + regular_args

    vararg = node.args.vararg.arg if node.args.vararg else None
    kwarg = node.args.kwarg.arg if node.args.kwarg else None
    kwonlyargs = tuple(arg.arg for arg in node.args.kwonlyargs)

    has_return = node.returns is not None
    return_annotation = ast.unparse(node.returns) if node.returns is not None else None
    is_async = isinstance(node, ast.AsyncFunctionDef)

    arg_annotations: dict[str, str] = {}
    for arg in list(getattr(node.args, "posonlyargs", [])) + list(node.args.args):
        if arg.annotation is not None:
            arg_annotations[arg.arg] = ast.unparse(arg.annotation)

    kwonlyarg_annotations: dict[str, str] = {}
    for arg in node.args.kwonlyargs:
        if arg.annotation is not None:
            kwonlyarg_annotations[arg.arg] = ast.unparse(arg.annotation)

    defaults_count = len(node.args.defaults)
    kw_defaults_count = sum(1 for d in getattr(node.args, "kw_defaults", []) if d is not None)

    decorators: list[str] = []
    for dec in node.decorator_list:
        if hasattr(ast, "unparse"):
            decorators.append(ast.unparse(dec))
        elif isinstance(dec, ast.Name):
            decorators.append(dec.id)
        else:
            decorators.append(type(dec).__name__)

    docstring = ast.get_docstring(node)

    return FunctionSignature(
        name=node.name,
        args=all_args,
        vararg=vararg,
        kwarg=kwarg,
        kwonlyargs=kwonlyargs,
        has_return_annotation=has_return,
        is_async=is_async,
        posonlyargs=posonly,
        defaults_count=defaults_count,
        kw_defaults_count=kw_defaults_count,
        decorators=tuple(decorators),
        docstring=docstring,
        return_annotation=return_annotation,
        arg_annotations=arg_annotations,
        kwonlyarg_annotations=kwonlyarg_annotations,
    )


def extract_signatures_from_code(code: str, module_path: str = "") -> dict[str, Any]:
    """Parse Python code into an AST and extract public signatures (ignoring private members). Supports module functions, class methods, async functions, and __init__ constructors. Fully conforms to RFC-015 Section 3.1."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"Syntax error parsing code for AST signatures: {e}")
        return {"functions": {}, "classes": {}, "syntax_error": str(e)}

    functions: dict[str, FunctionSignature] = {}
    classes: dict[str, dict[str, FunctionSignature]] = {}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            functions[node.name] = _extract_func_sig(node)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            class_methods: dict[str, FunctionSignature] = {}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    not item.name.startswith("_") or item.name == "__init__"
                ):
                    class_methods[item.name] = _extract_func_sig(item)
            classes[node.name] = class_methods

    return {"functions": functions, "classes": classes}


def extract_module_signatures(source: str | Path, module_path: str = "") -> ModuleSignatureSnapshot:
    """
    Extract an immutable ModuleSignatureSnapshot from source code or a file.
    """
    actual_path = module_path
    if isinstance(source, Path) or (
        isinstance(source, str)
        and not (
            "\n" in source
            or source.strip().startswith(("def ", "class ", "import ", "from ", "#", '"""', "'''"))
        )
    ):
        path_candidate = Path(source)
        if path_candidate.is_file():
            actual_path = str(path_candidate)
            code = path_candidate.read_text(encoding="utf-8")
        else:
            code = str(source)
    else:
        code = str(source)

    extracted = extract_signatures_from_code(code, module_path=actual_path)
    return ModuleSignatureSnapshot(
        module_path=actual_path,
        functions=extracted.get("functions", {}),
        classes=extracted.get("classes", {}),
        syntax_error=extracted.get("syntax_error"),
    )


def snapshot_file(file_path: Path | str) -> ModuleSignatureSnapshot:
    """Create an immutable AST snapshot from a Python file on disk."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"El archivo especificado no existe: {file_path}")
    content = p.read_text(encoding="utf-8")
    extracted = extract_signatures_from_code(content, module_path=str(p))
    return ModuleSignatureSnapshot(
        module_path=str(p),
        functions=extracted.get("functions", {}),
        classes=extracted.get("classes", {}),
        syntax_error=extracted.get("syntax_error"),
    )


def snapshot_directory(
    dir_path: Path | str,
    pattern: str = "**/*.py",
    exclude_dirs: tuple[str, ...] = (
        "venv",
        ".venv",
        ".git",
        "__pycache__",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    ),
) -> dict[str, ModuleSignatureSnapshot]:
    """Create a snapshot of all Python modules in a directory."""
    root = Path(dir_path).resolve()
    snapshots: dict[str, ModuleSignatureSnapshot] = {}

    for file_path in root.glob(pattern):
        # Excluir directorios prohibidos
        if any(part in exclude_dirs for part in file_path.parts):
            continue
        if file_path.is_file():
            rel_key = str(file_path.relative_to(root))
            snapshots[rel_key] = snapshot_file(file_path)

    return snapshots


def _normalize_to_snapshot(
    obj: ModuleSignatureSnapshot | dict[str, Any] | str | Path,
) -> tuple[dict[str, FunctionSignature], dict[str, dict[str, FunctionSignature]], str | None]:
    """Normaliza cualquier entrada a diccionarios de FunctionSignature y classes."""
    if isinstance(obj, ModuleSignatureSnapshot):
        return obj.functions, obj.classes, obj.syntax_error

    if isinstance(obj, dict):
        raw_functions = obj.get("functions", {})
        norm_functions: dict[str, FunctionSignature] = {}
        for k, v in raw_functions.items():
            if isinstance(v, FunctionSignature):
                norm_functions[k] = v
            elif isinstance(v, dict):
                norm_functions[k] = FunctionSignature.from_dict(v)

        raw_classes = obj.get("classes", {})
        norm_classes: dict[str, dict[str, FunctionSignature]] = {}
        for cls_name, methods in raw_classes.items():
            norm_classes[cls_name] = {}
            for m_name, m_val in methods.items():
                if isinstance(m_val, FunctionSignature):
                    norm_classes[cls_name][m_name] = m_val
                elif isinstance(m_val, dict):
                    norm_classes[cls_name][m_name] = FunctionSignature.from_dict(m_val)

        return norm_functions, norm_classes, obj.get("syntax_error")

    if isinstance(obj, (str, Path)):
        snap = extract_module_signatures(obj)
        return snap.functions, snap.classes, snap.syntax_error

    raise TypeError(f"Unsupported type for AST signature analysis: {type(obj)}")


def _diff_argument_type_annotations(
    symbol_name: str,
    base_annotations: dict[str, str],
    curr_annotations: dict[str, str],
    curr_args_container: tuple[str, ...],
    is_kwonly: bool = False,
) -> list[SignatureViolation]:
    violations: list[SignatureViolation] = []
    kw_prefix = "keyword-only " if is_kwonly else ""
    for arg_name, base_type in base_annotations.items():
        if arg_name in curr_annotations:
            curr_type = curr_annotations[arg_name]
            if base_type != curr_type:
                violations.append(
                    SignatureViolation(
                        symbol_name=symbol_name,
                        violation_type="ARG_TYPE_MUTATED",
                        details=f"Argument type {kw_prefix}'{arg_name}' altered in '{symbol_name}': Expected '{base_type}', got '{curr_type}'",
                    )
                )
        elif arg_name in curr_args_container:
            violations.append(
                SignatureViolation(
                    symbol_name=symbol_name,
                    violation_type="ARG_TYPE_MUTATED",
                    details=f"Type annotation for argument {kw_prefix}'{arg_name}' removed in '{symbol_name}'",
                )
            )
    return violations


def _diff_function_signatures(
    symbol_name: str,
    base_sig: FunctionSignature,
    curr_sig: FunctionSignature,
    is_method: bool = False,
) -> list[SignatureViolation]:
    violations: list[SignatureViolation] = []
    scope_str = f" in '{symbol_name}'" if is_method else ""

    if base_sig.args != curr_sig.args:
        details = f"Arguments altered{scope_str}: Expected {base_sig.args}, got {curr_sig.args}"
        violations.append(SignatureViolation(symbol_name=symbol_name, violation_type="ARGS_MUTATED", details=details))
    elif base_sig.kwonlyargs != curr_sig.kwonlyargs:
        details = f"Keyword-only arguments altered{scope_str}: Expected {base_sig.kwonlyargs}, got {curr_sig.kwonlyargs}" if not is_method else f"Keyword-only arguments altered in '{symbol_name}'"
        violations.append(SignatureViolation(symbol_name=symbol_name, violation_type="ARGS_MUTATED", details=details))
    elif base_sig.vararg != curr_sig.vararg:
        details = f"Parameter *args altered{scope_str}: Expected {base_sig.vararg}, got {curr_sig.vararg}" if not is_method else f"Parameter *args altered in '{symbol_name}'"
        violations.append(SignatureViolation(symbol_name=symbol_name, violation_type="ARGS_MUTATED", details=details))
    elif base_sig.kwarg != curr_sig.kwarg:
        details = f"Parameter **kwargs altered{scope_str}: Expected {base_sig.kwarg}, got {curr_sig.kwarg}" if not is_method else f"Parameter **kwargs altered in '{symbol_name}'"
        violations.append(SignatureViolation(symbol_name=symbol_name, violation_type="ARGS_MUTATED", details=details))

    if base_sig.is_async != curr_sig.is_async:
        violations.append(
            SignatureViolation(
                symbol_name=symbol_name,
                violation_type="ASYNC_MUTATED",
                details=f"Synchrony altered in '{symbol_name}': is_async changed from {base_sig.is_async} to {curr_sig.is_async}",
            )
        )

    if base_sig.has_return_annotation and not curr_sig.has_return_annotation:
        violations.append(
            SignatureViolation(
                symbol_name=symbol_name,
                violation_type="RETURN_MUTATED",
                details=f"Return annotation removed in '{symbol_name}'",
            )
        )
    elif (
        base_sig.return_annotation is not None
        and curr_sig.return_annotation is not None
        and base_sig.return_annotation != curr_sig.return_annotation
    ):
        violations.append(
            SignatureViolation(
                symbol_name=symbol_name,
                violation_type="RETURN_TYPE_MUTATED",
                details=f"Return type altered in '{symbol_name}': Expected '{base_sig.return_annotation}', got '{curr_sig.return_annotation}'",
            )
        )

    violations.extend(_diff_argument_type_annotations(symbol_name, base_sig.arg_annotations, curr_sig.arg_annotations, curr_sig.args, is_kwonly=False))
    if not is_method:
        violations.extend(_diff_argument_type_annotations(symbol_name, base_sig.kwonlyarg_annotations, curr_sig.kwonlyarg_annotations, curr_sig.kwonlyargs, is_kwonly=True))

    return violations


def _diff_classes_signatures(
    base_classes: dict[str, dict[str, FunctionSignature]],
    curr_classes: dict[str, dict[str, FunctionSignature]],
) -> list[SignatureViolation]:
    violations: list[SignatureViolation] = []
    for cls_name, base_methods in base_classes.items():
        if cls_name not in curr_classes:
            violations.append(
                SignatureViolation(
                    symbol_name=cls_name,
                    violation_type="CLASS_MUTATED",
                    details=f"Public class '{cls_name}' was removed.",
                )
            )
        else:
            curr_methods = curr_classes[cls_name]
            for m_name, base_m_sig in base_methods.items():
                if m_name not in curr_methods:
                    violations.append(
                        SignatureViolation(
                            symbol_name=f"{cls_name}.{m_name}",
                            violation_type="MISSING_FUNCTION",
                            details=f"Public method '{m_name}' of '{cls_name}' was removed.",
                        )
                    )
                else:
                    curr_m_sig = curr_methods[m_name]
                    violations.extend(_diff_function_signatures(f"{cls_name}.{m_name}", base_m_sig, curr_m_sig, is_method=True))
    return violations


def _diff_additive_symbols(
    base_fns: dict[str, Any],
    curr_fns: dict[str, Any],
    base_classes: dict[str, dict[str, Any]],
    curr_classes: dict[str, dict[str, Any]],
) -> list[SignatureViolation]:
    violations: list[SignatureViolation] = []
    for fn_name in curr_fns:
        if fn_name not in base_fns:
            violations.append(
                SignatureViolation(
                    symbol_name=fn_name,
                    violation_type="ADDITIVE_FUNCTION_FORBIDDEN",
                    details=f"Public function '{fn_name}' added in sealed mode (allow_additive=False).",
                )
            )

    for cls_name in curr_classes:
        if cls_name not in base_classes:
            violations.append(
                SignatureViolation(
                    symbol_name=cls_name,
                    violation_type="ADDITIVE_CLASS_FORBIDDEN",
                    details=f"Public class '{cls_name}' added in sealed mode (allow_additive=False).",
                )
            )
        else:
            for m_name in curr_classes[cls_name]:
                if m_name not in base_classes[cls_name]:
                    violations.append(
                        SignatureViolation(
                            symbol_name=f"{cls_name}.{m_name}",
                            violation_type="ADDITIVE_METHOD_FORBIDDEN",
                            details=f"Public method '{m_name}' of '{cls_name}' added in sealed mode.",
                        )
                    )
    return violations


def diff_module_signatures(
    baseline: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
    current: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
    allow_additive: bool = True,
) -> list[SignatureViolation]:
    """Compare two snapshots and detect interface regressions (RFC-015 Section 3.1):
1. If a baseline public function is missing -> VIOLATION (MISSING_FUNCTION).
2. If positional arguments or signatures changed -> VIOLATION (ARGS_MUTATED).
3. If synchrony (async def vs def) changed -> VIOLATION (ASYNC_MUTATED).
4. If return type annotation was removed -> VIOLATION (RETURN_MUTATED).
5. If a public class is missing -> VIOLATION (CLASS_MUTATED).
6. If a public class lost public methods -> VIOLATION (MISSING_FUNCTION).
7. If allow_additive is False and new symbols are detected -> VIOLATION (ADDITIVE_*_FORBIDDEN)."""
    violations: list[SignatureViolation] = []

    base_fns, base_classes, base_syntax_err = _normalize_to_snapshot(baseline)
    curr_fns, curr_classes, curr_syntax_err = _normalize_to_snapshot(current)

    if curr_syntax_err is not None and base_syntax_err is None:
        violations.append(
            SignatureViolation(
                symbol_name="<module>",
                violation_type="SYNTAX_ERROR",
                details=f"Syntax error analyzing current module: {curr_syntax_err}",
            )
        )

    # 1. Validate baseline module functions
    for fn_name, base_sig in base_fns.items():
        if fn_name not in curr_fns:
            violations.append(
                SignatureViolation(
                    symbol_name=fn_name,
                    violation_type="MISSING_FUNCTION",
                    details=f"Public function '{fn_name}' was removed or renamed.",
                )
            )
        else:
            violations.extend(_diff_function_signatures(fn_name, base_sig, curr_fns[fn_name], is_method=False))

    violations.extend(_diff_classes_signatures(base_classes, curr_classes))

    if not allow_additive:
        violations.extend(_diff_additive_symbols(base_fns, curr_fns, base_classes, curr_classes))

    return violations


def diff_ast_signatures(
    baseline: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
    current: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
    allow_additive: bool = True,
) -> list[SignatureViolation]:
    """Provide a canonical alias for diff_module_signatures."""
    return diff_module_signatures(baseline, current, allow_additive=allow_additive)


def diff_directory_snapshots(
    baseline: dict[str, ModuleSignatureSnapshot],
    current: dict[str, ModuleSignatureSnapshot],
    allow_additive: bool = True,
) -> dict[str, list[SignatureViolation]]:
    """Compare directory-level snapshots and group violations by module relative path."""
    violations_by_module: dict[str, list[SignatureViolation]] = {}

    for mod_path, base_snap in baseline.items():
        if mod_path not in current:
            violations_by_module[mod_path] = [
                SignatureViolation(
                    symbol_name=mod_path,
                    violation_type="MISSING_MODULE",
                    details=f"Entire module '{mod_path}' was removed or moved.",
                )
            ]
        else:
            curr_snap = current[mod_path]
            diff = diff_module_signatures(base_snap, curr_snap, allow_additive=allow_additive)
            if diff:
                violations_by_module[mod_path] = diff

    if not allow_additive:
        for mod_path in current:
            if mod_path not in baseline:
                violations_by_module[mod_path] = [
                    SignatureViolation(
                        symbol_name=mod_path,
                        violation_type="ADDITIVE_MODULE_FORBIDDEN",
                        details=f"Module '{mod_path}' added in sealed mode (allow_additive=False).",
                    )
                ]

    return violations_by_module


class AstSignatureGuard:
    """Provide a canonical facade to audit and certify interface contracts at development time."""

    @staticmethod
    def extract_signatures_from_code(code: str, module_path: str = "") -> dict[str, Any]:
        """Extract signatures from Python source code."""
        return extract_signatures_from_code(code, module_path=module_path)

    @staticmethod
    def extract_module_signatures(source: str | Path, module_path: str = "") -> ModuleSignatureSnapshot:
        """Extract a module signature snapshot from a source string or file path."""
        return extract_module_signatures(source, module_path=module_path)

    @staticmethod
    def snapshot_file(file_path: Path | str) -> ModuleSignatureSnapshot:
        """Create a signature snapshot for the specified Python file."""
        return snapshot_file(file_path)

    @staticmethod
    def snapshot_directory(
        dir_path: Path | str,
        pattern: str = "**/*.py",
        exclude_dirs: tuple[str, ...] = ("venv", ".venv", ".git", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache"),
    ) -> dict[str, ModuleSignatureSnapshot]:
        """Recursively create signature snapshots for Python files in a directory."""
        return snapshot_directory(dir_path, pattern=pattern, exclude_dirs=exclude_dirs)

    @staticmethod
    def diff(
        baseline: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
        current: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
        allow_additive: bool = True,
    ) -> list[SignatureViolation]:
        """Compute the difference between two signature snapshots."""
        return diff_module_signatures(baseline, current, allow_additive=allow_additive)

    @staticmethod
    def diff_ast_signatures(
        baseline: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
        current: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
        allow_additive: bool = True,
    ) -> list[SignatureViolation]:
        """Compare two AST signature collections and return their differences."""
        return diff_ast_signatures(baseline, current, allow_additive=allow_additive)

    @staticmethod
    def audit_code_changes(
        baseline_code: str,
        current_code: str,
        allow_additive: bool = True,
    ) -> list[SignatureViolation]:
        """Audit two in-memory code strings."""
        return diff_module_signatures(baseline_code, current_code, allow_additive=allow_additive)

    @staticmethod
    def audit_file_mutation(
        baseline_file: Path | str,
        current_file: Path | str,
        allow_additive: bool = True,
    ) -> list[SignatureViolation]:
        """Audita dos archivos en disco."""
        snap_base = snapshot_file(baseline_file)
        snap_curr = snapshot_file(current_file)
        return diff_module_signatures(snap_base, snap_curr, allow_additive=allow_additive)

    @staticmethod
    def verify_contract(
        baseline: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
        current: dict[str, Any] | ModuleSignatureSnapshot | str | Path,
        allow_additive: bool = True,
    ) -> tuple[bool, list[SignatureViolation]]:
        """Return (is_certified: bool, violations: list[SignatureViolation]). Certified if and only if violations is empty."""
        violations = diff_module_signatures(baseline, current, allow_additive=allow_additive)
        return (len(violations) == 0, violations)


def format_snapshot_as_stub(snapshot: ModuleSignatureSnapshot) -> str:
    """Format a ModuleSignatureSnapshot as a clean type stub (.pyi) for deterministic injection into LLM prompts."""
    lines: list[str] = []

    for cls_name, methods in snapshot.classes.items():
        if cls_name.startswith("_"):
            continue
        lines.append(f"class {cls_name}:")
        has_public_methods = False
        for m_name, m_sig in methods.items():
            if m_name.startswith("_") and m_name != "__init__":
                continue
            has_public_methods = True
            async_prefix = "async " if m_sig.is_async else ""
            args_list = []
            for a in m_sig.args:
                ann = m_sig.arg_annotations.get(a)
                args_list.append(f"{a}: {ann}" if ann else a)
            args_str = ", ".join(args_list)
            ret_str = f" -> {m_sig.return_annotation}" if m_sig.return_annotation else ""
            lines.append(f"    {async_prefix}def {m_name}({args_str}){ret_str}: ...")
        if not has_public_methods:
            lines.append("    ...")
        lines.append("")

    for f_name, f_sig in snapshot.functions.items():
        if f_name.startswith("_"):
            continue
        async_prefix = "async " if f_sig.is_async else ""
        args_list = []
        for a in f_sig.args:
            ann = f_sig.arg_annotations.get(a)
            args_list.append(f"{a}: {ann}" if ann else a)
        args_str = ", ".join(args_list)
        ret_str = f" -> {f_sig.return_annotation}" if f_sig.return_annotation else ""
        lines.append(f"{async_prefix}def {f_name}({args_str}){ret_str}: ...")

    return "\n".join(lines).strip()


ast_signature_guard = AstSignatureGuard()

__all__ = [
    "AstSignatureGuard", "CognitiveArbiterReport", "FunctionSignature", "ModuleSignatureSnapshot",
    "SignatureViolation", "VerdictStatus", "ast_signature_guard", "diff_ast_signatures",
    "diff_directory_snapshots", "diff_module_signatures", "extract_module_signatures",
    "extract_signatures_from_code", "format_snapshot_as_stub", "snapshot_directory", "snapshot_file",
]
