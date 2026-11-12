"""Canonical Single Source of Truth (SSOT) for CMMI maturity scales and boundary intervals.

Defines immutable numerical intervals and provides authoritative tier resolution
to eliminate split-brain inconsistencies across presentation compilers and actuarial engines.
"""

from __future__ import annotations

import dataclasses
from typing import Final


@dataclasses.dataclass(frozen=True)
class MaturityInterval:
    """Immutable CMMI maturity level boundary definition."""

    level: int
    tier_id: str
    name_key: str
    desc_key: str
    min_score: float
    max_score: float
    canonical_name: str
    canonical_description: str


_CANONICAL_INTERVALS: Final[tuple[MaturityInterval, ...]] = (
    MaturityInterval(
        level=1,
        tier_id="initial",
        name_key="cmmi_tier_1_name",
        desc_key="cmmi_tier_1_desc",
        min_score=1.00,
        max_score=1.59,
        canonical_name="Level 1 - Initial",
        canonical_description="Ad-hoc, reactive practices dependent on heroic individual efforts.",
    ),
    MaturityInterval(
        level=2,
        tier_id="managed",
        name_key="cmmi_tier_2_name",
        desc_key="cmmi_tier_2_desc",
        min_score=1.60,
        max_score=2.59,
        canonical_name="Level 2 - Managed",
        canonical_description="Basic operational processes established at tactical level with inter-silo inconsistencies.",
    ),
    MaturityInterval(
        level=3,
        tier_id="defined",
        name_key="cmmi_tier_3_name",
        desc_key="cmmi_tier_3_desc",
        min_score=2.60,
        max_score=3.59,
        canonical_name="Level 3 - Defined",
        canonical_description="Formalized and consistently documented processes across the entire enterprise.",
    ),
    MaturityInterval(
        level=4,
        tier_id="quantitatively_managed",
        name_key="cmmi_tier_4_name",
        desc_key="cmmi_tier_4_desc",
        min_score=3.60,
        max_score=4.59,
        canonical_name="Level 4 - Quantitatively Managed",
        canonical_description="Quantitatively measured capabilities aligned with corporate IT governance.",
    ),
    MaturityInterval(
        level=5,
        tier_id="optimizing",
        name_key="cmmi_tier_5_name",
        desc_key="cmmi_tier_5_desc",
        min_score=4.60,
        max_score=5.00,
        canonical_name="Level 5 - Optimized",
        canonical_description="Operational excellence model characterized by high automation and continuous improvement.",
    ),
)


def get_canonical_scale_intervals() -> tuple[MaturityInterval, ...]:
    """Return the immutable sequence of canonical CMMI scale intervals."""
    return _CANONICAL_INTERVALS

def resolve_maturity_interval(score: float) -> MaturityInterval:
    """Resolve a numerical maturity score into its authoritative MaturityInterval.
    Phase 3 (Plan V6): Delegates directly to GovernanceScaleEngine SSOT.
    """
    from assessment_engine.domain.governance import GovernanceScaleEngine
    res = GovernanceScaleEngine.get_instance().resolve_maturity(score)
    for interval in _CANONICAL_INTERVALS:
        if interval.level == res.level:
            return interval
    return _CANONICAL_INTERVALS[0]
    # Fallback to level 5 if boundary rounding produces 5.00+
    return _CANONICAL_INTERVALS[-1]
