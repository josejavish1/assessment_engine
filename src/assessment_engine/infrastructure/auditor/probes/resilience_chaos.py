"""
Audit resilience, fault tolerance, and chaos reliability patterns. Features:
- Detect network calls lacking finite timeouts in the AST.
- Recognize timeouts in context managers (httpx.AsyncClient(timeout=...) and httpx.Client(timeout=...)).
- Audit resilience patterns: Circuit Breaker, Exponential Backoff with Jitter, and Dead-Letter Queue (DLQ).
- Verify graceful shutdown handling for SIGTERM/SIGINT signals.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive"
}

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "request"}


class ResilienceASTVisitor(ast.NodeVisitor):
    """Inspect the AST for network calls lacking finite timeouts."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self.network_calls_count = 0
        self.bounded_client_vars: set[str] = {"http_client"}

    def _check_with_context(self, items: list[ast.withitem]) -> None:
        for item in items:
            if isinstance(item.context_expr, ast.Call):
                func = item.context_expr.func
                is_client_init = False
                if isinstance(func, ast.Attribute) and func.attr in ("Client", "AsyncClient"):
                    is_client_init = True
                elif isinstance(func, ast.Name) and func.id in ("Client", "AsyncClient", "Session"):
                    is_client_init = True

                if is_client_init and item.optional_vars:
                    var_name = getattr(item.optional_vars, "id", None)
                    if var_name:
                        has_timeout = any(kw.arg == "timeout" for kw in item.context_expr.keywords)
                        if has_timeout:
                            self.bounded_client_vars.add(var_name.lower())

    def visit_With(self, node: ast.With) -> None:
        """Visit an ast.With node."""
        self._check_with_context(node.items)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """Visit an ast.AsyncWith node."""
        self._check_with_context(node.items)
        self.generic_visit(node)

    def _get_caller_and_attr(self, node: ast.Call) -> tuple[str, str]:
        func_attr = ""
        caller_name = ""
        if isinstance(node.func, ast.Attribute):
            func_attr = node.func.attr.lower()
            if isinstance(node.func.value, ast.Name):
                caller_name = node.func.value.id.lower()
            elif isinstance(node.func.value, ast.Attribute):
                caller_name = node.func.value.attr.lower()
        elif isinstance(node.func, ast.Name):
            func_attr = node.func.id.lower()
        return caller_name, func_attr

    def _is_excluded_call(self, func_attr: str, caller_name: str, args_len: int) -> bool:
        if func_attr in ("get", "pop") and caller_name.endswith(("_data", "_dict", "_info", "_map", "_params", "_meta", "record")):
            return True
        if func_attr == "request" and caller_name == "requests" and args_len == 0:
            return True
        return False

    def _is_network_http_call(self, func_attr: str, caller_name: str, args_len: int) -> bool:
        if func_attr == "urlopen" and caller_name in ("urllib", "request", ""):
            return True
        if func_attr in HTTP_METHODS:
            if caller_name in ("requests", "httpx", "aiohttp"):
                return True
            if caller_name in self.bounded_client_vars or caller_name.endswith(("_client", "client")):
                return args_len > 0 and not caller_name.startswith("test")
        return False

    def _audit_timeout_argument(self, node: ast.Call, caller_name: str, func_attr: str) -> None:
        has_timeout = any(kw.arg == "timeout" for kw in node.keywords) or (caller_name in self.bounded_client_vars)

        if not has_timeout:
            self.findings.append(AuditFinding(
                category="RESILIENCE",
                severity="CRITICAL",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="RESIL-UNBOUNDED-TIMEOUT",
                message=f"HTTP call '{caller_name}.{func_attr}()' without 'timeout' parameter: thread exhaustion risk (Metastable failure)",
                recommendation="Always configure a finite timeout (e.g. 'timeout=10.0') on external network calls."
            ))
            return

        for kw in node.keywords:
            if kw.arg == "timeout" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, (int, float)):
                if kw.value.value > 30.0:
                    self.findings.append(AuditFinding(
                        category="RESILIENCE",
                        severity="MEDIUM",
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        rule_id="RESIL-EXCESSIVE-TIMEOUT",
                        message=f"Timeout {kw.value.value}s in '{caller_name}.{func_attr}()' exceeds recommended threshold (<= 30s)",
                        recommendation="Reduce timeout to <= 10.0s or offload to asynchronous background worker."
                    ))

    def visit_Call(self, node: ast.Call) -> None:
        """Visit an ast.Call node."""
        caller_name, func_attr = self._get_caller_and_attr(node)
        if not self._is_excluded_call(func_attr, caller_name, len(node.args)):
            if self._is_network_http_call(func_attr, caller_name, len(node.args)):
                self.network_calls_count += 1
                self._audit_timeout_argument(node, caller_name, func_attr)
        self.generic_visit(node)


def _scan_code_resilience_patterns(content: str) -> tuple[bool, bool, bool, bool]:
    lower_content = content.lower()
    has_cb = "circuit_breaker" in lower_content or "circuitbreaker" in lower_content
    has_eb = "exponential_backoff" in lower_content or "tenacity" in lower_content or "jitter" in lower_content
    has_dlq = "dead_letter_queue" in lower_content or "dlq" in lower_content
    has_gs = "graceful_shutdown" in lower_content or "sigterm" in lower_content
    return has_cb, has_eb, has_dlq, has_gs


def run_resilience_chaos_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive audit of fault tolerance, unbounded timeouts, and resilience patterns."""
    findings: list[AuditFinding] = []
    total_network_calls = 0
    unbounded_timeouts_count = 0

    has_circuit_breaker = False
    has_exponential_backoff = False
    has_dead_letter_queue = False
    has_graceful_shutdown = False

    for py_file in find_target_files(target_dir, (".py",)):
        rel_path = str(py_file.relative_to(target_dir))
        is_test = "test" in py_file.name or "tests" in py_file.parts

        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        cb, eb, dlq, gs = _scan_code_resilience_patterns(content)
        has_circuit_breaker = has_circuit_breaker or cb
        has_exponential_backoff = has_exponential_backoff or eb
        has_dead_letter_queue = has_dead_letter_queue or dlq
        has_graceful_shutdown = has_graceful_shutdown or gs

        if not is_test and "core/auditor" not in rel_path:
            try:
                tree = ast.parse(content)
                visitor = ResilienceASTVisitor(rel_path)
                visitor.visit(tree)
                total_network_calls += visitor.network_calls_count
                findings.extend(visitor.findings)
                unbounded_timeouts_count += sum(1 for f in visitor.findings if f.rule_id == "RESIL-UNBOUNDED-TIMEOUT")
            except SyntaxError:
                continue

    score = 100.0
    score -= unbounded_timeouts_count * 25.0
    if not has_circuit_breaker and total_network_calls > 5:
        score -= 10.0
    if not has_exponential_backoff and total_network_calls > 5:
        score -= 10.0

    score = max(0.0, min(100.0, round(score, 1)))
    passed = unbounded_timeouts_count == 0 and score >= 75.0

    return ProbeResult(
        probe_name="Resilience, Timeouts & Chaos (Netflix / SRE)",
        score_pct=score,
        passed=passed,
        metrics={
            "network_calls_audited": total_network_calls,
            "unbounded_timeouts_count": unbounded_timeouts_count,
            "has_circuit_breaker": has_circuit_breaker,
            "has_exponential_backoff": has_exponential_backoff,
            "has_dead_letter_queue": has_dead_letter_queue,
            "has_graceful_shutdown": has_graceful_shutdown
        },
        findings=findings
    )
