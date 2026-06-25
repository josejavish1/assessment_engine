import asyncio

#
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from assessment_engine.scripts.lib.ai_client import call_agent
from assessment_engine.scripts.lib.apex_models import ApexDebateResponse
from assessment_engine.scripts.lib.apex_sentinel import ApexSentinel

#
console = Console()
logging.basicConfig(level=logging.INFO, filename="working/apex/error.log")
logger = logging.getLogger("APEX-Dispatcher")

if "APEX_WORKSPACE_DIR" in os.environ:
    REPO_ROOT = Path(os.environ["APEX_WORKSPACE_DIR"]).resolve()
else:
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
BACKLOG_PATH = REPO_ROOT / "docs/audits/IMPROVEMENT_BACKLOG.md"
WORKING_DIR = REPO_ROOT / "working/apex"
SENTINEL = ApexSentinel(WORKING_DIR, budget_limit=25.0)


class Task(TypedDict):
    r"""{'docstring': "Defines the structure for a dictionary representing a single task.\n\nThis `TypedDict` enforces a consistent schema for task objects, which is\nused for static type analysis and data validation.\n\nAttributes:\n    id: A unique string identifier for the task.\n    priority: A string representing the priority level of the task.\n    title: A short, descriptive title for the task.\n    description: A detailed explanation of the task's objective.\n    status: The current execution status of the task.\n    instruction: An optional machine-readable instruction or command."}."""

    id: str
    priority: str
    title: str
    description: str
    status: str
    instruction: Optional[str]


class UiState(TypedDict):
    """Represents a snapshot of the application's user interface state.

    This TypedDict defines the dictionary structure for communicating the complete
    application state to a frontend, ensuring type-safe access to state
    attributes.

    Attributes:
        all_tasks (List[Task]): A list of all task objects managed by the system.
        active_task (Optional[Task]): The currently executing task, or None if
            the system is idle.
        active_logs (List[str]): A list of log messages associated with the
            active task.
        debate_transcript (List[Tuple[str, Any]]): A transcript of a debate,
            structured as a list of (speaker, message) tuples.
        total_cost (float): The cumulative monetary cost of all executed
            operations.
        start_time (float): The UNIX timestamp of the session start time.
        completed_count (int): The total number of completed tasks.
        last_event (str): A human-readable string describing the most recent
            event.
    """

    all_tasks: List[Task]
    active_task: Optional[Task]
    active_logs: List[str]
    debate_transcript: List[Tuple[str, Any]]
    total_cost: float
    start_time: float
    completed_count: int
    last_event: str


UI_STATE: UiState = {
    "all_tasks": [],
    "active_task": None,
    "active_logs": [],
    "debate_transcript": [],
    "total_cost": 0.0,
    "start_time": time.time(),
    "completed_count": 0,
    "last_event": "Inicializando...",
}


def load_apex_prompt(filename: str) -> dict:
    """Load an Apex prompt configuration from a YAML file.

    This function resolves the full file path by first checking for the
    `APEX_PROMPTS_DIR` environment variable. If this variable is set, the path is
    constructed as `$APEX_PROMPTS_DIR/registry/<filename>`. If the environment
    variable is not set, it falls back to a default path assuming a standard
    project structure, resolving to `<project_root>/prompts/registry/<filename>`
    relative to this source file's location.

    Args:
        filename (str): The name of the YAML configuration file to load.

    Returns:
        dict: The parsed content of the YAML file.

    Raises:
        FileNotFoundError: If the specified prompt file does not exist at the
            resolved path.
        yaml.YAMLError: If an error occurs during YAML parsing.
    """
    import yaml  #

    prompts_dir = os.environ.get("APEX_PROMPTS_DIR")
    if prompts_dir:
        filepath = Path(prompts_dir) / "registry" / filename
    else:
        filepath = (
            Path(__file__).resolve().parent.parent.parent
            / "prompts"
            / "registry"
            / filename
        )

    with filepath.open("r", encoding="utf-8") as f:
        return cast(dict, yaml.safe_load(f))


