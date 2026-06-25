"""Implements the Model Context Protocol (MCP) server for the Assessment Engine. This module provides API endpoints for core rendering and analysis functionalities, designed for consumption by Supervisor Agents (e.g., LangGraph, CrewAI) or other MCP-compliant clients."""

import asyncio
import json
import os
import subprocess
import sys
import uuid
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from domain.schemas.annex_synthesis import AnnexPayload
from domain.schemas.blueprint import BlueprintPayload

#
mcp = FastMCP("Assessment Engine Core")

#
ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable
LOAD_ERRORS = (JSONDecodeError, OSError, UnicodeDecodeError)


def _read_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _summarize_validation_error(error: ValidationError) -> list[str]:
    summary: list[str] = []
    for item in error.errors():
        location = " -> ".join(str(part) for part in item["loc"])
        summary.append(f"{location}: {item['msg']}")
    return summary


def _inspect_payload_artifact(path: Path, schema, artifact_name: str) -> dict:
    artifact_state: dict[str, Any] = {
        "path": str(path),
        "status": "missing",
    }
    if not path.exists():
        return artifact_state

    artifact_state["status"] = "present"
    try:
        data = _read_json_file(path)
    except LOAD_ERRORS as error:
        artifact_state["status"] = "error"
        artifact_state["message"] = f"{artifact_name} could not be loaded: {error}"
        return artifact_state

    try:
        payload = schema.model_validate(data)
    except ValidationError as error:
        artifact_state["status"] = "invalid"
        artifact_state["validation_errors"] = _summarize_validation_error(error)
        return artifact_state

    artifact_state["status"] = "valid"
    artifact_state["generation_metadata"] = data.get("_generation_metadata")
    if artifact_name == "Blueprint":
        artifact_state["tower_code"] = payload.document_meta.tower_code
        artifact_state["tower_name"] = payload.document_meta.tower_name
    else:
        artifact_state["tower_code"] = payload.document_meta.get("tower_code")
        artifact_state["tower_name"] = payload.document_meta.get("tower_name")
    return artifact_state


def _inspect_docx_artifact(pattern: str, case_dir: Path) -> dict:
    matches = sorted(case_dir.glob(pattern))
    if not matches:
        return {"status": "missing"}
    return {
        "status": "present",
        "path": str(matches[0]),
    }


def _canonical_overall_status(canonical_state: dict) -> str:
    payload_statuses = (
        canonical_state["blueprint_payload"]["status"],
        canonical_state["annex_payload"]["status"],
    )
    if all(status == "valid" for status in payload_statuses):
        return "complete"
    if any(status in {"invalid", "error"} for status in payload_statuses):
        return "invalid"
    if any(status in {"valid", "present"} for status in payload_statuses):
        return "partial"
    return "missing"


def _inspect_canonical_state(case_dir: Path) -> dict:
    blueprint_candidates = sorted(case_dir.glob("blueprint_*_payload.json"))
    annex_candidates = sorted(case_dir.glob("approved_annex_*.template_payload.json"))

    blueprint_path = (
        blueprint_candidates[0]
        if blueprint_candidates
        else case_dir / "blueprint_payload.json"
    )
    annex_path = (
        annex_candidates[0]
        if annex_candidates
        else case_dir / "approved_annex.template_payload.json"
    )

    canonical_state = {
        "mode": "blueprint-first",
        "blueprint_payload": _inspect_payload_artifact(
            blueprint_path,
            BlueprintPayload,
            "Blueprint",
        ),
        "annex_payload": _inspect_payload_artifact(
            annex_path,
            AnnexPayload,
            "Annex",
        ),
        "deliverables": {
            "blueprint_docx": _inspect_docx_artifact(
                "Blueprint_Transformacion_*.docx", case_dir
            ),
            "annex_docx": _inspect_docx_artifact("annex_*_final.docx", case_dir),
        },
    }
    canonical_state["overall_status"] = _canonical_overall_status(canonical_state)
    return canonical_state


def _inspect_legacy_state(case_dir: Path) -> dict:
    legacy_state = {}
    for section in ["asis", "risks", "gap", "tobe", "todo", "conclusion"]:
        file = case_dir / f"approved_{section}.generated.json"
        if not file.exists():
            legacy_state[section] = {"status": "missing"}
            continue

        try:
            data = _read_json_file(file)
        except LOAD_ERRORS as error:
            legacy_state[section] = {
                "status": "error",
                "message": str(error),
            }
            continue

        legacy_state[section] = {
            "status": data.get("status", "unknown"),
            "metadata": data.get("_approval_metadata", {}),
            "path": str(file),
        }
    return legacy_state


