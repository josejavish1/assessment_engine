"""
Localize faults using Spectrum-Based Fault Localization (SBFL) with the Ochiai algorithm. Calculate the correlation between passing and failing test execution traces to isolate suspicious lines. Ochiai formula: Suspicion(s) = e_f / sqrt(total_failed * (e_f + e_p))
Where: - e_f: Failed tests that executed statement s. - e_p: Passing tests that executed statement s. - total_failed: Total number of failed tests in the suite.
"""
from __future__ import annotations


import json
import logging
import math
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.evolution.fault_localizer")


@dataclass(frozen=True)
class SuspiciousLine:
    """Represent a code statement scored with the Ochiai suspicion coefficient."""
    lineno: int
    score: float
    failed_executed: int
    passed_executed: int
    code_snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance into a dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class FaultLocalizationReport:
    """Represent an SBFL diagnostic report."""
    target_file: str
    total_passed_tests: int
    total_failed_tests: int
    top_suspects: list[SuspiciousLine] = field(default_factory=list)
    most_likely_line: int | None = None
    most_likely_snippet: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the instance into a dictionary."""
        return {
            "target_file": self.target_file,
            "total_passed_tests": self.total_passed_tests,
            "total_failed_tests": self.total_failed_tests,
            "most_likely_line": self.most_likely_line,
            "most_likely_snippet": self.most_likely_snippet,
            "top_suspects": [s.to_dict() for s in self.top_suspects],
        }


def compute_ochiai_score(
    ef: int,
    total_failed: int,
    ep: int,
) -> float:
    """
    Calcula el coeficiente Ochiai:
        score = ef / sqrt(total_failed * (ef + ep))
    """
    if ef <= 0 or total_failed <= 0:
        return 0.0

    denominator = math.sqrt(total_failed * (ef + ep))
    if denominator == 0.0:
        return 0.0

    return round(ef / denominator, 4)


def compute_ochiai_ranking(
    passed_traces: dict[str, set[int]],
    failed_traces: dict[str, set[int]],
    source_lines: list[str] | None = None,
) -> list[SuspiciousLine]:
    """
    Build the execution hit matrix and rank all executed lines.
    """
    total_failed = len(failed_traces)

    if total_failed == 0:
        return []

    all_executed_lines: set[int] = set()
    for lines in passed_traces.values():
        all_executed_lines.update(lines)
    for lines in failed_traces.values():
        all_executed_lines.update(lines)

    ranked: list[SuspiciousLine] = []

    for lineno in sorted(all_executed_lines):
        # Count passing and failing tests for this line.
        ef = sum(1 for lines in failed_traces.values() if lineno in lines)
        ep = sum(1 for lines in passed_traces.values() if lineno in lines)

        score = compute_ochiai_score(ef=ef, total_failed=total_failed, ep=ep)

        snippet = ""
        if source_lines and 1 <= lineno <= len(source_lines):
            snippet = source_lines[lineno - 1].strip()

        ranked.append(
            SuspiciousLine(
                lineno=lineno,
                score=score,
                failed_executed=ef,
                passed_executed=ep,
                code_snippet=snippet,
            )
        )

    ranked.sort(key=lambda s: (-s.score, -s.failed_executed, s.passed_executed, s.lineno))
    return ranked


def _create_trace_hook_script(target_file_name: str, dump_json_path: Path) -> str:
    """Generate the pytest plugin script to capture the coverage matrix in a single run."""
    return f'''
import sys, json, os
from pathlib import Path
import pytest

TRACES = {{"passed": {{}}, "failed": {{}}}}
CURRENT_LINES = set()
TARGET_NAME = "{target_file_name}"

def _sbfl_tracer(frame, event, arg):
    if event == "line":
        fname = frame.f_code.co_filename
        if os.path.basename(fname) == TARGET_NAME:
            CURRENT_LINES.add(frame.f_lineno)
    return _sbfl_tracer

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    global CURRENT_LINES
    CURRENT_LINES = set()
    sys.settrace(_sbfl_tracer)
    try:
        yield
    finally:
        sys.settrace(None)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        bucket = "passed" if rep.passed else "failed"
        TRACES[bucket][item.nodeid] = list(CURRENT_LINES)

def pytest_sessionfinish(session, exitstatus):
    Path(r"{dump_json_path}").write_text(json.dumps(TRACES), encoding="utf-8")
'''


class FaultLocalizer:
    """
    Provide a Spectrum-Based Fault Localization (SBFL) harness using the Ochiai algorithm.
    """

    @staticmethod
    def compute_ranking(
        passed_traces: dict[str, set[int]],
        failed_traces: dict[str, set[int]],
        source_code: str | None = None,
    ) -> list[SuspiciousLine]:
        """Compute the ranking of elements based on the input data."""
        lines = source_code.splitlines() if source_code else None
        return compute_ochiai_ranking(passed_traces, failed_traces, lines)

    @staticmethod
    def localize_from_traces(
        target_file_path: str,
        passed_traces: dict[str, set[int]],
        failed_traces: dict[str, set[int]],
        source_code: str | None = None,
        top_k: int = 5,
    ) -> FaultLocalizationReport:
        """Localize target components or faults from execution traces."""
        lines = source_code.splitlines() if source_code else None
        ranking = compute_ochiai_ranking(passed_traces, failed_traces, lines)
        top = ranking[:top_k]

        most_likely_line = top[0].lineno if top and top[0].score > 0 else None
        most_likely_snippet = top[0].code_snippet if top and top[0].score > 0 else None

        return FaultLocalizationReport(
            target_file=target_file_path,
            total_passed_tests=len(passed_traces),
            total_failed_tests=len(failed_traces),
            top_suspects=top,
            most_likely_line=most_likely_line,
            most_likely_snippet=most_likely_snippet,
        )

    @staticmethod
    def localize_from_pytest(
        target_file: Path | str,
        test_file: Path | str,
        timeout_seconds: int = 20,
    ) -> FaultLocalizationReport:
        """Run pytest once by injecting the in-memory tracing hook.
