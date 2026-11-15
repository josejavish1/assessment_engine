"""
Unit test suite for Tier-1 Epistemic Fact Registry & Perspective Lease Allocation Engine.

Verifies:
1. Cryptographic SHA-256 provenance in ActuarialFactTuple.
2. Perspective Lease Allocation enforcing single-narrative ownership and preventing cross-domain duplication.
3. Polarity-Aware Claim Gating solving the Absence of Evidence vs Evidence of Absence fallacy.
"""

from assessment_engine.domain.ingestion.epistemic_fact_registry import (
    ActuarialFactTuple,
    ClaimPolarity,
    DomainPerspective,
    EpistemicFactRegistry,
    EpistemicModality,
    LeaseStatus,
    LeaseType,
)


def test_actuarial_fact_tuple_deterministic_provenance():
    """Verify deterministic SHA-256 ID generation for ActuarialFactTuple."""
    aft = ActuarialFactTuple.create(
        canonical_subject="SYS_SIMPLIVITY_NODE_01",
        predicate="HAS_CONTINUOUS_UPTIME",
        source_document_id="transcript_20261014.docx",
        source_char_span=(12450, 12580),
        verbatim_quote="este lleva activo 613 días continuos sin reinicio",
        modality=EpistemicModality.MANAGEMENT_ASSERTION,
        value_scalar=613,
        unit_iso="DAYS",
    )
    assert aft.fact_id.startswith("AFT-")
    assert len(aft.fact_id) == 16  # "AFT-" + 12 hex chars

    # Re-creating with exact same span produces exact same hash
    aft2 = ActuarialFactTuple.create(
        canonical_subject="SYS_SIMPLIVITY_NODE_01",
        predicate="HAS_CONTINUOUS_UPTIME",
        source_document_id="transcript_20261014.docx",
        source_char_span=(12450, 12580),
        verbatim_quote="este lleva activo 613 días continuos sin reinicio",
        modality=EpistemicModality.MANAGEMENT_ASSERTION,
        value_scalar=613,
        unit_iso="DAYS",
    )
    assert aft.fact_id == aft2.fact_id


def test_perspective_lease_allocation_prevents_narrative_duplication():
    """Verify that Primary Owner can redeem narrative lease once, preventing cross-chapter repetition."""
    registry = EpistemicFactRegistry()

    aft = ActuarialFactTuple.create(
        canonical_subject="SYS_SIMPLIVITY_NODE_01",
        predicate="HAS_CONTINUOUS_UPTIME",
        source_document_id="transcript_20261014.docx",
        source_char_span=(12450, 12580),
        verbatim_quote="este lleva activo 613 días continuos sin reinicio",
        modality=EpistemicModality.MANAGEMENT_ASSERTION,
        value_scalar=613,
        unit_iso="DAYS",
        domain_leases=[
            DomainPerspective(
                domain_id="T2",
                lease_type=LeaseType.PRIMARY_OWNER,
                semantic_framing="Plataforma de Cómputo: Estabilidad operativa de hipervisores locales",
            ),
            DomainPerspective(
                domain_id="T6",
                lease_type=LeaseType.SECONDARY_CONSUMER,
                semantic_framing="Ciberseguridad: Exposición a vulnerabilidades no parcheadas por ausencia de reinicio",
            ),
        ],
    )
    fact_id = registry.register_fact(aft)

    # 1. T2 (Primary Owner) acquires lease in Section 3.2.1 -> SUCCESS
    success, msg, lease = registry.acquire_lease(fact_id, domain_id="T2", section_id="sec_3_2_1")
    assert success is True
    assert lease is not None
    assert lease.status == LeaseStatus.CONSUMED
    assert lease.consumed_in_section == "sec_3_2_1"

    # 2. T2 attempts to re-narrate the fact in Section 3.2.5 -> FAILS (Prohibits repetition)
    success2, msg2, lease2 = registry.acquire_lease(fact_id, domain_id="T2", section_id="sec_3_2_5")
    assert success2 is False
    assert "already consumed in 'sec_3_2_1'" in msg2

    # 3. T6 (Secondary Consumer) acquires lease as a causal premise -> SUCCESS
    success3, msg3, lease3 = registry.acquire_lease(fact_id, domain_id="T6", section_id="sec_3_2_cyber")
    assert success3 is True
    assert lease3 is not None
    assert lease3.lease_type == LeaseType.SECONDARY_CONSUMER

    # 4. T4 (Unauthorized domain) attempts to acquire lease -> FAILS (Stops NetApp leakage!)
    success4, msg4, lease4 = registry.acquire_lease(fact_id, domain_id="T4", section_id="sec_3_2_storage")
    assert success4 is False
    assert "possesses no lease authority" in msg4


def test_polarity_aware_claim_gating_permits_negative_benchmarks():
    """Verify that absent controls can be cited under NEGATIVE_GAP or REMEDIATION_TARGET polarities."""
    accredited_corpus_entities = {"vmware vsphere", "hpe simplivity", "zabbix", "huawei"}

    # 1. Assertive claim of uninstalled technology (VESDA) -> REJECTED
    allowed1, reason1 = EpistemicFactRegistry.evaluate_claim_polarity(
        entity_token="VESDA",
        polarity=ClaimPolarity.ASSERTIVE,
        accredited_entities=accredited_corpus_entities,
    )
    assert allowed1 is False
    assert "Polarity Violation" in reason1

    # 2. Assertive claim of accredited technology (VMware) -> PERMITTED
    allowed2, reason2 = EpistemicFactRegistry.evaluate_claim_polarity(
        entity_token="VMware vSphere",
        polarity=ClaimPolarity.ASSERTIVE,
        accredited_entities=accredited_corpus_entities,
    )
    assert allowed2 is True

    # 3. Negative gap claim citing absent technology (VESDA) -> PERMITTED!
    # (Solves the Absence of Evidence vs Evidence of Absence fallacy)
    allowed3, reason3 = EpistemicFactRegistry.evaluate_claim_polarity(
        entity_token="VESDA",
        polarity=ClaimPolarity.NEGATIVE_GAP,
        accredited_entities=accredited_corpus_entities,
    )
    assert allowed3 is True
    assert "Permitted non-assertive citation" in reason3

    # 4. Remediation target citing absent technology (BitLocker) -> PERMITTED!
    allowed4, reason4 = EpistemicFactRegistry.evaluate_claim_polarity(
        entity_token="BitLocker",
        polarity=ClaimPolarity.REMEDIATION_TARGET,
        accredited_entities=accredited_corpus_entities,
    )
    assert allowed4 is True
    assert "REMEDIATION_TARGET" in reason4
