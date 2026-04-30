"""
Módulo generate_smoke_data.py.
Genera inputs sintéticos y deterministas para el caso smoke_ivirma.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from assessment_engine.scripts.lib.runtime_paths import ROOT


DEFAULT_CLIENT = "smoke_ivirma"
DEFAULT_SEED = 42
DEFAULT_TOWERS = ["T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]
DEFAULT_TOWER_TARGETS: dict[str, tuple[float, float]] = {
    "T2": (2.0, 3.0),
    "T3": (1.5, 2.5),
    "T4": (2.5, 3.5),
    "T5": (1.0, 2.0),
    "T6": (1.5, 2.5),
    "T7": (2.0, 3.0),
    "T8": (3.0, 4.0),
    "T9": (2.5, 3.5),
}
DEFAULT_CONTEXT_TEXT = """
Notas de la reunión de Assessment Tecnológico de IVIRMA (Smoke Test).

Contexto de Negocio:
La compañía está en fase de expansión inorgánica internacional impulsada por KKR, con el objetivo de duplicar la facturación a 1.300M€.
La principal preocupación del CEO es asegurar la integración rápida de nuevas clínicas manteniendo el nivel de excelencia clínica y operativa.

Tecnología:
El proveedor estratégico cloud es Microsoft Azure. Sin embargo, el crecimiento ha fragmentado la red de comunicaciones.
El almacenamiento de imágenes médicas e historiales clínicos es el core absoluto del negocio, pero no existe una estrategia inmutable de recuperación (Vault).

Seguridad y Normativa:
El CISO está alarmado por el aumento de incidentes de ransomware en el sector salud. Además, son conscientes de que la inminente aplicación de la directiva NIS2 en Europa les afecta directamente como operadores esenciales de salud, y actualmente su infraestructura no garantiza el cumplimiento.

Operaciones:
El soporte a usuarios (médicos y embriólogos) es muy manual, con un ITSM básico. Faltan procesos industrializados y visibilidad de los activos (CMDB inexistente), lo que choca con la agilidad necesaria para la expansión.
"""


def normalize_towers(towers: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for tower in towers or DEFAULT_TOWERS:
        tower_id = tower.upper().strip()
        if tower_id and tower_id not in normalized:
            normalized.append(tower_id)
    return normalized


def build_responses(
    root: Path,
    towers: list[str],
    seed: int,
    tower_targets: dict[str, tuple[float, float]] | None = None,
) -> list[str]:
    rng = random.Random(seed)
    responses_lines: list[str] = []
    targets = tower_targets or DEFAULT_TOWER_TARGETS

    for tower_id in towers:
        def_file = (
            root / "engine_config" / "towers" / tower_id / f"tower_definition_{tower_id}.json"
        )
        if not def_file.exists():
            continue

        data = json.loads(def_file.read_text(encoding="utf-8"))
        min_score, max_score = targets.get(tower_id, (2.0, 3.0))
        for pillar in data.get("pillars", []):
            for kpi in pillar.get("kpis", []):
                score = round(rng.uniform(min_score, max_score), 1)
                responses_lines.append(f"{kpi['kpi_id']}.PR1: {score}")

    return responses_lines


def generate_smoke_inputs(
    client: str = DEFAULT_CLIENT,
    towers: list[str] | None = None,
    seed: int = DEFAULT_SEED,
    root: Path = ROOT,
    write_files: bool = True,
) -> tuple[Path, Path]:
    client_id = client.strip() or DEFAULT_CLIENT
    client_dir = root / "working" / client_id
    if write_files:
        client_dir.mkdir(parents=True, exist_ok=True)

    normalized_towers = normalize_towers(towers)
    responses_lines = build_responses(root, normalized_towers, seed)

    responses_path = client_dir / "responses.txt"
    context_path = client_dir / "context.txt"
    if write_files:
        responses_path.write_text("\n".join(responses_lines) + "\n", encoding="utf-8")
        context_path.write_text(DEFAULT_CONTEXT_TEXT.strip() + "\n", encoding="utf-8")

    return context_path, responses_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default=DEFAULT_CLIENT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--towers", nargs="*", default=DEFAULT_TOWERS)
    args = parser.parse_args(argv)

    context_path, responses_path = generate_smoke_inputs(
        client=args.client,
        towers=args.towers,
        seed=args.seed,
    )

    responses_count = len(
        responses_path.read_text(encoding="utf-8").splitlines()
    )
    print(
        f"✅ Inputs smoke generados en {context_path.parent} "
        f"(contexto + {responses_count} respuestas)."
    )
    print(f"   - {context_path}")
    print(f"   - {responses_path}")


if __name__ == "__main__":
    main()
