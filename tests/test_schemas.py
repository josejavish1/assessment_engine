import pytest
from pydantic import ValidationError

from assessment_engine.schemas.blueprint import (
    PillarBlueprintDraft,
    ProjectToDo,
)


def test_pillar_blueprint_valid():
    """Verifica que un PillarBlueprintDraft válido se instancia correctamente."""
    data = {
        "pilar_id": "T2.P1",
        "pilar_name": "Compute Foundation",
        "health_check_asis": [
            {
                "capability": "HA",
                "finding": "Weak",
                "business_risk": "High"
            }
        ],
        "target_architecture_tobe": {
            "vision": "Cloud Native",
            "design_principles": ["IaC"]
        },
        "projects_todo": [
            {
                "name": "Project 1",
                "business_case": "ROI",
                "tech_objective": "Deploy",
                "deliverables": ["Script"],
                "sizing": "M",
                "duration": "3 months"
            }
        ]
    }
    obj = PillarBlueprintDraft(**data)
    assert obj.pilar_id == "T2.P1"
    assert len(obj.projects_todo) == 1

def test_pillar_blueprint_invalid():
    """Verifica que PillarBlueprintDraft lanza error si faltan campos obligatorios."""
    data = {
        "pilar_id": "T2.P1"
        # Faltan todos los demás campos
    }
    with pytest.raises(ValidationError):
        PillarBlueprintDraft(**data)

def test_project_todo_sizing_enum_candidate():
    """Verifica la estructura de ProjectToDo."""
    # Nota: Aquí podríamos añadir validaciones personalizadas en el futuro (ej. que sizing sea S, M, L, XL)
    data = {
        "name": "P1",
        "business_case": "BC",
        "tech_objective": "TO",
        "deliverables": ["D1"],
        "sizing": "INVALID_SIZING", # Actualmente el esquema acepta cualquier string
        "duration": "1m"
    }
    obj = ProjectToDo(**data)
    assert obj.sizing == "INVALID_SIZING"
