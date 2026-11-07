"""Unit tests for RFC 082 Epistemic Ledger models and ports."""

import pytest
from uuid import uuid4

from assessment_engine.domain.contracts.ingestion_ports import (
    IEmpiricalDataParserPort,
    IEpistemicSynthesizerPort,
    IPhoneticResolverPort,
    ITranscriptParserPort,
)
from assessment_engine.domain.schemas.epistemic_ledger import (
    AuthorityRole,
    EpistemicFragment,
    EpistemicLedger,
    EpistemicState,
    EvidenceEntry,
    NormalizedUtterance,
    Polarity,
    RawUtterance,
    ResolvedEntity,
    TruthStatus,
)


def test_raw_utterance_validation_and_immutability():
    utt = RawUtterance(
        sequence_index=1,
        speaker_identifier="Lead Architect",
        speaker_role=AuthorityRole.SME_TECHNICAL,
        raw_text="We run 6 SimpliVity nodes across two server rooms.",
    )
    assert utt.sequence_index == 1
    assert utt.speaker_role == AuthorityRole.SME_TECHNICAL
    assert utt.speaker_identifier == "Lead Architect"
    assert utt.utterance_id is not None

    # Verify immutability
    with pytest.raises(Exception):
        utt.raw_text = "Modified text"

    # Verify whitespace validation
    with pytest.raises(ValueError):
        RawUtterance(
            sequence_index=2,
            raw_text="   \n  ",
        )


def test_normalized_utterance_resolved_entities():
    u_id = uuid4()
    norm = NormalizedUtterance(
        utterance_id=u_id,
        sequence_index=1,
        speaker_identifier="Lead Architect",
        speaker_role=AuthorityRole.SME_TECHNICAL,
        raw_text="We have simply nodes.",
        normalized_text="We have HPE SimpliVity nodes.",
        resolved_entities=[
            ResolvedEntity(
                original_token="simply",
                canonical_entity="HPE SimpliVity",
                resolution_method="PHONETIC_CONTEXTUAL_LLM",
                phonetic_distance=0.15,
                confidence=0.95,
            )
        ],
        normalization_confidence=0.95,
    )
    assert len(norm.resolved_entities) == 1
    assert norm.resolved_entities[0].canonical_entity == "HPE SimpliVity"
    assert norm.normalized_text == "We have HPE SimpliVity nodes."


def test_epistemic_fragment_and_ledger_cryptographic_hash():
    frag1 = EpistemicFragment(
        source_type="RAW_TRANSCRIPT",
        source_file="transcript_2026.docx",
        canonical_assertion="HPE SimpliVity cluster comprises 6 physical nodes.",
        polarity=Polarity.NEUTRAL,
        state=EpistemicState.CURRENT,
        epistemic_weight=0.75,
    )

    frag2 = EpistemicFragment(
        source_type="EMPIRICAL_XLSX",
        source_file="questionnaire.xlsx",
        canonical_assertion="Compute infrastructure runs on 6 hyperconverged nodes.",
        polarity=Polarity.POSITIVE,
        state=EpistemicState.CURRENT,
        epistemic_weight=0.80,
    )

    entry = EvidenceEntry(
        entry_id="EVD-001",
        domain_taxonomy_ref="T2.P1",
        canonical_assertion="Compute cluster operating on 6 HPE SimpliVity nodes.",
        truth_status=TruthStatus.VERIFIED_CONSISTENT,
        composite_confidence=0.95,
        supporting_fragments=[frag1, frag2],
    )

    ledger = EpistemicLedger(
        client_id="test_client",
        epistemic_entries=[entry],
    )

    hash1 = ledger.calculate_integrity_hash()
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 length

    # Cryptographic determinism check
    hash2 = ledger.calculate_integrity_hash()
    assert hash1 == hash2


def test_domain_ports_abstractness():
    # Ports cannot be instantiated directly
    with pytest.raises(TypeError):
        ITranscriptParserPort()

    with pytest.raises(TypeError):
        IEmpiricalDataParserPort()

    with pytest.raises(TypeError):
        IPhoneticResolverPort()

    with pytest.raises(TypeError):
        IEpistemicSynthesizerPort()
