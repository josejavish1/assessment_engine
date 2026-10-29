"""
Provide static application security testing (SAST) and secret scanning. Implement AST taint tracking for SQL and system command sinks (CWE-89, CWE-78, CWE-94). Use Shannon entropy analysis to detect hardcoded credentials (CWE-798). Distinguish safe parameterized SQLite DDL and PRAGMA patterns from SQL injections.
"""
from __future__ import annotations

import ast
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive"
}

SECRET_KNOWN_PATTERNS = [
    (re.compile(r"sk_live_[0-9a-zA-Z]{24,}"), "Stripe Live Secret Key", "CRITICAL"),
    (re.compile(r"ghp_[0-9a-zA-Z]{36}"), "GitHub Personal Access Token", "CRITICAL"),
    (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "Google Cloud API Key", "HIGH"),
    (re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"), "Cryptographic Private Key", "CRITICAL"),
]

UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def calculate_shannon_entropy(text: str) -> float:
    """Calculate Shannon entropy in bits per character."""
    if not text:
        return 0.0
    length = len(text)
    counts = Counter(text)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def is_high_entropy_secret(token: str) -> bool:
    """Determine whether a string literal exhibits randomness consistent with private keys."""
    if len(token) < 20 or len(token) > 120:
        return False
    if " " in token or "\n" in token:
        return False
    if token.startswith(("/", "http://", "https://", "data:", "SELECT", "INSERT", "UPDATE", "DELETE", "PRAGMA")):
        return False
    # Secret tokens and private keys are strictly ASCII (Base64, Hex, Alphanumeric).
    # Natural prose in non-Latin scripts (e.g., CJK, Cyrillic) is not a secret key.
    if any(ord(char) > 127 for char in token):
        return False
    if "/" in token and any(token.endswith(ext) for ext in (".md", ".json", ".yaml", ".yml", ".py", ".html", ".css", ".js", ".ts", ".txt", ".sh", ".sql", ".xml", ".svg", ".png", ".jpg", ".lock")):
        return False
    if UUID_REGEX.match(token):
        return False
    if len(token) == 40 and all(c in "0123456789abcdef" for c in token):
        return False
    if "0123456789" in token:
        return False
    if token in ("TRWAGMYFPDXBNJZSQVHLCKE", "ABCDEFGHJNPQRSUVW", "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"):
        return False
    if any(c in token for c in ("\\", "(", ")", "[", "]", "^", "$", "*", "|", "<", ">", "{", "}", ";", "?")):
        return False

    entropy = calculate_shannon_entropy(token)
    is_hex = all(c in "0123456789abcdefABCDEF-_" for c in token)
    if is_hex and entropy >= 3.6:
        return True
    if entropy >= 4.4:
        return True
    return False


class ASTSecurityTaintVisitor(ast.NodeVisitor):
    """
    AST Taint Tracker: detects dangerous execution sinks (SQL sinks, eval, exec, subprocess).
    Discriminates parameterized queries with '?' and SQLite DDL commands.
    """

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []

    def _is_safe_parameterized_ddl_or_query(self, sql_node: ast.AST, has_params: bool) -> bool:
        if not isinstance(sql_node, ast.JoinedStr):
            return False

        static_text = "".join(
            val.value for val in sql_node.values
            if isinstance(val, ast.Constant) and isinstance(val.value, str)
        )
        upper_static = static_text.upper()

        if "PRAGMA " in upper_static:
            return True
        if any(ddl in upper_static for ddl in ("CREATE TABLE", "CREATE INDEX", "ALTER TABLE")):
            return True
        if "WHERE" not in upper_static and ('FROM "' in upper_static or "FROM [" in upper_static):
            return True

        if has_params:
            has_placeholder_builder = any(
                isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name) and
                v.value.id.lower() in ("placeholders", "sql_pred", "range_pred", "keyset_pred", "full_pred", "set_clause", "col_names_sql")
                for v in sql_node.values
            )
            if has_placeholder_builder:
                return True

            if "?" in static_text:
                has_quoted_where = any(
                    isinstance(val, ast.Constant) and isinstance(val.value, str) and
                    "WHERE" in val.value.upper() and (val.value.rstrip().endswith("'") or val.value.rstrip().endswith('"'))
                    for val in sql_node.values
                )
                if not has_quoted_where:
                    return True

        return False

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Visit a JoinedStr node."""
        static_parts = [val.value for val in node.values if isinstance(val, ast.Constant) and isinstance(val.value, str)]
        full_static = " ".join(static_parts).upper()

        if any(kw in full_static for kw in ("SELECT ", "INSERT INTO", "UPDATE ", "DELETE FROM")):
            has_placeholder_builder = any(
                isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name) and
                v.value.id.lower() in ("placeholders", "sql_pred", "range_pred", "keyset_pred", "full_pred", "set_clause", "col_names_sql")
                for v in node.values
            )
            if not has_placeholder_builder and "WHERE" in full_static and len(node.values) > 1 and "?" not in full_static:
                self.findings.append(AuditFinding(
                    category="SECURITY",
                    severity="CRITICAL",
                    file_path=self.rel_path,
                    line_number=node.lineno,
                    rule_id="CWE-89-SQLI-FSTRING",
                    message="SQL Injection (CWE-89): Dynamic SQL query constructed via f-string without parameterized '?'",
                    recommendation="Use parameterized SQL queries with '?' and parameter tuple."
                ))
        self.generic_visit(node)

    def _check_sql_sink(self, node: ast.Call, func_name: str) -> None:
        if func_name not in ("execute", "executemany", "executescript") or not node.args:
            return

        sql_arg = node.args[0]
        has_params = len(node.args) > 1 or any(kw.arg in ("parameters", "params") for kw in node.keywords)

        if isinstance(sql_arg, ast.JoinedStr):
            if not self._is_safe_parameterized_ddl_or_query(sql_arg, has_params):
                self.findings.append(AuditFinding(
                    category="SECURITY",
                    severity="CRITICAL",
                    file_path=self.rel_path,
                    line_number=node.lineno,
                    rule_id="CWE-89-SQLI-FSTRING",
                    message=f"SQL Injection (CWE-89): Query in '{func_name}' constructed with dynamic f-string without parameters",
                    recommendation="Use parameterized queries with '?' and bound parameter tuple."
                ))
        elif isinstance(sql_arg, ast.BinOp) and isinstance(sql_arg.op, ast.Add):
            self.findings.append(AuditFinding(
                category="SECURITY",
                severity="CRITICAL",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="CWE-89-SQLI-CONCAT",
                message=f"SQL Injection (CWE-89): Query in '{func_name}' constructed via string concatenation '+'",
                recommendation="Use parameterized queries with '?' and bound parameter tuple."
            ))
        elif isinstance(sql_arg, ast.BinOp) and isinstance(sql_arg.op, ast.Mod):
            self.findings.append(AuditFinding(
                category="SECURITY",
                severity="CRITICAL",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="CWE-89-SQLI-MOD-FORMAT",
                message=f"SQL Injection (CWE-89): Query in '{func_name}' constructed via string formatting '%'",
                recommendation="Use parameterized queries with '?' and bound parameter tuple."
            ))
        elif isinstance(sql_arg, ast.Call) and isinstance(sql_arg.func, ast.Attribute) and sql_arg.func.attr == "format":
            self.findings.append(AuditFinding(
                category="SECURITY",
                severity="CRITICAL",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="CWE-89-SQLI-STR-FORMAT",
                message=f"SQL Injection (CWE-89): Query in '{func_name}' constructed with dynamic .format()",
                recommendation="Use parameterized queries with '?' and bound parameter tuple."
            ))

    def _check_dynamic_code(self, node: ast.Call, func_name: str) -> None:
        if func_name == "eval":
            self.findings.append(AuditFinding(
                category="SECURITY",
                severity="CRITICAL",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="CWE-94-CODE-INJECTION",
                message="Use of eval() detected: arbitrary code execution risk (CWE-94)",
                recommendation="Use ast.literal_eval() or typed serialization via Pydantic/JSON."
            ))
        elif func_name == "exec":
            self.findings.append(AuditFinding(
                category="SECURITY",
                severity="CRITICAL",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="CWE-95-CODE-INJECTION",
                message="Use of exec() detected: dynamic code injection risk (CWE-95)",
                recommendation="Eliminate dynamic runtime code execution."
            ))

    def _check_os_and_deserialization(self, node: ast.Call, func_name: str) -> None:
        if func_name == "system" and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                self.findings.append(AuditFinding(
                    category="SECURITY",
                    severity="HIGH",
                    file_path=self.rel_path,
                    line_number=node.lineno,
                    rule_id="CWE-78-OS-SYSTEM",
                    message="Use of os.system() detected: vulnerable to OS command injection (CWE-78)",
                    recommendation="Use subprocess.run(..., shell=False) with an explicit argument list."
                ))
        elif func_name in ("load", "loads") and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
                self.findings.append(AuditFinding(
                    category="SECURITY",
                    severity="CRITICAL",
                    file_path=self.rel_path,
                    line_number=node.lineno,
                    rule_id="CWE-502-DESERIALIZATION",
                    message="Use of pickle.loads() detected: insecure deserialization risk (CWE-502 / RCE)",
                    recommendation="Replace with secure serialization formats such as JSON or Protocol Buffers."
                ))
        elif func_name in ("run", "Popen", "call", "check_call"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append(AuditFinding(
                        category="SECURITY",
                        severity="HIGH",
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        rule_id="CWE-78-SHELL-TRUE",
                        message="Subshell execution enabled ('shell=True') in subprocess call",
                        recommendation="Pass command as argument list with 'shell=False'."
                    ))

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a Call node."""
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        self._check_sql_sink(node, func_name)
        self._check_dynamic_code(node, func_name)
        self._check_os_and_deserialization(node, func_name)
        self.generic_visit(node)


