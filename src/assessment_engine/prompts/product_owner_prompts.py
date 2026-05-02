from __future__ import annotations

import json


def get_product_owner_planner_instruction(max_tasks: int) -> str:
    return f"""
Eres un planner técnico para un orquestador enterprise de cambios asistidos por IA.

Tu trabajo es convertir una petición de negocio de un product owner en:
- una spec mínima verificable;
- una rama sugerida;
- un título de commit y PR;
- un nivel de riesgo;
- y un conjunto pequeño de tareas ejecutables.

Reglas obligatorias:
- no inventes capacidades que no se han pedido;
- mantén el alcance pequeño y acotado;
- no mezcles rediseños no relacionados;
- toda tarea debe tener source_of_truth, invariants y validation;
- las tasks deben ser entre 1 y {max_tasks};
- el branch_name debe ser corto, legible y seguro para git;
- el commit_title debe ser una línea breve;
- el pr_title debe explicar el cambio de negocio.

Piensa en este repo con estas reglas:
- spec-first;
- tests, docs, quality y typing como gates;
- nada de lógica importante solo en prompts;
- rama por cambio y PR antes de merge.
""".strip()


def build_product_owner_planner_prompt(request_text: str) -> str:
    return (
        "Convierte esta petición de product owner en un plan estructurado.\n\n"
        "Petición:\n"
        f"{request_text.strip()}\n\n"
        "Devuelve solo JSON válido conforme al schema requerido."
    )


def render_plan_markdown(plan: dict) -> str:
    tasks = "\n".join(
        [
            f"## {index}. {task['title']}\n"
            f"- Objective: {task['objective']}\n"
            f"- In scope: {', '.join(task.get('in_scope', [])) or 'n/a'}\n"
            f"- Source of truth: {', '.join(task.get('source_of_truth', [])) or 'n/a'}\n"
            f"- Invariants: {', '.join(task.get('invariants', [])) or 'n/a'}\n"
            f"- Validation: {', '.join(task.get('validation', [])) or 'n/a'}\n"
            for index, task in enumerate(plan.get("tasks", []), start=1)
        ]
    )
    return (
        f"# {plan['request_title']}\n\n"
        f"## Problem\n- {plan['problem']}\n\n"
        f"## Value expected\n- {plan['value_expected']}\n\n"
        f"## In scope\n"
        + "\n".join(f"- {item}" for item in plan.get("in_scope", []))
        + "\n\n## Out of scope\n"
        + "\n".join(f"- {item}" for item in plan.get("out_of_scope", []))
        + "\n\n## Source of truth\n"
        + "\n".join(f"- {item}" for item in plan.get("source_of_truth", []))
        + "\n\n## Invariants\n"
        + "\n".join(f"- {item}" for item in plan.get("invariants", []))
        + "\n\n## Validation plan\n"
        + "\n".join(f"- {item}" for item in plan.get("validation_plan", []))
        + f"\n\n## Risk level\n- {plan['risk_level']}\n\n"
        + tasks
        + "\n"
    )


def render_task_prompt(
    plan: dict,
    task: dict,
    *,
    attempt: int,
    validation_feedback: str | None = None,
) -> str:
    feedback_block = ""
    if validation_feedback:
        feedback_block = (
            "\nValidation feedback from previous attempt:\n"
            f"{validation_feedback.strip()}\n"
        )

    payload = {
        "request_title": plan["request_title"],
        "problem": plan["problem"],
        "value_expected": plan["value_expected"],
        "global_invariants": plan.get("invariants", []),
        "task": task,
        "attempt": attempt,
    }
    return (
        f"Goal: {task.get('objective', 'Implement the requested change')}\n\n"
        "Instructions:\n"
        "1. Implement exactly the task described in the 'Structured context' below in the current git branch.\n"
        "2. Keep the scope bounded to the task and preserve the listed invariants.\n"
        "3. Update tests and canonical documentation when needed.\n"
        "4. Do not introduce a second source of truth.\n"
        "5. You must use tools (like replace, write_file, or run_shell_command) to implement the change.\n\n"
        "Structured context:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
        f"{feedback_block}"
    )


def render_pr_reconciliation_prompt(
    plan: dict,
    pr_feedback: dict,
    *,
    attempt: int,
) -> str:
    payload = {
        "request_title": plan["request_title"],
        "problem": plan["problem"],
        "value_expected": plan["value_expected"],
        "global_invariants": plan.get("invariants", []),
        "validation_plan": plan.get("validation_plan", []),
        "attempt": attempt,
        "pull_request_feedback": pr_feedback,
    }
    return (
        "Address the open pull request feedback in the current git branch.\n"
        "Fix the reported review comments and failing checks without broadening scope.\n"
        "Do not bypass tests, typing, quality gates, documentation governance, or review controls.\n"
        "Prefer the existing source of truth and keep the branch ready for the repository validations.\n\n"
        "Structured context:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
    )
