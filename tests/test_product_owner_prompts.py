from __future__ import annotations

from assessment_engine.prompts.product_owner_prompts import (
    render_plan_markdown,
    render_task_prompt,
)


def test_render_plan_markdown_includes_core_sections() -> None:
    plan = {
        "request_title": "Improve global report",
        "problem": "Summary is weak",
        "value_expected": "Executives understand risks faster",
        "in_scope": ["global payload"],
        "out_of_scope": ["commercial flow"],
        "source_of_truth": ["docs/README.md"],
        "invariants": ["do not break smoke"],
        "validation_plan": ["pytest tests/ -q"],
        "risk_level": "medium",
        "tasks": [
            {
                "title": "Update global payload",
                "objective": "Refine executive summary",
                "in_scope": ["builder"],
                "source_of_truth": ["src/..."],
                "invariants": ["same schema"],
                "validation": ["pytest"],
            }
        ],
    }

    rendered = render_plan_markdown(plan)

    assert "# Improve global report" in rendered
    assert "## Problem" in rendered
    assert "## 1. Update global payload" in rendered


def test_render_task_prompt_appends_validation_feedback() -> None:
    plan = {
        "request_title": "Improve global report",
        "problem": "Summary is weak",
        "value_expected": "Executives understand risks faster",
        "invariants": ["do not break smoke"],
    }
    task = {"id": "task-1", "title": "Update payload"}

    rendered = render_task_prompt(
        plan,
        task,
        attempt=2,
        validation_feedback="pytest failed in test_example",
    )

    assert '"attempt": 2' in rendered
    assert "pytest failed in test_example" in rendered
