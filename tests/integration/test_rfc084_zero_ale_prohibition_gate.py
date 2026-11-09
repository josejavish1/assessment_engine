"""Integration Test: RFC 084 Gate 2 (Zero-ALE Prohibition Gate).

Validates end-to-end:
1. Discovery input containing ONLY 3 sentences about Network topology.
2. 9 out of 10 technology towers receive zero direct transcript evidence.
3. Zero towers emit an Annual Loss Expectancy of 0.00.
4. All 9 silent towers are classified as UNOBSERVED_BLINDSPOT.
5. Latent financial risk scales appropriately for a $2B Retail tenant.
"""

from __future__ import annotations

import pytest

from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    derive_in_memory_fair_risks,
)
from assessment_engine.application.services.actuarial_inference_engine import (
    ActuarialInferenceEngine,
    TenantActuarialProfile,
)
from assessment_engine.application.services.semantic_epistemic_router import (
    CANONICAL_TOWERS,
    SemanticEpistemicRouter,
)


def test_rfc084_zero_ale_prohibition_gate_end_to_end() -> None:
    """Verifies that 9 silent towers for a $2B Retail enterprise never emit ALE == 0.00."""
    # 1. Discovery transcript with ONLY network evidence
    minimal_network_transcript = [
        "Core switches and network routing infrastructure.",
        "BGP routing and MPLS WAN links between sites.",
        "Spine leaf switch fabric and VLAN subnet topology.",
    ]

    # 2. Epistemic Graph Router (RFC 084 Phase 1)
    router = SemanticEpistemicRouter(affinity_threshold=0.10)
    routed_packets = router.route_transcript(minimal_network_transcript)

    assert len(routed_packets) == 10
    assert routed_packets["T3"].epistemic_state == "OBSERVED_EXPLICIT"
    assert len(routed_packets["T3"].propositions) >= 1

    # Verify 9 towers are silent
    silent_codes = [c for c in CANONICAL_TOWERS if c != "T3"]
    for code in silent_codes:
        assert routed_packets[code].epistemic_state == "UNOBSERVED_BLINDSPOT"
        assert len(routed_packets[code].propositions) == 0

    # 3. Tenant Profile: $2B Retail enterprise
    tenant_revenue = 2_000_000_000.0
    tenant_profile = TenantActuarialProfile(
        annual_revenue=tenant_revenue,
        industry_vertical="retail",
        employee_headcount=25000,
        currency_code="USD",
    )
    act_engine = ActuarialInferenceEngine(default_profile=tenant_profile)

    # 4. Compile / Derive In-Memory FAIR Risks across all 10 towers
    compiled_portfolio_ales: dict[str, float] = {}

    for code in CANONICAL_TOWERS:
        packet = routed_packets[code]
        # Build payload representation
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
            # Populate observed health checks
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

        # Assert strictly positive ALE for all towers (Zero ALE Prohibition Gate)
        assert (
            tower_total_ale > 0.0
        ), f"VIOLATION OF GATE 2: Tower {code} emitted ALE == 0.00!"

        # For silent towers, assert presence of UNOBSERVED_BLINDSPOT
        if code in silent_codes:
            assert any(
                r.get("epistemic_state") == "UNOBSERVED_BLINDSPOT" for r in flat_risks
            ), f"Silent tower {code} failed to record UNOBSERVED_BLINDSPOT epistemic state"
            # Assert scaled loss: a $2B retailer must not have trivial $10 losses for an unobserved tower
            assert (
                tower_total_ale > 100_000.0
            ), f"Silent tower {code} ALE ({tower_total_ale}) too low for a $2B retailer"

    # 5. Check portfolio totals
    total_enterprise_ale = sum(compiled_portfolio_ales.values())
    assert total_enterprise_ale > 1_000_000.0
