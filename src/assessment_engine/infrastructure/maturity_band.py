"""Backward-compatible proxy delegating to canonical domain.maturity_band."""
from __future__ import annotations

from assessment_engine.domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    GLOBAL_MATURITY_BANDS,
    MaturityBandDefinition,
    resolve_maturity_band,
)

__all__ = [
    "ANNEX_MATURITY_BANDS",
    "GLOBAL_MATURITY_BANDS",
    "MaturityBandDefinition",
    "resolve_maturity_band",
]
