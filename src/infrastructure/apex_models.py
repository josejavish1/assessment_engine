from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ApexDebateResponse(BaseModel):
    """Represents the structured output of an Apex debate.

    This model encapsulates the final outcome of a deliberation process, detailing
    the decision made, the rationale behind it, and any follow-up actions
    required. It serves as a formal record and communication medium for the
    debate's conclusion.

    Attributes:
        decision (Literal["APPROVED", "REJECTED", "INJECT_PREREQUISITE"]): The
            final outcome of the debate. `APPROVED` authorizes the operation to
            proceed. `REJECTED` terminates the operation. `INJECT_PREREQUISITE`
            suspends the operation pending completion of new sub-tasks.
        reasoning (str): A comprehensive justification for the rendered decision.
        revised_instruction (str | None): An optional, revised technical
            instruction for the executing agent or system.
        prerequisite_tasks (list[dict[str, str]]): A list of sub-tasks that must
            be completed to satisfy preconditions. Each sub-task is a dictionary
            containing `id`, `title`, and `description` keys.
        is_terminal_failure (bool): An indicator for tasks deemed physically
            impossible. If True, the task is considered a hard block, and
            further execution attempts are prohibited.
    """
    decision: Literal["APPROVED", "REJECTED", "INJECT_PREREQUISITE"] = Field(
        description="An enumeration of the possible decision outcomes. `APPROVED`: The operation is authorized to proceed. `REJECTED`: The operation is terminated and will not be executed. `INJECT_PREREQUISITE`: The operation is suspended pending completion of newly defined prerequisite sub-tasks."
    )
    reasoning: str = Field(description="A comprehensive justification for the decision rendered.")
    revised_instruction: str | None = Field(
        default=None, description="A specific technical instruction for the agent or system responsible for task execution."
    )
    prerequisite_tasks: list[dict[str, str]] = Field(
        default_factory=list,
        description="A list of prerequisite sub-tasks that must be completed to satisfy operational preconditions. Each sub-task is specified by a unique `id`, `title`, and `description`.",
    )
    is_terminal_failure: bool = Field(
        default=False,
        description="A boolean indicator for physical impossibility. If `True`, the task is considered a `HARD_BLOCK`, and execution is prohibited.",
    )


class ApexBatchStatus(BaseModel):
    """Represents the data model for the status of a single task in an Apex batch job.

    Attributes:
        task_id (str): The unique identifier for the task.
        status (Literal["pending", "running", "success", "failed", "aborted"]):
            The current execution status of the task.
        attempts (int): The number of times this task has been attempted.
        error_summary (Optional[str]): A summary of the error if the task's
            status is "failed". Defaults to None.
        branch_name (Optional[str]): The source control branch name associated
            with the task, if applicable. Defaults to None.
    """
    task_id: str
    status: Literal["pending", "running", "success", "failed", "aborted"]
    attempts: int
    error_summary: str | None = None
    branch_name: str | None = None
