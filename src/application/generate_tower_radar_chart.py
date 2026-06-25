"""Implements the generation of tower radar chart visualizations for the Assessment Engine pipeline."""

import json
import math
import sys
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a 'utf-8-sig' encoded JSON file from a given path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def safe_float(value) -> Any:
    r"""{'docstring': 'Convert a value to a float, returning None on conversion failure.\n\nThis function attempts to convert the input value into a floating-point\nnumber. It is designed to handle `None`, integers, floats, and string\nrepresentations of numbers. For string inputs, commas are replaced with\nperiods to accommodate different decimal notations, and leading/trailing\nwhitespace is stripped before conversion. If the value is `None` or cannot\nbe parsed (e.g., a non-numeric string), `None` is returned instead of\nraising an exception.\n\nArgs:\n    value (Any): The value to be converted.\n\nReturns:\n    Optional[float]: The converted float, or None if the input is `None`\n    or cannot be converted.'}."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", ".").strip()
    try:
        return float(text)
    except Exception:
        return None


def generate_radar_chart_from_pillars(pillars: list[dict], out_path: Path) -> Path:
    """Generates and saves a polar plot (radar chart) from structured data.

    This function creates a radar chart using matplotlib's polar projection to
    visualize a set of scores corresponding to different labeled categories. The
    chart is configured with a fixed radial axis ranging from 0 to 5, and the
    resulting image is saved to the specified file path.

    Args:
        pillars: A list of dictionaries, where each dictionary represents a
            data point. Each dictionary is expected to contain a 'pillar_label'
            key with a string value for the axis label and a 'score_display'
            key with a value convertible to a float. Scores that cannot be
            converted are treated as 0.0.
        out_path: The `pathlib.Path` object specifying the destination file for
            the generated chart image. Parent directories are created if they
            do not exist.

    Returns:
        The path to the saved chart image file, which is identical to the
        `out_path` argument.

    Raises:
        ValueError: If the `pillars` list is empty or contains no extractable
            labels or valid scores, preventing chart generation.
    """
    labels = [p.get("pillar_label", "") for p in pillars]
    values = [safe_float(p.get("score_display")) for p in pillars]

    if not labels or not any(v is not None for v in values):
        raise ValueError("No hay datos suficientes para generar el radar chart.")

    values = [v if v is not None else 0.0 for v in values]

    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values += values[:1]

    fig = plt.figure(figsize=(8, 6.2))
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(math.pi / 2)  # type: ignore
    ax.set_theta_direction(-1)  # type: ignore

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)

    ax.set_rlabel_position(0)  # type: ignore
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=9)

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.15)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main(argv: list[str] | None = None) -> None:
    """Parses command-line arguments to generate a radar chart from a JSON payload.

    This function serves as the main entry point for the radar chart generation
    command-line utility. It processes command-line arguments to identify a
    source JSON payload file and an optional output image path. It extracts
    pillar score data from the payload, generates the radar chart, and then
    updates the source JSON file in-place to include a path to the new image.

    Args:
        argv: A list of command-line arguments. If `None`, `sys.argv` is used.
            The expected format is `[<script_name>, <template_payload_json>,
            [output_png]]`.

    Raises:
        SystemExit: If an incorrect number of command-line arguments is
            provided, or if the pillar data in the payload is invalid for chart
            generation (e.g., insufficient data points).
        FileNotFoundError: If the input JSON file specified in `argv` does not
            exist.
        json.JSONDecodeError: If the input JSON file contains malformed JSON.
        KeyError: If the JSON payload is missing the `pillar_score_profile` key,
            which is required for both data extraction and updating the payload.
    """
    if len(argv if argv is not None else sys.argv) not in (2, 3):
        raise SystemExit(
            "Uso: python -m scripts.generate_tower_radar_chart <template_payload_json> [output_png]"
        )

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    payload = load_json(payload_path)

    out_path = (
        Path((argv if argv is not None else sys.argv)[2]).resolve()
        if len(argv if argv is not None else sys.argv) == 3
        else payload_path.with_name("pillar_radar_chart.generated.png")
    )

    pillars = payload.get("pillar_score_profile", {}).get("pillars", [])
    try:
        generate_radar_chart_from_pillars(pillars, out_path)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    payload["pillar_score_profile"]["radar_chart"] = str(out_path)
    payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Radar chart generado en:", out_path)
    print("Payload actualizado en:", payload_path)


if __name__ == "__main__":
    main()
