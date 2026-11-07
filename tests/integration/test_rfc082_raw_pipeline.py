"""Integration test for RFC 082 Universal Raw Evidence Ingestion Pipeline."""

import docx
import json
import pytest
from pathlib import Path

from assessment_engine.application.pipelines.raw_evidence_ingestion_pipeline import (
    RawEvidenceIngestionPipeline,
)
from assessment_engine.domain.schemas.epistemic_ledger import EpistemicLedger


def test_rfc082_end_to_end_raw_pipeline_execution(tmp_path: Path):
    output_dir = tmp_path / "working" / "client_alpha"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a raw transcript with STT corruptions and technical statements
    transcript_docx = tmp_path / "interview_transcript.docx"
    doc = docx.Document()
    doc.add_paragraph("Interviewer: Tell us about the virtualization and compute platform.")
    doc.add_paragraph("Lead Architect: We have simplivity nodes running VMware vSphere with severe RAM saturation.")
    doc.add_paragraph("Interviewer: How is offsite backup managed?")
    doc.add_paragraph("Lead Architect: We use stretch microplaster and export archives to occlout.")
    doc.save(str(transcript_docx))

    # 2. Create empirical questionnaire scores
    responses_txt = tmp_path / "responses.txt"
    responses_txt.write_text(
        "T2.P1.K1.PR1    4.5    Capacity managed proactively\n"
        "T3.P1.K1.PR1    2.0    Storage migration ongoing\n",
        encoding="utf-8",
    )

    # 3. Execute the pipeline
    pipeline = RawEvidenceIngestionPipeline(
        client_id="client_alpha",
        output_dir=output_dir,
    )

    ledger = pipeline.run(
        transcript_files=[transcript_docx],
        empirical_files=[responses_txt],
    )

    # 4. Verify in-memory ledger
    assert isinstance(ledger, EpistemicLedger)
    assert ledger.client_id == "client_alpha"
    assert len(ledger.epistemic_entries) > 0

    # Verify that phonetic corruptions were resolved in the assertions or fragments
    t2_entry = next((e for e in ledger.epistemic_entries if e.domain_taxonomy_ref == "T2"), None)
    assert t2_entry is not None
    # Check that "simply" was normalized to "HPE SimpliVity" in the supporting fragment
    assert any("HPE SimpliVity" in f.canonical_assertion for f in t2_entry.supporting_fragments)

    # Verify dissonance detection (Survey claims 4.5/5.0 proactive, but Architect confirms RAM saturation)
    assert t2_entry.dissonance_flag is True
    assert "reality gap" in t2_entry.dissonance_analysis.lower()

    # 5. Verify persisted file
    persisted_path = output_dir / "epistemic_ledger.json"
    assert persisted_path.exists()
    data = json.loads(persisted_path.read_text(encoding="utf-8"))
    assert data["client_id"] == "client_alpha"
    assert len(data["epistemic_entries"]) == len(ledger.epistemic_entries)

    # 6. Verify cryptographic digest calculation
    digest = ledger.calculate_integrity_hash()
    assert len(digest) == 64
