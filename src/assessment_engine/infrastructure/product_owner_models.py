from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOwnerRiskItem(BaseModel):
    """Representa un elemento de la matriz de riesgos ejecutiva de un plan."""

    structural_risk: str = Field(default="", description="Riesgo estructural o desventaja identificado")
    mitigation_strategy: str = Field(default="", description="Estrategia técnica para mitigar el riesgo")
    second_order_impact: str = Field(default="", description="Impacto de segundo orden o coste asociado a la cura")
    reversibility: str = Field(default="Two-Way Door", description="Facilidad de reversión: 'Two-Way Door' o 'One-Way Door'")
    mitigation_effort: str = Field(default="Medium", description="Esfuerzo de mitigación: 'Small', 'Medium', 'Large'")
    confidence_score: str = Field(default="High", description="Nivel de confianza en la mitigación: 'High', 'Low'")


class ProductOwnerTask(BaseModel):
    """Representa una tarea técnica atómica ejecutable por un agente especializado."""

    id: str = Field(..., description="Identificador único de la tarea (ej. 'task_1')")
    title: str = Field(..., description="Título técnico conciso de la tarea")
    objective: str = Field(..., description="Objetivo concreto y verificable")
    in_scope: List[str] = Field(default_factory=list, description="Archivos o componentes dentro de alcance")
    source_of_truth: List[str] = Field(default_factory=list, description="Documentos o archivos que actúan como fuente de verdad")
    invariants: List[str] = Field(default_factory=list, description="Reglas y restricciones inmutables")
    validation: List[str] = Field(default_factory=list, description="Comandos o pruebas para validar la tarea")


class ProductOwnerPlan(BaseModel):
    """Representa un enfoque arquitectónico alternativo completo para resolver una petición."""

    approach_name: str = Field(..., description="Nombre del enfoque (ej. 'Opción 1: Parsing Topológico con BeautifulSoup')")
    recommendation_use_case: str = Field(default="", description="Criterio de recomendación ejecutiva ('Elígelo si...')")
    pros: List[str] = Field(default_factory=list, description="Ventajas técnicas y operativas del enfoque")
    risks: List[ProductOwnerRiskItem] = Field(default_factory=list, description="Matriz de riesgos, impacto de segundo orden y mitigaciones")
    request_title: str = Field(..., description="Título de la petición técnica")
    problem: str = Field(..., description="Descripción del problema técnico a resolver")
    value_expected: str = Field(..., description="Valor esperado de la solución")
    in_scope: List[str] = Field(default_factory=list, description="Alcance de archivos a modificar o crear")
    out_of_scope: List[str] = Field(default_factory=list, description="Elementos explícitamente fuera de alcance")
    source_of_truth: List[str] = Field(default_factory=list, description="Archivos o documentos canónicos de referencia")
    invariants: List[str] = Field(default_factory=list, description="Invariantes del repositorio a respetar")
    validation_plan: List[str] = Field(default_factory=list, description="Comandos de validación a ejecutar")
    risk_level: str = Field(default="medium", description="Nivel de riesgo ('low', 'medium', 'high')")
    branch_name: str = Field(default="", description="Nombre de la rama git sugerida")
    pr_title: str = Field(default="", description="Título del pull request")
    commit_title: str = Field(default="", description="Título del commit")
    tasks: List[ProductOwnerTask] = Field(default_factory=list, description="Lista ordenada de tareas técnicas ejecutables")


class ProductOwnerAlternatives(BaseModel):
    """Contenedor de planes alternativos y validaciones de ambigüedad/rechazo."""

    is_ambiguous: bool = Field(default=False, description="True si la petición es ambigua y requiere aclaración")
    clarification_question: Optional[str] = Field(default=None, description="Pregunta de aclaración si is_ambiguous es True")
    refused: bool = Field(default=False, description="True si la petición no puede ser atendida por ser destructiva")
    refusal_reason: Optional[str] = Field(default=None, description="Motivo del rechazo de la petición")
    best_index: int = Field(default=0, description="Índice de la alternativa recomendada (0-based)")
    alternatives: List[ProductOwnerPlan] = Field(default_factory=list, description="Lista de planes alternativos estructurados")
