"""Unit tests for ExecutiveSummaryAST and its 3 universal deterministic resolvers."""

from __future__ import annotations

import pytest

from assessment_engine.domain.schemas.executive_summary_ast import (
    ActuarialExposureBlock,
    CapitalAllocationBlock,
    CapitalInterventionItem,
    ExecutiveSummaryAST,
    LocaleFormattingContractResolver,
    LossDriverCategory,
    LossDriverItem,
    ScaleArchetype,
    ScaleArchetypeResolver,
    ScqaAnswerTheses,
    ScqaBlock,
    ScqaComplication,
    ScqaSituation,
    SystemicBottleneckBlock,
    VerticalArchetype,
    VerticalChokepointResolver,
)


def test_scale_archetype_resolver_litmus_tests() -> None:
    """Verifies scale resolution across mid-market, enterprise, and high-regulation overrides."""
    # 1. Mid-Market: €15M revenue, 80 employees -> MID_MARKET_OWNER
    scale_mid = ScaleArchetypeResolver.resolve(annual_revenue=15_000_000, employee_count=80)
    assert scale_mid == ScaleArchetype.MID_MARKET_OWNER

    # 2. Enterprise: €1.144B Molins, 3,000 employees -> ENTERPRISE_CORP
    scale_molins = ScaleArchetypeResolver.resolve(annual_revenue=1_144_000_000, employee_count=3000)
    assert scale_molins == ScaleArchetype.ENTERPRISE_CORP

    # 3. Committee Litmus Test: $40M FinTech with regulatory supervision -> TIER1_REGULATED override!
    scale_regulated_fintech = ScaleArchetypeResolver.resolve(
        annual_revenue=40_000_000, employee_count=150, is_regulated_sector=True
    )
    assert scale_regulated_fintech == ScaleArchetype.TIER1_REGULATED

    # 4. Mega-bank: $20B revenue -> TIER1_REGULATED
    scale_megabank = ScaleArchetypeResolver.resolve(annual_revenue=20_000_000_000, employee_count=45000)
    assert scale_megabank == ScaleArchetype.TIER1_REGULATED


def test_vertical_chokepoint_resolver_defaults_and_telemetry_priority() -> None:
    """Verifies that vertical bottlenecks are sector-native and respect discovered telemetry."""
    # 1. Financial Services default
    fin = VerticalChokepointResolver.resolve("FINANCIAL_SERVICES")
    assert "Payment Clearing Rails" in fin.primary_operational_asset
    assert "settlement freezing" in fin.operational_halt_consequence

    # 2. Healthcare default
    health = VerticalChokepointResolver.resolve("HEALTHCARE_LIFE_SCIENCES")
    assert "EHR/HIS" in health.primary_operational_asset
    assert "ambulance diversion" in health.operational_halt_consequence

    # 3. Manufacturing default
    manuf = VerticalChokepointResolver.resolve("MANUFACTURING_LOGISTICS")
    assert "Process Execution" in manuf.primary_operational_asset
    assert "supply chain" in manuf.operational_halt_consequence

    # 4. Telemetry Priority Override (Discovered Asset wins over default)
    custom_intel = {
        "primary_chokepoint_asset": "HPE SimpliVity 6-Node Clustered SAN",
        "operational_consequence": "halted cement packaging and truck dispatch",
        "secondary_blast_radius": "Sant Vicenç dels Horts plant floor",
    }
    custom_res = VerticalChokepointResolver.resolve("MANUFACTURING_LOGISTICS", tenant_intel=custom_intel)
    assert custom_res.primary_operational_asset == "HPE SimpliVity 6-Node Clustered SAN"
    assert custom_res.operational_halt_consequence == "halted cement packaging and truck dispatch"


