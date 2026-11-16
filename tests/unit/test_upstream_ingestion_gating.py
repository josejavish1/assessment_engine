"""
Unit test suite for Phase 16 Upstream Ingestion Gating.

Verifies:
1. MissingDataCircuitBreaker catches missing, corrupt, boolean, and empty responses without silent drops.
2. EpistemicContextRouter filters transcript fragments to legitimate MECE tower domains using word boundaries.
"""

from assessment_engine.domain.ingestion.missing_data_circuit_breaker import MissingDataCircuitBreaker
from assessment_engine.domain.ingestion.context_router import EpistemicContextRouter


def test_missing_data_circuit_breaker_preserves_missing_kpis():
    """Verify that unparsed, corrupt, or boolean answers become explicit MISSING_OR_INVALID objects."""
    expected_kpis = [
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K1", "kpi_name": "Access Control"},
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K2", "kpi_name": "Encryption"},
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K3", "kpi_name": "Audit Logs"},
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K4", "kpi_name": "Boolean Trap"},
    ]
    # Simulate parsed scores where K3 is missing and K4 is a boolean True (should be rejected)
    parsed_scores = {
        "T4.P4.K1.PR1": 4.0,
        "T4.P4.K2.PR1": 4.0,
        "T4.P4.K4.PR1": True,
        # T4.P4.K3.PR1 is omitted
    }

    answers = MissingDataCircuitBreaker.inspect_and_filter_kpi_responses(
        tower_id="T4",
        expected_kpis=expected_kpis,
        parsed_scores=parsed_scores,
    )

    assert len(answers) == 4, f"Expected exactly 4 answers, got {len(answers)}"

    k1 = next(a for a in answers if a["kpi_id"] == "T4.P4.K1")
    assert k1["value"] == 4.0
    assert k1["evidence_status"] == "VALIDATED"
    assert k1["validation_state"] == "EXPLORATORY"

    k3 = next(a for a in answers if a["kpi_id"] == "T4.P4.K3")
    assert k3["value"] is None
    assert k3["evidence_status"] == "MISSING_OR_INVALID"
    assert k3["validation_state"] == "UNOBSERVED"

    k4 = next(a for a in answers if a["kpi_id"] == "T4.P4.K4")
    assert k4["value"] is None
    assert k4["evidence_status"] == "MISSING_OR_INVALID"
    assert k4["validation_state"] == "UNOBSERVED"


def test_epistemic_context_router_isolates_tower_domains():
    """Verify that fragments are routed strictly by MECE domain boundaries without substring bugs."""
    raw_fragments = [
        "The primary data center facilities utilize two redundant chillers and diesel backup generators.",
        "Cloud spend in public cloud and operating budget constraints directly impact the annual IT strategy.",
        "The core network backbone leverages redundant switches and a point to point dark fiber 10 Gbps interconnect.",
        "Industrial SCADA telemetry controllers and shop floor weighbridge systems feed the legacy ERP database.",
    ]

    # Test T8 (FinOps & Governance)
    t8_context = EpistemicContextRouter.filter_context_for_tower("T8", raw_fragments)
    assert "Cloud spend" in t8_context
    assert "chillers" not in t8_context
    assert "dark fiber" not in t8_context

    # Test T1 (Physical Data Center)
    t1_context = EpistemicContextRouter.filter_context_for_tower("T1", raw_fragments)
    assert "chillers" in t1_context
    assert "Cloud spend" not in t1_context
    assert "weighbridge" not in t1_context

    # Test T3 (Network)
    t3_context = EpistemicContextRouter.filter_context_for_tower("T3", raw_fragments)
    assert "dark fiber" in t3_context
    assert "chillers" not in t3_context
    assert "Cloud spend" not in t3_context


def test_epistemic_context_router_prevents_substring_false_positives():
    """Verify that short keywords like 'ot' do not match 'not', 'both', or 'protocol'."""
    unrelated_fragments = [
        "This is not a valid server configuration.",
        "Both systems follow standard network protocol.",
        "Remote management is enabled across all units.",
    ]
    t10_context = EpistemicContextRouter.filter_context_for_tower("T10", unrelated_fragments)
    assert t10_context == "", f"Expected empty context (fail-closed), but got: {t10_context}"
