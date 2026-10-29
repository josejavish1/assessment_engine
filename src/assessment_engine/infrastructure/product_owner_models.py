from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOwnerRiskItem(BaseModel):
    """Represents an item within the executive risk matrix of an architectural plan."""

    structural_risk: str = Field(default="", description="Identified structural risk or architectural drawback")
    mitigation_strategy: str = Field(default="", description="Technical strategy to mitigate the risk")
    second_order_impact: str = Field(default="", description="Second-order operational impact or cost")
    reversibility: str = Field(default="Two-Way Door", description="Reversibility classification: 'Two-Way Door' or 'One-Way Door'")
    mitigation_effort: str = Field(default="Medium", description="Mitigation effort: 'Small', 'Medium', 'Large'")
    confidence_score: str = Field(default="High", description="Mitigation confidence score: 'High', 'Low'")


class ProductOwnerTask(BaseModel):
    """Represents an atomic technical task executable by a specialized agent."""

    id: str = Field(..., description="Unique task identifier (e.g. 'task_1')")
    title: str = Field(..., description="Concise technical title of the task")
    objective: str = Field(..., description="Concrete, verifiable objective")
    in_scope: List[str] = Field(default_factory=list, description="Files or components within scope")
    source_of_truth: List[str] = Field(default_factory=list, description="Canonical source of truth files")
    invariants: List[str] = Field(default_factory=list, description="Immutable rules and constraints")
    validation: List[str] = Field(default_factory=list, description="Commands or test suites to validate task")


class ProductOwnerPlan(BaseModel):
    """Represents a complete alternative architectural approach to resolve a request."""

    approach_name: str = Field(..., description="Name of the approach")
    recommendation_use_case: str = Field(default="", description="Executive recommendation criteria")
    pros: List[str] = Field(default_factory=list, description="Technical and operational advantages")
    risks: List[ProductOwnerRiskItem] = Field(default_factory=list, description="Risk matrix, second-order impacts, and mitigations")
    request_title: str = Field(..., description="Technical request title")
    problem: str = Field(..., description="Problem description")
    value_expected: str = Field(..., description="Expected solution value")
    in_scope: List[str] = Field(default_factory=list, description="Files to modify or create")
    out_of_scope: List[str] = Field(default_factory=list, description="Explicitly out-of-scope items")
    source_of_truth: List[str] = Field(default_factory=list, description="Canonical reference files")
    invariants: List[str] = Field(default_factory=list, description="Repository invariants to preserve")
    validation_plan: List[str] = Field(default_factory=list, description="Validation commands to execute")
    risk_level: str = Field(default="medium", description="Risk level ('low', 'medium', 'high')")
    branch_name: str = Field(default="", description="Suggested git branch name")
    pr_title: str = Field(default="", description="Pull request title")
    commit_title: str = Field(default="", description="Commit message title")
    tasks: List[ProductOwnerTask] = Field(default_factory=list, description="Ordered list of executable technical tasks")


class ProductOwnerAlternatives(BaseModel):
    """Container of alternative architectural plans and ambiguity/refusal validations."""

    is_ambiguous: bool = Field(default=False, description="True if the request is ambiguous and requires clarification")
    clarification_question: Optional[str] = Field(default=None, description="Clarification question when ambiguous")
    refused: bool = Field(default=False, description="True if the request is destructive or violates policy")
    refusal_reason: Optional[str] = Field(default=None, description="Reason for request refusal")
    best_index: int = Field(default=0, description="0-based index of recommended alternative")
    alternatives: List[ProductOwnerPlan] = Field(default_factory=list, description="List of structured alternative plans")
