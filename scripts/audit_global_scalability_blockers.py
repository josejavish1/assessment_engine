#!/usr/bin/env python3
"""Unified Global Scalability & Invariance Audit.

Scans the codebase across four essential dimensions required for universal enterprise readiness:
1. Vector 1: Tenant Contamination & Pilot Bleeding (Zero hardcoded customer names/domains).
2. Vector 2: Linguistic Decoupling & i18n Purity (100% Technical English in code, zero unlocalized report prose).
3. Vector 3: Scale Invariance (Relative ratios, dynamic FX, support for SMB to Global Conglomerates).
4. Vector 4: Vertical & Jurisdictional Decoupling (Abstract ontologies, zero hardcoded national laws in core domain).
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src" / "assessment_engine"
CONFIG_DIR = REPO_ROOT / "engine_config"

# --- Vector 1 Rules: Tenant Identifiers ---
SUSPICIOUS_TENANT_TOKENS: Tuple[str, ...] = (
    "molins",
    "secil",
    "cemex",
    "holcim",
    "heidelberg",
)

# --- Vector 2 Rules: Non-English words in code comments / docstrings ---
SPANISH_CODE_INDICATORS: Tuple[str, ...] = (
    "función",
    "parámetro",
    "configuración",
    "descripción",
    "evaluación",
    "análisis",
    "módulo",
    "método",
    "cálculo",
    "retorna",
    "ejecuta",
    "validación",
    "implementación",
    "información",
    "dirección",
    "operación",
    "página",
    "índice",
    "título",
    "párrafo",
    "cabecera",
    "tabla",
    "archivo",
    "carpeta",
)

INLINE_LANG_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:doc_lang|lang|meta_lang|target_lang|locale|base_loc)\s*(?:==|!=)\s*[\"'][a-zA-Z_\-]+[\"']"),
    re.compile(r"\b(?:doc_lang|lang|meta_lang|target_lang|locale|base_loc)\s+(?:in|not in)\s+\[.*?\]"),
    re.compile(r"if\s+.*?\b(?:doc_lang|lang|meta_lang|locale)\b.*?else"),
)

REPORT_LITERAL_CALLS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"add_heading_paragraph\s*\(\s*doc\s*,\s*[\"']([^\"']{5,})[\"']"),
    re.compile(r"add_heading\s*\(\s*doc\s*,\s*[\"']([^\"']{5,})[\"']"),
    re.compile(r"add_body_paragraph\s*\(\s*doc\s*,\s*[\"']([^\"']{5,})[\"']"),
    re.compile(r"add_run\s*\(\s*[\"']([^\"']{5,})[\"']"),
    re.compile(r"HeadingNode\s*\(\s*text\s*=\s*[\"']([^\"']{5,})[\"']"),
    re.compile(r"ParagraphNode\s*\(\s*text\s*=\s*[\"']([^\"']{5,})[\"']"),
)

# --- Vector 3 Rules: Scale Invariance & Currency Hardcoding ---
STATIC_CURRENCY_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"[\"'][€$£¥]\s*[\d\.,]+[\"']"),
    re.compile(r"[\"'][\d\.,]+\s*€[\"']"),
    re.compile(r"[\"']\s*EUR\s*[\"']"),
)

# --- Vector 4 Rules: National Regulatory & Industry Coupling in Core Domain ---
NATIONAL_REGULATOR_TOKENS: Tuple[str, ...] = (
    "CNMV",
    "BANCO DE ESPAÑA",
    "AEMPS",
    "BAFIN",
    "BUNDESBANK",
    "BFARM",
    "ANSSI",
    "SECNUMCLOUD",
    "ACPR",
    "FEDRAMP",
    "HIPAA",
    "HITECH",
    "BACEN",
    "CVM",
    "ANVISA",
    "FISC",
    "ISMAP",
    "NCA ECC",
)


@dataclass
class Finding:
    vector: str
    rule_id: str
    severity: str  # HIGH, MEDIUM, LOW
    file_path: str
    line_number: int
    message: str
    snippet: str


class ScalabilityAuditVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str, raw_lines: List[str]):
        self.rel_path = rel_path
        self.raw_lines = raw_lines
        self.findings: List[Finding] = []

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            val = node.value.strip()

            # Vector 1: Tenant Bleeding
            val_lower = val.lower()
            for token in SUSPICIOUS_TENANT_TOKENS:
                if token in val_lower:
                    # Ignore technical URLs, documentation links, or file suffixes
                    if not any(k in val_lower for k in ("http", "github", "example", ".py", ".md", ".json")):
                        # Also check if it's in hardcoded_artifacts probe itself
                        if "hardcoded_artifacts.py" not in self.rel_path and "test" not in self.rel_path:
                            self.findings.append(Finding(
                                vector="Vector 1 (Tenant Bleeding)",
                                rule_id="TENANT_IDENTIFIER_LEAK",
                                severity="HIGH",
                                file_path=self.rel_path,
                                line_number=node.lineno,
                                message=f"Tenant-specific token '{token}' found in string literal: '{val[:60]}...'",
                                snippet=self._get_snippet(node.lineno),
                            ))

            # Vector 4: Regulatory hardcoding in core domain/services
            is_core_domain = ("src/assessment_engine/domain" in self.rel_path or 
                              "src/assessment_engine/services" in self.rel_path)
            is_exempt = ("executive_summary_ast.py" in self.rel_path or 
                         "jurisdictional_sovereignty.py" in self.rel_path or
                         "framework_urn.py" in self.rel_path or
                         "test" in self.rel_path)
            if is_core_domain and not is_exempt:
                for token in NATIONAL_REGULATOR_TOKENS:
                    if re.search(rf"\b{re.escape(token)}\b", val, re.IGNORECASE):
                        self.findings.append(Finding(
                            vector="Vector 4 (Jurisdictional Coupling)",
                            rule_id="CORE_REGULATOR_HARDCODED",
                            severity="HIGH",
                            file_path=self.rel_path,
                            line_number=node.lineno,
                            message=f"National regulatory token '{token}' hardcoded in core domain logic: '{val[:60]}...'",
                            snippet=self._get_snippet(node.lineno),
                        ))

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_docstring(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_docstring(node)
        self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> None:
        self._check_docstring(node)
        self.generic_visit(node)

    def _check_docstring(self, node: ast.AST) -> None:
        doc = ast.get_docstring(node)
        if doc and "test" not in self.rel_path:
            doc_lower = doc.lower()
            for token in SPANISH_CODE_INDICATORS:
                if re.search(rf"\b{re.escape(token)}\b", doc_lower):
                    lineno = getattr(node, "lineno", 1)
                    self.findings.append(Finding(
                        vector="Vector 2 (Linguistic Decoupling)",
                        rule_id="SPANISH_DOCSTRING_IN_PYTHON",
                        severity="MEDIUM",
                        file_path=self.rel_path,
                        line_number=lineno,
                        message=f"Spanish word '{token}' detected in Python docstring.",
                        snippet=doc[:100].replace("\n", " "),
                    ))
                    break

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.raw_lines):
            return self.raw_lines[lineno - 1].strip()
        return ""


def audit_python_file(file_path: Path) -> List[Finding]:
    rel_path = file_path.relative_to(REPO_ROOT).as_posix()
    findings: List[Finding] = []

    try:
        content = file_path.read_text(encoding="utf-8")
        raw_lines = content.splitlines()
    except Exception as e:
        return [Finding(
            vector="Vector 0 (File Access)",
            rule_id="FILE_READ_ERROR",
            severity="HIGH",
            file_path=rel_path,
            line_number=0,
            message=str(e),
            snippet="",
        )]

    # 1. AST Analysis
    try:
        tree = ast.parse(content, filename=rel_path)
        visitor = ScalabilityAuditVisitor(rel_path, raw_lines)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError as e:
        findings.append(Finding(
            vector="Vector 0 (Syntax Error)",
            rule_id="PYTHON_SYNTAX_ERROR",
            severity="CRITICAL",
            file_path=rel_path,
            line_number=e.lineno or 0,
            message=f"SyntaxError parsing file: {e}",
            snippet="",
        ))

    # 2. Line-by-line checks for comments, i18n branching, and literal calls
    is_test_file = "test" in rel_path or "fixtures" in rel_path
    for idx, line in enumerate(raw_lines, start=1):
        s_line = line.strip()

        # Vector 2: Check Spanish in comments
        if "#" in line and not is_test_file:
            comment_text = line.split("#", 1)[1].lower()
            for token in SPANISH_CODE_INDICATORS:
                if re.search(rf"\b{re.escape(token)}\b", comment_text):
                    findings.append(Finding(
                        vector="Vector 2 (Linguistic Decoupling)",
                        rule_id="SPANISH_COMMENT_IN_PYTHON",
                        severity="LOW",
                        file_path=rel_path,
                        line_number=idx,
                        message=f"Spanish comment indicator '{token}' in Python comment.",
                        snippet=s_line,
                    ))
                    break

        # Vector 2: Check inline language branching
        if not is_test_file and "localization.py" not in rel_path and "i18n.py" not in rel_path:
            for pattern in INLINE_LANG_PATTERNS:
                if pattern.search(s_line):
                    findings.append(Finding(
                        vector="Vector 2 (Linguistic Decoupling)",
                        rule_id="INLINE_LANGUAGE_BRANCHING",
                        severity="MEDIUM",
                        file_path=rel_path,
                        line_number=idx,
                        message="Inline language branching anti-pattern (if lang == ...). Use declarative locales.",
                        snippet=s_line,
                    ))
                    break

        # Vector 2: Hardcoded report strings in compiler
        if "compiler" in rel_path and not is_test_file:
            for pattern in REPORT_LITERAL_CALLS:
                m = pattern.search(s_line)
                if m:
                    lit = m.group(1).strip()
                    if len(lit) > 6 and not lit.startswith(("{", "%", "[")) and not lit.endswith(".docx"):
                        findings.append(Finding(
                            vector="Vector 2 (Linguistic Decoupling)",
                            rule_id="HARDCODED_REPORT_LITERAL",
                            severity="MEDIUM",
                            file_path=rel_path,
                            line_number=idx,
                            message=f"Direct hardcoded report literal: '{lit}'",
                            snippet=s_line,
                        ))

        # Vector 3: Hardcoded currency symbols in mathematical domain code
        if "domain" in rel_path and not is_test_file:
            for pattern in STATIC_CURRENCY_PATTERNS:
                if pattern.search(s_line) and "executive_summary_ast.py" not in rel_path:
                    findings.append(Finding(
                        vector="Vector 3 (Scale Invariance)",
                        rule_id="HARDCODED_CURRENCY_SYMBOL",
                        severity="MEDIUM",
                        file_path=rel_path,
                        line_number=idx,
                        message="Hardcoded currency literal in domain calculation. Use LocaleFormattingContract.",
                        snippet=s_line,
                    ))
                    break

    return findings


def audit_engine_config() -> List[Finding]:
    findings: List[Finding] = []
    
    # Check locales.json for suspicious tenant leaks
    locales_file = CONFIG_DIR / "locales.json"
    if locales_file.is_file():
        try:
            data = json.loads(locales_file.read_text(encoding="utf-8"))
            raw_str = json.dumps(data, ensure_ascii=False).lower()
            for token in SUSPICIOUS_TENANT_TOKENS:
                if token in raw_str:
                    findings.append(Finding(
                        vector="Vector 1 (Tenant Bleeding)",
                        rule_id="TENANT_TOKEN_IN_CONFIG",
                        severity="HIGH",
                        file_path="engine_config/locales.json",
                        line_number=1,
                        message=f"Tenant token '{token}' discovered in engine_config/locales.json",
                        snippet=f"Detected token '{token}' in locales configuration.",
                    ))
        except Exception as e:
            findings.append(Finding(
                vector="Vector 0 (Config Error)",
                rule_id="CONFIG_READ_ERROR",
                severity="HIGH",
                file_path="engine_config/locales.json",
                line_number=1,
                message=str(e),
                snippet="",
            ))

    return findings


def main() -> int:
    print("================================================================================")
    print(" UNIVERSAL ENTERPRISE SCALABILITY & INVARIANCE AUDIT (SOTA 4-VECTOR CHECK)")
    print("================================================================================")

    all_findings: List[Finding] = []

    # 1. Scan src/assessment_engine
    py_files = sorted(SRC_DIR.rglob("*.py"))
    print(f"[*] Scanning {len(py_files)} Python source files in {SRC_DIR}...")
    for f in py_files:
        all_findings.extend(audit_python_file(f))

    # 2. Scan engine_config
    print(f"[*] Scanning configuration catalogs in {CONFIG_DIR}...")
    all_findings.extend(audit_engine_config())

    # Aggregate by vector and severity
    vector_counts: Dict[str, int] = {}
    severity_counts: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for f in all_findings:
        vector_counts[f.vector] = vector_counts.get(f.vector, 0) + 1
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    print("\n--------------------------------------------------------------------------------")
    print(" AUDIT RESULTS SUMMARY:")
    print("--------------------------------------------------------------------------------")
    print(f"Total findings: {len(all_findings)}")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        print(f"  - Severity {sev:8s}: {severity_counts[sev]}")
    print()
    for vec, count in sorted(vector_counts.items()):
        print(f"  - {vec:36s}: {count}")

    if all_findings:
        print("\n--------------------------------------------------------------------------------")
        print(" ACTIONABLE FINDINGS (SEVERITY HIGH OR CRITICAL):")
        print("--------------------------------------------------------------------------------")
        high_crit = [f for f in all_findings if f.severity in ("CRITICAL", "HIGH")]
        if not high_crit:
            print("  (Zero HIGH or CRITICAL issues detected. All findings are MEDIUM or LOW quality refinements.)")
        else:
            for item in high_crit[:15]:
                print(f"[{item.severity}] {item.file_path}:{item.line_number} -> {item.rule_id}")
                print(f"  Message: {item.message}")
                if item.snippet:
                    print(f"  Snippet: {item.snippet[:80]}")
                print()

    # Save detailed JSON report
    report_path = REPO_ROOT / "docs" / "audits" / "scalability_blockers_census.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps([asdict(f) for f in all_findings], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[*] Detailed census written to {report_path.relative_to(REPO_ROOT)}")
    print("================================================================================")

    return 0 if severity_counts["CRITICAL"] == 0 and severity_counts["HIGH"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
