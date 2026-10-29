"""Top-Tier-1 adversarial and property unit tests for the evidence analyst engine."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

from assessment_engine.application.run_evidence_analyst import (
    _format_answers_summary,
    band_for_score,
    build_findings,
    first_evidence_refs,
    main as main_evidence_analyst,
)


def test_first_evidence_refs_filtering_and_strict_limit():
    """Verify that first_evidence_refs maintains relative ordering, filters by pillar, and truncates strictly."""
    evidences = [
        {"evidence_id": "EV-01", "pillar_ids": ["T1.P1", "T1.P2"]},
        {"evidence_id": "EV-02", "pillar_ids": ["T1.P2"]},
        {"evidence_id": "EV-03", "pillar_ids": ["T1.P1"]},
        {"evidence_id": "EV-04", "pillar_ids": ["T1.P1"]},
        {"evidence_id": "EV-05", "pillar_ids": ["T1.P1"]},
    ]

    refs_p1 = first_evidence_refs(evidences, pillar_id="T1.P1", limit=2)
    assert refs_p1 == ["EV-01", "EV-03"]

    refs_p2 = first_evidence_refs(evidences, pillar_id="T1.P2", limit=5)
    assert refs_p2 == ["EV-01", "EV-02"]

    refs_empty = first_evidence_refs(evidences, pillar_id="T1.P99", limit=3)
    assert refs_empty == []


def test_first_evidence_refs_missing_key_error():
    """Verify that first_evidence_refs raises KeyError if evidence_id key is missing."""
    evidences = [{"pillar_ids": ["T1.P1"]}]
    with pytest.raises(KeyError):
        first_evidence_refs(evidences, pillar_id="T1.P1")


def test_band_for_score_resolution():
    """Verify that band_for_score resolves maturity band labels deterministically."""
    tower_def = {
        "score_bands": [
            {"min": 1.0, "max": 2.0, "label": "Inicial"},
            {"min": 2.0, "max": 3.0, "label": "Repetible"},
            {"min": 3.0, "max": 4.0, "label": "Definido"},
            {"min": 4.0, "max": 5.0, "label": "Optimizado"},
        ]
    }
    assert band_for_score(1.5, tower_def) == "Inicial"
    assert band_for_score(2.5, tower_def) == "Repetible"
    assert band_for_score(3.8, tower_def) == "Definido"


def test_format_answers_summary_structure():
    """Verify answers text serialization for LLM analytical prompts."""
    answers = [
        {"kpi_id": "T1.P1.K1.PR1", "kpi_name": "Autoservicio", "value": 4.0, "context": "Portal Jira"},
        {"kpi_id": "T1.P1.K1.PR2", "score": 2.0, "question_text": "¿Existe CMDB actualizada?"},
    ]
    summary = _format_answers_summary(answers)
    assert "KPI T1.P1.K1.PR1 (Autoservicio): Score 4.0 | Question/Context: Portal Jira" in summary
    assert "KPI T1.P1.K1.PR2: Score 2.0 | Question/Context: ¿Existe CMDB actualizada?" in summary


@pytest.mark.asyncio
async def test_build_findings_evidence_gate_hallucination_recovery():
    """Verify that the Evidence Gate intercepts hallucinated fragment IDs and reassigns valid ones."""
    case_input = {
        "answers": [
            {"kpi_id": "T1.P1.K1.PR1", "value": 3.0, "context": "Validación"}
        ],
        "language": "es",
    }
    evidence_ledger = {
        "evidences": [
            {
                "fragment_id": "FRAG-LEGAL-01",
                "evidence_id": "EV-01",
                "pillar_ids": ["T1.P1"],
                "source_type": "atomic_fragment",
                "excerpt": "Contrato de mantenimiento sin SLA 24/7.",
            }
        ]
    }
    scoring_output = {
        "tower_id": "T1",
        "tower_score_display_1d": "3.0",
        "pillar_scores": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Operaciones",
                "score_exact": 3.0,
            }
        ],
    }
    tower_def = {
        "score_bands": [{"min": 1.0, "max": 5.0, "label": "Definido"}]
    }

    # Mock agent returning hallucinated fragment IDs
    mock_agent_analysis = {
        "strength": "Equipo certificado en ITIL.",
        "strength_fragment_id": "HALLUCINATED_FRAG_999",
        "gap": "Procesos manuales de despliegue.",
        "gap_fragment_id": "HALLUCINATED_FRAG_888",
        "risk_title": "Riesgo de indisponibilidad",
        "risk_description": "Impacto en negocio.",
        "risk_magnitude": "Medio",
        "risk_loss_scenario": "Caída del servicio.",
        "risk_tef": 2.0,
        "risk_vuln": 0.3,
        "risk_fragment_id": "HALLUCINATED_FRAG_777",
        "initiative_title": "Automatización con Ansible",
        "initiative_description": "Despliegue continuo.",
        "initiative_rationale": "Reducción del MTTR.",
        "initiative_horizon": "h1",
        "initiative_effort": "M",
    }

    with patch(
        "assessment_engine.application.run_evidence_analyst.run_agent",
        new_callable=AsyncMock,
        return_value=mock_agent_analysis,
    ):
        findings = await build_findings(
            case_input=case_input,
            evidence_ledger=evidence_ledger,
            scoring_output=scoring_output,
            tower_definition=tower_def,
        )

        assert "pillar_findings" in findings
        p_res = findings["pillar_findings"][0]

        # The Evidence Gate MUST have scrubbed the hallucinated fragment ID and replaced it with the valid one
        assert p_res["strengths"][0]["fragment_id"] == "FRAG-LEGAL-01"
        assert p_res["gaps"][0]["fragment_id"] == "FRAG-LEGAL-01"


@pytest.mark.asyncio
async def test_main_evidence_analyst_cli(tmp_path: Path):
    """Verify main CLI execution for evidence analysis."""
    case_dir = tmp_path / "T1"
    case_dir.mkdir(parents=True, exist_ok=True)

    case_input_file = case_dir / "case_input.json"
    evidence_file = case_dir / "evidence_ledger.json"
    scoring_file = case_dir / "scoring_output.json"

    case_input_file.write_text(json.dumps({"answers": []}), encoding="utf-8")
    evidence_file.write_text(json.dumps({"evidences": []}), encoding="utf-8")
    scoring_file.write_text(
        json.dumps({"tower_id": "T1", "tower_score_display_1d": "3.0", "pillar_scores": []}),
        encoding="utf-8",
    )

    async def fake_build_findings(*args, **kwargs):
        return {"tower_id": "T1", "pillar_findings": []}

    with patch(
        "assessment_engine.application.run_evidence_analyst.build_findings",
        side_effect=fake_build_findings,
    ):
        await main_evidence_analyst([
            "--case-input", str(case_input_file),
            "--evidence-ledger", str(evidence_file),
            "--scoring-output", str(scoring_file),
        ])

    out_file = case_dir / "findings.json"
    assert out_file.is_file()
    saved = json.loads(out_file.read_text(encoding="utf-8-sig"))
    assert saved["tower_id"] == "T1"
