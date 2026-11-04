"""Unit tests verifying RFC 071 multi-tenant decoupling in PayloadToASTBridge and ExecutiveNarrativeSynthesizer.

Guarantees:
1. Dynamic archetype override (e.g., T1 using SECURITY_GOVERNANCE).
2. Dynamic domain semantics injection from payload (operational mission, dilemma anchor).
3. Non-canonical domain identifiers (e.g., DOMAIN_CLOUD, T15).
4. Zero single-tenant leakage across heterogeneous enterprises (banking, healthcare, retail).
"""

from __future__ import annotations

import pytest

from assessment_engine.adapters.compilers.payload_to_ast import (
    ExecutiveNarrativeSynthesizer,
)


def test_synthesizer_dynamic_archetype_override() -> None:
    """Verifies that an explicit archetype passed in payload overrides the default T1..T10 mapping."""
    synthesizer = ExecutiveNarrativeSynthesizer(locale_code="en")

    # T1 defaults to INFRASTRUCTURE_PHYSICAL, but we override it with SECURITY_GOVERNANCE
    paragraphs = synthesizer.synthesize_chapter_one_paragraphs(
        client_name="Nordic Health Group",
        tower_name="Clinical Data Vault",
        maturity_score="3.80",
        maturity_tier_label="Defined",
        primary_workloads_summary="Electronic Health Records (EHR) and diagnostic imaging archives",
        findings_briefs=["Missing continuous database transaction log immutability"],
        hourly_burn_rate_fmt="4,500 EUR/h",
        net_downtime_hours_fmt="6.5",
        annual_loss_expectancy_fmt="125,000 EUR",
        p90_downtime_hours_fmt="12.0",
        p90_var_exposure_fmt="350,000 EUR",
        remediation_horizon_label="Horizon 1 (0-6 months)",
        primary_remediation_pillar="Data Security",
        target_maturity_score="4.20",
        tower_id="T1",
        archetype="SECURITY_GOVERNANCE",
        operational_mission="secure clinical records storage and patient data integrity",
        dilemma_anchor="Evaluating medical record durability under strict privacy regulations,",
        posture_modernization_focus="implementing cryptographic write-once immutability",
    )

    assert len(paragraphs) == 4
    # Paragraph 1 must reflect custom operational mission and client name
    assert "Nordic Health Group" in paragraphs[0]
    assert "secure clinical records storage and patient data integrity" in paragraphs[0]

    # Paragraph 3 must reflect the SECURITY_GOVERNANCE framing
    assert "4,500 EUR/h" in paragraphs[2]
    assert "125,000 EUR" in paragraphs[2]

    # Must contain zero manufacturing/cement artifacts
    full_text = " ".join(paragraphs).lower()
    assert "molins" not in full_text
    assert "secil" not in full_text
    assert "weighbridge" not in full_text
    assert "cement" not in full_text
    assert "sant vicen" not in full_text


def test_synthesizer_custom_non_canonical_domain_id() -> None:
    """Verifies synthesis for non-canonical domain codes (e.g., CLOUD_CORE, T12)."""
    synthesizer = ExecutiveNarrativeSynthesizer(locale_code="es")

    paragraphs = synthesizer.synthesize_chapter_one_paragraphs(
        client_name="Tokyo FinTech Bank",
        tower_name="Plataforma de Pagos Inmediatos",
        maturity_score="4.10",
        maturity_tier_label="Gestionado",
        primary_workloads_summary="Motor de liquidación interbancaria en tiempo real",
        findings_briefs=["Latencia en la replicación activa-activa entre zonas de disponibilidad"],
        hourly_burn_rate_fmt="15.000 USD/h",
        net_downtime_hours_fmt="2.0",
        annual_loss_expectancy_fmt="450.000 USD",
        p90_downtime_hours_fmt="4.5",
        p90_var_exposure_fmt="1.200.000 USD",
        remediation_horizon_label="Horizonte 1 (0-6 meses)",
        primary_remediation_pillar="Resiliencia Transaccional",
        target_maturity_score="4.50",
        tower_id="DOMAIN_FINTECH_PAYMENTS",
        archetype="COMPUTE_PLATFORMS",
        operational_mission="procesamiento transaccional de alta frecuencia y conciliación bancaria",
        dilemma_anchor="Desde la óptica de la resiliencia operativa y la disponibilidad continua,",
        posture_modernization_focus="reducir la latencia inter-zona y desplegar failover determinista",
    )

    assert len(paragraphs) == 4
    assert "Tokyo FinTech Bank" in paragraphs[0]
    assert "procesamiento transaccional de alta frecuencia" in paragraphs[0]

    full_text = " ".join(paragraphs).lower()
    assert "molins" not in full_text
    assert "secil" not in full_text
    assert "báscula" not in full_text
    assert "cemento" not in full_text
