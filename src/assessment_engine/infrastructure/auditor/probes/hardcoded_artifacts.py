"""
Detect hardcoded artifacts, including high-entropy secrets, absolute host paths, domain leaks, PII, hardcoded AI models (MODEL_LEAK), fallback secrets (CWE-1188), and magic sleeps (RAW_SLEEP). Implement Shannon entropy calculation and strict AST structural analysis.
"""
from __future__ import annotations

import ast
import logging
import math
import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

logger = logging.getLogger("assessment_engine.infrastructure.auditor.probes.hardcoded_artifacts")

# Regex Patterns
PATH_LEAK_REGEX = re.compile(r"(/home/[a-zA-Z0-9_-]+|/Users/[a-zA-Z0-9_-]+)(/[a-zA-Z0-9_-]+)*")
PII_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@(?:gmail|hotmail|yahoo|outlook)\.com", re.IGNORECASE)
SECRET_ASSIGN_REGEX = re.compile(r"(?i)(secret|api_key|password|token)\s*(:|=)\s*['\"]([^'\"]{10,})['\"]")
DOMAIN_LEAK_KEYWORDS = {"Patients", "clinic_id", "veterinari", "mascota"}
AI_MODEL_REGEX = re.compile(r"^(gemini|gpt|claude|deepseek)-[0-9]", re.IGNORECASE)


