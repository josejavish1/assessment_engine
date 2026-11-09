"""Bayesian Actuarial Inference Engine for Silent Pillars (RFC 084 Phase 2).

Quantifies epistemic uncertainty for unobserved/silent enterprise pillars using the
Factor Analysis of Information Risk (FAIR) framework, eradicating $0.00 ALE boilerplate.
"""

from __future__ import annotations

import dataclasses
import math
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from assessment_engine.application.services.semantic_epistemic_router import (
        EpistemicContextPacket,
    )


@dataclasses.dataclass(frozen=True)
class TenantActuarialProfile:
    """Immutable actuarial profile of an assessed enterprise tenant."""

    annual_revenue: float = 100_000_000.0
    industry_vertical: str = "general"
    employee_headcount: int = 500
    currency_code: str = "USD"


@dataclasses.dataclass(frozen=True)
class LatentActuarialFinding:
    """Immutable FAIR-based actuarial risk finding for observed or unobserved pillars."""

    finding_id: str
    tower_code: str
    pillar_id: str
    title: str
    epistemic_state: str
    loss_event_frequency: float
    single_loss_expectancy: float
    annual_loss_expectancy: float
    value_at_risk_90: float
    rationale: str


_TOWER_DEFAULT_PILLARS: Final[dict[str, tuple[str, str]]] = {
    "T1": ("T1.P1", "Power & Electrical Continuity"),
    "T2": ("T2.P1", "Compute Foundation & Virtualization"),
    "T3": ("T3.P1", "Data Center & Campus Network Foundation"),
    "T4": ("T4.P1", "Storage Architecture & Service Levels"),
    "T5": ("T5.P1", "BC/DR Governance & Continuity Strategy"),
    "T6": ("T6.P1", "Identity & Access Management (IAM)"),
    "T7": ("T7.P1", "Service Governance, Catalog & SLA Management"),
    "T8": ("T8.P1", "Technology Strategy & Strategic Roadmap"),
    "T9": ("T9.P1", "Endpoint & Device Lifecycle Management"),
    "T10": ("T10.P1", "Core Enterprise & Transactional Applications"),
}

_TOWER_ACTUARIAL_WEIGHTS: Final[dict[str, tuple[float, float, float]]] = {
    # tower_code: (base_lef, base_sle_revenue_bps, tail_var90_multiplier)
    "T1": (0.14, 18.0, 2.10),
    "T2": (0.22, 32.0, 2.35),
    "T3": (0.25, 38.0, 2.40),
    "T4": (0.18, 42.0, 2.60),
    "T5": (0.16, 48.0, 2.85),
    "T6": (0.28, 55.0, 3.10),
    "T7": (0.20, 28.0, 2.20),
    "T8": (0.24, 25.0, 2.15),
    "T9": (0.30, 20.0, 2.05),
    "T10": (0.26, 15.0, 1.95),
}

_SECTOR_MULTIPLIERS: Final[dict[str, tuple[float, float]]] = {
    # industry_vertical: (lef_multiplier, sle_multiplier)
    "fintech": (1.35, 1.65),
    "banking": (1.35, 1.65),
    "finance": (1.30, 1.55),
    "healthcare": (1.25, 1.50),
    "aerospace": (1.30, 1.55),
    "defense": (1.35, 1.60),
    "energy": (1.25, 1.45),
    "utilities": (1.20, 1.40),
    "telecom": (1.25, 1.40),
    "pharma": (1.20, 1.45),
    "technology": (1.20, 1.35),
    "public_sector": (1.20, 1.30),
    "government": (1.20, 1.30),
    "retail": (1.15, 1.25),
    "manufacturing": (1.05, 1.15),
    "logistics": (1.00, 0.95),
    "media": (1.00, 1.05),
    "general": (1.00, 1.00),
}

