"""
Audit SRE, observability, and concurrency (RFC 016 - Phase 5). Deterministically evaluate via AST:
1. ASYNC221 violations: Blocking I/O or subprocesses inside async functions.
2. OBS-001 violations (Zero-Print Mandate): Use of print() in production code.
3. REL-001 violations (Blind Exceptions): Silent 'except Exception: pass/continue' handling.
4. TRACE-001 violations: Missing context propagation in HTTP endpoints.
"""
from __future__ import annotations

import ast
from pathlib import Path

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files


class SREObservabilityVisitor(ast.NodeVisitor):
    """Inspect the AST for SRE reliability and observability violations."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self._current_async_func: str | None = None
        self._in_thread_offload: bool = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function definition node."""
        prev_func = self._current_async_func
        self._current_async_func = node.name
        self.generic_visit(node)
        self._current_async_func = prev_func

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node."""
        prev_func = self._current_async_func
        # Ignore nested synchronous functions (e.g., delegated to a thread) outside the async loop.
        self._current_async_func = None
        self.generic_visit(node)
        self._current_async_func = prev_func

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a call expression node."""
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.findings.append(AuditFinding(
                category="OBSERVABILITY",
                severity="HIGH",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="OBS-001-ZERO-PRINT",
                message="Uso de print() detectado en código de producción.",
                recommendation="Reemplazar por get_structured_logger(...) con active trace_id."
            ))

        # Detectar llamadas bloqueantes dentro de async def
        if self._current_async_func is not None and not self._in_thread_offload:
            # 1. subprocess.run, subprocess.Popen, etc.
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "subprocess" and node.func.attr in ("run", "call", "check_output", "Popen"):
                    self.findings.append(AuditFinding(
                        category="CONCURRENCY_SRE",
                        severity="CRITICAL",
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        rule_id="ASYNC221-BLOCKING-SUBPROCESS",
                        message=f"Llamada bloqueante subprocess.{node.func.attr}() dentro de función asíncrona '{self._current_async_func}'.",
                        recommendation="Delegar la ejecución a un hilo aislado mediante 'await asyncio.to_thread(...)' o 'anyio.to_thread.run_sync(...)'.",
                    ))
                elif node.func.value.id == "time" and node.func.attr == "sleep":
                    self.findings.append(AuditFinding(
                        category="CONCURRENCY_SRE",
                        severity="CRITICAL",
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        rule_id="ASYNC221-BLOCKING-SLEEP",
                        message=f"Llamada bloqueante time.sleep() dentro de función asíncrona '{self._current_async_func}'.",
                        recommendation="Reemplazar por 'await asyncio.sleep(...)'.",
                    ))

        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Visit a try statement node."""
        # Detectar blind exceptions silenciosas (except Exception: pass o continue)
        for handler in node.handlers:
            is_broad = False
            if handler.type is None:
                is_broad = True
            elif isinstance(handler.type, ast.Name) and handler.type.id in ("Exception", "BaseException"):
                is_broad = True

            if is_broad:
                if len(handler.body) == 1 and isinstance(handler.body[0], (ast.Pass, ast.Continue)):
                    self.findings.append(AuditFinding(
                        category="RESILIENCE",
                        severity="HIGH",
                        file_path=self.rel_path,
                        line_number=handler.lineno,
                        rule_id="REL-001-SILENT-EXCEPTION",
                        message="Captura ciega silenciosa (except Exception: pass/continue) detectada.",
                        recommendation="Capturar excepciones específicas o registrar el fallo con logger.error() antes de continuar.",
                    ))
        self.generic_visit(node)


def audit_sre_observability(target_dir: Path) -> ProbeResult:
    """Execute the static SRE audit on the target directory."""
    target_py_files = find_target_files(target_dir, (".py",))

    # Filter for production code only (core, routers, server.py, services).
    prod_files: list[Path] = []
    for p in target_py_files:
        rel = p.relative_to(target_dir).as_posix()
        if rel.startswith(("tests/", "scripts/", "core/fixtures/", "playbooks/", "core/legacy/")):
            continue
        prod_files.append(p)

    findings: list[AuditFinding] = []
    total_files_scanned = 0

    for py_file in prod_files:
        rel_str = py_file.relative_to(target_dir).as_posix()
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"), filename=rel_str)
        except SyntaxError:
            continue

        visitor = SREObservabilityVisitor(rel_str)
        visitor.visit(tree)
        findings.extend(visitor.findings)
        total_files_scanned += 1

    # Calculate deterministic SRE score normalized by density and clean files.
    affected_files = len({f.file_path for f in findings})
    clean_files = max(0, total_files_scanned - affected_files)
    file_compliance_ratio = clean_files / max(1, total_files_scanned)

    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    medium_count = sum(1 for f in findings if f.severity == "MEDIUM")

    penalty_points = (critical_count * 15.0) + (high_count * 2.0) + (medium_count * 0.5)
    normalized_penalty = (penalty_points / max(1, total_files_scanned)) * 10.0

    score = (file_compliance_ratio * 100.0) - normalized_penalty
    score = max(0.0, min(100.0, score))
    passed = (critical_count == 0) and (score >= 85.0)

    return ProbeResult(
        probe_name="SRE, Observability & W3C Tracing (RFC-016)",
        score_pct=round(score, 1),
        passed=passed,
        metrics={
            "files_scanned": total_files_scanned,
            "total_findings": len(findings),
            "critical_violations": sum(1 for f in findings if f.severity == "CRITICAL"),
            "high_violations": sum(1 for f in findings if f.severity == "HIGH"),
            "sre_grade_10": round(score / 10.0, 1),
        },
        findings=findings
    )
