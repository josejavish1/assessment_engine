"""Unit tests for RFC 074: Executive Actuarial Realism, Single-Incident Transparency & Chapter 1/3 Governance."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")
REQUIRED_INTERPOLATION_VARS_CH1 = {
    "formatted_ale",
    "worst_incident_cost",
    "worst_incident_code",
    "worst_incident_domain",
    "formatted_p90",
}
REQUIRED_INTERPOLATION_VARS_FOOTNOTE = {
    "worst_incident_cost",
    "worst_incident_code",
    "worst_incident_domain",
    "formatted_p90",
}


@pytest.fixture
def locales_catalog() -> Dict[str, Any]:
    """Loads the canonical locales catalog."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    with open(locales_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_rfc074_table3_header_sanitation_no_p95(locales_catalog: Dict[str, Any]) -> None:
    """Quality Gate: Assert (P95) acronym is completely eradicated from Table 3 header across all 6 locales."""
    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog, f"Missing locale {locale}"
        col_header = locales_catalog[locale].get("tomo_ch3_table4_col_severe_event", "")
        assert "P95" not in col_header, f"Jargon '(P95)' still present in locale '{locale}': {col_header}"
        assert len(col_header.strip()) > 5, f"Header too short in locale '{locale}'"


def test_rfc074_ch1_p3_placeholder_symmetry(locales_catalog: Dict[str, Any]) -> None:
    """Quality Gate: Assert exact placeholder symmetry in Chapter 1 economic paragraph across all 6 locales."""
    placeholder_regex = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    for locale in SUPPORTED_LOCALES:
        p3_text = locales_catalog[locale].get("tomo_ch1_p3", "")
        extracted = set(placeholder_regex.findall(p3_text))
        assert extracted == REQUIRED_INTERPOLATION_VARS_CH1, (
            f"Placeholder mismatch in tomo_ch1_p3 for locale '{locale}': {extracted} != {REQUIRED_INTERPOLATION_VARS_CH1}"
        )


def test_rfc074_table3_footnote_placeholder_symmetry(locales_catalog: Dict[str, Any]) -> None:
    """Quality Gate: Assert exact placeholder symmetry in Table 3 footnote across all 6 locales."""
    placeholder_regex = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    for locale in SUPPORTED_LOCALES:
        footnote = locales_catalog[locale].get("tomo_ch3_table4_footnote", "")
        extracted = set(placeholder_regex.findall(footnote))
        assert extracted == REQUIRED_INTERPOLATION_VARS_FOOTNOTE, (
            f"Placeholder mismatch in footnote for locale '{locale}': {extracted} != {REQUIRED_INTERPOLATION_VARS_FOOTNOTE}"
        )


def test_rfc074_peak_single_incident_computation() -> None:
    """Verify that _compute_peak_single_incident returns the maximum domain incident cost."""
    from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
        Volume1AsisASTCompiler,
    )

    compiler = Volume1AsisASTCompiler()
    topology = [
        ("T1", "Data Center", 2.6, "", ""),
        ("T2", "Compute", 2.5, "", ""),
        ("T5", "Operational Continuity", 2.1, "", ""),
    ]
    p90_allocations = {
        "T1": 352830,
        "T2": 252015,
        "T5": 515485,
    }

    code, name, val, formatted = compiler._compute_peak_single_incident(
        domain_topology=topology,
        reconciled_p90_allocations=p90_allocations,
        currency="€",
        doc_lang="es",
    )

    assert code == "T5"
    assert name == "Operational Continuity"
    assert val == 515485
    assert "515.485" in formatted
