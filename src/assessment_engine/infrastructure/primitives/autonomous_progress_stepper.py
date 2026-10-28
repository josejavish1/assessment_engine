"""
Autonomous Progress Stepper & Human Milestone Tracker — GEMA 79 (Tier-1 SOTA 2026).
Tracks the 5 canonical human-readable progress milestones during autonomous application synthesis:
1. Ontology & Database (SQLite WAL)
2. Transactional Endpoints & APIs (FastAPI)
3. Visual UI Synthesis (React + Tailwind)
4. Quality & Governance Gates (AST + Radon V(G)<=10)
5. Live Edge Deployment & Empirical Verification

Strictly adheres to NIST SP 500-235 for McCabe Cyclomatic Complexity V(G) <= 10.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.autonomous_progress_stepper")

logger = logging.getLogger("assessment_engine.infrastructure.primitives.autonomous_progress_stepper")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))

CANONICAL_STEPS = [
    {
        "id": "ontology_db",
        "title": "Ontología & Base de Datos",
        "description": "Modelado de entidades y tablas relacionales en SQLite WAL",
        "status": "pending",
        "progress_weight": 20,
    },
    {
        "id": "backend_logic",
        "title": "Lógica Transaccional & APIs",
        "description": "Contratos REST, esquemas Pydantic y lógica de negocio en FastAPI",
        "status": "pending",
        "progress_weight": 20,
    },
    {
        "id": "visual_ui",
        "title": "Síntesis Visual & Componentes",
        "description": "Ensamblado de vistas reactivas con tokens semánticos de Tailwind",
        "status": "pending",
        "progress_weight": 25,
    },
    {
        "id": "quality_gate",
        "title": "Control de Calidad & Gobernanza",
        "description": "Verificación de compuertas AST, accesibilidad WCAG y Radon V(G)<=10",
        "status": "pending",
        "progress_weight": 20,
    },
    {
        "id": "live_deployment",
        "title": "Despliegue en Vivo & Verificación",
        "description": "Comprobación empírica HTTP de rutas y entrega de URL de producción",
        "status": "pending",
        "progress_weight": 15,
    },
]


class AutonomousProgressStepperPrimitive(CapabilityPrimitive):
    """Orchestrates human-readable progress stepping and SSE event streaming."""

    def __init__(self, workspaces_dir: Path | None = None) -> None:
        self.workspaces_dir = workspaces_dir or WORKSPACES_DIR
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}

    @property
    def namespace(self) -> str:
        """Return the unique namespace identifier for the capability."""
        return "progress_stepper"

    def get_capabilities(self) -> dict[str, Any]:
        """Expose capability metadata and operations schema."""
        return {
            "version": "1.0.0",
            "steps_count": len(CANONICAL_STEPS),
            "features": ["milestone_progress", "sse_streaming", "duration_tracking", "atomic_persistence"],
        }

    def subscribe(self, slug: str) -> asyncio.Queue[dict[str, Any]]:
        """Subscribe to live milestone updates for a given project slug."""
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(slug, set()).add(q)
        return q

    def unsubscribe(self, slug: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Unsubscribe from live updates."""
        if slug in self._subscribers:
            self._subscribers[slug].discard(queue)
            if not self._subscribers[slug]:
                del self._subscribers[slug]

    def _get_tracker_file(self, slug: str) -> Path:
        clean_slug = re.sub(r"[^\w.-]", "", slug)
        data_dir = self.workspaces_dir / clean_slug / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "progress_tracker.json"

    def create_tracker(self, slug: str, prompt: str) -> dict[str, Any]:
        """Initialize a new 5-step milestone tracking session."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        initial_steps = [dict(s) for s in CANONICAL_STEPS]

        tracker_data = {
            "slug": slug,
            "prompt": prompt,
            "overall_progress_pct": 0,
            "status": "IN_PROGRESS",
            "active_step_id": initial_steps[0]["id"],
            "started_at": now,
            "updated_at": now,
            "steps": initial_steps,
        }

        tracker_file = self._get_tracker_file(slug)
        tracker_file.write_text(json.dumps(tracker_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return tracker_data

    def get_progress(self, slug: str) -> dict[str, Any]:
        """Retrieve the current milestone progress snapshot for a project."""
        tracker_file = self._get_tracker_file(slug)
        if not tracker_file.exists():
            return self.create_tracker(slug, "Generación autónoma inicial")

        try:
            return json.loads(tracker_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return self.create_tracker(slug, "Recuperación de sesión")

    def _update_step_data(self, step: dict[str, Any], status: str, summary: str | None, duration_ms: float | None) -> None:
        """Helper to update step attributes, keeping V(G) low."""
        step["status"] = status
        if summary:
            step["summary"] = summary
        if duration_ms is not None:
            step["duration_ms"] = round(duration_ms, 1)

    def _calculate_step_weight(self, step: dict[str, Any]) -> int:
        """Helper to calculate progress weight based on status, keeping V(G) low."""
        status = step.get("status")
        weight = step.get("progress_weight", 20)
        if status == "completed":
            return weight
        if status == "in_progress":
            return int(weight * 0.5)
        return 0

    def update_step(
        self,
        slug: str,
        step_id: str,
        status: str,
        summary: str | None = None,
        duration_ms: float | None = None,
    ) -> dict[str, Any]:
        """Atomically update status of a milestone step and calculate overall completion percentage."""
        tracker = self.get_progress(slug)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        step_found = False
        calc_pct = 0

        for step in tracker.get("steps", []):
            if step["id"] == step_id:
                self._update_step_data(step, status, summary, duration_ms)
                step_found = True
            
            calc_pct += self._calculate_step_weight(step)

        if not step_found:
            raise ValueError(f"Hito no reconocido: '{step_id}'")

        tracker["overall_progress_pct"] = min(100, calc_pct)
        tracker["updated_at"] = now
        tracker["active_step_id"] = step_id

        if tracker["overall_progress_pct"] >= 100:
            tracker["status"] = "COMPLETED"

        tracker_file = self._get_tracker_file(slug)
        tracker_file.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")

        for q in list(self._subscribers.get(slug, set())):
            try:
                q.put_nowait(tracker)
            except Exception as ex:
                logger.debug(f"[ProgressStepper] Error notificando suscriptor: {ex}")

        return tracker

    def to_sse_event(self, tracker: dict[str, Any]) -> str:
        """Format tracking state into a standard W3C Server-Sent Event."""
        payload = json.dumps(tracker, ensure_ascii=False)
        return f"event: milestone_progress\ndata: {payload}\n\n"


autonomous_progress_stepper = AutonomousProgressStepperPrimitive()