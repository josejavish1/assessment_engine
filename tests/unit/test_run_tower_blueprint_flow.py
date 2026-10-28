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
            payload["design_principles"] = ["Principio 1", "Principio 2"]

        # 2. Act: Execute with mocked AI generation and external services
        with patch(
            "assessment_engine.application.run_tower_blueprint_engine._resolve_epistemic_context",
            new_callable=AsyncMock,
            return_value=(mock_graph, mock_resolver, mock_ontology, "Resuelta"),
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
