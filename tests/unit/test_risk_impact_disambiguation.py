"""Unit tests for Phase 2: Tier-1 Disambiguation of Severity Enums and Causal Operational Impacts.

Verifies:
1. Rejection of bare ordinal enums (HIGH, CRITICAL) in qualitative narrative fields.
2. Contextual operational impact synthesis from finding telemetry.
3. Preservation of technical acronyms during clause synthesis.
Strictly 100% Technical English and tenant-agnostic.
"""

from __future__ import annotations

from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    _CANONICAL_SEVERITY_ENUM_TOKENS,
    _extract_verified_business_risk,
    _is_severity_enum_token,
)


def test_severity_enum_tokens_membership() -> None:
    assert "HIGH" in _CANONICAL_SEVERITY_ENUM_TOKENS
    assert "CRITICAL" in _CANONICAL_SEVERITY_ENUM_TOKENS
    assert "MEDIUM" in _CANONICAL_SEVERITY_ENUM_TOKENS
    assert _is_severity_enum_token("HIGH.", doc_lang="en")
    assert _is_severity_enum_token("  critical! ", doc_lang="en")


def test_extract_verified_business_risk_preserves_valid_prose() -> None:
    hc = {
        "business_risk": "Risk of unplanned factory downtime due to failure of dual electrical feeds.",
        "impact": "HIGH",
    }
    result = _extract_verified_business_risk(hc, "Physical Power", "en")
    assert result == "Risk of unplanned factory downtime due to failure of dual electrical feeds."


def test_extract_verified_business_risk_rejects_bare_enums_and_preserves_acronyms() -> None:
    hc = {
        "capability": "CRAC Thermal Dissipation",
        "finding": "UPS battery strings lack automated impedance telemetry across redundancy zones.",
        "business_risk": "HIGH",
        "impact": "HIGH",
    }
    result_en = _extract_verified_business_risk(hc, "Facilities & Cooling", "en")
    assert result_en != "HIGH"
    assert "HIGH" not in result_en.split()
    assert "UPS battery strings" in result_en


def test_extract_verified_business_risk_handles_empty_fields_gracefully() -> None:
    hc = {
        "capability": "Access Control Gateway",
    }
    result = _extract_verified_business_risk(hc, "Physical Security", "en")
    assert "access control gateway" in result
    assert "physical security" in result
    assert len(result.split()) >= 6


def test_extract_verified_business_risk_preserves_mixed_case_acronyms() -> None:
    hc = {
        "capability": "SaaS and SD-WAN Identity & Access Management",
    }
    result = _extract_verified_business_risk(hc, "Zero-Trust Security", "en")
    assert "SaaS and SD-WAN identity & access management" in result
    assert "zero-trust security" in result


def test_severity_enum_tokens_compound_labels() -> None:
    assert _is_severity_enum_token("HIGH / CRITICAL", doc_lang="en")
    assert _is_severity_enum_token("Severity: HIGH", doc_lang="en")
    assert _is_severity_enum_token("Tier 1 - Critical", doc_lang="en")
    assert not _is_severity_enum_token("Complete datacenter blackout due to generator failure", doc_lang="en")


def test_decapitalize_clause_preserves_post_delimiter_designators() -> None:
    hc = {
        "capability": "Dual Feed-A and Feed-B Utility Ingress",
    }
    result = _extract_verified_business_risk(hc, "Tier-IV Data Center", "en")
    assert "feed-A" in result
    assert "feed-B" in result
    assert "tier-IV" in result


def test_severity_enum_tokens_parenthetical_and_cat_edge_cases() -> None:
    assert _is_severity_enum_token("HIGH (P1)", doc_lang="en")
    assert _is_severity_enum_token("CRITICAL [SEV-1]", doc_lang="en")
    assert _is_severity_enum_token("CAT-I", doc_lang="en")
    assert _is_severity_enum_token("CAT-IV", doc_lang="en")
    assert not _is_severity_enum_token("CAT-|||", doc_lang="en")
    assert not _is_severity_enum_token("CAT-I|V", doc_lang="en")
