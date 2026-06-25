from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProductOwnerDoctorDiagnosis(BaseModel):
    """Encapsulates a diagnosis and proposed remediation for a system error.

    This data model represents the structured output of an automated analysis,
    determining the safety of a proposed fix, detailing the problem, outlining the
    solution, defining its scope (blast radius), and identifying any necessary
    violations of system invariants.

    Attributes:
        is_safe_to_proceed (bool): A flag indicating if the proposed fix can be
            applied automatically. This is `False` if the fix violates system
            invariants, modifies files outside the approved scope, or requires
            explicit human oversight.
        diagnosis (str): A user-facing explanation of the error's symptoms and root
            cause.
        proposed_cure (str): A detailed, technical implementation plan for
            remediating the identified error.
        blast_radius (list[str]): A comprehensive list of file paths that will be
            created or modified by the proposed cure.
        required_invariant_breach (str | None): The specific system invariant or
            architectural rule that the proposed cure must violate. This is `None`
            if no invariants are breached.
        second_order_impact (str): An analysis of the risks and consequences
            associated with violating a system invariant. This field is mandatory
            when `is_safe_to_proceed` is `False`.
    """

    is_safe_to_proceed: bool = Field(
        description="Indicates whether the proposed fix is safe to proceed automatically. True if within approved scope and invariants; False if it violates invariants, modifies out-of-scope files, or requires explicit human approval."
    )
    diagnosis: str = Field(
        description="A clear, user-facing explanation of the error symptom."
    )
    proposed_cure: str = Field(
        description="A detailed description of the implementation plan the Worker will execute to remediate the error."
    )
    blast_radius: list[str] = Field(
        default_factory=list,
        description="A list of file paths that will be modified to implement the proposed mitigation.",
    )
    required_invariant_breach: str | None = Field(
        default=None,
        description="If applicable, specifies the architectural rule or system invariant that must be violated to implement the proposed fix.",
    )
    second_order_impact: str = Field(
        description="An explanation of the violated system invariants and associated risks, required when `is_safe_to_proceed` is false."
    )


class ProductOwnerTask(BaseModel):
    """Represents a single, well-defined task specification for implementation.

    This data model serves as a structured specification for an engineering task,
    encapsulating all requirements necessary for unambiguous implementation and
    validation.

    Attributes:
        id: A unique identifier for the task.
        title: A concise, human-readable title for the task.
        objective: A detailed description of the task's primary goal and intended
            outcome.
        in_scope: A list of features or requirements explicitly included within the
            task's scope.
        source_of_truth: A list of URIs (e.g., URLs, file paths) pointing to
            authoritative reference documents.
        invariants: A list of logical conditions or business rules that must be
            maintained upon task completion.
        validation: A list of acceptance criteria or concrete validation steps to
            verify correctness and completion.
    """

    id: str
    title: str
    objective: str
    in_scope: list[str] = Field(default_factory=list)
    source_of_truth: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    validation: list[str] = Field(default_factory=list)


class ProductOwnerRisk(BaseModel):
    r"""{'docstring': 'A data model for a structured risk assessment of a technical approach.\n\nThis model encapsulates a single identified risk, its corresponding mitigation\nstrategy, the potential second-order effects of that mitigation, and\nassociated metadata such as implementation effort and reversibility.\n\nAttributes:\n    structural_risk (str): A description of the specific problem or\n        disadvantage introduced by an approach (e.g., \'Introduces request\n        latency\').\n    mitigation_strategy (str): The proposed mitigation or remediation\n        strategy for the identified risk.\n    second_order_impact (str): The new problem, trade-off, or cost\n        introduced by the proposed mitigation (e.g., \'Increased\n        infrastructure cost\').\n    reversibility (Literal["Two-Way Door", "One-Way Door"]): The ease with\n        which the mitigation can be rolled back. \'Two-Way Door\' indicates an\n        easily reversible change, while \'One-Way Door\' signifies a change\n        that is difficult or impossible to reverse.\n    mitigation_effort (Literal["Small", "Medium", "Large"]): The estimated\n        effort required to implement the proposed mitigation.\n    confidence_score (Literal["High", "Low"]): The confidence level in the\n        effectiveness and safety of the proposed mitigation.'}."""

    structural_risk: str = Field(
        description="A clear description of the specific problem or disadvantage introduced by this approach (e.g., 'Introduces request latency')."
    )
    mitigation_strategy: str = Field(
        description="The proposed mitigation or remediation strategy for the identified risk."
    )
    second_order_impact: str = Field(
        description="The new problem, trade-off, or cost introduced by the proposed mitigation (e.g., 'Increased infrastructure cost')."
    )
    reversibility: Literal["Two-Way Door", "One-Way Door"] = Field(
        description="The reversibility of the proposed mitigation, indicating the ease of rollback in case of failure."
    )
    mitigation_effort: Literal["Small", "Medium", "Large"] = Field(
        description="The estimated effort required to implement the proposed mitigation."
    )
    confidence_score: Literal["High", "Low"] = Field(
        description="The confidence score of the AI model regarding the effectiveness and safety of this mitigation."
    )


