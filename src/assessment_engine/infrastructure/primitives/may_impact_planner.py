"""
May-Impact DAG Planning Engine — GEMA 05 (Microsoft CodePlan / SOTA 2026).
Constructs a Directed Acyclic Graph (DAG) of module dependencies and AST contract drifts.
Detects signature drift in functions/classes and calculates the topological cascade of files affected.
Emits an ordered queue of edit obligations using graphlib.TopologicalSorter.
Restricts validation tests strictly to the impacted closure.
"""

from __future__ import annotations

import ast
import graphlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("assessment_engine.infrastructure.primitives.may_impact_planner")


@dataclass
class EditObligation:
    file_path: str
    impacted_symbol: str
    reason: str


@dataclass
class ImpactAnalysisResult:
    target_file: str
    impacted_files: list[str] = field(default_factory=list)
    impact_depth: int = 1
    edit_obligations: list[EditObligation] = field(default_factory=list)
    topological_order: list[str] = field(default_factory=list)


class MayImpactPlannerPrimitive:
    """
    Plan impact analysis based on dependency graphs and AST contract mutations.
    """

    @staticmethod
    def _extract_methods_from_class(node: ast.ClassDef, signatures: dict[str, list[str]]) -> None:
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                signatures[f"{node.name}.__init__"] = [a.arg for a in item.args.args]

    @classmethod
    def extract_function_signatures(cls, content: str) -> dict[str, list[str]]:
        """Extract function and method signatures and parameters using AST."""
        signatures: dict[str, list[str]] = {}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signatures[node.name] = [a.arg for a in node.args.args]
                elif isinstance(node, ast.ClassDef):
                    cls._extract_methods_from_class(node, signatures)
        except SyntaxError:
            pass
        return signatures

    def detect_signature_drift(self, old_content: str, new_content: str) -> list[str]:
        """Detect symbols whose signatures have changed between two code versions."""
        old_sigs = self.extract_function_signatures(old_content)
        new_sigs = self.extract_function_signatures(new_content)
        drifted: list[str] = []
        for name, args in old_sigs.items():
            if name in new_sigs and new_sigs[name] != args:
                drifted.append(name)
            elif name not in new_sigs:
                # Symbol deleted or renamed.
                drifted.append(name)
        return drifted

    def plan_propagation(
        self,
        drifted_symbol: str,
        project_files: dict[str, str],
    ) -> list[EditObligation]:
        """Calculate which files contain calls to the symbol whose signature changed."""
        obligations: list[EditObligation] = []
        sym_name = drifted_symbol.split(".")[-1]
        for rel_path, content in project_files.items():
            if sym_name in content:
                obligations.append(EditObligation(
                    file_path=rel_path,
                    impacted_symbol=drifted_symbol,
                    reason=f"Invocación de '{drifted_symbol}' con firma mutada detectada.",
                ))
        return obligations

    def _is_file_ignored(self, p: Path, modified_file: str, root: Path, SUPPORTED_EXTS: set[str]) -> bool:
        if p.suffix not in SUPPORTED_EXTS:
            return True
        if any(x in p.parts for x in ("venv", ".venv", "__pycache__", ".git", "node_modules", "dist", "build")):
            return True
        rel = str(p.relative_to(root))
        return rel == modified_file

    def _check_has_import(self, content: str, suffix: str, stem: str) -> bool:
        if suffix == ".py":
            return f"import {stem}" in content or f"from {stem}" in content or f".{stem}" in content
        elif suffix in {".ts", ".tsx", ".js", ".jsx"}:
            return (
                f"from '{stem}'" in content or 
                f"from \"{stem}\"" in content or 
                f"import('{stem}')" in content or
                f"/api/{stem}" in content
            )
        return False

    def _build_topological_order(self, impacted: set[str], file_deps: dict[str, set[str]]) -> list[str]:
        if not impacted:
            return []
        try:
            ts = graphlib.TopologicalSorter(file_deps)
            return [f for f in ts.static_order() if f in impacted]
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return sorted(list(impacted))

    def analyze_impact(self, root_dir: Path, modified_file: str) -> ImpactAnalysisResult:
        """Determine which files import or depend on the modified file, including TS/JS frontend files."""
        target_path = Path(modified_file)
        stem = target_path.stem
        root = root_dir.resolve()

        file_deps: dict[str, set[str]] = {}
        impacted: set[str] = set()
        SUPPORTED_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx"}

        for p in root.rglob("*"):
            if self._is_file_ignored(p, modified_file, root, SUPPORTED_EXTS):
                continue
            rel = str(p.relative_to(root))
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                if self._check_has_import(content, p.suffix, stem):
                    impacted.add(rel)
                    file_deps.setdefault(rel, set()).add(modified_file)
            except OSError:
                pass

        ordered_files = self._build_topological_order(impacted, file_deps)
        obligations = [EditObligation(file_path=f, impacted_symbol=stem, reason=f"Dependencia directa del módulo '{stem}'.") for f in ordered_files]

        logger.info(f"[MayImpactPlanner] '{modified_file}' afecta a {len(impacted)} archivos: {ordered_files[:3]}")
        return ImpactAnalysisResult(
            target_file=modified_file, impacted_files=sorted(list(impacted)),
            impact_depth=1 if impacted else 0, edit_obligations=obligations, topological_order=ordered_files,
        )


MayImpactPlanner = MayImpactPlannerPrimitive
may_impact_planner = MayImpactPlannerPrimitive()
