from __future__ import annotations

import pytest

from assessment_engine.application.tools.corporate_project_aggregator import (
    CorporateProgram,
    aggregate_corporate_projects,
)


def test_cross_tower_program_aggregation():
    """Verify that initiatives across different towers bind into a single corporate program while preserving local work packages."""
    initiatives = [
        {
            "id": "INIT-T1-01",
            "tower": "T1",
            "title": "Despliegue de Sondas de Hardware SAN y Blade para Monitorización",
            "objective": "Extraer métricas SNMP de chasis blade",
            "priority": "Alta",
            "expected_outcome": "Telemetría física en tiempo real",
            "capex_estimate": "30.000 €",
        },
        {
            "id": "INIT-T4-01",
            "tower": "T4",
            "title": "Implantación de Plataforma de Observabilidad y Correlación SIEM",
            "objective": "Desplegar clúster central de correlación",
            "priority": "Crítica",
            "expected_outcome": "Detección unificada de incidentes",
            "capex_estimate": "120.000 €",
        },
        {
            "id": "INIT-T5-01",
            "tower": "T5",
            "title": "Ingesta y Telemetría Centralizada de Logs Cloud",
            "objective": "Conectar suscripciones AWS/Azure con observabilidad",
            "priority": "Alta",
            "expected_outcome": "Trazabilidad multi-cloud",
            "capex_estimate": "45.000 €",
        },
        {
            "id": "INIT-T1-02",
            "tower": "T1",
            "title": "Sustitución física de regletas de alimentación en Rack 4",
            "objective": "Eliminar riesgo eléctrico local",
            "priority": "Media",
            "expected_outcome": "Continuidad eléctrica en Sala A",
            "capex_estimate": "5.000 €",
        },
    ]

    result = aggregate_corporate_projects(initiatives)

    assert "programs" in result
    assert "standalone_initiatives" in result

    programs = result["programs"]
    assert len(programs) == 1
    prog = programs[0]

    assert isinstance(prog, CorporateProgram)
    assert prog.program_id == "PROG_OBSERVABILITY"
    assert set(prog.participating_towers) == {"T1", "T4", "T5"}
    assert len(prog.work_packages) == 3

    # Local tower packages must be preserved with their specific scopes
    towers_in_packages = {wp.tower for wp in prog.work_packages}
    assert towers_in_packages == {"T1", "T4", "T5"}

    # Standalone local initiatives must not be lost or falsely aggregated
    standalone = result["standalone_initiatives"]
    assert len(standalone) == 1
    assert standalone[0]["id"] == "INIT-T1-02"


def test_subadditive_financial_synergy_discount():
    """Verify that multi-tower corporate programs receive a subadditive FinOps economy-of-scale discount."""
    initiatives = [
        {
            "id": "INIT-T4-01",
            "tower": "T4",
            "title": "Plataforma Central Zero Trust y Gestión de Identidades IAM",
            "objective": "IdP central",
            "capex_estimate": "100.000 €",
        },
        {
            "id": "INIT-T1-01",
            "tower": "T1",
            "title": "Despliegue de Agentes MFA y Control de Acceso Zero Trust en Puestos",
            "objective": "Rollout endpoints",
            "capex_estimate": "50.000 €",
        },
    ]

    result = aggregate_corporate_projects(initiatives)
    prog = result["programs"][0]

    # Linear sum = 150.000 €.
    # Subadditive synergy factor for 2 towers: 1 / (2^0.25) ≈ 0.8409.
    # Expected discounted capex < 150.000 €.
    assert prog.linear_capex_numeric == 150_000.0
    assert prog.consolidated_capex_numeric < 150_000.0
    assert prog.synergy_savings_numeric > 0.0


def test_empty_initiatives_safe():
    """Verify safe behavior when no initiatives are supplied."""
    result = aggregate_corporate_projects([])
    assert result["programs"] == []
    assert result["standalone_initiatives"] == []
