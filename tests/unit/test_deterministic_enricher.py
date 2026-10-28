from assessment_engine.infrastructure.deterministic_enricher import (
    DeterministicFinOpsEngine,
    LinguisticLinter,
    MeceClusteringEngine,
)


def test_deterministic_finops_calculation():
    rate_card = {
        "tarifas_hora": {"arquitecto": 65, "experto": 58, "project_manager": 45},
        "margenes": {"consultoria": 0.45},
    }
    wbs = [
        {"required_profile": "arquitecto", "estimated_hours": 100},
        {"required_profile": "experto", "estimated_hours": 200},
        {"required_profile": "project_manager", "estimated_hours": 50},
    ]
    # Internal cost: 100*65 (6500) + 200*58 (11600) + 50*45 (2250) = 20,350
    # Sell price: 20350 / 0.55 = 37,000.00 €

    # 1. Hardware/Network Project -> CapEx proportional
    opex, capex = DeterministicFinOpsEngine.calculate_project_costs(
        wbs_tasks=wbs,
        rate_card=rate_card,
        project_name="Renovación de Switches y Conmutadores",
        tech_objective="Despliegue de hardware físico",
        sizing="L",
    )
    assert "37.000,00 €" in opex
    assert "€" in capex
    assert "Inversión paramétrica" in capex

    # 2. Pure Governance Project -> CapEx Zero/Low
    opex_gov, capex_gov = DeterministicFinOpsEngine.calculate_project_costs(
        wbs_tasks=wbs,
        rate_card=rate_card,
        project_name="Marco de Gobernanza y Políticas",
        tech_objective="Definición de procesos y auditoría",
        sizing="M",
    )
    assert "37.000,00 €" in opex_gov
    assert "Bajo / Nulo" in capex_gov

    # 3. Multi-Currency Support (e.g., USD $)
    opex_usd, capex_usd = DeterministicFinOpsEngine.calculate_project_costs(
        wbs_tasks=wbs,
        rate_card=rate_card,
        project_name="Cloud Platform Migration",
        tech_objective="Deploy infrastructure in US region",
        sizing="L",
        currency_symbol="$",
    )
    assert "37.000,00 $" in opex_usd
    assert "$" in capex_usd


def test_mece_clustering_engine_deduplication():
    # Two overlapping projects with the same risk or overlapping keywords
    proj1 = {
        "name": "Programa de Certificación de Resiliencia para el DCI",
        "tech_objective": "Asegurar la interconexión redundante de centros de datos",
        "deliverables": ["Diseño de arquitectura", "Matriz de pruebas"],
        "mitigates_risk_id": "RISK_001",
        "sizing": "M",
    }
    proj2 = {
        "name": "Garantía de Resiliencia para Interconexión DCI",
        "tech_objective": "Validación de resiliencia y enlaces de interconexión redundante",
        "deliverables": ["Simulacro de conmutación"],
        "mitigates_risk_id": "RISK_001",
        "sizing": "L",
    }
    proj3 = {
        "name": "Automatización NetDevOps",
        "tech_objective": "Infraestructura como código para gestión de red",
        "deliverables": ["Pipelines CI/CD"],
        "mitigates_risk_id": "RISK_002",
        "sizing": "M",
    }

    consolidated = MeceClusteringEngine.consolidate_pillar_projects(
        [proj1, proj2, proj3], max_projects=2
    )

    # proj1 and proj2 must be merged into 1 project, plus proj3 -> Total 2 projects
    assert len(consolidated) == 2
    # Verify merged deliverables
    merged_proj = consolidated[0]
    assert len(merged_proj["deliverables"]) >= 3
    assert merged_proj["sizing"] == "L"  # Upgraded to higher sizing


def test_linguistic_linter_sanitization():
    raw_title = "Proactive Capacity Assurance for Business Continuity **Critical**"
    sanitized = LinguisticLinter.sanitize_title(raw_title)

    assert "Proactive Capacity Assurance" not in sanitized
    assert "Gestión Proactiva de Capacidad" in sanitized
    assert "Continuidad de Negocio" in sanitized
    assert "**" not in sanitized
