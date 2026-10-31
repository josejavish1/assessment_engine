"""Defines the Model Context Protocol (MCP) server for the Assessment Engine.

This module provides an API that exposes core assessment, rendering, and plan execution functionalities. It is designed for consumption by supervisor agents (e.g., LangGraph, CrewAI) or other MCP-compliant clients.
"""

import asyncio
import atexit
import concurrent.futures
import contextlib
import importlib
import io
import json
import logging
import os
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from assessment_engine.domain.schemas.annex_synthesis import AnnexPayload
from assessment_engine.domain.schemas.blueprint import BlueprintPayload

logger = logging.getLogger("assessment_engine.mcp_server")

mcp = FastMCP("Assessment Engine Core")

# Defines singleton path and runtime configuration constants.
ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable
LOAD_ERRORS = (JSONDecodeError, OSError, UnicodeDecodeError)

DEFAULT_MAX_WORKERS = int(os.environ.get("MCP_PROCESS_POOL_WORKERS", "4"))
DEFAULT_SYNTHESIS_PROFILE = os.environ.get("MCP_DEFAULT_SYNTHESIS_PROFILE", "short")
DEFAULT_EXECUTOR_COMMAND = os.environ.get(
    "MCP_ORCHESTRATOR_EXECUTOR_CMD",
    ".github/scripts/orchestrator-gemini-executor.sh {repo_root} {task_prompt_file} {attempt}",
)
DEFAULT_MCP_PORT = int(os.environ.get("MCP_SERVER_PORT", "8000"))
BLUEPRINT_DOCX_PATTERN = os.environ.get(
    "MCP_BLUEPRINT_DOCX_PATTERN", "Blueprint_Transformation_*.docx"
)
ANNEX_DOCX_PATTERN = os.environ.get("MCP_ANNEX_DOCX_PATTERN", "annex_*_final.docx")
PLAN_GENERATED_MARKER = "Plan generated in "

_IN_PROCESS_EXEC_LOCK = threading.RLock()
_POOL_LOCK = threading.Lock()
_PROCESS_POOL: concurrent.futures.ProcessPoolExecutor | None = None


def _shutdown_process_pool() -> None:
    """Cleanly shuts down the shared ProcessPoolExecutor on interpreter exit."""
    global _PROCESS_POOL
    with _POOL_LOCK:
        if _PROCESS_POOL is not None:
            _PROCESS_POOL.shutdown(wait=False, cancel_futures=True)
            _PROCESS_POOL = None


def _get_process_pool() -> concurrent.futures.ProcessPoolExecutor:
    """Lazily initializes and returns the bounded ProcessPoolExecutor singleton."""
    global _PROCESS_POOL
    if _PROCESS_POOL is None:
        with _POOL_LOCK:
            if _PROCESS_POOL is None:
                _PROCESS_POOL = concurrent.futures.ProcessPoolExecutor(
                    max_workers=DEFAULT_MAX_WORKERS
                )
                atexit.register(_shutdown_process_pool)
    return _PROCESS_POOL


@dataclass(frozen=True)
class TowerBuildRequest:
    """Typed request parameters for in-process tower payload synthesis."""

    approved_annex_json: str
    output_json: str
    client_name: str
    profile: str = DEFAULT_SYNTHESIS_PROFILE


@dataclass(frozen=True)
class DocxRenderRequest:
    """Typed request parameters for CPU-bound DOCX template rendering."""

    module_name: str
    payload_json: str
    template_docx: str
    output_docx: str


def _invoke_module_in_process(module_name: str, args: list[str]) -> str:
    """Executes an internal module in-process while capturing stdout and stderr streams safely."""
    with _IN_PROCESS_EXEC_LOCK:
        root_str = str(ROOT)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        original_argv = sys.argv[:]

        try:
            sys.argv = [module_name] + list(args)
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(
                stderr_buf
            ):
                module = importlib.import_module(module_name)
                if hasattr(module, "main") and callable(module.main):
                    try:
                        result = module.main(args)
                    except TypeError:
                        result = module.main()
                    if isinstance(result, int) and result != 0:
                        raise SystemExit(result)
                elif hasattr(module, "cli") and callable(module.cli):
                    module.cli()
                else:
                    import runpy

                    runpy.run_module(module_name, run_name="__main__", alter_sys=True)
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 0
            if code != 0:
                raise RuntimeError(
                    f"Error executing {module_name}:\nSTDOUT: {stdout_buf.getvalue()}\nSTDERR: {stderr_buf.getvalue()}"
                ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Error executing {module_name}: {exc}\nSTDOUT: {stdout_buf.getvalue()}\nSTDERR: {stderr_buf.getvalue()}"
            ) from exc
        finally:
            sys.argv = original_argv

        return f"{stdout_buf.getvalue()}\n{stderr_buf.getvalue()}".strip()


