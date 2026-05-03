from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProductOwnerDoctorDiagnosis(BaseModel):
    is_safe_to_proceed: bool = Field(
        description="True if the proposed fix is safe and within the approved scope/invariants. False if it violates invariants, modifies out-of-scope files, or requires human approval (Action Gate)."
    )
    diagnosis: str = Field(
        description="Explicación clara del error (Síntoma) en español."
    )
    proposed_cure: str = Field(
        description="Qué va a hacer el Worker para arreglar el error."
    )
    blast_radius: list[str] = Field(
        default_factory=list,
        description="Lista de archivos que se modificarán para aplicar la cura.",
    )
    required_invariant_breach: str | None = Field(
        default=None,
        description="Si aplica, describe qué regla arquitectónica o contrato base (invariante) es necesario romper para arreglar el problema.",
    )
    second_order_impact: str = Field(
        description="Si is_safe_to_proceed es False, explica qué pilar o invariante se rompe y los riesgos. En español."
    )


class ProductOwnerTask(BaseModel):
    id: str
    title: str
    objective: str
    in_scope: list[str] = Field(default_factory=list)
    source_of_truth: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    validation: list[str] = Field(default_factory=list)


class ProductOwnerRisk(BaseModel):
    structural_risk: str = Field(
        description="Descripción clara del problema o desventaja (ej. 'Añade latencia a las peticiones')."
    )
    mitigation_strategy: str = Field(
        description="La cura o solución propuesta para este riesgo."
    )
    second_order_impact: str = Field(
        description="El nuevo problema o coste que genera la cura (ej. 'Aumenta el coste de infraestructura')."
    )
    reversibility: Literal["Two-Way Door", "One-Way Door"] = Field(
        description="Facilidad para deshacer esta decisión si la mitigación falla."
    )
    mitigation_effort: Literal["Small", "Medium", "Large"] = Field(
        description="Esfuerzo estimado para implementar la mitigación."
    )
    confidence_score: Literal["High", "Low"] = Field(
        description="Nivel de confianza de la IA en esta mitigación."
    )


class ProductOwnerPlan(BaseModel):
    approach_name: str = Field(
        default="Standard",
        description="A short name for this approach, e.g. 'Fast & Tactical', 'Deep Refactor', 'Safe & Minimal'.",
    )
    recommendation_use_case: str = Field(
        default="",
        description="A short 'Choose this if...' (Elígelo si...) phrase explaining when to use this approach.",
    )
    pros: list[str] = Field(
        default_factory=list, description="List of pros for this approach."
    )
    risks: list[ProductOwnerRisk] = Field(
        default_factory=list,
        description="Detailed analysis of cons and risks for this approach.",
    )
    refused: bool = Field(
        default=False,
        description="Set to true if the request is destructive or out of scope.",
    )
    refusal_reason: str = Field(
        default="", description="Reason for refusal if refused is true."
    )
    request_title: str
    branch_name: str
    pr_title: str
    commit_title: str
    risk_level: Literal["low", "medium", "high"]
    problem: str
    value_expected: str
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    source_of_truth: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)
    tasks: list[ProductOwnerTask] = Field(default_factory=list)


class ProductOwnerAlternatives(BaseModel):
    is_ambiguous: bool = Field(
        default=False,
        description="Set to true if the request is too vague and you need to elicit input from the user before generating code.",
    )
    clarification_question: str = Field(
        default="",
        description="If is_ambiguous is true, what specific question do you need the human architect to answer?",
    )
    alternatives: list[ProductOwnerPlan] = Field(
        default_factory=list,
        description="Provide 2 to 3 distinct architectural approaches to solve the problem.",
    )
