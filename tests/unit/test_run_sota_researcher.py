"""Top-Tier-1 adversarial and property unit tests for SOTA researcher orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from assessment_engine.application.run_sota_researcher import (
    inject_sota,
    load_json,
    main as main_sota_researcher,
    research_pillar,
)


@pytest.mark.asyncio
async def test_research_pillar_retry_and_recovery():
    """Verify that research_pillar retries transient API errors and recovers on subsequent attempt."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sota_solution_name": "OpenShift Virtualization 4.16",
        "strategic_benefit": "Elimina dependencias de hipervisores propietarios.",
        "architectural_pattern": "Modern Hybrid Cloud",
        "source_reference": {"url": "https://redhat.com/openshift"},
    })

    # Fail twice with RuntimeError, succeed on the third attempt
    mock_generate = AsyncMock(side_effect=[
        RuntimeError("Transient 503 Service Unavailable"),
        RuntimeError("Transient 500 Internal Error"),
        mock_response,
    ])
    mock_client.aio.models.generate_content = mock_generate

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        p_name, result = await research_pillar(
            mock_client,
            p_name="Plataformas Cloud",
            gap_text="Dependencia crítica de hardware on-premise.",
            grounding_json="{}",
        )

        assert mock_generate.call_count == 3
        assert mock_sleep.call_count == 2
        assert p_name == "Plataformas Cloud"
        assert result["sota_solution_name"] == "OpenShift Virtualization 4.16"
        assert "Elimina dependencias" in result["strategic_benefit"]


@pytest.mark.asyncio
async def test_research_pillar_exhausted_retries_fallback():
    """Verify that research_pillar gracefully applies empty fallback when all 3 API attempts fail."""
    mock_client = MagicMock()
    mock_generate = AsyncMock(side_effect=RuntimeError("Fatal API Outage"))
    mock_client.aio.models.generate_content = mock_generate

    with patch("asyncio.sleep", new_callable=AsyncMock):
        p_name, result = await research_pillar(
            mock_client,
            p_name="Redes y Conectividad",
            gap_text="Falta de redundancia en enlaces WAN.",
            grounding_json="{}",
        )

        assert mock_generate.call_count == 3
        assert p_name == "Redes y Conectividad"
        assert result == {}


@pytest.mark.asyncio
async def test_research_pillar_malformed_json_fallback():
    """Verify that research_pillar handles unparseable markdown/garbage responses with fallback."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is conversational filler with no valid JSON {} inside: [broken"
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    p_name, result = await research_pillar(
        mock_client,
        p_name="Observabilidad",
        gap_text="Carencia de métricas unificadas.",
        grounding_json="{}",
    )
    assert p_name == "Observabilidad"
    assert result == {}


@pytest.mark.asyncio
async def test_inject_sota_candidate_initiatives_enrichment(tmp_path: Path):
    """Verify that inject_sota augments candidate initiatives in-place with SOTA research data."""
    findings = {
        "pillar_findings": [
            {
                "pillar_name": "Seguridad y Cumplimiento",
                "gaps": [{"statement": "Gestión reactiva de vulnerabilidades."}],
                "candidate_initiatives": [
                    {"title": "Antiguo Título", "rationale": "Antiguo Rationale"}
                ],
            }
        ]
    }

    mock_sota_data = {
        "sota_solution_name": "Wiz Cloud-Native Application Protection",
        "strategic_benefit": "Visibilidad 100% de la superficie de ataque.",
        "architectural_pattern": "Agentless CNAPP",
        "source_reference": {"report": "Gartner MQ 2026"},
    }

    with patch(
        "assessment_engine.application.run_sota_researcher.research_pillar",
        new_callable=AsyncMock,
        return_value=("Seguridad y Cumplimiento", mock_sota_data),
    ), patch(
        "assessment_engine.application.run_sota_researcher.resolve_client_intelligence_path",
        return_value=tmp_path / "non_existent.json",
    ):
        enriched = await inject_sota("ClientTest", findings)

        init = enriched["pillar_findings"][0]["candidate_initiatives"][0]
        assert (
            "Implantación de Wiz Cloud-Native" in init["title"]
            or "Implementation of Wiz Cloud-Native" in init["title"]
        )
        assert "Visibilidad 100%" in init["rationale"]
        assert "Agentless CNAPP" in init["rationale"]


@pytest.mark.asyncio
async def test_main_sota_researcher_cli_execution(tmp_path: Path):
    """Verify main CLI command execution and JSON persistence."""
    findings_file = tmp_path / "findings.json"
    initial_data = {
        "pillar_findings": [
            {
                "pillar_name": "Cómputo",
                "gaps": [{"statement": "Saturación de CPU"}],
                "candidate_initiatives": [{"title": "Old", "rationale": "Old"}],
            }
        ]
    }
    findings_file.write_text(json.dumps(initial_data), encoding="utf-8")

    async def fake_inject(client_name, data):
        data["pillar_findings"][0]["candidate_initiatives"][0]["title"] = "Enriched Title"
        return data

    with patch(
        "assessment_engine.application.run_sota_researcher.inject_sota",
        side_effect=fake_inject,
    ):
        await main_sota_researcher([
            "--client", "TestClient",
            "--findings-path", str(findings_file),
        ])

    saved = json.loads(findings_file.read_text(encoding="utf-8-sig"))
    assert saved["pillar_findings"][0]["candidate_initiatives"][0]["title"] == "Enriched Title"
