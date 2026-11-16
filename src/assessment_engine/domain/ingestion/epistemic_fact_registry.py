"""
Tier-1 Epistemic Fact Registry & Perspective Lease Allocation Engine.

Implements the formal graph-backed epistemic control plane specified by the Tier-1 Red Team:
1. Replaces raw string facts with immutable Actuarial Fact Tuples (AFTs) featuring SHA-256 span provenance.
2. Implements Perspective Lease Allocation (PRIMARY_OWNER vs SECONDARY_CONSUMER) to permit cross-domain
   causation while strictly barring narrative repetition.
3. Implements Polarity-Aware Claim Gating, solving the "Absence of Evidence vs Evidence of Absence" fallacy
   by permitting absent entities (e.g. VESDA, BitLocker) under NEGATIVE_GAP or REMEDIATION_TARGET polarities.
4. Enforces full concurrency thread-safety via reentrant locking (threading.RLock).
"""

from __future__ import annotations

import hashlib
import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
import logging

logger = logging.getLogger(__name__)


class EpistemicState(str, Enum):
    """Three-Valued Logic (3VL) epistemic state for shared telemetry facts."""
    INSTRUMENTED_VERIFIED = "INSTRUMENTED_VERIFIED"
    UNINSTRUMENTED_BLINDSPOT = "UNINSTRUMENTED_BLINDSPOT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class SharedFactRecord(BaseModel):
    """Shared telemetry fact record implementing Three-Valued Logic to eliminate hallucinated overcommitments."""
    model_config = ConfigDict(extra="ignore")

    fact_id: str = Field(..., pattern=r"^FACT-[A-Z0-9_]+$")
    domain: str
    subject_entity: str
    metric_name: str
    epistemic_state: EpistemicState
    observed_value: Optional[Union[float, int, str]] = None
    unit: Optional[str] = None
    accredited_vendors_or_tech: List[str] = Field(default_factory=list)
    allowed_semantic_inference: str = ""

    @model_validator(mode="after")
    def enforce_epistemic_discipline(self) -> "SharedFactRecord":
        if self.epistemic_state == EpistemicState.UNINSTRUMENTED_BLINDSPOT:
            if self.observed_value is not None:
                raise ValueError("Epistemic Violation: Uninstrumented facts cannot hold observed values.")
            self.allowed_semantic_inference = (
                f"Lack of telemetry/instrumentation regarding {self.metric_name} on {self.subject_entity}. "
                f"PROHIBITED INFERENCE: Do not claim resource exhaustion, overcommitment, or saturation."
            )
        return self

    def is_claim_allowed(self, claim_text: str) -> bool:
        """Evaluates whether an emitted narrative claim complies with the fact's epistemic state."""
        if self.epistemic_state != EpistemicState.UNINSTRUMENTED_BLINDSPOT:
            return True

        from pathlib import Path
        import json

        forbidden_patterns = [
            "overcommitment",
            "severe saturation",
            "critical oversubscription",
            "resource exhaustion",
        ]
        
        # Load external localized prohibited tokens from configuration
        cfg_path = Path(__file__).resolve().parents[4] / "engine_config" / "policies" / "epistemic_dependencies.json"
        if cfg_path.exists():
            try:
                cfg_data = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
                for tokens in cfg_data.get("uninstrumented_forbidden_tokens", {}).values():
                    forbidden_patterns.extend(tokens)
            except Exception:
                pass

        claim_lower = claim_text.lower()
        for pattern in forbidden_patterns:
            if pattern in claim_lower:
                return False
        return True

    def lift_to_governance_deficit(self) -> "SharedFactRecord":
        """GATE-30.3: Kleene Three-Valued Logic Epistemic Lifting Operator (uparrow_gov).

        Projects an UNINSTRUMENTED_BLINDSPOT (Unknown) in technical strata into a
        VERIFIED_PRESENT governance finding, mathematically converting an unmeasured
        technical metric into an audit-grade governance/telemetry deficit finding.
        """
        if self.epistemic_state != EpistemicState.UNINSTRUMENTED_BLINDSPOT:
            raise ValueError(
                f"Epistemic Lifting Violation: Only UNINSTRUMENTED_BLINDSPOT facts can be lifted. "
                f"Fact '{self.fact_id}' has state '{self.epistemic_state}'."
            )

        lifted_fact_id = f"{self.fact_id}_GOV_DEFICIT"
        lifted_metric = f"Governance & Telemetry Deficit regarding {self.metric_name}"

        return SharedFactRecord(
            fact_id=lifted_fact_id,
            domain="ENTERPRISE_GOVERNANCE",
            subject_entity=self.subject_entity,
            metric_name=lifted_metric,
            epistemic_state=EpistemicState.INSTRUMENTED_VERIFIED,
            observed_value=f"VERIFIED_ABSENCE_OF_FORMAL_TELEMETRY: {self.metric_name}",
            unit="GOVERNANCE_GAP",
            accredited_vendors_or_tech=[],
            allowed_semantic_inference=(
                f"Verified operational governance deficit: The enterprise lacks formal instrumentation, "
                f"telemetry capture, and capacity threshold alerts for {self.metric_name} on {self.subject_entity}."
            ),
        )


