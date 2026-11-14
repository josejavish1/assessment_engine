"""Architectural Fitness Function: Enforces Zero Brand and Client Specific Hardcoding.

Mandates:
1. Pure Technical English across all source code in src/.
2. Zero client-specific nouns (e.g. 'prenet', 'molins', 'bascula', 'horno', 'camiones', 'albaranes') in generic code and canonical configs.
3. Zero proprietary brand tokens (e.g. 'vesda', 'simplivity', 'netapp') in generic taxonomy, progression matrix, and policy files.
4. Zero canned consulting prose dictionaries mapping towers to pre-baked paragraph templates.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src" / "assessment_engine"
CONFIG_DIR = REPO_ROOT / "engine_config"

BANNED_CLIENT_AND_CEMENT_TOKENS = [
    r"\bprenet\b",
    r"\bhorno\b",
    r"\bhormig[oó]n\b",
    r"\bb[aá]scula\b",
    r"\bweighbridge\b",
    r"\bcamion(?:es)?\b",
    r"\balbar[aá]n(?:es)?\b",
    r"\bcantera(?:s)?\b",
    r"\bclinker\b",
]

BANNED_GENERIC_BRAND_TOKENS = [
    r"\bvesda\b",
    r"\bsimplivity\b",
    r"\bnetapp\b",
]


def test_no_client_or_cement_tokens_in_generic_source_code() -> None:
    """Verifies that no client or cement plant tokens leak into generic engine code."""
    violations: list[str] = []

    exempted_files = {
        "financial_profile.py",
        "executive_summary_ast.py",
        "config_loader.py",
        "hardcoded_artifacts.py",
    }

    for py_file in SRC_DIR.rglob("*.py"):
        if py_file.name in exempted_files or "__pycache__" in py_file.parts or "probes" in py_file.parts:
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for pat_str in BANNED_CLIENT_AND_CEMENT_TOKENS:
            pat = re.compile(pat_str, re.IGNORECASE)
            for idx, line in enumerate(content.splitlines(), start=1):
                sline = line.strip()
                if sline.startswith("#") or sline.startswith('"""') or sline.startswith("'''"):
                    continue
                if pat.search(sline):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}:L{idx} -> {sline}")

    assert not violations, "Client/Cement specific tokens detected in generic source code:\n" + "\n".join(violations)


def test_no_banned_tokens_in_locales() -> None:
    """Verifies that locales.json contains zero canned client/cement stories."""
    locales_path = CONFIG_DIR / "locales.json"
    assert locales_path.exists(), "locales.json missing."

    content = locales_path.read_text(encoding="utf-8")
    violations: list[str] = []

    for pat_str in BANNED_CLIENT_AND_CEMENT_TOKENS:
        pat = re.compile(pat_str, re.IGNORECASE)
        for idx, line in enumerate(content.splitlines(), start=1):
            if pat.search(line):
                violations.append(f"locales.json:L{idx} -> {line.strip()}")

    assert not violations, "Canned client/cement tokens detected in locales.json:\n" + "\n".join(violations)


def test_no_banned_tokens_in_cross_domain_nexus_map() -> None:
    """Verifies that cross_domain_nexus_map.json contains zero brands or client specifics."""
    nexus_path = CONFIG_DIR / "policies" / "cross_domain_nexus_map.json"
    assert nexus_path.exists(), "cross_domain_nexus_map.json missing."

    content = nexus_path.read_text(encoding="utf-8")
    violations: list[str] = []

    for pat_str in BANNED_CLIENT_AND_CEMENT_TOKENS + BANNED_GENERIC_BRAND_TOKENS:
        pat = re.compile(pat_str, re.IGNORECASE)
        for idx, line in enumerate(content.splitlines(), start=1):
            if pat.search(line):
                violations.append(f"cross_domain_nexus_map.json:L{idx} -> {line.strip()}")

    assert not violations, "Banned tokens detected in cross_domain_nexus_map.json:\n" + "\n".join(violations)


def test_no_vesda_in_canonical_taxonomy_and_configs() -> None:
    """Verifies that the proprietary brand VESDA is never hardcoded in canonical config files."""
    violations: list[str] = []

    target_configs = [
        CONFIG_DIR / "taxonomy_multilingual.json",
        CONFIG_DIR / "questions_multilingual.json",
        CONFIG_DIR / "policies" / "cmmi_progression_matrix.json",
        CONFIG_DIR / "abbreviations_glossary.json",
        CONFIG_DIR / "towers" / "T1" / "tower_definition_T1.json",
    ]

    for cfg_file in target_configs:
        if not cfg_file.exists():
            continue
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception:
            continue

        pat = re.compile(r"\bvesda\b", re.IGNORECASE)
        for idx, line in enumerate(content.splitlines(), start=1):
            if pat.search(line):
                violations.append(f"{cfg_file.relative_to(REPO_ROOT)}:L{idx} -> {line.strip()}")

    assert not violations, "Proprietary brand VESDA detected in canonical config files:\n" + "\n".join(violations)


def test_no_client_tokens_in_topology_rules() -> None:
    """Verifies that global topology classification rules contain zero client-specific tokens."""
    rules_path = CONFIG_DIR / "topology_classification_rules.yaml"
    assert rules_path.exists(), "topology_classification_rules.yaml missing."

    content = rules_path.read_text(encoding="utf-8")
    violations: list[str] = []

    for pat_str in BANNED_CLIENT_AND_CEMENT_TOKENS:
        pat = re.compile(pat_str, re.IGNORECASE)
        for idx, line in enumerate(content.splitlines(), start=1):
            if pat.search(line):
                violations.append(f"{rules_path.relative_to(REPO_ROOT)}:L{idx} -> {line.strip()}")

    assert not violations, "Client-specific terms found in topology_classification_rules.yaml:\n" + "\n".join(violations)


def test_no_canned_tower_prose_dictionaries_in_src() -> None:
    """AST Linter Invariant: Prohibits dictionaries mapping towers (T1-T10) to canned consulting paragraphs."""
    tower_keys = {"T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"}
    violations: list[str] = []

    for py_path in SRC_DIR.rglob("*.py"):
        # Exempt vector embedding anchors in router and test mock probes
        if "__pycache__" in py_path.parts or py_path.name in ("semantic_epistemic_router.py", "generate_smoke_data.py"):
            continue
        try:
            tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                has_tower = any(
                    isinstance(k, ast.Constant) and str(k.value) in tower_keys
                    for k in node.keys
                    if k is not None
                )
                if has_tower:
                    canned_vals = [
                        v.value
                        for v in node.values
                        if isinstance(v, ast.Constant) and isinstance(v.value, str) and len(v.value.strip()) > 140 and "." in v.value
                    ]
                    if canned_vals:
                        violations.append(f"{py_path.relative_to(REPO_ROOT)}:L{node.lineno} -> {canned_vals[0][:60]}...")

    assert not violations, "Canned consulting prose dictionaries detected in source code:\n" + "\n".join(violations)
