# golden-path: ignore
"""Unit Test Suite for Soverik Quality Engine in Assessment Engine.

Verifies universal project scanning, multi-probe execution, AST Taint Tracking, Shannon Entropy,
Cognitive Complexity, CycloneDX SBOM, Copyleft Licenses, GDPR, WCAG Accessibility,
Contract Drift, Resilience Timeouts, Code Hygiene, and Structural Smells.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.infrastructure.auditor.probes.ai_safety_llm import run_ai_safety_llm_probe
from assessment_engine.infrastructure.auditor.probes.ast_complexity import run_ast_complexity_probe
from assessment_engine.infrastructure.auditor.probes.browser_accessibility import run_browser_accessibility_probe
from assessment_engine.infrastructure.auditor.probes.code_hygiene import run_code_hygiene_probe
from assessment_engine.infrastructure.auditor.probes.contract_drift import run_contract_drift_probe
from assessment_engine.infrastructure.auditor.probes.legal_compliance import run_legal_compliance_probe
from assessment_engine.infrastructure.auditor.probes.performance_finops import run_performance_finops_probe
from assessment_engine.infrastructure.auditor.probes.resilience_chaos import run_resilience_chaos_probe
from assessment_engine.infrastructure.auditor.probes.security_sast import (
    calculate_shannon_entropy,
    is_high_entropy_secret,
    run_security_sast_probe,
)
from assessment_engine.infrastructure.auditor.probes.structural_smells import run_structural_smells_probe
from assessment_engine.infrastructure.auditor.probes.supply_chain import (
    generate_cyclonedx_sbom,
    run_supply_chain_probe,
)
from assessment_engine.infrastructure.auditor.scanner import SoverikQualityEngine, quality_engine


def test_shannon_entropy_calculation() -> None:
    assert calculate_shannon_entropy("aaaaaaaaaaaaaaaaaaaa") < 1.0
    assert 2.0 <= calculate_shannon_entropy("esta es una descripcion en lenguaje normal") <= 3.9
    hex_key = "9f8a3c2b1e4d5a6b7c8d9e0f1a2b3c4d"
    assert calculate_shannon_entropy(hex_key) >= 3.6
    assert is_high_entropy_secret(hex_key) is True
    assert is_high_entropy_secret("Descripción comercial para la tienda online") is False


def test_universal_auditor_clean_project(tmp_path: Path) -> None:
    ws_dir = tmp_path / "mock_clean_project"
    ws_dir.mkdir(parents=True, exist_ok=True)

    src_dir = ws_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "math_service.py").write_text(
        '"""Módulo de cálculo matemático limpio."""\n\n'
        "def add_numbers(a: int, b: int) -> int:\n"
        '    """Suma dos números enteros."""\n'
        "    return a + b\n",
        encoding="utf-8",
    )

    test_dir = ws_dir / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "test_math.py").write_text(
        "from src.math_service import add_numbers\n\n"
        "def test_add():\n"
        "    assert add_numbers(2, 3) == 5\n",
        encoding="utf-8",
    )

    (ws_dir / "requirements.txt").write_text("fastapi==0.110.0\nuvicorn==0.28.0\n", encoding="utf-8")
    (ws_dir / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    report = quality_engine.audit_project(ws_dir, project_name="MockCleanSaaS")

    assert report.project_name == "MockCleanSaaS"
    assert report.global_score >= 80.0
    assert report.global_grade in ("A+", "A")
    assert "security_sast" in report.probes
    assert "security_dast" in report.probes
    assert "ast_complexity" in report.probes
    assert "supply_chain" in report.probes
    assert "legal_compliance" in report.probes
    assert "performance_finops" in report.probes
    assert "browser_accessibility" in report.probes
    assert "contract_drift" in report.probes
    assert "resilience_chaos" in report.probes
    assert "ai_safety_llm" in report.probes
    assert "code_hygiene" in report.probes
    assert "structural_smells" in report.probes

    audit_dir = ws_dir / "docs" / "audits"
    assert (audit_dir / "AUDIT_REPORT.json").exists()
    assert (audit_dir / "AUDIT_CERTIFICATE.html").exists()

    report_dict = json.loads((audit_dir / "AUDIT_REPORT.json").read_text(encoding="utf-8"))
    assert report_dict["project_name"] == "MockCleanSaaS"


def test_ast_taint_tracking_detects_all_sqli_and_dangerous_calls(tmp_path: Path) -> None:
    ws_dir = tmp_path / "mock_taint_project"
    ws_dir.mkdir(parents=True, exist_ok=True)

    (ws_dir / "bad_backend.py").write_text(
        "import os\n"
        "import sqlite3\n"
        "import pickle\n\n"
        'conn = sqlite3.connect(":memory:")\n'
        "cur = conn.cursor()\n\n"
        "def vuln_queries(table, user_id, raw_data):\n"
        '    cur.execute("SELECT * FROM " + table)\n'
        '    cur.execute("SELECT * FROM users WHERE id = {}".format(user_id))\n'
        '    os.system("echo " + user_id)\n'
        "    eval(user_id)\n"
        "    pickle.loads(raw_data)\n",
        encoding="utf-8",
    )

    probe_res = run_security_sast_probe(ws_dir)
    assert probe_res.passed is False

    rule_ids = {f.rule_id for f in probe_res.findings}
    assert "CWE-89-SQLI-CONCAT" in rule_ids
    assert "CWE-89-SQLI-STR-FORMAT" in rule_ids
    assert "CWE-78-OS-SYSTEM" in rule_ids
    assert "CWE-94-CODE-INJECTION" in rule_ids
    assert "CWE-502-DESERIALIZATION" in rule_ids


def test_universal_auditor_detects_sqli_and_secret(tmp_path: Path) -> None:
    ws_dir = tmp_path / "mock_vulnerable_project"
    ws_dir.mkdir(parents=True, exist_ok=True)

    dummy_stripe = "sk_" + "live_" + "12345678901234567890123456"
    (ws_dir / "vuln.py").write_text(
        'user_id = "123"\n'
        'query = f"SELECT * FROM users WHERE id = {user_id}"\n'
        f'stripe_key = "{dummy_stripe}"\n'
        'generic_hex_secret = "9f8a3c2b1e4d5a6b7c8d9e0f1a2b3c4d"\n',
        encoding="utf-8",
    )

    engine = SoverikQualityEngine()
    report = engine.audit_project(ws_dir, project_name="VulnProject")

    assert report.global_grade in ("C", "F")
    assert report.probes["security_sast"].passed is False

    finding_rules = [f.rule_id for f in report.probes["security_sast"].findings]
    assert any("SQLI" in r for r in finding_rules)
    assert "CWE-798-SECRET-LEAK" in finding_rules
    assert "CWE-798-HIGH-ENTROPY-SECRET" in finding_rules


def test_cognitive_complexity_and_deep_nesting(tmp_path: Path) -> None:
    ws_dir = tmp_path / "mock_complex_project"
    ws_dir.mkdir(parents=True, exist_ok=True)

    (ws_dir / "deep_logic.py").write_text(
        "def process_deep(data):\n"
        "    for item in data:\n"
        "        if item > 0:\n"
        "            for sub in range(item):\n"
        "                if sub % 2 == 0:\n"
        "                    print(sub)\n",
        encoding="utf-8",
    )

    res = run_ast_complexity_probe(ws_dir)
    assert res.score_pct < 100.0
