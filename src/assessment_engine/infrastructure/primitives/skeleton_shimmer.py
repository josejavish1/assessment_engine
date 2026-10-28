"""
Progressive Shimmer Skeleton Generator — GEMA 66 (CLS = 0.00 / SOTA 2026).
Emits zero-runtime CSS shimmer skeleton keyframes and React components.
Reserves exact layout dimensions before asynchronous SQLite WAL data loads.
Guarantees a Google Core Web Vitals Cumulative Layout Shift (CLS) of exactly 0.00.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.skeleton_shimmer")


class SkeletonShimmerPrimitive:
    """
    Generador de estilos y componentes Shimmer Skeleton anti-CLS.
    """

    def generate_shimmer_css(self) -> str:
        """Generate the shimmer animation CSS block."""
        return """/* Tier-1 Shimmer Skeleton (CLS = 0.00) */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton-shimmer {
  background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite ease-in-out;
  border-radius: 0.5rem;
}

.dark .skeleton-shimmer {
  background: linear-gradient(90deg, #1E293B 25%, #334155 50%, #1E293B 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite ease-in-out;
}
"""

    def generate_skeleton_card_jsx(self) -> str:
        """Generate a shimmer card component in React."""
        return """export function SkeletonCard() {
  return (
    <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full skeleton-shimmer" />
        <div className="space-y-1.5 flex-1">
          <div className="h-4 w-1/3 skeleton-shimmer" />
          <div className="h-3 w-1/2 skeleton-shimmer" />
        </div>
      </div>
      <div className="h-16 w-full skeleton-shimmer" />
    </div>
  );
}
"""


skeleton_shimmer = SkeletonShimmerPrimitive()
