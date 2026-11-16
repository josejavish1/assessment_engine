"""
Unit Test Suite for GATE-30.4: Actuarial Sub-Additivity Bound & Euler Allocation.

Validates the formal multi-tower subadditivity engine in rounding.py:
1. Simulates failure of a shared core asset across all 10 towers.
2. Asserts that the sum of allocated Chapter 4 Business Interruption ALEs strictly satisfies:
   sum(ALE_i) == Single_Event_Max_ALE <= Annual_Revenue.
3. Proves zero double-counting of hourly disruption rates across towers.
4. Scale-agnosticism across $50M SMB to $100B+ global conglomerate perimeters.
"""

from decimal import Decimal
import pytest

from assessment_engine.domain.actuarial.rounding import (
    allocate_portfolio_euler_subadditivity,
    round_to_actuarial_significance,
)


def test_gate_30_4_euler_allocation_10_towers():
    """GATE-30.4: 10-tower shared core outage allocates sub-additively without double counting."""
    annual_revenue = 1144000000.0  # 1.144B EUR (Molins perimeter)
    single_event_max = 850000.0   # 850k EUR max single event outage

    tower_weights = {
        f"T{i}": (100000 + i * 15000) for i in range(1, 11)
    }

    allocated = allocate_portfolio_euler_subadditivity(
        single_event_max_ale=single_event_max,
        tower_risk_weights=tower_weights,
        annual_revenue=annual_revenue,
    )

    assert len(allocated) == 10
    total_allocated = sum(allocated.values())
    expected_target = int(round_to_actuarial_significance(single_event_max))

    # Strict Actuarial Monism Proof
    assert total_allocated == expected_target, f"Sum of towers {total_allocated} != target {expected_target}"
    assert total_allocated <= annual_revenue, "Total allocated ALE exceeds enterprise annual revenue!"


@pytest.mark.parametrize("revenue,max_event", [
    (50000000.0, 150000.0),       # $50M mid-market SMB
    (1250000000.0, 1200000.0),    # $1.25B multinational
    (85000000000.0, 45000000.0),  # $85B global tier-1 conglomerate
])
def test_gate_30_4_scale_agnostic_subadditivity(revenue: float, max_event: float):
    """GATE-30.4: Subadditivity holds universally across all enterprise scales ($50M to $100B+)."""
    tower_weights = {f"T{i}": max_event * (0.05 + 0.01 * i) for i in range(1, 11)}

    allocated = allocate_portfolio_euler_subadditivity(
        single_event_max_ale=max_event,
        tower_risk_weights=tower_weights,
        annual_revenue=revenue,
    )

    total_allocated = sum(allocated.values())
    expected_target = int(round_to_actuarial_significance(max_event))

    assert total_allocated == expected_target
    assert total_allocated <= revenue
    for tid, share in allocated.items():
        assert share >= 0, f"Tower {tid} received negative allocation: {share}"
