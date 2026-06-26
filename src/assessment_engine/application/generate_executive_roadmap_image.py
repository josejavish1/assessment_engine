"""Implements the core logic and utilities for the Assessment Engine pipeline."""

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file from a given path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def main(argv: list[str] | None = None) -> None:
    """Generates and saves a Gantt chart roadmap image from a JSON payload file.

    This function serves as the main entry point for a command-line script. It
    parses command-line arguments to obtain a path to an input JSON file and an
    optional output path for the generated PNG image.

    The function expects the JSON payload to contain an `execution_roadmap` key,
    which in turn contains a `horizons` key. The `horizons` object is
    structured with the following keys, each holding a list of initiative
    dictionaries: `quick_wins_0_3_months`, `year_1_3_12_months`,
    `year_2_12_24_months`, and `year_3_24_36_months`. Each initiative dictionary
    should contain `title`, `program`, `start_month`, and `duration_months`.

    The collected initiatives are plotted onto a 36-month Gantt chart using
    Matplotlib and saved to the specified output file. The process will
    terminate via `sys.exit(1)` if the input file path is not provided. It
    will terminate via `sys.exit(0)` if the JSON payload lacks valid roadmap
    data, preventing image generation in cases of empty input.

    Args:
        argv: A list of command-line arguments. If `None`, `sys.argv` is used.
            The first argument must be the path to the JSON payload file. The
            second, optional argument is the path for the output PNG file. If
            the output path is omitted, it defaults to
            `global_roadmap_timeline.png` in the same directory as the input file.
    """
    if len(argv if argv is not None else sys.argv) < 2:
        logger.info(
            "Uso: python scripts/generate_executive_roadmap_image.py <global_payload_json> [output_png]"
        )
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    payload = load_json(payload_path)

    out_path = (
        Path((argv if argv is not None else sys.argv)[2]).resolve()
        if len(argv if argv is not None else sys.argv) > 2
        else payload_path.with_name("global_roadmap_timeline.png")
    )

    roadmap_data = payload.get("execution_roadmap", {})
    horizons = roadmap_data.get("horizons", {})
    if not horizons:
        logger.warning("No hay roadmap de ejecución en el payload.")
        sys.exit(0)

    initiatives = []

    order = [
        "quick_wins_0_3_months",
        "year_1_3_12_months",
        "year_2_12_24_months",
        "year_3_24_36_months",
    ]
    labels = ["Quick Wins (0-3m)", "Año 1 (4-12m)", "Año 2 (13-24m)", "Año 3 (25-36m)"]
    colors = ["#e06666", "#f6b26b", "#ffd966", "#93c47d"]

    for idx, horizon_key in enumerate(order):
        for item in horizons.get(horizon_key, []):
            initiatives.append(
                {
                    "group_label": labels[idx],
                    "color": colors[idx],
                    "title": item.get("title", "Desconocido"),
                    "program": item.get("program", ""),
                    "start": max(1, item.get("start_month", 1)),
                    "duration": max(1, item.get("duration_months", 3)),
                }
            )

    if not initiatives:
        logger.warning("No hay iniciativas válidas.")
        sys.exit(0)

    # Inverts the Y-axis to adhere to the conventional top-to-bottom display order for initiatives. This correction is necessary because Matplotlib's default plotting behavior places the first data series at the bottom of the axis.
    initiatives.reverse()

    fig, ax = plt.subplots(figsize=(14, max(6, len(initiatives) * 0.4)))

    # Renders the horizontal bars for the Gantt chart; each bar's length and position correspond to an initiative's duration and temporal placement.
    for idx, init in enumerate(initiatives):
        y_pos = idx
        ax.barh(
            y_pos,
            init["duration"],
            left=init["start"],
            color=init["color"],
            alpha=0.9,
            height=0.6,
        )

        title = f"[{init['program']}] {init['title']}"
        if len(title) > 65:
            title = title[:62] + "..."
        ax.text(
            init["start"] + 0.5,
            y_pos,
            title,
            va="center",
            ha="left",
            fontsize=9,
            color="black",
            fontweight="medium",
        )

    ax.set_xlim(0, 36)
    ax.set_ylim(-1, len(initiatives))
    ax.set_yticks([])

    # Sets the X-axis to a monthly timeline scale. Major ticks are placed at 12-month intervals to denote calendar years, improving long-term roadmap readability.
    ax.set_xticks(range(0, 37, 3))
    ax.set_xticklabels([f"M{i}" for i in range(0, 37, 3)], fontsize=10, color="grey")
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    # Overlays a vertical grid with lines at 12-month intervals to visually separate calendar years, thereby enhancing timeline clarity.
    for x in [3, 12, 24, 36]:
        ax.axvline(x, color="grey", linestyle="--", alpha=0.5)

    ax.text(
        1.5,
        -0.8,
        "Quick Wins",
        color="#e06666",
        fontsize=11,
        fontweight="bold",
        ha="center",
    )
    ax.text(
        7.5, -0.8, "Año 1", color="#f6b26b", fontsize=11, fontweight="bold", ha="center"
    )
    ax.text(
        18, -0.8, "Año 2", color="#ffd966", fontsize=11, fontweight="bold", ha="center"
    )
    ax.text(
        30, -0.8, "Año 3", color="#93c47d", fontsize=11, fontweight="bold", ha="center"
    )

    # Removes the chart's bounding box (spines) to achieve a less cluttered and more modern visualization.
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    plt.title(
        "Plan de Implementación y Horizontes Temporales (36 Meses)",
        size=16,
        color="#004b87",
        pad=30,
        fontweight="bold",
    )

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    logger.info(f"Roadmap visual generado en: {out_path}")


if __name__ == "__main__":
    main()