def _run_script(module_name: str, args: list[str]) -> str:
    """Executes a specified engine script within an isolated and secure subprocess, capturing its standard output and error streams."""
    cmd = [PYTHON_BIN, "-m", module_name] + args
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Error ejecutando {module_name}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    # Redirect the standard error stream (stderr) to standard output (stdout). This consolidation is necessary to ensure capture of all process output, as many applications direct informational logs to stderr by convention.
    combined_output = f"{result.stdout}\n{result.stderr}".strip()
    return combined_output


@mcp.tool()
def build_tower_payload(
    approved_annex_json: str, output_json: str, client_name: str, profile: str = "short"
) -> str:
    """Generates a structured payload for a DOCX service from a legacy annex object.

    This function serves as an adapter, converting a refined annex object from a
    JSON file into a payload format compatible with the DOCX generation service.
    It delegates the core transformation logic to an external legacy script.

    Args:
        approved_annex_json: The filesystem path to the input JSON file
            containing the refined legacy annex data.
        output_json: The filesystem path where the generated output payload JSON
            file will be written.
        client_name: The name of the client associated with the document.
        profile: The rendering profile to apply during payload generation.
            Defaults to "short".

    Returns:
        A confirmation message prepended to the standard output captured from
        the underlying script execution.

    Raises:
        RuntimeError: If the underlying script execution fails or returns a
            non-zero exit code.
    """
    out = _run_script(
        "application._legacy.build_tower_annex_template_payload",
        [approved_annex_json, output_json, client_name, profile],
    )
    return f"✅ Payload construido con éxito.\n{out}"


@mcp.tool()
def render_tower_docx(payload_json: str, template_docx: str, output_docx: str) -> str:
    """Renders a Tower Annex DOCX document using a template and JSON data.

    This function orchestrates the document generation process by calling an
    external script, `adapters.render_tower_annex_from_template`. The script
    populates a given DOCX template with data from a specified JSON payload file,
    saving the result to an output path. The JSON payload must be generated by
    the `build_tower_payload` function before this is called.

    Args:
        payload_json: Path to the input JSON file containing the tower data.
        template_docx: Path to the corporate DOCX template file.
        output_docx: Path where the final rendered DOCX document will be saved.

    Returns:
        A string containing a success message and any standard output generated
        by the rendering script.

    Raises:
        Exception: Propagated from the underlying script runner if the document
            generation process fails for any reason.
    """
    out = _run_script(
        "adapters.render_tower_annex_from_template",
        [payload_json, template_docx, output_docx],
    )
    return f"✅ Documento de Torre renderizado con éxito.\n{out}"


@mcp.tool()
def generate_radar_chart(global_payload_json: str) -> str:
    """Invokes an external script to generate a radar chart PNG image.

    This function serves as a wrapper that executes the external script located at
    `application.generate_global_radar_chart`. It passes the provided JSON payload
    as a direct command-line argument to this script for processing.

    Args:
        global_payload_json: A string containing a JSON object with the data
            required by the generation script to create the radar chart.

    Returns:
        A string concatenating a static success message with the standard output
        (stdout) from the executed script. The stdout is expected to contain
        information about the generated file, such as its path.

    Raises:
        Exception: If the underlying script execution via `_run_script` fails,
            for example, due to a non-zero exit code.
    """
    out = _run_script("application.generate_global_radar_chart", [global_payload_json])
    return f"✅ Gráfico generado con éxito.\n{out}"


@mcp.tool()
def render_commercial_docx(
    commercial_payload_json: str, template_docx: str, output_docx: str
) -> str:
    """Render a Commercial Account Action Plan DOCX document from a data payload.

    This function orchestrates document generation by invoking an external script
    (`adapters.render_commercial_report`). It passes the JSON payload, input
    template path, and output path directly to this script for processing.

    Args:
        commercial_payload_json: A JSON formatted string containing the structured
            data for the commercial action plan.
        template_docx: The file system path to the source `.docx` template.
        output_docx: The destination file system path for the generated `.docx` report.

    Returns:
        A string confirming successful generation, including standard output from
        the underlying script.

    Raises:
        FileNotFoundError: If the file at `template_docx` cannot be found.
        Exception: If the underlying script fails during execution. Common causes
            include malformed JSON, template syntax errors, or file permission issues.
    """
    out = _run_script(
        "adapters.render_commercial_report",
        [commercial_payload_json, template_docx, output_docx],
    )
    return f"✅ Reporte comercial renderizado.\n{out}"


