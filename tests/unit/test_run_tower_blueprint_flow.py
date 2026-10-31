"""Unit tests for the end-to-end execution flow of run_tower_blueprint."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from assessment_engine.application.run_tower_blueprint_engine import run_tower_blueprint
from assessment_engine.infrastructure.runtime_paths import resolve_client_dir


@pytest.mark.asyncio
async def test_run_tower_blueprint_lifecycle(tmp_path: Path):
    """Verify that run_tower_blueprint executes the end-to-end blueprint synthesis lifecycle."""
    client_name = "Mock Flow Client"
    tower_id = "T1"
    client_dir = resolve_client_dir(client_name)
    tower_dir = client_dir / tower_id
    tower_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Arrange: Setup case input fixture
        case_input_data = {
            "tower_name": "Workplace & End User Services",
            "language": "es",
            "context_summary": "Entorno híbrido con puestos de trabajo Windows 10.",
            "answers": [
                {"kpi_id": "T1.P1.K1.PR1", "value": 3.5},
                {"kpi_id": "T1.P2.K1.PR1", "value": 4.0},
            ],
        }
        (tower_dir / "case_input.json").write_text(
            json.dumps(case_input_data), encoding="utf-8"
        )
        (tower_dir / "findings.json").write_text(
            json.dumps({"pillar_findings": []}), encoding="utf-8-sig"
        )

        mock_graph = MagicMock()
        mock_resolver = MagicMock()
        mock_ontology = MagicMock()

        async def fake_mr(*args, **kwargs):
            payload = kwargs.get("blueprint_payload") or args[-1]
            payload["pillars_analysis"] = [
                {
                    "thought_process": "Razonamiento arquitectónico para T1.P1",
                    "pilar_id": "T1.P1",
                    "pilar_name": "Digital Workplace",
                    "score": 3.5,
                    "target_score": 4.5,
                    "asis_architecture_description": "Descripción de workplace.",
                    "gaps": [],
                    "health_check_asis": [],
                    "target_architecture_tobe": {
                        "vision": "Puesto digital nativo en nube y seguro",
                        "architecture_summary": "Puesto digital moderno en nube",
                        "key_technologies": ["Windows 11 Enterprise", "Intune"],
                    },
                    "projects_todo": [
                        {
                            "name": "Proyecto 1",
                            "priority": "Alta",
                            "sizing": "M",
                            "duration": "H1",
                            "horizon": "h1",
                            "capex_estimate": "50000",
                            "opex_delta": "-10000",
                            "objective": "Modernizar puestos",
                            "transformation_typology": "Modernización de puesto",
                            "business_case": "Retorno estimado en 18 meses",
                            "deliverables": ["D1", "D2"],
                        }
                    ],
                }
            ]

        async def fake_closing(*args, **kwargs):
            payload = kwargs.get("blueprint_payload") or args[-1]
            payload["executive_snapshot"] = {
                "bottom_line": "Estable",
                "cost_of_inaction": "Obsolescencia operativa y riesgo de seguridad",
                "structural_risks": ["Fin de soporte de SO"],
                "business_impact": "Pérdida de productividad en puestos",
                "operational_benefits": ["Automatización y despliegue rápido"],
                "transformation_complexity": "Media",
                "decisions": ["Proyecto 1"],
            }
            payload["strategic_alignment"] = "Alineado con DORA"
            payload["target_state_vision"] = "Arquitectura Cloud Soberana"
            payload["roadmap"] = [{"wave": "Ola 1", "projects": ["Proyecto 1"]}]
            payload["external_dependencies"] = []
            payload["design_principles"] = ["Principio 1", "Principio 2", "Principio 3"]

        # 2. Act: Execute with mocked AI generation and external services
        with patch(
            "assessment_engine.application.run_tower_blueprint_engine._resolve_epistemic_context",
            new_callable=AsyncMock,
            return_value=(mock_graph, mock_resolver, mock_ontology, "Resolved"),
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._resolve_gravity_profile",
            new_callable=AsyncMock,
            return_value=(4.2, ""),
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._execute_pillar_mapreduce",
            side_effect=fake_mr,
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._orchestrate_closing_agent",
            side_effect=fake_closing,
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._enrich_projects_finops",
            new_callable=AsyncMock,
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine.sync_findings_to_graph",
        ), patch(
            "assessment_engine.application.tools.adversarial_consensus_engine.AdversarialConsensusEngine.process_payload",
            new_callable=AsyncMock,
            side_effect=lambda tid, payload, **kwargs: payload,
        ), patch(
            "assessment_engine.infrastructure.policy_engine.SovereignPolicyEngine.compile",
            side_effect=lambda payload: payload,
        ), patch(
            "assessment_engine.application.tools.actuarial_ledger_generator.generate_actuarial_ledger",
        ):
            await run_tower_blueprint(client_name, tower_id)

        # 3. Assert: Output blueprint payload generated
        out_payload = tower_dir / "blueprint_t1_payload.json"
        assert out_payload.is_file(), "El archivo de salida blueprint_t1_payload.json debe existir."
        data = json.loads(out_payload.read_text(encoding="utf-8-sig"))
        assert data["document_meta"]["tower_code"] == "T1"
        assert data["document_meta"]["client_name"] == client_name

    finally:
        # Cleanup
        if client_dir.exists():
            shutil.rmtree(client_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_run_tower_blueprint_cegar_synthesis_cutover(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that run_tower_blueprint integrates with CegarSynthesisEngine when CEGAR mode is active."""
    monkeypatch.setenv("SYNTHESIS_ENGINE_MODE", "CEGAR")

    from decimal import Decimal
    from assessment_engine.domain.synthesis.schemas import (
        ExecutiveRoadmapPhase,
        FinancialProjection,
        OptimizationAxis,
        StrategicOption,
        VerifiedEnterpriseDeliverable,
    )

    fin = FinancialProjection(
        currency_iso_4217="EUR",
        capex_allocation=Decimal("60000.00"),
        opex_allocation=Decimal("90000.00"),
        total_cost_of_ownership=Decimal("150000.00"),
        risk_exposure_p10=Decimal("15000.00"),
        risk_exposure_p50=Decimal("45000.00"),
        risk_exposure_p90=Decimal("120000.00"),
    )
    opts = [
        StrategicOption(
            option_id="OPT-CAP1",
            primary_axis=OptimizationAxis.CAPITAL_EFFICIENCY,
            strategy_designation="Capital Efficiency Strategy",
            architectural_rationale=(
                "Modernization combining hybrid edge resilience with sovereign cloud decoupling. "
                "Provides substantial operational leverage while shielding core enterprise boundaries."
            ),
            sacrificed_dimension_analysis=(
                "Immediate short-term execution velocity is deliberately traded off in favor of comprehensive "
                "telemetry shielding and zero-trust verification baselines across distributed microservices."
            ),
            financials=fin,
            supporting_evidence_ids=["EV-001", "EV-002"],
            utility_weights={
                OptimizationAxis.CAPITAL_EFFICIENCY: 0.34,
                OptimizationAxis.OPERATIONAL_RESILIENCE: 0.33,
                OptimizationAxis.EXECUTION_VELOCITY: 0.33,
            },
        ),
        StrategicOption(
            option_id="OPT-RES2",
            primary_axis=OptimizationAxis.OPERATIONAL_RESILIENCE,
            strategy_designation="Operational Resilience Strategy",
            architectural_rationale=(
                "Comprehensive high resilience architecture shielding mission critical enterprise systems "
                "against cascading availability failures and malicious boundary penetration attempts."
            ),
            sacrificed_dimension_analysis=(
                "Immediate cost minimization is deliberately traded off for geographic redundancy, automated "
                "failover infrastructure, and multi-region active-active database clustering."
            ),
            financials=fin,
            supporting_evidence_ids=["EV-002", "EV-003"],
            utility_weights={
                OptimizationAxis.CAPITAL_EFFICIENCY: 0.33,
                OptimizationAxis.OPERATIONAL_RESILIENCE: 0.34,
                OptimizationAxis.EXECUTION_VELOCITY: 0.33,
            },
        ),
        StrategicOption(
            option_id="OPT-VEL3",
            primary_axis=OptimizationAxis.EXECUTION_VELOCITY,
            strategy_designation="Execution Velocity Strategy",
            architectural_rationale=(
                "Accelerated digital transformation utilizing pre-built enterprise modules, opinionated "
                "developer golden paths, and managed software-as-a-service application backbones."
            ),
            sacrificed_dimension_analysis=(
                "Bespoke architectural customization depth is traded off for speed to market, standardized "
                "deployment templates, and immediate commercial time-to-value acceleration."
            ),
            financials=fin,
            supporting_evidence_ids=["EV-004", "EV-005"],
            utility_weights={
                OptimizationAxis.CAPITAL_EFFICIENCY: 0.33,
                OptimizationAxis.OPERATIONAL_RESILIENCE: 0.33,
                OptimizationAxis.EXECUTION_VELOCITY: 0.34,
            },
        ),
    ]

    mock_deliverable = VerifiedEnterpriseDeliverable(
        bcp47_locale="en-US",
        industry_isic_code="6201",
        executive_thesis=(
            "The enterprise stands at a pivotal technological inflection point where technical entropy directly "
            "constrains commercial agility. Through disciplined capital allocation and automated governance, "
            "leadership can secure sovereign operational autonomy while reducing baseline expenditure."
        ),
        pareto_frontier=opts,
        selected_equilibrium_option_id="OPT-CAP1",
        equilibrium_justification=(
            "Selecting Option OPT-CAP1 establishes the optimal strategic equilibrium between risk exposure mitigation "
            "and capital efficiency across the multi-horizon transformation lifecycle. This posture satisfies strict "
            "corporate governance requirements while systematically remediating vulnerability vectors."
        ),
        execution_roadmap=[
            ExecutiveRoadmapPhase(
                phase_index=1,
                phase_title="Phase 1: Foundation",
                duration_weeks=12,
                deliverable_artifacts=["Telemetry Gateway"],
                allocated_budget=Decimal("60000.00"),
                evidence_citations=["EV-001", "EV-002"],
            ),
            ExecutiveRoadmapPhase(
                phase_index=2,
                phase_title="Phase 2: Modernization",
                duration_weeks=16,
                deliverable_artifacts=["Service Mesh"],
                allocated_budget=Decimal("90000.00"),
                evidence_citations=["EV-002", "EV-003"],
            ),
        ],
    )

    client_name = "test_cegar_client"
    monkeypatch.setenv("ASSESSMENT_CLIENT_ID", client_name)
    tower_id = "T1"
    client_dir = Path("working") / client_name
    tower_dir = client_dir / tower_id
    tower_dir.mkdir(parents=True, exist_ok=True)
    case_input = tower_dir / "case_input.json"
    case_input.write_text(json.dumps({"tower_name": "Datacenter & Cloud", "document_meta": {"tower_name": "Datacenter & Cloud", "language": "en", "currency": "EUR"}, "pillars": []}))

    try:
        mock_graph = MagicMock()
        mock_resolver = MagicMock()
        mock_ontology = MagicMock()

        async def fake_mr(*args, **kwargs):
            return {"findings": [], "kpis": []}

        async def fake_closing(*args, **kwargs):
            payload = kwargs.get("blueprint_payload") or args[-1]
            payload["executive_snapshot"] = {
                "bottom_line": "Stable baseline",
                "cost_of_inaction": "Operational obsolescence and security risk",
                "structural_risks": ["OS end of support"],
                "business_impact": "Productivity loss",
                "operational_benefits": ["Rapid deployment automation"],
                "transformation_complexity": "Medium",
                "decisions": ["Project 1"],
            }
            payload["strategic_alignment"] = "Aligned with DORA"
            payload["target_state_vision"] = "Sovereign Cloud Architecture"
            payload["roadmap"] = [{"wave": "Wave 1", "projects": ["Project 1"]}]
            payload["external_dependencies"] = []
            payload["design_principles"] = ["Principle 1", "Principle 2", "Principle 3"]

        with patch(
            "assessment_engine.application.run_tower_blueprint_engine._resolve_epistemic_context",
            new_callable=AsyncMock,
            return_value=(mock_graph, mock_resolver, mock_ontology, "Resolved"),
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._resolve_gravity_profile",
            new_callable=AsyncMock,
            return_value=(4.2, ""),
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._execute_pillar_mapreduce",
            side_effect=fake_mr,
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._orchestrate_closing_agent",
            side_effect=fake_closing,
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine._enrich_projects_finops",
            new_callable=AsyncMock,
        ), patch(
            "assessment_engine.application.run_tower_blueprint_engine.sync_findings_to_graph",
        ), patch(
            "assessment_engine.application.services.cegar_synthesis_engine.CegarSynthesisEngine.synthesize",
            new_callable=AsyncMock,
            return_value=mock_deliverable,
        ), patch(
            "assessment_engine.infrastructure.policy_engine.SovereignPolicyEngine.compile",
            side_effect=lambda payload: payload,
        ), patch(
            "assessment_engine.application.tools.actuarial_ledger_generator.generate_actuarial_ledger",
        ):
            await run_tower_blueprint(client_name, tower_id)

        out_payload = tower_dir / "blueprint_t1_payload.json"
        assert out_payload.is_file()
        data = json.loads(out_payload.read_text(encoding="utf-8-sig"))
        assert "pareto_frontier" in data
        assert "strategic_roadmap" in data
        assert "executive_synthesis" in data
        assert "cegar_financials" in data
        assert data["synthesis_provenance"]["engine"] == "CEGAR_VERIFIED_V1"

    finally:
        if client_dir.exists():
            shutil.rmtree(client_dir, ignore_errors=True)
