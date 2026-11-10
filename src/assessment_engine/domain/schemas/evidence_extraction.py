"""Domain schemas for structured epistemic evidence extraction and modal partitioning.

Implements the Anthropic-style Tool Extraction pattern to categorize raw utterances into:
- ACTIVE_PRODUCTION: Empirically verified systems active in production today.
- FUTURE_PLAN: Aspirational desires, roadmap intentions, evaluation plans, or future wishes.
- CONFIRMED_ABSENCE: Explicitly confirmed gaps, deficits, or non-existent capabilities.

Enforces zero modal collapse in downstream AS-IS diagnostics by providing deterministic
context filtering methods. Strictly 100% Technical English and language-agnostic.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClaimStatus(str, Enum):
    """Universal epistemic status of an extracted technology claim."""

    ACTIVE_PRODUCTION = "ACTIVE_PRODUCTION"   # Active, running in live production today
    FUTURE_PLAN = "FUTURE_PLAN"               # Aspirational desire, roadmap, PoC, wish, TO-BE
    CONFIRMED_ABSENCE = "CONFIRMED_ABSENCE"   # Confirmed non-existence, gap, missing capability


class VerifiedEpistemicClaim(BaseModel):
    """Immutable, typed atomic claim extracted from source interview transcripts or documentation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_id: str = Field(description="Deterministic hash identifying this extracted claim.")
    tower_code: str = Field(description="Canonical tower code (e.g. T1, T2, ..., T10).")
    canonical_entity: str = Field(description="Normalized technology, protocol, or architectural component name.")
    claim_statement: str = Field(description="Technical English factual description of the claim.")
    status: ClaimStatus = Field(description="Epistemic modality: ACTIVE_PRODUCTION, FUTURE_PLAN, or CONFIRMED_ABSENCE.")
    verbatim_evidence_quote: str = Field(description="Exact source quotation from the transcript in its native language.")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction certainty score.")

    @classmethod
    def create(
        cls,
        tower_code: str,
        canonical_entity: str,
        claim_statement: str,
        status: ClaimStatus,
        verbatim_evidence_quote: str,
        confidence_score: float = 1.0,
    ) -> VerifiedEpistemicClaim:
        """Constructs an epistemic claim with deterministic SHA-256 claim ID."""
        clean_tower = str(tower_code).strip().upper()
        clean_entity = str(canonical_entity).strip()
        clean_statement = str(claim_statement).strip()
        clean_quote = str(verbatim_evidence_quote).strip()

        hasher = hashlib.sha256()
        for part in (clean_tower, clean_entity.lower(), clean_statement.lower(), clean_quote, status.value):
            hasher.update(part.encode("utf-8") + b"\x00")
        claim_id = f"CLM-{hasher.hexdigest()[:12].upper()}"

        return cls(
            claim_id=claim_id,
            tower_code=clean_tower,
            canonical_entity=clean_entity,
            claim_statement=clean_statement,
            status=status,
            verbatim_evidence_quote=clean_quote,
            confidence_score=confidence_score,
        )


class ExtractionLedger(BaseModel):
    """Container representing the complete, immutable set of extracted epistemic claims for a tenant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    claims: List[VerifiedEpistemicClaim] = Field(default_factory=list)

    @field_validator("claims", mode="after")
    @classmethod
    def deduplicate_claims(cls, claims: List[VerifiedEpistemicClaim]) -> List[VerifiedEpistemicClaim]:
        """Ensures claims with identical claim_id are deduplicated deterministically."""
        seen: set[str] = set()
        deduped: List[VerifiedEpistemicClaim] = []
        for c in claims:
            if c.claim_id not in seen:
                seen.add(c.claim_id)
                deduped.append(c)
        return deduped

    def get_asis_production_claims(self, tower_code: Optional[str] = None) -> List[VerifiedEpistemicClaim]:
        """Returns ONLY active production claims, strictly omitting all future aspirations."""
        filtered = [c for c in self.claims if c.status == ClaimStatus.ACTIVE_PRODUCTION]
        if tower_code:
            target = tower_code.strip().upper()
            filtered = [c for c in filtered if c.tower_code == target]
        return filtered

    def get_confirmed_absences(self, tower_code: Optional[str] = None) -> List[VerifiedEpistemicClaim]:
        """Returns explicitly confirmed gaps and absent capabilities."""
        filtered = [c for c in self.claims if c.status == ClaimStatus.CONFIRMED_ABSENCE]
        if tower_code:
            target = tower_code.strip().upper()
            filtered = [c for c in filtered if c.tower_code == target]
        return filtered

    def get_future_aspirations(self, tower_code: Optional[str] = None) -> List[VerifiedEpistemicClaim]:
        """Returns future desires, roadmap plans, and TO-BE aspirations for Volume 2."""
        filtered = [c for c in self.claims if c.status == ClaimStatus.FUTURE_PLAN]
        if tower_code:
            target = tower_code.strip().upper()
            filtered = [c for c in filtered if c.tower_code == target]
        return filtered

    @staticmethod
    def _sanitize_quote(quote: str, max_len: int = 500) -> str:
        import re
        clean = quote.replace('"', "'").replace("\r", " ").replace("\n", " ")
        clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:max_len]

    def build_asis_prompt_context(self, tower_code: str) -> str:
        """Constructs a mathematically isolated context for Volume 1 AS-IS synthesis.

        Guarantees that no FUTURE_PLAN tokens ever enter the AS-IS context space.
        """
        prod_claims = self.get_asis_production_claims(tower_code)
        absence_claims = self.get_confirmed_absences(tower_code)

        blocks: List[str] = []
        if prod_claims:
            blocks.append("=== CONFIRMED ACTIVE PRODUCTION SYSTEMS (AS-IS REALITY) ===")
            for c in prod_claims:
                safe_quote = self._sanitize_quote(c.verbatim_evidence_quote)
                blocks.append(f"- [{c.canonical_entity}]: {c.claim_statement} (Evidence: \"{safe_quote}\")")

        if absence_claims:
            blocks.append("\n=== CONFIRMED TECHNICAL ABSENCES AND VOIDS (DO NOT ASSUME ACTIVE) ===")
            for c in absence_claims:
                safe_quote = self._sanitize_quote(c.verbatim_evidence_quote)
                blocks.append(f"- [ABSENCE: {c.canonical_entity}]: {c.claim_statement} (Evidence: \"{safe_quote}\")")

        if not blocks:
            return "[EPISTEMIC_STATE: ZERO_EMPIRICAL_PRODUCTION_EVIDENCE_RECORDED]"

        return "\n".join(blocks)

    def build_tobe_prompt_context(self, tower_code: str) -> str:
        """Constructs a context of future aspirations and roadmap intents for Volume 2 TO-BE strategy."""
        tobe_claims = self.get_future_aspirations(tower_code)
        if not tobe_claims:
            return "[EPISTEMIC_STATE: ZERO_FUTURE_ASPIRATIONS_RECORDED]"
        blocks = ["=== CONFIRMED CLIENT ROADMAP & TRANSFORMATION ASPIRATIONS (TO-BE TARGETS) ==="]
        for c in tobe_claims:
            safe_quote = self._sanitize_quote(c.verbatim_evidence_quote)
            blocks.append(f"- [{c.canonical_entity}]: {c.claim_statement} (Evidence: \"{safe_quote}\")")
        return "\n".join(blocks)
