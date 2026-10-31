"""Unit tests for Authoritative Ontology Registry and Bijective Gatekeeper (RFC-024)."""

from __future__ import annotations

import pytest

from assessment_engine.infrastructure.ontology import (
    ControlBenchmarkMapping,
    IndustryProfile,
    KpiDefinition,
    OntologyIntegrityError,
    OntologyRegistry,
    OrganizationTier,
    PillarDefinition,
    Polarity,
    QuantitativeBenchmark,
    RegulatoryCitation,
    TowerDefinition,
)


@pytest.fixture
def valid_tower() -> TowerDefinition:
    """Fixture returning valid technical tower with two canonical controls."""
    return TowerDefinition(
        tower_id="T1_CORE_INFRASTRUCTURE",
        version="2.1.0",
        name_i18n_key="towers.t1_core_infrastructure.name",
        pillars=[
            PillarDefinition(
                pillar_id="PIL-RESILIENCE",
                name_i18n_key="pillars.resilience.name",
                weight=0.6,
                kpis=[
                    KpiDefinition(
                        kpi_id="KPI-AVAIL-SLA",
                        name_i18n_key="kpis.avail_sla.name",
                        unit="percentage",
                        polarity=Polarity.HIGHER_IS_BETTER,
                        canonical_control_ids=["CTRL-RES-AVAIL-001"],
                    )
                ],
            ),
            PillarDefinition(
                pillar_id="PIL-SECURITY",
                name_i18n_key="pillars.security.name",
                weight=0.4,
                kpis=[
                    KpiDefinition(
                        kpi_id="KPI-PATCH-LATENCY",
                        name_i18n_key="kpis.patch_latency.name",
                        unit="hours",
                        polarity=Polarity.LOWER_IS_BETTER,
                        canonical_control_ids=["CTRL-SEC-VULN-001"],
                    )
                ],
            ),
        ],
    )


@pytest.fixture
def valid_profile() -> IndustryProfile:
    """Fixture returning valid industry profile covering both controls of T1."""
    return IndustryProfile(
        profile_id="PROF-FINSERV_GLOBAL_T1",
        version="2.1.0",
        industry_vertical="FINANCIAL_SERVICES",
        target_tier=OrganizationTier.GLOBAL_TIER_1,
        applicable_towers=["T1_CORE_INFRASTRUCTURE"],
        control_mappings=[
            ControlBenchmarkMapping(
                control_id="CTRL-RES-AVAIL-001",
                criticality_weight=0.9,
                quantitative_thresholds=QuantitativeBenchmark(
                    tier_1_global_leader=99.999,
                    industry_median=99.95,
                    minimum_acceptable=99.9,
                ),
                regulatory_citations=[
                    RegulatoryCitation(
                        framework_id="DORA",
                        clause_id="Article 11.1",
                        enforcement_level="MANDATORY",
                        evidence_requirement_i18n_key="citations.dora.art_11_1",
                    )
                ],
            ),
            ControlBenchmarkMapping(
                control_id="CTRL-SEC-VULN-001",
                criticality_weight=0.85,
                quantitative_thresholds=QuantitativeBenchmark(
                    tier_1_global_leader=12.0,
                    industry_median=48.0,
                    minimum_acceptable=72.0,
                ),
                regulatory_citations=[
                    RegulatoryCitation(
                        framework_id="ISO27001_2022",
                        clause_id="A.8.8",
                        enforcement_level="MANDATORY",
                        evidence_requirement_i18n_key="citations.iso27001.a_8_8",
                    )
                ],
            ),
        ],
    )


def test_perfect_bipartite_graph_verification(
    valid_tower: TowerDefinition, valid_profile: IndustryProfile
) -> None:
    """Verify clean instantiation and O(1) benchmark resolution when graph is bijective."""
    registry = OntologyRegistry(
        towers={"T1_CORE_INFRASTRUCTURE": valid_tower},
        profiles={"PROF-FINSERV_GLOBAL_T1": valid_profile},
    )

    mapping = registry.resolve_benchmark_for_control(
        "PROF-FINSERV_GLOBAL_T1", "CTRL-RES-AVAIL-001"
    )
    assert mapping.control_id == "CTRL-RES-AVAIL-001"
    assert mapping.criticality_weight == 0.9
    assert mapping.quantitative_thresholds.tier_1_global_leader == 99.999


