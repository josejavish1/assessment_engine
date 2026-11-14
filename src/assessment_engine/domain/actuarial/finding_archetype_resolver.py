"""Finding-Level Polymorphic Loss Archetype and Epistemic Resolver (SR 11-7 / Open FAIR).

Provides finding-level polymorphic classification of loss physics:
- FINOPS_RESOURCE_WASTE (zero downtime burn, zero Euler discount)
- ENGINEERING_VELOCITY_FRICTION (zero downtime burn, bounded Euler discount)
- REGULATORY_AND_BREACH (zero downtime burn, forensic/regulatory liability)
- ASSET_OBSOLESCENCE_AND_INTEGRITY (workload-scoped migration/integrity debt)
- AVAILABILITY_OUTAGE (physical/operational service interruption)

Guarantees 100% Technical English in source code and closed-form AdditiveLossDecomposition.
Multilingual lexical tokens are loaded strictly from external declarative configuration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any, Final, Mapping, Sequence

from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
)


class EpistemicEvidenceState(StrEnum):
    """Institutional classification of evidence provenance per SR 11-7."""

    VERIFIED_EMPIRICAL = "VERIFIED_EMPIRICAL"
    SURVEY_INFERRED_BOILERPLATE = "SURVEY_INFERRED_BOILERPLATE"
    UNASSESSED_OUT_OF_SCOPE = "UNASSESSED_OUT_OF_SCOPE"


class FindingLossPhysics(StrEnum):
    """Granular finding-level loss mechanics overriding macro-tower defaults."""

    AVAILABILITY_OUTAGE = "AVAILABILITY_OUTAGE"
    PLATFORM_DEGRADATION = "PLATFORM_DEGRADATION"
    FINOPS_RESOURCE_WASTE = "FINOPS_RESOURCE_WASTE"
    ENGINEERING_VELOCITY_FRICTION = "ENGINEERING_VELOCITY_FRICTION"
    REGULATORY_AND_BREACH = "REGULATORY_AND_BREACH"
    ASSET_OBSOLESCENCE_AND_INTEGRITY = "ASSET_OBSOLESCENCE_AND_INTEGRITY"

    def to_canonical_archetype(self) -> LossArchetypeType:
        """Maps finding-level physics to canonical Open FAIR loss archetype."""
        mapping = {
            FindingLossPhysics.AVAILABILITY_OUTAGE: LossArchetypeType.AVAILABILITY_OUTAGE,
            FindingLossPhysics.PLATFORM_DEGRADATION: LossArchetypeType.AVAILABILITY_OUTAGE,
            FindingLossPhysics.FINOPS_RESOURCE_WASTE: LossArchetypeType.CAPITAL_INEFFICIENCY,
            FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION: LossArchetypeType.PRODUCTIVITY_TOIL,
            FindingLossPhysics.REGULATORY_AND_BREACH: LossArchetypeType.REGULATORY_AND_BREACH,
            FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY: (
                LossArchetypeType.ASSET_OBSOLESCENCE
                if hasattr(LossArchetypeType, "ASSET_OBSOLESCENCE")
                else LossArchetypeType.AVAILABILITY_OUTAGE
            ),
        }
        return mapping[self]


@dataclass(frozen=True)
class FindingPhysicsProfile:
    """Immutable physics rules governing a single finding's actuarial evaluation."""

    loss_physics: FindingLossPhysics
    canonical_archetype: LossArchetypeType
    epistemic_state: EpistemicEvidenceState
    allows_downtime_burn: bool
    allows_secondary_regulatory_fallout: bool
    default_rto_hours: float
    blast_radius_factor: float
    max_euler_ale_discount_pct: float
    max_euler_var_discount_pct: float
    classification_rationale: str
    default_lef_annual: float = 0.10


@dataclass(frozen=True)
class PhysicsDefaultSpec:
    """Declarative actuarial parameter specification for a FindingLossPhysics class."""

    allows_downtime_burn: bool
    allows_secondary_regulatory_fallout: bool
    default_rto_hours: float
    default_blast_radius_factor: float
    max_euler_ale_discount_pct: float
    max_euler_var_discount_pct: float
    default_lef_annual: float = 0.10


