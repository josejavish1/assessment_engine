"""Unit tests for LinguisticQualityGuardrail (RFC-022)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.linguistic_guardrail import LinguisticQualityGuardrail


def test_detect_language_drift_clean_text() -> None:
    """Verify that pure text in target locale does not trigger drift violation."""
    # Clean text in English
    clean_en = "The cloud foundation demonstrates lack of declarative automation across cluster environments."
    drift_en, _ = LinguisticQualityGuardrail.detect_language_drift(clean_en, target_locale="en")
    assert not drift_en

    # Clean text in German
    clean_de = "Die Cloud-Grundlage zeigt einen Mangel an deklarativer Automatisierung für Server."
    drift_de, _ = LinguisticQualityGuardrail.detect_language_drift(clean_de, target_locale="de")
    assert not drift_de


def test_detect_language_drift_catches_english_contagion_in_foreign_target() -> None:
    """Verify that raw English paragraphs are caught when target is non-English."""
    contaminated_text = (
        "The organization completely lacks a standardized platform service catalog, developer portal, "
        "or automated self-service provisioning workflow, leading to severe operational bottlenecks."
    )
    # Target is German, but input is 100% English
    has_drift, reason = LinguisticQualityGuardrail.detect_language_drift(contaminated_text, target_locale="de")
    assert has_drift
    assert "Language contagion detected" in reason


def test_audit_blueprint_payload_identifies_contagion() -> None:
    """Verify full payload auditing flags unlocalized findings."""
    payload = {
        "pillars_analysis": [
            {
                "pilar_name": "Compute Foundation",
                "asis_architecture_description": "Normaler Betrieb ohne nennenswerte Fehler.",
                "health_check_asis": [
                    {
                        "finding": "Compute host lifecycle management and firmware maintenance rely on manual procedures.",
                        "business_risk": "Elevated vulnerability to hypervisor breakout exploits and unscheduled outages.",
                    }
                ],
            }
        ]
    }
    violations = LinguisticQualityGuardrail.audit_blueprint_payload(payload, target_locale="de")
    assert len(violations) >= 1
    assert any("Finding 1" in v for v in violations)
