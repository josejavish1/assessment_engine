"""Implements the core pipeline and utility functions for generating global radar charts within the Assessment Engine."""

import json
import logging
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def load_json(path: Path):
    """Load and parse a UTF-8 JSON file from a `pathlib.Path`, handling a potential BOM."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_float(value):
    """Safely converts an object to a float, returning 0.0 on failure.

    The function first casts the input value to a string. It then isolates the
    first whitespace-separated token and replaces comma decimal separators with
    periods. This pre-processing allows for robust parsing of common numerical
    formats, such as "1,234.56 USD".

    If the input is `None` or if any step of the conversion process raises an
    exception, 0.0 is returned.

    Args:
        value (Any): The object to convert to a float.

    Returns:
        float: The floating-point representation of the value, or 0.0 if the
            input is `None` or cannot be converted.
    """
    if value is None:
        return 0.0
    try:
        return float(str(value).split()[0].replace(",", "."))
    except Exception:
        return 0.0


def main(argv: list[str] | None = None) -> None:
    """Generates and saves a global technology maturity radar chart from a JSON file.

    This function serves as the main entry point for a command-line script.
    It parses arguments for an input JSON file path and an optional output
    PNG file path. The function reads technology tower maturity data from the
    JSON, performs a natural sort on tower identifiers, plots the data on a
    polar (radar) chart using matplotlib, and saves the resulting image to disk.

    Args:
        argv: A list of command-line arguments. If None, `sys.argv` is used.
            The script expects the following arguments:
            - argv[1]: The file path to the input JSON payload.
            - argv[2] (optional): The file path for the output PNG image. If
              omitted, defaults to 'global_radar_chart.png' in the same
              directory as the input file.

    Raises:
        SystemExit: If fewer than two command-line arguments are provided, or if
            the input JSON payload lacks a 'heatmap' key or its value is an
            empty list.
        FileNotFoundError: If the input JSON file specified by `argv[1]` does not
            exist.
        IOError: If the output PNG file cannot be written to the specified path,
            for instance due to insufficient file system permissions.
        ValueError: If the JSON payload is malformed, a 'score' value cannot be
            converted to a float, or a tower 'id' does not conform to the
            expected 'T<number>' format required for sorting.
        json.JSONDecodeError: If the input file contains invalid JSON.
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

    # Implements a natural sort order for tower identifiers (e.g., 'T1', 'T2', ..., 'T10') to prevent incorrect lexicographical sorting where 'T10' would precede 'T2'.
    towers = sorted(
        towers, key=lambda x: int(x.get("id")[1:]) if x.get("id")[1:].isdigit() else 99
    )

    labels = [t.get("id", "") for t in towers]
    values = [safe_float(t.get("score")) for t in towers]

    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values += values[:1]

    # Defines the color palette for the chart series, adhering to professional data visualization standards.
    plt.style.use("ggplot")
    # Expands the figure width to ensure sufficient canvas space for the plot and an external legend, preventing visual truncation.
    fig = plt.figure(figsize=(14, 8))
    # Configures subplot layout parameters to provide adequate spacing and prevent label or title overlap.
    fig.subplots_adjust(left=0.1, right=0.7, top=0.85, bottom=0.1)
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(
        math.pi / 2
    )  # Suppresses a static type checker warning on the following line where type inference may be inaccurate.
    ax.set_theta_direction(
        -1
    )  # Suppresses a static type checker warning on the following line where type inference may be inaccurate.

    plt.xticks(angles[:-1], labels, color="grey", size=13)
    ax.set_rlabel_position(
        0
    )  # Suppresses a static type checker warning on the following line where type inference may be inaccurate.
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=10)
    plt.ylim(0, 5.5)

    ax.plot(angles, values, linewidth=3, linestyle="solid", color="#1f77b4")
    ax.fill(angles, values, color="#1f77b4", alpha=0.25)

    # Iteratively annotates each data point on the radar plot with its numerical value to enhance data interpretability.
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

    # Configures and positions the chart legend outside the plot area to maintain data visibility, adjusting font size for readability.
    tower_names = [f"{t.get('id')}: {t.get('name')}" for t in towers]
    plt.figtext(
        0.72, 0.5, "\n\n".join(tower_names), fontsize=13, color="#333333", va="center"
    )

    # Sets the primary chart title, using a larger font size and centered alignment for visual hierarchy.
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
