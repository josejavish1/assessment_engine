"""Risk aggregation engine for deduplicating overlapping blast radii using joint probability."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List


class BlastRadiusDeduplicator:
    """
    Eliminates double-counting of overlapping downtime across shared infrastructure
    using Joint Probability of Failure (Inclusion-Exclusion Principle).
    """

    OPERATING_YEAR_HOURS = Decimal("8760.0")

    @classmethod
    def compute_effective_downtime(cls, raw_downtime_hours: List[Decimal]) -> Decimal:
        """
        Calculates deduplicated downtime hours by modeling individual risk outages
        as non-mutually-exclusive probabilistic events within an 8760-hour window.
        """
        if not raw_downtime_hours:
            return Decimal("0.00")

        survival_probability = Decimal("1.0")

        for hours in raw_downtime_hours:
            clamped_hours = min(max(hours, Decimal("0.0")), cls.OPERATING_YEAR_HOURS)
            event_probability = clamped_hours / cls.OPERATING_YEAR_HOURS
            survival_probability *= (Decimal("1.0") - event_probability)

        joint_failure_probability = Decimal("1.0") - survival_probability
        effective_hours = cls.OPERATING_YEAR_HOURS * joint_failure_probability

        return effective_hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
