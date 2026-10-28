"""
Probe AI and LLM security in accordance with the OWASP Top 10 for LLM Applications. Implement:
- LLM03: Excessive agency mitigation via Bubblewrap sandboxing and ExecutionGuard.
- LLM01: Prompt injection prevention via strict role separation.
- LLM06: Unbounded consumption control and FinOps limits.
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

GENAI_CALLS = {"generate_content", "create_chat", "generate", "chat"}


class AISafetyASTVisitor(ast.NodeVisitor):
    """Inspect language model and agent tool calls in the AST."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self.llm_calls_count = 0
        self.raw_shell_calls_count = 0

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Visit a formatted string literal node."""
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                lower_val = val.value.lower()
                if "system:" in lower_val or "instrucciones del sistema" in lower_val or "system instructions" in lower_val:
                    if len(node.values) > 1:
                        self.findings.append(AuditFinding(
                            category="AI_SAFETY",
                            severity="HIGH",
                            file_path=self.rel_path,
                            line_number=node.lineno,
                            rule_id="LLM01-PROMPT-INJECTION-RISK",
                            message="Interpolación directa de variables en prompt del sistema: vulnerable a Prompt Injection (LLM01:2026)",
                            recommendation="Usar el parámetro explícito 'system_instruction' de la API de GenAI para aislar el contexto del sistema."
                        ))
                        break
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call node."""
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        if func_name in GENAI_CALLS or func_name in ("create", "generate_content"):
            self.llm_calls_count += 1

        if func_name in ("run", "Popen", "call", "check_call"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.raw_shell_calls_count += 1

        self.generic_visit(node)


def _scan_code_ai_patterns(content: str) -> tuple[bool, bool, bool]:
    lower = content.lower()
    has_bwrap = "bwrap" in lower or "bubblewrap" in lower
    has_guard = "execution_guard" in lower or "169.254.169.254" in lower
    has_budget = "max_cost_usd" in lower or "max_tokens" in lower or "max_output_tokens" in lower
    return has_bwrap, has_guard, has_budget


def _calculate_ai_safety_score(
    has_raw_unsandboxed_shell: bool,
    total_llm_calls: int,
    has_finops_budget: bool,
    findings: list[AuditFinding]
) -> tuple[float, bool]:
    score = 100.0
    if has_raw_unsandboxed_shell:
        score -= 40.0
    for f in findings:
        if f.rule_id == "LLM01-PROMPT-INJECTION-RISK":
            score -= 25.0
        elif f.rule_id == "LLM03-EXCESSIVE-AGENCY":
            score -= 30.0

    if total_llm_calls > 0 and not has_finops_budget:
        score -= 10.0
        findings.append(AuditFinding(
            category="AI_SAFETY",
            severity="MEDIUM",
            file_path="core/config/",
            line_number=None,
            rule_id="LLM06-UNBOUNDED-CONSUMPTION",
            message="Llamadas a LLM sin presupuesto FinOps ni límite estricto de tokens de salida (Denial of Wallet)",
            recommendation="Fijar 'max_cost_usd' y 'max_output_tokens' en la configuración de llamada."
        ))

    score = max(0.0, min(100.0, round(score, 1)))
    has_high_or_crit = any(f.severity in ("CRITICAL", "HIGH") for f in findings)
    passed = not has_raw_unsandboxed_shell and not has_high_or_crit and score >= 75.0
    return score, passed


def run_ai_safety_llm_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive AI security audit and agentic risk mitigation."""
    findings: list[AuditFinding] = []
    total_llm_calls = 0

    has_bwrap_sandbox = False
    has_execution_guard = False
    has_finops_budget = False
    has_raw_unsandboxed_shell = False

    for py_file in find_target_files(target_dir, (".py",)):
        rel_path = str(py_file.relative_to(target_dir))
        is_test = "test" in py_file.name or "tests" in py_file.parts

        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        bwrap, guard, budget = _scan_code_ai_patterns(content)
        has_bwrap_sandbox = has_bwrap_sandbox or bwrap
        has_execution_guard = has_execution_guard or guard
        has_finops_budget = has_finops_budget or budget

        if not is_test:
            try:
                tree = ast.parse(content)
                visitor = AISafetyASTVisitor(rel_path)
                visitor.visit(tree)
                total_llm_calls += visitor.llm_calls_count
                findings.extend(visitor.findings)

                if visitor.raw_shell_calls_count > 0 and not has_bwrap_sandbox:
                    has_raw_unsandboxed_shell = True
                    findings.append(AuditFinding(
                        category="AI_SAFETY",
                        severity="CRITICAL",
                        file_path=rel_path,
                        line_number=1,
                        rule_id="LLM03-EXCESSIVE-AGENCY",
                        message="Ejecución de shell por código agéntico sin enjaulamiento en sandbox Bubblewrap (LLM03:2026 Agencia Excesiva)",
                        recommendation="Enjaular todo comando bash con 'bwrap --unshare-all --ro-bind /' y aplicar ExecutionGuard."
                    ))
            except SyntaxError:
                continue

    if total_llm_calls == 0 and not has_bwrap_sandbox and len(findings) == 0:
        return ProbeResult(
            probe_name="AI Safety & LLM Guardrails (OWASP for LLM 2026)",
            score_pct=100.0,
            passed=True,
            metrics={"status": "NO_AI_INFERENCE_DETECTED", "llm_calls_count": 0, "has_bwrap_sandbox": has_bwrap_sandbox}
        )

    score, passed = _calculate_ai_safety_score(has_raw_unsandboxed_shell, total_llm_calls, has_finops_budget, findings)

    return ProbeResult(
        probe_name="AI Safety & LLM Guardrails (OWASP for LLM 2026)",
        score_pct=score,
        passed=passed,
        metrics={
            "llm_calls_audited": total_llm_calls,
            "has_bwrap_sandbox": has_bwrap_sandbox,
            "has_execution_guard": has_execution_guard,
            "has_finops_budget": has_finops_budget,
            "owasp_llm_compliance": "Conforme Nivel 1" if passed else "No Conforme"
        },
        findings=findings
    )
