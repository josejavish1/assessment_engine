"""
In-Memory IP Rate Limiting & Anti-Abuse Primitive — GEMA 17 (SOTA 2026).
Sliding-window rate limiter per client IP.
Protects sensitive endpoints (auth, cognitive ingest, payments) against brute force and DoS.
Zero external Redis dependency needed.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("assessment_engine.infrastructure.primitives.rate_limiter")


class RateLimiterPrimitive:
    """
    Limit request rates using a sliding window by IP or key.
    """

    def __init__(self, default_limit: int = 60, default_window_seconds: float = 60.0) -> None:
        self.default_limit = default_limit
        self.default_window = default_window_seconds
        # clave_ip -> lista de timestamps
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, client_key: str, limit: int | None = None, window_seconds: float | None = None) -> tuple[bool, int, float]:
        """Check if the request is allowed. Returns: (allowed, remaining_requests, seconds_to_reset)"""
        max_reqs = limit if limit is not None else self.default_limit
        win = window_seconds if window_seconds is not None else self.default_window
        now = time.time()
        window_start = now - win

        if client_key not in self._requests:
            self._requests[client_key] = []

        valid_timestamps = [t for t in self._requests[client_key] if t > window_start]
        self._requests[client_key] = valid_timestamps

        if len(valid_timestamps) >= max_reqs:
            oldest = valid_timestamps[0]
            retry_after = max(1.0, oldest + win - now)
            logger.warning(f"[RateLimiter] Límite excedido para '{client_key}' ({len(valid_timestamps)}/{max_reqs}). Retry after {retry_after:.1f}s")
            return False, 0, round(retry_after, 1)

        self._requests[client_key].append(now)
        remaining = max_reqs - len(self._requests[client_key])
        return True, remaining, 0.0

    def reset(self, client_key: str | None = None) -> None:
        """Reset the request counter."""
        if client_key:
            self._requests.pop(client_key, None)
        else:
            self._requests.clear()


rate_limiter = RateLimiterPrimitive()
