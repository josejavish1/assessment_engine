"""Defines the primary entry point and core utilities for the Assessment Engine scoring pipeline."""

import argparse
import json
from pathlib import Path

from assessment_engine.scripts.lib.maturity_band import resolve_maturity_band
from assessment_engine.scripts.lib.runtime_paths import ROOT


def load_json(path: Path) -> dict:
    """Load and deserialize a dictionary from a UTF-8 encoded JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def average(values: list[float]) -> float:
    """Return the arithmetic mean of a list of floats, or 0.0 if empty."""
    return sum(values) / len(values) if values else 0.0


def round_display(value: float) -> float:
    """Round a floating-point number to one decimal place."""
    return round(value, 1)


def resolve_band(score: float, tower_definition: dict) -> dict:
    """Resolve a numerical score into its corresponding maturity band dictionary."""
    return dict(
        resolve_maturity_band(
            score,
            tower_definition.get("score_bands", []),
            score_precision=4,
        )
    )


def build_scoring(case_input: dict, tower_definition: dict) -> dict:
    """Calculates a weighted tower score from raw case answers and a tower definition.

    The function aggregates numerical answer values into a final tower score through a
    multi-level process. First, an average score is computed for each Key
    Performance Indicator (KPI) based on its associated answers. These KPI scores
    are then averaged to produce a score for each pillar. Finally, a weighted
    average of the pillar scores determines the overall tower score. The function
    also resolves a qualitative maturity band corresponding to the final score.

    Args:
        case_input: A dictionary representing a user's submission. Must contain
            'case_id', 'tower_id', 'tower_name', and a list of 'answers'. Each
            element in the 'answers' list is a dictionary with 'kpi_id' and a
            numerical 'value'.
        tower_definition: A dictionary defining the structure and scoring rules for
            the tower. Must contain 'pillars', 'working_rules', and
            'maturity_scale'. The 'pillars' list must contain dictionaries, each
            specifying 'pillar_id', 'pillar_name', 'weight_pct', and a list of
            its constituent 'kpis'.

    Returns:
        A dictionary containing the comprehensive scoring results. Key fields
        include 'tower_score_exact', a list of 'pillar_scores' with their
        individual results, 'maturity_band_from_exact' containing the
        qualitative assessment, and metadata from the inputs.

    Raises:
        KeyError: If essential keys are missing from `case_input` (e.g., 'case_id',
            'answers') or from the nested structures within `tower_definition`
            (e.g., 'pillars', 'kpis', 'weight_pct').
        ValueError: If a 'value' within the `case_input['answers']` list cannot be
            cast to a float.
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
    target_maturity_default = 4.0
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
    """Executes the case scoring pipeline from command-line arguments.

    This function serves as the primary entry point for the scoring script. It
    parses a path to a case input file via the '--case-input' command-line
    argument. It subsequently loads the case data and dynamically locates and
    loads the corresponding tower definition JSON file using the 'tower_id' key
    from the case data. The scoring is then calculated by invoking the core
    building logic. Finally, the results are serialized to a JSON file named
    'scoring_output.json' within the same directory as the input case file.

    Raises:
        FileNotFoundError: If the specified case input file or the derived tower
            definition file does not exist.
        json.JSONDecodeError: If the case input or tower definition file contains
            malformed JSON.
        KeyError: If the 'tower_id' key is absent from the case input data.
        OSError: If an error occurs while writing the output file.
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
