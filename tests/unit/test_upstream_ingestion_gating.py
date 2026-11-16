"""
Unit test suite for Phase 16 Upstream Ingestion Gating.

Verifies:
1. MissingDataCircuitBreaker catches missing, corrupt, boolean, and empty responses without silent drops.
2. EpistemicContextRouter derives domain tokens dynamically from canonical tower schemas and performs ArgMax Primary Custody routing.
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
    parsed_scores = {
        "T4.P4.K1.PR1": 4.0,
        "T4.P4.K2.PR1": 4.0,
        "T4.P4.K4.PR1": True,
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


def test_epistemic_context_router_dynamic_ontology_derivation():
    """Verify that domain tokens are derived dynamically from tower definitions without static dictionaries."""
    sample_definition = {
        "tower_name": "Advanced Quantum Compute & Cryptography",
        "pillars": [
            {
                "pillar_name": "Post-Quantum Cryptographic Readiness",
                "kpis": [
                    {"kpi_name": "Lattice-Based Key Encapsulation Mechanisms"},
                    {"kpi_name": "Stateful Hash-Based Signature Migration"},
                ],
            }
        ],
    }

    tokens = EpistemicContextRouter.derive_domain_tokens(sample_definition)
    assert "quantum" in tokens
    assert "cryptography" in tokens
    assert "lattice" in tokens
    assert "signature" in tokens
    assert "this" not in tokens  # Stop word exclusion


def test_epistemic_context_router_argmax_primary_custody_isolation():
    """Verify that fragments are routed strictly to their ArgMax primary custody tower."""
    raw_fragments = [
        "Data center cooling facilities maintain physical temperature and humidity in server rooms.",
        "IT portfolio governance and budget planning steer strategic capex and opex allocations.",
        "Core network routing switches manage dark fiber perimeter connections.",
    ]

    t1_context = EpistemicContextRouter.filter_context_for_tower("T1", raw_fragments)
    assert "cooling facilities" in t1_context
    assert "budget planning" not in t1_context
    assert "network routing" not in t1_context

    t8_context = EpistemicContextRouter.filter_context_for_tower("T8", raw_fragments)
    assert "budget planning" in t8_context
    assert "cooling facilities" not in t8_context
    assert "network routing" not in t8_context


def test_epistemic_context_router_fails_closed_on_unrelated_text():
    """Verify that unrelated text produces empty context (fail-closed), eliminating cross-tower leakage."""
    unrelated_fragments = [
        "Corporate catering menus were updated for executive dining.",
        "Annual employee performance review cycles open next quarter.",
    ]
    t1_context = EpistemicContextRouter.filter_context_for_tower("T1", unrelated_fragments)
    assert t1_context == "", f"Expected fail-closed empty context, got: '{t1_context}'"
