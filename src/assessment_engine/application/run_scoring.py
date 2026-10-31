"""Implements the core processing pipeline and foundational utilities for the Assessment Engine."""

import argparse
import json
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from assessment_engine.domain.maturity_band import resolve_maturity_band
from assessment_engine.infrastructure.runtime_paths import ROOT

DEFAULT_TARGET_MATURITY: float = 4.0
DEFAULT_KPI_WEIGHT: float = 1.0
DEFAULT_CRITICAL_FLOOR_CEILING: float = 2.0
SCORE_PRECISION_DECIMALS: int = 4
DISPLAY_PRECISION_DECIMALS: int = 1
PERCENTAGE_DIVISOR: float = 100.0
ZERO_SCORE_THRESHOLD: float = 0.0

DEFAULT_OPERATIONAL_READINGS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("init",),
        "Domain operational practices are ad-hoc, unstable, or dependent on individual heroics.",
    ),
    (
        ("basic", "repeat"),
        "Domain operational capabilities are applied inconsistently across silos without enterprise standard.",
    ),
    (
        ("standard", "defin"),
        "Platform processes and controls are formalized, documented, and consistently implemented.",
    ),
    (
        ("optim", "manag"),
        "Domain operations and capabilities are industrialized, predictively governed, and substantiated by metrics.",
    ),
    (
        ("advanc",),
        "The technical domain operates in continuous optimization and evolution, powered by intelligent automation.",
    ),
)


class AnswerDTO(BaseModel):
    """Strict DTO representing an individual KPI answer in a case input."""

    model_config = ConfigDict(extra="allow")

    kpi_id: str
    value: float


class CaseInputDTO(BaseModel):
    """Strict DTO representing the boundary input for an assessment case."""

    model_config = ConfigDict(extra="allow")

    case_id: str
    tower_id: str
    tower_name: str
    target_maturity_default: float = DEFAULT_TARGET_MATURITY
    answers: list[AnswerDTO] = Field(default_factory=list)


class KPIDefinitionDTO(BaseModel):
    """Strict DTO representing a KPI configuration within a pillar."""

    model_config = ConfigDict(extra="allow")

    kpi_id: str
    weight: float = DEFAULT_KPI_WEIGHT
    is_critical: bool = False
    critical: bool = False
    regulatory_critical: bool = False

    @property
    def is_regulatory_critical(self) -> bool:
        """Return True if any critical regulatory flag is enabled on the KPI."""
        return bool(self.is_critical or self.critical or self.regulatory_critical)


class PillarDefinitionDTO(BaseModel):
    """Strict DTO representing a pillar configuration within a tower."""

    model_config = ConfigDict(extra="allow")

    pillar_id: str
    pillar_name: str
    weight_pct: float
    critical_floor_ceiling: float | None = None
    kpis: list[KPIDefinitionDTO] = Field(default_factory=list)


class WorkingRulesDTO(BaseModel):
    """Strict DTO representing scoring aggregation working rules."""

    model_config = ConfigDict(extra="allow")

    score_indicator: str = "average"
    score_pillar: str = "weighted_average"
    score_tower: str = "weighted_average"
    critical_kpi_floor_ceiling: float = DEFAULT_CRITICAL_FLOOR_CEILING


class MaturityScaleItemDTO(BaseModel):
    """Strict DTO representing a single level in the maturity scale."""

    model_config = ConfigDict(extra="allow")

    label: str
    operational_reading: str = ""


class TowerDefinitionDTO(BaseModel):
    """Strict DTO representing the complete tower configuration definition."""

    model_config = ConfigDict(extra="allow")

    pillars: list[PillarDefinitionDTO] = Field(default_factory=list)
    working_rules: WorkingRulesDTO = Field(default_factory=WorkingRulesDTO)
    maturity_scale: list[MaturityScaleItemDTO] = Field(default_factory=list)
    score_bands: list[dict[str, Any]] = Field(default_factory=list)
    critical_kpi_floor_ceiling: float | None = None

    def resolve_floor_ceiling(self, pillar: PillarDefinitionDTO) -> float:
        """Determine the effective minimum floor gate ceiling for a given pillar."""
        if pillar.critical_floor_ceiling is not None:
            return float(pillar.critical_floor_ceiling)
        if self.critical_kpi_floor_ceiling is not None:
            return float(self.critical_kpi_floor_ceiling)
        return float(self.working_rules.critical_kpi_floor_ceiling)


def _validate_case_input(case_input: CaseInputDTO | dict[str, Any]) -> CaseInputDTO:
    """Validate and coerce raw dictionary or DTO into a strict CaseInputDTO."""
    if isinstance(case_input, CaseInputDTO):
        return case_input
    if not isinstance(case_input, dict):
        raise TypeError("case_input must be a dict or CaseInputDTO instance.")
    try:
        return CaseInputDTO.model_validate(case_input)
    except ValidationError as exc:
        for err in exc.errors():
            if err.get("type") == "missing":
                missing_loc = err.get("loc", ("unknown",))[-1]
                raise KeyError(f"Missing required key in case_input: {missing_loc}") from exc
        raise ValueError(f"Invalid value in case_input: {exc}") from exc


