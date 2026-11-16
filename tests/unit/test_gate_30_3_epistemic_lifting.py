"""
Unit Test Suite for GATE-30.3: Kleene 3VL Epistemic Lifting Operator (uparrow_gov).

Validates the formal mathematical lifting operator in SharedFactRecord:
1. Transforms an UNINSTRUMENTED_BLINDSPOT in technical strata into an
   INSTRUMENTED_VERIFIED governance deficit in the ENTERPRISE_GOVERNANCE domain.
2. Mathematically converts unmeasured technical metrics (e.g. vCPU oversubscription)
   into audit-grade governance/telemetry deficit findings.
3. Prohibits lifting facts that are already INSTRUMENTED_VERIFIED.
"""

import pytest

from assessment_engine.domain.ingestion.epistemic_fact_registry import (
    EpistemicState,
    SharedFactRecord,
)


def test_gate_30_3_epistemic_lifting_operator():
    """GATE-30.3: Epistemic Lifting Operator lifts uninstrumented metric to verified governance gap."""
    uninstrumented_fact = SharedFactRecord(
        fact_id="FACT-VCPU_OVERSUBSCRIPTION",
        domain="COMPUTE",
        subject_entity="Compute_Cluster_Nodes_3_and_4",
        metric_name="vCPU_to_pCPU_Allocation_Ratio",
        epistemic_state=EpistemicState.UNINSTRUMENTED_BLINDSPOT,
        observed_value=None,
    )

    # Apply the Epistemic Lifting Operator: uparrow_gov(UNKNOWN) -> VERIFIED_PRESENT
    lifted_governance_fact = uninstrumented_fact.lift_to_governance_deficit()

    assert lifted_governance_fact.fact_id == "FACT-VCPU_OVERSUBSCRIPTION_GOV_DEFICIT"
    assert lifted_governance_fact.domain == "ENTERPRISE_GOVERNANCE"
    assert lifted_governance_fact.epistemic_state == EpistemicState.INSTRUMENTED_VERIFIED
    assert "VERIFIED_ABSENCE_OF_FORMAL_TELEMETRY" in str(lifted_governance_fact.observed_value)
    assert "Verified operational governance deficit" in lifted_governance_fact.allowed_semantic_inference


def test_gate_30_3_prohibits_lifting_verified_facts():
    """GATE-30.3: Operator raises ValueError if invoked on an already verified fact."""
    verified_fact = SharedFactRecord(
        fact_id="FACT-RAM_UTILIZATION",
        domain="COMPUTE",
        subject_entity="Compute_Cluster_Nodes_3_and_4",
        metric_name="Host_RAM_Saturation",
        epistemic_state=EpistemicState.INSTRUMENTED_VERIFIED,
        observed_value="88%",
    )

    with pytest.raises(ValueError, match="Only UNINSTRUMENTED_BLINDSPOT facts can be lifted"):
        verified_fact.lift_to_governance_deficit()
