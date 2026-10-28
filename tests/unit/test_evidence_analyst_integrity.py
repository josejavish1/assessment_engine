from unittest.mock import AsyncMock, patch

import pytest

from assessment_engine.application.run_evidence_analyst import build_findings


@pytest.mark.asyncio
async def test_evidence_analyst_rescues_hallucinated_fragment_ids():
    """Verify that hallucinated fragment IDs returned by the LLM are intercepted
    and safely remapped to physical evidence references from the ledger."""
    case_input = {
        "context_summary": "Test context",
        "answers": [
            {
                "kpi_id": "T1.P1.K1",
                "kpi_name": "Autonomía UPS",
                "value": 2.0,
                "question_text": "¿Cuál es la autonomía?",
            }
        ],
    }

    evidence_ledger = {
        "evidences": [
            {
                "fragment_id": "frag_real_001",
                "pillar_ids": ["T1.P1"],
                "source_type": "atomic_fragment",
                "excerpt": "UPS de 100 kVA con autonomía probada de 15 minutos.",
            }
        ]
    }

    scoring_output = {
        "case_id": "case_123",
        "tower_id": "T1",
        "tower_score_display_1d": "2.0",
        "pillar_scores": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Energía",
                "score_exact": 1.8,
            }
        ],
    }

    tower_definition = {
        "score_bands": [{"min": 1.0, "max": 2.5, "label": "Nivel 1 - Básico"}]
    }

    # Mock an LLM that hallucinates an invalid fragment ID
    mock_analysis = {
        "strength": "Existe SAI redundante.",
        "strength_fragment_id": "frag_hallucinated_999",  # Does NOT exist in ledger!
        "gap": "Baterías degradadas.",
        "gap_fragment_id": "frag_real_001",  # Real ID
        "risk_title": "Corte de suministro",
        "elicited_tef_score": 4,
        "elicited_lm_score": 5,
        "initiatives": [{"title": "Renovar banco de baterías"}],
    }

    with patch(
        "assessment_engine.application.run_evidence_analyst.run_agent",
        new=AsyncMock(return_value=mock_analysis),
    ):
        result = await build_findings(
            case_input, evidence_ledger, scoring_output, tower_definition
        )

        p1_findings = result["pillar_findings"][0]
        strength_frag = p1_findings["strengths"][0]["fragment_id"]
        gap_frag = p1_findings["gaps"][0]["fragment_id"]

        # Hallucinated ID must be rescued to the valid pillar fragment from the ledger
        assert strength_frag == "frag_real_001"
        assert gap_frag == "frag_real_001"

        # Initiative with e_lm=5 and p_score=1.8 must receive "Crítica" priority
        assert p1_findings["candidate_initiatives"][0]["priority"] == "Crítica"
