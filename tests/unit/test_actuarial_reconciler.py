"""Unit tests for ActuarialReconciler (RFC 065)."""

from __future__ import annotations

from decimal import Decimal
import pytest

from assessment_engine.domain.actuarial_reconciler import (
    ActuarialReconciler,
    ActuarialReconciliationError,
)


def test_reconcile_domain_allocations_exact_sum():
    """Verify that domain allocations sum exactly to the target corporate ALE."""
    target_ale = 916416
    domains = [
        ("T1", Decimal("141184.4")),
        ("T2", Decimal("101231.2")),
        ("T3", Decimal("85000.0")),
        ("T4", Decimal("31000.0")),
        ("T5", Decimal("210000.0")),
        ("T6", Decimal("65000.0")),
        ("T7", Decimal("45000.0")),
        ("T8", Decimal("135000.0")),
        ("T9", Decimal("28000.0")),
        ("T10", Decimal("75000.0")),
    ]

    allocated = ActuarialReconciler.reconcile_domain_allocations(target_ale, domains)
    assert len(allocated) == 10
    assert sum(allocated.values()) == target_ale


def test_reconcile_domain_allocations_zero():
    """Verify handling of zero target corporate ALE."""
    domains = [("T1", Decimal("100")), ("T2", Decimal("200"))]
    allocated = ActuarialReconciler.reconcile_domain_allocations(0, domains)
    assert allocated == {"T1": 0, "T2": 0}


def test_reconcile_domain_allocations_empty_error():
    """Verify error on empty domain exposures sequence."""
    with pytest.raises(ActuarialReconciliationError, match="cannot be empty"):
        ActuarialReconciler.reconcile_domain_allocations(100, [])


def test_reconcile_domain_allocations_negative_error():
    """Verify error on negative target."""
    with pytest.raises(ActuarialReconciliationError):
        ActuarialReconciler.reconcile_domain_allocations(-100, [("T1", Decimal("100"))])


def test_reconcile_domain_allocations_negative_individual_error():
    """Verify error on negative individual domain exposure."""
    with pytest.raises(ActuarialReconciliationError, match="must be a finite non-negative Decimal"):
        ActuarialReconciler.reconcile_domain_allocations(100, [("T1", Decimal("-10")), ("T2", Decimal("110"))])


def test_reconcile_domain_allocations_duplicate_domains_error():
    """Verify error on duplicate domain IDs."""
    with pytest.raises(ActuarialReconciliationError, match="Duplicate domain IDs"):
        ActuarialReconciler.reconcile_domain_allocations(100, [("T1", Decimal("50")), ("T1", Decimal("50"))])


def test_reconcile_scenario_card_arithmetic():
    """Verify scenario card quantization satisfies SLE * LEF == ALE."""
    card = ActuarialReconciler.reconcile_scenario_card(105000, Decimal("0.40"))
    assert card["sle"] == 105000
    assert card["lef"] == Decimal("0.40")
    assert card["ale_p50"] == 42000

    card2 = ActuarialReconciler.reconcile_scenario_card(128333, Decimal("0.30"))
    assert card2["sle"] == 128333
    assert card2["lef"] == Decimal("0.30")
    assert card2["ale_p50"] == 38500


def test_reconcile_scenario_card_negative_error():
    """Verify error on negative SLE or LEF."""
    with pytest.raises(ActuarialReconciliationError, match="SLE cannot be negative"):
        ActuarialReconciler.reconcile_scenario_card(-1000, Decimal("0.1"))

    with pytest.raises(ActuarialReconciliationError, match="LEF must be a finite non-negative Decimal"):
        ActuarialReconciler.reconcile_scenario_card(1000, Decimal("-0.1"))


def test_reconcile_cmmi_scores():
    """Verify calculation of simple mean and weighted corporate mean."""
    scores = [
        Decimal("2.60"),
        Decimal("2.50"),
        Decimal("2.50"),
        Decimal("3.30"),
        Decimal("2.10"),
        Decimal("2.80"),
        Decimal("2.50"),
        Decimal("2.40"),
        Decimal("3.10"),
        Decimal("2.40"),
    ]
    simple, weighted = ActuarialReconciler.reconcile_cmmi_scores(scores)
    assert simple == Decimal("2.62")
    assert weighted == Decimal("2.62")

    weights = [
        Decimal("1.2"),
        Decimal("1.2"),
        Decimal("1.0"),
        Decimal("0.8"),
        Decimal("1.5"),
        Decimal("1.1"),
        Decimal("0.9"),
        Decimal("1.0"),
        Decimal("0.7"),
        Decimal("1.4"),
    ]
    simple2, weighted2 = ActuarialReconciler.reconcile_cmmi_scores(scores, weights)
    assert simple2 == Decimal("2.62")
    assert weighted2 < Decimal("2.60")


def test_reconcile_cmmi_scores_mismatched_weights_error():
    """Verify error when weights and scores have different lengths."""
    scores = [Decimal("2.50"), Decimal("3.00")]
    weights = [Decimal("1.0")]
    with pytest.raises(ActuarialReconciliationError, match="does not match weights length"):
        ActuarialReconciler.reconcile_cmmi_scores(scores, weights)
