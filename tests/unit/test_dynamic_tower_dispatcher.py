from __future__ import annotations

import asyncio
import pytest

from assessment_engine.application.tools.dynamic_tower_dispatcher import (
    DynamicTowerDispatcher,
    TowerExecutionResult,
)


def test_induced_subgraph_and_dependency_resolution():
    """Verify that the dispatcher extracts the induced subgraph and identifies correct ready nodes."""
    dispatcher = DynamicTowerDispatcher(
        requested_towers=["T1", "T2", "T6"],
        industry_profile="critical_infrastructure",
        max_concurrency=3,
    )

    # In critical infrastructure / default:
    # T6 -> T1 is an active edge in induced subgraph.
    # T2's parents in the full graph (T5, T3) are not in the requested set,
    # so T2's in-degree in the induced subgraph is 0.
    ready_initial = dispatcher.get_initial_ready_towers()
    assert "T6" in ready_initial
    assert "T2" in ready_initial
    assert "T1" not in ready_initial  # T1 must wait for T6


def test_independent_towers_run_in_parallel():
    """Verify that disjoint towers have in-degree 0 in the induced subgraph and start concurrently."""
    dispatcher = DynamicTowerDispatcher(
        requested_towers=["T9", "T10"],
        industry_profile="default",
        max_concurrency=2,
    )

    ready_initial = dispatcher.get_initial_ready_towers()
    assert set(ready_initial) == {"T9", "T10"}


def test_single_tower_runs_immediately():
    """Verify that an assessment with a single tower starts immediately."""
    dispatcher = DynamicTowerDispatcher(
        requested_towers=["T4"],
        industry_profile="retail",
        max_concurrency=2,
    )

    ready_initial = dispatcher.get_initial_ready_towers()
    assert ready_initial == ["T4"]


@pytest.mark.asyncio
async def test_dynamic_execution_order_and_concurrency_bounding():
    """Verify that execution respects topological dependencies and does not exceed max_concurrency."""
    dispatcher = DynamicTowerDispatcher(
        requested_towers=["T1", "T2", "T6"],
        industry_profile="default",
        max_concurrency=2,
    )

    start_times = {}
    end_times = {}
    running_counts = []
    current_running = 0

    async def mock_tower_runner(tower_id: str) -> TowerExecutionResult:
        nonlocal current_running
        current_running += 1
        running_counts.append(current_running)
        start_times[tower_id] = asyncio.get_event_loop().time()

        # Simulate execution duration
        await asyncio.sleep(0.05)

        end_times[tower_id] = asyncio.get_event_loop().time()
        current_running -= 1
        return TowerExecutionResult(tower_id=tower_id, success=True, duration_seconds=0.05)

    results = await dispatcher.execute_all(runner=mock_tower_runner)

    assert len(results) == 3
    assert all(r.success for r in results.values())

    # T1 must strictly start AFTER T6 has completed
    assert start_times["T1"] >= end_times["T6"]

    # Concurrency must never exceed max_concurrency (2)
    assert max(running_counts) <= 2
