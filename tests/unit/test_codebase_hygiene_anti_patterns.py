"""Automated Governance & Hygiene Test Suite.

Prevents technical debt, hardcoded magic numbers, client/brand leaks, and language guessing.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


def test_no_hardcoded_consulting_brands() -> None:
    """ASSERTS that zero legacy consulting brands (NTT DATA, Everis) are hardcoded in src/."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    banned_brands = [r"\bNTT DATA\b", r"\bEveris\b", r"\bWhyNttData\b"]
    
    violations = []
    for p in root.rglob("*.py"):
        # Skip audit probes and tests
        if "auditor" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            if sline.startswith("#"):
                continue
            for pat in banned_brands:
                if re.search(pat, sline, re.IGNORECASE):
                    violations.append(f"{p.relative_to(root)}:L{idx} -> {sline}")

    assert not violations, f"Found hardcoded consulting brands in codebase:\n" + "\n".join(violations)


def test_no_currency_guessing_by_language() -> None:
    """ASSERTS that no file guesses currency based on whether doc_lang == 'es'."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    bad_patterns = [
        r'currency\s*=\s*["\']€["\']\s+if\s+doc_lang\s*==\s*["\']es["\']',
        r'if\s+doc_lang\s*==\s*["\']es["\']:\s*currency\s*=\s*["\']€["\']',
    ]

    violations = []
    for p in root.rglob("*.py"):
        if "auditor" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            for pat in bad_patterns:
                if re.search(pat, sline):
                    violations.append(f"{p.relative_to(root)}:L{idx} -> {sline}")

    assert not violations, f"Found currency guessing by language antipattern:\n" + "\n".join(violations)


def test_no_hardcoded_client_entities_in_prompts() -> None:
    """ASSERTS that generic prompts do not contain specific client names or plant locations."""
    prompts_dir = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "domain" / "prompts"
    banned_entities = [r"\bmolins\b", r"\bsecil\b", r"\bsant vicen[çc]\b"]

    violations = []
    for p in prompts_dir.rglob("*.yaml"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            for pat in banned_entities:
                if re.search(pat, sline, re.IGNORECASE):
                    violations.append(f"{p.name}:L{idx} -> {sline}")

    assert not violations, f"Found client-specific entities in generic prompts:\n" + "\n".join(violations)


def test_no_raw_tower_dictionaries_in_global_payload_builder() -> None:
    """ASSERTS that build_global_report_payload does not contain hardcoded Spanish tower maps."""
    p = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "application" / "build_global_report_payload.py"
    text = p.read_text(encoding="utf-8")
    assert "TOWER_NAMES_MAP" not in text, "Found legacy hardcoded TOWER_NAMES_MAP in build_global_report_payload.py"
    assert "TOWER_CRITICAL_DECISIONS" not in text, "Found legacy hardcoded TOWER_CRITICAL_DECISIONS in build_global_report_payload.py"


def test_no_spanish_in_yaml_prompts_registry() -> None:
    """ASSERTS that all YAML prompts in registry are 100% technical English."""
    prompts_dir = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "domain" / "prompts" / "registry"
    spanish_char_pattern = re.compile(r'[\"\'][^\"\'\n]*[áéíóúÁÉÍÓÚñÑ¿¡][^\"\'\n]*[\"\']')

    violations = []
    for y in sorted(prompts_dir.glob("*.yaml")):
        for idx, l in enumerate(y.read_text(encoding="utf-8").splitlines(), 1):
            if spanish_char_pattern.search(l) and "CLICH" not in l.upper():
                violations.append(f"{y.name}:L{idx} -> {l.strip()}")

    assert not violations, f"Found Spanish sentences in YAML prompts:\n" + "\n".join(violations)


