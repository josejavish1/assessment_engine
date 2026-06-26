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

from assessment_engine.infrastructure.ai_client import call_agent
from assessment_engine.infrastructure.apex_models import ApexDebateResponse
from assessment_engine.infrastructure.apex_sentinel import ApexSentinel

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
    """Define the dictionary structure for a task object."""

    id: str
    priority: str
    title: str
    description: str
    status: str
    instruction: Optional[str]


class UiState(TypedDict):
    """A TypedDict that specifies the data structure for the user interface state.

    This class serves as a data transfer object (DTO) to encapsulate all
    necessary information for rendering the UI at a given point in time.

    Attributes:
        all_tasks: A list of all `Task` objects managed by the system.
        active_task: The `Task` object currently being processed, or `None` if no
            task is active.
        active_logs: A list of string log messages associated with the
            `active_task`.
        debate_transcript: A chronological record of a debate, represented as a
            list of tuples, where each tuple contains a speaker's name (str)
            and their message (Any).
        total_cost: The cumulative computational or monetary cost incurred during
            the session.
        start_time: The UNIX timestamp (seconds since epoch) marking the start of
            the process.
        completed_count: The total number of tasks that have been successfully
            completed.
        last_event: A human-readable string describing the most recent
            significant event.
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

    Locates and parses a prompt configuration file from the prompt registry. The
    search path is resolved by first checking the `APEX_PROMPTS_DIR`
    environment variable for a custom registry path. If the environment
    variable is not set, the function falls back to the default
    package-internal prompt registry.

    Args:
        filename: The basename of the YAML prompt file to load.

    Returns:
        A dictionary representing the parsed content of the YAML file.

    Raises:
        FileNotFoundError: If the prompt file cannot be found in the resolved
            search path.
        yaml.YAMLError: If the target file contains malformed YAML.
    """
    import yaml  # type: ignore

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
    """Define and return the primary Rich Layout for the application UI."""
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
    r"""{'docstring': "Populates a Rich Layout with data from the global UI state.\n\n    This function renders a complete terminal UI frame by updating distinct\n    panels within the provided layout object. It sources all data from the\n    global `UI_STATE` dictionary, making it suitable for repeated calls in a\n    refresh loop.\n\n    The function updates the following layout panels:\n    - 'header': Displays cost, progress, and uptime statistics.\n    - 'active_mission': Shows the currently executing task.\n    - 'brain_stream': Renders the latest agent thought processes.\n    - 'terminal_mirror': Mirrors recent log output.\n    - 'registry': Lists the backlog of upcoming and completed tasks.\n    - 'footer': Shows the last logged event or UI error messages.\n\n    Any exceptions encountered during the rendering process are caught and their\n    message is displayed in the 'footer' panel to prevent UI crashes.\n\n    Args:\n        layout: The `rich.layout.Layout` object to be updated in-place."}."""
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
    r"""{'docstring': "Asynchronously executes the 'po-run' orchestrator script with a task prompt.\n\n    The function sanitizes the input `task_prompt` by removing newlines and\n    escaping double quotes. It then launches the 'po-run' script as an\n    asynchronous subprocess, passing the sanitized prompt as a command-line\n    argument. Standard error is redirected to standard output, and the\n    `PYTHONUNBUFFERED` environment variable is set to facilitate real-time\n    output streaming.\n\n    Output from the subprocess is captured line-by-line. Each line is appended\n    to a persistent `session.log` file and simultaneously used to populate the\n    global `UI_STATE['active_logs']` list for real-time interface updates.\n    The function awaits the termination of the subprocess before returning.\n\n    Args:\n        task_prompt: The task description to be processed by the orchestrator.\n\n    Returns:\n        A tuple containing a boolean success flag (True if the process exit code\n        was 0) and the complete captured standard output as a single string,\n        with each line stripped of whitespace.\n\n    Raises:\n        FileNotFoundError: If the 'po-run' executable is not found.\n        PermissionError: If the script lacks permissions to execute 'po-run' or\n            write to the log file."}."""
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
    """Orchestrates a simulated two-agent debate to determine an error recovery strategy.

    This function simulates a multi-step reasoning process within a single large-
    language model call to decide on a recovery strategy for a given error. A
    prompt for an "Apex Doctor" persona is first generated, which analyzes the
    error logs and previous failures to formulate a proposed fix. This proposal is
    then embedded into a larger prompt for an "Apex Architect" persona. The
    architect evaluates the doctor's proposal against high-level repository
    invariants loaded from `GEMINI.md` to make a final, authoritative decision.

    The function appends status updates to the global `UI_STATE` transcript and
    logs the final decision and reasoning as a transaction.

    Args:
        error_logs: The raw error log output from the failed execution. This
            input is truncated to the first 1500 characters within the prompt.
        previous_failures: A textual description of previously attempted fixes
            that were unsuccessful.

    Returns:
        An `ApexDebateResponse` object containing the final decision and the
        supporting reasoning from the architect persona.

    Raises:
        FileNotFoundError: If `apex_doctor.yaml`, `apex_architect.yaml`, or the
            repository invariants file (`GEMINI.md`) cannot be found.
        pydantic.ValidationError: If the response from the language model does
            not conform to the `ApexDebateResponse` schema.
    """
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
    """Parses a Markdown-formatted backlog file into a list of Task objects.

    Reads and parses the backlog file specified by the global `BACKLOG_PATH`
    constant. The file is expected to contain a Markdown table with columns for
    priority, area, title, and description. A regular expression is used to
    extract data from each row, skipping the table header and formatting lines.
    Each valid entry is transformed into a `Task` dictionary with a generated ID
    and a default "Pending" status.

    Returns:
        A list of `Task` dictionaries. An empty list is returned if the
        backlog file does not exist or if no valid task entries are found.

    Raises:
        OSError: If the backlog file cannot be read due to filesystem errors,
            such as insufficient permissions.
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
    """Executes a task with an adaptive, multi-attempt failure-recovery loop.

    This function attempts to execute a task using an external orchestrator.
    Upon failure, it initiates a rescue protocol that runs for a maximum of
    `max_rescue_rounds`. In each round, a 'debate' mechanism analyzes the
    failure logs to determine a recovery strategy. The possible outcomes are:

    1.  **Revise and Retry**: The task's instructions are revised based on the
        analysis, and another execution attempt is made.
    2.  **Inject Prerequisite**: New, high-priority 'Emergency' (EMG) tasks are
        generated and inserted into the main `queue` at the specified `idx`.
        The current task's status is updated to 'Waiting EMG' and execution is
        deferred (returns False).
    3.  **Hard Block**: The task is deemed unrecoverable, its status is set to
        'HARD_BLOCK', and all further attempts are ceased.

    The function has significant side effects, directly mutating the state of the
    `task` object, the `queue` list, and the global `UI_STATE` dictionary.

    Args:
        task: The task object to process. Its 'status' and 'instruction'
            attributes are mutated in-place during execution.
        queue: The primary task queue (a list of tasks). This list is modified
            in-place if prerequisite tasks need to be injected.
        idx: The index in the `queue` at which new prerequisite tasks will be
            inserted.

    Returns:
        True if the task completes successfully. False if the task is deferred,
        fails after all retry attempts, or is marked as a 'HARD_BLOCK'.

    Raises:
        SystemExit: If a prerequisite task of 'EMG' priority fails and is
            subsequently hard-blocked, indicating a critical failure that
            necessitates immediate termination of the application.
    """
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
            # A rescue counter is employed to prevent infinite loops during task recovery sequences.
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
                    # Prevents duplicate task insertion when the emergency queue and the main task list reference the same object instance.
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
    """Asynchronously polls a ledger file to update application state and refresh the UI.

    Initializes the application's task list by parsing the backlog, then enters an
    infinite loop to monitor for state changes.

    The loop polls the ledger file specified by `SENTINEL.ledger_path` at one-second
    intervals. The function reads the file line-by-line, parsing each line as a
    JSON transaction. Malformed lines that raise an exception during parsing are
    silently skipped. Based on the contents of valid transactions, this function
    mutates the shared `UI_STATE` dictionary, updating task statuses, aggregate
    costs, and debate transcripts. After each polling cycle, it triggers a refresh
    of the user interface components.

    Args:
        layout (Layout): The main UI layout object to be refreshed with updated
            state information.

    Returns:
        None: This function runs in an infinite loop and does not return.
    """
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
    """Runs the main asynchronous event loop for the Apex dispatcher.

    The application operates in one of two modes, selected via command-line
    arguments:
    - "monitor": Activated by the `--monitor` flag. This mode displays a
      real-time terminal dashboard monitoring the state of the task
      processing system.
    - "worker": The default mode. This mode parses a task backlog file and
      processes the tasks sequentially. The UI can be suppressed by passing
      the `--headless` flag.

    In worker mode, the function iterates through the list of tasks. It
    skips tasks with a status of "success" or "hard_block". For each
    pending task, it calls the `process_task` coroutine and updates the UI
    with the current status and cumulative cost. If a task's status becomes
    "Waiting EMG", the loop does not advance to the next task in the
    subsequent iteration. This mechanism ensures that an emergency task,
    which is injected into the queue at the current position, is processed
    immediately.

    Raises:
        FileNotFoundError: If the backlog file cannot be found in worker mode.
        ValueError: If the backlog file contains malformed data.
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

            # The loop counter 'i' is not incremented upon a task's transition to the 'Waiting EMG' state to ensure the newly injected emergency task is processed in the immediately subsequent iteration.
            #
            if task["status"] != "Waiting EMG":
                i += 1


if __name__ == "__main__":
    asyncio.run(main())
