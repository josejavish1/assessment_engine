"""Encapsulates the core logic and utility functions for generating global radar charts as a component of the Assessment Engine pipeline."""

import json
import logging
import math
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


from typing import Any, cast

from assessment_engine.domain.actuarial_scale_calibrator import (
    safe_float as _domain_safe_float,
)


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a UTF-8 encoded JSON file from a given path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def safe_float(value: Any, locale: str | None = None) -> float:
    """Safely convert an arbitrary value to a finite float using the domain calibrator."""
    return _domain_safe_float(value, locale=locale, allow_zero=True) or 0.0


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
            "Usage: python -m assessment_engine.application.generate_global_radar_chart <global_payload_json> [output_png]"
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
        logger.warning("Zero tower data points in global payload.")
        sys.exit(1)

    # Enforces a strict numerical sort on tower labels with secondary string tie-breaking
    def _sort_key(node: dict[str, Any]) -> tuple[int, str]:
        t_code = str(node.get("id") or node.get("tower_code") or "")
        match = re.search(r"\d+", t_code)
        return (int(match.group(0)) if match else 99, t_code)

    towers = sorted(towers, key=_sort_key)

    from assessment_engine.infrastructure.localization import format_number, t
    from assessment_engine.infrastructure.text_utils import CANONICAL_TOWER_NAMES

    doc_lang = str(payload.get("meta", {}).get("language") or "en").lower()

    labels = [str(t_node.get("id") or t_node.get("tower_code") or "") for t_node in towers]
    values = [safe_float(t_node.get("score"), locale=doc_lang) for t_node in towers]

    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values += values[:1]
    raw_brand = str(payload.get("meta", {}).get("brand_color") or payload.get("meta", {}).get("primary_color_hex") or "0072BC").lstrip("#")
    if len(raw_brand) == 3 and all(c in "0123456789abcdefABCDEF" for c in raw_brand):
        raw_brand = "".join(c * 2 for c in raw_brand)
    elif len(raw_brand) != 6 or not all(c in "0123456789abcdefABCDEF" for c in raw_brand):
        raw_brand = "0072BC"
    brand_hex = f"#{raw_brand}"

    # Expands the figure width to ensure both the chart and its legend render completely within page boundaries
    fig = Figure(figsize=(14, 8), facecolor="white")
    fig.subplots_adjust(left=0.1, right=0.7, top=0.85, bottom=0.1)
    ax = fig.add_subplot(111, polar=True, facecolor="#F8FAFC")
    ax.grid(color="#E2E8F0", linestyle="-", linewidth=1.0)
    ax.spines["polar"].set_color("#CBD5E1")

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color="#2D3748", size=13, weight="bold")
    ax.set_rlabel_position(0)
    y_tick_labels = [format_number(float(i), locale=doc_lang, decimals=1) for i in [1, 2, 3, 4, 5]]
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(y_tick_labels, color="#718096", size=10)
    ax.set_ylim(0, 5.5)

    # Pure forensic AS-IS Current state polygon (solid corporate blue)
    ax.plot(
        angles,
        values,
        linewidth=3.0,
        linestyle="solid",
        color=brand_hex,
        marker="o",
        markersize=7,
    )
    ax.fill(angles, values, color=brand_hex, alpha=0.25)

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

        text_val = format_number(value, locale=doc_lang, decimals=2)
        ax.text(
            angle,
            value + 0.4,
            text_val,
            color=brand_hex,
            size=13,
            horizontalalignment=ha,
            verticalalignment=va,
            weight="bold",
        )

    # Positions the legend, containing tower names, to the right of the chart
    tower_names = []
    for t_item in towers:
        t_id = str(t_item.get("id") or t_item.get("tower_code") or "")
        localized_name = t(f"tomo_tower_{t_id.lower()}_clean", locale=doc_lang)
        if not localized_name or localized_name.startswith("tomo_tower_"):
            num, dom = CANONICAL_TOWER_NAMES.get(t_id, ("", t_item.get("name", "")))
            localized_name = dom.replace("_", " ") if dom else t_item.get("name", "")
        tower_names.append(f"{t_id}: {localized_name}")

    n_towers = len(towers)
    legend_sep = "\n" if n_towers > 10 else "\n\n"
    legend_fontsize = max(9, min(13, int(130 / max(1, n_towers))))

    fig.text(
        0.72, 0.5, legend_sep.join(tower_names), fontsize=legend_fontsize, color="#333333", va="center"
    )

    chart_title = t("global_radar_chart_title", locale=doc_lang)
    fig.suptitle(
        chart_title,
        size=24,
        color=brand_hex,
        x=0.5,
        y=0.96,
        horizontalalignment="center",
    )

    fig.savefig(out_path, dpi=200, bbox_inches="tight")

    logger.info("Global radar chart generated at: %s", out_path)


if __name__ == "__main__":
    main()
