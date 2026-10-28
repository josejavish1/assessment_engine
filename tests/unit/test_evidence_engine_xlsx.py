from pathlib import Path

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine


def test_xlsx_ingestion(tmp_path: Path):
    storage_dir = tmp_path / "molins_test"
    storage_dir.mkdir(parents=True, exist_ok=True)

    engine = EvidenceEngine(client_id="molins_test", storage_dir=storage_dir)

    xlsx_source = Path(
        "source_docs/molins/Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    )
    assert xlsx_source.exists(), "Source xlsx must exist"

    new_count = engine.ingest_file(xlsx_source)
    assert new_count > 0, "Should ingest fragments from xlsx"
    assert len(engine.ledger.fragments) == new_count

    # Check deduplication
    duplicate_count = engine.ingest_file(xlsx_source)
    assert duplicate_count == 0, "Re-ingesting same file should yield 0 new fragments"

    # Verify fragment structure
    sample_frag = engine.ledger.fragments[0]
    assert sample_frag.source_uri == str(xlsx_source)
    assert "spreadsheet_row" == sample_frag.location_metadata.get("type")
    assert "hierarchy" in sample_frag.location_metadata
    assert len(sample_frag.content) >= 20