def calculate_shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy to detect pseudorandom strings (keys, hashes)."""
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        entropy -= p_x * math.log2(p_x)
    return entropy


def is_public_url(val: str) -> bool:
    """Determine whether the specified string is a publicly accessible URL."""
    return val.startswith("http://") or val.startswith("https://")


class PythonHardcodedVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []

    def visit_Constant(self, node: ast.Constant):
        """Visit an AST Constant node."""
        if isinstance(node.value, str):
            val = node.value
            if PATH_LEAK_REGEX.search(val):
                self.findings.append(AuditFinding(
                    category="ENV_LEAK", severity="CRITICAL", file_path=self.rel_path, line_number=node.lineno,
                    rule_id="CWE-200_HARDCODED_PATH", message=f"Ruta de host local absoluta detectada: '{val[:30]}...'",
                    recommendation="Usar anclaje relativo con Path(__file__).resolve().parents o inyección de variable de entorno."
                ))
            if PII_EMAIL_REGEX.search(val) and "example.com" not in val.lower() and "test" not in val.lower():
                self.findings.append(AuditFinding(
                    category="PII_LEAK", severity="HIGH", file_path=self.rel_path, line_number=node.lineno,
                    rule_id="RGPD_ART5_HARDCODED_PII", message=f"Posible PII detectado en literal de cadena: '{val}'",
                    recommendation="Evitar PII real. Usar faker, example.com o resolución de DB dinámica."
                ))
            if ("core/primitives" in self.rel_path or "core/auditor" in self.rel_path) and "test_" not in self.rel_path:
                if any(kw in val for kw in DOMAIN_LEAK_KEYWORDS):
                    if "hardcoded_artifacts.py" not in self.rel_path:
                        self.findings.append(AuditFinding(
                            category="DOMAIN_LEAK", severity="MEDIUM", file_path=self.rel_path, line_number=node.lineno,
                            rule_id="ARCH_DOMAIN_LEAK", message=f"Fuga de dominio detectada en paquete agnóstico: '{val}'",
                            recommendation="Desacoplar la entidad específica usando configuración de esquema genérico."
                        ))
        self.generic_visit(node)

    def _check_assign_target(self, target: Any, node: ast.Assign) -> None:
        if not isinstance(target, ast.Name):
            return
        name = target.id.lower()
        if not any(k in name for k in ["secret", "key", "password", "token"]):
            return
        if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            return
        val = node.value.value
        if len(val) < 12 or is_public_url(val) or any(k in val.lower() for k in ("env", "mock", "test")):
            return
        entropy = calculate_shannon_entropy(val)
        if entropy > 3.8:
            self.findings.append(AuditFinding(
                category="SECRET_LEAK", severity="CRITICAL", file_path=self.rel_path, line_number=node.lineno,
                rule_id="CWE-798_HARDCODED_SECRET", message=f"Secreto estático de alta entropía ({entropy:.2f}) en '{target.id}'.",
                recommendation="Usar os.environ.get() o secrets.token_hex() para fallbacks locales."
            ))

    def visit_Assign(self, node: ast.Assign):
        """Visit an AST Assign node."""
        for target in node.targets:
            self._check_assign_target(target, node)
        self.generic_visit(node)

    def _check_model_leak(self, node: ast.Call) -> None:
        if "core/genai_client.py" in self.rel_path or "core/legacy/" in self.rel_path:
            return
        for kw in node.keywords:
            if kw.arg == "model" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                if AI_MODEL_REGEX.match(kw.value.value):
                    self.findings.append(AuditFinding(
                        category="MODEL_LEAK", severity="HIGH", file_path=self.rel_path, line_number=node.lineno,
                        rule_id="ARCH_HARDCODED_AI_MODEL", message=f"Modelo de IA hardcodeado en llamada: '{kw.value.value}'.",
                        recommendation="Usar get_model(ModelTier.REASONING) o get_model(ModelTier.FAST) de core.genai_client."
                    ))

    def _check_fallback_secret(self, node: ast.Call) -> None:
        if not (isinstance(node.func, ast.Attribute) and node.func.attr in ("get", "getenv")):
            return
        if len(node.args) < 2:
            return
        if not (isinstance(node.args[0], ast.Constant) and isinstance(node.args[1], ast.Constant)):
            return
        key_name = str(node.args[0].value).lower()
        fallback_val = node.args[1].value
        if not (isinstance(fallback_val, str) and len(fallback_val) > 8):
            return
        if any(s in key_name for s in ("secret", "password", "token_key")) and "mock" not in fallback_val.lower():
            self.findings.append(AuditFinding(
                category="FALLBACK_SECRET_LEAK", severity="CRITICAL", file_path=self.rel_path, line_number=node.lineno,
                rule_id="CWE-1188_INSECURE_DEFAULT_SECRET", message=f"Secreto estático por defecto en entorno para '{node.args[0].value}'.",
                recommendation="Usar resolve_secret() para aplicar Fail-Fast o generar token en memoria."
            ))

    def _check_raw_sleep(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "sleep":
            return
        if not node.args or not (isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, (int, float))):
            return
        if any(p in self.rel_path for p in ("daemon_supervisor", "core/primitives")):
            self.findings.append(AuditFinding(
                category="RAW_SLEEP_LITERAL", severity="MEDIUM", file_path=self.rel_path, line_number=node.lineno,
                rule_id="SRE_RAW_SLEEP_MAGIC_NUMBER", message=f"Pausa con número mágico '{node.args[0].value}' en lugar de constante SRE.",
                recommendation="Usar constantes semánticas de core.config.sre_constants (ej. DEFAULT_RETRY_BACKOFF_SEC)."
            ))

    def visit_Call(self, node: ast.Call):
        """Visit an AST Call node."""
        self._check_model_leak(node)
        self._check_fallback_secret(node)
        self._check_raw_sleep(node)
        self.generic_visit(node)


def _scan_single_python_file(py_file: Path, target_path: Path) -> list[AuditFinding]:
    if "tests/" in str(py_file) or py_file.name.startswith("test_"):
        return []
    try:
        rel_path = py_file.relative_to(target_path).as_posix()
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=py_file.name)
        visitor = PythonHardcodedVisitor(rel_path)
        visitor.visit(tree)
        return visitor.findings
    except (SyntaxError, ValueError, UnicodeDecodeError, OSError):
        return []


def _scan_single_ts_line(line: str, i: int, rel_path: str) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    if line.strip().startswith(("//", "/*", "*")):
        return findings

    if PATH_LEAK_REGEX.search(line):
        findings.append(AuditFinding(
            category="ENV_LEAK", severity="CRITICAL", file_path=rel_path, line_number=i,
            rule_id="CWE-200_HARDCODED_PATH", message="Ruta de host local absoluta detectada.",
            recommendation="Usar configuración inyectada (ej. variable de entorno) o ruta relativa."
        ))
    if PII_EMAIL_REGEX.search(line) and "example.com" not in line.lower() and "test" not in line.lower():
        findings.append(AuditFinding(
            category="PII_LEAK", severity="HIGH", file_path=rel_path, line_number=i,
            rule_id="RGPD_ART5_HARDCODED_PII", message="PII real detectado en código fuente.",
            recommendation="Usar variables de sesión, un .env o un proveedor de Auth."
        ))
    match = SECRET_ASSIGN_REGEX.search(line)
    if match:
        val = match.group(3)
        if len(val) >= 12 and not is_public_url(val) and not any(k in line.lower() for k in ("mock", "test", "env")):
            entropy = calculate_shannon_entropy(val)
            if entropy > 3.8:
                findings.append(AuditFinding(
                    category="SECRET_LEAK", severity="CRITICAL", file_path=rel_path, line_number=i,
                    rule_id="CWE-798_HARDCODED_SECRET", message=f"Asignación de secreto de alta entropía ({entropy:.2f}).",
                    recommendation="Usar variables de entorno (VITE_ / process.env)."
                ))
    return findings


def _scan_single_ts_file(ts_file: Path, target_path: Path) -> list[AuditFinding]:
    if "tests/" in str(ts_file) or ".test." in ts_file.name:
        return []
    findings: list[AuditFinding] = []
    try:
        rel_path = ts_file.relative_to(target_path).as_posix()
        content = ts_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            findings.extend(_scan_single_ts_line(line, i, rel_path))
    except (OSError, UnicodeDecodeError) as ex:
        logger.debug(f"TS scan error in {ts_file}: {ex}")
    return findings


def run_hardcoded_artifacts_probe(target_path: Path) -> ProbeResult:
    """Scan the target path for hardcoded artifacts."""
    target_path = target_path.resolve()
    py_files = find_target_files(target_path, (".py",))
    ts_files = find_target_files(target_path, (".ts", ".tsx", ".js", ".jsx"))

    findings: list[AuditFinding] = []
    for pf in py_files:
        findings.extend(_scan_single_python_file(pf, target_path))
    for tf in ts_files:
        findings.extend(_scan_single_ts_file(tf, target_path))

    total_files = len(py_files) + len(ts_files)
    passed = len(findings) == 0
    score_pct = max(0.0, 100.0 - (len(findings) * 5.0))

    return ProbeResult(
        probe_name="Hardcoded Artifacts & Secrets (CWE-798 / 12-Factor)",
        score_pct=score_pct,
        passed=passed,
        metrics={"scanned_files": total_files, "hardcoded_issues": len(findings)},
        findings=findings
    )
