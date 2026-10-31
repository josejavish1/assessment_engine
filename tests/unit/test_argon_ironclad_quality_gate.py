# golden-path: ignore
"""Unit tests verifying the ArgonIroncladQualityGate and deterministic pre-flight sieve."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
import pytest

from assessment_engine.infrastructure.quality.argon_gate import (
    ArgonAuditReport,
    ArgonIroncladQualityGate,
    AuditFinding,
    AuditVerdict,
    CryptographicClearanceToken,
    DeterministicPreFlightSieve,
    ViolationCategory,
)


def test_deterministic_pre_flight_sieve_catches_spanish(tmp_path: Path) -> None:
    bad_file = tmp_path / "sample.py"
    bad_file.write_text('def procesar_datos():\n    return "función"\n', encoding="utf-8")

    findings = DeterministicPreFlightSieve.inspect_files(tmp_path, ["sample.py"])
    assert len(findings) >= 1
    categories = {f.category for f in findings}
    assert ViolationCategory.NON_ENGLISH_LEXICON in categories


def test_deterministic_pre_flight_sieve_catches_bare_except(tmp_path: Path) -> None:
    bad_file = tmp_path / "flawed.py"
    bad_file.write_text("try:\n    x = 1\nexcept:\n    pass\n", encoding="utf-8")

    findings = DeterministicPreFlightSieve.inspect_files(tmp_path, ["flawed.py"])
    assert any(f.category == ViolationCategory.ARCHITECTURAL_ANTIPATTERN for f in findings)


def test_mathematical_approval_invariant_enforcement() -> None:
    # 1. Hallucinated PASS with finding must be REJECTED
    bogus_report = ArgonAuditReport(
        verdict=AuditVerdict.PASS,
        zero_bugs_or_antipatterns=True,
        zero_hardcoding_verified=True,
        universal_tier1_enterprise_ready=True,
        strict_english_only_verified=True,
        findings=[
            AuditFinding(
                file_path="src/mod.py",
                line_number=10,
                category=ViolationCategory.BUG_OR_LOGIC_ERROR,
                offending_snippet="x = 1",
                technical_critique="Flawed logic",
                mandatory_remediation="Fix it",
            )
        ],
        forensic_summary="Fake pass",
    )
    assert ArgonIroncladQualityGate._is_mathematically_approved(bogus_report) is False

    # 2. Invariant False must be REJECTED
    invariant_fail = ArgonAuditReport(
        verdict=AuditVerdict.PASS,
        zero_bugs_or_antipatterns=True,
        zero_hardcoding_verified=False,  # Failed check
        universal_tier1_enterprise_ready=True,
        strict_english_only_verified=True,
        findings=[],
        forensic_summary="Hardcoding present",
    )
    assert ArgonIroncladQualityGate._is_mathematically_approved(invariant_fail) is False

    # 3. Clean report must be APPROVED
    clean_report = ArgonAuditReport(
        verdict=AuditVerdict.PASS,
        zero_bugs_or_antipatterns=True,
        zero_hardcoding_verified=True,
        universal_tier1_enterprise_ready=True,
        strict_english_only_verified=True,
        findings=[],
        forensic_summary="Flawless Tier-1 implementation",
    )
    assert ArgonIroncladQualityGate._is_mathematically_approved(clean_report) is True


def test_cryptographic_clearance_token_tamper_proofing() -> None:
    secret = b"tier1_secret_key"
    diff_hash = hashlib.sha256(b"diff content").hexdigest()

    token = CryptographicClearanceToken(
        block_id="PR-1",
        diff_sha256=diff_hash,
        model_used="gemini-4-argon",
        timestamp_utc=time.time(),
        signature="",
    )
    # Manually compute signature
    import hmac
    payload = f"{token.block_id}:{token.diff_sha256}:{token.model_used}:{token.timestamp_utc}".encode("utf-8")
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    valid_token = CryptographicClearanceToken(
        block_id=token.block_id,
        diff_sha256=token.diff_sha256,
        model_used=token.model_used,
        timestamp_utc=token.timestamp_utc,
        signature=sig,
    )

    # Valid diff hash passes
    assert valid_token.verify(secret, diff_hash) is True

    # Mutated diff hash (TOCTOU) fails
    mutated_diff_hash = hashlib.sha256(b"diff mutated").hexdigest()
    assert valid_token.verify(secret, mutated_diff_hash) is False
