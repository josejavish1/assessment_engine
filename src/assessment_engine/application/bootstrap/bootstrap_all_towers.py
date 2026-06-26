"""Implements the bootstrapping procedure for the Assessment Engine pipeline. This module is responsible for the initialization and configuration of all constituent service components, referred to as 'towers'."""

import argparse
import logging
from pathlib import Path

from assessment_engine.application.bootstrap.bootstrap_tower_from_matrix import (
    ROOT,
    bootstrap_tower,
)
from assessment_engine.application.validate_tower_definition import (
    validate_tower_definition,
)

logger = logging.getLogger(__name__)


def find_matrix_file(tower_dir: Path) -> Path:
    """Locate the primary matrix file in a directory, prioritizing `.docx` files.

    The function scans for files within the specified directory, sorting them
    lexicographically. It gives precedence to the first file with a `.docx`
    extension (case-insensitive). If no `.docx` file is present, it returns
    the first file in the sorted list, regardless of its type.

    Args:
        tower_dir: The filesystem path to the directory to be searched.

    Returns:
        A `pathlib.Path` object representing the located matrix file.

    Raises:
        FileNotFoundError: If the `tower_dir` contains no files.
    """
    candidates = sorted(path for path in tower_dir.iterdir() if path.is_file())
    if not candidates:
        raise FileNotFoundError(f"No hay ficheros matriz en {tower_dir}")
    docx_candidates = [path for path in candidates if path.suffix.lower() == ".docx"]
    if docx_candidates:
        return docx_candidates[0]
    return candidates[0]


def main() -> None:
    """Orchestrates the bootstrapping and validation of all tower configurations.

    This function serves as the script's main entry point. It parses command-line
    arguments specifying source and destination directories, then iterates through
    each tower subdirectory found in the source location. For each tower, it
    locates the primary matrix file, executes the bootstrap process to generate an
    engine configuration, and validates the resulting definition.

    A summary of the outcome for each tower (OK, WARNING, or ERROR), including
    any diagnostic messages, is logged upon completion.

    The process is controlled via the following command-line arguments:
      --source-root: The root directory containing tower source subdirectories.
      --engine-root: The root directory where generated engine configurations
                     will be written.

    Returns:
        None.

    Raises:
        SystemExit: If no tower directories are found in the source root, or if
            any tower encounters a fatal error during processing, causing the
            script to terminate with a non-zero exit code.
    """
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
