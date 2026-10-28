from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from assessment_engine.domain.schemas.evidence import RaptorNode
from assessment_engine.infrastructure.raptor_engine import RaptorEngine


@pytest.mark.asyncio
async def test_raptor_summarize_group_injects_hard_metric_retention(
    tmp_path: Path,
):
    """Verify that Raptor summarization prompt rigorously enforces hard entity and metric preservation."""
    engine = RaptorEngine(client_id="test_density_client", storage_dir=tmp_path)
    nodes = [
        RaptorNode(
            node_id="n1",
            level=0,
            content="Switch central Cisco Catalyst 9300 con latencia media de 12 ms.",
        ),
        RaptorNode(
            node_id="n2",
            level=0,
            content="Ancho de banda de 40 Gbps interconectado con AWS Direct Connect.",
        ),
    ]

    mock_response = MagicMock()
    mock_response.text = (
        "Resumen estratégico con Cisco Catalyst 9300, 12 ms y 40 Gbps."
    )

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=mock_response
    )

    with patch("google.genai.Client", return_value=mock_client):
        summary = await engine._summarize_group(nodes)
        assert (
            summary
            == "Resumen estratégico con Cisco Catalyst 9300, 12 ms y 40 Gbps."
        )

        call_kwargs = mock_client.aio.models.generate_content.call_args.kwargs
        contents = call_kwargs["contents"]
        system_instruction = call_kwargs["config"]["system_instruction"]

        assert (
            "INVARIANTE DE PRESERVACIÓN DE ENTIDADES Y MÉTRICAS DURAS"
            in contents
        )
        assert "auditor forense de sistemas" in system_instruction