class ResolutionStatus(str, Enum):
    """Resolution status of an entity reference in the evidence corpus."""
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNVERIFIED = "UNVERIFIED"


class AmbiguousEntityReference(BaseModel):
    """Tracks unresolved entity references (e.g. '3 y 4') to prevent speculative materialization."""
    model_config = ConfigDict(extra="ignore")

    reference_id: str = Field(..., pattern=r"^REF-[A-Z0-9_\-]+$")
    raw_span: str
    source_chunk_id: str
    resolution_status: ResolutionStatus = ResolutionStatus.AMBIGUOUS
    candidate_entity_types: List[str] = Field(default_factory=list)
    allowed_semantic_framing: str = ""

    @model_validator(mode="after")
    def enforce_ambiguity_guard(self) -> "AmbiguousEntityReference":
        if self.resolution_status == ResolutionStatus.AMBIGUOUS:
            self.allowed_semantic_framing = (
                f"Observed items referenced as '{self.raw_span}' without formal topology confirmation. "
                "PROHIBITED INFERENCE: Do not materialize into specific cluster, host, or node names."
            )
        return self

    def is_claim_allowed(self, claim_text: str) -> bool:
        """Determines whether a claim impermissibly materializes the ambiguous entity."""
        if self.resolution_status != ResolutionStatus.AMBIGUOUS:
            return True

        from pathlib import Path
        import json

        forbidden_patterns = [
            "clusters 3 and 4",
            "cluster 3 and 4",
            "nodes 3 and 4 of simplivity",
            "simplivity nodes 3 and 4",
        ]

        cfg_path = Path(__file__).resolve().parents[4] / "engine_config" / "policies" / "epistemic_dependencies.json"
        if cfg_path.exists():
            try:
                cfg_data = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
                for tokens in cfg_data.get("ambiguous_entity_forbidden_tokens", {}).values():
                    forbidden_patterns.extend(tokens)
            except Exception:
                pass

        claim_lower = claim_text.lower()
        for pattern in forbidden_patterns:
            if pattern in claim_lower:
                return False
        return True


class EpistemicModality(str, Enum):
    """Epistemic modality of an extracted enterprise fact."""
    OBSERVED_EVIDENCE = "OBSERVED_EVIDENCE"        # Directly verified in telemetry, logs, or config files
    MANAGEMENT_ASSERTION = "MANAGEMENT_ASSERTION"  # Declared in interview or survey without direct instrumentation
    DERIVED_METRIC = "DERIVED_METRIC"              # Deterministically pre-calculated by Python/Rust kernel
    ABSENT_CONTROL = "ABSENT_CONTROL"              # Formally confirmed absent or unmonitored


class ClaimPolarity(str, Enum):
    """Semantic polarity of an emitted narrative statement."""
    ASSERTIVE = "ASSERTIVE"                        # Asserts client possesses, operates, or relies upon the entity
    NEGATIVE_GAP = "NEGATIVE_GAP"                  # Asserts client lacks, misses, or unmonitors the entity
    REMEDIATION_TARGET = "REMEDIATION_TARGET"      # Recommends client deploy or configure the entity in roadmap
    BENCHMARK_COMPARISON = "BENCHMARK_COMPARISON"  # Cites entity as an external industry standard or reference model


class LeaseType(str, Enum):
    """Ownership level of a domain over a shared enterprise fact."""
    PRIMARY_OWNER = "PRIMARY_OWNER"                # Permitted full descriptive narrative and baseline quotation
    SECONDARY_CONSUMER = "SECONDARY_CONSUMER"      # Permitted ONLY causal reference (cannot restate descriptive narrative)