Compute the complete Ochiai diagnosis in milliseconds."""
        target_p = Path(target_file).resolve()
        test_p = Path(test_file).resolve()

        if not target_p.exists():
            raise FileNotFoundError(f"Archivo objetivo no encontrado: {target_p}")
        if not test_p.exists():
            raise FileNotFoundError(f"Archivo de pruebas no encontrado: {test_p}")

        source_code = target_p.read_text(encoding="utf-8")
        dump_json = target_p.parent / f"_sbfl_trace_{target_p.stem}.json"
        plugin_file = target_p.parent / f"_sbfl_plugin_{target_p.stem}.py"

        plugin_code = _create_trace_hook_script(target_p.name, dump_json)
        plugin_file.write_text(plugin_code, encoding="utf-8")

        cmd = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            str(test_p),
            "-p",
            plugin_file.stem,
            "-q",
        ]

        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": f"{target_p.parent}:{os.environ.get('PYTHONPATH', '')}",
        }

        try:
            subprocess.run(
                cmd,
                cwd=str(target_p.parent),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                env=env,
            )

            if not dump_json.exists():
                logger.warning("[SBFL] Coverage trace dump was not generated.")
                return FaultLocalizationReport(
                    target_file=str(target_p),
                    total_passed_tests=0,
                    total_failed_tests=0,
                    top_suspects=[],
                )

            data = json.loads(dump_json.read_text(encoding="utf-8"))
            raw_passed = data.get("passed", {})
            raw_failed = data.get("failed", {})

            passed_traces = {k: set(v) for k, v in raw_passed.items()}
            failed_traces = {k: set(v) for k, v in raw_failed.items()}

            return FaultLocalizer.localize_from_traces(
                target_file_path=str(target_p),
                passed_traces=passed_traces,
                failed_traces=failed_traces,
                source_code=source_code,
            )
        finally:
            # Clean up ephemeral instrumentation artifacts immediately.
            if plugin_file.exists():
                plugin_file.unlink(missing_ok=True)
            if dump_json.exists():
                dump_json.unlink(missing_ok=True)


fault_localizer = FaultLocalizer()

__all__ = [
    "FaultLocalizationReport",
    "FaultLocalizer",
    "SuspiciousLine",
    "compute_ochiai_ranking",
    "compute_ochiai_score",
    "fault_localizer",
]
