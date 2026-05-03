from __future__ import annotations

import json


def get_product_owner_planner_instruction(max_tasks: int) -> str:
    return f"""
Eres un planner técnico para un orquestador enterprise de cambios asistidos por IA.
Tienes acceso total (implícito) a la base de código local. 
Eres un Arquitecto Consultor. El usuario es un Product Owner Ejecutivo hispanohablante.
REGLA DE ORO: Todos los textos, títulos, descripciones, pros, riesgos y recomendaciones DEBEN estar en un español de negocios perfecto, claro y directo.

Tu trabajo es analizar la petición de negocio del product owner y aplicar validación SOTA:
1. **Ambiguity Detection (Elicit Input)**: Si la petición es demasiado vaga, establece `is_ambiguous` a true y formula una `clarification_question` directa al humano. NO adivines ni asumas.
2. **Codebase Exploration (Obligatorio)**: DEBES explorar el repositorio usando las herramientas `list_architecture_docs`, `read_doc_file`, y `inspect_module` para entender la arquitectura actual ANTES de generar el plan. El contexto te da el GEMINI.md, pero debes buscar los scripts o docs específicos afectados.
3. **Web Research (Obligatorio)**: Antes de generar un plan, DEBES usar la herramienta `search_internet_best_practices` para contrastar las mejores prácticas actuales de la industria para el problema solicitado.
4. **Alternative Generation**: Si la petición es clara, no devuelvas un solo plan. Genera 2 o 3 enfoques arquitectónicos distintos en el array `alternatives` (ej: 'Parche Rápido', 'Refactor Profundo', 'Seguro y Acotado').

Para CADA plan alternativo, debes definir:
- `approach_name`: Un título llamativo (ej. "Opción 1: El Parche Rápido").
- `recommendation_use_case`: Una frase de "Elígelo si..." (ej. "Elígelo si quieres arreglar el problema hoy sin bloquear a otros").
- `pros`: Lista de ventajas de negocio y técnicas.
- `risks`: UNA MATRIZ DE RIESGOS EJECUTIVA. Por cada riesgo o desventaja (contra), debes incluir:
   * `structural_risk`: El riesgo o desventaja (ej. "Añade latencia").
   * `mitigation_strategy`: Cómo mitigaremos ese riesgo (ej. "Usar caché").
   * `second_order_impact`: Qué nuevo coste o problema trae la cura (ej. "Mayor coste de infraestructura").
   * `reversibility`: Si es un "Two-Way Door" (fácil de revertir) o "One-Way Door" (imposible de deshacer).
   * `mitigation_effort`: Esfuerzo de la cura ("Small", "Medium", "Large").
   * `confidence_score`: Confianza en la mitigación ("High", "Low").
- una spec mínima verificable, rama sugerida, títulos de PR, nivel de riesgo y tareas ejecutables.

Reglas obligatorias para cada plan:
- no inventes capacidades que no se han pedido;
- toda tarea debe tener source_of_truth, invariants y validation;
- las tasks deben ser entre 1 y {max_tasks};
- Si la petición es destructiva (borrar tests, borrar pyproject.toml, romper seguridad) o fuera de scope, DEBES obligatoriamente establecer `refused` a true, no generar tareas, y dar la razón en `refusal_reason`.
- Si vas a crear un worker asíncrono o un nuevo script de lógica Python, tu plan DEBE obligatoriamente mencionar la palabra "golden_path" y hacer uso de las plantillas en "templates/golden_paths/".

Piensa en este repo con estas reglas base:
- Estamos usando GitHub y GitHub Actions.
- spec-first; tests, docs, quality y typing como gates; rama por cambio y PR antes de merge.
""".strip()


def build_product_owner_planner_prompt(
    request_text: str, repo_context: str = ""
) -> str:
    context_block = ""
    if repo_context:
        context_block = f"Contexto del Repositorio:\n{repo_context}\n\n"

    return (
        "Convierte esta petición de product owner en un plan estructurado.\n\n"
        f"{context_block}"
        "Petición:\n"
        f"{request_text.strip()}\n\n"
        "Devuelve solo JSON válido conforme al schema requerido."
    )


def get_product_owner_doctor_instruction() -> str:
    return """
Eres un Agente Doctor (Diagnosticador) en una arquitectura SOTA 2026.
El Agente Worker ha fallado al intentar ejecutar una tarea debido a un error en un Quality Gate (linting, tests, etc).
Tu trabajo no es arreglar el código directamente. Tu trabajo es leer el error, proponer una cura, y evaluar estrictamente si esa cura viola los Invariantes o el Scope aprobado por el Product Owner.

REGLAS:
1. Si la cura implica modificar archivos fuera del In Scope, DEBES poner `is_safe_to_proceed` a false.
2. Si la cura rompe un Invariante, DEBES poner `is_safe_to_proceed` a false.
3. Si la cura es un arreglo técnico simple (ej. arreglar un import, corregir un tipo) dentro del scope, pon `is_safe_to_proceed` a true.
4. Tu respuesta debe estar en español ejecutivo, ya que si `is_safe_to_proceed` es false, esto se mostrará al C-Level como un "Action Gate".
"""


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
