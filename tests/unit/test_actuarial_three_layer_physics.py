"""Unit test suite for 3-Layer Actuarial Physics and Canary Scenarios (SR 11-7)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.bowtie_escalation import BowTieEscalationEngine
from assessment_engine.domain.actuarial.regulatory_gating import RegulatoryGatingEngine
from assessment_engine.domain.actuarial.temporal_physics import TemporalPhysicsEngine
from assessment_engine.domain.schemas.actuarial_contracts import (
    ArchitecturalRole,
    AssetActuarialProfile,
    CausalNature,
    DataClassification,
    EnvironmentTier,
)


def test_orc_04_canary_pam_control_plane_cascades_to_dependent_nodes() -> None:
    """ORC-04: PAM root compromise cascades across production plant nodes, elevating exposure."""
    # Target PAM node has 0 EUR direct production revenue (pure security infrastructure)
    pam_node = AssetActuarialProfile(
        asset_id="T6-RVS02",
        environment_tier=EnvironmentTier.PROD_CRITICAL,
        architectural_role=ArchitecturalRole.CONTROL_PLANE,
        hourly_revenue_contribution=0.0,
        reconstitution_labor_cost=3000.0,
    )

    # 12 critical production plant and database nodes governed by this PAM root
    dependent_nodes = [
        AssetActuarialProfile(
            asset_id=f"PLANT-NODE-{i:02d}",
            environment_tier=EnvironmentTier.PROD_CRITICAL,
            architectural_role=ArchitecturalRole.DATA_PLANE,
            hourly_revenue_contribution=1088.0,  # 12 * 1088 = ~13,061 EUR/h total plant revenue
        )
        for i in range(12)
    ]

    cascaded_hourly = BowTieEscalationEngine.calculate_cascaded_hourly_exposure(
        target_asset=pam_node,
        causal_nature=CausalNature.DESTRUCTIVE_SABOTAGE,
        dependent_assets=dependent_nodes,
        contagion_factor=1.0,
    )

    # Hourly exposure must equal total plant revenue (~13,061 EUR/h), not 0 EUR
    assert cascaded_hourly >= 13000.0
    # Over a 15-hour recovery window, total simulated loss exceeds 195,000 EUR
    fifteen_hour_loss = cascaded_hourly * 15.0
    assert fifteen_hour_loss > 195000.0


def test_orc_05_canary_k8s_lab_yields_zero_business_interruption() -> None:
    """ORC-05: K8s cluster in LAB_DEV_TEST yields strictly 0 EUR revenue loss and pure IT labor."""
    k8s_lab = AssetActuarialProfile(
        asset_id="T2-RVS03",
        environment_tier=EnvironmentTier.LAB_DEV_TEST,
        architectural_role=ArchitecturalRole.DATA_PLANE,
        hourly_revenue_contribution=50000.0,  # Nominal enterprise revenue rate
        reconstitution_labor_cost=1500.0,
        operational_buffer_hours=0.0,
    )

    scalar = BowTieEscalationEngine.get_environment_revenue_scalar(k8s_lab.environment_tier)
    assert scalar == 0.0

    cascaded_hourly = BowTieEscalationEngine.calculate_cascaded_hourly_exposure(
        target_asset=k8s_lab,
        causal_nature=CausalNature.RESOURCE_EXHAUSTION,
        dependent_assets=[],
    )
    # Business interruption loss is strictly zero
    assert cascaded_hourly == 0.0

    # Total loss equals pure direct IT labor
    direct_labor = TemporalPhysicsEngine.calculate_reconstitution_labor_cost(
        tech_restoration_hours=8.0,
        hourly_engineering_rate=65.0,
    )
    assert direct_labor == 520.0


def test_orc_06_canary_physical_fiber_cut_zero_privacy_fine() -> None:
    """ORC-06: Backhoe physical cable cut carries zero GDPR/privacy statutory fines."""
    causal_nature = CausalNature.ACCIDENTAL_PHYSICAL_SEVERANCE
    # Asset carries PII/financial data across transport link
    data_class = DataClassification.REGULATED_PII_FINANCIAL

    # Regulatory gate must block privacy fine
    assert RegulatoryGatingEngine.is_privacy_breach_eligible(causal_nature, data_class) is False
    privacy_fine = RegulatoryGatingEngine.calculate_statutory_privacy_exposure(
        causal_nature=causal_nature,
        data_classification=data_class,
        baseline_statutory_fine=2000000.0,
    )
    assert privacy_fine == 0.0


def test_orc_07_canary_disk_log_cleanup_absorbed_by_buffer() -> None:
    """ORC-07: 15-minute log cleanup absorbed by operational buffer yields 0h outage and < 250 EUR loss."""
    tech_restoration = 0.25  # 15 minutes
    buffer_hours = 1.0       # 1-hour buffer tolerance before plant interruption

    effective_downtime = TemporalPhysicsEngine.calculate_effective_downtime_hours(
        tech_restoration_hours=tech_restoration,
        buffer_hours=buffer_hours,
        beta=2.0,
    )
    assert effective_downtime == 0.0

    hourly_rate = 13061.0
    business_interruption = effective_downtime * hourly_rate
    assert business_interruption == 0.0

    labor_cost = TemporalPhysicsEngine.calculate_reconstitution_labor_cost(
        tech_restoration_hours=tech_restoration,
        hourly_engineering_rate=65.0,
    )
    assert labor_cost == 16.25  # ~16 EUR
    assert (business_interruption + labor_cost) < 250.0