@dataclass(frozen=True)
class AdditiveLossDecomposition:
    """Closed-form, zero-plug additive decomposition of Single and Annualized Loss Expectancy.

    Enforces exact arithmetic conservation between Domain Engine and Presentation AST.
    """

    currency_iso: str
    mean_lef: float
    expected_downtime_loss: int
    expected_replacement_cost: int
    expected_secondary_loss: int
    gross_mean_sle: int
    gross_standalone_ale: int
    euler_overlap_adjustment_ale: int
    net_allocated_ale: int
    euler_discount_pct: Decimal
    gross_standalone_p90: int
    net_allocated_p90: int
    loss_physics: str
    epistemic_state: str
    ledger_type: str = "LEDGER_A_STOCHASTIC"
    is_deterministic: bool = False
    fleet_volume: int = 1

    def validate_conservation(self) -> None:
        sle_sum = (
            self.expected_downtime_loss
            + self.expected_replacement_cost
            + self.expected_secondary_loss
        )
        if sle_sum != self.gross_mean_sle:
            raise ValueError(
                f"SLE Additive Conservation Violation: Downtime ({self.expected_downtime_loss}) + "
                f"Replacement ({self.expected_replacement_cost}) + Secondary ({self.expected_secondary_loss}) "
                f"= {sle_sum} != Gross Mean SLE ({self.gross_mean_sle})."
            )
        if self.euler_overlap_adjustment_ale > 0:
            raise ValueError(
                f"Sub-additivity Violation: Euler overlap adjustment must be <= 0, "
                f"got {self.euler_overlap_adjustment_ale}."
            )
        if self.is_deterministic and self.euler_overlap_adjustment_ale != 0:
            raise ValueError(
                f"Deterministic OpEx Violation: Ledger B must have 0 Euler adjustment, "
                f"got {self.euler_overlap_adjustment_ale}."
            )
        ale_bridge = self.gross_standalone_ale + self.euler_overlap_adjustment_ale
        if ale_bridge != self.net_allocated_ale:
            raise ValueError(
                f"ALE Bridge Conservation Violation: Gross ({self.gross_standalone_ale}) + "
                f"Euler Adjustment ({self.euler_overlap_adjustment_ale}) = {ale_bridge} != "
                f"Net Allocated ALE ({self.net_allocated_ale})."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency_iso": self.currency_iso,
            "mean_lef": self.mean_lef,
            "expected_downtime_loss": self.expected_downtime_loss,
            "expected_replacement_cost": self.expected_replacement_cost,
            "expected_secondary_loss": self.expected_secondary_loss,
            "gross_mean_sle": self.gross_mean_sle,
            "gross_standalone_ale": self.gross_standalone_ale,
            "euler_overlap_adjustment_ale": self.euler_overlap_adjustment_ale,
            "net_allocated_ale": self.net_allocated_ale,
            "euler_discount_pct": float(self.euler_discount_pct),
            "gross_standalone_p90": self.gross_standalone_p90,
            "net_allocated_p90": self.net_allocated_p90,
            "loss_physics": self.loss_physics,
            "epistemic_state": self.epistemic_state,
            "ledger_type": self.ledger_type,
            "is_deterministic": self.is_deterministic,
            "fleet_volume": self.fleet_volume,
        }


ADMISSIBILITY_MATRIX: Final[Mapping[str, Set[FindingLossPhysics]]] = {
    "T1": {
        FindingLossPhysics.AVAILABILITY_OUTAGE,
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
        FindingLossPhysics.REGULATORY_AND_BREACH,
    },
    "T2": {
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.FINOPS_RESOURCE_WASTE,
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
        FindingLossPhysics.AVAILABILITY_OUTAGE,
    },
    "T3": {
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.AVAILABILITY_OUTAGE,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
    },
    "T4": {
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.AVAILABILITY_OUTAGE,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
    },
    "T5": {
        FindingLossPhysics.AVAILABILITY_OUTAGE,
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.REGULATORY_AND_BREACH,
    },
    "T6": {
        FindingLossPhysics.REGULATORY_AND_BREACH,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.AVAILABILITY_OUTAGE,
    },
    "T7": {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.REGULATORY_AND_BREACH,
    },
    "T8": {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
    },
    "T9": {
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
        FindingLossPhysics.PLATFORM_DEGRADATION,
    },
    "T10": {
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.AVAILABILITY_OUTAGE,
    },
}

