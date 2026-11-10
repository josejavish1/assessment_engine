"""Unit tests for the Universal Deterministic CMMI Coherence Gatekeeper."""

import pytest
from assessment_engine.domain.coherence_gatekeeper import (
    FindingSeverity,
    reconcile_subcontrol_cmmi,
)


def test_critical_finding_clamps_cmmi_to_1_25() -> None:
    # A client claims PAM = 4.50 in survey, but audit found shared root credentials (CRITICAL)
    findings = [{"severity": "CRITICAL", "title": "Shared local root credentials without PAM"}]
    res = reconcile_subcontrol_cmmi(raw_survey_score=4.50, linked_findings=findings)

    assert res.final_cmmi == 1.25
    assert res.raw_self_assessment == 4.50
    assert res.optimism_bias_delta == 3.25
    assert res.override_triggered is True
    assert res.dominant_finding_severity == FindingSeverity.CRITICAL
    assert "clamped to 1.25" in res.audit_rationale


def test_high_finding_clamps_cmmi_to_1_75() -> None:
    findings = [{"severity": "HIGH", "title": "Untested DR backups"}]
    res = reconcile_subcontrol_cmmi(raw_survey_score=3.80, linked_findings=findings)

    assert res.final_cmmi == 1.75
    assert res.override_triggered is True


def test_clean_optimizing_control_preserved() -> None:
    # A mature control with no findings maintains its legitimate high score
    findings = []
    res = reconcile_subcontrol_cmmi(raw_survey_score=4.25, linked_findings=findings, evidence_verified=True)

    assert res.final_cmmi == 4.25
    assert res.override_triggered is False
    assert res.optimism_bias_delta == 0.0


def test_unverified_optimism_without_evidence_clamped() -> None:
    # Claiming Level 4 without audit evidence verification is capped at 2.75
    findings = []
    res = reconcile_subcontrol_cmmi(raw_survey_score=4.50, linked_findings=findings, evidence_verified=False)

    assert res.final_cmmi == 2.75
    assert res.override_triggered is True


def test_compiler_barrier_detects_malformed_ast() -> None:
    from assessment_engine.domain.coherence_gatekeeper import (
        EpistemicCompilationException,
        EpistemicCompilerBarrier,
    )
    with pytest.raises(EpistemicCompilationException, match="FATAL: AST is empty"):
        EpistemicCompilerBarrier.assert_zero_defect_invariants(None, "dummy.json")


def test_compiler_barrier_detects_missing_headings() -> None:
    from assessment_engine.domain.coherence_gatekeeper import (
        EpistemicCompilationException,
        EpistemicCompilerBarrier,
    )
    from assessment_engine.domain.schemas.ast import DocumentAST, ParagraphNode
    doc = DocumentAST(title="Test Document", nodes=[ParagraphNode(text="Just body text without headings")])
    with pytest.raises(EpistemicCompilationException, match="FATAL: AST missing primary headings"):
        EpistemicCompilerBarrier.assert_zero_defect_invariants(doc, "dummy.json")
