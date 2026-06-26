import json
import logging
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger("Apex-Sentinel")


class ApexTransaction(BaseModel):
    r"""{'docstring': "Represents a single transactional event within a task's lifecycle.\n\n    This Pydantic model captures a discrete state transition or action for a\n    specific task, along with associated metadata such as timing, cost, and\n    contextual details. Each instance serves as an immutable record of a step\n    in the task's execution history.\n\n    Attributes:\n        task_id: The unique identifier for the task to which this transaction\n            belongs.\n        event: The name of the event, representing a state in the task's state\n            machine. This attribute governs the control flow and operational\n            logic.\n        details: A dictionary containing arbitrary key-value data relevant to the\n            event.\n        timestamp: The UTC Unix timestamp indicating when the event occurred.\n        cost_usd: The monetary cost associated with this transaction in USD.\n            Defaults to 0.0."}."""

    task_id: str
    event: str  # Defines the discrete states within the task's state machine. These states govern the control flow and operational logic for task execution and resolution.
    details: dict[str, Any]
    timestamp: float
    cost_usd: float = 0.0


class ApexSentinel:
    r"""[{'target': 'ApexSentinel', 'docstring': 'Tracks financial operations against a predefined budget, acting as a circuit breaker.\n\n    This class provides an interface for logging financial transactions to a\n    persistent JSONL ledger file. It maintains a running total of costs and\n    implements a circuit breaker pattern: if a transaction causes the total\n    cost to exceed a specified budget limit, it raises a RuntimeError to halt\n    execution and prevent further spending. State is persisted across multiple\n    runs by loading the ledger upon initialization.\n\n    Attributes:\n        working_dir: The `pathlib.Path` object for the directory where the\n            ledger file is stored.\n        ledger_path: The full `pathlib.Path` to the `apex_ledger.jsonl`\n            ledger file.\n        budget_limit: The maximum cumulative cost in USD before the circuit\n            breaker is triggered.\n        total_cost: The current cumulative cost in USD, loaded from the ledger\n            and updated with each new transaction.'}, {'target': '__init__', 'docstring': 'Initializes the ApexSentinel instance.\n\n        Ensures the working directory exists, sets the budget limit, and loads\n        any pre-existing state from the ledger file to compute the initial\n        cumulative cost.\n\n        Args:\n            working_dir: The directory path for storing the `apex_ledger.jsonl` file.\n            budget_limit: The maximum cumulative cost in USD. If this limit is\n                exceeded, a `RuntimeError` will be raised by `log_transaction`.\n                Defaults to 10.0.\n\n        Raises:\n            PermissionError: If the `working_dir` cannot be created due to\n                insufficient filesystem permissions.'}, {'target': '_load_state', 'docstring': 'Calculates the total cost by reading and summing transactions from the ledger.\n\n        If the ledger file exists, this method reads it line by line, parsing\n        each line as a JSON object. It aggregates the `cost_usd` value from each\n        valid entry to populate the `total_cost` instance attribute. Lines that\n        contain malformed JSON are silently ignored.'}, {'target': 'log_transaction', 'docstring': "Logs a transaction to the ledger and updates the cumulative cost.\n\n        Appends a new transaction record as a JSON line to the ledger file. After\n        writing the record, it checks if the cumulative cost has exceeded the\n        budget limit. If the limit is surpassed, the method acts as a circuit\n        breaker, raising an exception to halt further operations.\n\n        Args:\n            task_id: A unique identifier for the task associated with the transaction.\n            event: A string describing the event or state (e.g., 'API_CALL').\n            details: A dictionary containing arbitrary structured data about the\n                transaction.\n            cost: The cost of this specific transaction in USD. Defaults to 0.0.\n\n        Raises:\n            RuntimeError: If the cumulative `total_cost` after this transaction\n                exceeds the `budget_limit`.\n            IOError: If the ledger file cannot be opened for writing."}, {'target': 'get_task_status', 'docstring': 'Retrieves the most recent event for a given task ID from the ledger.\n\n        Performs a linear scan of the entire ledger file from beginning to end,\n        returning the `event` string from the last entry that matches the\n        specified `task_id`. This overwriting behavior ensures that the returned\n        status is always the most recent one recorded. Malformed JSON lines or\n        entries missing required keys are silently skipped.\n\n        Args:\n            task_id: The identifier of the task to query.\n\n        Returns:\n            The last recorded event string for the specified task, or None if\n            the ledger file does not exist or if no entry with the given\n            `task_id` is found.'}]."""

    def __init__(self, working_dir: Path, budget_limit: float = 10.0):
        """Initializes the ApexSentinel and its operational environment.

        Establishes the specified working directory for state persistence. The
        constructor sets the operational budget limit and attempts to load any
        pre-existing state from the ledger file (`apex_ledger.jsonl`) found
        within this directory. If the directory does not exist, it is created.

        Args:
            working_dir: The path to the root directory for sentinel operations
                and state storage.
            budget_limit: The maximum cumulative cost allowed for operations
                tracked by this instance.

        Raises:
            PermissionError: If the process lacks the necessary permissions to create
                the `working_dir`.
            OSError: If an I/O error occurs while reading the ledger file.
            ValueError: If the ledger file contains malformed or unparseable data.
        """
        self.working_dir = working_dir
        self.ledger_path = working_dir / "apex_ledger.jsonl"
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self):
        if not self.ledger_path.exists():
            return

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    tx = json.loads(line)
                    self.total_cost += tx.get("cost_usd", 0.0)
                except json.JSONDecodeError:
                    continue

        logger.info(
            f"Sentinel: Estado cargado. Coste total acumulado: ${self.total_cost:.4f}"
        )

    def log_transaction(
        self, task_id: str, event: str, details: dict[str, Any], cost: float = 0.0
    ):
        """Log a transaction to the ledger and check against the budget.

        This method records a transaction by appending its JSON representation to the
        ledger file. It also updates the cumulative cost and triggers a circuit breaker
        by raising a RuntimeError if the total cost surpasses the configured budget
        limit.

        Args:
            task_id: The unique identifier for the task associated with the transaction.
            event: A descriptive name for the event being logged (e.g., 'API_CALL').
            details: A dictionary containing detailed, structured information about
                the event.
            cost: The monetary cost in USD of the transaction. Defaults to 0.0.

        Raises:
            RuntimeError: If the cumulative total cost exceeds the budget limit.
        """
        import time

        tx = ApexTransaction(
            task_id=task_id,
            event=event,
            details=details,
            timestamp=time.time(),
            cost_usd=cost,
        )
        self.total_cost += cost

        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(tx.model_dump_json() + "\n")

        if self.total_cost > self.budget_limit:
            raise RuntimeError(
                f"CIRCUIT BREAKER: El presupuesto de Apex (${self.budget_limit}) ha sido superado. Deteniendo ejecución por seguridad."
            )

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Retrieves the last recorded status for a specified task ID from the ledger.

        The method reads a newline-delimited JSON (NDJSON) file, referred to as
        the ledger, to find the terminal event entry for a specific task. It performs
        a linear scan of the entire file; if multiple entries for the same `task_id`
        exist, the status from the last matching entry is returned. Lines that are
        malformed JSON or lack the required 'task_id' or 'event' keys are
        silently ignored.

        Args:
            task_id (str): The unique identifier for the task whose status is being
                queried.

        Returns:
            Optional[str]: The status string from the last matching record in the
                ledger. Returns None if the ledger file does not exist or if no
                entry for the given task_id is found.
        """
        status = None
        if not self.ledger_path.exists():
            return None

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    tx = json.loads(line)
                    if tx["task_id"] == task_id:
                        status = tx["event"]
                except (json.JSONDecodeError, KeyError):
                    continue
        return status
