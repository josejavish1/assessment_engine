"""Bow-Tie Control-Plane Graph Escalation and Environmental Scaling (SR 11-7)."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence
from assessment_engine.domain.schemas.actuarial_contracts import (
    ArchitecturalRole,
    AssetActuarialProfile,
    CausalNature,
    EnvironmentTier,
)


class BowTieEscalationEngine:
    """Computes systemic cascading exposure across Control-Plane boundaries and environment tiers."""

    _ENVIRONMENT_REVENUE_SCALARS: Mapping[EnvironmentTier, float] = {
        EnvironmentTier.PROD_CRITICAL: 1.00,
        EnvironmentTier.PROD_SUPPORT: 0.35,
        EnvironmentTier.STAGING_UAT: 0.00,
        EnvironmentTier.LAB_DEV_TEST: 0.00,
    }

    @classmethod
    def get_environment_revenue_scalar(cls, env: EnvironmentTier) -> float:
        """Returns the deterministic revenue dependency factor for an environment tier."""
        return cls._ENVIRONMENT_REVENUE_SCALARS.get(env, 0.0)

    @classmethod
    def calculate_cascaded_hourly_exposure(
        cls,
        target_asset: AssetActuarialProfile,
        causal_nature: CausalNature,
        dependent_assets: Sequence[AssetActuarialProfile],
        contagion_factor: Optional[float] = None,
    ) -> float:
        """Calculates total hourly business interruption exposure including bow-tie contagion.

        V_cascade(u) = V_rev(u) * omega(E_u) + sum_{v in B(u)} alpha(u, v) * V_rev(v) * omega(E_v)
        """
        target_scalar = cls.get_environment_revenue_scalar(target_asset.environment_tier)
        direct_hourly = target_asset.hourly_revenue_contribution * target_scalar

        # If not a Control-Plane threat with lateral contagion, blast radius is purely localized
        if target_asset.architectural_role != ArchitecturalRole.CONTROL_PLANE:
            return float(direct_hourly)

        is_destructive_or_exfil = causal_nature in (
            CausalNature.DESTRUCTIVE_SABOTAGE,
            CausalNature.MALICIOUS_EXFILTRATION,
        )
        if not is_destructive_or_exfil:
            return float(direct_hourly)

        # Default contagion factors (Tier-0 PAM / Identity compromise)
        if contagion_factor is None:
            contagion_factor = 1.0 if causal_nature == CausalNature.DESTRUCTIVE_SABOTAGE else 0.65

        cascaded_exposure = direct_hourly
        for dep in dependent_assets:
            dep_scalar = cls.get_environment_revenue_scalar(dep.environment_tier)
            dep_effective_hourly = dep.hourly_revenue_contribution * dep_scalar
            cascaded_exposure += dep_effective_hourly * contagion_factor

        return float(round(cascaded_exposure, 2))
