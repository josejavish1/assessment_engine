"""Unit tests for Euler Marginal Risk Allocation and Hare-Niemeyer Rounding Engine."""

from __future__ import annotations

from decimal import Decimal
import random
import pytest

from assessment_engine.domain.actuarial.euler_allocator import (
    EulerAllocationResult,
    EulerPortfolioAllocator,
    PortfolioEulerDecomposition,
)


def test_euler_allocation_10_towers_molins() -> None:
    standalone_ales = {
        "T1": 62093.0,
        "T2": 104190.0,
        "T3": 64640.0,
        "T4": 104537.0,
        "T5": 84650.0,
        "T6": 250167.0,
        "T7": 25498.0,
        "T8": 175129.0,
        "T9": 17929.0,
        "T10": 73182.0,
    }
    # Expected gross sum: 962,015 EUR. Let target net be 819,398 EUR (~14.8% copula discount)
    target_net = 819398.0

    decomp = EulerPortfolioAllocator.allocate_portfolio(
        standalone_ales=standalone_ales,
        total_portfolio_ale=target_net,
        currency_iso="EUR",
    )

    assert isinstance(decomp, PortfolioEulerDecomposition)
    assert decomp.currency_iso == "EUR"
    assert len(decomp.allocations) == 10
    assert decomp.subtotal_gross_undiversified_ale == 962015
    assert decomp.total_net_consolidated_ale == 819398
    assert decomp.actuarial_copula_adjustment_ale == -142617
    assert decomp.actuarial_copula_overlap_pct == Decimal("14.8")

    # Check horizontal accounting identity on every single row
    for row in decomp.allocations:
        assert row.standalone_ale + row.diversification_adjustment == row.euler_net_contribution
        assert row.diversification_adjustment <= 0
        assert row.euler_net_contribution >= 0

    # Check vertical identities
    assert sum(r.standalone_ale for r in decomp.allocations) == decomp.subtotal_gross_undiversified_ale
    assert sum(r.diversification_adjustment for r in decomp.allocations) == decomp.actuarial_copula_adjustment_ale
    assert sum(r.euler_net_contribution for r in decomp.allocations) == decomp.total_net_consolidated_ale
    assert sum(r.portfolio_weight_pct for r in decomp.allocations) == Decimal("100.0")


def test_euler_allocation_6_towers_starling() -> None:
    standalone_ales = {
        "T1": 253624.0,
        "T3": 37053.0,
        "T5": 144840.0,
        "T6": 144840.0,
        "T8": 158218.0,
        "T10": 51671.0,
    }
    target_net = 646741.0

    decomp = EulerPortfolioAllocator.allocate_portfolio(
        standalone_ales=standalone_ales,
        total_portfolio_ale=target_net,
        currency_iso="GBP",
    )

    assert len(decomp.allocations) == 6
    assert decomp.currency_iso == "GBP"
    assert sum(r.portfolio_weight_pct for r in decomp.allocations) == Decimal("100.0")
    assert decomp.subtotal_gross_undiversified_ale + decomp.actuarial_copula_adjustment_ale == decomp.total_net_consolidated_ale


def test_single_tower_degenerate_case() -> None:
    standalone = {"T1": 50000.0}
    decomp = EulerPortfolioAllocator.allocate_portfolio(
        standalone_ales=standalone,
        total_portfolio_ale=50000.0,
        currency_iso="USD",
    )

    assert len(decomp.allocations) == 1
    assert decomp.allocations[0].standalone_ale == 50000
    assert decomp.allocations[0].diversification_adjustment == 0
    assert decomp.allocations[0].euler_net_contribution == 50000
    assert decomp.allocations[0].portfolio_weight_pct == Decimal("100.0")
    assert decomp.actuarial_copula_adjustment_ale == 0


def test_randomized_scenarios_identities() -> None:
    currencies = ["USD", "EUR", "GBP", "JPY", "CHF"]
    random.seed(42)

    for _ in range(50):
        curr = random.choice(currencies)
        n_towers = random.randint(2, 10)
        selected_towers = [f"T{i}" for i in range(1, n_towers + 1)]

        # Generate realistic random ALEs between 5,000 and 5,000,000
        ales = {t: float(random.randint(5_000, 5_000_000)) for t in selected_towers}
        gross = sum(ales.values())
        # Random diversification discount between 5% and 35%
        discount_factor = random.uniform(0.65, 0.95)
        net = gross * discount_factor

        decomp = EulerPortfolioAllocator.allocate_portfolio(
            standalone_ales=ales,
            total_portfolio_ale=net,
            currency_iso=curr,
        )

        # Validate that the Pydantic model validator passes and identities hold
        assert decomp.subtotal_gross_undiversified_ale + decomp.actuarial_copula_adjustment_ale == decomp.total_net_consolidated_ale
        assert sum(r.euler_net_contribution for r in decomp.allocations) == decomp.total_net_consolidated_ale
        assert sum(r.portfolio_weight_pct for r in decomp.allocations) == Decimal("100.0")
        for r in decomp.allocations:
            assert r.standalone_ale + r.diversification_adjustment == r.euler_net_contribution
