"""CI/CD Linter for Multilingual Ontology Completeness.

Enforces that every capability (KPI) defined across all 10 technology towers in the
multilingual taxonomy catalog possesses a valid, non-empty translation for every
officially supported locale in the system (e.g., 'es', 'en', 'pt', 'fr', 'de', 'ja').
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TAXONOMY_FILE = REPO_ROOT / "engine_config" / "taxonomy_multilingual.json"

# The official locales supported by the assessment platform
SUPPORTED_LOCALES = ["en", "es", "pt", "fr", "de", "ja"]


def test_taxonomy_file_exists() -> None:
    assert TAXONOMY_FILE.exists(), f"Taxonomy file missing: {TAXONOMY_FILE}"


def load_taxonomy() -> Dict[str, Any]:
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_all_10_towers_present() -> None:
    tax = load_taxonomy()
    for t_idx in range(1, 11):
        t_key = f"T{t_idx}"
        assert t_key in tax, f"Missing tower definition for {t_key} in taxonomy."


def test_multilingual_kpi_completeness() -> None:
    tax = load_taxonomy()
    errors = []

    for t_idx in range(1, 11):
        t_key = f"T{t_idx}"
        t_data = tax.get(t_key, {})
        pillars = t_data.get("pillars", {})

        for pid, pdata in pillars.items():
            kpis = pdata.get("kpis", {})
            for kid, kdata in kpis.items():
                locales = kdata.get("locales", {})
                
                # Check each supported locale
                for locale in SUPPORTED_LOCALES:
                    translation = locales.get(locale)
                    if not translation or not str(translation).strip():
                        errors.append(f"Missing '{locale}' translation for KPI {kid} in {t_key}")

    if errors:
        error_msg = f"Found {len(errors)} multilingual ontology completeness gaps:\n" + "\n".join(errors[:10])
        if len(errors) > 10:
            error_msg += f"\n...and {len(errors) - 10} more."
        pytest.fail(error_msg)
