"""
Full Jitter Exponential Backoff SRE Pattern — GEMA 68 (AWS Architecture / SOTA 2026).
Implements resilient async retries with exponential backoff and randomized decorrelated jitter.
Prevents thundering herd problems when interacting with external LLMs or third-party APIs.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Callable

logger = logging.getLogger("assessment_engine.infrastructure.primitives.exponential_backoff_jitter")


class ExponentialBackoffJitterPrimitive:
    """
    Execute resilient retries with full jitter.
    """

    async def execute_with_retry(
        self,
        func: Callable[[], Any],
        max_attempts: int = 4,
        base_delay_seconds: float = 0.5,
        max_delay_seconds: float = 8.0
    ) -> Any:
        """Execute an asynchronous or synchronous function with retries and random jitter."""
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                return func()
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                last_exception = ex
                if attempt == max_attempts:
                    logger.error(f"[FullJitter] Agotados {max_attempts} intentos. Fallo definitivo: {ex}")
                    raise

                calculated_delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
                jitter_delay = random.uniform(0.1, calculated_delay)

                logger.warning(f"[FullJitter] Intento {attempt}/{max_attempts} falló ({ex}). Reintentando en {jitter_delay:.2f}s...")
                await asyncio.sleep(jitter_delay)

        raise last_exception if last_exception else RuntimeError("Retry loop exited abnormally")


exponential_backoff_jitter = ExponentialBackoffJitterPrimitive()
