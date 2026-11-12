"""Continuous Beta Buffer Attenuation and Temporal Physics Engine (SR 11-7)."""

from __future__ import annotations

import math
from typing import Mapping, Optional


class TemporalPhysicsEngine:
    """Calculates continuous business interruption duration and labor reconstruction costs.

    Prevents catastrophic business interruption losses on fast-recovery operational friction
    while avoiding discontinuous step-function cliffs via smooth second-order attenuation.
    """

    @staticmethod
    def calculate_effective_downtime_hours(
        tech_restoration_hours: float,
        buffer_hours: float,
        beta: float = 2.0,
        grace_delta: float = 0.0,
    ) -> float:
        """Computes Effective Business Interruption Duration T_eff from T_tech and tau_buffer.

        Formula:
        If tau_buffer == 0: T_eff = T_tech
        If T_tech <= tau_buffer * (1 - delta): T_eff = 0.0
        If T_tech > tau_buffer: T_eff = (T_tech - tau_buffer) * (T_tech / (T_tech + tau_buffer)) ** beta
        """
        if tech_restoration_hours <= 0.0:
            return 0.0
        if buffer_hours <= 0.0:
            return float(tech_restoration_hours)

        # Hard buffer cutoff within grace tolerance
        if tech_restoration_hours <= buffer_hours * (1.0 - grace_delta):
            return 0.0

        # Continuous smooth second-order attenuation above the buffer threshold
        excess = tech_restoration_hours - buffer_hours
        attenuation_ratio = tech_restoration_hours / (tech_restoration_hours + buffer_hours)
        attenuation_factor = math.pow(attenuation_ratio, max(1.0, beta))

        return float(max(0.0, excess * attenuation_factor))

    @staticmethod
    def calculate_reconstitution_labor_cost(
        tech_restoration_hours: float,
        hourly_engineering_rate: float = 65.0,
        fte_count: float = 1.0,
    ) -> float:
        """Direct internal engineering labor cost for technical restoration.

        C_reconst = T_tech * R_eng * N_FTE
        Always incurred regardless of whether business interruption is absorbed by the buffer.
        """
        if tech_restoration_hours <= 0.0:
            return 0.0
        return float(round(tech_restoration_hours * hourly_engineering_rate * max(1.0, fte_count), 2))
