"""
Módulo generate_tower_radar_chart.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_float(value):
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

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)

    ax.set_rlabel_position(0)
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
