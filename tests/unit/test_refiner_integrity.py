from unittest.mock import AsyncMock, MagicMock, patch

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
