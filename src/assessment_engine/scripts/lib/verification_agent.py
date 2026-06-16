# --- START OF BUSINESS LOGIC ---
import logging
import subprocess
from pathlib import Path

from assessment_engine.scripts.lib.pipeline_runtime import resolve_python_bin

logger = logging.getLogger(__name__)


class VerificationError(RuntimeError):
    """Excepción lanzada cuando el código falla las pruebas formales (AST, Tipos o Linting)."""

    pass


class VerificationAgent:
    """
    Agente matemático determinista (Pragmatismo de Élite).
    Evalúa si el código generado cumple los contratos de tipos (MyPy) y sintaxis (Ruff/AST)
    antes de delegarlo al Doctor Agent.
    """

    @classmethod
    def verify_changes(cls, request_dir: Path, changed_files: list[str]) -> None:
        """
        Ejecuta las validaciones sobre los archivos cambiados en el worktree.
        Lanza VerificationError si alguna validación falla.
        """
        logger.info(
            "Verification Agent: Iniciando análisis estático determinista sobre los cambios."
        )

        if not changed_files:
            logger.info(
                "Verification Agent: No hay archivos Python modificados para analizar."
            )
            return

        python_bin = resolve_python_bin()

        # 1. Validación Estructural y Linting (Ruff)
        quality_cmd = [
            python_bin,
            "src/assessment_engine/scripts/tools/run_incremental_quality_gate.py",
            "--repo-root",
            ".",
        ]

        # 2. Prueba de Tipos Estricta (MyPy)
        typing_cmd = [
            python_bin,
            "src/assessment_engine/scripts/tools/run_incremental_typecheck.py",
            "--repo-root",
            ".",
        ]

        # 3. Validación de Invariantes / Golden Path
        golden_cmd = [
            python_bin,
            "src/assessment_engine/scripts/tools/run_golden_path_check.py",
            "--repo-root",
            ".",
        ]

        for path in changed_files:
            quality_cmd.extend(["--path", path])
            typing_cmd.extend(["--path", path])

        commands = [
            ("Linting / Sintaxis", quality_cmd),
            ("Typestate Proof (MyPy)", typing_cmd),
            ("Golden Path Invariants", golden_cmd),
        ]

        for index, (name, cmd) in enumerate(commands, start=1):
            logger.info(f"Verification Agent: Ejecutando {name}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=".",  # Root directory as the executor runs from there
            )

            # Log to request dir for traceability
            log_path = request_dir / f"verification_agent_step_{index}.log"
            log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")

            if result.returncode != 0:
                error_msg = f"Violación Estructural Provable detectada en {name}.\n\nSalida del Verificador:\n{result.stderr or result.stdout}"
                logger.error(error_msg)
                raise VerificationError(error_msg)

        logger.info(
            "Verification Agent: Todas las pruebas estructurales pasaron con éxito. Código seguro."
        )