def _scan_known_secrets(content: str, rel_path: str) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for line_idx, line in enumerate(content.splitlines(), 1):
        clean = line.strip()
        if clean.startswith("#") or clean.startswith("//"):
            continue
        for pattern, sec_name, severity in SECRET_KNOWN_PATTERNS:
            if pattern.search(line):
                findings.append(AuditFinding(
                    category="SECURITY",
                    severity=severity,
                    file_path=rel_path,
                    line_number=line_idx,
                    rule_id="CWE-798-SECRET-LEAK",
                    message=f"Fuga de credencial con prefijo oficial: {sec_name}",
                    recommendation="Mover secreto a variables de entorno o Secret Manager."
                ))
    return findings


def _scan_entropy_secrets(tree: ast.AST, rel_path: str) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value.strip()
            if is_high_entropy_secret(val):
                findings.append(AuditFinding(
                    category="SECURITY",
                    severity="HIGH",
                    file_path=rel_path,
                    line_number=node.lineno,
                    rule_id="CWE-798-HIGH-ENTROPY-SECRET",
                    message=f"High-entropy constant (H={round(calculate_shannon_entropy(val), 2)} bits/char): possible hardcoded private key",
                    recommendation="Externalize secret keys to environment variables (os.environ)."
                ))
    return findings