def _serialize_docx_worker(request: DocxRenderRequest) -> str:
    """Top-level worker function executed inside the bounded ProcessPoolExecutor."""
    return _invoke_module_in_process(
        request.module_name,
        [request.payload_json, request.template_docx, request.output_docx],
    )


async def execute_tower_build(request: TowerBuildRequest) -> str:
    """Typed coroutine that executes tower payload synthesis directly in-process."""
    return await asyncio.to_thread(
        _invoke_module_in_process,
        "assessment_engine.application.run_executive_annex_synthesizer",
        [
            request.approved_annex_json,
            request.output_json,
            request.client_name,
            request.profile,
        ],
    )


async def execute_docx_render(request: DocxRenderRequest) -> str:
    """Typed coroutine that dispatches CPU-bound DOCX XML serialization to the shared ProcessPoolExecutor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _get_process_pool(), _serialize_docx_worker, request
    )


def _run_coro_sync(coro: Any) -> str:
    """Bridges an asynchronous coroutine into a synchronous execution context safely."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


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
                BLUEPRINT_DOCX_PATTERN, case_dir
            ),
            "annex_docx": _inspect_docx_artifact(ANNEX_DOCX_PATTERN, case_dir),
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
    """Executes a specified engine module in-process or via the bounded ProcessPoolExecutor for DOCX rendering."""
    if module_name == "assessment_engine.application.run_executive_annex_synthesizer":
        request = TowerBuildRequest(
            approved_annex_json=args[0],
            output_json=args[1],
            client_name=args[2],
            profile=args[3] if len(args) > 3 else DEFAULT_SYNTHESIS_PROFILE,
        )
        return _run_coro_sync(execute_tower_build(request))

    if module_name in {
        "assessment_engine.adapters.render_tower_annex_from_template",
        "assessment_engine.adapters.render_commercial_report",
    }:
        render_req = DocxRenderRequest(
            module_name=module_name,
            payload_json=args[0],
            template_docx=args[1],
            output_docx=args[2],
        )
        return _run_coro_sync(execute_docx_render(render_req))

    return _invoke_module_in_process(module_name, args)


@mcp.tool()
def build_tower_payload(
    approved_annex_json: str,
    output_json: str,
    client_name: str,
    profile: str = DEFAULT_SYNTHESIS_PROFILE,
) -> str:
    """Generates a JSON payload for Tower Annex rendering from a legacy artifact.

    This function acts as a wrapper, executing the executive annex synthesizer
    in-process to transform an 'annex refined' JSON artifact into the canonical
    payload format required for DOCX document generation.

    Args:
        approved_annex_json: Path to the input JSON file containing the legacy
            'annex refined' data.
        output_json: Path to the file where the generated JSON payload will be
            written.
        client_name: Name of the client to be embedded within the payload.
        profile: The rendering profile that dictates the transformation logic.

    Returns:
        A success message concatenated with the standard output from the
            execution.

    Raises:
        RuntimeError: If the underlying execution encounters an error.
    """
    request = TowerBuildRequest(
        approved_annex_json=approved_annex_json,
        output_json=output_json,
        client_name=client_name,
        profile=profile,
    )
    out = _run_coro_sync(execute_tower_build(request))
    return f"Payload successfully built.\n{out}"


