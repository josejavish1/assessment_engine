#!/usr/bin/env python3
"""Audit codebase quality against international standards:

1. ISO/IEC 25010 (SQuaRE Product Quality & Testability Ratio).
2. McCabe Cyclomatic Complexity V(G) (IEEE Standard 29119).
3. SEI Maintainability Index (MI) (Carnegie Mellon / IEEE).
4. Google Python Style Guide Docstrings Coverage (PEP 257).
5. PEP 561 Strict Type-Safety Ratio.
6. MITRE CWE-561 Dead Code & Unreferenced Symbols.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import asdict, dataclass, field
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Generator

REPO_ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "working",
    "node_modules",
    "infrastructure/docker",
    ".hypothesis",
}


@dataclass
class FunctionQuality:
    file: str
    name: str
    line: int
    complexity: int  # McCabe V(G)
    is_typed: bool
    has_docstring: bool
    args_count: int
    classification: str  # "A" (1-5), "B" (6-10), "C" (11-20), "D" (>20)


@dataclass
class ModuleQuality:
    file: str
    sloc: int
    functions_count: int
    classes_count: int
    avg_complexity: float
    max_complexity: int
    maintainability_index: float
    docstring_coverage_pct: float
    type_coverage_pct: float
    complex_functions: list[str] = field(default_factory=list)


class QualityStandardsAuditor:
    """Comprehensive auditor for international software engineering standards."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.functions: list[FunctionQuality] = []
        self.modules: dict[str, ModuleQuality] = {}
        self.all_symbols_defined: dict[str, list[str]] = defaultdict(list)
        self.all_symbols_referenced: set[str] = set()
        self.test_sloc = 0
        self.prod_sloc = 0

    def compute_mccabe_complexity(self, node: ast.AST) -> int:
        """Calculate McCabe's Cyclomatic Complexity: V(G) = 1 + decision points.

        Decision points: if, while, for, async for, except, and, or, ifexp.
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.IfExp):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def compute_halstead_volume(self, code: str) -> float:
        """Deterministically approximate Halstead Volume from lexical tokens."""
        tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b|[+\-*/%=<>!&|^~]+", code)
        if not tokens:
            return 1.0
        n_total = len(tokens)
        n_unique = len(set(tokens))
        vocabulary = max(2, n_unique)
        return float(n_total * math.log2(vocabulary))

    def compute_maintainability_index(
        self, halstead_vol: float, cyclomatic: int, sloc: int
    ) -> float:
        """SEI formula: MI = max(0, (171 - 5.2*ln(V) - 0.23*G - 16.2*ln(L)) * 100 / 171)."""
        if sloc <= 0:
            return 100.0
        v = max(1.0, halstead_vol)
        g = max(1, cyclomatic)
        l = max(1, sloc)
        raw_mi = 171.0 - 5.2 * math.log(v) - 0.23 * g - 16.2 * math.log(l)
        normalized = max(0.0, (raw_mi * 100.0) / 171.0)
        return round(min(100.0, normalized), 1)

    def _iter_python_files(self) -> Generator[tuple[Path, str, bool], None, None]:
        """Recursively iterate over Python files, skipping excluded directories."""
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if not file.endswith(".py"):
                    continue
                py_path = Path(root) / file
                rel_parts = py_path.relative_to(self.root_dir).parts
                if any(ex in rel_parts for ex in EXCLUDE_DIRS):
                    continue

                rel_str = str(py_path.relative_to(self.root_dir))
                is_test = rel_str.startswith("tests/") or "test_" in rel_str
                yield py_path, rel_str, is_test

    def audit_codebase(self) -> None:
        """Audit repository production and test code."""
        for py_path, rel_str, is_test in self._iter_python_files():
            try:
                code = py_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code)
            except Exception:
                continue

            lines = code.splitlines()
            sloc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

            if is_test:
                self.test_sloc += sloc
            else:
                self.prod_sloc += sloc

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    self.all_symbols_referenced.add(node.id)
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    self.all_symbols_referenced.add(node.attr)

            if not is_test:
                self._audit_module_quality(rel_str, code, tree, sloc)

    def _audit_function_node(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        rel_path: str,
        complex_fns: list[str],
    ) -> tuple[bool, bool, int]:
        """Audit typing, docstring coverage, and cyclomatic complexity for an individual function."""
        is_decorated = len(node.decorator_list) > 0
        is_visitor_hook = node.name.startswith("visit_")
        if (
            not node.name.startswith("_")
            and not is_decorated
            and not is_visitor_hook
            and node.name != "main"
        ):
            self.all_symbols_defined[node.name].append(rel_path)

        has_doc = ast.get_docstring(node) is not None
        args = [a for a in node.args.args if a.arg != "self"]
        has_typed_args = all(a.annotation is not None for a in args) if args else True
        has_typed_ret = node.returns is not None
        is_typed = has_typed_args and has_typed_ret

        complexity = self.compute_mccabe_complexity(node)
        classification = "A"
        if complexity > 20:
            classification = "D"
            complex_fns.append(f"{node.name} (V(G)={complexity})")
        elif complexity > 10:
            classification = "C"
            complex_fns.append(f"{node.name} (V(G)={complexity})")
        elif complexity > 5:
            classification = "B"

        self.functions.append(
            FunctionQuality(
                file=rel_path,
                name=node.name,
                line=node.lineno,
                complexity=complexity,
                is_typed=is_typed,
                has_docstring=has_doc,
                args_count=len(args),
                classification=classification,
            )
        )
        return has_doc, is_typed, complexity

    def _audit_module_quality(
        self, rel_path: str, code: str, tree: ast.AST, sloc: int
    ) -> None:
        fn_count = 0
        cls_count = 0
        typed_count = 0
        docstring_count = 0
        complexities: list[int] = []
        complex_fns: list[str] = []

        if ast.get_docstring(tree) is not None:
            docstring_count += 1

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_count += 1
                self.all_symbols_defined[node.name].append(rel_path)
                if ast.get_docstring(node):
                    docstring_count += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_count += 1
                has_doc, is_typed, comp = self._audit_function_node(
                    node, rel_path, complex_fns
                )
                if has_doc:
                    docstring_count += 1
                if is_typed:
                    typed_count += 1
                complexities.append(comp)

        total_documentable = 1 + cls_count + fn_count
        doc_pct = round((docstring_count / max(1, total_documentable)) * 100, 1)
        type_pct = round((typed_count / max(1, fn_count)) * 100, 1) if fn_count > 0 else 100.0

        avg_comp = round(sum(complexities) / max(1, len(complexities)), 1)
        max_comp = max(complexities, default=1)

        halstead_vol = self.compute_halstead_volume(code)
        mi = self.compute_maintainability_index(halstead_vol, max_comp, sloc)

        self.modules[rel_path] = ModuleQuality(
            file=rel_path,
            sloc=sloc,
            functions_count=fn_count,
            classes_count=cls_count,
            avg_complexity=avg_comp,
            max_complexity=max_comp,
            maintainability_index=mi,
            docstring_coverage_pct=doc_pct,
            type_coverage_pct=type_pct,
            complex_functions=complex_fns,
        )

    def generate_report(self) -> dict[str, Any]:
        self.audit_codebase()

        rank_a = sum(1 for f in self.functions if f.classification == "A")
        rank_b = sum(1 for f in self.functions if f.classification == "B")
        rank_c = sum(1 for f in self.functions if f.classification == "C")
        rank_d = sum(1 for f in self.functions if f.classification == "D")
        total_fns = max(1, len(self.functions))

        avg_mi = round(
            sum(m.maintainability_index for m in self.modules.values())
            / max(1, len(self.modules)),
            1,
        )
        avg_doc = round(
            sum(m.docstring_coverage_pct for m in self.modules.values())
            / max(1, len(self.modules)),
            1,
        )
        avg_type = round(
            sum(m.type_coverage_pct for m in self.modules.values())
            / max(1, len(self.modules)),
            1,
        )

        test_ratio = round(self.test_sloc / max(1, self.prod_sloc), 2)

        unreferenced = [
            {"symbol": sym, "defined_in": defs}
            for sym, defs in self.all_symbols_defined.items()
            if sym not in self.all_symbols_referenced
            and not sym.startswith("test_")
            and not any(
                d.startswith("src/assessment_engine/domain/schemas/")
                or d.startswith("scripts/")
                or d.startswith("templates/")
                for d in defs
            )
        ]

        top_complex = sorted(self.functions, key=lambda f: f.complexity, reverse=True)[:10]

        return {
            "summary": {
                "total_production_modules": len(self.modules),
                "total_production_sloc": self.prod_sloc,
                "total_test_sloc": self.test_sloc,
                "testability_ratio_iso25010": test_ratio,
                "global_maintainability_index": avg_mi,
                "global_docstring_coverage_pct": avg_doc,
                "global_strict_type_safety_pct": avg_type,
                "mccabe_distribution": {
                    "rank_A_simple_1_5": f"{rank_a} ({round(rank_a/total_fns*100, 1)}%)",
                    "rank_B_moderate_6_10": f"{rank_b} ({round(rank_b/total_fns*100, 1)}%)",
                    "rank_C_complex_11_20": f"{rank_c} ({round(rank_c/total_fns*100, 1)}%)",
                    "rank_D_risk_over_20": f"{rank_d} ({round(rank_d/total_fns*100, 1)}%)",
                },
                "cwe_561_unreferenced_symbols_count": len(unreferenced),
            },
            "top_10_complex_functions": [asdict(f) for f in top_complex],
            "modules_audit": {
                k: asdict(v)
                for k, v in sorted(
                    self.modules.items(), key=lambda x: x[1].maintainability_index
                )
            },
            "cwe_561_unreferenced_symbols_sample": unreferenced[:15],
        }


def main() -> None:
    auditor = QualityStandardsAuditor(REPO_ROOT)
    report = auditor.generate_report()

    out_file = REPO_ROOT / "docs" / "audits" / "STANDARDS_QUALITY_REPORT.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    s = report["summary"]
    print("\n" + "=" * 78)
    print("FORMAL CODE QUALITY & INTERNATIONAL STANDARDS REPORT")
    print("Standards: ISO/IEC 25010 | McCabe IEEE 29119 | SEI MI | Google PEP 257 | CWE-561")
    print("=" * 78)
    print(f"Production SLOC:                     {s['total_production_sloc']:,}")
    print(f"Test SLOC:                           {s['total_test_sloc']:,}")
    print(
        f"Test-to-Code Ratio (ISO 25010):      {s['testability_ratio_iso25010']} "
        f"(Tier-1 Target: >0.50) -> {'PASS' if s['testability_ratio_iso25010'] >= 0.5 else 'WARN'}"
    )
    print(
        f"Maintainability Index (SEI MI):      {s['global_maintainability_index']}/100 -> "
        f"{'HIGH MAINTAINABILITY' if s['global_maintainability_index'] >= 80 else 'MODERATE'}"
    )
    print(f"Docstring Coverage (PEP 257):        {s['global_docstring_coverage_pct']}%")
    print(f"Strict Type-Safety (PEP 561):        {s['global_strict_type_safety_pct']}%")
    print("-" * 78)
    print("MCCABE CYCLOMATIC COMPLEXITY DISTRIBUTION (V(G)):")
    m = s["mccabe_distribution"]
    print(f"  Rank A (Simple 1-5):                {m['rank_A_simple_1_5']}")
    print(f"  Rank B (Moderate 6-10):             {m['rank_B_moderate_6_10']}")
    print(f"  Rank C (Complex 11-20):             {m['rank_C_complex_11_20']}")
    print(f"  Rank D (High Risk >20):             {m['rank_D_risk_over_20']}")
    print("-" * 78)
    print(f"CWE-561 Unreferenced Symbols:        {s['cwe_561_unreferenced_symbols_count']}")
    print(f"Report exported to:                  {out_file.relative_to(REPO_ROOT)}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
