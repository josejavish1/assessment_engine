"""
Unit test suite for Phase 16 Upstream Ingestion Gating.
Verifies:
1. MissingDataCircuitBreaker catches missing, corrupt, and empty responses without silent drops.
2. EpistemicContextRouter filters transcript fragments to legitimate MECE tower domains.
"""

from assessment_engine.domain.ingestion.missing_data_circuit_breaker import MissingDataCircuitBreaker
from assessment_engine.domain.ingestion.context_router import EpistemicContextRouter


def test_missing_data_circuit_breaker_preserves_missing_kpis():
    """Verify that unparsed or corrupt answers become explicit MISSING_OR_INVALID objects."""
    expected_kpis = [
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K1", "kpi_name": "Access Control"},
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K2", "kpi_name": "Encryption"},
        {"pillar_id": "T4.P4", "pillar_name": "Security", "kpi_id": "T4.P4.K3", "kpi_name": "Audit Logs"},
    ]
    # Simulate parsed scores where K3 is completely missing (e.g. was a stray comma in survey)
    parsed_scores = {
        "T4.P4.K1.PR1": 4.0,
        "T4.P4.K2.PR1": 4.0,
        # T4.P4.K3.PR1 is omitted
    }

    answers = MissingDataCircuitBreaker.inspect_and_filter_kpi_responses(
        tower_id="T4",
        expected_kpis=expected_kpis,
        parsed_scores=parsed_scores,
    )

    assert len(answers) == 3, f"Expected exactly 3 answers, got {len(answers)} (silent drop occurred!)"
    
    k1 = next(a for a in answers if a["kpi_id"] == "T4.P4.K1")
    assert k1["value"] == 4.0
    assert k1["evidence_status"] == "VALIDATED"
    assert k1["validation_state"] == "Exploratoria"

    k3 = next(a for a in answers if a["kpi_id"] == "T4.P4.K3")
    assert k3["value"] is None
    assert k3["evidence_status"] == "MISSING_OR_INVALID"
    assert k3["validation_state"] == "NO_EVIDENCIADO"


def test_epistemic_context_router_isolates_tower_domains():
    """Verify that fragments are routed strictly by MECE domain boundaries."""
    raw_fragments = [
        "En la sala técnica del CPD principal contamos con dos enfriadoras y grupos electrógenos diésel.",
        "Los costes de cloud en Azure y el licenciamiento de VMware Broadcom impactan fuertemente en el presupuesto operativo.",
        "La red troncal utiliza conmutadores Huawei y un tendido punto a punto de fibra oscura a 10 Gbps.",
        "Las básculas de pesaje de camiones de las canteras alimentan la base de datos Prenet en Oracle.",
    ]

    # Test T8 (FinOps & Governance)
    t8_context = EpistemicContextRouter.filter_context_for_tower("T8", raw_fragments)
    assert "costes de cloud en Azure" in t8_context
    assert "enfriadoras" not in t8_context
    assert "fibra oscura" not in t8_context

    # Test T1 (Physical Data Center)
    t1_context = EpistemicContextRouter.filter_context_for_tower("T1", raw_fragments)
    assert "enfriadoras" in t1_context
    assert "costes de cloud" not in t1_context
    assert "básculas de pesaje" not in t1_context

    # Test T3 (Network)
    t3_context = EpistemicContextRouter.filter_context_for_tower("T3", raw_fragments)
    assert "fibra oscura" in t3_context
    assert "enfriadoras" not in t3_context
    assert "costes de cloud" not in t3_context
