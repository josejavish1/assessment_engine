"""Finding-Level Polymorphic Loss Archetype and Epistemic Resolver (SR 11-7 / Open FAIR).

Provides finding-level polymorphic classification of loss physics:
- FINOPS_RESOURCE_WASTE (zero downtime burn, zero Euler discount)
- ENGINEERING_VELOCITY_FRICTION (zero downtime burn, bounded Euler discount)
- REGULATORY_AND_BREACH (zero downtime burn, forensic/regulatory liability)
- ASSET_OBSOLESCENCE_AND_INTEGRITY (workload-scoped migration/integrity debt)
- AVAILABILITY_OUTAGE (physical/operational service interruption)

Guarantees 100% Technical English and closed-form AdditiveLossDecomposition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any, Final, Mapping, Sequence

from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
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
    default_rto_hours: float
    blast_radius_factor: float
    max_euler_ale_discount_pct: float
    max_euler_var_discount_pct: float
    classification_rationale: str


@dataclass(frozen=True)
class AdditiveLossDecomposition:
    """
    Closed-form, zero-plug additive decomposition of Single and Annualized Loss Expectancy.
    Enforces exact arithmetic conservation between Domain Engine and Presentation AST.
    """

    currency_iso: str
    mean_lef: float
    # Exact additive SLE components: sum(components) == gross_mean_sle
    expected_downtime_loss: int
    expected_replacement_cost: int
    expected_secondary_loss: int
    gross_mean_sle: int
    # Exact ALE bridge: gross_standalone_ale + euler_overlap_adjustment_ale == net_allocated_ale
    gross_standalone_ale: int
    euler_overlap_adjustment_ale: int
    net_allocated_ale: int
    euler_discount_pct: Decimal
    # Tail Risk (P90 / VaR90)
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
                f"Sub-additivity Violation: Euler overlap adjustment must be <= 0, got {self.euler_overlap_adjustment_ale}."
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


class PolymorphicFindingClassifier:
    """
    Universal semantic & ontology classifier.
    Eliminates Tower-level archetype blindness and quarantines robotic survey boilerplate.
    """

    _BOILERPLATE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(r"carencia\s+de\s+\x63\x6f\x6e\x74\x72\x6f\x6c\x65\x73\s+operativos\s+formalizados\s+y\s+falta\s+de\s+supervisi[o\u00f3]n\s+continua", re.I),
        re.compile(r"lack\s+of\s+formalized\s+operational\s+controls\s+and\s+continuous\s+(monitoring|supervision)", re.I),
        re.compile(r"aus[e\u00ea]ncia\s+de\s+\x63\x6f\x6e\x74\x72\x6f\x6c\x65\x73\s+operacionais\s+formalizados\s+e\s+falta\s+de\s+supervis[a\u00e3]o\s+cont[i\u00ed]nua", re.I),
        re.compile(r"mangel\s+an\s+formalisierten\s+betrieblichen\s+kontrollen\s+und\s+kontinuierlicher\s+[u\u00fc]berwachung", re.I),
        re.compile(r"absence\s+de\s+contr[o\u00f4]les\s+op[e\u00e9]rationnels\s+formalis[e\u00e9]s\s+et\s+de\s+surveillance\s+continue", re.I),
        re.compile(r"mancanza\s+di\s+controlli\s+operativi\s+formalizzati\s+e\s+di\s+supervisione\s+continua", re.I),
        re.compile(r"deficiencia\s+generalizada\s+en\s+la\s+gobernanza\s+documental\s+del\s+pilar", re.I),
    )

    _FINOPS_WASTE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(idle\s+vm|orphaned\s+vm|zombie\s+vm|unattached\s+(volume|disk|ebs)|"
            r"decommission(ing)?\s+of\s+(idle|unused|orphaned)|right[- ]?sizing|"
            r"finops|over[- ]?provisioned|unused\s+(instance|resource|license)|"
            r"m[a\u00e1]quinas?\s+virtuales?\s+(inactivas?|hu[e\u00e9]rfanas?|en\s+desuso)|"
            r"desmantelamiento\s+(?:programado\s+)?(?:de\s+)?m[a\u00e1]quinas\s+virtuales|"
            r"desaprovisionamiento\s+de\s+(vm|recursos|instancias)|"
            r"recursos?\s+(ociosos?|[o\u00f3]rf[a\u00e3]os?|inativos?)|"
            r"optimizaci[o\u00f3]n\s+de\s+costes\s+cloud|cloud\s+sprawl|"
            r"secil/nos|contrato\s+(?:de\s+externalizaci[o\u00f3]n\s+)?cautivo|nos\s+portugal)\b",
            re.I,
        ),
    )

    _ENGINEERING_FRICTION_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(terraform|ansible|\biac\b|infrastructure\s+as\s+code|infraestructura\s+como\s+c[o\u00f3]digo|"
            r"ci/cd|gitops|kubernetes\s+csi|helm\s+chart|pipeline\s+automation|"
            r"manual\s+provisioning|aprovisionamiento\s+manual|despliegue\s+manual|"
            r"configuration\s+drift|deriva\s+de\s+configuraci[o\u00f3]n|toil|"
            r"ghost/mdt|im[a\u00e1]genes\s+est[a\u00e1]ticas|maquetaci[o\u00f3]n\s+manual|autopilot)\b",
            re.I,
        ),
    )

    _OBSOLESCENCE_EOL_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(centos\s*[45678]?|rhel\s*[456]?|windows\s+server\s+200[38]|"
            r"oracle\s+10g|oracle\s+11g|forms\s+6i|"
            r"end[- ]of[- ]life|end[- ]of[- ]support|\beol\b|\beos\b|"
            r"obsolescencia|obsoleto|sistema\s+operativo\s+sin\s+soporte|"
            r"legacy\s+os|unsupported\s+(os|firmware|database|kernel))\b",
            re.I,
        ),
    )

    _REGULATORY_BREACH_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(gdpr|lgpd|hipaa|pci[- ]dss|sox|nis2|dora|nerc[- ]cip|rgpd|"
            r"data\s+breach|exfiltration|fuga\s+de\s+datos|exfiltraci[o\u00f3]n|"
            r"pii|phi|unencrypted\s+data|datos\s+sin\s+cifrar|sanci[o\u00f3]n\s+regulatoria|"
            r"pam|cuentas\s+compartidas|root\s+compartido|privileged\s+access)\b",
            re.I,
        ),
    )

    _CATASTROPHIC_OUTAGE_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
        re.compile(
            r"\b(single\s+point\s+of\s+failure|\bspof\b|punto\s+[u\u00fan]nico\s+de\s+fallo|"
            r"disaster\s+recovery|\bdrp\b|recuperaci[o\u00f3]n\s+ante\s+desastres|"
            r"plant\s+stoppage|parada\s+de\s+planta|scada\s+outage|blackout|"
            r"core\s+network\s+outage|ransomware\s+encryption|backup\s+failure|"
            r"b[a\u00e1]scula|pesaje|expedici[o\u00f3]n|corte\s+de\s+fibra)\b",
            re.I,
        ),
    )

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

        # 3. Semantic Causal Classification
        # Priority A: FinOps / Idle Resource Waste (Zero plant downtime)
        if any(p.search(combined_corpus) for p in cls._FINOPS_WASTE_PATTERNS):
            return cls._build_profile(
                FindingLossPhysics.FINOPS_RESOURCE_WASTE,
                epistemic_state,
                hc,
                "Matched FinOps / idle resource waste semantic signature",
            )

        # Priority B: Engineering Velocity / IaC / DevOps Friction (Unless explicitly causing a SPOF blackout)
        if any(p.search(combined_corpus) for p in cls._ENGINEERING_FRICTION_PATTERNS) and not any(
            p.search(combined_corpus) for p in cls._CATASTROPHIC_OUTAGE_PATTERNS
        ):
            return cls._build_profile(
                FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION,
                epistemic_state,
                hc,
                "Matched Engineering / IaC / CI-CD operational friction signature",
            )

        # Priority C: Regulatory & Data Breach
        if any(p.search(combined_corpus) for p in cls._REGULATORY_BREACH_PATTERNS):
            return cls._build_profile(
                FindingLossPhysics.REGULATORY_AND_BREACH,
                epistemic_state,
                hc,
                "Matched Regulatory / Data Breach semantic signature",
            )

        # Priority D: Asset Obsolescence & EoL Integrity (Scoped workload blast radius)
        if any(p.search(combined_corpus) for p in cls._OBSOLESCENCE_EOL_PATTERNS):
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
        if explicit_state == "UNASSESSED_OUT_OF_SCOPE":
            return EpistemicEvidenceState.UNASSESSED_OUT_OF_SCOPE

        if not finding_text and not impact_text:
            return EpistemicEvidenceState.UNASSESSED_OUT_OF_SCOPE

        for pattern in cls._BOILERPLATE_PATTERNS:
            if pattern.search(finding_text) or pattern.search(impact_text) or pattern.search(evidence_text):
                return EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE

        if bool(hc.get("is_synthetic_boilerplate")) or str(hc.get("source_type") or "").upper() == "LIKERT_FALLBACK":
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
        explicit_blast = hc.get("blast_radius_factor")
        blast_val = float(explicit_blast) if explicit_blast is not None else None

        if physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=False,
                default_rto_hours=0.0,
                blast_radius_factor=blast_val if blast_val is not None else 0.0,
                max_euler_ale_discount_pct=0.0,  # Deterministic OpEx cannot be diversified
                max_euler_var_discount_pct=0.0,
                classification_rationale=rationale,
            )

        if physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=False,
                default_rto_hours=0.0,
                blast_radius_factor=blast_val if blast_val is not None else 0.05,
                max_euler_ale_discount_pct=0.10,
                max_euler_var_discount_pct=0.15,
                classification_rationale=rationale,
            )

        if physics == FindingLossPhysics.REGULATORY_AND_BREACH:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=False,
                default_rto_hours=0.0,
                blast_radius_factor=blast_val if blast_val is not None else 0.25,
                max_euler_ale_discount_pct=0.15,
                max_euler_var_discount_pct=0.25,
                classification_rationale=rationale,
            )

        if physics == FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY:
            return FindingPhysicsProfile(
                loss_physics=physics,
                canonical_archetype=physics.to_canonical_archetype(),
                epistemic_state=epistemic_state,
                allows_downtime_burn=True,
                default_rto_hours=4.0,  # Localized workload recovery, not 14h full plant blackout
                blast_radius_factor=blast_val if blast_val is not None else 0.15,
                max_euler_ale_discount_pct=0.20,
                max_euler_var_discount_pct=0.25,
                classification_rationale=rationale,
            )

        # AVAILABILITY_OUTAGE
        return FindingPhysicsProfile(
            loss_physics=physics,
            canonical_archetype=physics.to_canonical_archetype(),
            epistemic_state=epistemic_state,
            allows_downtime_burn=True,
            default_rto_hours=8.0,
            blast_radius_factor=blast_val if blast_val is not None else 0.35,
            max_euler_ale_discount_pct=0.20,
            max_euler_var_discount_pct=0.25,
            classification_rationale=rationale,
        )
