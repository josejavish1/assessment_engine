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


@pytest.mark.asyncio
async def test_raptor_deterministic_metric_retention_rescues_dropped_metrics(
    tmp_path: Path,
):
    """Verify that when the LLM omits quantitative metrics, the deterministic gate rescues them."""
    engine = RaptorEngine(client_id="test_density_client", storage_dir=tmp_path)
    nodes = [
        RaptorNode(
            node_id="n1",
            level=0,
            content="Base de datos con 12 ms de latencia y 99.9% disponibilidad.",
        ),
        RaptorNode(
            node_id="n2",
            level=0,
            content="Capacidad contratada de 500 TB con coste mensual de 15.000 €.",
        ),
    ]

    # Mock an LLM that omitted the numbers and units in its abstractive summary
    mock_response = MagicMock()
    mock_response.text = (
        "La base de datos tiene alta disponibilidad y almacenamiento escalable."
    )

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=mock_response
    )

    with patch("google.genai.Client", return_value=mock_client):
        summary = await engine._summarize_group(nodes)

        # Verify the deterministic gate rescued and appended the exact missing metrics
        assert "[Métricas Críticas Preservadas]:" in summary
        assert "12 ms" in summary
        assert "99.9%" in summary
        assert "500 tb" in summary.lower() or "500 TB" in summary
        assert "15.000 €" in summary