def test_locale_formatting_contract_resolver_jurisdictional_titles() -> None:
    """Verifies that governance titles and regulators are accurately localized without Anglo-bias."""
    # 1. es-ES Enterprise (Molins) with localized contract overrides
    contract_es = LocaleFormattingContractResolver.resolve(
        locale_code="es-ES",
        scale=ScaleArchetype.ENTERPRISE_CORP,
        vertical=VerticalArchetype.MANUFACTURING_LOGISTICS,
        currency_iso="EUR",
        governance_target_title="Consejo de Administración y Comité de Dirección",
        primary_regulator_acronyms=["Directiva NIS2", "Directiva CER", "RGPD"],
    )
    assert contract_es.currency_symbol == "€"
    assert contract_es.governance_target_title == "Consejo de Administración y Comité de Dirección"
    assert any("NIS2" in reg for reg in contract_es.primary_regulator_acronyms)

    # 2. en-GB Tier-1 Regulated (Starling Bank) default contract
    contract_gb = LocaleFormattingContractResolver.resolve(
        locale_code="en-GB",
        scale=ScaleArchetype.TIER1_REGULATED,
        vertical=VerticalArchetype.FINANCIAL_SERVICES,
        currency_iso="GBP",
    )
    assert contract_gb.currency_symbol == "£"
    assert contract_gb.governance_target_title == "Board Risk Committee & Prudential Regulation Authority Liaison"
    assert "ISO/IEC 27001" in contract_gb.primary_regulator_acronyms

    # 3. pt-BR Tier-1 Regulated (Rede D'Or) with localized overrides
    contract_br = LocaleFormattingContractResolver.resolve(
        locale_code="pt-BR",
        scale=ScaleArchetype.TIER1_REGULATED,
        vertical=VerticalArchetype.HEALTHCARE_LIFE_SCIENCES,
        currency_iso="BRL",
        governance_target_title="Comitê de Auditoria e Riscos do Conselho de Administração",
        primary_regulator_acronyms=["ANVISA", "ANS", "LGPD"],
    )
    assert contract_br.currency_symbol == "R$"
    assert contract_br.governance_target_title == "Comitê de Auditoria e Riscos do Conselho de Administração"
    assert "ANVISA" in contract_br.primary_regulator_acronyms

    # 4. ja-JP Tier-1 Regulated (Tokyo Financial) with localized overrides
    contract_jp = LocaleFormattingContractResolver.resolve(
        locale_code="ja-JP",
        scale=ScaleArchetype.TIER1_REGULATED,
        vertical=VerticalArchetype.FINANCIAL_SERVICES,
        currency_iso="JPY",
        governance_target_title="取締役会・監査等委員会",
        primary_regulator_acronyms=["FSA (Financial Services Agency)", "Bank of Japan (BOJ)"],
    )
    assert contract_jp.currency_symbol == "¥"
    assert any("FSA" in reg for reg in contract_jp.primary_regulator_acronyms)
    assert not any("PRA" in reg for reg in contract_jp.primary_regulator_acronyms)

    # 5. Currency Normalization: 2.5B JPY (~$16M) is MID_MARKET_OWNER, NOT a $2.5B Mega Bank!
    scale_jpy = ScaleArchetypeResolver.resolve(annual_revenue=2_500_000_000, fx_rate_to_usd=150.0)
    assert scale_jpy == ScaleArchetype.MID_MARKET_OWNER

    # 6. de-DE Mid-Market Owner with localized overrides
    contract_de = LocaleFormattingContractResolver.resolve(
        locale_code="de-DE",
        scale=ScaleArchetype.MID_MARKET_OWNER,
        vertical=VerticalArchetype.MANUFACTURING_LOGISTICS,
        currency_iso="EUR",
        governance_target_title="Geschäftsführung und Betriebsleitung",
    )
    assert contract_de.governance_target_title == "Geschäftsführung und Betriebsleitung"


def test_executive_summary_ast_rendering_under_350_words() -> None:
    """Verifies that ExecutiveSummaryAST renders cohesive 4-paragraph prose strictly <= 350 words."""
    ast = ExecutiveSummaryAST(
        tower_id="T2",
        tower_name="Hybrid Cloud, Compute & Virtualization",
        scale_archetype=ScaleArchetype.ENTERPRISE_CORP,
        vertical_context={"vertical": "MANUFACTURING_LOGISTICS"},
        locale_contract={"locale_code": "es-ES", "currency_iso": "EUR"},
        scqa_hook=ScqaBlock(
            situation=ScqaSituation(
                operational_footprint="The compute infrastructure hosts 300+ mission-critical virtual machines across dual production sites.",
                core_dependency="Core enterprise operations depend strictly upon hypervisor availability and real-time state synchronization.",
            ),
            complication=ScqaComplication(
                primary_vulnerability_vector="85% memory saturation across 6 HPE SimpliVity nodes hosting co-mingled OT and test workloads.",
                unmitigated_chokepoint_failure="a single physical host failure eliminates N+1 redundancy and forces ungraceful virtual machine pauses.",
            ),
            answer_theses=ScqaAnswerTheses(
                governance_mandate="Isolate production OT clusters and execute memory expansion prior to contractual licensing milestones.",
                immediate_containment_action="deploying memory re-allocation policies and decommissioning zombie non-production workloads",
                quantified_risk_reduction_pct=65.0,
            ),
        ),
        actuarial_exposure=ActuarialExposureBlock(
            formatted_p50_expected_loss="162.695 €",
            formatted_p95_tail_var="426.387 €",
            ebitda_impact_percentage=0.35,
            loss_drivers=[
                LossDriverItem(
                    category=LossDriverCategory.OPERATIONAL_INTERRUPTION,
                    sector_specific_label="Plant Floor Production & Dispatch Halting",
                    formatted_amount="350.000 €",
                    percentage_of_total=82.0,
                )
            ],
        ),
        systemic_bottleneck=SystemicBottleneckBlock(
            entry_vector="Staged lateral traversal via unsegmented test VLANs",
            lateral_movement_mechanism="credential re-use across unpatched CentOS 5/6 legacy hosts",
            crown_jewel_target="Core ERP Database and Weighbridge Dispatch Gateways",
            mean_time_to_compromise_hours=3.5,
            recovery_bottleneck="SimpliVity write-cache de-staging and manual backup snapshot re-assembly",
        ),
        capital_allocation=CapitalAllocationBlock(
            horizon_label="90-Day Enterprise Program",
            formatted_total_capex="85.000 €",
            formatted_net_risk_eliminated="275.000 €",
            blended_rosi_ratio="3.2x",
            top_interventions=[
                CapitalInterventionItem(
                    action_title="HPE SimpliVity RAM Augmentation & Cluster Segregation",
                    target_asset="6 HPE SimpliVity Nodes",
                    formatted_cost="45.000 €",
                    risk_reduction_pct=45.0,
                )
            ],
        ),
    )

    summary_text = ast.render_plain_text_summary()
    assert summary_text is not None
    paragraphs = summary_text.strip().split("\n\n")
    assert len(paragraphs) == 4, f"Expected exactly 4 paragraphs, got {len(paragraphs)}"

    word_count = len(summary_text.split())
    assert word_count <= 350, f"Expected <= 350 words for executive brevity, got {word_count}"
    assert "426.387 €" in summary_text
    assert "HPE SimpliVity" in summary_text
    assert "90-Day Enterprise Program" in summary_text
