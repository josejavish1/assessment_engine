"""Epistemic Ledger Domain Models (RFC 082).

Defines immutable Pydantic v2 data models for raw utterances, phonetic normalization,
atomic epistemic fragments, evidence entries, and the reconciled epistemic ledger.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthorityRole(str, Enum):
    """Authority role classification for dialogue participants."""

    INTERVIEWER = "INTERVIEWER"
    SME_TECHNICAL = "SME_TECHNICAL"
    EXECUTIVE_SPONSOR = "EXECUTIVE_SPONSOR"
    UNKNOWN = "UNKNOWN"


class Polarity(str, Enum):
    """Epistemic polarity of an extracted factual assertion."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    CONTEXTUAL = "CONTEXTUAL"


class EpistemicState(str, Enum):
    """Temporal or operational state of an extracted assertion."""

    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    TARGET = "TARGET"
    HYPOTHETICAL = "HYPOTHETICAL"


class TruthStatus(str, Enum):
    """Reconciled truth status after multi-modal triangulation."""

    VERIFIED_CONSISTENT = "VERIFIED_CONSISTENT"
    VERIFIED_DISSONANT = "VERIFIED_DISSONANT"
    SINGLE_SOURCE_UNVERIFIED = "SINGLE_SOURCE_UNVERIFIED"
    REFUTED = "REFUTED"


class RawUtterance(BaseModel):
    """Represents a discrete raw speech turn extracted from an interview transcript."""

    model_config = ConfigDict(frozen=True)

    utterance_id: UUID = Field(default_factory=uuid4)
    sequence_index: int = Field(ge=1)
    source_file: str = "interview_transcript"
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    speaker_identifier: str = "Unknown"
    speaker_role: AuthorityRole = AuthorityRole.UNKNOWN
    raw_text: str

    @field_validator("raw_text")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        """Validate that raw utterance text is non-empty after stripping whitespace."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("raw_text must not be empty or whitespace only")
        return cleaned


class ResolvedEntity(BaseModel):
    """Tracks a single phonetic or semantic entity resolution applied to text."""

    model_config = ConfigDict(frozen=True)

    original_token: str
    canonical_entity: str
    resolution_method: Literal[
        "PHONETIC_CONTEXTUAL_LLM",
        "EXACT_ONTOLOGY_MATCH",
        "DOUBLE_METAPHONE",
        "MANUAL_OVERRIDE",
    ]
    phonetic_distance: float = Field(ge=0.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class NormalizedUtterance(BaseModel):
    """Represents an utterance whose phonetic Speech-to-Text corruptions have been resolved."""

    model_config = ConfigDict(frozen=True)

    utterance_id: UUID
    sequence_index: int = Field(ge=1)
    source_file: str = "interview_transcript"
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    speaker_identifier: str = "Unknown"
    speaker_role: AuthorityRole = AuthorityRole.UNKNOWN
    raw_text: str
    normalized_text: str
    resolved_entities: List[ResolvedEntity] = Field(default_factory=list)
    normalization_confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class EpistemicFragment(BaseModel):
    """An atomic factual assertion extracted from a primary evidence source."""

    model_config = ConfigDict(frozen=True)

    fragment_id: UUID = Field(default_factory=uuid4)
    utterance_id: Optional[UUID] = None
    source_type: Literal[
        "RAW_TRANSCRIPT", "EMPIRICAL_XLSX", "EMPIRICAL_TXT", "DOCUMENT_ATTACHMENT"
    ]
    source_file: str
    location_reference: str = Field(default="")
    domain_taxonomy_ref: str = Field(default="")
    canonical_assertion: str
    epistemic_weight: float = Field(ge=0.0, le=1.0, default=0.75)
    polarity: Polarity = Polarity.NEUTRAL
    state: EpistemicState = EpistemicState.CURRENT
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceEntry(BaseModel):
    """Triangulated, multi-source evidence entry reconciled in the epistemic ledger."""

    model_config = ConfigDict(frozen=True)

    entry_id: str
    domain_taxonomy_ref: str
    canonical_assertion: str
    truth_status: TruthStatus = TruthStatus.SINGLE_SOURCE_UNVERIFIED
    composite_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    dissonance_flag: bool = False
    dissonance_analysis: Optional[str] = None
    supporting_fragments: List[EpistemicFragment] = Field(default_factory=list)


class EpistemicLedger(BaseModel):
    """Immutable, board-verifiable Ground Truth ledger for an enterprise assessment."""

    model_config = ConfigDict(frozen=True)

    ledger_id: UUID = Field(default_factory=uuid4)
    client_id: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = "2.1.0-RFC082"
    epistemic_entries: List[EvidenceEntry] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def calculate_integrity_hash(self) -> str:
        """Computes a collision-resistant SHA-256 digest over canonicalized ledger entries."""
        sorted_entries = [
            e.model_dump(mode="json")
            for e in sorted(self.epistemic_entries, key=lambda x: x.entry_id)
        ]
        canonical_payload = json.dumps(
            {
                "client_id": self.client_id,
                "schema_version": self.schema_version,
                "epistemic_entries": sorted_entries,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