@mcp.tool()
def render_tower_docx(payload_json: str, template_docx: str, output_docx: str) -> str:
    """Populates a DOCX template using a structured JSON payload via the bounded ProcessPoolExecutor.

    This function dispatches CPU-bound XML document serialization to the shared
    process pool for `assessment_engine.adapters.render_tower_annex_from_template`.

    Args:
        payload_json: The file path to the input JSON data.
        template_docx: The file path to the source DOCX template.
        output_docx: The destination file path for the rendered DOCX document.

    Returns:
        A string containing a success message concatenated with the standard
        output from the rendering worker upon successful execution.

    Raises:
        FileNotFoundError: If the `payload_json` or `template_docx` file cannot
            be located.
        RuntimeError: If the underlying rendering worker fails during execution.
    """
    request = DocxRenderRequest(
        module_name="assessment_engine.adapters.render_tower_annex_from_template",
        payload_json=payload_json,
        template_docx=template_docx,
        output_docx=output_docx,
    )
    out = _run_coro_sync(execute_docx_render(request))
    return f"Tower Document successfully rendered.\n{out}"


@mcp.tool()
def generate_radar_chart(global_payload_json: str) -> str:
    """Generates a global radar chart in-process.

    This function acts as a wrapper, passing the provided JSON payload to the
    `assessment_engine.application.generate_global_radar_chart` module for
    processing.

    Args:
        global_payload_json: A JSON string containing the aggregated global
            assessment data.

    Returns:
        A formatted string containing a success message prefixed to the standard
        output from the generation module.

    Raises:
        Exception: Propagated from the runner if the chart generation
            module encounters an error during execution.
    """
    out = _run_script(
        "assessment_engine.application.generate_global_radar_chart",
        [global_payload_json],
    )
    return f"Chart successfully generated.\n{out}"


@mcp.tool()
def render_commercial_docx(
    commercial_payload_json: str, template_docx: str, output_docx: str
) -> str:
    """Renders a commercial action plan into a DOCX document from a JSON payload.

    This function dispatches `assessment_engine.adapters.render_commercial_report`
    to the bounded ProcessPoolExecutor for CPU-bound DOCX serialization.

    Args:
        commercial_payload_json: The file path to the JSON payload containing
            the commercial account action plan data.
        template_docx: The file path to the DOCX template document.
        output_docx: The destination file path for the generated DOCX report.

    Returns:
        A confirmation message concatenated with the standard output from the
        rendering module upon successful execution.

    Raises:
        FileNotFoundError: If the `commercial_payload_json` or `template_docx`
            file does not exist at the specified paths.
        RuntimeError: If the underlying rendering module encounters an error
            during document generation.
    """
    request = DocxRenderRequest(
        module_name="assessment_engine.adapters.render_commercial_report",
        payload_json=commercial_payload_json,
        template_docx=template_docx,
        output_docx=output_docx,
    )
    out = _run_coro_sync(execute_docx_render(request))
    return f"Commercial report successfully rendered.\n{out}"


@mcp.tool()
def get_tower_state(case_dir: str) -> str:
    """Generates a JSON-serialized summary of tower artifact states.

    This function inspects a specified case directory to determine the state of
    its artifacts. It distinguishes between artifacts generated by the canonical
    blueprint-to-annex workflow and those from legacy processes. The resulting
    JSON object contains distinct 'canonical' and 'legacy' keys. For backward
    compatibility, the contents of the 'legacy' key are also merged into the
    top-level of the JSON object.

    Args:
        case_dir: The file system path to the case directory to inspect.

    Returns:
        A JSON-formatted string summarizing the state of the tower artifacts.
        If the path specified by `case_dir` does not exist or is not a
        directory, a plain-text error string is returned.
    """
    path = Path(case_dir)
    if not path.exists() or not path.is_dir():
        return f"Error: Directory {case_dir} not found."

    state = {
        "canonical": _inspect_canonical_state(path),
        "legacy": _inspect_legacy_state(path),
    }
    state.update(state["legacy"])
    return json.dumps(state, indent=2, ensure_ascii=False)


# Maintains the in-memory state of all asynchronous jobs, mapping job IDs to their current status, logs, and final results.
job_status: dict[str, str] = {}
job_results: dict[str, str] = {}


