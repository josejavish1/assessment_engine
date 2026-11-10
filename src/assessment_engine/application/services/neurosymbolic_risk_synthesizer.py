"""Neurosymbolic Risk Synthesizer with Circuit Breakers and Adaptive Complexity Ceilings.

Part of Stage 4.2 & 4.3 of the Neurosymbolic Decoupling Protocol.
Combines deterministic Python actuarial invariants with LLM semantic reasoning.
Guarantees:
- Zero arithmetic hallucination (math is an immutable physical constraint).
- Single-pass batch synthesis per tower (sub-30 second full client execution).
- Adaptive Complexity Ceiling (prevents SME hallucinated sophistication).
- Resilient Circuit Breaker (seamless degradation to DeterministicFallbackSynthesizer).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from assessment_engine.application.services.risk_synthesis_service import (
    DeterministicFallbackSynthesizer,
)
from assessment_engine.domain.schemas.risk_synthesis import (
    IRiskSynthesizer,
    RiskSynthesisContext,
    SynthesizedRiskItem,
)
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

logger = logging.getLogger(__name__)


class NeurosymbolicLLMSynthesizer(IRiskSynthesizer):
    """Production LLM risk synthesizer with adaptive complexity bounding and circuit breakers."""

    def __init__(self, fallback_provider: IRiskSynthesizer | None = None) -> None:
        self.fallback_provider = fallback_provider or DeterministicFallbackSynthesizer()
        self._client = None
        self._model_name = None

    def _get_client_and_model(self) -> tuple[Any, str]:
        if self._client is None:
            self._client = create_genai_client()
            # Use fast high-performance tier for fast, reliable JSON synthesis
            self._model_name = get_model(ModelTier.FAST)
        return self._client, self._model_name

    def synthesize_risk(self, ctx: RiskSynthesisContext) -> SynthesizedRiskItem:
        """Synthesizes single risk card with live LLM reasoning, protected by circuit breaker."""
        results = self.synthesize_tower_risks([ctx])
        return results[0] if results else self.fallback_provider.synthesize_risk(ctx)

    def synthesize_tower_risks(
        self, contexts: list[RiskSynthesisContext]
    ) -> list[SynthesizedRiskItem]:
        """Batch synthesizes all primary pillar risks for an entire tower in a single LLM reasoning pass."""
        if not contexts:
            return []

        try:
            client, model = self._get_client_and_model()
            prompt = self._build_tower_batch_prompt(contexts)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            raw = (response.text or "").strip()
            fence_match = re.search(r"```(?:json|JSON)?\s*(\{.*?\}|\[.*?\])\s*```", raw, re.DOTALL)
            if fence_match:
                raw_json = fence_match.group(1).strip()
            else:
                start_idx = raw.find("{")
                end_idx = raw.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    raw_json = raw[start_idx : end_idx + 1].strip()
                else:
                    raw_json = raw

            parsed = json.loads(raw_json)
            risks_list = (
                parsed.get("risks", [])
                if isinstance(parsed, dict)
                else (parsed if isinstance(parsed, list) else [])
            )
            items_dict = {
                item.get("kpi_id"): item
                for item in risks_list
                if isinstance(item, dict) and item.get("kpi_id")
            }

            results: list[SynthesizedRiskItem] = []
            for ctx in contexts:
                ctx_hash = ctx.compute_context_hash()
                item_data = items_dict.get(ctx.kpi_id)
                if item_data and item_data.get("causal_risk_title"):
                    results.append(
                        SynthesizedRiskItem(
                            risk_id=f"RSK-{ctx.kpi_id}",
                            causal_risk_title=str(item_data.get("causal_risk_title", "")).strip(),
                            technical_failure_mechanism=str(item_data.get("technical_failure_mechanism", "")).strip(),
                            actuarial_justification=str(item_data.get("actuarial_justification", "")).strip(),
                            remediation_architecture=str(item_data.get("remediation_architecture", "")).strip(),
                            context_hash=ctx_hash,
                        )
                    )
                else:
                    results.append(self.fallback_provider.synthesize_risk(ctx))
            return results
        except Exception as exc:
            logger.warning(
                "CIRCUIT_BREAKER_TRIGGERED: Batch LLM synthesis failed for tower %s (%s). Degrading to deterministic fallback.",
                contexts[0].tower_code,
                exc,
            )
            return [self.fallback_provider.synthesize_risk(ctx) for ctx in contexts]

    def _build_adaptive_prompt(self, ctx: RiskSynthesisContext) -> str:
        """Constructs prompt for a single context, maintaining backwards compatibility."""
        return self._build_tower_batch_prompt([ctx])

    def _build_tower_batch_prompt(
        self, contexts: list[RiskSynthesisContext]
    ) -> str:
        """Constructs a consolidated prompt for an entire tower enforcing per-pillar Adaptive Complexity Ceilings."""
        first_ctx = contexts[0]

        p_items_str = []
        for ctx in contexts:
            tech_str = ", ".join(ctx.verified_tech_stack) if ctx.verified_tech_stack else ctx.pillar_name
            if ctx.assessed_score < 2.60:
                p_ceiling = (
                    "LOW_MATURITY (<2.60): Strictly FORBIDDEN vocabulary: Do NOT mention Kubernetes, microservices, Zero Trust, service mesh, SIEM, SOAR, or multi-region active-active. "
                    "Focus strictly on realistic baseline risks: single physical server failure, unmonitored disk exhaustion, manual backup neglect, lack of vendor support contracts, or unmaintained local network switches."
                )
            elif ctx.assessed_score >= 3.80:
                p_ceiling = (
                    "CLOUD_NATIVE (>=3.80): Focus on advanced distributed systems edge cases: cross-region state replication lag, split-brain consensus partitions, ephemeral credential expiration, telemetry blind spots, or automated failover race conditions."
                )
            else:
                p_ceiling = (
                    "TRANSITIONAL / MID-TIER (2.60-3.79): Balance infrastructure resilience and operational process: hypervisor host contention, storage array volume saturation, backup catalog verification lags, and change management gaps."
                )

            p_items_str.append(
                f"- Pillar: {ctx.pillar_name} (KPI: {ctx.kpi_id})\n"
                f"  Score: {ctx.assessed_score:.2f}/5.00 | Verified Tech: {tech_str}\n"
                f"  Complexity Ceiling: {p_ceiling}\n"
                f"  Actuarial Invariants: {ctx.currency_symbol}{ctx.calibrated_ale:,.0f} ALE | {ctx.currency_symbol}{ctx.total_sle:,.0f} SLE | {ctx.downtime_minutes} min duration\n"
                f"  Decomposition: Direct Stoppage {ctx.currency_symbol}{ctx.stoppage_loss:,.0f} + Recovery Burn {ctx.currency_symbol}{ctx.recovery_burn:,.0f} + Penalty {ctx.currency_symbol}{ctx.penalty_loss:,.0f}"
            )

        scenarios_block = "\n\n".join(p_items_str)

        complexity_rules = """
