"""Encapsulates the core logic and utility functions for generating global radar charts as a component of the Assessment Engine pipeline."""

import json
import logging
import math
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Final, cast

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure

from assessment_engine.domain.actuarial_scale_calibrator import (
    safe_float as _domain_safe_float,
)

logger = logging.getLogger(__name__)

DEFAULT_BRAND_COLOR_HEX: Final[str] = "0072BC"
RADAR_FIG_WIDTH_IN: Final[float] = 14.0
RADAR_FIG_HEIGHT_IN: Final[float] = 8.0
RADAR_DPI: Final[int] = 200
RADAR_YLIM_MAX: Final[float] = 5.6
RADAR_LABEL_RADIAL_OFFSET: Final[float] = 0.35
RADAR_LABEL_MAX_RADIUS: Final[float] = 5.25
FALLBACK_SORT_RANK: Final[int] = 99
LEGEND_MIN_FONT_SIZE: Final[int] = 9
LEGEND_MAX_FONT_SIZE: Final[int] = 13
LEGEND_FONT_DIVIDEND: Final[int] = 130
LEGEND_COMPACT_TOWER_THRESHOLD: Final[int] = 10

RADAR_GRID_COLOR_HEX: Final[str] = "#E2E8F0"
RADAR_SPINE_COLOR_HEX: Final[str] = "#CBD5E1"
RADAR_BG_COLOR_HEX: Final[str] = "#F8FAFC"
RADAR_LABEL_COLOR_HEX: Final[str] = "#2D3748"
RADAR_YTICK_COLOR_HEX: Final[str] = "#718096"
RADAR_LEGEND_TEXT_COLOR_HEX: Final[str] = "#333333"

RADAR_SUBPLOT_LEFT: Final[float] = 0.1
RADAR_SUBPLOT_RIGHT: Final[float] = 0.7
RADAR_SUBPLOT_TOP: Final[float] = 0.85
RADAR_SUBPLOT_BOTTOM: Final[float] = 0.1
RADAR_LINE_WIDTH: Final[float] = 3.0
RADAR_MARKER_SIZE: Final[float] = 7.0
RADAR_FILL_ALPHA: Final[float] = 0.25
RADAR_SUPTITLE_FONT_SIZE: Final[float] = 24.0


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a UTF-8 encoded JSON file from a given path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def _safe_float_zero(
    value: Any, locale: str | None = None, allow_zero: bool = True
) -> float:
    """Safely convert an arbitrary value to a finite float using the domain calibrator."""
    return _domain_safe_float(value, locale=locale, allow_zero=allow_zero) or 0.0


