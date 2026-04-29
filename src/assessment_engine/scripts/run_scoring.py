"""
Módulo run_scoring.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import argparse
import json
from pathlib import Path

from assessment_engine.scripts.lib.runtime_paths import ROOT


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def round_display(value: float) -> float:
    return round(value, 1)


def resolve_band(score: float, tower_definition: dict) -> dict:
    normalized_score = round(score, 4)
    for band in tower_definition.get("score_bands", []):
        if band["min"] <= normalized_score <= band["max"]:
            return band
    return tower_definition.get("score_bands", [])[-1]


def build_scoring(case_input: dict, tower_definition: dict) -> dict:
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
