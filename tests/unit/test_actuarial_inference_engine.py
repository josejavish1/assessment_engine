"""Deterministic Test Oracle for Phase 2: Actuarial Inference Engine (RFC 084).

Validates:
1. Mathematical calculation of Latent Loss Event Frequency (LEF), Single Loss Expectancy (SLE),
   and Annual Loss Expectancy (ALE) for unobserved/silent enterprise pillars.
2. The Zero-ALE Prohibition Gate: Zero instances of ale == 0.0 when 9 towers are silent.
3. Scale sensitivity: Monotonic loss scaling across enterprise revenues ($10M SMB vs $2B Retail).
4. Epistemic state differentiation: OBSERVED_EXPLICIT vs UNOBSERVED_BLINDSPOT.
5. Strict Technical English language decoupling and typed data contracts.
6. Mutation CTF probe resilience: Kills boolean, operator, and comparison mutants.
"""

from __future__ import annotations

import dataclasses
import pytest

from assessment_engine.application.services.actuarial_inference_engine import (
    ActuarialInferenceEngine,
    LatentActuarialFinding,
    TenantActuarialProfile,
)
from assessment_engine.application.services.semantic_epistemic_router import (
    EpistemicContextPacket,
    SemanticProposition,
)


def test_tenant_actuarial_profile_immutability() -> None:
    """Kills mutant where TenantActuarialProfile frozen=True is changed to False."""
    profile = TenantActuarialProfile()
    with pytest.raises(dataclasses.FrozenInstanceError):
        profile.annual_revenue = 500.0  # type: ignore[misc]