def render_radar_chart(
    towers: list[dict[str, Any]],
    out_path: Path,
    doc_lang: str = "en",
    brand_color_hex: str = DEFAULT_BRAND_COLOR_HEX,
) -> Path:
    """Render a high-resolution single-series CMMI polar radar chart for any N-domain topology."""
    if not towers:
        raise ValueError("Cannot render radar chart: zero towers provided.")

    from assessment_engine.infrastructure.localization import format_number, t
    from assessment_engine.infrastructure.text_utils import CANONICAL_TOWER_NAMES

    # Enforces a strict numerical sort on tower labels with secondary string tie-breaking
    def _sort_key(node: dict[str, Any]) -> tuple[int, str]:
        t_code = str(node.get("id") or node.get("tower_code") or "")
        match = re.search(r"\d+", t_code)
        return (int(match.group(0)) if match else FALLBACK_SORT_RANK, t_code)

    sorted_towers = sorted(towers, key=_sort_key)

    labels = [str(t_node.get("id") or t_node.get("tower_code") or "") for t_node in sorted_towers]
    values = [
        _safe_float_zero(
            t_node.get("score_num") if t_node.get("score_num") is not None else t_node.get("score"),
            locale=doc_lang,
            allow_zero=True,
        )
        for t_node in sorted_towers
    ]

    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values += values[:1]

    raw_brand = str(brand_color_hex or DEFAULT_BRAND_COLOR_HEX).lstrip("#")
    if len(raw_brand) == 3 and all(c in "0123456789abcdefABCDEF" for c in raw_brand):
        raw_brand = "".join(c * 2 for c in raw_brand)
    elif len(raw_brand) != 6 or not all(c in "0123456789abcdefABCDEF" for c in raw_brand):
        raw_brand = DEFAULT_BRAND_COLOR_HEX
    brand_hex = f"#{raw_brand}"

    # Expands the figure width to ensure both the chart and its legend render completely within page boundaries
    fig = Figure(figsize=(RADAR_FIG_WIDTH_IN, RADAR_FIG_HEIGHT_IN), facecolor="white")
    fig.subplots_adjust(left=RADAR_SUBPLOT_LEFT, right=RADAR_SUBPLOT_RIGHT, top=RADAR_SUBPLOT_TOP, bottom=RADAR_SUBPLOT_BOTTOM)
    ax = fig.add_subplot(111, polar=True, facecolor=RADAR_BG_COLOR_HEX)
    ax.grid(color=RADAR_GRID_COLOR_HEX, linestyle="-", linewidth=1.0)
    ax.spines["polar"].set_color(RADAR_SPINE_COLOR_HEX)

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=RADAR_LABEL_COLOR_HEX, size=13, weight="bold")
    ax.set_rlabel_position(0)
    y_tick_labels = [format_number(float(i), locale=doc_lang, decimals=1) for i in [1, 2, 3, 4, 5]]
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(y_tick_labels, color=RADAR_YTICK_COLOR_HEX, size=10)
    ax.set_ylim(0, RADAR_YLIM_MAX)

    # Pure forensic AS-IS Current state polygon (solid corporate blue)
    ax.plot(
        angles,
        values,
        linewidth=RADAR_LINE_WIDTH,
        linestyle="solid",
        color=brand_hex,
        marker="o",
        markersize=RADAR_MARKER_SIZE,
    )
    ax.fill(angles, values, color=brand_hex, alpha=RADAR_FILL_ALPHA)

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
        label_radius = min(value + RADAR_LABEL_RADIAL_OFFSET, RADAR_LABEL_MAX_RADIUS)
        ax.text(
            angle,
            label_radius,
            text_val,
            color=brand_hex,
            size=13,
            horizontalalignment=ha,
            verticalalignment=va,
            weight="bold",
        )

    # Positions the legend, containing tower names, to the right of the chart
    tower_names = []
    for t_item in sorted_towers:
        t_id = str(t_item.get("id") or t_item.get("tower_code") or "")
        localized_name = t(f"tomo_tower_{t_id.lower()}_clean", locale=doc_lang)
        if not localized_name or localized_name.startswith("tomo_tower_"):
            num, dom = CANONICAL_TOWER_NAMES.get(t_id, ("", t_item.get("name", "")))
            localized_name = dom.replace("_", " ") if dom else t_item.get("name", "")
        tower_names.append(f"{t_id}: {localized_name}")

    n_towers = len(sorted_towers)
    legend_sep = "\n" if n_towers > LEGEND_COMPACT_TOWER_THRESHOLD else "\n\n"
    legend_fontsize = max(LEGEND_MIN_FONT_SIZE, min(LEGEND_MAX_FONT_SIZE, int(LEGEND_FONT_DIVIDEND / max(1, n_towers))))

    fig.text(
        0.72, 0.5, legend_sep.join(tower_names), fontsize=legend_fontsize, color=RADAR_LEGEND_TEXT_COLOR_HEX, va="center"
    )

    chart_title = t("global_radar_chart_title", locale=doc_lang)
    fig.suptitle(
        chart_title,
        size=RADAR_SUPTITLE_FONT_SIZE,
        color=brand_hex,
        x=0.5,
        y=0.96,
        horizontalalignment="center",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_png = tempfile.mkstemp(
        dir=str(out_path.parent), prefix="tmp_radar_chart_", suffix=".png"
    )
    fd_closed = False
    try:
        os.close(temp_fd)
        fd_closed = True
        fig.savefig(temp_png, dpi=RADAR_DPI, bbox_inches="tight")
        os.replace(temp_png, str(out_path))
    except Exception:
        if not fd_closed:
            try:
                os.close(temp_fd)
            except OSError:
                pass
        try:
            if os.path.exists(temp_png):
                os.unlink(temp_png)
        except OSError:
            pass
        raise
    finally:
        fig.clear()

    return out_path


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

    doc_lang = str(payload.get("meta", {}).get("language") or "en").lower()
    raw_brand = str(
        payload.get("meta", {}).get("brand_color")
        or payload.get("meta", {}).get("primary_color_hex")
        or DEFAULT_BRAND_COLOR_HEX
    )

    render_radar_chart(towers, out_path, doc_lang=doc_lang, brand_color_hex=raw_brand)
    logger.info("Global radar chart generated at: %s", out_path)


if __name__ == "__main__":
    main()
