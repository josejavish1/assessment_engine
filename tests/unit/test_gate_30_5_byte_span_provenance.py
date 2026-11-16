"""
Unit Test Suite for GATE-30.5: Byte-Span Provenance Enforcement.

Validates the cryptographic byte-span provenance invariant:
1. Prohibits certifying a fact as OBSERVED_EVIDENCE if byte_offset_span is invalid
   (e.g., end <= start) or if verbatim_quote is empty.
2. Immediate compilation panic (ValueError) prior to LLM socket allocation.
3. Permitted when byte_offset_span carries a valid positive span and exact quote snippet.
"""

import pytest

from assessment_engine.domain.ingestion.epistemic_fact_registry import (
    ActuarialFactTuple,
    EpistemicModality,
)


def test_gate_30_5_rejects_observed_evidence_without_valid_span():
    """GATE-30.5: Rejects OBSERVED_EVIDENCE facts with invalid byte offset span (0, 0)."""
    with pytest.raises(ValueError, match="GATE-30.5 Provenance Breach"):
        ActuarialFactTuple.create(
            canonical_subject="SYS_STORAGE_NETAPP",
            predicate="HAS_WORM_RETENTION",
            source_document_id="transcript_interview_infra_01.txt",
            source_char_span=(0, 0),  # Invalid empty span
            verbatim_quote="",
            modality=EpistemicModality.OBSERVED_EVIDENCE,
        )


def test_gate_30_5_rejects_inverted_span():
    """GATE-30.5: Rejects OBSERVED_EVIDENCE facts with inverted span (100, 50)."""
    with pytest.raises(ValueError, match="GATE-30.5 Provenance Breach"):
        ActuarialFactTuple.create(
            canonical_subject="SYS_STORAGE_NETAPP",
            predicate="HAS_WORM_RETENTION",
            source_document_id="transcript_interview_infra_01.txt",
            source_char_span=(100, 50),  # Inverted span
            verbatim_quote="some quote",
            modality=EpistemicModality.OBSERVED_EVIDENCE,
        )


def test_gate_30_5_permits_valid_byte_span_and_quote():
    """GATE-30.5: Permits OBSERVED_EVIDENCE facts with verified positive span and quote."""
    fact = ActuarialFactTuple.create(
        canonical_subject="SYS_STORAGE_NETAPP",
        predicate="HAS_FAS_STORAGE",
        source_document_id="transcript_interview_infra_01.txt",
        source_char_span=(420, 485),
        verbatim_quote="tenemos dos cabinas NetApp FAS principales para almacenamiento",
        modality=EpistemicModality.OBSERVED_EVIDENCE,
    )
    assert fact.source_char_span == (420, 485)
    assert "NetApp FAS" in fact.verbatim_quote
    assert fact.modality == EpistemicModality.OBSERVED_EVIDENCE
