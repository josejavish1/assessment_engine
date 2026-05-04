from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

class ApexDebateResponse(BaseModel):
    decision: Literal["APPROVED", "REJECTED", "INJECT_PREREQUISITE"] = Field(
        description="APPROVED: Seguir con el rescate. REJECTED: Abortar tarea. INJECT_PREREQUISITE: Pausar y ejecutar tareas de emergencia primero."
    )
    reasoning: str = Field(
        description="Justificación detallada de la decisión."
    )
    revised_instruction: str | None = Field(
        default=None,
        description="Instrucción técnica para el Worker."
    )
    prerequisite_tasks: list[dict[str, str]] = Field(
        default_factory=list,
        description="Lista de mini-tareas de emergencia (id, title, description) para arreglar pre-condiciones."
    )
    is_terminal_failure: bool = Field(
        default=False,
        description="True si se determina que la tarea es físicamente imposible (HARD_BLOCK)."
    )

class ApexBatchStatus(BaseModel):
    task_id: str
    status: Literal["pending", "running", "success", "failed", "aborted"]
    attempts: int
    error_summary: str | None = None
    branch_name: str | None = None
