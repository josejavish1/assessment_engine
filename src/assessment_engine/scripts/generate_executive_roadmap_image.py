"""
Módulo generate_executive_roadmap_image.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main(argv: list[str] | None = None) -> None:
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

    # Orden inverso para el eje Y (para que el primero salga arriba)
    initiatives.reverse()

    fig, ax = plt.subplots(figsize=(14, max(6, len(initiatives) * 0.4)))

    # Dibujar barras de Gantt
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

    # Eje X con meses y marcas anuales
    ax.set_xticks(range(0, 37, 3))
    ax.set_xticklabels([f"M{i}" for i in range(0, 37, 3)], fontsize=10, color="grey")
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    # Líneas verticales anuales (12, 24, 36 meses)
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

    # Limpiar bordes
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
