"""Defines the validation procedures and supporting utilities for tower definition schemas used in the Assessment Engine pipeline."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    """Parse a JSON file from a path into a dictionary."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def _validate_top_level_structure(
    definition: dict[str, Any],
) -> tuple[str, str, list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Validate presence and types of mandatory top-level keys."""
    errors: list[str] = []
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
            errors.append(f"Missing required key: {key}")

    if not tower_id:
        errors.append("tower_id is empty.")
    if not tower_name:
        errors.append("tower_name is empty.")
    if not isinstance(pillars, list) or not pillars:
        errors.append("pillars must be a non-empty list.")
        pillars = []

    for k in ["score_bands", "maturity_scale", "working_rules"]:
        if not definition.get(k):
            errors.append(f"{k} is empty.")

    return tower_id, tower_name, pillars, questions, errors


def _validate_kpi_questions(
    kpi_id: str, kpi_questions: Any, errors: list[str]
) -> list[str]:
    """Validate list of questions embedded inside a single KPI."""
    question_ids: list[str] = []
    if not isinstance(kpi_questions, list):
        errors.append(f"{kpi_id} has questions with invalid shape.")
        return question_ids

    for question in kpi_questions:
        question_id = str(question.get("question_id", "")).strip().upper()
        question_text = str(question.get("question_text", "")).strip()
        if not question_id:
            errors.append(f"{kpi_id} contiene una question sin question_id.")
            continue
        question_ids.append(question_id)
        if not question_id.startswith(f"{kpi_id}.PR"):
            errors.append(f"{question_id} no pertenece al KPI {kpi_id}.")
        if not question_text:
            errors.append(f"{question_id} has empty question_text.")
    return question_ids


def _validate_pillar_hierarchy(
    tower_id: str, pillars: list[dict[str, Any]], errors: list[str]
) -> tuple[list[str], list[str], list[str], int]:
    """Validate pillar integrity, weights, and contained KPIs."""
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
            errors.append(f"{pillar_id} does not belong to tower {tower_id}.")
        if not pillar_name:
            errors.append(f"{pillar_id} has empty pillar_name.")

        weight = pillar.get("weight_pct")
        if not isinstance(weight, int):
            errors.append(f"{pillar_id} tiene weight_pct no entero.")
        else:
            total_weight += weight

        if not isinstance(kpis, list) or not kpis:
            errors.append(f"{pillar_id} must have a non-empty list of kpis.")
            continue

        for kpi in kpis:
            kpi_id = str(kpi.get("kpi_id", "")).strip().upper()
            kpi_name = str(kpi.get("kpi_name", "")).strip()
            if not kpi_id:
                errors.append(f"{pillar_id} contiene un KPI sin kpi_id.")
                continue
            kpi_ids.append(kpi_id)

            if not kpi_id.startswith(f"{pillar_id}.K"):
                errors.append(f"{kpi_id} no pertenece al pilar {pillar_id}.")
            if not kpi_name:
                errors.append(f"{kpi_id} has empty kpi_name.")

            if "questions" in kpi:
                q_ids = _validate_kpi_questions(
                    kpi_id, kpi.get("questions", []), errors
                )
                question_ids.extend(q_ids)

    return pillar_ids, kpi_ids, question_ids, total_weight


def _validate_top_level_questions(
    tower_id: str,
    questions: Any,
    pillar_ids: list[str],
    kpi_ids: list[str],
    embedded_question_ids: list[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate referential integrity of optional top-level questions catalog."""
    if not questions:
        return
    if not isinstance(questions, list):
        errors.append("questions debe ser lista cuando existe.")
        return

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
            errors.append(f"{question_id} does not belong to tower {tower_id}.")
        if pillar_id not in known_pillars:
            errors.append(
                f"{question_id} references nonexistent pillar_id: {pillar_id}."
            )
        if kpi_id not in known_kpis:
            errors.append(f"{question_id} references nonexistent kpi_id: {kpi_id}.")
        if not question_text:
            errors.append(f"{question_id} has empty question_text.")

    if len(top_question_ids) != len(set(top_question_ids)):
        errors.append("Duplicate question_ids detected in top-level questions.")
    if embedded_question_ids and set(top_question_ids) != set(embedded_question_ids):
        warnings.append(
            "Top-level questions do not exactly match embedded questions in pillars[*].kpis[*].questions."
        )


def validate_tower_definition(
    definition: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Validates a tower definition dictionary against canonical schema and consistency rules."""
    warnings: list[str] = []
    tower_id, tower_name, pillars, questions, errors = _validate_top_level_structure(
        definition
    )

    pillar_ids, kpi_ids, question_ids, total_weight = _validate_pillar_hierarchy(
        tower_id, pillars, errors
    )

    if len(pillar_ids) != len(set(pillar_ids)):
        errors.append("Hay pillar_id duplicados.")
    if len(kpi_ids) != len(set(kpi_ids)):
        errors.append("Hay kpi_id duplicados.")
    if question_ids and len(question_ids) != len(set(question_ids)):
        errors.append("Hay question_id duplicados en pillars[*].kpis[*].questions.")

    if pillars and total_weight != 100:
        errors.append(f"Sum of weight_pct is {total_weight}, expected 100.")

    _validate_top_level_questions(
        tower_id,
        questions,
        pillar_ids,
        kpi_ids,
        question_ids,
        errors,
        warnings,
    )
    return errors, warnings


def main() -> None:
    """Parses and validates a tower definition JSON file from a CLI argument."""
    parser = argparse.ArgumentParser()
    parser.add_argument("definition_json")
    args = parser.parse_args()

    path = Path(args.definition_json).resolve()
    definition = load_json(path)
    errors, warnings = validate_tower_definition(definition)

    logger.info(f"Archivo: {path}")
    if errors:
        logger.info("STATUS: ERROR")
        for item in errors:
            logger.info(f"ERROR: {item}")
        for item in warnings:
            logger.info(f"WARNING: {item}")
        raise SystemExit(1)

    if warnings:
        logger.info("STATUS: WARNINGS")
        for item in warnings:
            logger.info(f"WARNING: {item}")
    else:
        logger.info("STATUS: OK")


if __name__ == "__main__":
    main()
