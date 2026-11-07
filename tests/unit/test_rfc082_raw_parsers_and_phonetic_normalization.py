"""Unit tests for RFC 082 Raw Parsers and Phonetic Entity Resolution."""

import docx
import pytest
from pathlib import Path
from uuid import uuid4

from assessment_engine.domain.schemas.epistemic_ledger import AuthorityRole, RawUtterance
from assessment_engine.infrastructure.normalization.phonetic_entity_resolver import (
    PhoneticEntityResolver,
)
from assessment_engine.infrastructure.parsers.empirical_response_parser import (
    EmpiricalResponseParser,
)
from assessment_engine.infrastructure.parsers.raw_transcript_parser import (
    RawTranscriptParser,
)


def test_raw_transcript_parser_docx(tmp_path: Path):
    docx_file = tmp_path / "test_interview.docx"
    doc = docx.Document()
    doc.add_paragraph("Interviewer: How many hyperconverged nodes are deployed in Sant Vicenç?")
    doc.add_paragraph("Lead Architect (SME): We have 6 nodes of SimpliVity active across both CPDs.")
    doc.save(str(docx_file))

    parser = RawTranscriptParser()
    utterances = parser.parse_transcript(docx_file)

    assert len(utterances) == 2
    assert utterances[0].sequence_index == 1
    assert utterances[0].speaker_role == AuthorityRole.INTERVIEWER
    assert "Sant Vicenç" in utterances[0].raw_text

    assert utterances[1].sequence_index == 2
    assert utterances[1].speaker_role == AuthorityRole.SME_TECHNICAL
    assert "SimpliVity" in utterances[1].raw_text


def test_raw_transcript_parser_vtt(tmp_path: Path):
    vtt_file = tmp_path / "test_session.vtt"
    vtt_content = """WEBVTT

00:01:10.000 --> 00:01:15.500
<v Consultant>Do you have off-site backups?</v>

00:01:16.000 --> 00:01:22.000
<v IT Director>Yes, Cohesity replicates to an external object store.</v>
"""
    vtt_file.write_text(vtt_content, encoding="utf-8")

    parser = RawTranscriptParser()
    utterances = parser.parse_transcript(vtt_file)

    assert len(utterances) == 2
    assert utterances[0].timestamp_start == "00:01:10.000"
    assert utterances[0].speaker_identifier == "Consultant"
    assert utterances[0].speaker_role == AuthorityRole.INTERVIEWER

    assert utterances[1].timestamp_start == "00:01:16.000"
    assert utterances[1].speaker_identifier == "IT Director"
    assert utterances[1].speaker_role == AuthorityRole.EXECUTIVE_SPONSOR
    assert "Cohesity" in utterances[1].raw_text


def test_empirical_response_parser_txt(tmp_path: Path):
    txt_file = tmp_path / "responses.txt"
    txt_content = """# Test Assessment Responses
T1.P1.K1.PR1    3.0    Autonomía garantizada con generador
T1.P2.K1.PR1    1.0    Falta de climatización ASHRAE
T2.P1.K1.PR1    4.5
"""
    txt_file.write_text(txt_content, encoding="utf-8")

    parser = EmpiricalResponseParser()
    fragments = parser.parse_empirical_file(txt_file)

    assert len(fragments) == 3
    assert fragments[0].source_type == "EMPIRICAL_TXT"
    assert fragments[0].location_reference == "Line 2"
    assert fragments[0].metadata["question_id"] == "T1.P1.K1.PR1"
    assert fragments[0].metadata["numeric_score"] == 3.0
    assert fragments[1].polarity.value == "NEGATIVE"
    assert fragments[2].polarity.value == "POSITIVE"


def test_phonetic_entity_resolver_normalization():
    resolver = PhoneticEntityResolver()

    # Raw utterance with speech-to-text corruptions:
    # "simplivity" -> "HPE SimpliVity"
    # "occlout" -> "Oracle Cloud Infrastructure"
    # "stretch microplaster" -> "NetApp MetroCluster"
    raw_utt = RawUtterance(
        sequence_index=1,
        speaker_identifier="Architect",
        speaker_role=AuthorityRole.SME_TECHNICAL,
        raw_text="We migrated the simplivity cluster to stretch microplaster and export logs to occlout.",
    )

    norm = resolver.normalize_utterance(raw_utt)

    assert "HPE SimpliVity" in norm.normalized_text
    assert "NetApp MetroCluster" in norm.normalized_text
    assert "Oracle Cloud Infrastructure" in norm.normalized_text
    assert len(norm.resolved_entities) == 3

    # Validate audit entities
    canonical_set = {e.canonical_entity for e in norm.resolved_entities}
    assert "HPE SimpliVity" in canonical_set
    assert "NetApp MetroCluster" in canonical_set
    assert "Oracle Cloud Infrastructure" in canonical_set
