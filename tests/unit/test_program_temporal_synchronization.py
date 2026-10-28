from __future__ import annotations

import pytest

from assessment_engine.application.tools.corporate_project_aggregator import (
    CorporateProgram,
    WorkPackage,
)
from assessment_engine.infrastructure.networkx_analyzer import NetworkXAnalyzer


def test_enforce_program_temporal_precedence_orders_waves():
    """Verify that within a corporate program, contributing work packages are sequenced after the core platform package."""
    analyzer = NetworkXAnalyzer()

    # Define a corporate program with core package in T4 and contributing packages in T1 and T5
    core_wp = WorkPackage(
        id="INIT-T4-01",
        tower="T4",
        title="Plataforma Central de Observabilidad y SIEM",
        capex_estimate="120.000 €",
        capex_numeric=120_000.0,
    )
    contrib_wp_t1 = WorkPackage(
        id="INIT-T1-01",
        tower="T1",
        title="Despliegue de Sondas de Hardware SAN en Puestos",
        capex_estimate="30.000 €",
        capex_numeric=30_000.0,
    )
    contrib_wp_t5 = WorkPackage(
        id="INIT-T5-01",
        tower="T5",
        title="Ingesta y Telemetría de Logs Cloud",
        capex_estimate="45.000 €",
        capex_numeric=45_000.0,
    )

    prog = CorporateProgram(
        program_id="PROG_OBSERVABILITY",
        participating_towers=["T1", "T4", "T5"],
        work_packages=[core_wp, contrib_wp_t1, contrib_wp_t5],
        linear_capex_numeric=195_000.0,
        consolidated_capex_numeric=150_000.0,
        synergy_savings_numeric=45_000.0,
    )

    # Initialize graph with the nodes
    analyzer.graph.add_node("INIT-T4-01")
    analyzer.graph.add_node("INIT-T1-01")
    analyzer.graph.add_node("INIT-T5-01")

    # Enforce temporal precedence
    analyzer.enforce_program_temporal_precedence([prog])

    # Calculate waves
    waves = analyzer.calculate_topological_waves()

    # Map each project to its wave index
    project_wave = {}
    for w_idx, wave_data in enumerate(waves):
        for proj in wave_data["projects"]:
            project_wave[proj] = w_idx

    # Core package must strictly precede contributing packages in wave scheduling
    assert "INIT-T4-01" in project_wave
    assert "INIT-T1-01" in project_wave
    assert "INIT-T5-01" in project_wave

    assert project_wave["INIT-T4-01"] < project_wave["INIT-T1-01"]
    assert project_wave["INIT-T4-01"] < project_wave["INIT-T5-01"]


def test_enforce_program_temporal_precedence_preserves_dag():
    """Verify that temporal precedence edges never introduce cycles."""
    analyzer = NetworkXAnalyzer()

    wp1 = WorkPackage(id="INIT-T8-01", tower="T8", title="Core Cloud Landing Zone", capex_numeric=100_000.0)
    wp2 = WorkPackage(id="INIT-T4-02", tower="T4", title="Microservicios en Cloud", capex_numeric=40_000.0)

    prog = CorporateProgram(
        program_id="PROG_SOVEREIGN_CLOUD",
        participating_towers=["T4", "T8"],
        work_packages=[wp1, wp2],
        linear_capex_numeric=140_000.0,
        consolidated_capex_numeric=120_000.0,
        synergy_savings_numeric=20_000.0,
    )

    analyzer.graph.add_node("INIT-T8-01")
    analyzer.graph.add_node("INIT-T4-02")

    # Pre-existing edge: WP2 -> Some intermediate
    analyzer.graph.add_edge("INIT-T4-02", "SOME_OTHER_TASK")

    analyzer.enforce_program_temporal_precedence([prog])

    cycles = analyzer.detect_cycles()
    assert len(cycles) == 0