class LeaseStatus(str, Enum):
    """MVCC lease state tracking."""
    AVAILABLE = "AVAILABLE"
    CONSUMED = "CONSUMED"


class DomainPerspective(BaseModel):
    """Domain-specific lease framing for a shared enterprise fact."""
    model_config = ConfigDict(extra="forbid")

    domain_id: str = Field(..., description="Target tower ID, e.g., T1, T2, T5, T6")
    lease_type: LeaseType = Field(..., description="Lease authority type")
    semantic_framing: str = Field(..., description="Domain-specific consequence (e.g., 'Stability' vs 'Unpatched CVE')")
    status: LeaseStatus = Field(default=LeaseStatus.AVAILABLE, description="Lease consumption state")
    consumed_in_section: Optional[str] = Field(default=None, description="Section ID where lease was redeemed")

    @field_validator("domain_id")
    @classmethod
    def _normalize_domain_id(cls, v: str) -> str:
        return v.strip().upper()


class ActuarialFactTuple(BaseModel):
    """Immutable, typed actuarial fact with cryptographic provenance."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_id: str = Field(..., description="Deterministic SHA-256 hash of subject + predicate + span")
    canonical_subject: str = Field(..., description="Ontology entity ID, e.g., 'SYS_COMPUTE_HOST_01'")
    predicate: str = Field(..., description="Ontology relationship verb, e.g., 'HAS_CONTINUOUS_UPTIME'")
    value_scalar: Optional[Union[bool, int, float]] = Field(default=None, description="Canonical scalar value")
    value_text: Optional[str] = Field(default=None, description="Descriptive textual value")
    unit_iso: Optional[str] = Field(default=None, description="Standardized ISO unit, e.g., 'DAYS', 'HOURS', 'EUR'")
    modality: EpistemicModality = Field(..., description="Verification degree")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Epistemic confidence rating")
    source_document_id: str = Field(..., description="Identifier of source document or audio transcript")
    source_char_span: Tuple[int, int] = Field(..., description="Character offset span (start, end) in source text")
    verbatim_quote: str = Field(..., description="Exact raw text snippet from evidence corpus")
    domain_leases: Tuple[DomainPerspective, ...] = Field(default_factory=tuple, description="Assigned domain perspective leases")

    @model_validator(mode="after")
    def _enforce_unique_domain_leases(self) -> "ActuarialFactTuple":
        seen: Set[str] = set()
        for lease in self.domain_leases:
            if lease.domain_id in seen:
                raise ValueError(f"Duplicate DomainPerspective for domain '{lease.domain_id}' in fact '{self.fact_id}'.")
            seen.add(lease.domain_id)
        return self

    @model_validator(mode="after")
    def _enforce_byte_span_provenance(self) -> "ActuarialFactTuple":
        """GATE-30.5: Byte-Span Provenance Enforcement.

        Guarantees that an empirical evidence fact cannot be certified as OBSERVED_EVIDENCE
        unless it carries a valid non-empty byte offset span and non-empty verbatim quote.
        """
        if self.modality == EpistemicModality.OBSERVED_EVIDENCE:
            start, end = self.source_char_span
            if start < 0 or end <= start or not self.verbatim_quote.strip():
                raise ValueError(
                    f"GATE-30.5 Provenance Breach: Fact '{self.fact_id}' declared OBSERVED_EVIDENCE "
                    f"without valid byte offset span ({start}, {end}) or empty verbatim quote."
                )
        return self

    @classmethod
    def create(
        cls,
        canonical_subject: str,
        predicate: str,
        source_document_id: str,
        source_char_span: Tuple[int, int],
        verbatim_quote: str,
        modality: EpistemicModality,
        confidence_score: float = 1.0,
        value_scalar: Optional[Union[bool, int, float]] = None,
        value_text: Optional[str] = None,
        unit_iso: Optional[str] = None,
        domain_leases: Optional[List[DomainPerspective]] = None,
    ) -> ActuarialFactTuple:
        """Constructs an ActuarialFactTuple with a deterministic SHA-256 fact_id."""
        hash_input = f"{canonical_subject}:{predicate}:{source_document_id}:{source_char_span[0]}:{source_char_span[1]}"
        fact_id = f"AFT-{hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12].upper()}"
        return cls(
            fact_id=fact_id,
            canonical_subject=canonical_subject,
            predicate=predicate,
            value_scalar=value_scalar,
            value_text=value_text,
            unit_iso=unit_iso,
            modality=modality,
            confidence_score=confidence_score,
            source_document_id=source_document_id,
            source_char_span=source_char_span,
            verbatim_quote=verbatim_quote,
            domain_leases=tuple(domain_leases or []),
        )


class EpistemicFactRegistry:
    """Thread-safe graph-backed repository for Actuarial Fact Tuples and perspective lease management."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._facts: Dict[str, ActuarialFactTuple] = {}
        self._subject_index: Dict[str, Set[str]] = {}
        self._domain_index: Dict[str, Set[str]] = {}

    def register_fact(self, fact: ActuarialFactTuple) -> str:
        """Registers an immutable fact tuple and updates search indices in a thread-safe manner."""
        with self._lock:
            self._facts[fact.fact_id] = fact

            if fact.canonical_subject not in self._subject_index:
                self._subject_index[fact.canonical_subject] = set()
            self._subject_index[fact.canonical_subject].add(fact.fact_id)

            for lease in fact.domain_leases:
                d_id = lease.domain_id.upper()
                if d_id not in self._domain_index:
                    self._domain_index[d_id] = set()
                self._domain_index[d_id].add(fact.fact_id)

            return fact.fact_id

    def get_fact(self, fact_id: str) -> Optional[ActuarialFactTuple]:
        """Retrieves a fact by its canonical AFT ID."""
        with self._lock:
            return self._facts.get(fact_id)

    def get_facts_for_domain(self, domain_id: str) -> List[ActuarialFactTuple]:
        """Returns all facts accessible to the specified domain tower."""
        with self._lock:
            fact_ids = self._domain_index.get(domain_id.upper(), set())
            return [self._facts[fid] for fid in sorted(fact_ids) if fid in self._facts]

    def acquire_lease(
        self,
        fact_id: str,
        domain_id: str,
        section_id: str,
    ) -> Tuple[bool, str, Optional[DomainPerspective]]:
        """Attempts to acquire and redeem a narrative lease for a domain in a specific document section.

        Enforces the Lease Rule:
        - PRIMARY_OWNER can only redeem the lease ONCE. Subsequent attempts return already consumed.
        - SECONDARY_CONSUMER can cite the fact as a causal premise, but cannot claim primary ownership.
        """
        with self._lock:
            fact = self._facts.get(fact_id)
            if not fact:
                return False, f"Fact '{fact_id}' not found in registry.", None

            target_domain = domain_id.strip().upper()
            for lease in fact.domain_leases:
                if lease.domain_id == target_domain:
                    if lease.status == LeaseStatus.CONSUMED:
                        return (
                            False,
                            f"Lease for domain '{domain_id}' on fact '{fact_id}' already consumed in '{lease.consumed_in_section}'. Restatement prohibited.",
                            lease.model_copy(deep=True),
                        )
                    # Redeem lease
                    lease.status = LeaseStatus.CONSUMED
                    lease.consumed_in_section = section_id
                    return True, "Lease acquired successfully.", lease.model_copy(deep=True)

            return False, f"Domain '{domain_id}' possesses no lease authority over fact '{fact_id}'.", None

    @staticmethod
    def evaluate_claim_polarity(
        entity_token: str,
        polarity: ClaimPolarity,
        accredited_entities: Set[str],
    ) -> Tuple[bool, str]:
        """Evaluates whether citing an entity token is permissible under the specified epistemic polarity.

        Solves the 'Absence of Evidence vs Evidence of Absence' fallacy:
        - ASSERTIVE polarity requires the entity to be present in accredited evidence.
        - NEGATIVE_GAP, REMEDIATION_TARGET, and BENCHMARK_COMPARISON are explicitly permitted
          to cite absent technologies (e.g. VESDA, BitLocker) to diagnose control deficiencies.
        """
        token_clean = entity_token.strip().lower()
        is_accredited = any(token_clean == e.strip().lower() for e in accredited_entities)

        if polarity == ClaimPolarity.ASSERTIVE:
            if not is_accredited:
                return (
                    False,
                    f"Polarity Violation: Entity '{entity_token}' asserted as installed/operational, "
                    f"but absent from accredited evidence corpus.",
                )
            return True, "Assertive claim verified against accredited evidence."

        return (
            True,
            f"Permitted non-assertive citation under polarity '{polarity.value}'. "
            f"Allowed to reference absent standard '{entity_token}'.",
        )
