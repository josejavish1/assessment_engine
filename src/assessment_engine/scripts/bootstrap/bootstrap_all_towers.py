"""
Módulo bootstrap_all_towers.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import argparse
import logging
from pathlib import Path

from assessment_engine.scripts.bootstrap.bootstrap_tower_from_matrix import (
    ROOT,
    bootstrap_tower,
)
from assessment_engine.scripts.validate_tower_definition import (
    validate_tower_definition,
)

logger = logging.getLogger(__name__)


def find_matrix_file(tower_dir: Path) -> Path:
    candidates = sorted(path for path in tower_dir.iterdir() if path.is_file())
    if not candidates:
        raise FileNotFoundError(f"No hay ficheros matriz en {tower_dir}")
    docx_candidates = [path for path in candidates if path.suffix.lower() == ".docx"]
    if docx_candidates:
        return docx_candidates[0]
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        default=str(ROOT / "source_docs" / "towers"),
        help="Directorio raíz con source_docs/towers/T*/",
    )
    parser.add_argument(
        "--engine-root",
        default=str(ROOT / "engine_config" / "towers"),
        help="Directorio raíz de salida engine_config/towers/T*/",
    )
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    engine_root = Path(args.engine_root).resolve()
    tower_dirs = sorted(
        path
        for path in source_root.iterdir()
        if path.is_dir() and path.name.startswith("T")
    )

    if not tower_dirs:
        raise SystemExit(f"No se encontraron torres en {source_root}")

    summary: list[dict] = []
    had_errors = False

    for tower_dir in tower_dirs:
        tower_id = tower_dir.name.upper().strip()
        out_dir = engine_root / tower_id
        try:
            matrix_file = find_matrix_file(tower_dir)
            tower_definition, _manifest, bootstrap_warnings = bootstrap_tower(
                tower_id, matrix_file, out_dir
            )
            validation_errors, validation_warnings = validate_tower_definition(
                tower_definition
            )

            status = "OK"
            warning_items = list(bootstrap_warnings) + list(validation_warnings)
            if validation_errors:
                status = "ERROR"
                had_errors = True
            elif warning_items:
                status = "WARNING"

            summary.append(
                {
                    "tower_id": tower_id,
                    "status": status,
                    "matrix_file": str(matrix_file),
                    "warnings": warning_items,
                    "errors": validation_errors,
                }
            )
        except Exception as exc:
            had_errors = True
            summary.append(
                {
                    "tower_id": tower_id,
                    "status": "ERROR",
                    "matrix_file": "",
                    "warnings": [],
                    "errors": [str(exc)],
                }
            )

    for item in summary:
        logger.info(f"{item['tower_id']}: {item['status']}")
        if item["matrix_file"]:
            logger.info(f"  matrix_file: {item['matrix_file']}")
        for warning in item["warnings"]:
            logger.warning(f"  WARNING: {warning}")
        for error in item["errors"]:
            logger.error(f"  ERROR: {error}")

    if had_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
