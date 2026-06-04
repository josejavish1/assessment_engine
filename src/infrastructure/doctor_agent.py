from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DoctorAgent:
    """Agente supervisor Tier-1 para autocuración de fallos."""

    @classmethod
    async def diagnose(
        cls, plan: Dict[str, Any], task: Dict[str, Any], error_log: str
    ) -> Dict[str, Any]:
        return {"status": "SAFE"}
