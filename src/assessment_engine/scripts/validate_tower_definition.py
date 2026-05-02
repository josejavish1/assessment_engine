"""
Módulo validate_tower_definition.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_tower_definition(definition: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    tower_id = str(definition.get("tower_id", "")).strip().upper()
    tower_name = str(definition.get("tower_name", "")).strip()
    pillars = definition.get("pillars", [])
    questions = definition.get("questions", [])

    required_top_level = [
        "tower_id",
        "tower_name",
        "pillars",
        "working_rules",
        "score_bands",
        "maturity_scale",
    ]
    for key in required_top_level:
        if key not in definition:
            errors.append(f"Falta clave requerida: {key}")

    if not tower_id:
        errors.append("tower_id vacío.")
    if not tower_name:
        errors.append("tower_name vacío.")
    if not isinstance(pillars, list) or not pillars:
        errors.append("pillars debe ser una lista no vacía.")
        pillars = []

    pillar_ids: list[str] = []
    kpi_ids: list[str] = []
    question_ids: list[str] = []

    total_weight = 0
    for pillar in pillars:
        pillar_id = str(pillar.get("pillar_id", "")).strip().upper()
        pillar_name = str(pillar.get("pillar_name", "")).strip()
        kpis = pillar.get("kpis", [])

        if not pillar_id:
            errors.append("Hay un pilar sin pillar_id.")
            continue
        pillar_ids.append(pillar_id)

        if tower_id and not pillar_id.startswith(f"{tower_id}.P"):
            errors.append(f"{pillar_id} no pertenece a la torre {tower_id}.")
        if not pillar_name:
            errors.append(f"{pillar_id} tiene pillar_name vacío.")

        weight = pillar.get("weight_pct")
        if not isinstance(weight, int):
            errors.append(f"{pillar_id} tiene weight_pct no entero.")
        else:
            total_weight += weight

        if not isinstance(kpis, list) or not kpis:
            errors.append(f"{pillar_id} debe tener una lista no vacía de kpis.")
            continue

        for kpi in kpis:
            kpi_id = str(kpi.get("kpi_id", "")).strip().upper()
            kpi_name = str(kpi.get("kpi_name", "")).strip()
            kpi_questions = kpi.get("questions", [])

            if not kpi_id:
                errors.append(f"{pillar_id} contiene un KPI sin kpi_id.")
                continue
            kpi_ids.append(kpi_id)

            if not kpi_id.startswith(f"{pillar_id}.K"):
                errors.append(f"{kpi_id} no pertenece al pilar {pillar_id}.")
            if not kpi_name:
                errors.append(f"{kpi_id} tiene kpi_name vacío.")

            if "questions" in kpi:
                if not isinstance(kpi_questions, list):
                    errors.append(f"{kpi_id} tiene questions con shape inválido.")
                for question in kpi_questions:
                    question_id = str(question.get("question_id", "")).strip().upper()
                    question_text = str(question.get("question_text", "")).strip()
                    if not question_id:
                        errors.append(
                            f"{kpi_id} contiene una question sin question_id."
                        )
                        continue
                    question_ids.append(question_id)
                    if not question_id.startswith(f"{kpi_id}.PR"):
                        errors.append(f"{question_id} no pertenece al KPI {kpi_id}.")
                    if not question_text:
                        errors.append(f"{question_id} tiene question_text vacío.")

    if len(pillar_ids) != len(set(pillar_ids)):
        errors.append("Hay pillar_id duplicados.")
    if len(kpi_ids) != len(set(kpi_ids)):
        errors.append("Hay kpi_id duplicados.")
    if question_ids and len(question_ids) != len(set(question_ids)):
        errors.append("Hay question_id duplicados en pillars[*].kpis[*].questions.")

    if pillars and total_weight != 100:
        errors.append(f"La suma de weight_pct es {total_weight}, no 100.")

    if questions:
        if not isinstance(questions, list):
            errors.append("questions debe ser lista cuando existe.")
            questions = []
        known_pillars = set(pillar_ids)
        known_kpis = set(kpi_ids)
        top_question_ids: list[str] = []
        for question in questions:
            question_id = str(question.get("question_id", "")).strip().upper()
            pillar_id = str(question.get("pillar_id", "")).strip().upper()
            kpi_id = str(question.get("kpi_id", "")).strip().upper()
            question_text = str(question.get("question_text", "")).strip()
            if not question_id:
                errors.append("Hay una question top-level sin question_id.")
                continue
            top_question_ids.append(question_id)
            if tower_id and not question_id.startswith(f"{tower_id}.P"):
                errors.append(f"{question_id} no pertenece a la torre {tower_id}.")
            if pillar_id not in known_pillars:
                errors.append(
                    f"{question_id} referencia un pillar_id inexistente: {pillar_id}."
                )
            if kpi_id not in known_kpis:
                errors.append(
                    f"{question_id} referencia un kpi_id inexistente: {kpi_id}."
                )
            if not question_text:
                errors.append(f"{question_id} tiene question_text vacío.")
        if len(top_question_ids) != len(set(top_question_ids)):
            errors.append("Hay question_id duplicados en questions top-level.")
        if question_ids and set(top_question_ids) != set(question_ids):
            warnings.append(
                "Las questions top-level no coinciden exactamente con las embebidas en pillars[*].kpis[*].questions."
            )

    if not definition.get("score_bands"):
        errors.append("score_bands vacío.")
    if not definition.get("maturity_scale"):
        errors.append("maturity_scale vacío.")
    if not definition.get("working_rules"):
        errors.append("working_rules vacío.")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("definition_json")
    args = parser.parse_args()

    path = Path(args.definition_json).resolve()
    definition = load_json(path)
    errors, warnings = validate_tower_definition(definition)

    print(f"Archivo: {path}")
    if errors:
        print("STATUS: ERROR")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARNING: {item}")
        raise SystemExit(1)

    if warnings:
        print("STATUS: WARNINGS")
        for item in warnings:
            print(f"WARNING: {item}")
    else:
        print("STATUS: OK")


if __name__ == "__main__":
    main()
