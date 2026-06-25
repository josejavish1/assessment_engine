from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ApexDebateResponse(BaseModel):
    """Defines the structured response from an Apex debate about a task's feasibility.

    This model captures the outcome of a decision-making process, including the final
    verdict, the reasoning behind it, and any necessary next steps or revised
    instructions.

    Attributes:
        decision (Literal["APPROVED", "REJECTED", "INJECT_PREREQUISITE"]): The
            verdict on task feasibility. `APPROVED` allows the task to proceed,
            `REJECTED` aborts it, and `INJECT_PREREQUISITE` pauses it pending
            completion of prerequisite tasks.
        reasoning (str): A detailed rationale supporting the rendered verdict.
        revised_instruction (str | None): An optional, precise technical directive
            for the assigned worker agent to execute. Defaults to None.
        prerequisite_tasks (list[dict[str, str]]): A list of prerequisite emergency
            tasks required to resolve blocking conditions. Each dictionary is
            expected to contain 'id', 'title', and 'description' keys.
        is_terminal_failure (bool): A flag indicating if the task is deemed
            physically impossible (a "HARD_BLOCK"), signifying an unrecoverable
            state. Defaults to False.
    """
    decision: Literal["APPROVED", "REJECTED", "INJECT_PREREQUISITE"] = Field(
        description="The verdict on the task's feasibility. APPROVED: The task may proceed. REJECTED: The task must be aborted. INJECT_PREREQUISITE: The task is paused pending completion of prerequisite emergency tasks."
    )
    reasoning: str = Field(description="A detailed rationale supporting the rendered verdict.")
    revised_instruction: str | None = Field(
        default=None, description="A precise, technical directive for the assigned worker agent to execute."
    )
    prerequisite_tasks: list[dict[str, str]] = Field(
        default_factory=list,
        description="A list of prerequisite emergency tasks (id, title, description) that must be completed to resolve blocking conditions.",
    )
    is_terminal_failure: bool = Field(
        default=False,
        description="Indicates if the task is deemed physically impossible (HARD_BLOCK), signifying an unrecoverable state.",
    )


class ApexBatchStatus(BaseModel):
    """Represents the status of an individual Apex batch processing task.

    A data model used to serialize and validate status information for a
    specific batch task.

    Attributes:
        task_id: The unique string identifier for the batch task.
        status: The current execution status, constrained to one of 'pending',
            'running', 'success', 'failed', or 'aborted'.
        attempts: The integer count of execution attempts for the task.
        error_summary: A summary of the terminal error if the task has failed,
            otherwise None.
        branch_name: The source control branch associated with the task, if
            applicable.
    """
    task_id: str
    status: Literal["pending", "running", "success", "failed", "aborted"]
    attempts: int
    error_summary: str | None = None
    branch_name: str | None = None
