from unittest.mock import AsyncMock, MagicMock

import pytest

from assessment_engine.application.run_sota_researcher import research_pillar


@pytest.mark.asyncio
async def test_sota_researcher_robust_json_parsing_with_markdown_fences():
    """Verify that research_pillar correctly decodes JSON wrapped in conversational markdown text,
    without collapsing to an empty dictionary."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    # Complex markdown response that previously broke greedy regex
    mock_response.text = """
    Aquí está la investigación SOTA solicitada:
    ```json
    {
        "market_solutions": ["Cisco Nexus 9000", "Arista 7050X"],
        "strategic_benefits": "Baja latencia y telemetría por streaming.",
        "architectural_pattern": "Spine-and-Leaf EVPN-VXLAN"
    }
    ```
    Espero que esto sea de utilidad para el informe.
    """
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    p_name, result = await research_pillar(
        mock_client, "Redes y Conectividad", "Falta de automatización", "{}"
    )

    assert p_name == "Redes y Conectividad"
    assert "market_solutions" in result
    assert result["architectural_pattern"] == "Spine-and-Leaf EVPN-VXLAN"


def test_postprocess_refined_findings_schema_conformance():
    """Verify that postprocess_refined_findings enforces canonical schemas and preserves sovereign data."""
    from assessment_engine.application.run_executive_refiner import (
        postprocess_refined_findings,
    )

    raw_findings = {
        "_generation_metadata": {"version": "1.0"},
        "heatmap": [{"tower": "T1", "score": 3.2}],
        "tower_bottom_lines": [
            {
                "tower_id": "T1",
                "score": 3.2,
                "band": "Alineado",
                "status_color": "green",
            }
        ],
    }

    refined = {
        "burning_platform": [
            {
                "pain_point": "Latencia",
                "root_causes": "Falta de fibra",
            }  # string should be coerced to list
        ],
        "tower_bottom_lines": [
            {"tower_id": "T1"}  # score, band, status_color missing
        ],
        "target_vision": {
            "evolution_principles": [
                {"title": "Cloud Smart"}
            ],  # title should map to principle
            "strategic_pillars": [
                {"title": "Observabilidad"}
            ],  # title should map to pillar
        },
        "execution_roadmap": {
            "programs": [{"id": "PROG-1"}],
            "horizons": {
                "quick_wins_0_6_months": [
                    {
                        "title": "IaC Pilot",
                        "program_id": "PROG-1",
                        "objective": "Automatizar despliegue",
                    }
                ]
            },
        },
        "executive_decisions": ["Aprobar presupuesto Q1"],
    }

    result = postprocess_refined_findings(refined, raw_findings)

    # 1. Sovereign fields preserved
    assert result["_generation_metadata"] == {"version": "1.0"}
    assert result["heatmap"] == [{"tower": "T1", "score": 3.2}]

    # 2. Burning platform normalized
    assert result["burning_platform"][0]["root_causes"] == ["Falta de fibra"]

    # 3. Tower bottom lines populated
    assert result["tower_bottom_lines"][0]["score"] == 3.2
    assert result["tower_bottom_lines"][0]["band"] == "Alineado"
    assert result["tower_bottom_lines"][0]["status_color"] == "green"

    # 4. Target vision keys aligned
    assert (
        result["target_vision"]["evolution_principles"][0]["principle"] == "Cloud Smart"
    )
    assert result["target_vision"]["strategic_pillars"][0]["pillar"] == "Observabilidad"

    # 5. Roadmap normalized and temporal aliases migrated
    roadmap = result["execution_roadmap"]
    assert "quick_wins_0_3_months" in roadmap["horizons"]
    assert "quick_wins_0_6_months" not in roadmap["horizons"]
    qw_item = roadmap["horizons"]["quick_wins_0_3_months"][0]
    assert qw_item["program"] == "PROG-1"
    assert "program_id" not in qw_item
    assert qw_item["business_case"] == "Automatizar despliegue"
    assert "objective" not in qw_item
    assert qw_item["start_month"] == 1
    assert qw_item["duration_months"] == 3

    # 6. Executive decisions normalized to dict
    assert isinstance(result["executive_decisions"], dict)
    assert result["executive_decisions"]["immediate_decisions"] == [
        "Aprobar presupuesto Q1"
    ]
