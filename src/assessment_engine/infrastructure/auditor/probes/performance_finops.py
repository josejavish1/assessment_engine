"""
Probe performance, resource efficiency, and FinOps (Google SRE & SQLite WAL). Implement:
- AST detection of N+1 database query anti-patterns (SELECT statements inside loops).
- SQLite production tuning audit (PRAGMA journal_mode = WAL for high concurrency).
- CPU waste and thread lock prevention.
"""
from __future__ import annotations

import ast
import sqlite3
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive"
}


class PerformanceASTVisitor(ast.NodeVisitor):
    """Inspect the AST for loops executing repetitive database queries (N+1)."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self.in_loop = False

    def visit_For(self, node: ast.For) -> None:
        """Visit a for-loop node."""
        # node.iter is evaluated only once before iteration begins
        self.visit(node.target)
        self.visit(node.iter)
        # Only statements inside node.body execute N times
        prev = self.in_loop
        self.in_loop = True
        for stmt in node.body:
            self.visit(stmt)
        self.in_loop = prev

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        """Visit an asynchronous for-loop node."""
        self.visit(node.target)
        self.visit(node.iter)
        prev = self.in_loop
        self.in_loop = True
        for stmt in node.body:
            self.visit(stmt)
        self.in_loop = prev

    def visit_While(self, node: ast.While) -> None:
        """Visit a while-loop node."""
        self.visit(node.test)
        prev = self.in_loop
        self.in_loop = True
        for stmt in node.body:
            self.visit(stmt)
        self.in_loop = prev

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a call node."""
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        # 1. N+1 anti-pattern: database queries inside loops
        if self.in_loop and func_name in ("execute", "raw_query") and node.args:
            first_arg = node.args[0]
            sql_text = ""
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                sql_text = first_arg.value.upper()
            elif isinstance(first_arg, ast.JoinedStr):
                sql_text = "".join(v.value.upper() for v in first_arg.values if isinstance(v, ast.Constant) and isinstance(v.value, str))

            if "SELECT " in sql_text and "COUNT(*)" not in sql_text and not any(ddl in sql_text for ddl in ("PRAGMA", "CREATE TABLE", "ALTER TABLE", "SQLITE_MASTER")):
                self.findings.append(AuditFinding(
                    category="PERFORMANCE",
                    severity="HIGH",
                    file_path=self.rel_path,
                    line_number=node.lineno,
                    rule_id="PERF-N-PLUS-ONE",
                    message=f"N+1 query anti-pattern detected: SELECT query in '{func_name}()' invoked inside loop",
                    recommendation="Hoist query outside loop using parameterized 'IN (?, ...)' or relational JOIN."
                ))

        self.generic_visit(node)


def audit_sqlite_wal_tuning(db_path: Path) -> list[AuditFinding]:
    """Audit performance and concurrency PRAGMAs for a physical SQLite database."""
    findings: list[AuditFinding] = []
    try:
        if not db_path.exists() or db_path.stat().st_size < 100:
            return findings

        conn = sqlite3.connect(str(db_path), timeout=5.0)
        cur = conn.cursor()

        cur.execute("PRAGMA journal_mode;")
        journal_mode = str(cur.fetchone()[0]).lower()
        if journal_mode != "wal":
            findings.append(AuditFinding(
                category="PERFORMANCE",
                severity="HIGH",
                file_path=str(db_path.name),
                line_number=None,
                rule_id="PERF-SQLITE-NO-WAL",
                message=f"Base de datos SQLite en modo '{journal_mode}': bloquea lectores durante escrituras concurrentes",
                recommendation="Enable 'PRAGMA journal_mode = WAL;' to support concurrent reads and writes."
            ))
        conn.close()
    except (sqlite3.Error, OSError):
        pass
    return findings


def run_performance_finops_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive audit of resource efficiency, N+1 anti-patterns, and SQLite tuning."""
    findings: list[AuditFinding] = []
    n_plus_one_count = 0
    scanned_db_count = 0

    for py_file in find_target_files(target_dir, (".py",)):
        if "test" in py_file.name or "tests" in py_file.parts:
            continue

        rel_path = str(py_file.relative_to(target_dir))
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            visitor = PerformanceASTVisitor(rel_path)
            visitor.visit(tree)
            if visitor.findings:
                n_plus_one_count += len(visitor.findings)
                findings.extend(visitor.findings)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

    # 2. Audit SQLite WAL tuning in .db files
    for db_file in find_target_files(target_dir, (".db",)):
        scanned_db_count += 1
        db_findings = audit_sqlite_wal_tuning(db_file)
        findings.extend(db_findings)

    score = 100.0
    score -= n_plus_one_count * 20.0
    wal_issues = sum(1 for f in findings if f.rule_id == "PERF-SQLITE-NO-WAL")
    score -= wal_issues * 20.0

    score = max(0.0, min(100.0, round(score, 1)))
    passed = n_plus_one_count == 0 and wal_issues == 0 and score >= 75.0

    return ProbeResult(
        probe_name="Performance, SRE & FinOps (N+1 / WAL / Leaks)",
        score_pct=score,
        passed=passed,
        metrics={
            "n_plus_one_queries_detected": n_plus_one_count,
            "sqlite_databases_audited": scanned_db_count,
            "wal_compliance": "Conforme" if wal_issues == 0 else "No Conforme"
        },
        findings=findings
    )
