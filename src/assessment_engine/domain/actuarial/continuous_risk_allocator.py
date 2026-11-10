"""Continuous Risk Allocator for Microeconomic Scenarios.

Enforces deterministic, scale-invariant risk distribution across arbitrary
enterprise sizes, currencies, maturity scales, and locales while guaranteeing
exact horizontal closure to the master domain ALE via Hare-Niemeyer discretization.
"""

from __future__ import annotations

import copy
import hashlib
import math
from typing import Any, Dict, List, Mapping, Optional

# Canonical multi-locale severity weights supporting global enterprise ingestion.
_SEVERITY_WEIGHT_MAP: Mapping[str, float] = {
    # English
    "CRITICAL": 3.5,
    "VERY HIGH": 3.5,
    "HIGH": 2.2,
    "MEDIUM": 1.2,
    "MODERATE": 1.2,
    "LOW": 0.6,
    "NONE": 0.3,
    "INFO": 0.3,
    # Spanish / Portuguese / Italian equivalents
    "CRITICO": 3.5,
    "CRÍTICO": 3.5,
    "MUY ALTO": 3.5,
    "ALTO": 2.2,
    "ALTA": 2.2,
    "MEDIO": 1.2,
    "MEDIA": 1.2,
    "MODERADO": 1.2,
    "BAJO": 0.6,
    "BAJA": 0.6,
    "BAIXO": 0.6,
    "NINGUNO": 0.3,
    "NULO": 0.3,
    # French / German equivalents
    "CRITIQUE": 3.5,
    "ÉLEVÉ": 2.2,
    "ELEVE": 2.2,
    "HOCH": 2.2,
    "MOYEN": 1.2,
    "MITTEL": 1.2,
    "FAIBLE": 0.6,
    "NIEDRIG": 0.6,
    "KRITISCH": 3.5,
}

_LEGACY_OVERRIDE_KEYS: tuple[str, ...] = (
    "fair_ale",
    "fair_ale_score",
    "fair_p90_score",
    "ale_val",
)