_SECTOR_TOWER_AMPLIFIERS: Final[dict[tuple[str, str], float]] = {
    ("fintech", "T6"): 1.45,
    ("fintech", "T5"): 1.30,
    ("banking", "T6"): 1.45,
    ("banking", "T5"): 1.35,
    ("aerospace", "T6"): 1.40,
    ("aerospace", "T2"): 1.25,
    ("energy", "T1"): 1.35,
    ("energy", "T3"): 1.25,
    ("retail", "T3"): 1.25,
    ("retail", "T5"): 1.20,
    ("manufacturing", "T2"): 1.20,
    ("manufacturing", "T3"): 1.20,
    ("manufacturing", "T10"): 1.30,
    ("logistics", "T3"): 1.15,
    ("logistics", "T10"): 1.20,
}


class ActuarialInferenceEngine:
    """FAIR Bayesian Actuarial Inference Engine for Observed and Unobserved Pillars."""

    def __init__(self, default_profile: TenantActuarialProfile | None = None) -> None:
        """Initialize the actuarial engine with an optional tenant profile."""
        self._default_profile = default_profile or TenantActuarialProfile()

    @property
    def default_profile(self) -> TenantActuarialProfile:
        """Return the configured default tenant actuarial profile."""
        return self._default_profile

    def calculate_latent_risk(
        self,
        tower_code: str,
        pillar_id: str,
        pillar_name: str,
        profile: TenantActuarialProfile | None = None,
    ) -> LatentActuarialFinding:
        """Calculate FAIR latent actuarial metrics for an unobserved pillar."""
        active_profile = profile or self._default_profile
        normalized_tower = tower_code.strip().upper()
        base_lef, base_bps, tail_mult = _TOWER_ACTUARIAL_WEIGHTS.get(
            normalized_tower, (0.20, 25.0, 2.25)
        )
        sector_key = active_profile.industry_vertical.strip().lower()
        lef_mult, sle_mult = _SECTOR_MULTIPLIERS.get(sector_key, (1.0, 1.0))
        tower_amp = _SECTOR_TOWER_AMPLIFIERS.get((sector_key, normalized_tower), 1.0)

        raw_rev = active_profile.annual_revenue
        safe_revenue = raw_rev if (math.isfinite(raw_rev) and raw_rev >= 100_000.0) else 100_000.0
        headcount_factor = 1.0 + min(max(active_profile.employee_headcount, 1) / 100_000.0, 0.25)

        lef = round(min(max(base_lef * lef_mult * tower_amp, 0.01), 0.99), 4)
        base_sle = safe_revenue * (base_bps / 10_000.0)
        sle = round(max(base_sle * sle_mult * tower_amp * headcount_factor, 1_000.0), 2)
        ale = round(max(lef * sle, 100.0), 2)
        var_90 = round(ale * tail_mult, 2)

        sanitized_pillar = pillar_id.replace(".", "_")
        finding_id = f"BLINDSPOT_{normalized_tower}_{sanitized_pillar}"
        title = f"Unobserved Epistemic Exposure: {pillar_name}"
        rationale = (
            f"Epistemic silence in {pillar_name} ({pillar_id}) within the {sector_key} "
            f"vertical prevents control verification, exposing {active_profile.currency_code} "
            f"{ale:,.2f} in unmitigated baseline Annual Loss Expectancy."
        )

        return LatentActuarialFinding(
            finding_id=finding_id,
            tower_code=normalized_tower,
            pillar_id=pillar_id,
            title=title,
            epistemic_state="UNOBSERVED_BLINDSPOT",
            loss_event_frequency=lef,
            single_loss_expectancy=sle,
            annual_loss_expectancy=ale,
            value_at_risk_90=var_90,
            rationale=rationale,
        )

    def _calculate_observed_risk(
        self,
        packet: EpistemicContextPacket,
        profile: TenantActuarialProfile,
    ) -> LatentActuarialFinding:
        """Calculate FAIR actuarial risk for an explicitly observed tower packet."""
        normalized_tower = packet.tower_code.strip().upper()
        pillar_id, pillar_name = _TOWER_DEFAULT_PILLARS.get(
            normalized_tower, (f"{normalized_tower}.P1", f"{normalized_tower} Core Domain")
        )
        baseline = self.calculate_latent_risk(
            tower_code=normalized_tower,
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            profile=profile,
        )

        negative_count = sum(
            1 for p in packet.propositions if getattr(p, "polarity", "") == "NEGATIVE"
        )
        positive_count = sum(
            1 for p in packet.propositions if getattr(p, "polarity", "") == "POSITIVE"
        )

        _, _, tail_mult = _TOWER_ACTUARIAL_WEIGHTS.get(
            normalized_tower, (0.20, 25.0, 2.50)
        )

        lead_evidence = (
            packet.propositions[0].text
            if packet.propositions
            else f"Observed control telemetry in {pillar_name}."
        )

        if negative_count == 0 and positive_count > 0:
            attenuation = max(0.40, 1.0 - (0.12 * min(positive_count, 5)))
            lef = round(max(baseline.loss_event_frequency * attenuation, 0.01), 4)
            sle = round(max(baseline.single_loss_expectancy * max(0.60, attenuation), 1_000.0), 2)
            ale = round(max(lef * sle, 100.0), 2)
            var_90 = round(ale * max(tail_mult, 2.50), 2)
            title = f"Observed Control Resilience: {pillar_name}"
            rationale = f"Empirical telemetry confirms verified resilience and control posture: {lead_evidence}"
        else:
            density_boost = 1.0 + (0.20 * max(packet.semantic_density_score, 0.1))
            polarity_boost = 1.0 + (0.15 * min(max(negative_count, 1), 5))
            combined_boost = density_boost * polarity_boost

            lef = round(min(baseline.loss_event_frequency * combined_boost, 0.99), 4)
            sle = round(baseline.single_loss_expectancy * polarity_boost, 2)
            ale = round(max(lef * sle, 100.0), 2)
            var_90 = round(ale * max(tail_mult, 2.50), 2)
            title = f"Observed Control Deficiency: {pillar_name}"
            rationale = f"Empirical telemetry confirms active exposure: {lead_evidence}"

        return LatentActuarialFinding(
            finding_id=f"OBSERVED_{normalized_tower}_{pillar_id.replace('.', '_')}",
            tower_code=normalized_tower,
            pillar_id=pillar_id,
            title=title,
            epistemic_state=packet.epistemic_state,
            loss_event_frequency=lef,
            single_loss_expectancy=sle,
            annual_loss_expectancy=ale,
            value_at_risk_90=var_90,
            rationale=rationale,
        )

    def hydrate_portfolio_risks(
        self,
        packets: dict[str, EpistemicContextPacket],
        profile: TenantActuarialProfile | None = None,
    ) -> dict[str, list[LatentActuarialFinding]]:
        """Hydrate FAIR risk findings across all portfolio towers, preventing $0.00 ALE."""
        active_profile = profile or self._default_profile
        hydrated: dict[str, list[LatentActuarialFinding]] = {}

        for tower_code, packet in packets.items():
            normalized_tower = tower_code.strip().upper()
            is_observed = (
                packet.epistemic_state == "OBSERVED_EXPLICIT" and len(packet.propositions) > 0
            )
            if is_observed:
                finding = self._calculate_observed_risk(packet, active_profile)
                hydrated[tower_code] = [finding]
                continue

            pillar_id, pillar_name = _TOWER_DEFAULT_PILLARS.get(
                normalized_tower, (f"{normalized_tower}.P1", f"{normalized_tower} Core Pillar")
            )
            latent_finding = self.calculate_latent_risk(
                tower_code=normalized_tower,
                pillar_id=pillar_id,
                pillar_name=pillar_name,
                profile=active_profile,
            )
            hydrated[tower_code] = [latent_finding]

        return hydrated
