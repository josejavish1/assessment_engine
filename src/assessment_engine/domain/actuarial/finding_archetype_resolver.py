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

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
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
    FINOPS_RESOURCE_WASTE = "FINOPS_RESOURCE_WASTE"
    ENGINEERING_VELOCITY_FRICTION = "ENGINEERING_VELOCITY_FRICTION"
    REGULATORY_AND_BREACH = "REGULATORY_AND_BREACH"
    ASSET_OBSOLESCENCE_AND_INTEGRITY = "ASSET_OBSOLESCENCE_AND_INTEGRITY"

    def to_canonical_archetype(self) -> LossArchetypeType:
        """Maps finding-level physics to canonical Open FAIR loss archetype."""
        mapping = {
            FindingLossPhysics.AVAILABILITY_OUTAGE: LossArchetypeType.AVAILABILITY_OUTAGE,
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


@dataclass(frozen=True)
class PhysicsDefaultSpec:
    """Declarative actuarial parameter specification for a FindingLossPhysics class."""

    allows_downtime_burn: bool
    allows_secondary_regulatory_fallout: bool
    default_rto_hours: float
    default_blast_radius_factor: float
    max_euler_ale_discount_pct: float
    max_euler_var_discount_pct: float


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
        }


@lru_cache(maxsize=1)
def _load_external_physics_lexicon() -> dict[str, Sequence[re.Pattern[str]]]:
    """Loads multilingual semantic patterns from external declarative configuration if present."""
    candidates = (
        Path("engine_config/taxonomy/finding_physics_lexicon.json"),
        Path(__file__).resolve().parents[4] / "engine_config" / "taxonomy" / "finding_physics_lexicon.json",
    )
    for path in candidates:
        if path.is_file():
            try:
                raw_data = json.loads(path.read_text(encoding="utf-8"))
                return {
                    key: tuple(re.compile(pat, re.I) for pat in patterns if isinstance(pat, str))
                    for key, patterns in raw_data.items()
                    if isinstance(patterns, list)
                }
            except (OSError, ValueError):
                break
    return {}


