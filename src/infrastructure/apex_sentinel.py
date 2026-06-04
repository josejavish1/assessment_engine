from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class ApexSentinel:
    """Sentinel industrial Tier-1 para gobernanza de agentes."""

    def __init__(self, working_dir: Path, budget_limit: float = 25.0):
        self.working_dir = working_dir
        self.budget_limit = budget_limit
        self.total_cost = 0.0

    def log_transaction(
        self, task_id: str, event: str, details: Dict[str, Any], cost: float = 0.0
    ) -> None:
        pass