def test_orphan_control_detection_fails_boot_time(valid_tower: TowerDefinition) -> None:
    """Ensure boot-time failure if a tower control lacks corresponding benchmark in profile."""
    # Profile only provides CTRL-RES-AVAIL-001, missing CTRL-SEC-VULN-001
    incomplete_profile = IndustryProfile(
        profile_id="PROF-INCOMPLETE",
        version="1.0.0",
        industry_vertical="FINANCIAL_SERVICES",
        target_tier=OrganizationTier.ENTERPRISE,
        applicable_towers=["T1_CORE_INFRASTRUCTURE"],
        control_mappings=[
            ControlBenchmarkMapping(
                control_id="CTRL-RES-AVAIL-001",
                criticality_weight=0.9,
                quantitative_thresholds=QuantitativeBenchmark(
                    tier_1_global_leader=99.99,
                    industry_median=99.9,
                    minimum_acceptable=99.5,
                ),
                regulatory_citations=[
                    RegulatoryCitation(
                        framework_id="DORA",
                        clause_id="Article 11.1",
                        enforcement_level="MANDATORY",
                        evidence_requirement_i18n_key="citations.dora",
                    )
                ],
            )
        ],
    )

    with pytest.raises(OntologyIntegrityError) as exc_info:
        OntologyRegistry(
            towers={"T1_CORE_INFRASTRUCTURE": valid_tower},
            profiles={"PROF-INCOMPLETE": incomplete_profile},
        )

    diag = exc_info.value.to_diagnostic_report()
    orphans = diag["diagnostics"]["orphan_controls_in_profiles"]["PROF-INCOMPLETE"]
    assert "CTRL-SEC-VULN-001" in orphans


def test_dangling_control_reference_fails_boot_time(
    valid_tower: TowerDefinition, valid_profile: IndustryProfile
) -> None:
    """Ensure boot-time failure if profile references control not present in any active tower."""
    # Add a dangling control mapping that no tower emits
    dangling_mapping = ControlBenchmarkMapping(
        control_id="CTRL-GHOST-OBSOLETE-999",
        criticality_weight=0.5,
        quantitative_thresholds=QuantitativeBenchmark(
            tier_1_global_leader=1.0, industry_median=2.0, minimum_acceptable=3.0
        ),
        regulatory_citations=[
            RegulatoryCitation(
                framework_id="SOC2",
                clause_id="CC6.1",
                enforcement_level="ADVISORY",
                evidence_requirement_i18n_key="citations.soc2",
            )
        ],
    )
    overloaded_profile = valid_profile.model_copy(
        update={"control_mappings": list(valid_profile.control_mappings) + [dangling_mapping]}
    )

    with pytest.raises(OntologyIntegrityError) as exc_info:
        OntologyRegistry(
            towers={"T1_CORE_INFRASTRUCTURE": valid_tower},
            profiles={"PROF-FINSERV_GLOBAL_T1": overloaded_profile},
        )

    diag = exc_info.value.to_diagnostic_report()
    dangling = diag["diagnostics"]["dangling_control_references"]["PROF-FINSERV_GLOBAL_T1"]
    assert "CTRL-GHOST-OBSOLETE-999" in dangling


def test_invalid_pillar_weights_sum(valid_tower: TowerDefinition, valid_profile: IndustryProfile) -> None:
    """Verify that pillar weights not summing to 1.0 are rejected."""
    # Change weights so they sum to 0.9 instead of 1.0
    bad_pillars = [
        valid_tower.pillars[0].model_copy(update={"weight": 0.5}),
        valid_tower.pillars[1].model_copy(update={"weight": 0.4}),
    ]
    bad_tower = valid_tower.model_copy(update={"pillars": bad_pillars})

    with pytest.raises(OntologyIntegrityError) as exc_info:
        OntologyRegistry(
            towers={"T1_CORE_INFRASTRUCTURE": bad_tower},
            profiles={"PROF-FINSERV_GLOBAL_T1": valid_profile},
        )

    assert "pillar weights sum to 0.9000, expected 1.0" in str(exc_info.value)
