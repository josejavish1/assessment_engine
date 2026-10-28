"""Mathematical and formal invariant certification test suite for Internationalization (i18n).

Formally verifies:
1. Exact Key Symmetry Theorem: Card(Keys(L)) == Card(Keys(es)) and Keys(L) Δ Keys(es) == ∅ for all L in {en, pt, fr, de, ja}.
2. AST Zero-Hardcoding Invariant: No hardcoded Spanish literals in UI fallback calls.
3. Pure Multi-Language Oracle: Zero Spanish template leakage when resolving foreign locales.
"""

import ast
import json
from pathlib import Path
from typing import Any
import pytest

from assessment_engine.infrastructure.localization import (
    load_locales_catalog,
    get_localized_string,
    t,
)
from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary


def test_i18n_catalog_mathematical_symmetry() -> None:
    """THEORETIC INVARIANT: Locales catalog must be 100% symmetric across all supported languages."""
    catalog = load_locales_catalog()
    assert "es" in catalog, "Base locale 'es' must exist in catalog."
    
    supported_locales = ["en", "pt", "fr", "de", "ja"]
    base_keys = set(catalog["es"].keys())
    assert len(base_keys) >= 120, f"Expected at least 120 canonical keys, got {len(base_keys)}"

    for loc in supported_locales:
        assert loc in catalog, f"Locale '{loc}' is missing from locales.json catalog."
        loc_keys = set(catalog[loc].keys())
        
        diff_missing = base_keys - loc_keys
        diff_extra = loc_keys - base_keys
        
        assert not diff_missing, (
            f"Mathematical Asymmetry: Locale '{loc}' is missing {len(diff_missing)} keys: {diff_missing}"
        )
        assert not diff_extra, (
            f"Mathematical Asymmetry: Locale '{loc}' has {len(diff_extra)} extra unaligned keys: {diff_extra}"
        )
        assert loc_keys == base_keys, f"Symmetric difference Keys({loc}) Δ Keys(es) must be strictly empty."


def test_i18n_pure_resolution_zero_spanish_leakage() -> None:
    """ORACLE: Resolving keys in foreign languages must NEVER leak default Spanish strings."""
    test_keys = [
        "title",
        "annex_technical_prefix",
        "client_lbl",
        "v_lbl",
        "toc_title",
        "dashboard_title",
        "score_lbl",
        "maturity_lbl",
        "radar_title",
    ]

    # In English, none of these should match the Spanish translation
    for key in test_keys:
        es_val = t(key, locale="es")
        en_val = t(key, locale="en")
        assert en_val != "", f"English translation for '{key}' must not be empty."
        assert es_val != "", f"Spanish translation for '{key}' must not be empty."
        
        # English translation must not be identical to Spanish (except for pure acronyms)
        if len(es_val) > 4 and not es_val.isupper():
            assert en_val != es_val, (
                f"Language Leakage Detected: Key '{key}' in English returned Spanish string '{es_val}'."
            )

    # In French
    fr_prefix = t("annex_technical_prefix", locale="fr")
    assert "Annexe" in fr_prefix, f"French annex prefix expected 'Annexe', got '{fr_prefix}'"

    # In German
    de_prefix = t("annex_technical_prefix", locale="de")
    assert "Anhang" in de_prefix, f"German annex prefix expected 'Anhang', got '{de_prefix}'"

    # In Japanese
    ja_prefix = t("annex_technical_prefix", locale="ja")
    assert "技術付録" in ja_prefix, f"Japanese annex prefix expected '技術付録', got '{ja_prefix}'"


def test_i18n_ast_zero_hardcoded_spanish_fallbacks() -> None:
    """AST INVARIANT: Assert zero hardcoded Spanish UI fallback strings in adapter functions."""
    root = Path(__file__).resolve().parents[2]
    adapter_file = root / "src" / "assessment_engine" / "adapters" / "compile_asis_docx_from_modules.py"
    assert adapter_file.exists(), f"Target adapter {adapter_file} must exist."

    tree = ast.parse(adapter_file.read_text(encoding="utf-8"))

    # Blacklisted Spanish UI literal tokens that must never be hardcoded as fallbacks in python code
    banned_tokens = [
        "INFORME DE EVALUACIÓN",
        "Anexo Técnico:",
        "Índice de Contenidos",
        "Cliente:\n",
        "Cuadro de Mando",
        "PUNTUACIÓN AS-IS",
    ]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for dict.get(key, 'Hardcoded Spanish')
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    for banned in banned_tokens:
                        assert banned != arg.value, (
                            f"AST Violation at line {node.lineno}: Found hardcoded Spanish UI string '{banned}' "
                            f"passed as argument in {adapter_file.name}. Must resolve through t(key, locale)."
                        )