@mcp.tool()
def get_tower_state(case_dir: str) -> str:
    """Inspects a case directory and returns the state of tower artifacts as a JSON string.

    This function validates the existence of the specified `case_dir` path. It
    then aggregates the state of both canonical (blueprint-to-annex) and legacy
    tower artifacts by calling internal helper functions.

    The resulting state dictionary is serialized to a JSON string. The JSON object
    will contain 'canonical' and 'legacy' keys. For backward compatibility, all
    key-value pairs from the 'legacy' state dictionary are also merged into the
    root of the JSON object.

    Args:
        case_dir: The file system path to the case directory to inspect.

    Returns:
        A JSON-formatted string representing the consolidated artifact state.
        If `case_dir` does not exist or is not a directory, a plain-text error
        message is returned instead.
    """
    path = Path(case_dir)
    if not path.exists() or not path.is_dir():
        return f"Error: Directorio {case_dir} no encontrado."

    state = {
        "canonical": _inspect_canonical_state(path),
        "legacy": _inspect_legacy_state(path),
    }
    state.update(state["legacy"])
    return json.dumps(state, indent=2, ensure_ascii=False)


# An in-memory dictionary serves as the job store. This provides a lightweight, transient mechanism for managing job state without requiring an external persistence layer.
job_status: dict[str, str] = {}
job_results: dict[str, str] = {}


async def _background_run_plan(job_id: str, request_text: str):
    loop = asyncio.get_event_loop()

    def run_sync():
        """Executes the product owner orchestrator's 'plan' command synchronously."""
        return _run_script(
            "application.tools.run_product_owner_orchestrator",
            ["plan", "--request", request_text],
        )

    try:
        out = await loop.run_in_executor(None, run_sync)
        found_plan = False
        for line in out.splitlines():
            try:
                log_data = json.loads(line)
                msg = log_data.get("message", "")
                if "Plan generado en " in msg:
                    request_dir = msg.split("Plan generado en ")[1].strip()
                    plan_path = Path(request_dir) / "plan.json"
                    if plan_path.exists():
                        plan_data = plan_path.read_text(encoding="utf-8")
                        job_results[job_id] = (
                            f"✅ Plan generado con éxito.\nREQUEST_DIR={request_dir}\n{plan_data}"
                        )
                        found_plan = True
                        break
            except Exception:
                continue
        if not found_plan:
            job_results[job_id] = (
                f"❌ Error: Plan generated but path not found in logs.\nLogs: {out}"
            )
        job_status[job_id] = "completed"
    except Exception as e:
        job_status[job_id] = "error"
        job_results[job_id] = f"❌ Error ejecutando orquestador: {e}"


