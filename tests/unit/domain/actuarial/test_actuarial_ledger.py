"""Unit tests for ActuarialLedgerSSOT guaranteeing zero arithmetic drift across sections."""

from decimal import Decimal
import pytest

from assessment_engine.domain.actuarial.actuarial_ledger import (
    ActuarialLedgerSSOT,
    DomainFinancialMetric,
)


def test_actuarial_ledger_ssot_validation() -> None:
    t1 = DomainFinancialMetric(
        tower_id="T1",
        raw_standalone_ale=100_000,
        diversification_adjustment=-20_000,
        calibrated_net_ale=80_000,
        worst_crisis_event_p90=250_000,
        portfolio_weight_pct=Decimal("40.0"),
    )
    t2 = DomainFinancialMetric(
        tower_id="T2",
        raw_standalone_ale=150_000,
        diversification_adjustment=-30_000,
        calibrated_net_ale=120_000,
        worst_crisis_event_p90=400_000,
        portfolio_weight_pct=Decimal("60.0"),
    )

    ledger = ActuarialLedgerSSOT(
        currency_iso="EUR",
        domain_metrics={"T1": t1, "T2": t2},
        gross_undiversified_ale=250_000,
        copula_adjustment_ale=-50_000,
        copula_overlap_pct=Decimal("20.0"),
        net_consolidated_portfolio_ale=200_000,
    )

    assert ledger.gross_undiversified_ale == 250_000
    assert ledger.net_consolidated_portfolio_ale == 200_000
    assert ledger.get_domain_metric("T1").calibrated_net_ale == 80_000
    assert ledger.get_domain_metric("t2").calibrated_net_ale == 120_000


def test_row_conservation_failure() -> None:
    with pytest.raises(ValueError, match="Row conservation failed"):
        DomainFinancialMetric(
            tower_id="T1",
            raw_standalone_ale=100_000,
            diversification_adjustment=-20_000,
            calibrated_net_ale=85_000,  # Intentional drift (+5k)
            worst_crisis_event_p90=250_000,
            portfolio_weight_pct=Decimal("50.0"),
        )
