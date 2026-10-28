"""Unit tests for commercial refiner agent orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest

from assessment_engine.application.run_commercial_refiner import (
    build_proactive_proposal,
    call_commercial_agent,
)
from assessment_engine.domain.schemas.commercial import EngagementManagerOutput


@pytest.mark.asyncio
async def test_call_commercial_agent_mock():
    """Verify that call_commercial_agent executes run_agent and returns structured output."""
    mock_response = {
        "context_and_why": {
            "origin": "Auditoría técnica",
            "cost_of_inaction": "Riesgo de indisponibilidad",
        },
        "solution_and_what": {
            "target_state": "Solución Cloud Native",
            "north_star_metric": "99.99% SLA",
        },
    }

    with patch(
        "assessment_engine.application.run_commercial_refiner.run_agent",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await call_commercial_agent(
            model_name="default",
            agent_role="ENGAGEMENT MANAGER",
            instruction="Generar contexto",
            payload_str="{}",
            schema_cls=EngagementManagerOutput,
            client_name="Acme",
        )
        assert result == mock_response


@pytest.mark.asyncio
async def test_build_proactive_proposal_mock():
    """Verify that build_proactive_proposal orchestrates commercial sub-agents into a unified proposal."""
    mock_agent_result = {}

    with patch(
        "assessment_engine.application.run_commercial_refiner.call_commercial_agent",
        new_callable=AsyncMock,
        return_value=mock_agent_result,
    ):
        opp = {"initiative": "Modernización de Red"}
        proposal = await build_proactive_proposal(
            model_name="default",
            opp=opp,
            payload_str="{}",
            client_name="Acme",
        )
        assert proposal["initiative_name"] == "Modernización de Red"
        assert "context_and_why" in proposal
        assert "solution_and_what" in proposal
        assert "scope_and_how" in proposal


def test_aggregate_blueprint_catalogs_lcr_killer(tmp_path: Path):
    """Verify that aggregate_blueprint_catalogs extracts initiatives with fallback objective and name fields."""
    import json
    from assessment_engine.application.run_commercial_refiner import aggregate_blueprint_catalogs

    bp_path = tmp_path / "blueprint_t1_payload.json"
    bp_data = {
        "document_meta": {"tower_code": "T1", "tower_name": "Torre 1"},
        "pillars_analysis": [
            {
                "projects_todo": [
                    {"name": "Proj1", "tech_objective": "Objetivo Tecnológico Solo"},
                    {"initiative": "Proj2", "objective": "Objetivo Directo Solo"},
                ]
            }
        ],
    }
    bp_path.write_text(json.dumps(bp_data), encoding="utf-8")

    catalog = aggregate_blueprint_catalogs([bp_path])
    inits = catalog["T1"]["initiatives"]
    assert inits[0]["name"] == "Proj1"
    assert inits[0]["objective"] == "Objetivo Tecnológico Solo"
    assert inits[1]["name"] == "Proj2"
    assert inits[1]["objective"] == "Objetivo Directo Solo"