PILLAR_SUB_ADMISSIBILITY: Final[Mapping[str, Set[FindingLossPhysics]]] = {
    "T1.P3": {
        FindingLossPhysics.REGULATORY_AND_BREACH,
        FindingLossPhysics.PLATFORM_DEGRADATION,
    },
    "T1.P4": {
        FindingLossPhysics.AVAILABILITY_OUTAGE,
        FindingLossPhysics.REGULATORY_AND_BREACH,
    },
    "T2.P4": {
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
    },
    "T2.P3": {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.REGULATORY_AND_BREACH,
    },
    "T2.P5": {
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
        FindingLossPhysics.PLATFORM_DEGRADATION,
        FindingLossPhysics.AVAILABILITY_OUTAGE,
    },
    "T7.P4": {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE,
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
    },
    "T8.P1": {FindingLossPhysics.FINOPS_RESOURCE_WASTE},
    "T8.P2": {FindingLossPhysics.FINOPS_RESOURCE_WASTE},
    "T8.P3": {FindingLossPhysics.FINOPS_RESOURCE_WASTE},
    "T8.P4": {FindingLossPhysics.FINOPS_RESOURCE_WASTE},
    "T8.P5": {FindingLossPhysics.FINOPS_RESOURCE_WASTE},
}


class PolymorphicFindingClassifier:
    """Universal neurosymbolic classifier governed by a Topological Admissibility Firewall.

    Guarantees that operational toil and governance deficiencies never escalate into
    catastrophic outages, executing purely on typed contracts and topological priors without NLP regexes.
    """

    _PHYSICS_DEFAULTS: Final[Mapping[FindingLossPhysics, PhysicsDefaultSpec]] = {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            allows_secondary_regulatory_fallout=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.0,
            max_euler_ale_discount_pct=0.0,
            max_euler_var_discount_pct=0.0,
            default_lef_annual=1.00,
        ),
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            allows_secondary_regulatory_fallout=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.05,
            max_euler_ale_discount_pct=0.10,
            max_euler_var_discount_pct=0.15,
            default_lef_annual=1.00,
        ),
        FindingLossPhysics.PLATFORM_DEGRADATION: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            allows_secondary_regulatory_fallout=False,
            default_rto_hours=0.5,
            default_blast_radius_factor=0.02,
            max_euler_ale_discount_pct=0.15,
            max_euler_var_discount_pct=0.20,
            default_lef_annual=0.85,
        ),
        FindingLossPhysics.REGULATORY_AND_BREACH: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            allows_secondary_regulatory_fallout=True,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.25,
            max_euler_ale_discount_pct=0.15,
            max_euler_var_discount_pct=0.25,
            default_lef_annual=0.25,
        ),
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            allows_secondary_regulatory_fallout=True,
            default_rto_hours=2.0,
            default_blast_radius_factor=0.10,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
            default_lef_annual=0.35,
        ),
        FindingLossPhysics.AVAILABILITY_OUTAGE: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            allows_secondary_regulatory_fallout=True,
            default_rto_hours=4.0,
            default_blast_radius_factor=0.35,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
            default_lef_annual=0.10,
        ),
    }

    @classmethod
    def classify_finding(
        cls,
        hc: Mapping[str, Any],
        tower_id: str,
    ) -> FindingPhysicsProfile:
        finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
        impact_text = str(hc.get("business_risk") or hc.get("primary_impact") or "").strip()
        evidence_text = str(hc.get("evidence") or "").strip()

        # 1. Epistemic Provenance Evaluation
        epistemic_state = cls._evaluate_epistemic_state(hc, finding_text, impact_text, evidence_text)

        # 2. Extract proposed physics from finding contract
        explicit_physics_str = str(
            hc.get("loss_physics")
            or hc.get("loss_archetype")
            or ""
        ).strip().upper()

        proposed_physics: Optional[FindingLossPhysics] = None
        if explicit_physics_str in FindingLossPhysics.__members__:
            proposed_physics = FindingLossPhysics[explicit_physics_str]

        # 3. Determine allowable physics via Topological Admissibility Firewall
        clean_tower = tower_id.strip().upper()
        p_id = str(hc.get("pillar_id") or "").strip().upper()
        
        allowed_physics = PILLAR_SUB_ADMISSIBILITY.get(
            p_id,
            ADMISSIBILITY_MATRIX.get(clean_tower, set(FindingLossPhysics))
        )

        # 4. Enforce Semantic Admissibility
        if proposed_physics is not None:
            if proposed_physics in allowed_physics:
                return cls._build_profile(
                    proposed_physics,
                    epistemic_state,
                    hc,
                    "Explicit typed contract accepted by Topological Firewall",
                )
            else:
                fallback_physics = (
                    FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION
                    if FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION in allowed_physics
                    else FindingLossPhysics.FINOPS_RESOURCE_WASTE
                    if FindingLossPhysics.FINOPS_RESOURCE_WASTE in allowed_physics
                    else FindingLossPhysics.PLATFORM_DEGRADATION
                )
                return cls._build_profile(
                    fallback_physics,
                    epistemic_state,
                    hc,
                    f"Topological Firewall Downgrade: {proposed_physics} not admissible for {p_id or clean_tower}",
                )

        # 5. Deterministic Taxonomy Prior Fallback (Zero NLP guesswork)
        default_physics = (
            FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION
            if "P4" in p_id or clean_tower == "T8"
            else FindingLossPhysics.FINOPS_RESOURCE_WASTE
            if "FINOPS" in p_id or "TAGGING" in p_id
            else FindingLossPhysics.PLATFORM_DEGRADATION
            if clean_tower in {"T2", "T3", "T4", "T9", "T10"}
            else FindingLossPhysics.REGULATORY_AND_BREACH
            if clean_tower == "T6"
            else FindingLossPhysics.AVAILABILITY_OUTAGE
        )

        if default_physics not in allowed_physics:
            default_physics = next(iter(allowed_physics))

        return cls._build_profile(
            default_physics,
            epistemic_state,
            hc,
            f"Taxonomy Prior Fallback for {p_id or clean_tower}",
        )

    @classmethod
    def _evaluate_epistemic_state(
        cls,
        hc: Mapping[str, Any],
        finding_text: str,
        impact_text: str,
        evidence_text: str,
    ) -> EpistemicEvidenceState:
        explicit_state = str(hc.get("epistemic_state") or "").strip().upper()
        if explicit_state in EpistemicEvidenceState.__members__:
            return EpistemicEvidenceState[explicit_state]

        if not finding_text and not impact_text:
            return EpistemicEvidenceState.UNASSESSED_OUT_OF_SCOPE

        if (
            bool(hc.get("is_synthetic_boilerplate"))
            or str(hc.get("source_type") or "").upper() == "LIKERT_FALLBACK"
            or not evidence_text
        ):
            return EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE

        return EpistemicEvidenceState.VERIFIED_EMPIRICAL

    @classmethod
    def _build_profile(
        cls,
        physics: FindingLossPhysics,
        epistemic_state: EpistemicEvidenceState,
        hc: Mapping[str, Any],
        rationale: str,
    ) -> FindingPhysicsProfile:
        spec = cls._PHYSICS_DEFAULTS[physics]
        explicit_blast = hc.get("blast_radius_factor")
        blast_val = (
            float(explicit_blast)
            if explicit_blast is not None
            else spec.default_blast_radius_factor
        )
        explicit_rto = hc.get("default_rto_hours")
        rto_val = (
            float(explicit_rto)
            if (explicit_rto is not None and spec.allows_downtime_burn)
            else spec.default_rto_hours
        )

        return FindingPhysicsProfile(
            loss_physics=physics,
            canonical_archetype=physics.to_canonical_archetype(),
            epistemic_state=epistemic_state,
            allows_downtime_burn=spec.allows_downtime_burn,
            allows_secondary_regulatory_fallout=spec.allows_secondary_regulatory_fallout,
            default_rto_hours=rto_val,
            blast_radius_factor=blast_val,
            max_euler_ale_discount_pct=spec.max_euler_ale_discount_pct,
            max_euler_var_discount_pct=spec.max_euler_var_discount_pct,
            classification_rationale=rationale,
            default_lef_annual=spec.default_lef_annual,
        )
