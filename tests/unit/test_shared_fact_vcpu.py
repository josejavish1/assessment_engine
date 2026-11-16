"""
Phase A Characterization and Regression Test Suite: SharedFactRegistry (vCPU 3VL).

Verifies the Three-Valued Logic (3VL) invariant for vCPU oversubscription:
1. SharedFactRecord enforces INSTRUMENTED_VERIFIED vs UNINSTRUMENTED_BLINDSPOT.
2. When epistemic_state == UNINSTRUMENTED_BLINDSPOT, observed_value must be None and
   allowed_semantic_inference locks strictly to an observability/instrumentation gap.
3. is_claim_allowed() rejects assertions of resource saturation, critical overcommitment,
   or severe oversubscription across all towers.
4. All tower payloads in working/molins_fresh_e2e must adhere to UNKNOWN_MEASUREMENT,
   completely free of 'sobresuscripción', 'sobreasignación', or 'contención de vcpu'.
"""

import json
from pathlib import Path
import pytest

from assessment_engine.domain.ingestion.epistemic_fact_registry import (
    EpistemicState,
    SharedFactRecord,
)
from assessment_engine.infrastructure.runtime_paths import ROOT


def test_shared_fact_vcpu_three_valued_logic_validation():
    """1. SharedFactRecord enforces 3VL: Uninstrumented facts cannot hold observed values."""
    # Attempting to assign an observed ratio to an uninstrumented blindspot must raise ValueError
    with pytest.raises(ValueError, match="Uninstrumented facts cannot hold observed values"):
        SharedFactRecord(
            fact_id="FACT-VCPU_OVERSUBSCRIPTION",
            domain="COMPUTE",
            subject_entity="Compute_Cluster_Nodes_3_and_4",
            metric_name="vCPU_to_pCPU_Allocation_Ratio",
            epistemic_state=EpistemicState.UNINSTRUMENTED_BLINDSPOT,
            observed_value=4.5,
        )

    # Valid uninstrumented blindspot record
    fact = SharedFactRecord(
        fact_id="FACT-VCPU_OVERSUBSCRIPTION",
        domain="COMPUTE",
        subject_entity="Compute_Cluster_Nodes_3_and_4",
        metric_name="vCPU_to_pCPU_Allocation_Ratio",
        epistemic_state=EpistemicState.UNINSTRUMENTED_BLINDSPOT,
        observed_value=None,
    )
    assert fact.epistemic_state == EpistemicState.UNINSTRUMENTED_BLINDSPOT
    assert "Lack of telemetry/instrumentation" in fact.allowed_semantic_inference
    assert "PROHIBITED INFERENCE" in fact.allowed_semantic_inference


def test_shared_fact_vcpu_claim_policy_enforcement():
    """2. is_claim_allowed() strictly forbids severe overcommitment claims for uninstrumented facts."""
    fact = SharedFactRecord(
        fact_id="FACT-VCPU_OVERSUBSCRIPTION",
        domain="COMPUTE",
        subject_entity="Compute_Cluster_Nodes_3_and_4",
        metric_name="vCPU_to_pCPU_Allocation_Ratio",
        epistemic_state=EpistemicState.UNINSTRUMENTED_BLINDSPOT,
        observed_value=None,
    )

    # Permitted claim: telemetry/observability gap
    valid_claim = "La relación vCPU/pCPU se encuentra pendiente de instrumentación telemétrica formal."
    assert fact.is_claim_allowed(valid_claim) is True

    # Prohibited claims asserting technical saturation
    prohibited_claims = [
        "Existe una sobreasignación crítica de vCPU en los hosts.",
        "Se constatan niveles severos de sobresuscripción de vCPU frente a CPU física.",
        "Acusada sobreasignación de vCPU motivada por cargas de control industrial.",
        "Contención de vCPU severa en la infraestructura de virtualización.",
    ]
    for claim in prohibited_claims:
        assert fact.is_claim_allowed(claim) is False, f"Prohibited claim was incorrectly allowed: '{claim}'"


def test_all_tower_payloads_vcpu_unknown_cleanliness():
    """3. All tower payloads in molins_fresh_e2e must be free of unverified vCPU saturation claims."""
    forbidden_terms = [
        "sobreasignación",
        "sobresuscripción",
        "contención de vcpu",
        "sobreasignacion",
        "sobresuscripcion",
    ]
    
    violations = []
    fresh_dir = ROOT / "working" / "molins_fresh_e2e"
    for i in range(1, 11):
        tid = f"T{i}"
        bp_path = fresh_dir / tid / f"blueprint_{tid.lower()}_payload.json"
        if not bp_path.exists():
            continue
        text = bp_path.read_text(encoding="utf-8-sig").lower()
        for term in forbidden_terms:
            if term in text:
                violations.append(f"Tower {tid}: found forbidden term '{term}'")

    assert not violations, "vCPU UNKNOWN_MEASUREMENT invariant violated:\n" + "\n".join(violations)
