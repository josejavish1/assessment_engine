"""
Audit probe for test assertion density and anti-complacency quality.
Evaluates strong assertions (exact equality, invariants, schema contracts) vs weak checks.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult


def run_assertion_quality_probe(target_dir: Path) -> ProbeResult:
    """Analyze test files to verify high assertion density and invariant strength."""
    test_dir = target_dir / "tests"
    if not test_dir.is_dir():
        return ProbeResult(
            probe_name="assertion_quality",
            score_pct=100.0,
            passed=True,
            metrics={"total_tests": 0, "strong_ratio_pct": 100.0},
        )

    test_files = sorted(test_dir.rglob("test_*.py"))
    weak_assertions = 0
    strong_assertions = 0
    total_tests = 0
    findings: list[AuditFinding] = []

    weak_markers = ("is not None", "> 0", "len(", "exists()")

    for tf in test_files:
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                total_tests += 1
                for child in ast.walk(node):
                    if isinstance(child, ast.Assert):
                        test_str = ast.unparse(child.test)
                        if any(w in test_str for w in weak_markers):
                            weak_assertions += 1
                        else:
                            strong_assertions += 1

    total_assertions = strong_assertions + weak_assertions
    if total_assertions == 0:
        ratio = 100.0
    else:
        ratio = round((strong_assertions / total_assertions) * 100.0, 1)

    passed = ratio >= 80.0
    if not passed:
        findings.append(
            AuditFinding(
                category="TEST_QUALITY",
                severity="HIGH",
                file_path=str(test_dir),
                line_number=None,
                rule_id="ASSERT-WEAK-COMPLACENCY",
                message=f"Strong assertion ratio ({ratio}%) below Tier-1 threshold (80.0%).",
                recommendation="Replace loose existence checks ('len > 0', 'is not None') with domain invariants.",
            )
        )

    return ProbeResult(
        probe_name="assertion_quality",
        score_pct=ratio,
        passed=passed,
        metrics={
            "total_tests": total_tests,
            "total_assertions": total_assertions,
            "strong_assertions": strong_assertions,
            "weak_assertions": weak_assertions,
            "strong_ratio_pct": ratio,
        },
        findings=findings,
    )
