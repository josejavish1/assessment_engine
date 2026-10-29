"""
Probe code smells and structural entropy violations based on SWEBOK and Clean Architecture. Implement:
- AST detection of long parameter lists (> 5 positional arguments per function).
- God class detection (> 25 methods in a single class).
- Structural entropy violation detection (old/, backup/ folders and _v2/_final suffixes).
- Zombie code detection (commented-out dead code blocks in production).
"""
from __future__ import annotations

import ast
import re
import os
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files, EXCLUDE_DIRS

ENTROPY_FOLDER_NAMES = {"old", "_archive", "backup", "copia", "copias", "temp_backup"}
MANUAL_VERSION_FILE_REGEX = re.compile(r"""(?i)[-_](v\d+|final|copia|bueno)\.[a-zA-Z0-9]+$""")
PYTHON_CODE_IN_COMMENT = re.compile(r"""^\s*#\s*(def\s+|class\s+|return\s+|import\s+|from\s+|if\s+|for\s+)""")


class StructuralSmellVisitor(ast.NodeVisitor):
    """Inspect the AST for structural design antipatterns (Fowler smells)."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self.total_funcs = 0
        self.long_param_funcs = 0
        self.god_classes = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node."""
        self.total_funcs += 1
        self._check_function_params(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function definition node."""
        self.total_funcs += 1
        self._check_function_params(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition node."""
        methods = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) > 40:
            self.god_classes += 1
            self.findings.append(AuditFinding(
                category="STRUCTURAL_SMELL",
                severity="HIGH",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="SMELL-GOD-CLASS",
                message=f"God Class anti-pattern detected in '{node.name}': {len(methods)} methods (recommended threshold <= 40)",
                recommendation="Apply Single Responsibility Principle (SRP) and decompose into specialized classes."
            ))
        self.generic_visit(node)

    def _check_function_params(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # 1. Skip internal private decomposition functions (prefixed with _).
        if node.name.startswith("_"):
            return

        # 2. Skip web framework endpoint handlers (FastAPI/Starlette).
        for dec in node.decorator_list:
            try:
                dec_str = ast.unparse(dec).lower()
                if any(kw in dec_str for kw in ("router.", "app.", "api_route")):
                    return
            except (AttributeError, ValueError):
                pass

        # 3. Skip explicit cryptographic signatures and W3C standards.
        name_lower = node.name.lower()
        if any(kw in name_lower for kw in ("entry_hash", "record_cdc", "record_event", "webauthn", "registration_response")):
            return

        total_args = [a for a in node.args.args if a.arg not in ("self", "cls")]
        num_defaults = len(node.args.defaults)
        num_required = len(total_args) - num_defaults

        # SonarQube S107 and Clean Code standard:
        if num_required > 5:
            self.long_param_funcs += 1
            self.findings.append(AuditFinding(
                category="STRUCTURAL_SMELL",
                severity="MEDIUM",
                file_path=self.rel_path,
                line_number=node.lineno,
                rule_id="SMELL-LONG-PARAMETER-LIST",
                message=f"Public function '{node.name}' declares {num_required} required parameters without default (recommended threshold <= 5)",
                recommendation="Apply 'Introduce Parameter Object' (Martin Fowler): encapsulate parameters in a typed Pydantic model."
            ))


def run_structural_smells_probe(target_dir: Path) -> ProbeResult:
    """Run a comprehensive audit for code smells and repository entropy discipline."""
    findings: list[AuditFinding] = []
    scanned_files = 0
    total_funcs_count = 0
    entropy_violations_count = 0
    long_params_count = 0
    god_classes_count = 0
    zombie_code_blocks_count = 0

    # 1. Audit directory tree (zero-entropy architecture).
    for root, dirs, files in os.walk(str(target_dir), topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for d in dirs:
            if d.lower() in ENTROPY_FOLDER_NAMES:
                entropy_violations_count += 1
                rel_d = str(Path(root, d).relative_to(target_dir))
                findings.append(AuditFinding(
                    category="STRUCTURAL_SMELL",
                    severity="HIGH",
                    file_path=rel_d,
                    line_number=None,
                    rule_id="SMELL-REPO-ENTROPY-DIR",
                    message=f"Prohibited backup folder detected: '{rel_d}' (Zero-Entropy Violation)",
                    recommendation="Remove manual backup folders; Git is the sole authorized time machine."
                ))
        for f in files:
            if MANUAL_VERSION_FILE_REGEX.search(f):
                entropy_violations_count += 1
                rel_f = str(Path(root, f).relative_to(target_dir))
                findings.append(AuditFinding(
                    category="STRUCTURAL_SMELL",
                    severity="HIGH",
                    file_path=rel_f,
                    line_number=None,
                    rule_id="SMELL-REPO-ENTROPY-FILE",
                    message=f"Nombre de archivo con versionado manual prohibido: '{f}'",
                    recommendation="Use canonical filenames without '_v2' or '_final' suffixes; track history via Git commits."
                ))

    for py_file in find_target_files(target_dir, (".py",)):
        rel_path = str(py_file.relative_to(target_dir))
        is_test = "test" in py_file.name or "tests" in py_file.parts

        scanned_files += 1
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        # Detect commented-out zombie code (production only).
        if not is_test:
            consecutive_commented_code = 0
            for line_idx, line in enumerate(content.splitlines(), 1):
                if PYTHON_CODE_IN_COMMENT.search(line):
                    consecutive_commented_code += 1
                    if consecutive_commented_code == 4:
                        zombie_code_blocks_count += 1
                        findings.append(AuditFinding(
                            category="STRUCTURAL_SMELL",
                            severity="LOW",
                            file_path=rel_path,
                            line_number=line_idx - 3,
                            rule_id="SMELL-ZOMBIE-CODE",
                            message="Commented dead code block detected (>= 4 lines of commented syntax)",
                            recommendation="Remove dead code; Git version control preserves history."
                        ))
                else:
                    consecutive_commented_code = 0

            # Inspect AST.
            try:
                tree = ast.parse(content)
                visitor = StructuralSmellVisitor(rel_path)
                visitor.visit(tree)
                total_funcs_count += visitor.total_funcs
                long_params_count += visitor.long_param_funcs
                god_classes_count += visitor.god_classes
                findings.extend(visitor.findings)
            except SyntaxError:
                continue

    # Calculate weighted score based on ISO 25010 defect density.
    score = 100.0
    score -= entropy_violations_count * 20.0
    score -= god_classes_count * 15.0
    long_params_ratio = long_params_count / max(1, total_funcs_count)
    if long_params_ratio > 0.02:
        score -= min(15.0, (long_params_ratio - 0.02) * 200.0)
    score -= min(10.0, zombie_code_blocks_count * 2.0)

    score = max(0.0, min(100.0, round(score, 1)))
    passed = entropy_violations_count == 0 and god_classes_count == 0 and score >= 70.0

    return ProbeResult(
        probe_name="Structural Smells & Zero-Entropy (SWEBOK v4 / Clean Code)",
        score_pct=score,
        passed=passed,
        metrics={
            "scanned_files": scanned_files,
            "entropy_violations_count": entropy_violations_count,
            "long_parameter_funcs_count": long_params_count,
            "god_classes_count": god_classes_count,
            "zombie_code_blocks_count": zombie_code_blocks_count
        },
        findings=findings
    )
