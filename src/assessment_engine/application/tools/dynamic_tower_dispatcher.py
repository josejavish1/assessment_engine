from __future__ import annotations

import asyncio
import importlib
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

TowerRunner = Callable[[str], Awaitable[Any]]

_DEFAULT_TOPOLOGY: dict[str, set[str]] = {
    "T6": {"T1"},
    "T5": {"T2"},
    "T3": {"T2"},
}

_SERVICE_MODULE_CANDIDATES: tuple[str, ...] = (
    "assessment_engine.infrastructure.epistemic_graph_service",
    "assessment_engine.domain.services.epistemic_graph_service",
    "assessment_engine.domain.epistemic_graph_service",
    "assessment_engine.application.services.epistemic_graph_service",
    "assessment_engine.services.epistemic_graph_service",
)


class _FallbackEpistemicGraphService:
    """Deterministic fallback graph service when external domain module is absent."""

    def __init__(self, industry_profile: str = "default") -> None:
        self.industry_profile = industry_profile
        self.graph: dict[str, set[str]] = {
            k: set(v) for k, v in _DEFAULT_TOPOLOGY.items()
        }

    def get_induced_subgraph(
        self, requested_towers: list[str]
    ) -> dict[str, set[str]]:
        requested_set = set(requested_towers)
        return {
            src: {dst for dst in targets if dst in requested_set}
            for src, targets in self.graph.items()
            if src in requested_set
        }


def _resolve_epistemic_graph_service_cls() -> type[Any]:
    """Resolves EpistemicGraphService across package layouts or returns fallback."""
    for mod_name in _SERVICE_MODULE_CANDIDATES:
        try:
            module = importlib.import_module(mod_name)
            cls = getattr(module, "EpistemicGraphService", None)
            if cls is not None:
                return cls
        except ImportError:
            continue
    return _FallbackEpistemicGraphService


EpistemicGraphService = _resolve_epistemic_graph_service_cls()


@dataclass(frozen=True)
class TowerExecutionResult:
    """Immutable result structure for individual tower execution."""

    tower_id: str
    success: bool
    duration_seconds: float
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _normalize_graph_representation(raw: Any) -> dict[str, set[str]]:
    """Normalizes graph representation (dict or edge iterable) to adjacency map."""
    resolved = raw() if callable(raw) else raw
    if isinstance(resolved, dict):
        return {str(k): {str(i) for i in v} for k, v in resolved.items() if v}
    edges = getattr(resolved, "edges", resolved)
    edges = edges() if callable(edges) else edges
    if not isinstance(edges, (list, tuple, set)):
        return {}
    result: dict[str, set[str]] = {}
    for edge in edges:
        if isinstance(edge, (tuple, list)) and len(edge) >= 2:
            result.setdefault(str(edge[0]), set()).add(str(edge[1]))
    return result


