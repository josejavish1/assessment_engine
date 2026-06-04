from typing import List

from pydantic import BaseModel, Field, field_validator

from .common import BaseDraftModel


class TargetMaturity(BaseModel):
    recommended_level: str = Field(
        ..., description="Nivel de madurez objetivo (ej. Nivel 4 - Optimizado)"
    )
    recommended_score_reference: str = Field(
        ..., description="Puntuación numérica de referencia (ej. 4.0)"
    )
    justification: str = Field(
        ..., description="Justificación detallada del nivel objetivo"
    )


class PillarCapability(BaseModel):
    pillar: str = Field(..., description="Nombre del pilar")
    target_capabilities: List[str] = Field(
        ..., description="Lista de capacidades a alcanzar"
    )


class ToBeDraft(BaseDraftModel):
    section_id: str = "tobe"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "TO-BE"
    introduction: str
    target_maturity: TargetMaturity
    target_capabilities_by_pillar: List[PillarCapability]
    architecture_principles: List[str]
    operating_model_implications: List[str]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        return [
            "quick wins",
            "roadmap",
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "plan de evolucion",
            "plan de evolución",
        ]

    @field_validator("target_capabilities_by_pillar")
    @classmethod
    def validate_pillars_not_empty(cls, v):
        if not v:
            raise ValueError("Debe haber al menos un pilar con capacidades objetivo")
        return v


class Defect(BaseModel):
    severity: str = Field(..., pattern="^(critical|major|minor)$")
    type: str
    message: str
    suggested_fix: str


class ToBeReview(BaseModel):
    section_id: str = "tobe"
    status: str = Field(..., pattern="^(approve|revise|human_validation_required)$")
    overall_assessment: str
    defects: List[Defect] = []
    approval_conditions: List[str] = []
    review_notes: List[str] = []
