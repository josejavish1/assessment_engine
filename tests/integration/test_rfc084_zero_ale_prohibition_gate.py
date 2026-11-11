"""Integration Test: Epistemic Integrity and Prior Governance Gate (SR 11-7).

Replaces the legacy RFC 084 zero-ALE prohibition gate.
Proves that:
1. When 9 of 10 towers receive zero empirical findings, the presentation compiler does NOT fabricate positive synthetic currency.
2. Silent towers are explicitly marked with unassessed/insufficient telemetry status.
3. Observed towers with empirical findings are quantified faithfully without presentation distortions.
"""

from __future__ import annotations

from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    derive_in_memory_fair_risks,
)
from assessment_engine.application.services.semantic_epistemic_router import (
    CANONICAL_TOWERS,
    SemanticEpistemicRouter,
)


def test_epistemic_integrity_and_unassessed_scope_gate() -> None:
    """Verifies that 9 silent towers never fabricate synthetic loss in the presentation compiler."""
    # 1. Discovery transcript with ONLY network evidence
    minimal_network_transcript = [
        "Core switches and network routing infrastructure.",
        "BGP routing and MPLS WAN links between sites.",
        "Spine leaf switch fabric and VLAN subnet topology.",
    ]

    # 2. Epistemic Graph Router
    router = SemanticEpistemicRouter(affinity_threshold=0.10)
    routed_packets = router.route_transcript(minimal_network_transcript)

    assert len(routed_packets) == 10
    assert routed_packets["T3"].epistemic_state == "OBSERVED_EXPLICIT"

    silent_codes = [c for c in CANONICAL_TOWERS if c != "T3"]
    tenant_revenue = 2_000_000_000.0

    compiled_portfolio_ales: dict[str, float] = {}

    for code in CANONICAL_TOWERS:
        packet = routed_packets[code]
        payload: dict = {
            "tower_id": code,
            "document_meta": {
                "tower_id": code,
                "annual_revenue": tenant_revenue,
                "industry_vertical": "retail",
            },
            "financial_telemetry": {
                "annual_revenue": tenant_revenue,
            },
            "pillars_analysis": [],
        }

        if packet.epistemic_state == "OBSERVED_EXPLICIT":
            payload["pillars_analysis"] = [
                {
                    "pillar_id": f"{code}.P1",
                    "target_state": "Core Redundancy",
                    "health_check_asis": [
                        {
                            "finding": prop.text,
                            "business_risk": "Network outage and packet loss during peak operations",
                            "threat_event_frequency": 3.0,
                            "loss_magnitude": 3.5,
                            "fair_ale_score": 250000.0,
                            "fair_p90_score": 600000.0,
                        }
                        for prop in packet.propositions
                    ],
                }
            ]

        flat_risks, risks_by_pillar = derive_in_memory_fair_risks(
            payload,
            doc_lang="en",
            currency="$",
            rate_mult=1.0,
        )

        assert len(flat_risks) > 0, f"Tower {code} produced 0 risk records"
        tower_total_ale = sum(float(r.get("ale") or 0.0) for r in flat_risks)
        compiled_portfolio_ales[code] = tower_total_ale

        if code in silent_codes:
            # Epistemic Honesty Gate: Silent towers must NOT fabricate positive currency in presentation
            assert tower_total_ale == 0.0, (
                f"Governance Gate Violation: Silent tower {code} fabricated positive currency {tower_total_ale} "
                f"without empirical findings!"
            )
            assert any(
                r.get("epistemic_state") == "UNASSESSED_OUT_OF_SCOPE" for r in flat_risks
            )
            assert any(
                r.get("ale_str") == "UNQUANTIFIED" for r in flat_risks
            )
        else:
            # Observed tower carries empirical quantitative valuation
            assert tower_total_ale > 0.0
            assert any(r.get("ale_str") != "UNQUANTIFIED" for r in flat_risks)