async def _background_run_plan(job_id: str, request_text: str):
    loop = asyncio.get_running_loop()

    def run_sync():
        """Synchronously execute the 'plan' command of the product owner orchestrator module."""
        return _run_script(
            "assessment_engine.application.tools.run_product_owner_orchestrator",
            ["plan", "--request", request_text],
        )

    try:
        out = await loop.run_in_executor(None, run_sync)
        found_plan = False
        for line in out.splitlines():
            try:
                log_data = json.loads(line)
                msg = log_data.get("message", "")
                if PLAN_GENERATED_MARKER in msg:
                    request_dir = msg.split(PLAN_GENERATED_MARKER)[1].strip()
                    plan_path = Path(request_dir) / "plan.json"
                    if plan_path.exists():
                        plan_data = plan_path.read_text(encoding="utf-8")
                        job_results[job_id] = (
                            f"Plan successfully generated.\nREQUEST_DIR={request_dir}\n{plan_data}"
                        )
                        found_plan = True
                        break
            except (json.JSONDecodeError, IndexError, OSError) as ex:
                logger.debug(f"[PO-Orchestrator] Log line unparseable as plan: {ex}")
                continue
        if not found_plan:
            job_results[job_id] = (
                f"Error: Plan generated but path not found in logs.\nLogs: {out}"
            )
        job_status[job_id] = "completed"
    except Exception as e:
        job_status[job_id] = "error"
        job_results[job_id] = f"Error executing orchestrator: {e}"


@mcp.tool()
async def start_plan_generation(request_text: str) -> str:
    """Dispatches an asynchronous job to generate a Commercial Account Action Plan.

    Schedules the plan generation to run as a background task and returns a unique
    job identifier immediately. This non-blocking design enables a client to use
    the returned `job_id` to poll for completion status without waiting for the
    operation to finish.

    Args:
        request_text: The user-provided prompt or details required for plan
            generation.

    Returns:
        A JSON-serialized string containing the unique `job_id` for the
        background task and an initial status of 'started'.
        Example: '{"job_id": "...", "status": "started"}'
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = "running"

    asyncio.create_task(_background_run_plan(job_id, request_text))

    return json.dumps({"job_id": job_id, "status": "started"})


@mcp.tool()
def check_plan_status(job_id: str) -> str:
    """Return the status of a plan generation job as a JSON-formatted string."""
    status = job_status.get(job_id, "not_found")
    if status == "completed" or status == "error":
        result = job_results.get(job_id, "")
        return json.dumps({"status": status, "result": result})
    return json.dumps({"status": status})


@mcp.tool()
async def start_plan_execution(request_dir: str, alt_index: int = 0) -> str:
    """Initiates the asynchronous execution of an action plan in a background task.

    This function invokes the product owner orchestrator module
    (`run_product_owner_orchestrator`) in-process via a background thread.
    A unique job ID is generated and returned immediately, allowing the caller
    to track the long-running task without blocking.

    Args:
        request_dir: The file system path to the directory containing the
            action plan request to execute.
        alt_index: The zero-based index of the alternative plan within the
            request to execute. Defaults to 0.

    Returns:
        A JSON-formatted string containing the unique job ID and an initial
        status of "started".
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = "running"
    job_results[job_id] = ""

    async def _background_run_execution():
        exec_args = [
            "execute",
            "--request-dir",
            request_dir,
            "--alt-index",
            str(alt_index),
            "--allow-dirty",
            "--executor-command",
            DEFAULT_EXECUTOR_COMMAND,
        ]

        try:
            out = await asyncio.to_thread(
                _invoke_module_in_process,
                "assessment_engine.application.tools.run_product_owner_orchestrator",
                exec_args,
            )
            job_results[job_id] += out + "\nExecution completed."
            job_status[job_id] = "completed"
        except Exception as e:
            job_status[job_id] = "error"
            job_results[job_id] += f"\nExecution error: {e}"

    asyncio.create_task(_background_run_execution())
    return json.dumps({"job_id": job_id, "status": "started"})


@mcp.tool()
def check_execution_status(job_id: str) -> str:
    """Return the status and result of an execution job as a JSON-serialized string."""
    status = job_status.get(job_id, "not_found")
    result = job_results.get(job_id, "")
    return json.dumps({"status": status, "result": result})