def test_latent_actuarial_finding_immutability_and_types() -> None:
    """Verifies typed contract and immutability of LatentActuarialFinding."""
    finding = LatentActuarialFinding(
        finding_id="BLINDSPOT_T5_P1",
        tower_code="T5",
        pillar_id="T5.P1",
        title="Unobserved Operational Resilience and Continuity Controls",
        epistemic_state="UNOBSERVED_BLINDSPOT",
        loss_event_frequency=0.15,
        single_loss_expectancy=250000.0,
        annual_loss_expectancy=37500.0,
        value_at_risk_90=75000.0,
        rationale="Absence of continuity evidence exposes the enterprise to unmitigated latent baseline risk.",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        finding.annual_loss_expectancy = 0.0  # type: ignore[misc]

    assert finding.annual_loss_expectancy > 0.0
    assert finding.epistemic_state == "UNOBSERVED_BLINDSPOT"
    assert finding.value_at_risk_90 >= finding.annual_loss_expectancy


def test_latent_risk_calculation_strictly_positive() -> None:
    """Verifies that latent risk for silent pillars produces strictly positive FAIR metrics."""
    profile = TenantActuarialProfile(
        annual_revenue=2_000_000_000.0,
        industry_vertical="retail",
        employee_headcount=15000,
        currency_code="USD",
    )
    engine = ActuarialInferenceEngine(default_profile=profile)

    finding = engine.calculate_latent_risk(
        tower_code="T5",
        pillar_id="T5.P1",
        pillar_name="Business Continuity & Disaster Recovery",
    )

    # Kills arithmetic operator mutant in base_sle = safe_revenue * (base_bps / 10_000.0)
    assert finding.single_loss_expectancy > 5_000_000.0
    assert finding.annual_loss_expectancy > 500_000.0
    assert finding.loss_event_frequency > 0.0
    assert finding.value_at_risk_90 > finding.annual_loss_expectancy
    assert finding.epistemic_state == "UNOBSERVED_BLINDSPOT"
    assert "Disaster Recovery" in finding.title or "Continuity" in finding.title


def test_observed_risk_polarity_and_boost() -> None:
    """Kills mutant in negative polarity comparison (== vs !=) and boost multiplication."""
    profile = TenantActuarialProfile(
        annual_revenue=100_000_000.0,
        industry_vertical="retail",
        currency_code="USD",
    )
    engine = ActuarialInferenceEngine(default_profile=profile)
    baseline = engine.calculate_latent_risk("T3", "T3.P1", "Network")

    pos_prop = SemanticProposition(text="Redundant switches", turn_index=0, polarity="POSITIVE")
    neg_prop = SemanticProposition(text="Failed switches", turn_index=0, polarity="NEGATIVE")

    pkt_pos = EpistemicContextPacket("T3", [pos_prop], 0.5, "OBSERVED_EXPLICIT")
    pkt_neg = EpistemicContextPacket("T3", [neg_prop], 0.5, "OBSERVED_EXPLICIT")

    res_pos = engine._calculate_observed_risk(pkt_pos, profile)
    res_neg = engine._calculate_observed_risk(pkt_neg, profile)

    # Kills == vs != mutant: negative proposition must boost risk more than positive proposition
    assert res_neg.loss_event_frequency > res_pos.loss_event_frequency
    assert res_neg.single_loss_expectancy > res_pos.single_loss_expectancy
    # Kills * vs // mutant on combined_boost: combined boost must exceed baseline by > 15%
    assert res_neg.loss_event_frequency > baseline.loss_event_frequency * 1.15


def test_hydrate_observed_vs_empty_propositions_discrimination() -> None:
    """Kills relational mutant len(packet.propositions) > 0 vs <= 0."""
    profile = TenantActuarialProfile(
        annual_revenue=100_000_000.0,
        industry_vertical="general",
    )
    engine = ActuarialInferenceEngine(default_profile=profile)

    prop = SemanticProposition(text="Core switches configured", turn_index=0, polarity="POSITIVE")
    obs_pkt = EpistemicContextPacket("T3", [prop], 0.5, "OBSERVED_EXPLICIT")
    hydrated = engine.hydrate_portfolio_risks({"T3": obs_pkt})

    assert hydrated["T3"][0].finding_id.startswith("OBSERVED_T3_")
    assert hydrated["T3"][0].epistemic_state == "OBSERVED_EXPLICIT"

    # Packet with empty propositions must fall back to latent blindspot
    empty_pkt = EpistemicContextPacket("T3", [], 0.0, "OBSERVED_EXPLICIT")
    hydrated_empty = engine.hydrate_portfolio_risks({"T3": empty_pkt})
    assert hydrated_empty["T3"][0].finding_id.startswith("BLINDSPOT_T3_")
    assert hydrated_empty["T3"][0].epistemic_state == "UNOBSERVED_BLINDSPOT"


def test_zero_ale_prohibition_gate_9_silent_towers() -> None:
    """Gate 2: Zero-ALE Prohibition Gate (RFC 084 Phase 2).

    Simulates a discovery session where ONLY Network Infrastructure (T3) provides telemetry,
    leaving the other 9 technology towers completely silent.
    Asserts that ZERO towers emit an ALE of 0.00.
    """
    profile = TenantActuarialProfile(
        annual_revenue=2_000_000_000.0,
        industry_vertical="retail",
        employee_headcount=20000,
        currency_code="USD",
    )
    engine = ActuarialInferenceEngine(default_profile=profile)

    propositions = [
        SemanticProposition(
            text="Core Cisco Nexus spine-leaf network switches lack dual power feeds in distribution centers.",
            turn_index=1,
            polarity="NEGATIVE",
        )
    ]
    t3_packet = EpistemicContextPacket(
        tower_code="T3",
        propositions=propositions,
        semantic_density_score=0.85,
        epistemic_state="OBSERVED_EXPLICIT",
    )

    packets: dict[str, EpistemicContextPacket] = {"T3": t3_packet}
    for i in [1, 2, 4, 5, 6, 7, 8, 9, 10]:
        code = f"T{i}"
        packets[code] = EpistemicContextPacket(
            tower_code=code,
            propositions=[],
            semantic_density_score=0.0,
            epistemic_state="UNOBSERVED_BLINDSPOT",
        )

    hydrated_risks = engine.hydrate_portfolio_risks(packets)

    assert len(hydrated_risks) == 10

    for code, findings in hydrated_risks.items():
        assert len(findings) > 0, f"Tower {code} emitted zero risk findings"
        total_tower_ale = sum(f.annual_loss_expectancy for f in findings)
        assert (
            total_tower_ale > 0.0
        ), f"Violation of Gate 2: Tower {code} emitted ALE == 0.00!"

    for code in [f"T{i}" for i in [1, 2, 4, 5, 6, 7, 8, 9, 10]]:
        findings = hydrated_risks[code]
        assert any(f.epistemic_state == "UNOBSERVED_BLINDSPOT" for f in findings)


def test_scale_sensitivity_monotonic_growth() -> None:
    """Verifies that latent risk scales monotonically with enterprise scale."""
    smb_profile = TenantActuarialProfile(
        annual_revenue=10_000_000.0,
        industry_vertical="manufacturing",
        employee_headcount=50,
        currency_code="EUR",
    )
    enterprise_profile = TenantActuarialProfile(
        annual_revenue=1_144_000_000.0,
        industry_vertical="manufacturing",
        employee_headcount=5000,
        currency_code="EUR",
    )

    smb_engine = ActuarialInferenceEngine(default_profile=smb_profile)
    ent_engine = ActuarialInferenceEngine(default_profile=enterprise_profile)

    smb_finding = smb_engine.calculate_latent_risk("T2", "T2.P1", "Hypervisor Infrastructure")
    ent_finding = ent_engine.calculate_latent_risk("T2", "T2.P1", "Hypervisor Infrastructure")

    assert ent_finding.single_loss_expectancy > (smb_finding.single_loss_expectancy * 10.0)
    assert ent_finding.annual_loss_expectancy > (smb_finding.annual_loss_expectancy * 10.0)


def test_sector_specific_loss_curves() -> None:
    """Verifies that different industry verticals apply distinct actuarial loss profiles."""
    revenue = 500_000_000.0
    fintech_profile = TenantActuarialProfile(
        annual_revenue=revenue,
        industry_vertical="fintech",
        currency_code="USD",
    )
    logistics_profile = TenantActuarialProfile(
        annual_revenue=revenue,
        industry_vertical="logistics",
        currency_code="USD",
    )

    fintech_engine = ActuarialInferenceEngine(default_profile=fintech_profile)
    logistics_engine = ActuarialInferenceEngine(default_profile=logistics_profile)

    fintech_sec = fintech_engine.calculate_latent_risk("T6", "T6.P1", "Identity & Access Control")
    logistics_sec = logistics_engine.calculate_latent_risk("T6", "T6.P1", "Identity & Access Control")

    assert fintech_sec.annual_loss_expectancy != logistics_sec.annual_loss_expectancy
    assert fintech_sec.annual_loss_expectancy > logistics_sec.annual_loss_expectancy
