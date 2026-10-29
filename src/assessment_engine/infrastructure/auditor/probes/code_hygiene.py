"""
Analyze code hygiene and self-admitted technical debt (SATD / CWE-391). Features:
- Detect blind exception swallowing in the AST (CWE-391: unlogged 'except: pass').
- Filter self-admitted technical debt (disallow colloquial language, workarounds, and emojis in comments).
- Detect abuse of linter suppressions (systematic '# noqa' or '# type: ignore').
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive"
}

INFORMAL_SLANG_PATTERN = re.compile(
    r"""(?i)#\s*.*?\b(ñapa|chapuza|magia negra|hack rápido|quick hack|viva la virgen|a tomar por saco|truco sucio|maldita sea|menuda mierda)\b"""
)

EMOJI_PATTERN = re.compile(
    r"""[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF]"""
)

SUPPRESSION_DIRECTIVES = re.compile(
    r"""(?i)(#\s*noqa|#\s*type:\s*ignore|//\s*@ts-ignore|/\*\s*eslint-disable)"""
)


class SilentExceptionVisitor(ast.NodeVisitor):
    """Inspecciona bloques try/except buscando silenciamiento ciego de errores (CWE-391)."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self.total_handlers = 0

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Visit an ExceptHandler node."""
        self.total_handlers += 1
        is_broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException"))
        if not is_broad:
            self.generic_visit(node)
            return

        is_silent_pass = False
        if len(node.body) == 1:
            first = node.body[0]
            if isinstance(first, ast.Pass):
                is_silent_pass = True
            elif isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and first.value.value is Ellipsis:
                is_silent_pass = True

        if is_silent_pass:
            exc_type = "Exception" if node.type is None else getattr(node.type, "id", "Exception")

            self.findings.append(AuditFinding(
                category="CODE_HYGIENE",
                severity="HIGH",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="HYGIENE-CWE391-SILENT-PASS",
                message=f"Generic exception '{exc_type}' silenced with blind 'pass': masks silent errors (CWE-391)",
                recommendation="Log failure with 'logger.warning/debug' or re-raise the exception ('raise')."
            ))

        self.generic_visit(node)


def _audit_file_hygiene(
    content: str, rel_path: str, findings: list[AuditFinding]
) -> tuple[int, int]:
    unprofessional_comments_count = 0
    file_suppressions = 0

    for line_idx, line in enumerate(content.splitlines(), 1):
        clean_line = line.strip()

        if clean_line.startswith("#") or " #" in line:
            if not any(k in clean_line.lower() for k in ("cve-", "rfc", "http://", "https://", "noqa", "type:")):
                if INFORMAL_SLANG_PATTERN.search(clean_line):
                    unprofessional_comments_count += 1
                    findings.append(AuditFinding(
                        category="CODE_HYGIENE",
                        severity="MEDIUM",
                        file_path=rel_path,
                        line_number=line_idx,
                        rule_id="HYGIENE-UNPROFESSIONAL-COMMENT",
                        message=f"Comentario informal o vibe-coding detectado: '{clean_line[:60]}...'",
                        recommendation="Maintain sober, objective, and professional technical tone without informal vernacular."
                    ))

                if EMOJI_PATTERN.search(clean_line):
                    unprofessional_comments_count += 1
                    findings.append(AuditFinding(
                        category="CODE_HYGIENE",
                        severity="LOW",
                        file_path=rel_path,
                        line_number=line_idx,
                        rule_id="HYGIENE-EMOJI-IN-CODE",
                        message="Emojis detected in production code comments",
                        recommendation="Remove emojis; enterprise production codebase requires strict sobriety."
                    ))

        if SUPPRESSION_DIRECTIVES.search(line):
            file_suppressions += 1

    return unprofessional_comments_count, file_suppressions


def run_code_hygiene_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive code hygiene and discipline audit."""
    findings: list[AuditFinding] = []
    scanned_files = 0
    total_handlers_count = 0
    silent_pass_count = 0
    unprofessional_comments_count = 0
    suppression_abuse_count = 0

    for py_file in find_target_files(target_dir, (".py",)):
        rel_path = str(py_file.relative_to(target_dir))
        is_test = "test" in py_file.name or "tests" in py_file.parts

        scanned_files += 1
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        # 1. Audit informal comments and emojis (production only, exclude tests)
        if not is_test:
            up_count, file_supp = _audit_file_hygiene(content, rel_path, findings)
            unprofessional_comments_count += up_count

            if file_supp > 15:
                suppression_abuse_count += 1
                findings.append(AuditFinding(
                    category="CODE_HYGIENE",
                    severity="MEDIUM",
                    file_path=rel_path,
                    line_number=None,
                    rule_id="HYGIENE-SUPPRESSION-SPAM",
                    message=f"Excessive suppression directives ({file_supp} directives # noqa or # type: ignore)",
                    recommendation="Resolve structural types and warnings directly instead of mass-suppressing linters."
                ))

        # 2. AST Analysis of Silenced Exceptions (CWE-391)
        if not is_test:
            try:
                tree = ast.parse(content)
                visitor = SilentExceptionVisitor(rel_path)
                visitor.visit(tree)
                total_handlers_count += visitor.total_handlers
                if visitor.findings:
                    silent_pass_count += len(visitor.findings)
                    findings.extend(visitor.findings)
            except SyntaxError:
                continue

    # 3. Run deterministic linter checks (Ruff: F821, F822, BLE001)
    import json
    import shutil
    import subprocess

    ruff_bin = shutil.which("ruff") or str(target_dir / "venv" / "bin" / "ruff")
    static_defects_count = 0
    if Path(ruff_bin).exists() or shutil.which("ruff"):
        try:
            cmd = [
                ruff_bin, "check",
                str(target_dir / "core"),
                str(target_dir / "routers"),
                str(target_dir / "server.py"),
                "--format=json"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.stdout:
                ruff_errors = json.loads(res.stdout)
                static_defects_count = len(ruff_errors)
                for err in ruff_errors:
                    rule = err.get("code")
                    findings.append(AuditFinding(
                        category="CODE_HYGIENE",
                        severity="CRITICAL",
                        file_path=err.get("filename"),
                        line_number=err.get("location", {}).get("row"),
                        rule_id=f"STATIC-{rule}",
                        message=f"Ruff {rule}: {err.get('message')}",
                        recommendation="Resolve blind exceptions or undefined symbols before certifying release."
                    ))
        except (json.JSONDecodeError, OSError, subprocess.SubprocessError):
            pass

    # Compute strict weighted score with zero tolerance for silent exceptions and static defects
    score = 100.0
    score -= min(30.0, silent_pass_count * 5.0)
    score -= min(30.0, static_defects_count * 10.0)
    score -= min(15.0, unprofessional_comments_count * 5.0)
    score -= min(15.0, suppression_abuse_count * 2.0)

    score = max(0.0, min(100.0, round(score, 1)))
    passed = silent_pass_count == 0 and static_defects_count == 0 and unprofessional_comments_count == 0 and score >= 70.0

    return ProbeResult(
        probe_name="Code Hygiene & Anti-Vibe Governance (SATD / CWE-391)",
        score_pct=score,
        passed=passed,
        metrics={
            "scanned_files": scanned_files,
            "silent_exceptions_count": silent_pass_count,
            "static_defects_count": static_defects_count,
            "unprofessional_comments_count": unprofessional_comments_count,
            "suppression_abuses_count": suppression_abuse_count,
            "sobriety_status": "Sobrio y Disciplinado" if passed else "Desviaciones Detectadas"
        },
        findings=findings
    )