def _validate_tower_definition(
    tower_definition: TowerDefinitionDTO | dict[str, Any],
) -> TowerDefinitionDTO:
    """Validate and coerce raw dictionary or DTO into a strict TowerDefinitionDTO."""
    if isinstance(tower_definition, TowerDefinitionDTO):
        return tower_definition
    if not isinstance(tower_definition, dict):
        raise TypeError("tower_definition must be a dict or TowerDefinitionDTO instance.")
    try:
        return TowerDefinitionDTO.model_validate(tower_definition)
    except ValidationError as exc:
        for err in exc.errors():
            if err.get("type") == "missing":
                missing_loc = err.get("loc", ("unknown",))[-1]
                raise KeyError(f"Missing required key in tower_definition: {missing_loc}") from exc
        raise ValueError(f"Invalid value in tower_definition: {exc}") from exc


def load_json(path: Path) -> dict[str, Any]:
    """Load and decode a JSON file from a specified path using 'utf-8-sig' encoding."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def average(values: list[float]) -> float:
    """Calculate the arithmetic mean of a list of floats, returning 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0


def weighted_average(values: list[float], weights: list[float] | None = None) -> float:
    """Calculate the weighted linear mean sum(v * w) / sum(w), defaulting weights to 1.0."""
    if not values:
        return 0.0
    effective_weights = (
        [DEFAULT_KPI_WEIGHT] * len(values) if weights is None else weights
    )
    if len(values) != len(effective_weights):
        raise ValueError("Length of values and weights must match for weighted_average.")
    total_weight = sum(effective_weights)
    if total_weight <= ZERO_SCORE_THRESHOLD:
        return 0.0
    return sum(v * w for v, w in zip(values, effective_weights)) / total_weight


def round_display(value: float) -> float:
    """Round a floating-point number to the configured display precision."""
    return round(value, DISPLAY_PRECISION_DECIMALS)


def resolve_band(
    score: float, tower_definition: TowerDefinitionDTO | dict[str, Any]
) -> dict[str, Any]:
    """Find the corresponding score band for a given numerical score.

    This function extracts the `score_bands` list from a `tower_definition`
    dictionary or DTO and delegates to `resolve_maturity_band` to find the
    appropriate band for the given score. A fixed score precision of 4 decimal
    places is used for the underlying comparison.

    Args:
        score: The numerical score to be categorized into a band.
        tower_definition: The configuration dictionary or DTO for a tower. This must
            contain a "score_bands" attribute or key whose value is a list of band
            definition dictionaries.

    Returns:
        A dictionary representing the matched score band.

    Raises:
        ValueError: If the score does not fall within any of the defined bands.
        TypeError: If the value associated with the 'score_bands' key is not a
            list of dictionaries.
    """
    if isinstance(tower_definition, TowerDefinitionDTO):
        score_bands = tower_definition.score_bands
    elif isinstance(tower_definition, dict):
        score_bands = tower_definition.get("score_bands", [])
    else:
        raise TypeError("tower_definition must be a dict or TowerDefinitionDTO.")

    return dict(
        resolve_maturity_band(
            score,
            score_bands,
            score_precision=SCORE_PRECISION_DECIMALS,
        )
    )


def _fallback_reading_for_label(normalized_label: str) -> str:
    """Return the standard English operational reading matching a normalized band label."""
    for keywords, reading in DEFAULT_OPERATIONAL_READINGS:
        if any(keyword in normalized_label for keyword in keywords):
            return reading
    return ""


def _resolve_operational_reading(
    band_label: str, maturity_scale: list[MaturityScaleItemDTO]
) -> str:
    """Resolve the English operational reading for a given maturity band label."""
    normalized_band = band_label.lower()
    for level in maturity_scale:
        if level.label.lower() in normalized_band:
            configured_reading = level.operational_reading.strip()
            if configured_reading:
                return configured_reading
            fallback = _fallback_reading_for_label(normalized_band)
            return fallback if fallback else configured_reading

    return _fallback_reading_for_label(normalized_band)


