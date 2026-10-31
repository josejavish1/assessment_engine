"""Unit tests for in-memory functional compiler derivation (RFC-025 / SSOT)."""

from __future__ import annotations

import pytest

from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    derive_in_memory_fair_risks,
    derive_in_memory_maturity_matrix,
)


@pytest.fixture
def sample_blueprint_payload() -> dict:
    """Fixture providing synthetic blueprint payload with pillars and health checks."""
    return {
        "document_meta": {
            "tower_code": "T2",
            "tower_name": "Hybrid Compute & Platforms",
            "client_name": "Acme Global Industries",
            "language": "en",
        },
        "pillars_analysis": [
            {
                "pillar_id": "T2.P1",
                "pillar_name": "Compute Foundation & Virtualization",
                "score": 2.4,
                "health_check_asis": [
                    {
                        "target_state": "Virtualization Lifecycle Management",
                        "finding": "Virtualization host lifecycle relies on manual ad-hoc firmware maintenance.",
                        "business_risk": "Elevated hypervisor vulnerability and unscheduled downtime.",
                        "threat_event_frequency": 4.0,
                        "loss_magnitude": 3.0,
                        "fair_ale_score": 15000.0,
                        "fair_p90_score": 35000.0,
                    }
                ],
            },
            {
                "pillar_id": "T2.P2",
                "pillar_name": "Container Platform & Kubernetes",
                "score": 3.8,
                "health_check_asis": [
                    {
                        "target_state": "Cluster Autoscaling",
                        "finding": "Kubernetes worker node autoscaling lacks automated cluster provisioning.",
                        "business_risk": "Capacity constraints during seasonal traffic spikes.",
                        "threat_event_frequency": 2.5,
                        "loss_magnitude": 2.0,
                        "fair_ale_score": 5000.0,
                        "fair_p90_score": 12000.0,
                    }
                ],
            },
        ],
    }


def test_derive_in_memory_fair_risks(sample_blueprint_payload: dict) -> None:
    """Verify in-memory extraction of FAIR risk scenarios without disk I/O."""
    flat_risks, risks_by_pillar = derive_in_memory_fair_risks(
        sample_blueprint_payload, doc_lang="en", currency="$", rate_mult=1.0
    )

    assert len(flat_risks) == 2
    assert "Compute Foundation & Virtualization" in risks_by_pillar
    assert "Container Platform & Kubernetes" in risks_by_pillar

    risk1 = flat_risks[0]
    assert risk1["id"] == "RVS01"
    assert risk1["tef"] == 4.0
    assert risk1["lm"] == 3.0
    assert risk1["ale"] == 15000.0
    assert risk1["p90"] == 35000.0
    assert "$" in risk1["ale_str"]


def test_derive_in_memory_maturity_matrix(sample_blueprint_payload: dict) -> None:
    """Verify in-memory extraction of maturity assessment rows without disk I/O."""
    rows = derive_in_memory_maturity_matrix(sample_blueprint_payload, doc_lang="en")

    assert len(rows) == 2

    row1 = rows[0]
    assert row1["pillar_id"] == "T2.P1"
    assert row1["score"] == 2.4
    assert "Virtualization host lifecycle" in row1["justification"]

    row2 = rows[1]
    assert row2["pillar_id"] == "T2.P2"
    assert row2["score"] == 3.8
    assert "Kubernetes worker node" in row2["justification"]
