from typing import List

from pydantic import BaseModel, Field

from .common import BaseDraftModel


class AsIsPillar(BaseModel):
    pillar: str = Field(..., description="Nombre del pilar")
    score: float = Field(..., description="Puntuación del pilar")
    maturity_level: str = Field(
        ..., description="Nivel de madurez (ej. Nivel 2 - Básico)"
    )
    findings_summary: List[str] = Field(..., description="Resumen de hallazgos")
    operational_impact: str = Field(..., description="Impacto operativo")


class AsIsDraft(BaseDraftModel):
    section_id: str = "asis"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "AS-IS"
    executive_narrative: str
    pillars: List[AsIsPillar]
    cross_cutting_themes: List[str]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        return [
            "TO-BE",
            "estado objetivo",
            "capacidades objetivo",
            "roadmap",
            "recomendamos",
            "plan de accion",
        ]
