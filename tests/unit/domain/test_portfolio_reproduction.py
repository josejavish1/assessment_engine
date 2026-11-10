"""Unit tests for Portfolio Reproduction Manifest and Deterministic Replay (SR 11-7)."""

import json

import pytest
from pydantic import ValidationError

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
    PortfolioReproductionManifest,
    create_reproduction_manifest,
    replay_portfolio_simulation,
)


def _build_test_portfolio() -> tuple[BayesianFairCopulaEngine, list[FindingTelemetry]]:
    zone = OperationalZone(
        zone_id="TIER_1_CORE",
        hourly_burn_rate=8000.0,
        max_annual_outage_hours=36.0,
    )
    findings = [
        FindingTelemetry(
            finding_id="F1",
            tower_id="T1",
            title="Core Switch Redundancy Failure",
            cmmi_maturity=2.4,
            zone=zone,
            tef_pert_min=0.10,
            tef_pert_mode=0.25,
            tef_pert_max=0.60,
            rto_hours_min=1.5,
            rto_hours_mode=5.0,
            rto_hours_max=12.0,
            secondary_loss_mean=4000.0,
            blast_radius_alpha=0.55,
        ),
        FindingTelemetry(
            finding_id="F2",
            tower_id="T2",
            title="Hyperconverged Storage Imbalance",
            cmmi_maturity=2.7,
            zone=zone,
            tef_pert_min=0.08,
            tef_pert_mode=0.20,
            tef_pert_max=0.50,
            rto_hours_min=1.0,
            rto_hours_mode=4.0,
            rto_hours_max=10.0,
            secondary_loss_mean=2500.0,
            blast_radius_alpha=0.45,
        ),
    ]
    engine = BayesianFairCopulaEngine(num_simulations=2048)
    return engine, findings


def test_portfolio_reproduction_manifest_roundtrip_parity() -> None:
    """Proves full manifest round-trip reproduction with seed-hash and metric equality."""
    engine, findings = _build_test_portfolio()
    summary = engine.evaluate_portfolio(findings, currency_code="EUR")

    manifest = create_reproduction_manifest(
        engine=engine,
        findings=findings,
        summary=summary,
        currency_code="EUR",
    )

    # Test JSON serialization roundtrip
    raw_json = manifest.model_dump_json()
    reconstituted_manifest = PortfolioReproductionManifest.model_validate(json.loads(raw_json))
    assert reconstituted_manifest.deterministic_seed_hash == summary.deterministic_seed_hash

    # Execute deterministic replay
    replay_result = replay_portfolio_simulation(reconstituted_manifest, currency_tolerance=0.01)
    assert replay_result["verified"] is True
    assert replay_result["seed_hash"] == summary.deterministic_seed_hash
    assert replay_result["total_portfolio_ale"] == summary.total_portfolio_ale
    assert replay_result["portfolio_var_90"] == summary.portfolio_var_90


def test_portfolio_reproduction_fails_on_mutated_material_input() -> None:
    """Proves that a mutated material input (e.g. tef_pert_mode altered) causes loud assertion failure."""
    engine, findings = _build_test_portfolio()
    summary = engine.evaluate_portfolio(findings, currency_code="EUR")
    manifest = create_reproduction_manifest(engine, findings, summary, "EUR")

    manifest_dict = manifest.model_dump()
    # Mutate material input
    manifest_dict["findings_telemetry"][0]["tef_pert_mode"] = 0.95

    with pytest.raises(AssertionError, match="Seed hash divergence|diverged"):
        replay_portfolio_simulation(manifest_dict, currency_tolerance=0.01)


def test_portfolio_reproduction_fails_on_missing_manifest_fields() -> None:
    """Proves that missing required manifest fields fail Pydantic model validation."""
    engine, findings = _build_test_portfolio()
    summary = engine.evaluate_portfolio(findings, currency_code="EUR")
    manifest = create_reproduction_manifest(engine, findings, summary, "EUR")

    manifest_dict = manifest.model_dump()
    del manifest_dict["engine_config"]

    with pytest.raises(ValidationError):
        replay_portfolio_simulation(manifest_dict)
