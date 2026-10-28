"""
Optimistic UI State Helper Primitive — GEMA 39 (Linear / Notion Pattern / SOTA 2026).
Provides React/TypeScript hook patterns for immediate optimistic UI updates
with automatic state rollback if backend mutations fail.
Eliminates interface latency by assuming success by default.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.optimistic_ui")


class OptimisticUIPrimitive:
    """
    Generate the useOptimisticMutation React hook for the frontend.
    """

    def generate_react_hook_ts(self) -> str:
        """Generate the TypeScript code for the useOptimisticAction hook."""
        return """import { useState, useCallback } from 'react';

export interface OptimisticMutationOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error, previousState: T[]) => void;
}

export function useOptimisticList<T extends { id: string | number }>(initialItems: T[]) {
  const [items, setItems] = useState<T[]>(initialItems);
  const [isPending, setIsPending] = useState(false);

  const optimisticAdd = useCallback(async (
    newItem: T,
    mutationPromise: () => Promise<any>,
    options?: OptimisticMutationOptions<T>
  ) => {
    const rollbackState = [...items];
    // 1. Mutación optimista inmediata en la UI
    setItems((prev) => [newItem, ...prev]);
    setIsPending(true);

    try {
      const result = await mutationPromise();
      if (options?.onSuccess) options.onSuccess(result);
    } catch (err: any) {
      // 2. Reversión automática en caso de error en el backend
      console.error('[OptimisticUI] Mutación fallida, revirtiendo estado:', err);
      setItems(rollbackState);
      if (options?.onError) options.onError(err, rollbackState);
    } finally {
      setIsPending(false);
    }
  }, [items]);

  const optimisticDelete = useCallback(async (
    id: string | number,
    mutationPromise: () => Promise<any>
  ) => {
    const rollbackState = [...items];
    setItems((prev) => prev.filter((item) => item.id !== id));
    setIsPending(true);

    try {
      await mutationPromise();
    } catch (err) {
      console.error('[OptimisticUI] Eliminación fallida, revirtiendo:', err);
      setItems(rollbackState);
    } finally {
      setIsPending(false);
    }
  }, [items]);

  return { items, setItems, optimisticAdd, optimisticDelete, isPending };
}
"""


optimistic_ui = OptimisticUIPrimitive()
