"""Integration Test: RFC 084 Gate 3 (Cascade Assertion Gate).

Validates end-to-end:
1. Multi-tower portfolio payload where Tower 2 (Compute) contains critical memory saturation.
2. Cross-Tower Nexus DAG engine processes topological dependencies across all 10 towers.
3. Tower 6 (Cybersecurity) automatically receives a derived SecondOrderRiskAssertion.
4. The causal narrative directly links lack of memory headroom to patch postponement.
5. Topological sorting guarantees zero circular dependency deadlocks.
"""

from __future__ import annotations

import pytest

from assessment_engine.application.services.cross_tower_nexus import (
    CrossTowerNexusEngine,
    SecondOrderRiskAssertion,
)


def test_rfc084_cascade_assertion_gate_end_to_end() -> None:
    """Gate 3: Cross-Tower Nexus Cascade Assertion Gate."""
    engine = CrossTowerNexusEngine()

    # Verify DAG acyclicity invariant across all 10 canonical towers
    order = engine.get_topological_order()
    assert len(order) == 10
    assert len(set(order)) == 10  # Zero duplicates or cycles

    # Construct complete 10-tower portfolio payload
    portfolio = {
        f"T{i}": {
            "tower_id": f"T{i}",
            "pillars_analysis": [
                {
                    "pillar_id": f"T{i}.P1",
                    "health_check_asis": [],
                }
            ],
        }
        for i in range(1, 11)
    }

    # Inject critical memory saturation into Tower 2
    portfolio["T2"]["pillars_analysis"][0]["health_check_asis"] = [
        {
            "finding": "Hypervisor cluster RAM saturated at 98% with zero HA redundancy.",
            "business_risk": "Imminent host crashing and inability to evacuate workloads.",
            "severity": "CRITICAL",
            "fair_ale_score": 500000.0,
        }
    ]

    # Evaluate systemic cross-tower cascades
    cascades = engine.evaluate_cascades(portfolio)

    assert len(cascades) > 0

    # Verify Tower 6 (Cybersecurity) received the derived second-order risk assertion
    t6_cascades = [c for c in cascades if c.target_tower == "T6"]
    assert len(t6_cascades) >= 1, "Violation of Gate 3: Tower 6 received 0 cascade assertions!"

    sec_cascade = t6_cascades[0]
    assert isinstance(sec_cascade, SecondOrderRiskAssertion)
    assert sec_cascade.source_tower == "T2"
    assert sec_cascade.target_tower == "T6"
    assert sec_cascade.blast_radius_severity == "HIGH"
    assert sec_cascade.compounded_ale_impact > 0.0
    assert "patch" in sec_cascade.causal_narrative.lower() or "security" in sec_cascade.title.lower()
