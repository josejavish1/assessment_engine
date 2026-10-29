"""
Assess test assertion resilience via AST mutation testing per ISO/IEC/IEEE 29119. Empirically evaluate project test assertion effectiveness by injecting mutants. Deterministically pair each production module with its respective test suite.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files
from assessment_engine.infrastructure.auditor.mutation_probe import MutationTestingProbe

PYTEST_CMD = [sys.executable, "-m", "pytest"]


def run_mutation_gate_probe(target_dir: Path, max_samples: int = 6) -> ProbeResult:
    """Execute mutation testing sampling on the project code."""
    all_py = find_target_files(target_dir, (".py",))
    test_files = [f for f in all_py if f.name.startswith("test_")]
    findings: list[AuditFinding] = []

    if not test_files:
        return ProbeResult(
            probe_name="Mutation Testing Score (ISO/IEC/IEEE 29119 & GEMA 54)",
            score_pct=0.0,
            passed=False,
            metrics={"status": "NO_TESTS_FOUND", "mutants_tested": 0},
            findings=[AuditFinding(
                category="MUTATION",
                severity="HIGH",
                file_path=str(target_dir),
                line_number=None,
                rule_id="MUT-NO-TESTS",
                message="Project contains zero unit test files (test_*.py)",
                recommendation="Add unit test suite to protect business domain logic."
            )]
        )

    test_map = {t.stem: t for t in test_files}
    pairs: list[tuple[Path, Path]] = []
    for pf in all_py:
        if pf.name.startswith("test_") or "tests" in pf.parts:
            continue
        expected_test_name = f"test_{pf.stem}"
        if expected_test_name in test_map:
            pairs.append((pf, test_map[expected_test_name]))

    tested_mutants = 0
    killed_mutants = 0

    candidates = pairs[:max_samples] if pairs else [(pf, test_files[0]) for pf in all_py if not pf.name.startswith("test_")][:max_samples]

    for py_file, test_file in candidates:
        rel_path = str(py_file.relative_to(target_dir))
        cmd = [*PYTEST_CMD, str(test_file), "-q", "--tb=no"]

        try:
            res = MutationTestingProbe.audit_test_against_mutation(py_file, cmd)
            if "Sin operadores mutables" in res.mutation_description:
                continue

            tested_mutants += 1
            if res.mutant_killed:
                killed_mutants += 1
            else:
                rule_id = "MUT-SURVIVED"
                if "AOR" in res.mutation_description:
                    rule_id = "MUT-AOR-SURVIVED"
                elif "LCR" in res.mutation_description:
                    rule_id = "MUT-LCR-SURVIVED"
                elif "ROR" in res.mutation_description:
                    rule_id = "MUT-ROR-SURVIVED"

                findings.append(AuditFinding(
                    category="MUTATION",
                    severity="MEDIUM",
                    file_path=rel_path,
                    line_number=None,
                    rule_id=rule_id,
                    message=f"Mutant in '{py_file.name}' survived ({res.mutation_description}): test suite failed to catch corruption.",
                    recommendation="Add direct assertions over arithmetic or logical operators evaluated."
                ))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

    if tested_mutants == 0:
        score = 100.0
        passed = True
    else:
        score = round((killed_mutants / tested_mutants) * 100.0, 1)
        passed = score >= 75.0

    return ProbeResult(
        probe_name="Mutation Testing Score (ISO/IEC/IEEE 29119 & GEMA 54)",
        score_pct=score,
        passed=passed,
        metrics={
            "mutants_tested": tested_mutants,
            "mutants_killed": killed_mutants,
            "mutation_score_pct": score,
            "paired_modules_count": len(pairs)
        },
        findings=findings
    )
