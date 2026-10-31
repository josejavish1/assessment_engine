"""Infrastructure-grade unit tests for Deterministic Artifact Registry (RFC-023)."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path
import pytest

from assessment_engine.infrastructure.artifacts import (
    ArtifactContext,
    ArtifactFormat,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactPathResolver,
    ArtifactRegistry,
    DocumentType,
    InvalidArtifactTokenError,
    PresentationFilenameBuilder,
)


def test_sanitize_token_edge_cases() -> None:
    """Verify strict POSIX token sanitization against path traversal, diacritics, and symbols."""
    # Accented Latin characters
    assert ArtifactPathResolver.sanitize_token("Crème Brûlée & Co.") == "creme_brulee_co"
    # Currency symbols and special characters
    assert ArtifactPathResolver.sanitize_token("Global $100M Corp € ¥") == "global_100m_corp"
    # Path traversal attempts
    assert ArtifactPathResolver.sanitize_token("../../etc/passwd") == "etc_passwd"
    # Uppercase and spaces
    assert ArtifactPathResolver.sanitize_token("  TOYOTA MOTOR CORP  ") == "toyota_motor_corp"

    # Non-Latin CJK and Arabic enterprise names
    cjk_token = ArtifactPathResolver.sanitize_token("トヨタ自動車")
    assert cjk_token.startswith("tok_")
    arabic_token = ArtifactPathResolver.sanitize_token("بنك قطر")
    assert arabic_token.startswith("tok_")

    # Blank and invalid tokens
    with pytest.raises(InvalidArtifactTokenError):
        ArtifactPathResolver.sanitize_token("   ")

    with pytest.raises(InvalidArtifactTokenError):
        ArtifactPathResolver.sanitize_token("???---###")


def test_build_physical_filename() -> None:
    """Verify deterministic POSIX physical filename format."""
    ctx = ArtifactContext(
        tenant_id="global_bank",
        assessment_id="asmt_2026_q1",
        period="2026q1",
        domain_unit_id="cloud_operations",
        doc_type=DocumentType.TECHNICAL_ANNEX,
        locale="en_us",
        extension=ArtifactFormat.DOCX,
    )
    sha_dummy = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    filename = ArtifactPathResolver.build_physical_filename(ctx, version=1, sha256_full=sha_dummy)

    expected = "global_bank_2026q1_cloud_operations_tech_annex_en_us_v001_e3b0c44298fc.docx"
    assert filename == expected


def test_registry_registration_and_idempotence(tmp_path: Path) -> None:
    """Verify deliverable registration, cryptographic tracking, and idempotency."""
    registry = ArtifactRegistry(
        base_storage_dir=tmp_path,
        tenant_id="enterprise_corp",
        assessment_id="asmt_001",
    )
    ctx = ArtifactContext(
        tenant_id="enterprise_corp",
        assessment_id="asmt_001",
        period="202610",
        domain_unit_id="tower_compute",
        doc_type=DocumentType.TECHNICAL_BLUEPRINT,
        locale="en",
        extension=ArtifactFormat.DOCX,
    )

    # Create dummy source artifact
    sample_file = tmp_path / "sample_v1.docx"
    sample_file.write_bytes(b"Initial binary payload content.")

    # 1. First registration -> version 1
    rec1 = registry.register_artifact(ctx, sample_file, generator_engine="engine_v1")
    assert rec1.version == 1
    assert "v001" in rec1.physical_filename

    # Verify physical file exists and matches
    latest_path = registry.get_latest_artifact(
        domain_unit_id="tower_compute",
        doc_type=DocumentType.TECHNICAL_BLUEPRINT,
        locale="en",
        extension=ArtifactFormat.DOCX,
    )
    assert latest_path.exists()
    assert latest_path.read_bytes() == b"Initial binary payload content."

    # 2. Idempotent re-registration of identical content -> returns same version 1 without duplication
    rec1_repeat = registry.register_artifact(ctx, sample_file, generator_engine="engine_v1")
    assert rec1_repeat.version == 1
    assert rec1_repeat.sha256_full == rec1.sha256_full

    # 3. Modification of content -> version 2
    sample_file.write_bytes(b"Updated binary payload content with new findings.")
    rec2 = registry.register_artifact(ctx, sample_file, generator_engine="engine_v1")
    assert rec2.version == 2
    assert "v002" in rec2.physical_filename
    assert rec2.sha256_full != rec1.sha256_full

    # Latest artifact points to version 2
    latest_path_v2 = registry.get_latest_artifact(
        domain_unit_id="tower_compute",
        doc_type=DocumentType.TECHNICAL_BLUEPRINT,
        locale="en",
        extension=ArtifactFormat.DOCX,
    )
    assert latest_path_v2.name == rec2.physical_filename
    assert latest_path_v2.read_bytes() == b"Updated binary payload content with new findings."


def test_tampering_detection(tmp_path: Path) -> None:
    """Verify cryptographic tampering detection raises ArtifactIntegrityError."""
    registry = ArtifactRegistry(
        base_storage_dir=tmp_path,
        tenant_id="security_bank",
        assessment_id="asmt_tamper",
    )
    ctx = ArtifactContext(
        tenant_id="security_bank",
        assessment_id="asmt_tamper",
        period="202610",
        domain_unit_id="core_ledger",
        doc_type=DocumentType.EXECUTIVE_REPORT,
        locale="en",
        extension=ArtifactFormat.PDF,
    )
    sample_file = tmp_path / "valid.pdf"
    sample_file.write_bytes(b"Legitimate executive summary.")

    registry.register_artifact(ctx, sample_file)

    latest_path = registry.get_latest_artifact(
        domain_unit_id="core_ledger",
        doc_type=DocumentType.EXECUTIVE_REPORT,
        locale="en",
        extension=ArtifactFormat.PDF,
        verify_integrity=True,
    )
    assert latest_path.exists()

    # Simulate unauthorized file tampering on disk
    latest_path.write_bytes(b"Tampered payload with altered financial numbers.")

    with pytest.raises(ArtifactIntegrityError) as exc_info:
        registry.get_latest_artifact(
            domain_unit_id="core_ledger",
            doc_type=DocumentType.EXECUTIVE_REPORT,
            locale="en",
            extension=ArtifactFormat.PDF,
            verify_integrity=True,
        )
    assert "Cryptographic tampering detected" in str(exc_info.value)


def test_concurrent_registrations(tmp_path: Path) -> None:
    """Verify thread-safe atomic manifest mutations under parallel execution."""
    registry = ArtifactRegistry(
        base_storage_dir=tmp_path,
        tenant_id="multi_tenant_corp",
        assessment_id="asmt_concurrent",
    )

    def register_single(idx: int) -> int:
        unit_id = f"tower_{idx}"
        ctx = ArtifactContext(
            tenant_id="multi_tenant_corp",
            assessment_id="asmt_concurrent",
            period="2026q1",
            domain_unit_id=unit_id,
            doc_type=DocumentType.TECHNICAL_ANNEX,
            locale="en",
            extension=ArtifactFormat.DOCX,
        )
        src = tmp_path / f"source_{idx}.docx"
        src.write_bytes(f"Binary payload for unit {idx}".encode("utf-8"))
        rec = registry.register_artifact(ctx, src)
        return rec.version

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(register_single, i) for i in range(12)]
        for f in concurrent.futures.as_completed(futures):
            assert f.result() == 1

    # Verify all 12 entries exist in manifest
    artifacts = registry.list_artifacts()
    assert len(artifacts) == 12


def test_late_binding_presentation_and_content_disposition() -> None:
    """Verify late-binding commercial filename and RFC 5987 / RFC 6266 headers."""
    ctx = ArtifactContext(
        tenant_id="acme_holding",
        assessment_id="asmt_99",
        period="202610",
        domain_unit_id="cybersecurity",
        doc_type=DocumentType.EXECUTIVE_REPORT,
        locale="fr",
        extension=ArtifactFormat.DOCX,
    )
    from assessment_engine.infrastructure.artifacts.domain import ArtifactVersionRecord

    rec = ArtifactVersionRecord(
        version=2,
        physical_filename="acme_holding_202610_cybersecurity_exec_report_fr_v002_abcdef123456.docx",
        relative_path="artifacts/acme_holding_202610_cybersecurity_exec_report_fr_v002_abcdef123456.docx",
        sha256_full="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        size_bytes=1024,
        generated_at_utc="2026-10-31T12:00:00Z",
        generator_engine="test_engine",
        presentation_metadata={
            "tenant_display_name": "Acme International",
            "domain_unit_display": "Cybersécurité & Résilience",
            "doc_title_localized": "Rapport Exécutif de Maturité",
        },
    )

    display_name = PresentationFilenameBuilder.build_display_filename(rec, ctx)
    assert display_name == "Acme International - Rapport Exécutif de Maturité - Cybersécurité & Résilience (202610) v2.docx"

    header = PresentationFilenameBuilder.build_http_content_disposition(display_name)
    assert "attachment;" in header
    assert "filename=" in header
    assert "filename*=UTF-8''" in header
