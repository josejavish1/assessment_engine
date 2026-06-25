"""Implements the core processing pipeline and foundational utilities for the Assessment Engine."""

import argparse
import json
from pathlib import Path
from typing import Any, cast

from domain.maturity_band import resolve_maturity_band
from infrastructure.runtime_paths import ROOT


def load_json(path: Path) -> dict[str, Any]:
    """Load and decode a JSON file from a specified path using 'utf-8-sig' encoding."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def average(values: list[float]) -> float:
    """Calculate the arithmetic mean of a list of floats, returning 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0


def round_display(value: float) -> float:
    """{'docstring': 'Round a floating-point number to one decimal place.'}."""
    return round(value, 1)


def resolve_band(score: float, tower_definition: dict) -> dict:
    """Find the corresponding score band for a given numerical score.

    This function extracts the `score_bands` list from a `tower_definition`
    dictionary and delegates to `resolve_maturity_band` to find the
    appropriate band for the given score. A fixed score precision of 4 decimal
    places is used for the underlying comparison.

    Args:
        score: The numerical score to be categorized into a band.
        tower_definition: The configuration dictionary for a tower. This must
            contain a "score_bands" key whose value is a list of band
            definition dictionaries.

    Returns:
        A dictionary representing the matched score band.

    Raises:
        ValueError: If the score does not fall within any of the defined bands.
        TypeError: If the value associated with the 'score_bands' key is not a
            list of dictionaries.
    """
    return dict(
        resolve_maturity_band(
            score,
            tower_definition.get("score_bands", []),
            score_precision=4,
        )
    )


def build_scoring(case_input: dict, tower_definition: dict) -> dict:
    """Calculates pillar and tower scores from user answers and a tower definition.

    Aggregates scores from individual key performance indicator (KPI) answers to
    compute scores for pillars and a final, weighted tower score. The process
    involves three stages:
    1.  KPI Score Calculation: Averages the scores for all answers corresponding
        to a single KPI.
    2.  Pillar Score Calculation: Averages the calculated scores of all KPIs
        that constitute a single pillar.
    3.  Tower Score Calculation: Computes a weighted average of all pillar scores
        to determine the final tower score.

    The final score is also used to resolve a qualitative maturity band based
    on predefined thresholds in the tower definition.

    Args:
        case_input: A dictionary containing case data and user responses.
            Expected structure includes 'case_id', 'tower_id', 'tower_name',
            'target_maturity_default', and an 'answers' list where each
            element is a dictionary with 'kpi_id' and a numeric 'value'.
        tower_definition: A dictionary defining the tower's structure,
            weighting, and scoring rules. Expected structure includes a 'pillars'
            list (each with 'pillar_id', 'weight_pct', and a list of 'kpis'),
            'working_rules', and a 'maturity_scale'.

    Returns:
        A dictionary containing the detailed scoring results. This includes
        case/tower identifiers, aggregation methods, pillar-level scores, the
        final weighted tower score, the resolved maturity band, and the gap
        to a target maturity.

    Raises:
        KeyError: If a required key (e.g., 'case_id', 'pillar_id', 'kpi_id')
            is missing from the input dictionaries.
        ValueError: If a value that must be numeric for calculation (e.g., an
            answer's 'value' or a pillar's 'weight_pct') cannot be
            converted to a float.
    """
    answers = case_input.get("answers", [])
    answers_by_kpi: dict[str, list[float]] = {}
    for answer in answers:
        answers_by_kpi.setdefault(answer["kpi_id"], []).append(float(answer["value"]))

    pillar_scores = []
    weights_pct = {}

    for pillar in tower_definition.get("pillars", []):
        kpi_scores = []
        for kpi in pillar.get("kpis", []):
            scores = answers_by_kpi.get(kpi["kpi_id"], [])
            if scores:
                kpi_scores.append(average(scores))

        pillar_score = average(kpi_scores)
        pillar_scores.append(
            {
                "pillar_id": pillar["pillar_id"],
                "pillar_name": pillar["pillar_name"],
                "weight_pct": pillar["weight_pct"],
                "score_exact": round(pillar_score, 4),
                "score_display_1d": round_display(pillar_score),
            }
        )
        weights_pct[pillar["pillar_id"]] = pillar["weight_pct"]

    tower_score = sum(
        item["score_exact"] * (float(item["weight_pct"]) / 100.0)
        for item in pillar_scores
    )
    target_maturity_default = float(case_input.get("target_maturity_default", 4.0))
    band = resolve_band(tower_score, tower_definition)

    return {
        "case_id": case_input["case_id"],
        "tower_id": case_input["tower_id"],
        "tower_name": case_input["tower_name"],
        "aggregation_method": {
            "indicator": tower_definition["working_rules"]["score_indicator"],
            "pillar": tower_definition["working_rules"]["score_pillar"],
            "tower": tower_definition["working_rules"]["score_tower"],
        },
        "weights_pct": weights_pct,
        "pillar_scores": pillar_scores,
        "tower_score_exact": round(tower_score, 4),
        "tower_score_display_1d": round_display(tower_score),
        "maturity_band_from_exact": {
            "label": band["label"],
            "reading": next(
                (
                    level["operational_reading"]
                    for level in tower_definition.get("maturity_scale", [])
                    if level["label"] in band["label"]
                ),
                "",
            ),
        },
        "proposed_reporting_note": (
            "El score mostrado se redondea a una decimal, pero la banda cualitativa se determina "
            "con el score exacto interno para evitar saltos artificiales por redondeo."
        ),
        "target_maturity_default": target_maturity_default,
        "gap_to_target_exact": round(target_maturity_default - tower_score, 4),
    }


def main() -> None:
    """Executes the scoring pipeline from a case input file.

    This function orchestrates the end-to-end scoring process. It parses the
    `--case-input` command-line argument to locate a JSON file containing the
    case data. It then dynamically loads the corresponding tower definition based
    on the `tower_id` within the case data. The scoring is computed and the
    results are serialized to `scoring_output.json` in the same directory as
    the input file. A summary is printed to standard output.

    Raises:
        FileNotFoundError: If the case input file or its derived tower definition
            file does not exist.
        KeyError: If the `tower_id` key is not found in the case input data.
        json.JSONDecodeError: If the case input or tower definition file contains
            malformed JSON.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-input", required=True)
    args = parser.parse_args()

    case_input_path = Path(args.case_input).resolve()
    case_input = load_json(case_input_path)
    tower_definition = load_json(
        ROOT
        / "engine_config"
        / "towers"
        / case_input["tower_id"]
        / f"tower_definition_{case_input['tower_id']}.json"
    )
    scoring = build_scoring(case_input, tower_definition)
    output_path = case_input_path.with_name("scoring_output.json")
    output_path.write_text(
        json.dumps(scoring, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"scoring generado en: {output_path}")
    print(f"tower_score_exact: {scoring['tower_score_exact']}")


if __name__ == "__main__":
    main()
