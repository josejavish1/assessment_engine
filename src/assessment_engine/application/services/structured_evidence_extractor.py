"""Application service for structured epistemic evidence extraction from raw multilingual interview transcripts.

Uses structured reasoning without hardcoding physical model names (parameterized via ModelTier).
Classifies raw utterances across any human language into:
- ACTIVE_PRODUCTION
- FUTURE_PLAN
- CONFIRMED_ABSENCE

Strictly 100% Technical English, zero client coupling, robust schema validation.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from assessment_engine.domain.schemas.evidence_extraction import (
    ClaimStatus,
    ExtractionLedger,
    VerifiedEpistemicClaim,
)
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

logger = logging.getLogger(__name__)


class StructuredEvidenceExtractor:
    """Extracts typed epistemic claims from raw transcripts using structured reasoning."""

    EXTRACTION_SYSTEM_DIRECTIVE = """You are a Formal Epistemic Logic Parser and Lead Due Diligence Systems Auditor.
Your objective is to analyze interview transcripts (which may be in Spanish, English, German, Portuguese, French, Japanese, etc.)
and extract strictly verified, atomic technology claims into structured JSON.

CRITICAL MODAL DISAMBIGUATION RULES (ZERO TOLERANCE FOR MODAL COLLAPSE):
1. ACTIVE_PRODUCTION: The client explicitly states that this system, hardware, vendor, or process is currently implemented, active, and operating in live production today.
2. FUTURE_PLAN: The speaker expresses a desire, wish, ambition, future roadmap, evaluation, planned trial, or target architecture (e.g. intending to adopt, planning to migrate, evaluating options, future roadmap items). You MUST tag these strictly as FUTURE_PLAN. NEVER mark them as ACTIVE_PRODUCTION.
3. CONFIRMED_ABSENCE: The speaker explicitly states that a capability, tool, process, or redundancy does NOT exist, is lacking, is completely missing, or is zero (e.g. absence of tooling, lacking automation, zero DR validation).