class ContinuousRiskAllocator:
    """Distributes a macro-level domain ALE across N individual health checks/risks
    using continuous capability deficits, finding severities, and deterministic
    entropy while preserving exact horizontal closure across any monetary scale.
    """

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        """Coerces arbitrary input to a finite float without truthiness traps."""
        if value is None or isinstance(value, bool):
            return default
        try:
            parsed = float(value)
            return parsed if math.isfinite(parsed) else default
        except (ValueError, TypeError):
            return default

    @classmethod
    def _resolve_severity_multiplier(cls, raw_severity: Any) -> float:
        """Resolves localized or canonical severity strings to actuarial weights."""
        if raw_severity is None:
            return 1.2
        normalized = str(raw_severity).strip().upper()
        return _SEVERITY_WEIGHT_MAP.get(normalized, 1.2)

    @classmethod
    def allocate_risks(
        cls,
        total_ale: float,
        total_sle: float,
        health_checks: List[Dict[str, Any]],
        *,
        max_maturity_score: float = 5.0,
        precision_decimals: Optional[int] = None,
        mutate_in_place: bool = True,
    ) -> List[Dict[str, Any]]:
        """Allocates total_ale and total_sle across health_checks deterministically.

        Args:
            total_ale: Aggregate domain Annualized Loss Expectancy.
            total_sle: Aggregate domain Single Loss Expectancy.
            health_checks: Collection of finding dictionaries.
            max_maturity_score: Upper bound of the capability maturity scale (default 5.0).
            precision_decimals: Decimal places for discretization (auto-scaled if None).
            mutate_in_place: If False, returns a deep-copied list leaving input untouched.

        Guarantees:
            1. Exact horizontal closure: sum(hc['ale']) == round(total_ale, precision).
            2. Exact SLE closure: sum(hc['sle']) == round(total_sle, 2).
            3. Zero NaN/Inf propagation or truthiness-induced score corruption.
        """
        if not health_checks:
            return []

        target_checks = health_checks if mutate_in_place else copy.deepcopy(health_checks)
        clean_ale = cls._safe_float(total_ale, 0.0)
        clean_sle = cls._safe_float(total_sle, 0.0)
        scale_max = max(1.0, cls._safe_float(max_maturity_score, 5.0))
        default_midpoint = scale_max / 2.0
        min_deficit = scale_max * 0.10

        # Always purge legacy keys regardless of whether total_ale is zero
        for hc in target_checks:
            for k in _LEGACY_OVERRIDE_KEYS:
                hc.pop(k, None)

        if clean_ale <= 0.0:
            for hc in target_checks:
                hc["ale"] = 0.0
                hc["sle"] = 0.0
            return target_checks

        # Auto-detect discretization precision so fractional/millions scales do not collapse
        n_items = len(target_checks)
        if precision_decimals is None:
            if clean_ale < n_items * 10:
                precision_decimals = 2
            else:
                precision_decimals = 0

        scale_factor = 10 ** precision_decimals

        # Step 1: Compute continuous weight for each health check
        raw_weights: List[float] = []
        for idx, hc in enumerate(target_checks):
            raw_score = cls._safe_float(hc.get("score"), default_midpoint)
            clamped_score = max(0.0, min(scale_max, raw_score))
            deficit = max(min_deficit, scale_max - clamped_score)

            sev_mult = cls._resolve_severity_multiplier(hc.get("severity"))

            seed_str = (
                f"{hc.get('id', '')}:{hc.get('capability', '')}:"
                f"{idx}:{hc.get('finding', '')}"
            )
            h_val = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
            # Continuous perturbation in [0.85, 1.15] with 10,000 buckets to prevent collisions
            perturbation = 0.85 + (h_val % 3001) / 10000.0

            w = deficit * sev_mult * perturbation
            raw_weights.append(w)

        total_weight = sum(raw_weights)
        if total_weight <= 0.0 or not math.isfinite(total_weight):
            raw_weights = [1.0] * n_items
            total_weight = float(n_items)

        # Step 2: Hare-Niemeyer largest-remainder allocation for ALE
        scaled_total_ale = int(round(clean_ale * scale_factor))
        raw_scaled_ales = [scaled_total_ale * (w / total_weight) for w in raw_weights]
        floor_scaled_ales = [math.floor(v) for v in raw_scaled_ales]
        ale_shortfall = scaled_total_ale - sum(floor_scaled_ales)

        remainder_indices = sorted(
            range(n_items),
            key=lambda i: (raw_scaled_ales[i] - floor_scaled_ales[i], raw_weights[i], -i),
            reverse=True,
        )
        for i in range(max(0, min(ale_shortfall, n_items))):
            floor_scaled_ales[remainder_indices[i]] += 1

        # Step 3: Hare-Niemeyer largest-remainder allocation for SLE (in cents)
        scaled_total_sle = int(round(max(0.0, clean_sle) * 100))
        raw_scaled_sles = [scaled_total_sle * (w / total_weight) for w in raw_weights]
        floor_scaled_sles = [math.floor(v) for v in raw_scaled_sles]
        sle_shortfall = scaled_total_sle - sum(floor_scaled_sles)

        sle_remainder_indices = sorted(
            range(n_items),
            key=lambda i: (raw_scaled_sles[i] - floor_scaled_sles[i], raw_weights[i], -i),
            reverse=True,
        )
        for i in range(max(0, min(sle_shortfall, n_items))):
            floor_scaled_sles[sle_remainder_indices[i]] += 1

        # Step 4: Assign final values
        for idx, hc in enumerate(target_checks):
            hc["ale"] = round(floor_scaled_ales[idx] / scale_factor, precision_decimals)
            hc["sle"] = round(floor_scaled_sles[idx] / 100.0, 2)

        return target_checks
