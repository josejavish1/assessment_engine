from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import IO, Any, Protocol, cast


class _YamlModule(Protocol):
    def safe_load(self, stream: IO[str]) -> Any: ...


def _load_yaml_config(filename: str) -> dict:
    yaml = cast(_YamlModule, import_module("yaml"))
    filepath = Path(__file__).resolve().parent / "registry" / filename
    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_product_owner_planner_instruction(max_tasks: int) -> str:
    config = _load_yaml_config("product_owner_planner.yaml")

    # Helper to format sections
    def format_section(title, items):
        bullet_points = "\n".join(f"- {item}" for item in items)
        return f"{title}:\n{bullet_points}"

    # Build the prompt string from YAML
    prompt = f"""{config["persona"]}
{config["golden_rule"]}

{config["main_task"]["title"]}:
{format_section("", config["main_task"]["steps"])}

{config["alternative_plan_requirements"]["title"]}:
{format_section("", config["alternative_plan_requirements"]["fields"])}
   * {format_section("", config["alternative_plan_requirements"]["risk_matrix_fields"])}
{format_section("", config["alternative_plan_requirements"]["common_fields"])}

{format_section(config["general_rules"]["title"], config["general_rules"]["rules"])}

{format_section(config["repo_rules"]["title"], config["repo_rules"]["rules"])}
"""
    return prompt.strip().format(max_tasks=max_tasks)


def build_product_owner_planner_prompt(
    request_text: str, repo_context: str = ""
) -> str:
    context_block = ""
    if repo_context:
        context_block = f"=== CONTEXTO REPOSITORIO (SOLO LECTURA) ===\n{repo_context}\n=============================================\n\n"

    return (
        f"{context_block}"
        "⚠️ ATENCIÓN: LA SIGUIENTE ES LA ÚNICA TAREA QUE DEBES RESOLVER: ⚠️\n"
        "========================================================================\n"
        "PETICIÓN DEL PRODUCT OWNER:\n"
        f"{request_text.strip()}\n"
        "========================================================================\n\n"
        "Instrucciones Críticas:\n"
        "1. NO inventes características ni tareas basadas en el contexto del repositorio. Tu plan debe enfocarse EXCLUSIVAMENTE en resolver la PETICIÓN DEL PRODUCT OWNER.\n"
        "2. Devuelve solo JSON válido conforme al schema requerido."
    )


def get_product_owner_doctor_instruction() -> str:
    config = _load_yaml_config("product_owner_doctor.yaml")
    rules = "\n".join(f"{idx + 1}. {rule}" for idx, rule in enumerate(config["rules"]))
    return f"""{config["persona"]}
{config["context"]}
{config["mission"]}

REGLAS:
{rules}
""".strip()


def build_product_owner_doctor_prompt(plan: dict, task: dict, error_log: str) -> str:
    payload = {
        "request_title": plan["request_title"],
        "in_scope": plan.get("in_scope", []),
        "out_of_scope": plan.get("out_of_scope", []),
        "global_invariants": plan.get("invariants", []),
        "task_invariants": task.get("invariants", []),
    }
    return (
        "Evalúa este fallo de ejecución y emite un diagnóstico.\n\n"
        "Contexto del Plan Aprobado:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Log de Error del Quality Gate:\n"
        f"{error_log}\n\n"
        "Devuelve tu diagnóstico en formato JSON conforme al schema."
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
