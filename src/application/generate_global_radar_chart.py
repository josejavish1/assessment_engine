"""Encapsulates the core logic and utility functions for generating global radar charts as a component of the Assessment Engine pipeline."""

import json
import logging
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a UTF-8 encoded JSON file from a given path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def safe_float(value) -> Any:
    """Safely convert an arbitrary value to a float.

    Converts a value to a float with robust error handling. The input is first
    cast to a string. The logic then isolates the first whitespace-separated
    token from this string representation and replaces any commas with periods
    to handle different decimal formats.

    If the conversion to a float fails for any reason (e.g., the token is
    non-numeric) or if the initial input value is None, the function returns 0.0
    instead of raising an exception.

    Args:
        value (Any): The input value to coerce into a float.

    Returns:
        float: The value as a float, or 0.0 if the input is None or if
            coercion fails.
    """
    if value is None:
        return 0.0
    try:
        return float(str(value).split()[0].replace(",", "."))
    except Exception:
        return 0.0


def main(argv: list[str] | None = None) -> None:
    """Generate and save a global technology maturity radar chart.

    This function serves as the main entry point for a command-line script that
    visualizes technology maturity data. It reads a specified JSON payload file,
    processes scores for each defined 'tower', and renders them as a polar plot
    (radar chart) using Matplotlib. The resulting chart is saved as a PNG image.

    The input JSON is expected to contain a 'heatmap' key, which maps to a
    list of tower objects. Each tower object must have an 'id' (e.g., 'T1') and a
    'score'. Towers are sorted numerically based on their ID to ensure a
    consistent and logical axis order in the chart.

    Args:
        argv: A list of command-line arguments. If `None`, `sys.argv` is used.
            The list is expected to contain:
            1. The path to the input JSON payload file.
            2. (Optional) The path for the output PNG file. If omitted, the
               output is saved as 'global_radar_chart.png' in the same
               directory as the input file.

    Raises:
        SystemExit: If the number of command-line arguments is insufficient or
            if the input JSON payload does not contain any tower data under the
            'heatmap' key.
        FileNotFoundError: If the path to the input JSON file does not exist.
        json.JSONDecodeError: If the input file is not a valid JSON document.
        ValueError: If a tower 'id' cannot be parsed for numerical sorting
            (e.g., 'T' followed by non-digits) or if a 'score' cannot be
            converted to a float.
    """
    if len(argv if argv is not None else sys.argv) < 2:
        logger.info(
            "Uso: python scripts/generate_global_radar_chart.py <global_payload_json> [output_png]"
        )
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    payload = load_json(payload_path)

    out_path = (
        Path((argv if argv is not None else sys.argv)[2]).resolve()
        if len(argv if argv is not None else sys.argv) > 2
        else payload_path.with_name("global_radar_chart.png")
    )

    towers = payload.get("heatmap", [])
    if not towers:
        logger.warning("No hay datos de torres en el payload.")
        sys.exit(1)

    # Enforces a strict numerical sort on tower labels (e.g., T1, T2, ..., T10) to guarantee a logical and consistent axis order, preventing lexicographical sorting artifacts such as 'T10' preceding 'T2'.
    towers = sorted(
        towers, key=lambda x: int(x.get("id")[1:]) if x.get("id")[1:].isdigit() else 99
    )

    labels = [t.get("id", "") for t in towers]
    values = [safe_float(t.get("score")) for t in towers]

    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values += values[:1]

    # Sets a professional color scheme (Blue/Gray) to maintain visual consistency with standard consulting presentation styles.
    plt.style.use("ggplot")
    # Expands the figure width to ensure both the chart and its legend render completely within the page boundaries without element collision or truncation.
    fig = plt.figure(figsize=(14, 8))
    # Enforces a tight layout to optimize padding and spacing between plot elements, preventing overlap and improving visual clarity.
    fig.subplots_adjust(left=0.1, right=0.7, top=0.85, bottom=0.1)
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(math.pi / 2)  # Type checking is ignored for this line due to a known limitation or incompatibility with the current type hinting system.
    ax.set_theta_direction(-1)  # Type checking is ignored for this line due to a known limitation or incompatibility with the current type hinting system.

    plt.xticks(angles[:-1], labels, color="grey", size=13)
    ax.set_rlabel_position(0)  # Type checking is ignored for this line due to a known limitation or incompatibility with the current type hinting system.
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=10)
    plt.ylim(0, 5.5)

    ax.plot(angles, values, linewidth=3, linestyle="solid", color="#1f77b4")
    ax.fill(angles, values, color="#1f77b4", alpha=0.25)

    # Annotates each data point on the plot with its numerical score to facilitate precise, at-a-glance value retrieval.
    for angle, value in zip(angles[:-1], values[:-1]):
        ha = "center"
        va = "center"
        if 0 < angle < math.pi:
            ha = "left"
        elif math.pi < angle < 2 * math.pi:
            ha = "right"

        if angle < math.pi / 2 or angle > 3 * math.pi / 2:
            va = "bottom"
        elif math.pi / 2 < angle < 3 * math.pi / 2:
            va = "top"

        ax.text(
            angle,
            value + 0.4,
            f"{value:.1f}",
            color="#1f77b4",
            size=13,
            horizontalalignment=ha,
            verticalalignment=va,
            weight="bold",
        )

    # Positions the legend, containing tower names, to the right of the chart and sets an optimized font size to ensure maximum readability without obscuring data points.
    tower_names = [f"{t.get('id')}: {t.get('name')}" for t in towers]
    plt.figtext(
        0.72, 0.5, "\n\n".join(tower_names), fontsize=13, color="#333333", va="center"
    )

    # Configures the primary chart title with a 24pt font size and center alignment to establish a clear visual hierarchy.
    plt.suptitle(
        "Mapa de Madurez Tecnológica Global",
        size=24,
        color="#1f77b4",
        x=0.5,
        y=0.96,
        horizontalalignment="center",
    )

    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Gráfico radar global generado en: {out_path}")


if __name__ == "__main__":
    main()
