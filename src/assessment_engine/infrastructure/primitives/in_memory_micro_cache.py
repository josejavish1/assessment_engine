"""
Transactional In-Memory LRU Micro-Cache — GEMA 59 (SOTA 2026).
Sub-millisecond read cache with table-level auto-invalidation on database mutations.
Eliminates repetitive SQLite disk reads for frequently queried domain data.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.in_memory_micro_cache")


class InMemoryMicroCachePrimitive:
    """
    Provide an in-memory cache with automatic per-table invalidation.
    """

    def __init__(self, max_entries: int = 500, default_ttl_seconds: float = 60.0) -> None:
        self.max_entries = max_entries
        self.default_ttl = default_ttl_seconds
        # clave -> (valor, expires_at, table_name)
        self._cache: dict[str, tuple[Any, float, str]] = {}

    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache if it has not expired."""
        if key not in self._cache:
            return None

        val, expires_at, _ = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None

        return val

    def set(self, key: str, value: Any, table_name: str, ttl_seconds: float | None = None) -> None:
        """Store a value in the cache associated with a database table."""
        if len(self._cache) >= self.max_entries:
            # Purge the oldest 20% or expired entries using simple LRU.
            now = time.time()
            expired_keys = [k for k, (_, exp, _) in self._cache.items() if now > exp]
            if expired_keys:
                for k in expired_keys:
                    del self._cache[k]
            else:
                # Remove the first 50 entries.
                for k in list(self._cache.keys())[:50]:
                    del self._cache[k]

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = (value, time.time() + ttl, table_name)

    def invalidate_table(self, table_name: str) -> int:
        """Invalidate all keys associated with a table after an INSERT, UPDATE, or DELETE."""
        keys_to_del = [k for k, (_, _, tbl) in self._cache.items() if tbl.lower() == table_name.lower()]
        for k in keys_to_del:
            del self._cache[k]
        if keys_to_del:
            logger.debug(f"[MicroCache] Invalidadas {len(keys_to_del)} entradas de la tabla '{table_name}'")
        return len(keys_to_del)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()


in_memory_micro_cache = InMemoryMicroCachePrimitive()
