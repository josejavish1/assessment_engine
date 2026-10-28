"""
Execute optimistic state transitions with immutable snapshotting and deterministic rollback on precondition failure (HTTP 412, ETag, or network error).
"""
from __future__ import annotations
import copy
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar
logger = logging.getLogger('core.evolution.optimistic_action')
T = TypeVar('T')
R = TypeVar('R')

@dataclass(frozen=False)
class OptimisticExecutionResult(Generic[R]):
    """Represent the result of an optimistic action execution."""
    success: bool
    data: R | None
    error: str | None
    rolled_back: bool

class OptimisticActionEngine(Generic[T]):
    """Manage optimistic state with guaranteed automatic rollback."""

    def __init__(self, initial_state: T) -> None:
        self._current_state = copy.deepcopy(initial_state)

    @property
    def current_state(self) -> T:
        """Return the current state."""
        return self._current_state

    def execute(self, mutation_fn: Callable[[T], T], remote_operation: Callable[[], R]) -> OptimisticExecutionResult[R]:
        """Execute the local optimistic mutation and then invoke the remote operation.
If the remote operation fails, unconditionally restore the previous snapshot."""
        snapshot = copy.deepcopy(self._current_state)
        draft = copy.deepcopy(self._current_state)
        try:
            self._current_state = mutation_fn(draft)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f'[OptimisticAction] Fallo en mutación local: {ex}')
            self._current_state = snapshot
            return OptimisticExecutionResult(success=False, data=None, error=str(ex), rolled_back=True)
        try:
            result = remote_operation()
            return OptimisticExecutionResult(success=True, data=result, error=None, rolled_back=False)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f'[OptimisticAction] Fallo remoto, revirtiendo estado: {ex}')
            self._current_state = snapshot
            return OptimisticExecutionResult(success=False, data=None, error=str(ex), rolled_back=True)
__all__ = ['OptimisticActionEngine', 'OptimisticExecutionResult']