class DynamicTowerDispatcher:
    """
    Reactive topological dispatcher for epistemic towers.
    Computes the induced subgraph for requested towers and schedules execution
    bounded by an asyncio Semaphore, dynamically unlocking dependent towers as
    prerequisites finish.
    """

    def __init__(
        self,
        requested_towers: list[str],
        industry_profile: str = "default",
        max_concurrency: int = 4,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")

        self.requested_towers: list[str] = list(dict.fromkeys(requested_towers))
        self.industry_profile: str = industry_profile
        self.max_concurrency: int = max_concurrency
        self.graph_service = EpistemicGraphService(industry_profile=industry_profile)

        self._dependents: dict[str, set[str]] = {
            t: set() for t in self.requested_towers
        }
        self._in_degrees: dict[str, int] = {t: 0 for t in self.requested_towers}
        self._build_induced_subgraph()

    def _build_induced_subgraph(self) -> None:
        """Extracts the induced subgraph for the requested towers."""
        requested_set = set(self.requested_towers)
        adj = self._extract_adjacency_map()
        for src, targets in adj.items():
            if src in requested_set:
                self._register_targets(src, targets, requested_set)

    def _register_targets(
        self, src: str, targets: set[str], requested_set: set[str]
    ) -> None:
        """Registers valid induced edges originating from src."""
        for dst in targets:
            if dst in requested_set and dst != src and dst not in self._dependents[src]:
                self._dependents[src].add(dst)
                self._in_degrees[dst] += 1

    def _extract_adjacency_map(self) -> dict[str, set[str]]:
        """Resolves edges from EpistemicGraphService across possible API conventions."""
        if hasattr(self.graph_service, "get_induced_subgraph"):
            sub = self.graph_service.get_induced_subgraph(self.requested_towers)
            return _normalize_graph_representation(sub)
        raw = getattr(self.graph_service, "graph", None)
        return _normalize_graph_representation(raw) or dict(_DEFAULT_TOPOLOGY)

    def get_initial_ready_towers(self) -> list[str]:
        """Returns towers with in-degree 0 in the induced subgraph, preserving request order."""
        return [t for t in self.requested_towers if self._in_degrees.get(t, 0) == 0]

    async def execute_all(
        self, runner: TowerRunner
    ) -> dict[str, TowerExecutionResult]:
        """
        Executes all requested towers in topological order with bounded concurrency.
        Unlocks dependent towers reactively as prerequisites complete.
        """
        if not self.requested_towers:
            return {}

        initial_ready = self.get_initial_ready_towers()
        if not initial_ready:
            raise ValueError("Cycle detected in induced epistemic tower subgraph.")

        results = await self._run_execution_loop(initial_ready, runner)
        if len(results) < len(self.requested_towers):
            raise ValueError("Cycle detected in induced epistemic tower subgraph.")
        return results

    async def _run_execution_loop(
        self, initial_ready: list[str], runner: TowerRunner
    ) -> dict[str, TowerExecutionResult]:
        """Coordinates the asynchronous task queue until all reachable towers complete."""
        semaphore = asyncio.Semaphore(self.max_concurrency)
        in_degrees = dict(self._in_degrees)
        results: dict[str, TowerExecutionResult] = {}
        active_tasks = {
            asyncio.create_task(
                self._run_single_tower(t, runner, semaphore, results)
            )
            for t in initial_ready
        }

        while active_tasks:
            done, active_tasks = await asyncio.wait(
                active_tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for t in self._collect_unlocked_towers(done, in_degrees):
                active_tasks.add(
                    asyncio.create_task(
                        self._run_single_tower(t, runner, semaphore, results)
                    )
                )

        return results

    def _collect_unlocked_towers(
        self,
        done_tasks: set[asyncio.Task[str]],
        in_degrees: dict[str, int],
    ) -> list[str]:
        """Decrements in-degrees for dependents of finished tasks and returns ready ones."""
        unlocked: list[str] = []
        for task in done_tasks:
            for dep in self._dependents.get(task.result(), set()):
                in_degrees[dep] -= 1
                if in_degrees[dep] == 0:
                    unlocked.append(dep)
        return unlocked

    async def _run_single_tower(
        self,
        tower_id: str,
        runner: TowerRunner,
        semaphore: asyncio.Semaphore,
        results: dict[str, TowerExecutionResult],
    ) -> str:
        """Executes a single tower within the concurrency semaphore and records duration."""
        async with semaphore:
            results[tower_id] = await self._execute_and_measure(tower_id, runner)
            return tower_id

    async def _execute_and_measure(
        self, tower_id: str, runner: TowerRunner
    ) -> TowerExecutionResult:
        """Runs the tower callable and wraps output or exception with timing metrics."""
        start_ts = time.perf_counter()
        try:
            raw_result = await runner(tower_id)
            elapsed = time.perf_counter() - start_ts
            return self._coerce_result(tower_id, raw_result, elapsed)
        except Exception as exc:
            elapsed = time.perf_counter() - start_ts
            return TowerExecutionResult(
                tower_id=tower_id,
                success=False,
                duration_seconds=elapsed,
                error=str(exc),
            )

    @staticmethod
    def _coerce_result(
        tower_id: str, raw_result: Any, measured_duration: float
    ) -> TowerExecutionResult:
        """Ensures the runner output is wrapped in a valid TowerExecutionResult."""
        if not isinstance(raw_result, TowerExecutionResult):
            return TowerExecutionResult(
                tower_id=tower_id,
                success=True,
                duration_seconds=measured_duration,
                output=raw_result,
            )

        duration = (
            raw_result.duration_seconds
            if raw_result.duration_seconds > 0
            else measured_duration
        )
        return TowerExecutionResult(
            tower_id=raw_result.tower_id,
            success=raw_result.success,
            duration_seconds=duration,
            output=raw_result.output,
            error=raw_result.error,
            metadata=raw_result.metadata,
        )