class PolymorphicFindingClassifier:
    """Universal semantic and ontology classifier.

    Eliminates Tower-level archetype blindness and quarantines synthetic survey boilerplate.
    Contains 100% Technical English patterns in code, augmented by declarative external lexicons.
    """

    _PHYSICS_DEFAULTS: Final[Mapping[FindingLossPhysics, PhysicsDefaultSpec]] = {
        FindingLossPhysics.FINOPS_RESOURCE_WASTE: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            allows_secondary_regulatory_fallout=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.0,
            max_euler_ale_discount_pct=0.0,
            max_euler_var_discount_pct=0.0,
        ),
        FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            allows_secondary_regulatory_fallout=False,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.05,
            max_euler_ale_discount_pct=0.10,
            max_euler_var_discount_pct=0.15,
        ),
        FindingLossPhysics.REGULATORY_AND_BREACH: PhysicsDefaultSpec(
            allows_downtime_burn=False,
            allows_secondary_regulatory_fallout=True,
            default_rto_hours=0.0,
            default_blast_radius_factor=0.25,
            max_euler_ale_discount_pct=0.15,
            max_euler_var_discount_pct=0.25,
        ),
        FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            allows_secondary_regulatory_fallout=True,
            default_rto_hours=4.0,
            default_blast_radius_factor=0.15,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
        ),
        FindingLossPhysics.AVAILABILITY_OUTAGE: PhysicsDefaultSpec(
            allows_downtime_burn=True,
            allows_secondary_regulatory_fallout=True,
            default_rto_hours=8.0,
            default_blast_radius_factor=0.35,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
        ),
    }

    _BOILERPLATE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"lack\s+of\s+formalized\s+operational\s+controls\s+and\s+continuous\s+(monitoring|supervision)",
            re.I,
        ),
        re.compile(
            r"generalized\s+deficiency\s+in\s+documentary\s+governance\s+across\s+the\s+pillar",
            re.I,
        ),
    )

    _FINOPS_WASTE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(idle\s+vm|orphaned\s+vm|zombie\s+vm|unattached\s+(volume|disk|ebs)|"
            r"decommission(ing)?\s+of\s+(idle|unused|orphaned)|right[- ]?sizing|"
            r"finops|over[- ]?provisioned|unused\s+(instance|resource|license|compute)|"
            r"cloud\s+cost\s+optimization|cloud\s+sprawl|license\s+shelfware)\b",
            re.I,
        ),
    )

    _ENGINEERING_FRICTION_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(terraform|ansible|\biac\b|infrastructure\s+as\s+code|"
            r"ci/cd|gitops|kubernetes\s+csi|helm\s+chart|pipeline\s+automation|"
            r"manual\s+provisioning|manual\s+deployment|configuration\s+drift|"
            r"deployment\s+toil|static\s+os\s+imaging|golden\s+image\s+drift|autopilot)\b",
            re.I,
        ),
    )

    _OBSOLESCENCE_EOL_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(centos\s*[45678]?|rhel\s*[456]?|windows\s+server\s+200[38]|"
            r"oracle\s+10g|oracle\s+11g|forms\s+6i|"
            r"end[- ]of[- ]life|end[- ]of[- ]support|\beol\b|\beos\b|"
            r"legacy\s+os|unsupported\s+(os|firmware|database|kernel|runtime))\b",
            re.I,
        ),
    )

    _REGULATORY_BREACH_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(gdpr|lgpd|hipaa|pci[- ]dss|sox|nis2|dora|nerc[- ]cip|rgpd|"
            r"data\s+breach|data\s+exfiltration|unauthorized\s+disclosure|"
            r"pii|phi|unencrypted\s+data|regulatory\s+fine|statutory\s+penalty|"
            r"shared\s+privileged\s+account|shared\s+root)\b",
            re.I,
        ),
    )

    _CATASTROPHIC_OUTAGE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(single\s+point\s+of\s+failure|\bspof\b|"
            r"disaster\s+recovery|\bdrp\b|business\s+continuity\s+failure|"
            r"plant\s+stoppage|production\s+halt|scada\s+outage|blackout|"
            r"core\s+network\s+outage|ransomware\s+encryption|backup\s+failure|"
            r"dispatch\s+halt|weighbridge\s+outage|fiber\s+cut|clinical\s+triage\s+outage)\b",
            re.I,
        ),
    )

    @classmethod
    def _matches_category(
        cls,
        corpus: str,
        builtin_patterns: Sequence[re.Pattern[str]],
        lexicon_key: str,
    ) -> bool:
        if any(p.search(corpus) for p in builtin_patterns):
            return True
        ext_patterns = _load_external_physics_lexicon().get(lexicon_key, ())
        return any(p.search(corpus) for p in ext_patterns)

    @classmethod
    def classify_finding(
        cls,
        hc: Mapping[str, Any],
        tower_id: str,
    ) -> FindingPhysicsProfile:
        finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
        capability_text = str(hc.get("capability") or hc.get("title") or hc.get("name") or "").strip()
        impact_text = str(hc.get("business_risk") or hc.get("primary_impact") or "").strip()
        evidence_text = str(hc.get("evidence") or "").strip()
        vulnerability_text = str(hc.get("control_vulnerability") or "").strip()

        combined_corpus = " | ".join(
            filter(None, [finding_text, capability_text, impact_text, evidence_text, vulnerability_text])
        )

        # 1. Epistemic Provenance Evaluation
        epistemic_state = cls._evaluate_epistemic_state(hc, finding_text, impact_text, evidence_text)

        # 2. Explicit Payload Override Check
        explicit_physics = str(hc.get("loss_physics") or hc.get("loss_archetype") or "").strip().upper()
        if explicit_physics in FindingLossPhysics.__members__:
            physics = FindingLossPhysics[explicit_physics]
            return cls._build_profile(physics, epistemic_state, hc, "Explicit payload loss_physics tag")

        has_catastrophic_outage = cls._matches_category(
            combined_corpus, cls._CATASTROPHIC_OUTAGE_PATTERNS, "catastrophic_outage"
        )

        # 3. Semantic Causal Classification (Guarded against masking true catastrophic outages)
        # Priority A: FinOps / Idle Resource Waste (Only when not describing an operational outage)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._FINOPS_WASTE_PATTERNS, "finops_waste"
        ):
            return cls._build_profile(
                FindingLossPhysics.FINOPS_RESOURCE_WASTE,
                epistemic_state,
                hc,
                "Matched FinOps / idle resource waste semantic signature",
            )

        # Priority B: Engineering Velocity / IaC / DevOps Friction (Unless causing a catastrophic outage)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._ENGINEERING_FRICTION_PATTERNS, "engineering_friction"
        ):
            return cls._build_profile(
                FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
                epistemic_state,
                hc,
                "Matched Engineering / IaC / CI-CD operational friction signature",
            )

        # Priority C: Regulatory & Data Breach (Unless primary mechanics involve catastrophic service outage)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._REGULATORY_BREACH_PATTERNS, "regulatory_breach"
        ):
            return cls._build_profile(
                FindingLossPhysics.REGULATORY_AND_BREACH,
                epistemic_state,
                hc,
                "Matched Regulatory / Data Breach semantic signature",
            )

        # Priority D: Asset Obsolescence & EoL Integrity (Scoped workload blast radius)
        if not has_catastrophic_outage and cls._matches_category(
            combined_corpus, cls._OBSOLESCENCE_EOL_PATTERNS, "obsolescence_eol"
        ):
            return cls._build_profile(
                FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY,
                epistemic_state,
                hc,
                "Matched EoL / Asset Obsolescence semantic signature",
            )

        # Priority E: True Availability Outage or Tower Default (with scoped blast radius)
        return cls._build_profile(
            FindingLossPhysics.AVAILABILITY_OUTAGE,
            epistemic_state,
            hc,
            f"Resolved to Availability Outage physics for tower {tower_id}",
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
        ):
            return EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE

        combined = f"{finding_text} | {impact_text} | {evidence_text}"
        if cls._matches_category(combined, cls._BOILERPLATE_PATTERNS, "boilerplate"):
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
        )
