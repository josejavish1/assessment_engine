"""
Phase C Characterization and Regression Test Suite: KPI-to-Claim Semantic Alignment.

Verifies the semantic entailment invariant validate_claim_entailment(claim, evidence):
1. A survey maturity score without qualitative transcript evidence cannot generate specific
   physical hardware claims (e.g., CCTV with blind spots, standalone NVRs, retention < 30 days).
2. Findings derived from survey scores must restrict their scope strictly to process governance,
   audit logging cadence, and operational maturity.
3. Tower T1 payload in working/molins_fresh_e2e must be completely free of unaccredited
   CCTV, NVR, and video surveillance hardware allegations.
"""

from pathlib import Path
import pytest

from assessment_engine.domain.validation.claim_evidence_validator import (
    validate_claim_entailment,
)
from assessment_engine.infrastructure.runtime_paths import ROOT


def test_claim_evidence_entailment_validator():
    """1. validate_claim_entailment rejects physical hardware claims from survey-only evidence."""
    survey_only_evidence = "Vulnerability in physical forensic readiness (Score 1.0 in T1.P3.K3)."
    
    # Prohibited claim: asserts unverified physical hardware defects
    unsupported_hardware_claim = (
        "El sistema de videovigilancia CCTV cuenta con ángulos muertos y NVR autónomos "
        "con retención inferior a treinta días en salas técnicas."
    )
    assert validate_claim_entailment(unsupported_hardware_claim, survey_only_evidence) is False

    # Permitted claim: process/governance operational gap
    valid_governance_claim = (
        "Madurez inicial en cobertura y formalización de registros de acceso y control "
        "de áreas técnicas según autoevaluación declarada. La configuración física y los "
        "periodos de retención permanecen pendientes de contraste pericial."
    )
    assert validate_claim_entailment(valid_governance_claim, survey_only_evidence) is True


def test_tower_1_payload_cctv_nvr_cleanliness():
    """2. Tower T1 payload must be free of hallucinated CCTV and NVR hardware defects."""
    bp_path = ROOT / "working" / "molins_fresh_e2e" / "T1" / "blueprint_t1_payload.json"
    if not bp_path.exists():
        pytest.skip(f"T1 payload not found at {bp_path}")

    text = bp_path.read_text(encoding="utf-8-sig").lower()
    
    forbidden_terms = [
        "cctv",
        "nvr",
        "ángulos muertos",
        "angulos muertos",
        "retención inferior a treinta días",
        "retencion inferior a treinta dias",
    ]
    
    violations = []
    for term in forbidden_terms:
        if term in text:
            violations.append(f"Tower T1 contains unverified term: '{term}'")

    assert not violations, "KPI-to-Claim Misalignment in Tower T1:\n" + "\n".join(violations)