@mcp.tool()
async def start_plan_generation(request_text: str) -> str:
    """Initiates the asynchronous generation of an execution plan.

    This function immediately returns a unique job identifier and dispatches the
    plan generation to a background task using `asyncio.create_task`. This
    non-blocking approach allows a client to poll for the job's status using
    the returned `job_id` without waiting for the computation to complete.

    Args:
        request_text (str): The natural language request from which to generate
            an execution plan.

    Returns:
        str: A JSON-formatted string containing the unique `job_id` for the
            background task and its initial status, which is always 'started'.
            Example: '{"job_id": "...", "status": "started"}'.
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = "running"

    # Dispatch the task to a background executor. This non-blocking, fire-and-forget approach decouples the main server thread from the lifecycle of the asynchronous job.
    asyncio.create_task(_background_run_plan(job_id, request_text))

    return json.dumps({"job_id": job_id, "status": "started"})


@mcp.tool()
def check_plan_status(job_id: str) -> str:
    """Poll the status of an asynchronous plan generation job.

    Queries an internal job store for the current state of a specified job ID.
    If the job has reached a terminal state ('completed' or 'error'), this
    function also retrieves and includes the associated final result payload.

    Args:
        job_id (str): The unique identifier for the job to query.

    Returns:
        str: A JSON-formatted string describing the job status. If the job is
            in a terminal state ('completed' or 'error'), the JSON object
            includes both 'status' and 'result' keys. Otherwise, it
            contains only the 'status' key.
    """
    status = job_status.get(job_id, "not_found")
    if status == "completed" or status == "error":
        result = job_results.get(job_id, "")
        return json.dumps({"status": status, "result": result})
    return json.dumps({"status": status})


@mcp.tool()
async def start_plan_execution(request_dir: str, alt_index: int = 0) -> str:
    """Asynchronously executes a pre-approved plan via a subprocess.

    This function spawns a background `asyncio` task to run an external
    orchestrator script. It returns immediately with a unique job identifier,
    allowing the caller to poll for status and results without blocking.

    The state and standard output of the background process are stored in
    module-level dictionaries, keyed by the returned `job_id`. The job status
    is updated to 'running', 'completed', or 'error' based on the subprocess's
    execution lifecycle and exit code.

    Args:
        request_dir (str): The file system path to the directory containing the
            plan and associated artifacts to be executed.
        alt_index (int): The zero-based index of the alternative plan variant
            to execute. Defaults to 0.

    Returns:
        str: A JSON-formatted string containing the unique `job_id` for the
            background task and an initial status of "started".
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = "running"
    job_results[job_id] = ""

    async def _background_run_execution():
        import asyncio.subprocess

        cmd = [
            PYTHON_BIN,
            "-m",
            "application.tools.run_product_owner_orchestrator",
            "execute",
            "--request-dir",
            request_dir,
            "--alt-index",
            str(alt_index),
            "--allow-dirty",
            "--executor-command",
            ".github/scripts/orchestrator-gemini-executor.sh {repo_root} {task_prompt_file} {attempt}",
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                job_results[job_id] += line.decode("utf-8")

            await process.wait()

            if process.returncode != 0:
                job_status[job_id] = "error"
                job_results[job_id] += (
                    f"\n❌ El proceso terminó con código de error {process.returncode}"
                )
            else:
                job_status[job_id] = "completed"
                job_results[job_id] += "\n✅ Ejecución completada."

        except Exception as e:
            job_status[job_id] = "error"
            job_results[job_id] += f"\n❌ Error en ejecución: {e}"

    asyncio.create_task(_background_run_execution())
    return json.dumps({"job_id": job_id, "status": "started"})


@mcp.tool()
def check_execution_status(job_id: str) -> str:
    """Return a JSON string containing the execution status and result for a job."""
    status = job_status.get(job_id, "not_found")
    result = job_results.get(job_id, "")
    return json.dumps({"status": status, "result": result})


@mcp.tool()
def check_action_gate(request_dir: str) -> str:
    """Checks for a `reconciliation_summary.json` lock file and returns its contents.

    This function inspects the specified directory for a file named
    `reconciliation_summary.json`. The presence of this file acts as a control
    mechanism, termed an "Action Gate," signaling that a subsequent process
    requires explicit authorization before it can proceed.

    If the file exists and contains valid JSON, its deserialized content is
    returned within a JSON structure indicating the gate is active. If the file
    is absent, the gate is considered inactive. If the file exists but cannot
    be read or parsed as JSON (e.g., due to permissions or malformed content),
    the gate is also considered inactive, and an error message is included in
    the response.

    Args:
        request_dir (str): The filesystem path to the directory to search for
            the `reconciliation_summary.json` file.

    Returns:
        str: A JSON-formatted string representing the state of the action gate.
            The string will serialize a dictionary with one of the following
            structures:
            - `{'action_gate_active': True, 'data': ...}`: If the file is found
              and successfully parsed. The `data` key holds the deserialized
              JSON content from the file.
            - `{'action_gate_active': False}`: If the file does not exist.
            - `{'action_gate_active': False, 'error': '...'}`: If an error
              occurs during file reading or JSON deserialization. The `error`
              key contains a string representation of the exception.
    """
    import os

    summary_path = os.path.join(request_dir, "reconciliation_summary.json")
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps({"action_gate_active": True, "data": data})
        except Exception as e:
            return json.dumps({"action_gate_active": False, "error": str(e)})
    return json.dumps({"action_gate_active": False})


@mcp.tool()
def authorize_action_gate(request_dir: str, alt_index: int = 0) -> str:
    r"""{'docstring': 'Authorizes a pending Action Gate by applying a reconciliation summary to a plan.\n\n    This function consumes a `reconciliation_summary.json` file, which serves\n    as a transactional lock and contains proposed modifications for a paused\n    execution. It applies these modifications to the corresponding `plan.json`\n    file within the same directory.\n\n    The authorization process involves two primary updates to the plan:\n    1.  The `blast_radius` list from the summary is merged into the `in_scope`\n        file list of the active plan.\n    2.  Any `required_invariant_breach` specified in the summary is sanctioned by\n        updating the plan\'s `invariants` list with an explicit authorization\n        entry.\n\n    Upon successful modification of the plan, an `authorized_feedback.json` file\n    is created for auditing. The `reconciliation_summary.json` file is then\n    removed, which unlocks the gate and permits the execution of the updated plan.\n\n    Args:\n        request_dir: The directory path containing `plan.json` and the\n            `reconciliation_summary.json` lock file.\n        alt_index: The zero-based index of the plan alternative to modify if\n            `plan.json` contains an `alternatives` list.\n\n    Returns:\n        A JSON-formatted string indicating the outcome. On success, contains\n        `{"success": true, ...}`. On failure, such as a missing file,\n        malformed JSON, or I/O error, contains `{"success": false, ...}` with an\n        error description.'}."""
    import os

    summary_path = os.path.join(request_dir, "reconciliation_summary.json")
    plan_path = os.path.join(request_dir, "plan.json")

    if not os.path.exists(summary_path):
        return json.dumps({"success": False, "message": "No hay Action Gate activo."})

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)

            active_plan = plan
            if "tasks" not in plan and "alternatives" in plan:
                active_plan = plan["alternatives"][alt_index]

            blast_radius = summary.get("diagnosis", {}).get("blast_radius", [])
            if "in_scope" not in active_plan:
                active_plan["in_scope"] = []
            for file in blast_radius:
                if file not in active_plan["in_scope"]:
                    active_plan["in_scope"].append(file)

            invariant_breach = summary.get("diagnosis", {}).get(
                "required_invariant_breach"
            )
            if invariant_breach and "invariants" in active_plan:
                active_plan["invariants"] = [
                    inv for inv in active_plan["invariants"] if inv != invariant_breach
                ]
                active_plan["invariants"].append(
                    f"EXCEPTION AUTHORIZED BY HUMAN: Se permite romper el invariante previo respecto a: {invariant_breach}"
                )

            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            #
            feedback_path = os.path.join(request_dir, "authorized_feedback.json")
            with open(feedback_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "task_id": summary.get("task_id"),
                        "feedback": f"SÍNTOMA ANTERIOR:\n{summary.get('raw_error')}\n\nCURA AUTORIZADA POR EL PRODUCT OWNER:\n{summary.get('diagnosis', {}).get('proposed_cure')}",
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        os.remove(summary_path)
        return json.dumps({"success": True, "message": "Action Gate autorizado."})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Error autorizando: {e}"})


@mcp.tool()
def abort_and_revert() -> str:
    r"""{'docstring': "Reverts the local Git repository to its last committed state.\n\nExecutes `git reset --hard` followed by `git clean -fd` to restore the\nrepository to the state of the last commit (HEAD). The `reset` command\ndiscards all staged and unstaged changes to tracked files, while the `clean`\ncommand removes all untracked files and directories.\n\nWarning: This is a destructive operation that results in the irreversible\nloss of all uncommitted work.\n\nReturns:\n    str: A JSON-encoded string representing the operation's result.\n        On success, the JSON object is `{'success': True, 'message': str}`.\n        On failure, it is `{'success': False, 'message': str}`, where the\n        message contains details of the exception that occurred."}."""
    try:
        # Production hardening: For improved robustness, the Popen process should be terminated directly via its Process ID (PID) rather than relying on higher-level abstractions.
        subprocess.run(
            ["git", "reset", "--hard"], cwd=str(ROOT), check=True, capture_output=True
        )
        subprocess.run(
            ["git", "clean", "-fd"], cwd=str(ROOT), check=True, capture_output=True
        )
        return json.dumps(
            {
                "success": True,
                "message": "✅ Abortado y código revertido a su estado original (git reset --hard).",
            }
        )
    except Exception as e:
        return json.dumps({"success": False, "message": f"❌ Error al revertir: {e}"})


if __name__ == "__main__":
    import argparse
    import logging

    from infrastructure.logger_config import setup_structured_logging

    setup_structured_logging(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run()