@mcp.tool()
def check_action_gate(request_dir: str) -> str:
    """Checks for an active Immune Governance Action Gate for a given plan.

    Determines if a mandatory manual approval step is required by verifying the
    existence and readability of a `reconciliation_summary.json` file within the
    specified request directory. The presence of this file signifies an active
    action gate.

    Args:
        request_dir: The file system path to the directory containing the plan's
            reconciliation files.

    Returns:
        A JSON-formatted string describing the action gate status. The structure of
        the returned JSON object depends on the state of the summary file:
        - If `reconciliation_summary.json` exists and is successfully parsed,
          returns `{"action_gate_active": true, "data": <content>}` where
          `<content>` is the parsed JSON data from the file.
        - If the file does not exist, returns `{"action_gate_active": false}`.
        - If the file exists but an error occurs during I/O or JSON decoding,
          returns `{"action_gate_active": false, "error": "<error_message>"}`.
    """
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
    """Resolves a pending Action Gate by applying an authorization summary to a plan file.

    This function operates on a file-based signaling mechanism within a specified
    directory. It reads authorization details from `reconciliation_summary.json`,
    modifies the corresponding `plan.json` to reflect the authorized changes,
    generates an `authorized_feedback.json` audit file, and finally deletes the
    summary file to signify completion.

    The modifications include updating the plan's `in_scope` files based on the
    summary's `blast_radius` and overriding specified invariants with an explicit
    authorization notice.

    Args:
        request_dir (str): The path to the directory containing the `plan.json`
            and `reconciliation_summary.json` files.
        alt_index (int): The index of the alternative plan to use from
            `plan.json` if the primary plan lacks a "tasks" field. Defaults to 0.

    Returns:
        str: A JSON-formatted string with a 'success' (bool) status and a
            'message' (str). On failure, the message contains a description of
            the error, which may include missing files, malformed JSON, or
            filesystem permission issues.
    """
    summary_path = os.path.join(request_dir, "reconciliation_summary.json")
    plan_path = os.path.join(request_dir, "plan.json")

    if not os.path.exists(summary_path):
        return json.dumps({"success": False, "message": "No active Action Gate found."})

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
                    f"EXCEPTION AUTHORIZED BY HUMAN: Waiver granted to break prior invariant regarding: {invariant_breach}"
                )

            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            feedback_path = os.path.join(request_dir, "authorized_feedback.json")
            with open(feedback_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "task_id": summary.get("task_id"),
                        "feedback": f"PREVIOUS SYMPTOM:\n{summary.get('raw_error')}\n\nAUTHORIZED REMEDIATION:\n{summary.get('diagnosis', {}).get('proposed_cure')}",
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        os.remove(summary_path)
        return json.dumps({"success": True, "message": "Action Gate authorized."})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Error authorizing: {e}"})


@mcp.tool()
def abort_and_revert() -> str:
    """Forcefully reverts the working directory to the `HEAD` commit.

    This function provides a destructive reset capability by reverting the repository
    to its last committed state. It executes `git reset --hard` followed by
    `git clean -fd`. This operation discards all uncommitted local modifications,
    including staged changes, and removes all untracked files and directories.

    Potential exceptions during the execution of git commands are caught and
    encapsulated within the returned JSON object.

    Returns:
        str: A JSON-formatted string representing the outcome of the operation.
            The object contains the following keys:
            - 'success' (bool): True if the repository was reverted successfully,
              False otherwise.
            - 'message' (str): A description of the result or the error that
              occurred.
    """
    try:
        subprocess.run(
            ["git", "reset", "--hard"], cwd=str(ROOT), check=True, capture_output=True
        )
        subprocess.run(
            ["git", "clean", "-fd"], cwd=str(ROOT), check=True, capture_output=True
        )
        return json.dumps(
            {
                "success": True,
                "message": "Aborted and working tree reverted to original commit (git reset --hard).",
            }
        )
    except Exception as e:
        return json.dumps({"success": False, "message": f"Error reverting: {e}"})


if __name__ == "__main__":
    import argparse

    from assessment_engine.lib.logger_config import setup_structured_logging

    setup_structured_logging(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=DEFAULT_MCP_PORT)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run()
