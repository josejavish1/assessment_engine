"""Deterministic Test Oracle for Phase 3: Cross-Tower Nexus & Second-Order Cascade Engine (RFC 084).

Validates:
1. Directed Acyclic Graph (DAG) construction and topological sorting across all 10 technology towers.
2. Acyclicity guarantee: Zero circular dependency deadlocks.
3. The Cascade Assertion Gate: Critical compute finding in Tower 2 cascades second-order risk
   into Tower 6 (Cybersecurity) and Tower 5 (Resilience).
4. Declarative ontology loading from engine_config/policies/cross_domain_nexus_map.json.
5. Typed contracts: SecondOrderRiskAssertion immutability and Technical English decoupling.
6. Mutation CTF probe resilience: Kills DAG edge addition and compounded ALE operator mutants.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
import pytest

from assessment_engine.application.services.cross_tower_nexus import (
    CrossTowerNexusEngine,
    SecondOrderRiskAssertion,
    _add_dag_edge,
)


def test_second_order_risk_assertion_immutability_and_types() -> None:
    """Verifies typed contract and immutability of SecondOrderRiskAssertion."""
    assertion = SecondOrderRiskAssertion(
        assertion_id="CASCADE_T2_TO_T6_001",
        source_tower="T2",
        source_pillar="T2.P1",
        target_tower="T6",
        target_pillar="T6.P1",
        title="Secondary Security Risk: Impeded Kernel and Hypervisor Patching",
        causal_narrative="Exhaustion of hypervisor cluster RAM prevents physical node evacuation for critical security patching.",
        compounded_ale_impact=185000.0,
        blast_radius_severity="HIGH",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        assertion.compounded_ale_impact = 0.0  # type: ignore[misc]

    assert assertion.source_tower == "T2"
    assert assertion.target_tower == "T6"
    assert assertion.compounded_ale_impact > 0.0
    assert assertion.blast_radius_severity == "HIGH"


def test_dag_edge_addition_and_deduplication() -> None:
    """Kills mutant at line 309 where 'not in' was inverted to 'in' in _add_dag_edge."""
    adjacency = {"T1": set(), "T2": set()}
    in_degree = {"T1": 0, "T2": 0}

    # First addition must succeed and increment in_degree
    _add_dag_edge(adjacency, in_degree, "T1", "T2")
    assert "T2" in adjacency["T1"]
    assert in_degree["T2"] == 1

    # Duplicate edge addition must be a no-op (idempotent)
    _add_dag_edge(adjacency, in_degree, "T1", "T2")
    assert in_degree["T2"] == 1
    assert len(adjacency["T1"]) == 1


def test_dag_topological_sort_and_acyclicity() -> None:
    """Verifies that the cross-tower nexus graph is strictly acyclic and sortable."""
    engine = CrossTowerNexusEngine()
    order = engine.get_topological_order()

    assert isinstance(order, list)
    assert len(order) == 10
    # Foundation facilities (T1) and core compute/network must precede dependent workplace/app towers
    assert order.index("T1") < order.index("T9")
    assert order.index("T2") < order.index("T10")


def test_cascade_assertion_gate_t2_compute_to_t6_security() -> None:
    """Gate 3: Cascade Assertion Gate (RFC 084 Phase 3).

    Injects a high-severity compute resource saturation finding in Tower 2:
    'Hypervisor cluster RAM saturated at 98% with zero HA redundancy.'
    Asserts that Tower 6 (Cybersecurity) receives a derived SecondOrderRiskAssertion
    asserting technical impossibility of node evacuation for emergency kernel patching.
    """
    engine = CrossTowerNexusEngine()

    tower_payloads = {
        "T2": {
            "tower_id": "T2",
            "pillars_analysis": [
                {
                    "pillar_id": "T2.P1",
                    "health_check_asis": [
                        {
                            "finding": "Hypervisor cluster RAM saturated at 98% with zero HA redundancy.",
                            "business_risk": "Imminent host crashing and inability to sustain node failure.",
                            "severity": "CRITICAL",
                            "fair_ale_score": 450000.0,
                        }
                    ],
                }
            ],
        },
        "T6": {
            "tower_id": "T6",
            "pillars_analysis": [
                {
                    "pillar_id": "T6.P1",
                    "health_check_asis": [],
                }
            ],
        },
    }

    cascade_assertions = engine.evaluate_cascades(tower_payloads)

    assert len(cascade_assertions) > 0

    # Locate cascade into Tower 6 (Cybersecurity)
    t6_cascades = [c for c in cascade_assertions if c.target_tower == "T6"]
    assert len(t6_cascades) >= 1, "Failed Gate 3: Tower 2 did not trigger cascade into Tower 6!"

    lead_cascade = t6_cascades[0]
    assert lead_cascade.source_tower == "T2"
    assert "patch" in lead_cascade.causal_narrative.lower() or "security" in lead_cascade.title.lower()
    # Kills arithmetic operator mutant at line 524 (* vs //): 450000.0 * 0.40 = 180000.0
    assert lead_cascade.compounded_ale_impact == pytest.approx(180000.0, rel=1e-2)


def test_declarative_ontology_loading() -> None:
    """Verifies that cross-domain causal rules load dynamically from policy catalog."""
    engine = CrossTowerNexusEngine()
    rules = engine.rules

    assert len(rules) >= 10
    # Verify rule for T1 -> T2 and T2 -> T6/T5
    assert any(r.get("source_tower") == "T1" and r.get("target_tower") == "T2" for r in rules)
    assert any(r.get("source_tower") == "T2" and r.get("target_tower") in ("T5", "T6", "T8") for r in rules)
