"""
Provide data models and AST signature snapshots. Decoupled from ast_signature_guard.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class VerdictStatus(str, Enum):
    """Represent canonical verdict states for the Cognitive Arbiter."""
    CERTIFIED = "CERTIFIED"
    REJECTED_REGRESSION = "REJECTED_REGRESSION"
    REJECTED_AST_SIGNATURE = "REJECTED_AST_SIGNATURE"
    REJECTED_MUTATION_SCORE = "REJECTED_MUTATION_SCORE"
    REJECTED_COMPLEXITY = "REJECTED_COMPLEXITY"
    REJECTED_DEPENDENCY_DRIFT = "REJECTED_DEPENDENCY_DRIFT"
    REJECTED_TRUNCATION = "REJECTED_TRUNCATION"
    ABORTED_USER = "ABORTED_USER"


@dataclass(frozen=True)
class FunctionSignature:
    """Represent a function or method extracted via AST."""
    name: str
    args: tuple[str, ...]
    vararg: str | None
    kwarg: str | None
    kwonlyargs: tuple[str, ...]
    has_return_annotation: bool
    is_async: bool
    posonlyargs: tuple[str, ...] = ()
    defaults_count: int = 0
    kw_defaults_count: int = 0
    decorators: tuple[str, ...] = ()
    docstring: str | None = None
    return_annotation: str | None = None
    arg_annotations: dict[str, str] = field(default_factory=dict)
    kwonlyarg_annotations: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FunctionSignature:
        """Create a FunctionSignature instance from a dictionary."""
        return cls(
            name=data["name"],
            args=tuple(data.get("args", ())),
            vararg=data.get("vararg"),
            kwarg=data.get("kwarg"),
            kwonlyargs=tuple(data.get("kwonlyargs", ())),
            has_return_annotation=bool(data.get("has_return_annotation", False)),
            is_async=bool(data.get("is_async", False)),
            posonlyargs=tuple(data.get("posonlyargs", ())),
            defaults_count=int(data.get("defaults_count", 0)),
            kw_defaults_count=int(data.get("kw_defaults_count", 0)),
            decorators=tuple(data.get("decorators", ())),
            docstring=data.get("docstring"),
            return_annotation=data.get("return_annotation"),
            arg_annotations=dict(data.get("arg_annotations", {})),
            kwonlyarg_annotations=dict(data.get("kwonlyarg_annotations", {})),
        )


@dataclass(frozen=True)
class ModuleSignatureSnapshot:
    """Represent an immutable snapshot of a module's public signatures."""
    module_path: str
    functions: dict[str, FunctionSignature]
    classes: dict[str, dict[str, FunctionSignature]]
    syntax_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "module_path": self.module_path,
            "functions": {k: v.to_dict() for k, v in self.functions.items()},
            "classes": {
                cls_name: {m_name: m_sig.to_dict() for m_name, m_sig in methods.items()}
                for cls_name, methods in self.classes.items()
            },
            "syntax_error": self.syntax_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModuleSignatureSnapshot:
        """Create a ModuleSignatureSnapshot instance from a dictionary."""
        functions: dict[str, FunctionSignature] = {}
        for k, v in data.get("functions", {}).items():
            functions[k] = v if isinstance(v, FunctionSignature) else FunctionSignature.from_dict(v)

        classes: dict[str, dict[str, FunctionSignature]] = {}
        for cls_name, methods in data.get("classes", {}).items():
            classes[cls_name] = {}
            for m_name, m_val in methods.items():
                classes[cls_name][m_name] = (
                    m_val if isinstance(m_val, FunctionSignature) else FunctionSignature.from_dict(m_val)
                )

        return cls(
            module_path=str(data.get("module_path", "")),
            functions=functions,
            classes=classes,
            syntax_error=data.get("syntax_error"),
        )

    def get_symbol_count(self) -> int:
        """Return the total number of tracked public symbols."""
        methods_count = sum(len(methods) for methods in self.classes.values())
        return len(self.functions) + methods_count

    def all_symbols(self) -> list[str]:
        """Return a canonical list of tracked symbol names."""
        symbols = list(self.functions.keys())
        for cls_name, methods in self.classes.items():
            symbols.append(cls_name)
            for m_name in methods:
                symbols.append(f"{cls_name}.{m_name}")
        return sorted(symbols)


@dataclass(frozen=True)
class SignatureViolation:
    """Represent a formal interface contract violation."""
    symbol_name: str
    violation_type: str  # 'MISSING_FUNCTION' | 'ARGS_MUTATED' | 'RETURN_MUTATED' | 'CLASS_MUTATED' | 'ASYNC_MUTATED' | 'SYNTAX_ERROR'
    details: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)


@dataclass
class CognitiveArbiterReport:
    """Represent a certification dossier issued by the Cognitive Arbiter."""
    task_description: str
    status: VerdictStatus
    iterations_used: int
    ast_violations: list[SignatureViolation]
    regression_tests_passed: bool
    total_tests_run: int
    mutation_score: float
    max_cyclomatic_complexity: int
    diff_stat: str
    worktree_path: Path | None
    execution_time_seconds: float