OUTPUT SPECIFICATION:
Output ONLY a valid JSON object matching this schema:
{
  "claims": [
    {
      "tower_code": "<Canonical tower code: T1, T2, T3, T4, T5, T6, T7, T8, T9, or T10>",
      "canonical_entity": "<Normalized technology, protocol, or architectural component name>",
      "claim_statement": "<Clear, concise Technical English factual description of the claim>",
      "status": "<ACTIVE_PRODUCTION | FUTURE_PLAN | CONFIRMED_ABSENCE>",
      "verbatim_evidence_quote": "<Exact unaltered source quote from the transcript in its native language>",
      "confidence_score": 1.0
    }
  ]
}
"""

    def __init__(self, model_tier: ModelTier = ModelTier.REASONING) -> None:
        self._model_tier = model_tier
        self._client = create_genai_client()
        self._router = None

    @property
    def router(self):
        """Lazily instantiates and caches EpistemicGraphRouter once to eliminate per-claim disk IO."""
        if self._router is None:
            from assessment_engine.application.services.semantic_epistemic_router import (
                EpistemicGraphRouter,
            )
            self._router = EpistemicGraphRouter()
        return self._router

    def extract_claims_from_text(
        self,
        tenant_id: str,
        transcript_content: str,
        active_towers: Optional[List[str]] = None,
    ) -> ExtractionLedger:
        """Parses multilingual transcript into typed ExtractionLedger using semantic reasoning."""
        if not transcript_content or not transcript_content.strip():
            return ExtractionLedger(tenant_id=tenant_id, claims=[])

        model_name = get_model(self._model_tier)
        towers_filter_prompt = f"\nFocus on evidence applicable to active domains: {', '.join(active_towers)}." if active_towers else ""

        full_prompt = (
            f"{self.EXTRACTION_SYSTEM_DIRECTIVE}\n"
            f"{towers_filter_prompt}\n\n"
            f"INPUT TRANSCRIPT CONTENT FOR TENANT '{tenant_id}':\n"
            f"\"\"\"\n{transcript_content}\n\"\"\"\n"
        )

        try:
            import re
            response = self._client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config={"response_mime_type": "application/json"},
            )
            raw_text = (response.text or "{}").strip()
            # Non-greedy extraction targeting explicit claims object or array, avoiding preamble brackets
            clean_json = raw_text
            obj_match = re.search(r"(\{\s*\"claims\"\s*:\s*\[.*\]\s*\})", raw_text, re.DOTALL)
            if obj_match:
                clean_json = obj_match.group(1)
            else:
                match = re.search(r"(\{\s*\".*\"\s*:.*\}|\[\s*\{.*\}\s*\])", raw_text, re.DOTALL)
                if match:
                    clean_json = match.group(1)

            parsed = json.loads(clean_json)
            if isinstance(parsed, list):
                raw_claims = parsed
            elif isinstance(parsed, dict):
                raw_claims = parsed.get("claims", [])
            else:
                raw_claims = []

            from assessment_engine.application.services.semantic_epistemic_router import CANONICAL_TOWERS

            # Canonical synonym mapping
            synonym_map = {
                "CURRENT": ClaimStatus.ACTIVE_PRODUCTION,
                "IMPLEMENTED": ClaimStatus.ACTIVE_PRODUCTION,
                "ACTIVE": ClaimStatus.ACTIVE_PRODUCTION,
                "PRODUCTION": ClaimStatus.ACTIVE_PRODUCTION,
                "ACTIVE_PRODUCTION": ClaimStatus.ACTIVE_PRODUCTION,
                "PLANNED": ClaimStatus.FUTURE_PLAN,
                "ROADMAP": ClaimStatus.FUTURE_PLAN,
                "POC": ClaimStatus.FUTURE_PLAN,
                "EVALUATION": ClaimStatus.FUTURE_PLAN,
                "FUTURE": ClaimStatus.FUTURE_PLAN,
                "FUTURE_PLAN": ClaimStatus.FUTURE_PLAN,
                "MISSING": ClaimStatus.CONFIRMED_ABSENCE,
                "NONE": ClaimStatus.CONFIRMED_ABSENCE,
                "ABSENT": ClaimStatus.CONFIRMED_ABSENCE,
                "GAP": ClaimStatus.CONFIRMED_ABSENCE,
                "DEFICIT": ClaimStatus.CONFIRMED_ABSENCE,
                "CONFIRMED_ABSENCE": ClaimStatus.CONFIRMED_ABSENCE,
            }

            verified_claims: List[VerifiedEpistemicClaim] = []
            for item in raw_claims:
                if not isinstance(item, dict):
                    continue
                try:
                    status_raw = str(item.get("status") or "").upper().strip()
                    resolved_status = synonym_map.get(status_raw)
                    if not resolved_status:
                        logger.warning("Skipping claim with unrecognized epistemic status: '%s'", status_raw)
                        continue

                    raw_tower = str(item.get("tower_code") or "").upper().strip()
                    if raw_tower in CANONICAL_TOWERS:
                        tower_code = raw_tower
                    elif active_towers and len(active_towers) == 1:
                        tower_code = active_towers[0]
                    else:
                        claim_summary = f"{item.get('canonical_entity', '')} {item.get('claim_statement', '')}"
                        affinities = self.router.compute_affinities(claim_summary)
                        best_candidate = max(affinities.items(), key=lambda kv: kv[1])[0] if affinities else "UNASSIGNED"
                        tower_code = best_candidate if affinities.get(best_candidate, 0.0) >= 0.15 else "UNASSIGNED"

                    try:
                        raw_conf = float(item.get("confidence_score") if item.get("confidence_score") is not None else 1.0)
                        confidence_score = max(0.0, min(1.0, raw_conf))
                    except (ValueError, TypeError):
                        confidence_score = 1.0

                    entity = str(item.get("canonical_entity") or "").strip()
                    statement = str(item.get("claim_statement") or "").strip()
                    quote = str(item.get("verbatim_evidence_quote") or "").strip()

                    if not entity or not statement:
                        logger.warning("Skipping incomplete claim lacking entity or statement: %s", item)
                        continue

                    claim = VerifiedEpistemicClaim.create(
                        tower_code=tower_code,
                        canonical_entity=entity,
                        claim_statement=statement,
                        status=resolved_status,
                        verbatim_evidence_quote=quote,
                        confidence_score=confidence_score,
                    )
                    verified_claims.append(claim)
                except Exception as item_err:
                    logger.warning("Skipping individual malformed claim item: %s (%s)", item, item_err)

            return ExtractionLedger(tenant_id=tenant_id, claims=verified_claims)

        except Exception as ex:
            logger.error("Failed structured evidence extraction for tenant '%s': %s", tenant_id, ex)
            return ExtractionLedger(tenant_id=tenant_id, claims=[])