def build_scoring(
    case_input: CaseInputDTO | dict[str, Any],
    tower_definition: TowerDefinitionDTO | dict[str, Any],
) -> dict[str, Any]:
    """Calculates pillar and tower scores from user answers and a tower definition.

    Aggregates scores from individual key performance indicator (KPI) answers to
    compute scores for pillars and a final, weighted tower score. The process
    involves three stages:
    1.  KPI Score Calculation: Averages the scores for all answers corresponding
        to a single KPI.
    2.  Pillar Score Calculation: Computes a weighted linear average of the
        calculated scores of all KPIs that constitute a single pillar
        (`sum(v * w) / sum(w)`), and applies a Minimum Floor Gate if any
        critical regulatory KPI evaluates to 0.0.
    3.  Tower Score Calculation: Computes a weighted average of all pillar scores
        to determine the final tower score.

    The final score is also used to resolve a qualitative maturity band based
    on predefined thresholds in the tower definition.

    Args:
        case_input: A CaseInputDTO or dictionary containing case data and user
            responses. Expected structure includes 'case_id', 'tower_id',
            'tower_name', 'target_maturity_default', and an 'answers' list where
            each element has 'kpi_id' and a numeric 'value'.
        tower_definition: A TowerDefinitionDTO or dictionary defining the tower's
            structure, weighting, and scoring rules. Expected structure includes a
            'pillars' list (each with 'pillar_id', 'weight_pct', and a list of
            'kpis'), 'working_rules', and a 'maturity_scale'.

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
    case_dto = _validate_case_input(case_input)
    tower_dto = _validate_tower_definition(tower_definition)

    answers_by_kpi: dict[str, list[float]] = {}
    for answer in case_dto.answers:
        answers_by_kpi.setdefault(answer.kpi_id, []).append(float(answer.value))

    pillar_scores: list[dict[str, Any]] = []
    weights_pct: dict[str, float | int] = {}

    for pillar in tower_dto.pillars:
        kpi_scores: list[float] = []
        kpi_weights: list[float] = []
        critical_zero_triggered = False

        for kpi in pillar.kpis:
            scores = answers_by_kpi.get(kpi.kpi_id, [])
            if scores:
                kpi_mean_score = average(scores)
                kpi_scores.append(kpi_mean_score)
                kpi_weights.append(float(kpi.weight))
                if kpi.is_regulatory_critical and kpi_mean_score <= ZERO_SCORE_THRESHOLD:
                    critical_zero_triggered = True

        pillar_score = weighted_average(kpi_scores, kpi_weights)
        if critical_zero_triggered:
            ceiling = tower_dto.resolve_floor_ceiling(pillar)
            pillar_score = min(pillar_score, ceiling)

        weight_val: float | int = (
            int(pillar.weight_pct)
            if pillar.weight_pct.is_integer()
            else pillar.weight_pct
        )
        pillar_scores.append(
            {
                "pillar_id": pillar.pillar_id,
                "pillar_name": pillar.pillar_name,
                "weight_pct": weight_val,
                "score_exact": round(pillar_score, SCORE_PRECISION_DECIMALS),
                "score_display_1d": round_display(pillar_score),
            }
        )
        weights_pct[pillar.pillar_id] = weight_val

    tower_score = sum(
        float(item["score_exact"]) * (float(item["weight_pct"]) / PERCENTAGE_DIVISOR)
        for item in pillar_scores
    )
    target_maturity_default = float(case_dto.target_maturity_default)
    band = resolve_band(tower_score, tower_dto)

    return {
        "case_id": case_dto.case_id,
        "tower_id": case_dto.tower_id,
        "tower_name": case_dto.tower_name,
        "aggregation_method": {
            "indicator": tower_dto.working_rules.score_indicator,
            "pillar": tower_dto.working_rules.score_pillar,
            "tower": tower_dto.working_rules.score_tower,
        },
        "weights_pct": weights_pct,
        "pillar_scores": pillar_scores,
        "tower_score_exact": round(tower_score, SCORE_PRECISION_DECIMALS),
        "tower_score_display_1d": round_display(tower_score),
        "maturity_band_from_exact": {
            "label": band["label"],
            "reading": _resolve_operational_reading(
                band["label"], tower_dto.maturity_scale
            ),
        },
        "proposed_reporting_note": (
            "Reported score is rounded to one decimal place, while qualitative band alignment "
            "is determined from exact internal score to prevent artificial rounding jumps."
        ),
        "target_maturity_default": target_maturity_default,
        "gap_to_target_exact": round(
            target_maturity_default - tower_score, SCORE_PRECISION_DECIMALS
        ),
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
    case_dto = _validate_case_input(case_input)
    tower_definition = load_json(
        ROOT
        / "engine_config"
        / "towers"
        / case_dto.tower_id
        / f"tower_definition_{case_dto.tower_id}.json"
    )
    tower_dto = _validate_tower_definition(tower_definition)
    scoring = build_scoring(case_dto, tower_dto)
    output_path = case_input_path.with_name("scoring_output.json")
    output_path.write_text(
        json.dumps(scoring, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Scoring generated at: {output_path}")
    print(f"tower_score_exact: {scoring['tower_score_exact']}")


if __name__ == "__main__":
    main()
