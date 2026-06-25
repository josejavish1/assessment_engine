#
import logging
import subprocess
from pathlib import Path

from assessment_engine.scripts.lib.pipeline_runtime import resolve_python_bin

logger = logging.getLogger(__name__)


class VerificationError(RuntimeError):
    """Raised when a generated code artifact fails a formal verification stage."""

    pass


class VerificationAgent:
    r"""{'docstring': 'Executes a static analysis pipeline against a list of modified files.\n\nThis method runs a sequence of verification stages to ensure code quality.\nThe pipeline executes the following checks in order:\n1.  Linting and abstract syntax tree (AST) validation with Ruff.\n2.  Static type checking with MyPy.\n3.  Core invariant validation via golden path tests.\n\nThe process is short-circuiting; it halts and raises an exception on the\nfirst stage that fails. If the list of changed files is empty, the method\nreturns immediately without performing any checks. Execution logs for each\nstage, containing both stdout and stderr, are persisted to the directory\nspecified by `request_dir`.\n\nArgs:\n    request_dir: Path to the directory for storing execution logs from each\n        stage.\n    changed_files: A list of repository-relative file paths to be analyzed.\n\nReturns:\n    None. The method completes without error if all verification stages pass.\n\nRaises:\n    VerificationError: If any verification stage fails by returning a non-zero\n        exit code. The exception message includes the output from the\n        failed command.'}."""

    @classmethod
    def verify_changes(cls, request_dir: Path, changed_files: list[str]) -> None:
        """Run a short-circuiting static analysis pipeline against specified files.

        Executes a sequence of verification stages on a list of modified files. The
        pipeline is short-circuiting: failure at any stage prevents subsequent
        stages from running and immediately raises an exception. If the `changed_files`
        list is empty, the method returns without performing any checks.

        The analysis pipeline consists of the following stages:
        1.  Linting and Abstract Syntax Tree (AST) validation using Ruff.
        2.  Static type checking using MyPy.
        3.  Core invariant validation via golden path tests.

        Execution logs for each stage are persisted to the `request_dir`.

        Args:
            request_dir: The directory path for storing execution logs from each
                verification stage.
            changed_files: A list of file paths, relative to the repository root,
                that require static analysis.

        Raises:
            VerificationError: If any analysis stage command returns a non-zero exit
                code, indicating a failure.
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

        # Stage 1: Execute Ruff for linting and abstract syntax tree (AST) validation. This serves as a rapid, low-cost preliminary check to catch structural and stylistic issues before more expensive analyses.
        quality_cmd = [
            python_bin,
            "src/assessment_engine/scripts/tools/run_incremental_quality_gate.py",
            "--repo-root",
            ".",
        ]

        # Stage 2: Perform strict static type analysis using MyPy. This stage enforces type safety and validates adherence to defined type contracts.
        typing_cmd = [
            python_bin,
            "src/assessment_engine/scripts/tools/run_incremental_typecheck.py",
            "--repo-root",
            ".",
        ]

        # Stage 3: Execute targeted tests to validate core business logic invariants and verify the primary success path.
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
                cwd=".",  # Set the process execution context to the project root directory. All subsequent commands and file paths are relative to this origin.
            )

            # Persist execution logs to a request-specific directory, ensuring full operational traceability for each verification run.
            log_path = request_dir / f"verification_agent_step_{index}.log"
            log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")

            if result.returncode != 0:
                error_msg = f"Violación Estructural Provable detectada en {name}.\n\nSalida del Verificador:\n{result.stderr or result.stdout}"
                logger.error(error_msg)
                raise VerificationError(error_msg)

        logger.info(
            "Verification Agent: Todas las pruebas estructurales pasaron con éxito. Código seguro."
        )