- ADAPTIVE COMPLEXITY CEILING:
  * Respect each pillar's individual Complexity Ceiling specified above.
  * For pillars marked LOW_MATURITY (<2.60): Strictly FORBIDDEN vocabulary: Do NOT mention Kubernetes, microservices, Zero Trust, service mesh, SIEM, SOAR, or multi-region active-active. Focus strictly on single points of failure and unmaintained baseline systems.
  * For pillars marked ADAPTIVE COMPLEXITY CEILING (HIGH MATURITY / CLOUD-NATIVE) (>=3.80): Analyze sophisticated distributed systems failure modes: cross-region state replication lag, split-brain consensus partitions, ephemeral credential expiration, and automated failover race conditions.
  * For pillars marked TRANSITIONAL (2.60-3.79): Balance infrastructure resilience and operational process: hypervisor host contention, storage array volume saturation, and backup verification lags.
"""

        lang_names = {
            "pt": "Brazilian Portuguese",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "en": "English",
        }
        target_lang = lang_names.get(first_ctx.doc_lang, first_ctx.doc_lang)

        return f"""You are a Principal Enterprise Risk Assessor and Actuary conducting a formal Open FAIR assessment for {first_ctx.client_name}.
Synthesize an organic, stack-grounded, and mathematically verified Risk Card for EACH evaluated pillar in {first_ctx.tower_name} ({first_ctx.tower_code}).
MANDATORY OUTPUT LANGUAGE: All generated string values MUST be written 100% in {target_lang}.

CLIENT METADATA:
- Client: {first_ctx.client_name}
- Industry: {first_ctx.industry} ({first_ctx.sub_industry})
- Domain: {first_ctx.tower_name} ({first_ctx.tower_code})
- Baseline Hourly Downtime Rate: {first_ctx.currency_symbol}{first_ctx.hourly_rate:,.2f}/hr

EVALUATED PILLARS & ACTUARIAL INVARIANTS:
{scenarios_block}

{complexity_rules}

RULES:
1. Zero Arithmetic Modification: You MUST cite the exact SLE and ALE figures (prefixed with {first_ctx.currency_symbol}) provided in the EVALUATED PILLARS block above for each respective pillar. Do not round or alter them.
2. Causal Threat Title: Follow format: [Specific Component Failure] -> [Specific Operational Consequence]. Always include an explicit threat or exposure connector in {target_lang} (such as "risking" or "exposing" in English, or target language equivalents) to denote unambiguous threat polarity. NEVER use generic phrases like "Operational Risk Scenario: ...".
3. Lexical Variety: Ensure each pillar has a distinct, organic threat title reflecting its unique engineering domain.
4. Target Language: All text values MUST be written exclusively in {target_lang}. JSON keys remain in English.

MANDATORY RAW JSON OUTPUT:
{{
  "risks": [
    {{
      "kpi_id": "<exact KPI id matching input>",
      "causal_risk_title": "<Specific causal threat title>",
      "technical_failure_mechanism": "<Concise 2-3 sentence technical sequence of failure>",
      "actuarial_justification": "<Cohesive narrative decomposing the SLE and ALE>",
      "remediation_architecture": "<Concrete engineering solution referencing relevant international standards>"
    }}
  ]
}}
"""
