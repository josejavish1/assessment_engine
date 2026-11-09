"""Unit tests for Phase 3: Table 6 Justification Polarity & Orthographic Sanitizer.

Verifies:
1. Strict rejection of leading adversative connectives in operational strength slots.
2. Direct statement formatting and prefix stripping in resilience breach slots.
3. Localized catalog fallback resolution without hardcoded language literals in tests.
Strictly 100% Technical English and tenant-agnostic.
"""

from __future__ import annotations

from typing import Any, Dict

from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    _sanitize_breach_clause,
    _sanitize_strength_clause,
    derive_in_memory_maturity_matrix,
)


def test_sanitize_strength_clause_rejects_adversative_connectives() -> None:
    # Simulates an adversative sentence fragment leaking into the strength slot
    adversative_text = (
        "However, the actual effectiveness of this survival design against total "
        "facility loss is severely compromised by two operational factors."
    )
    fallback = "Operational processes structured according to early smoke detection and clean gas suppression."

    result = _sanitize_strength_clause(adversative_text, fallback, score=4.0, doc_lang="en")
    assert result == fallback
    assert not result.lower().startswith("however")


def test_sanitize_strength_clause_preserves_clean_affirmative_sentences() -> None:
    clean_text = (
        "Facilities mitigation relies on physical segregation across two technical rooms separated by 500 meters. "
        "However, secondary cluster capacity is constrained."
    )
    fallback = "Fallback strength."

    result = _sanitize_strength_clause(clean_text, fallback, score=4.0, doc_lang="en")
    assert "separated by 500 meters" in result
    assert "However" not in result


def test_sanitize_breach_clause_strips_leading_adversative_connectors() -> None:
    adversative_gap = "nevertheless, deficit in environmental risk telemetry under raised floor plenums."
    fallback = "Default gap."

    result = _sanitize_breach_clause(adversative_gap, fallback, doc_lang="en")
    assert not result.lower().startswith("nevertheless")
    assert result.startswith("Deficit")
    assert result.endswith(".")


def test_maturity_matrix_uses_localized_catalog_fallbacks_when_findings_empty() -> None:
    sample_payload: Dict[str, Any] = {
        "domain_id": "D1",
        "pillars_analysis": [
            {
                "pillar_id": "D1.P4",
                "pillar_name": "Fire Suppression and Environmental Telemetry",
                "score": 4.0,
                "asis_architecture_description": "However, real effectiveness is compromised.",
                "health_check_asis": [],
            }
        ],
    }

    rows = derive_in_memory_maturity_matrix(sample_payload, doc_lang="en")
    assert len(rows) == 1
    justification = rows[0]["justification"]

    assert "However, real effectiveness" not in justification
