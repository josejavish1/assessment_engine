"""
Módulo generate_global_radar_chart.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import logging
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_float(value):
    if value is None:
        return 0.0
    try:
        return float(str(value).split()[0].replace(",", "."))
    except Exception:
        return 0.0


def main(argv: list[str] | None = None) -> None:
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

    # Ordenación numérica estricta T1...T10
    towers = sorted(
        towers, key=lambda x: int(x.get("id")[1:]) if x.get("id")[1:].isdigit() else 99
    )

    labels = [t.get("id", "") for t in towers]
    values = [safe_float(t.get("score")) for t in towers]

    n = len(labels)
    angles = [i / float(n) * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values += values[:1]

    # Estilo Consultoría (Azul/Gris profesional)
    plt.style.use("ggplot")
    # Aumentar ancho para que el gráfico pueda ocupar toda la página y la leyenda quepa
    fig = plt.figure(figsize=(14, 8))
    # Dejar espacio equilibrado
    fig.subplots_adjust(left=0.1, right=0.7, top=0.85, bottom=0.1)
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], labels, color="grey", size=13)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=10)
    plt.ylim(0, 5.5)

    ax.plot(angles, values, linewidth=3, linestyle="solid", color="#1f77b4")
    ax.fill(angles, values, color="#1f77b4", alpha=0.25)

    # Añadir las puntuaciones (ej. 2.5) en cada punto
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

    # Añadir nombres de torres como leyenda a la derecha con buen tamaño
    tower_names = [f"{t.get('id')}: {t.get('name')}" for t in towers]
    plt.figtext(
        0.72, 0.5, "\n\n".join(tower_names), fontsize=13, color="#333333", va="center"
    )

    # Título centrado y más grande (24pt)
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
