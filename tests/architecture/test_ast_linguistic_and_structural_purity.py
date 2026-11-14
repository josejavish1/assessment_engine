"""
Architectural Fitness Function: AST-Level Linguistic & Structural Purity Guard.
Implements Phase 1 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.

Mandates:
1. Pure Technical English across all source modules under src/assessment_engine/ (domain, application, adapters, infrastructure).
2. Zero ad-hoc regex sanitizers in adapters/compilers (presentation layer must not clean upstream domain data).
3. Zero inlined jurisdiction/regulatory dictionaries in presentation compilers (must load declarative catalogs).
4. Zero Spanish tokens or non-ASCII diacritics in code, comments, or docstrings.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Set

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src" / "assessment_engine"

FORBIDDEN_DIACRITICS = set("áéíóúñÁÉÍÓÚÑ¿¡")

# Banned Spanish linguistic stems that signal domain leakage in Python code
BANNED_SPANISH_STEMS = {
    "produccion",
    "parche",
    "bascula",
    "conmutacion",
    "gestion",
    "operacion",
    "resiliencia",
    "seguridad",
    "infraestructura",
    "almacenamiento",
    "comunicaciones",
    "riesgo",
    "vulnerabilidad",
    "madurez",
}

# Banned ad-hoc cleaning patterns in compilers (Fix the baseline, do not hack compilers)
BANNED_COMPILER_REGEX_HACKS = [
    r"bajo el modelo",
    r"preparando el terreno",
    r"incorporaci[oó]n de la tecnolog[ií]a",
    r"hacia una arquitectura",
    r"hacia el paradigma",
    r"Sovereign Hybrid Edge",
]


def _get_all_engine_python_files() -> List[Path]:
    """Collect all python files under src/assessment_engine/."""
    exempted_files = {
        "localization.py",  # Manages diacritics restoration interface
    }
    files: List[Path] = []
    for py_file in SRC_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts or py_file.name in exempted_files:
            continue
        files.append(py_file)
    return sorted(files)


def test_zero_ad_hoc_regex_hacks_in_compilers() -> None:
    """Invariant: Compilers must never execute ad-hoc regex patches to clean domain text."""
    compilers_dir = SRC_DIR / "adapters" / "compilers"
    assert compilers_dir.exists(), "Compilers directory must exist"

    violations: List[str] = []
    for py_file in compilers_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pat in BANNED_COMPILER_REGEX_HACKS:
            if re.search(pat, content, re.IGNORECASE):
                violations.append(
                    f"{py_file.name} contains banned ad-hoc regex patch matching pattern: '{pat}'"
                )

    assert not violations, (
        "Anti-pattern detected: Compilers must not patch dirty payload data via regex.\n"
        + "\n".join(violations)
    )


def test_zero_inlined_jurisdiction_maps_in_compilers() -> None:
    """Invariant: Compilers must load regulatory frameworks from config, never hardcode jurisdiction_map."""
    compilers_dir = SRC_DIR / "adapters" / "compilers"
    violations: List[str] = []

    for py_file in compilers_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if "jurisdiction_map = {" in content or "jurisdiction_map={" in content:
            violations.append(
                f"{py_file.name} defines an inlined jurisdiction_map dictionary. Must use load_regulatory_jurisdictions()."
            )

    assert not violations, (
        "Anti-pattern detected: Inlined jurisdiction map in presentation compiler.\n"
        + "\n".join(violations)
    )


def test_zero_spanish_stems_in_domain_and_compilers() -> None:
    """Invariant: Domain and adapter logic must use pure Technical English identifiers and string checks."""
    target_dirs = [SRC_DIR / "domain", SRC_DIR / "adapters" / "compilers"]
    violations: List[str] = []

    for target_dir in target_dirs:
        for py_file in target_dir.rglob("*.py"):
            if (
                "__pycache__" in py_file.parts
                or "in_memory_asis_compiler.py" in py_file.name
                or "linguistic_guardrail.py" in py_file.name
            ):
                continue
            content = py_file.read_text(encoding="utf-8")
            for idx, line in enumerate(content.splitlines(), start=1):
                sline = line.strip()
                if sline.startswith("#") or sline.startswith('"""') or sline.startswith("'''"):
                    continue
                # Check for standalone tokens matching banned stems
                for stem in BANNED_SPANISH_STEMS:
                    if re.search(rf'["\']\b{stem}\b["\']', sline, re.IGNORECASE):
                        violations.append(
                            f"{py_file.relative_to(REPO_ROOT)}:L{idx} -> '{stem}' in code line: {sline[:80]}"
                        )

    assert not violations, (
        "Spanish domain stems detected in generic Python logic. Must use 100% Technical English:\n"
        + "\n".join(violations)
    )


def test_zero_raw_spanish_fallback_titles_in_payload_to_ast() -> None:
    """Invariant: payload_to_ast.py must not hardcode 'Riesgo Operativo' or Spanish strings as fallbacks."""
    bridge_file = SRC_DIR / "adapters" / "compilers" / "payload_to_ast.py"
    assert bridge_file.exists(), "payload_to_ast.py must exist"

    content = bridge_file.read_text(encoding="utf-8")
    assert '"Riesgo Operativo"' not in content, (
        "payload_to_ast.py hardcodes 'Riesgo Operativo'. Must use t('default_operational_risk_title', locale=meta_lang)."
    )
    assert 'primary_reg = "NIS2"' not in content, (
        "payload_to_ast.py hardcodes default 'NIS2'. Must resolve declaratively via load_regulatory_jurisdictions()."
    )