class ProductOwnerPlan(BaseModel):
    r"""{'docstring': 'Represents a comprehensive plan for a software change request.\n\n    This model structures the output of a planning phase, detailing the proposed\n    approach, its scope, associated risks, and the concrete tasks required for\n    implementation. It serves as a formal specification between the requestor and\n    the implementer.\n\n    Attributes:\n        approach_name (str): A descriptive name for the architectural approach,\n            e.g., \'Fast & Tactical\', \'Deep Refactor\', \'Safe & Minimal\'.\n        recommendation_use_case (str): A concise heuristic outlining the\n            conditions under which this approach is most suitable.\n        pros (list[str]): The primary advantages and benefits of adopting this\n            approach.\n        risks (list[ProductOwnerRisk]): An analysis of the disadvantages,\n            trade-offs, and potential risks associated with this approach.\n        refused (bool): A flag indicating if the request was refused due to being\n            destructive, out of scope, or violating safety constraints.\n        refusal_reason (str): The justification for the refusal, required if\n            `refused` is True.\n        request_title (str): The high-level title of the user\'s request.\n        branch_name (str): The suggested Git branch name for the implementation.\n        pr_title (str): The suggested title for the pull request.\n        commit_title (str): The suggested title for the primary commit.\n        risk_level (Literal["low", "medium", "high"]): The assessed risk level of\n            implementing the plan.\n        problem (str): A concise statement of the problem being solved.\n        value_expected (str): The expected business or technical value delivered by\n            the implementation of this plan.\n        in_scope (list[str]): Items explicitly considered within the scope of work.\n        out_of_scope (list[str]): Items explicitly considered outside the scope of\n            work.\n        source_of_truth (list[str]): Documents, specifications, or contacts that\n            serve as the source of truth for requirements.\n        invariants (list[str]): Conditions or properties that must remain true\n            throughout and after the implementation.\n        validation_plan (list[str]): Steps or criteria to validate that the\n            implementation is correct and complete.\n        tasks (list[ProductOwnerTask]): A structured sequence of tasks required to\n            implement the plan.'}."""

    approach_name: str = Field(
        default="Standard",
        description="A descriptive, concise name for the architectural approach (e.g., 'Fast & Tactical', 'Deep Refactor', 'Safe & Minimal').",
    )
    recommendation_use_case: str = Field(
        default="",
        description="A concise heuristic outlining the conditions under which this approach is most suitable.",
    )
    pros: list[str] = Field(
        default_factory=list,
        description="A list of the primary advantages and benefits of adopting this approach.",
    )
    risks: list[ProductOwnerRisk] = Field(
        default_factory=list,
        description="A detailed analysis of the disadvantages, trade-offs, and potential risks associated with this approach.",
    )
    refused: bool = Field(
        default=False,
        description="Indicates that the request was refused due to being destructive, out of scope, or violating safety constraints.",
    )
    refusal_reason: str = Field(
        default="",
        description="A justification for the refusal, required when `refused` is set to true.",
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
    """Encapsulates proposed architectural alternatives or a request for clarification.

    This data model either presents a collection of distinct architectural plans
    in response to a well-defined request, or it signals that the request is
    too ambiguous for implementation and requires user clarification. The state is
    determined by the `is_ambiguous` flag.

    Attributes:
        is_ambiguous (bool): A flag indicating if the user's request is too
            ambiguous to generate architectural plans. If true, `alternatives` will
            be empty and `clarification_question` will be populated.
        clarification_question (str): The question for the user to provide more
            details when the request is ambiguous. This field is populated if and
            only if `is_ambiguous` is true.
        alternatives (list[ProductOwnerPlan]): A list of 2 to 3 distinct
            architectural plans, each representing a viable approach. This list is
            populated if and only if `is_ambiguous` is false.
    """

    is_ambiguous: bool = Field(
        default=False,
        description="Indicates that the request is too vague for implementation and requires clarification from the user.",
    )
    clarification_question: str = Field(
        default="",
        description="Specifies the clarifying question for the human architect, required when `is_ambiguous` is true.",
    )
    alternatives: list[ProductOwnerPlan] = Field(
        default_factory=list,
        description="A collection of 2 to 3 distinct architectural approaches proposed to solve the core problem.",
    )
