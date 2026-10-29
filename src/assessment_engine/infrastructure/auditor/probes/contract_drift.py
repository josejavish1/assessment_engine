"""
Audit contract integrity and schema drift for OpenAPI 3.1, Pydantic v2, and DDL sync. Implement:
- Drift detection between SQLite schema (DDL) and in-code SQL statements (CWE-404 / OperationalError).
- Strictness auditing in Pydantic models (prohibition of loose 'Any' types).
- Existence and version verification of the OpenAPI / Domain Contract.
"""
from __future__ import annotations

import ast
import re
import sqlite3
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive"
}

CREATE_TABLE_REGEX = re.compile(
    r"""(?i)CREATE\s+(?:VIRTUAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)(?:\s+USING\s+[a-zA-Z0-9_]+)?\s*\((.*?)\);""",
    re.DOTALL
)

INSERT_INTO_REGEX = re.compile(
    r"""(?i)INSERT\s+INTO\s+([a-zA-Z0-9_]+)\s*\((.*?)\)""",
    re.DOTALL
)


def extract_ddl_schemas(target_dir: Path) -> dict[str, set[str]]:
    """Extract table and column structures declared in DDL or SQLite databases."""
    table_schemas: dict[str, set[str]] = {}

    # 1. Extract from physical SQLite files (.db) if they exist
    for db_file in find_target_files(target_dir, (".db",)):
        try:
            conn = sqlite3.connect(str(db_file), timeout=2.0)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]
            for t in tables:
                cur.execute(f"PRAGMA table_info('{t}');")
                cols = {r[1].lower() for r in cur.fetchall()}
                table_schemas[t.lower()] = cols
            conn.close()
        except sqlite3.Error:
            pass

    # 2. Extract from Python code (CREATE TABLE strings)
    for py_file in find_target_files(target_dir, (".py",)):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for match in CREATE_TABLE_REGEX.finditer(content):
                table_name = match.group(1).lower().strip()
                body = match.group(2)
                cols: set[str] = set()
                body_clean = re.sub(r"--.*$", "", body, flags=re.MULTILINE)
                for line in body_clean.split(","):
                    clean_line = line.strip()
                    if not clean_line or clean_line.upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "CHECK")):
                        continue
                    first_token = clean_line.split()[0].replace('"', '').replace("'", "").lower()
                    if first_token:
                        cols.add(first_token)
                if table_name not in table_schemas:
                    table_schemas[table_name] = cols
                else:
                    table_schemas[table_name].update(cols)
        except OSError:
            pass

    return table_schemas


class PydanticModelVisitor(ast.NodeVisitor):
    """Inspect Pydantic classes to verify the absence of loose 'Any' types."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.findings: list[AuditFinding] = []
        self.model_count = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition node."""
        is_pydantic = any(
            (isinstance(b, ast.Name) and b.id in ("BaseModel", "Schema")) or
            (isinstance(b, ast.Attribute) and b.attr == "BaseModel")
            for b in node.bases
        )

        if is_pydantic:
            self.model_count += 1
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    # Detect usage of 'Any'
                    ann = item.annotation
                    is_any = (isinstance(ann, ast.Name) and ann.id == "Any") or (
                        isinstance(ann, ast.Attribute) and ann.attr == "Any"
                    )
                    if is_any:
                        self.findings.append(AuditFinding(
                            category="CONTRACT_DRIFT",
                            severity="MEDIUM",
                            file_path=self.rel_path,
                            line_number=item.lineno,
                            rule_id="DRIFT-LOOSE-TYPE-ANY",
                            message=f"Modelo Pydantic '{node.name}' declara campo '{field_name}: Any' sin tipado estricto",
                            recommendation="Definir tipo primitivo estricto (str, int, float, bool) o submodelo para OpenAPI 3.1."
                        ))

        self.generic_visit(node)


def run_contract_drift_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive audit of schema consistency and OpenAPI contracts."""
    findings: list[AuditFinding] = []
    table_schemas = extract_ddl_schemas(target_dir)

    total_models = 0
    drift_violations_count = 0

    # 1. Audit INSERT INTO queries in Python code against the DDL schema
    for py_file in find_target_files(target_dir, (".py",)):
        rel_path = str(py_file.relative_to(target_dir))
        is_test = "test" in py_file.name or "tests" in py_file.parts
        if is_test:
            continue

        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")

            for match in INSERT_INTO_REGEX.finditer(content):
                table_name = match.group(1).lower().strip()
                columns_part = match.group(2)
                inserted_cols = [c.replace('\\n', ' ').replace('\\r', ' ').strip().replace('"', '').replace("'", "").lower() for c in columns_part.split(",") if c.strip()]

                if table_name in table_schemas:
                    known_cols = table_schemas[table_name]
                    for col in inserted_cols:
                        if col and col not in known_cols:
                            drift_violations_count += 1
                            lineno = content[:match.start()].count("\n") + 1
                            findings.append(AuditFinding(
                                category="CONTRACT_DRIFT",
                                severity="CRITICAL",
                                file_path=rel_path,
                                line_number=lineno,
                                rule_id="DRIFT-COLUMN-MISMATCH",
                                message=f"Schema Drift: Column '{col}' referenced in INSERT missing from table '{table_name}'",
                                recommendation=f"Add '{col}' to table '{table_name}' in SQLite or correct SQL statement."
                            ))

            tree = ast.parse(content)
            visitor = PydanticModelVisitor(rel_path)
            visitor.visit(tree)
            total_models += visitor.model_count
            findings.extend(visitor.findings)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

    has_versioned_contract = (
        (target_dir / "docs" / "DOMAIN_CONTRACT.json").exists() or
        (target_dir / "docs" / "openapi.json").exists() or
        (target_dir / "docs" / "schema.json").exists()
    )

    if not has_versioned_contract and total_models > 0:
        findings.append(AuditFinding(
            category="CONTRACT_DRIFT",
            severity="LOW",
            file_path="docs/",
            line_number=None,
            rule_id="DRIFT-NO-VERSIONED-CONTRACT",
            message="Versioned OpenAPI/Domain Contract missing from docs/ (e.g. openapi.json)",
            recommendation="Export and version formal API contract to ensure frontend/backend synchronization."
        ))

    score = 100.0
    score -= drift_violations_count * 25.0
    for f in findings:
        if f.rule_id == "DRIFT-LOOSE-TYPE-ANY":
            score -= 5.0
        elif f.rule_id == "DRIFT-NO-VERSIONED-CONTRACT":
            score -= 5.0

    score = max(0.0, min(100.0, round(score, 1)))
    passed = drift_violations_count == 0 and score >= 75.0

    return ProbeResult(
        probe_name="Contract Integrity & Schema Drift (OpenAPI 3.1 / Pydantic)",
        score_pct=score,
        passed=passed,
        metrics={
            "ddl_tables_indexed": len(table_schemas),
            "pydantic_models_audited": total_models,
            "drift_violations_count": drift_violations_count,
            "has_versioned_contract": has_versioned_contract
        },
        findings=findings
    )
