"""Infrastructure adapter implementing SynthesisGeneratorPort via Frontier LLMs (RFC-009)."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable
from google import genai
from google.genai import types

from assessment_engine.application.services.cegar_synthesis_engine import (
    SynthesisGeneratorPort,
)
from assessment_engine.domain.synthesis.oracle import SynthesisContext
from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    CounterexampleVector,
)
from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger(__name__)


class CegarLLMAdapter(SynthesisGeneratorPort):
    """Frontier LLM Adapter for candidate Pareto synthesis and surgical delta repair."""

    def __init__(
        self,
        client: genai.Client | None = None,
        model_tier: ModelTier = ModelTier.REASONING,
        custom_caller: Callable[..., Any] | None = None,
    ) -> None:
        """Initialize adapter with GenAI client, model tier, or optional mock caller."""
        self._client = client or genai.Client()
        self._model_tier = model_tier
        self._custom_caller = custom_caller

    async def generate_candidate(
        self, context: SynthesisContext, evidence_payload: dict[str, Any]
    ) -> CandidateEnterpriseDeliverable:
        """Synthesize initial unverified candidate deliverable via structured output."""
        if self._custom_caller:
            raw_result = await self._custom_caller(
                prompt="GENERATE",
                context=context,
                payload=evidence_payload,
            )
            return self._parse_candidate_response(raw_result)

        system_instruction = (
            f"You are a Principal Solutions Architect synthesizing an executive-grade Pareto Frontier Deliverable.\n"
            f"TARGET LANGUAGE / LOCALE: {context.target_locale}\n"
            f"TARGET CURRENCY: {context.target_currency}\n"
            f"INDUSTRY ISIC CODE: {context.target_isic_code}\n\n"
            f"MANDATES:\n"
            f"1. Generate exactly 3 orthogonal options in 'pareto_frontier' (CAPITAL_EFFICIENCY, OPERATIONAL_RESILIENCE, EXECUTION_VELOCITY).\n"
            f"2. Ensure exact accounting identities: total_cost_of_ownership == capex_allocation + opex_allocation.\n"
            f"3. Ensure FAIR risk monotonicity: risk_exposure_p10 <= risk_exposure_p50 <= risk_exposure_p90.\n"
            f"4. Ensure sum of allocated_budget across execution_roadmap equals the selected option's total_cost_of_ownership.\n"
            f"5. All evidentiary citations MUST strictly match IDs present in input evidence.\n"
            f"6. Emit output conforming strictly to the requested JSON schema."
        )

        user_content = json.dumps(
            {
                "context": {
                    "locale": context.target_locale,
                    "currency": context.target_currency,
                    "isic_code": context.target_isic_code,
                    "valid_evidence_ids": list(context.valid_evidence_ids),
                },
                "evidence_payload": evidence_payload,
            },
            ensure_ascii=False,
            indent=2,
        )

        response = await self._client.aio.models.generate_content(
            model=get_model(self._model_tier),
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CandidateEnterpriseDeliverable,
            ),
        )
        return self._parse_candidate_response(response.text)

    async def optimize_repair(
        self,
        candidate: CandidateEnterpriseDeliverable,
        counterexamples: CounterexampleVector,
        context: SynthesisContext,
    ) -> CandidateEnterpriseDeliverable:
        """Perform surgical 1-shot AST/JSON mutation to rectify formal counterexamples."""
        if self._custom_caller:
            raw_result = await self._custom_caller(
                prompt="REPAIR",
                candidate=candidate,
                counterexamples=counterexamples,
                context=context,
            )
            return self._parse_candidate_response(raw_result)

        violations_summary = [
            {
                "rule_id": v.rule_id,
                "json_path": v.json_path,
                "expected": v.expected_invariant,
                "actual": v.actual_value,
                "directive": v.remediation_directive,
            }
            for v in counterexamples.violations
        ]

        system_instruction = (
            f"You are a Formal Repair Optimizer in a CEGAR (Counterexample-Guided Abstraction Refinement) pipeline.\n"
            f"TARGET LANGUAGE / LOCALE: {context.target_locale}\n"
            f"TARGET CURRENCY: {context.target_currency}\n"
            f"INDUSTRY ISIC CODE: {context.target_isic_code}\n\n"
            f"SURGICAL REPAIR MANDATE:\n"
            f"Your previous synthesis attempt contained formal invariant violations.\n"
            f"Perform targeted delta mutations at the specified 'json_path' nodes to satisfy every remediation directive.\n"
            f"Hold all valid nodes invariant while resolving all mathematical, accounting, and citation defects."
        )

        repair_payload = json.dumps(
            {
                "candidate_attempt_1": candidate.model_dump(mode="json"),
                "formal_violations": violations_summary,
            },
            ensure_ascii=False,
            indent=2,
        )

        response = await self._client.aio.models.generate_content(
            model=get_model(self._model_tier),
            contents=repair_payload,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CandidateEnterpriseDeliverable,
            ),
        )
        return self._parse_candidate_response(response.text)

    @staticmethod
    def _parse_candidate_response(raw: Any) -> CandidateEnterpriseDeliverable:
        """Deserialize raw response or dict into validated CandidateEnterpriseDeliverable."""
        if isinstance(raw, CandidateEnterpriseDeliverable):
            return raw
        if isinstance(raw, dict):
            return CandidateEnterpriseDeliverable.model_validate(raw)
        if isinstance(raw, str):
            clean_str = raw.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.startswith("```"):
                clean_str = clean_str[3:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            return CandidateEnterpriseDeliverable.model_validate_json(clean_str.strip())
        raise ValueError(f"Unsupported candidate response type: {type(raw)}")
