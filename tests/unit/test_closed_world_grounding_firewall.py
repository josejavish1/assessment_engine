"""Unit tests for Phase 4: Closed-World Grounding and Hallucination Firewall Domain Service.

Verifies:
1. Detection and iterative stripping of ungrounded measuring instruments and manual paper artifacts.
2. Verification against empirical source evidence corpus (attested vs unattested).
3. Executive summary domain headline isolation with boundary-safe keyword matching.
4. Multi-language dynamic resolution via LocalizationPort using synthetic locale tokens.
5. Sentence boundary protection against technical abbreviations (e.g., i.e., vs.).

Strictly 100% Technical English and tenant-agnostic.
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.services.closed_world_grounding_firewall import (
    ClosedWorldGroundingFirewall,
)


class SyntheticLocalizationProvider:
    """Test double implementing LocalizationPort using synthetic English test tokens."""

    def get_localized_list(self, key: str, locale: str = "en") -> list[str]:
        if key == "speculative_artifact_regexes" and locale == "x-test":
            return [
                r"synthetic_sensor_probe\w*",
                r"custom_calibration_device\w*",
                r"paper_inspection_sheet\w*",
            ]
        return []

    def translate(self, key: str, locale: str = "en") -> str:
        if key == "speculative_clause_prefix_regex" and locale == "x-test":
            return r"(?:utilizing|via|relying on)\s+[^,\.;]*"
        return ""


def test_speculative_artifact_detected_when_absent_from_corpus() -> None:
    corpus = "The client reported lack of real-time electrical capacity telemetry."
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus=corpus,
        doc_lang="en",
    )

    narrative = (
        "Power distribution panels lack telemetry, relying on clamp meters for ad-hoc surveys. "
        "This absence of metrics elevates breaker trip exposure."
    )

    result = firewall.sanitize_narrative_block(
        narrative=narrative,
        fallback_rubric_statement="Power distribution panels lack continuous telemetry.",
    )

    assert not result.is_clean
    assert len(result.detected_violations) == 1
    assert "clamp meters" in result.detected_violations[0]
    assert "clamp meters" not in result.sanitized_text
    assert "elevates breaker trip exposure" in result.sanitized_text


def test_speculative_artifact_permitted_when_present_in_corpus() -> None:
    corpus = "The datacenter manager stated staff uses clamp meters during weekly breaker checks."
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus=corpus,
        doc_lang="en",
    )

    narrative = (
        "Facilities staff conducts manual load verification relying on clamp meters as stated. "
        "However, real-time alerting remains absent."
    )

    result = firewall.sanitize_narrative_block(narrative=narrative)

    assert result.is_clean
    assert len(result.detected_violations) == 0
    assert "clamp meters" in result.sanitized_text


def test_subordinate_clause_stripping_preserves_grammatical_integrity() -> None:
    corpus = "No structured access control exists for third-party maintenance contractors."
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus=corpus,
        doc_lang="en",
    )

    narrative = (
        "Contractor room ingress is unmonitored, utilizing physical logbooks for facility access."
    )

    result = firewall.sanitize_narrative_block(
        narrative=narrative,
        fallback_rubric_statement="Contractor room ingress lacks formal digital authorization.",
    )

    assert not result.is_clean
    assert "physical logbooks" not in result.sanitized_text
    assert result.sanitized_text.endswith(".")


def test_iterative_stripping_of_multiple_speculative_artifacts() -> None:
    corpus = "The primary power panels operate without telemetry."
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus=corpus,
        doc_lang="en",
    )

    narrative = (
        "Power feeds are unmonitored, relying on clamp meters for current measurement "
        "and utilizing physical logbooks for data recording."
    )

    result = firewall.sanitize_narrative_block(
        narrative=narrative,
        fallback_rubric_statement="Power feeds operate without continuous digital telemetry.",
    )

    assert not result.is_clean
    assert "clamp meters" not in result.sanitized_text
    assert "physical logbooks" not in result.sanitized_text


def test_sentence_boundary_does_not_split_on_abbreviations() -> None:
    corpus = "Power panels lack telemetry."
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus=corpus,
        doc_lang="en",
    )

    narrative = (
        "Main panels lack telemetry (e.g. branch sensors), relying on clamp meters for load checks. "
        "Secondary breakers remain unverified."
    )

    result = firewall.sanitize_narrative_block(
        narrative=narrative,
        fallback_rubric_statement="Main panels lack continuous digital telemetry.",
    )

    assert not result.is_clean
    assert "e.g. branch sensors" in result.sanitized_text
    assert "clamp meters" not in result.sanitized_text
    assert "Secondary breakers remain unverified." in result.sanitized_text


def test_executive_summary_boundary_safe_keyword_isolation() -> None:
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus="Facilities power and cooling review.",
        in_scope_keywords={"power", "cooling", "ups", "generator", "datacenter", "facility"},
        foreign_domain_primary_terms={"ram", "sap", "erp", "vmware"},
        doc_lang="en",
    )

    # "parameters" contains "ram", "program" contains "ram" -> must NOT be treated as foreign "ram" hit!
    paragraphs = [
        (
            "Primary power parameters conform to baseline specifications across all UPS units. "
            "Server nodes experience extreme ram exhaustion under sap transaction peaks. "
            "Cooling distribution units maintain sufficient sensible capacity under N+1 redundancy."
        )
    ]

    sanitized = firewall.enforce_executive_summary_tower_focus(paragraphs)

    assert len(sanitized) == 1
    cleaned_p = sanitized[0]
    assert "Primary power parameters conform" in cleaned_p
    assert "Cooling distribution units" in cleaned_p
    assert "ram exhaustion" not in cleaned_p
    assert "sap transaction" not in cleaned_p


def test_multi_language_resolution_via_localization_port() -> None:
    corpus = "The infrastructure assessment observed no sensor automation."
    provider = SyntheticLocalizationProvider()
    firewall = ClosedWorldGroundingFirewall(
        source_evidence_corpus=corpus,
        doc_lang="x-test",
        localization_provider=provider,
    )

    narrative = (
        "Subsystem status is unmonitored, utilizing synthetic_sensor_probes for spot evaluations. "
        "This architectural deficit requires remediation."
    )

    result = firewall.sanitize_narrative_block(
        narrative=narrative,
        fallback_rubric_statement="Subsystem status is unmonitored.",
    )

    assert not result.is_clean
    assert any("synthetic_sensor_probe" in v for v in result.detected_violations)
    assert "synthetic_sensor_probe" not in result.sanitized_text
    assert "This architectural deficit requires remediation." in result.sanitized_text


def test_build_domain_scoped_prompt_directives_parameterized_scale() -> None:
    firewall = ClosedWorldGroundingFirewall(doc_lang="en")
    rubric = [
        {
            "kpi_id": "D_FAC.P1.K4",
            "kpi_name": "Available Power Telemetry",
            "score": 1,
            "selected_option_text": "Capacity is unknown and branch loads are not monitored.",
        }
    ]

    directives = firewall.build_domain_scoped_prompt_directives(
        domain_name="Physical Facilities",
        kpi_rubric_selections=rubric,
        canonical_pillar_titles=["Electrical Power", "Cooling & Airflow"],
        excluded_foreign_tower_keywords=["Hypervisors", "Kubernetes", "ERP"],
        score_scale_max=5,
    )

    assert "CLOSED-WORLD EPISTEMIC GROUNDING MANDATE" in directives
    assert "D_FAC.P1.K4" in directives
    assert "Score: 1/5" in directives
    assert "ZERO SPECULATIVE EMBELLISHMENT ON DEFICIENT CONTROLS" in directives
    assert "Capacity is unknown and branch loads are not monitored." in directives
