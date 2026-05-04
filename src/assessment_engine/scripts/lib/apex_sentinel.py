import json
import logging
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("Apex-Sentinel")

class ApexTransaction(BaseModel):
    task_id: str
    event: str  # e.g., "started", "failed", "debate_started", "debate_approved", "success"
    details: dict[str, Any]
    timestamp: float
    cost_usd: float = 0.0

class ApexSentinel:
    """Gestiona el Ledger persistente y las cuotas de FinOps (Circuit Breaker)."""
    
    def __init__(self, working_dir: Path, budget_limit: float = 10.0):
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
        
        logger.info(f"Sentinel: Estado cargado. Coste total acumulado: ${self.total_cost:.4f}")

    def log_transaction(self, task_id: str, event: str, details: dict[str, Any], cost: float = 0.0):
        import time
        tx = ApexTransaction(
            task_id=task_id,
            event=event,
            details=details,
            timestamp=time.time(),
            cost_usd=cost
        )
        self.total_cost += cost
        
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(tx.model_dump_json() + "\n")
        
        if self.total_cost > self.budget_limit:
            raise RuntimeError(f"CIRCUIT BREAKER: El presupuesto de Apex (${self.budget_limit}) ha sido superado. Deteniendo ejecución por seguridad.")

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Busca el último estado registrado para una tarea específica."""
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