def _scan_single_file_security(
    code_file: Path, target_dir: Path
) -> tuple[list[AuditFinding], int, bool]:
    findings: list[AuditFinding] = []
    entropy_secrets_found = 0
    rel_path = str(code_file.relative_to(target_dir))
    is_test = "test" in code_file.name or "tests" in code_file.parts

    try:
        content = code_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings, 0, True

    file_has_issue = False
    if not is_test:
        secret_findings = _scan_known_secrets(content, rel_path)
        if secret_findings:
            file_has_issue = True
            findings.extend(secret_findings)

    if code_file.suffix == ".py":
        try:
            tree = ast.parse(content)
            visitor = ASTSecurityTaintVisitor(rel_path)
            visitor.visit(tree)
            if visitor.findings:
                file_has_issue = True
                findings.extend(visitor.findings)

            if not is_test:
                ent_findings = _scan_entropy_secrets(tree, rel_path)
                if ent_findings:
                    entropy_secrets_found += len(ent_findings)
                    file_has_issue = True
                    findings.extend(ent_findings)
        except SyntaxError:
            pass

    return findings, entropy_secrets_found, not file_has_issue


def run_security_sast_probe(target_dir: Path) -> ProbeResult:
    """Run a static vulnerability scan using SAST and Shannon entropy analysis."""
    findings: list[AuditFinding] = []
    scanned_files = 0
    clean_files = 0
    entropy_secrets_found = 0

    for code_file in find_target_files(target_dir, (".py", ".js", ".ts", ".tsx", ".json")):
        scanned_files += 1
        f_findings, ent_cnt, is_clean = _scan_single_file_security(code_file, target_dir)
        findings.extend(f_findings)
        entropy_secrets_found += ent_cnt
        if is_clean:
            clean_files += 1

    score = 100.0
    for f in findings:
        if f.severity == "CRITICAL":
            score -= 25.0
        elif f.severity == "HIGH":
            score -= 15.0
        elif f.severity == "MEDIUM":
            score -= 5.0

    score = max(0.0, min(100.0, round(score, 1)))
    passed = not any(f.severity == "CRITICAL" for f in findings) and score >= 80.0

    return ProbeResult(
        probe_name="Security SAST & Secret Scanner (OWASP ASVS 5.0)",
        score_pct=score,
        passed=passed,
        metrics={
            "scanned_files": scanned_files,
            "clean_files": clean_files,
            "findings_count": len(findings),
            "critical_count": sum(1 for f in findings if f.severity == "CRITICAL"),
            "high_count": sum(1 for f in findings if f.severity == "HIGH"),
            "entropy_secrets_found": entropy_secrets_found
        },
        findings=findings
    )
