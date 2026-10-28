"""Top-Tier-1 domain schema validation and sovereign policy property tests."""

from __future__ import annotations

from typing import List

import pytest

from assessment_engine.domain.schemas.common import (
    BaseDraftModel,
    Defect,
    collect_all_strings,
)
from assessment_engine.domain.schemas.conclusion import ConclusionDraft
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.archimate import (
    ArchiMateDeliverablesPolicy,
)
from assessment_engine.infrastructure.policies.business_case import (
    BusinessCaseGroundingPolicy,
)


class SampleDraftModel(BaseDraftModel):
    title: str
    body: str

    def get_forbidden_phrases(self) -> List[str]:
        return ["CONFIDENCIAL_INTERNO", "BORRADOR_TEMPORAL"]


def test_collect_all_strings_nested():
    """Verify recursive string extraction across arbitrary dictionaries and lists."""
    nested = {
        "a": "uno",
        "b": ["dos", {"c": "tres", "d": 4, "e": True}],
        "f": None,
    }
    extracted = collect_all_strings(nested)
    assert extracted == ["uno", "dos", "tres"]


def test_base_draft_model_notes_filtering_and_strict_validation():
    """Verify that forbidden phrases are silently filtered in reviewer notes, but raise ValueError in body."""
    # 1. Permitted model with forbidden phrase in notes: should be stripped
    valid_model = SampleDraftModel(
        section_id="sec_01",
        title="Arquitectura de Red",
        body="Contenido técnico verificado.",
        notes_for_reviewer=["Nota limpia", "Nota con CONFIDENCIAL_INTERNO que debe eliminarse"],
    )
    assert valid_model.notes_for_reviewer == ["Nota limpia"]

    # 2. Model with forbidden phrase in content body: must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        SampleDraftModel(
            section_id="sec_01",
            title="BORRADOR_TEMPORAL de Red",
            body="Texto normal",
        )
    assert "frase prohibida" in str(exc_info.value)


def test_defect_severity_regex():
    """Verify regex pattern validation on Defect severity."""
    defect = Defect(
        severity="critical",
        type="Security",
        message="Credenciales expuestas",
        suggested_fix="Rotar llaves",
    )
    assert defect.severity == "critical"

    with pytest.raises(ValueError):
        Defect(
            severity="extreme",  # Invalid enum
            type="Security",
            message="Error",
            suggested_fix="Fix",
        )


def test_conclusion_draft_validation_and_forbidden_phrases():
    """Verify ConclusionDraft enforces non-empty fields and forbids generic roadmap phrases."""
    # Valid conclusion
    valid = ConclusionDraft(
        tower_id="T1",
        tower_name="Workplace",
        final_assessment="Evaluación madura con oportunidades de optimización.",
        executive_message="Acelerar la adopción de automatización.",
        priority_focus_areas=["Automatización"],
        closing_statement="Cierre estratégico verificado.",
    )
    assert valid.section_id == "conclusion"

    # Empty final_assessment raises ValueError
    with pytest.raises(ValueError) as exc_empty:
        ConclusionDraft(
            tower_id="T1",
            tower_name="Workplace",
            final_assessment="",
            executive_message="Mensaje",
            priority_focus_areas=["Automatización"],
            closing_statement="Cierre estratégico verificado.",
        )
    assert "final_assessment" in str(exc_empty.value)

    # Forbidden phrase "quick wins" raises ValueError
    with pytest.raises(ValueError) as exc_forbidden:
        ConclusionDraft(
            tower_id="T1",
            tower_name="Workplace",
            final_assessment="Implantar quick wins en el primer mes.",
            executive_message="Mensaje",
            priority_focus_areas=["Automatización"],
            closing_statement="Cierre estratégico verificado.",
        )
    assert "frase prohibida" in str(exc_forbidden.value)


def test_business_case_grounding_policy():
    """Verify that BusinessCaseGroundingPolicy links project to matching AS-IS findings."""
    policy = BusinessCaseGroundingPolicy()
    graph = EpistemicGraph()

    payload = {
        "document_meta": {"language": "es", "regulatory_frameworks": ["DORA", "NIS2"]},
        "pillars_analysis": [
            {
                "health_check_asis": [
                    {
                        "node_id": "FIND-01",
                        "finding": "Obsolescencia crítica en el sistema operativo",
                        "impact": "Riesgo de denegación de servicio",
                    }
                ],
                "projects_todo": [
                    {
                        "name": "Actualización de Sistema Operativo Base",
                        "tech_objective": "Despliegue automatizado",
                    },
                    {
                        "name": "Proyecto Sin Coincidencia",
                        "tech_objective": "Capacitación de equipo",
                    },
                ],
            }
        ],
    }

    evaluated = policy.evaluate_and_patch(graph, payload)
    p0 = evaluated["pillars_analysis"][0]["projects_todo"][0]
    p1 = evaluated["pillars_analysis"][0]["projects_todo"][1]

    # p0 matches finding
    assert p0.get("mitigates_risk_id") == "FIND-01"
    assert "business_case" in p0
    # p1 gets strategic enabler template fallback
    assert "business_case" in p1


def test_archimate_deliverables_policy():
    """Verify that ArchiMateDeliverablesPolicy enriches project deliverables with catalog items."""
    policy = ArchiMateDeliverablesPolicy()
    graph = EpistemicGraph()

    payload = {
        "document_meta": {"language": "es"},
        "pillars_analysis": [
            {
                "projects_todo": [
                    {
                        "name": "Despliegue de Kubernetes",
                        "tech_objective": "Plataforma de contenedores cloud native",
                        "deliverables": [],
                    }
                ]
            }
        ],
    }

    evaluated = policy.evaluate_and_patch(graph, payload)
    deliverables = evaluated["pillars_analysis"][0]["projects_todo"][0]["deliverables"]
    assert len(deliverables) > 0
    assert any(isinstance(d, str) and len(d) > 5 for d in deliverables)
