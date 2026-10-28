from __future__ import annotations

import asyncio
import pytest

from assessment_engine.application.tools.corporate_project_aggregator import (
    CorporateProgram,
    aggregate_corporate_projects,
)
from assessment_engine.application.tools.dynamic_tower_dispatcher import (
    DynamicTowerDispatcher,
    TowerExecutionResult,
)
from assessment_engine.infrastructure.networkx_analyzer import NetworkXAnalyzer


@pytest.mark.asyncio
async def test_e2e_federated_pipeline_flow():
    """End-to-End verification of the federated corporate project architecture.

    1. Dispatcher executes an arbitrary subset of towers (T1, T4, T5, T8) respecting DAG dependencies.
    2. Candidate initiatives from towers are aggregated into canonical Corporate Programs.
    3. FinOps subadditive economy-of-scale discount is applied.
    4. Topological temporal precedence is enforced without cycles.
    5. Waves correctly sequence core platform milestones before contributing local rollouts.
    """
    # -------------------------------------------------------------
    # Step 1: Dynamic Tower Dispatcher with Bounded Concurrency
    # -------------------------------------------------------------
    requested_towers = ["T1", "T4", "T5", "T8"]
    dispatcher = DynamicTowerDispatcher(
        requested_towers=requested_towers,
        industry_profile="default",
        max_concurrency=2,
    )

    execution_log: list[str] = []

    async def mock_runner(tower_id: str) -> TowerExecutionResult:
        execution_log.append(f"START_{tower_id}")
        await asyncio.sleep(0.02)
        execution_log.append(f"FINISH_{tower_id}")
        return TowerExecutionResult(tower_id=tower_id, success=True, duration_seconds=0.02)

    dispatch_results = await dispatcher.execute_all(runner=mock_runner)
    assert len(dispatch_results) == 4
    assert all(r.success for r in dispatch_results.values())

    # -------------------------------------------------------------
    # Step 2: Multi-Tower Initiatives Emitted by Tower Blueprints
    # -------------------------------------------------------------
    initiatives = [
        # Multi-tower Program: PROG_SOVEREIGN_CLOUD
        {
            "id": "INIT-T8-01",
            "tower": "T8",
            "title": "Despliegue de Landing Zone en Cloud Híbrido y Soberano",
            "objective": "Infraestructura base y gobierno cloud",
            "priority": "Crítica",
            "capex_estimate": "120.000 €",
        },
        {
            "id": "INIT-T4-01",
            "tower": "T4",
            "title": "Migración y Adopción de Workloads en Cloud Soberano",
            "objective": "Refactorizar aplicaciones core para cloud",
            "priority": "Alta",
            "capex_estimate": "60.000 €",
        },
        # Multi-tower Program: PROG_OBSERVABILITY
        {
            "id": "INIT-T5-01",
            "tower": "T5",
            "title": "Plataforma Centralizada de Observabilidad y Correlación SIEM",
            "objective": "Cluster central de telemetría y seguridad",
            "priority": "Crítica",
            "capex_estimate": "100.000 €",
        },
        {
            "id": "INIT-T1-01",
            "tower": "T1",
            "title": "Despliegue de Sondas de Hardware y Agentes de Monitorización",
            "objective": "Telemetría física en servidores y puesto",
            "priority": "Alta",
            "capex_estimate": "25.000 €",
        },
        # Standalone Tower-specific Initiative
        {
            "id": "INIT-T1-02",
            "tower": "T1",
            "title": "Sustitución de Baterías de SAI en CPD Secundario",
            "objective": "Mitigar riesgo eléctrico local",
            "priority": "Media",
            "capex_estimate": "8.000 €",
        },
    ]

    # -------------------------------------------------------------
    # Step 3: Corporate Project Aggregator & FinOps Synergy
    # -------------------------------------------------------------
    aggregation = aggregate_corporate_projects(initiatives)
    programs = aggregation["programs"]
    standalone = aggregation["standalone_initiatives"]

    # Must produce exactly 2 corporate programs and 1 standalone initiative
    assert len(programs) == 2
    assert len(standalone) == 1
    assert standalone[0]["id"] == "INIT-T1-02"

    cloud_prog = next(p for p in programs if p.program_id == "PROG_SOVEREIGN_CLOUD")
    obs_prog = next(p for p in programs if p.program_id == "PROG_OBSERVABILITY")

    assert set(cloud_prog.participating_towers) == {"T4", "T8"}
    assert set(obs_prog.participating_towers) == {"T1", "T5"}

    # FinOps subadditive synergy check (linear sum > consolidated sum)
    assert cloud_prog.linear_capex_numeric == 180_000.0
    assert cloud_prog.consolidated_capex_numeric < 180_000.0
    assert cloud_prog.synergy_savings_numeric > 0.0

    assert obs_prog.linear_capex_numeric == 125_000.0
    assert obs_prog.consolidated_capex_numeric < 125_000.0
    assert obs_prog.synergy_savings_numeric > 0.0

    # -------------------------------------------------------------
    # Step 4: Temporal Precedence in NetworkX Analyzer
    # -------------------------------------------------------------
    analyzer = NetworkXAnalyzer()
    for init in initiatives:
        analyzer.graph.add_node(init["id"])

    # Enforce temporal precedence of core platform milestones
    analyzer.enforce_program_temporal_precedence(programs)

    # Graph must be strictly acyclic (DAG)
    assert len(analyzer.detect_cycles()) == 0

    # -------------------------------------------------------------
    # Step 5: Wave Scheduling (Core Precedes Contributing)
    # -------------------------------------------------------------
    waves = analyzer.calculate_topological_waves()
    assert len(waves) >= 2

    project_wave = {}
    for w_idx, wave_data in enumerate(waves):
        for proj in wave_data["projects"]:
            project_wave[proj] = w_idx

    # Cloud: Core T8 (Landing Zone) must precede Contributing T4 (Microservicios)
    assert project_wave["INIT-T8-01"] < project_wave["INIT-T4-01"]

    # Observability: Core T5 (Central SIEM) must precede Contributing T1 (Sondas)
    assert project_wave["INIT-T5-01"] < project_wave["INIT-T1-01"]

    # Standalone initiative is scheduled independently without blocking
    assert "INIT-T1-02" in project_wave
