from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProductOwnerTask(BaseModel):
    id: str
    title: str
    objective: str
    in_scope: list[str] = Field(default_factory=list)
    source_of_truth: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    validation: list[str] = Field(default_factory=list)


class ProductOwnerPlan(BaseModel):
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