def make_layout() -> Layout:
    """Construct a pre-configured vertical layout for the main terminal UI."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="active_mission", size=6),
        Layout(name="brain_stream", ratio=1),
        Layout(name="terminal_mirror", size=8),
        Layout(name="registry", size=10),
        Layout(name="footer", size=3),
    )
    return layout


def update_ui_components(layout: Layout) -> None:
    """Populate a Rich layout with data from the global UI state.

    This function is the central rendering entrypoint for the user interface. It
    populates a `rich.layout.Layout` object by reading metrics, logs, and
    state from the global `UI_STATE` dictionary. The function updates specific
    layout panels corresponding to the header (cost, progress, uptime), the
    active mission, a 'brain stream' transcript, a terminal log mirror, the
    task backlog, and a footer log.

    Errors occurring during the update cycle are caught internally and their
    messages are rendered into the footer panel, which prevents UI rendering
    failures from crashing the application.

    Args:
        layout (Layout): The `rich.layout.Layout` instance to update in-place.
    """
    try:
        #
        elapsed = time.time() - UI_STATE["start_time"]
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        total = len(UI_STATE["all_tasks"])
        done = UI_STATE["completed_count"]
        pct = (done / total * 100) if total > 0 else 0
        header_text = Text.assemble(
            (" APEX SENTINEL ", "bold white on blue"),
            f" | BURN: ${UI_STATE['total_cost']:.3f} | ",
            (f"PROGRESS: {pct:.1f}% ({done}/{total}) ", "bold yellow"),
            f"| UPTIME: {h:02d}:{m:02d}:{s:02d}",
        )
        layout["header"].update(Panel(header_text, style="blue"))

        #
        active_task = UI_STATE["active_task"]
        if active_task:
            status_color = "green" if "Running" in active_task["status"] else "yellow"
            mission_text = f"[bold cyan]ID:[/] {active_task['id']}  [bold {status_color}]STATUS:[/] {active_task['status']}\n[bold white]MISIÓN:[/] {active_task['title'][:80]}"
            layout["active_mission"].update(
                Panel(
                    mission_text,
                    title="[bold red]CURRENT MISSION[/]",
                    border_style="red",
                )
            )
        else:
            layout["active_mission"].update(
                Panel("Esperando tareas...", title="MISSION")
            )

        #
        text = Text()
        for role, msg in UI_STATE["debate_transcript"][-6:]:
            color = "yellow" if "DOCTOR" in role else "magenta"
            if "SENTINEL" in role:
                color = "blue"
            text.append(f"[{role}]: ", style=f"bold {color}")
            text.append(f"{str(msg)[:200]}\n", style="italic")
        layout["brain_stream"].update(
            Panel(text, title="[bold]BRAIN STREAM[/]", border_style="yellow")
        )

        #
        logs = "\n".join(UI_STATE["active_logs"][-6:])
        layout["terminal_mirror"].update(
            Panel(logs, title="[bold]TERMINAL MIRROR[/]", border_style="dim")
        )

        #
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("ID", width=8)
        table.add_column("Status", width=15)
        table.add_column("Task Title", ratio=1)
        start = max(0, UI_STATE["completed_count"] - 1)
        for t in UI_STATE["all_tasks"][start : start + 7]:
            color = "green" if "Success" in t["status"] else "white"
            table.add_row(t["id"], f"[{color}]{t['status']}[/]", t["title"][:50])
        layout["registry"].update(
            Panel(table, title="[bold]BACKLOG[/]", border_style="blue")
        )
        layout["footer"].update(Panel(f"LOG: {UI_STATE['last_event']}", style="dim"))
    except Exception as e:
        layout["footer"].update(Panel(f"UI Error: {e}", style="red"))


async def run_po_orchestrator(task_prompt: str) -> tuple[bool, str]:
    """Asynchronously execute the 'po-run' orchestrator subprocess and capture its output.

    This coroutine spawns the `po-run` command, passing the provided `task_prompt`
    as a command-line argument. The prompt is first sanitized by replacing
    newlines with spaces and escaping double quotes. The subprocess's standard
    error is redirected to standard output, and the `PYTHONUNBUFFERED` environment
    variable is set to ensure unbuffered, real-time output streaming.

    Output is captured line by line. Each line is decoded, written to a persistent
    session log file (`WORKING_DIR/session.log`), and appended to a global
    `UI_STATE` dictionary for immediate display. The function waits for the
    subprocess to complete before returning.

    Args:
        task_prompt: The natural language prompt to be executed by the orchestrator.

    Returns:
        A tuple containing a boolean success flag and the complete captured log.
        The first element is True if the subprocess exited with code 0, False
        otherwise. The second element is a single string of all non-empty, stripped
        log lines, joined by newlines.

    Raises:
        FileNotFoundError: If the 'po-run' executable is not found at the
            expected path (`REPO_ROOT / "bin/po-run"`).
        PermissionError: If the session log file (`WORKING_DIR / "session.log"`)
            cannot be opened for writing.
    """
    clean_prompt = task_prompt.replace("\n", " ").replace('"', '\\"')
    cmd = [str(REPO_ROOT / "bin/po-run"), clean_prompt]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=REPO_ROOT,
        env=env,
    )
    full_log = []

    session_log_path = WORKING_DIR / "session.log"

    with open(session_log_path, "a", encoding="utf-8") as f_log:
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode()
                f_log.write(decoded)
                f_log.flush()
                clean_decoded = decoded.strip()
                if clean_decoded:
                    UI_STATE["active_logs"].append(clean_decoded)
                    full_log.append(clean_decoded)

        await process.wait()

    return process.returncode == 0, "\n".join(full_log)


async def perform_apex_debate(
    error_logs: str, previous_failures: str
) -> ApexDebateResponse:
    r"""{'docstring': 'Orchestrates a simulated two-agent debate to generate a solution for an error.\n\n    This function formulates a single, composite prompt for an "Architect" large\n    language model. The prompt simulates a two-step reasoning process. It first\n    frames the problem context (error logs, past failures) for a hypothetical\n    "Doctor" agent. It then tasks the primary "Architect" agent with evaluating\n    this context against the repository\'s documented invariants (from GEMINI.md)\n    to produce a final, authoritative decision.\n\n    The function updates a global UI state with the debate progress and logs the\n    final transaction details.\n\n    Args:\n        error_logs: The raw error logs from a failed execution. The input is\n            truncated to the first 1500 characters.\n        previous_failures: A string summarizing previously attempted solutions\n            that have failed.\n\n    Returns:\n        An `ApexDebateResponse` instance containing the final decision and\n        accompanying reasoning from the architect agent.\n\n    Raises:\n        FileNotFoundError: If `apex_doctor.yaml`, `apex_architect.yaml`, or\n            `GEMINI.md` are not found in their expected locations.'}."""
    UI_STATE["debate_transcript"].append(("SENTINEL", "Iniciando debate..."))
    doctor_config = load_apex_prompt("apex_doctor.yaml")
    architect_config = load_apex_prompt("apex_architect.yaml")
    doctor_prompt = doctor_config["prompt_details"]["template"].format(
        error_logs=error_logs[:1500], previous_failures=previous_failures
    )
    architect_prompt = architect_config["prompt_details"]["template"].format(
        repository_invariants=(REPO_ROOT / "GEMINI.md").read_text(),
        proposed_strategy=doctor_prompt,
    )
    data = await call_agent(
        model_name="gemini-2.5-pro",
        prompt=architect_prompt,
        output_schema=ApexDebateResponse,
        instruction="Resuelve el bloqueo.",
    )
    response = ApexDebateResponse(**data)
    UI_STATE["debate_transcript"].append(("ARCHITECT", response.decision))

    active_id = UI_STATE["active_task"]["id"] if UI_STATE["active_task"] else "N/A"
    SENTINEL.log_transaction(
        active_id,
        "debate_completed",
        {"decision": response.decision, "reasoning": response.reasoning},
        cost=0.15,
    )
    return response


def parse_backlog() -> List[Task]:
    """Parses a Markdown-formatted backlog file into a list of tasks.

    Reads the file specified by the global `BACKLOG_PATH` constant. The file is
    expected to contain a Markdown table with columns for priority, area, title,
    and description. A regular expression extracts data from each row,
    ignoring the table's header and separator lines.

    For each valid data row, a `Task` dictionary is created. The parsing
    logic strips leading/trailing whitespace from all fields and removes any
    Markdown emphasis characters (asterisks) from the priority field. Each
    task is assigned a sequentially generated `id` (e.g., 'T1', 'T2'), a
    default `status` of 'Pending', and a `None` value for `instruction`.

    Returns:
        List[Task]: A list of dictionaries, where each dictionary represents a
            task conforming to the `Task` type definition. An empty list is
            returned if the source file does not exist or contains no parsable
            task rows.
    """
    if not BACKLOG_PATH.exists():
        return []
    content = BACKLOG_PATH.read_text()
    pattern = (
        r"\|\s*(\*?\*?P[123]\*?\*?)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
    )
    matches = re.findall(pattern, content)
    tasks: List[Task] = []
    for match in matches:
        p, area, title, desc = [m.strip().replace("*", "") for m in match]
        if "Área" in area or "Prioridad" in p:
            continue
        task: Task = {
            "id": f"T{len(tasks) + 1}",
            "priority": p,
            "title": title,
            "description": desc,
            "status": "Pending",
            "instruction": None,
        }
        tasks.append(task)
    return tasks


async def process_task(task: Task, queue: List[Task], idx: int) -> bool:
    r"""{'docstring': 'Executes a task, attempting automated recovery from failures via an analytical debate.\n\n    The function attempts to execute the task via an orchestrator. If execution\n    fails, it enters a recovery loop for a configured maximum number of attempts.\n    In each recovery attempt, an asynchronous "APEX debate" analyzes the failure\n    logs to determine a corrective action.\n\n    Based on the debate\'s outcome, the function may:\n    1.  Inject new prerequisite tasks into the queue and defer the current task.\n    2.  Revise the task\'s instructions and retry execution.\n    3.  Mark the task as a terminal failure ("HARD_BLOCK").\n\n    A circuit breaker mitigates infinite recovery loops by limiting the total\n    number of injected emergency tasks. If a task with \'EMG\' priority results\n    in a HARD_BLOCK, the entire program terminates. This function is not pure\n    and modifies global state for UI updates and transaction logging.\n\n    Args:\n        task: The task object to be processed. Its \'status\' and \'instruction\'\n            fields may be modified in-place during execution.\n        queue: The main task queue. This list is modified in-place if the\n            recovery process injects new prerequisite emergency tasks.\n        idx: The index within `queue` at which new prerequisite tasks are to\n            be inserted.\n\n    Returns:\n        True if the task completes successfully. False if the task is deferred,\n        fails terminally (hard-blocked), or exhausts all recovery attempts.\n\n    Raises:\n        SystemExit: If a critical \'EMG\' priority task fails and is hard-blocked.\n        KeyError: If the input `task` dictionary is missing required keys such\n            as \'id\' or \'title\'.'}."""
    attempts = 0
    max_rescue_rounds = 3
    previous_failures: List[str] = []
    UI_STATE["active_task"] = task
    task["status"] = "Running"
    while attempts <= max_rescue_rounds:
        SENTINEL.log_transaction(
            task["id"], f"attempt_{attempts}", cast(Dict[str, Any], task)
        )
        prompt = task.get("instruction")
        if not prompt:
            prompt = f"Implementa: {task['title']}\nDescripción: {task.get('description', '')}"

        success, logs = await run_po_orchestrator(prompt)
        if success:
            task["status"] = "Success"
            SENTINEL.log_transaction(task["id"], "success", {}, cost=0.05)
            UI_STATE["completed_count"] += 1
            return True

        SENTINEL.log_transaction(
            task["id"], "attempt_failed", {"error_snippet": logs[-300:]}
        )
        attempts += 1
        task["status"] = "Rescuing"
        debate = await perform_apex_debate(logs, "\n".join(previous_failures))
        previous_failures.append(f"Fallo {attempts}: {debate.reasoning}")

        if debate.decision == "INJECT_PREREQUISITE":
            # A circuit breaker mechanism to mitigate infinite rescue loops. This logic prevents a task from being repeatedly re-queued in a failure state.
            emg_tasks = [t for t in queue if t.get("id", "").startswith("EMG-")]
            if len(emg_tasks) > 5:
                UI_STATE["debate_transcript"].append(
                    ("SENTINEL", "Max emergency tasks reached. Hard blocking.")
                )
                task["status"] = "HARD_BLOCK"
                SENTINEL.log_transaction(
                    task["id"],
                    "hard_block",
                    {"reason": "Infinite rescue loop detected."},
                )
                UI_STATE["completed_count"] += 1
                return False

            if debate.prerequisite_tasks:
                for p_task_data in reversed(debate.prerequisite_tasks):
                    new_task: Task = {
                        "id": f"EMG-{int(time.time()) % 1000}",
                        "priority": "EMG",
                        "title": p_task_data.get("title", "Emergency Task"),
                        "description": p_task_data.get("description", ""),
                        "status": "Pending",
                        "instruction": p_task_data.get("instruction"),
                    }
                    # Ensures list independence by creating a shallow copy. This prevents unintended side effects, such as duplicate task insertions, which can occur if the `queue` and `all_tasks` variables reference the same underlying list object.
                    queue.insert(idx, new_task)
                    if queue is not UI_STATE["all_tasks"]:
                        UI_STATE["all_tasks"].insert(idx, new_task)

            task["status"] = "Waiting EMG"
            return False

        elif debate.decision == "REJECTED" or debate.is_terminal_failure:
            task["status"] = "HARD_BLOCK"
            SENTINEL.log_transaction(
                task["id"], "hard_block", {"reason": debate.reasoning}
            )
            UI_STATE["completed_count"] += 1
            if task.get("priority") == "EMG":
                UI_STATE["last_event"] = (
                    f"🛑 CRITICAL: Fallo en pre-requisito EMG ({task['id']}). Deteniendo orquestador."
                )
                print(
                    f"\n[!] ERROR CRÍTICO: La tarea de emergencia {task['id']} ha sido bloqueada (HARD_BLOCK)."
                )
                print(f"Razón: {debate.reasoning}")
                print(
                    "Como es una tarea de infraestructura crítica, no es seguro continuar. Abortando."
                )
                sys.exit(1)
            return False
        task["instruction"] = debate.revised_instruction
    return False


async def monitor_mode(layout: Layout) -> None:
    r"""{'docstring': "Run the application's monitoring mode by continuously updating the UI.\n\n    Initializes the task state from the project backlog, then enters an\n    infinite polling loop to provide a real-time view of task execution.\n\n    In each cycle, this coroutine checks for the existence of the ledger file\n    at `SENTINEL.ledger_path`. If found, the entire file is read from the\n    beginning, and each line is processed as a JSON-encoded transaction. These\n    transactions are used to update the global `UI_STATE` dictionary by:\n    - Recalculating the total cost from all transactions.\n    - Updating individual task statuses based on event types ('success',\n      'hard_block', 'attempt').\n    - Assembling a debate transcript from 'debate_completed' events.\n\n    Lines that fail JSON decoding or cause processing errors are silently skipped.\n    After processing, the provided layout is updated, and the coroutine sleeps\n    for one second before the next cycle.\n\n    Args:\n        layout: The Rich layout object to be updated on each cycle.\n\n    Returns:\n        This coroutine runs in an infinite loop and is not expected to return.\n\n    Raises:\n        PermissionError: If the ledger file at `SENTINEL.ledger_path` exists but\n            cannot be opened due to insufficient read permissions."}."""
    UI_STATE["all_tasks"] = parse_backlog()
    while True:
        if SENTINEL.ledger_path.exists():
            with SENTINEL.ledger_path.open("r") as f:
                UI_STATE["total_cost"] = 0
                for line in f:
                    try:
                        tx = json.loads(line)
                        UI_STATE["total_cost"] += tx.get("cost_usd", 0.0)
                        for t in UI_STATE["all_tasks"]:
                            if t["id"] == tx["task_id"]:
                                if tx["event"] == "success":
                                    t["status"] = "Success"
                                elif tx["event"] == "hard_block":
                                    t["status"] = "HARD_BLOCK"
                                elif "attempt" in tx["event"]:
                                    t["status"] = "Running"
                                    UI_STATE["active_task"] = t
                        if tx["event"] == "debate_completed":
                            UI_STATE["debate_transcript"].append(
                                ("ARCHITECT", tx["details"]["decision"])
                            )
                    except Exception:
                        continue
        update_ui_components(layout)
        await asyncio.sleep(1)


async def main() -> None:
    """Executes the main application loop for the Apex dispatcher.

    The application operates in one of two modes, configured via command-line
    arguments passed to `sys.argv`:

    - Monitor mode (invoked with `--monitor`): Displays a real-time,
      non-interactive dashboard of task statuses without executing any tasks.
    - Worker mode (default): Parses a task backlog and processes each task
      sequentially. A terminal user interface is displayed unless the
      `--headless` flag is provided.

    The worker mode's primary loop iterates through the task list, skipping any
    tasks with a terminal status ('success', 'hard_block'). For each viable
    task, it delegates to `process_task` and updates the UI with progress and
    cost information. The loop contains a specific control flow for emergent
    tasks: if a task's status transitions to 'Waiting EMG', the loop counter
    is not incremented for that cycle. This mechanism forces an immediate
    re-evaluation of the task list, ensuring that a newly prioritized
    emergency task is processed in the subsequent iteration.

    Returns:
        None

    Raises:
        FileNotFoundError: If the backlog data source cannot be found by the
            `parse_backlog` function.
        ValueError: If the backlog data is malformed or its format is invalid.
    """
    mode = "monitor" if "--monitor" in sys.argv else "worker"
    layout = make_layout()
    if mode == "monitor":
        with Live(layout, refresh_per_second=2, screen=True):
            await monitor_mode(layout)
        return
    UI_STATE["all_tasks"] = parse_backlog()
    with Live(layout, refresh_per_second=2, screen="--headless" not in sys.argv):
        i = 0
        while i < len(UI_STATE["all_tasks"]):
            task = UI_STATE["all_tasks"][i]
            if SENTINEL.get_task_status(task["id"]) in ["success", "hard_block"]:
                i += 1
                continue
            if "--headless" not in sys.argv:
                update_ui_components(layout)
            await process_task(task, UI_STATE["all_tasks"], i)
            UI_STATE["total_cost"] = SENTINEL.total_cost
            if "--headless" not in sys.argv:
                update_ui_components(layout)

            # The loop counter `i` is intentionally not incremented when a task transitions to the 'Waiting EMG' state. This control flow manipulation ensures that the newly prepended emergency task is evaluated in the immediately following loop iteration.
            #
            if task["status"] != "Waiting EMG":
                i += 1


if __name__ == "__main__":
    asyncio.run(main())
