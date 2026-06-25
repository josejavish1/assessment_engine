"""Provides functionality for generating tower-based radar charts to visualize assessment results."""

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt


def load_json(path: Path):
    """Parse a UTF-8 encoded JSON file from a given path."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_float(value):
    """Safely convert a value to a float.

    Converts a value to a float, suppressing exceptions. This function handles
    `None`, numeric types (`int`, `float`), and strings. String inputs are
    normalized by replacing comma decimal separators with periods prior to
    conversion.

    Args:
        value (Any): The input value to convert.

    Returns:
        Optional[float]: The converted float, or `None` if the input is `None` or
            if the conversion fails.
    """
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
    r"""{'docstring': "Generates and saves a polar plot (radar chart) from pillar score data.\n\n    This function visualizes a list of pillar scores as a radar chart using\n    matplotlib. It plots each pillar's label and score on a polar axis. The\n    radial axis is fixed on a scale of 0 to 5. Scores that are missing or\n    cannot be converted to a float are treated as 0.0. The resulting chart is\n    saved as an image file to the specified path.\n\n    Args:\n        pillars: A list of dictionaries, each representing a pillar. Each\n            dictionary should contain a 'pillar_label' key with a string value\n            for the axis label and a 'score_display' key with a value that can\n            be converted to a float.\n        out_path: The file system path where the generated radar chart image\n            will be saved. Parent directories are created if they do not exist.\n\n    Returns:\n        The path to the saved chart image file, identical to the `out_path`\n        argument.\n\n    Raises:\n        ValueError: If the `pillars` list is empty or if none of the provided\n            dictionaries contain a 'score_display' value that can be\n            converted to a float."}."""
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
    """Generate a radar chart and update the source JSON payload.

    This function serves as the main entry point for a command-line script.
    It performs the following sequence of operations:
    1. Parses command-line arguments for an input JSON file and an optional
       output PNG file path.
    2. Loads the JSON payload from the specified input file.
    3. Extracts pillar score data from the `pillar_score_profile.pillars` key.
    4. Invokes the chart generation logic with the extracted data.
    5. Updates the in-memory JSON payload to include a `radar_chart` key
       referencing the path of the generated image.
    6. Overwrites the original input file with the updated JSON payload.

    If an output path is not provided, the image is saved as
    'pillar_radar_chart.generated.png' in the same directory as the input file.

    Args:
        argv: A list of command-line arguments. If None, `sys.argv` is
            used. The first argument (`argv[1]`) must be the path to the
            input JSON file. The second argument (`argv[2]`) is an optional
            path for the output PNG image.

    Raises:
        SystemExit: If the number of command-line arguments is incorrect, or if
            the pillar data within the payload is invalid and causes a
            `ValueError` during chart generation.
        FileNotFoundError: If the input JSON file specified by `argv[1]` does
            not exist.
        json.JSONDecodeError: If the input file is not a valid JSON document.
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
