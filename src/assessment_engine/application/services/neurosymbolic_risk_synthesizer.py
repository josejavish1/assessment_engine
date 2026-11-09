"""Neurosymbolic Risk Synthesizer with Circuit Breakers and Adaptive Complexity Ceilings.

Part of Stage 4.2 & 4.3 of the Neurosymbolic Decoupling Protocol.
Combines deterministic Python actuarial invariants with LLM semantic reasoning.
Guarantees:
- Zero arithmetic hallucination (math is an immutable physical constraint).
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
            self._model_name = get_model(ModelTier.REASONING)
        return self._client, self._model_name

    def synthesize_risk(self, ctx: RiskSynthesisContext) -> SynthesizedRiskItem:
        """Synthesizes risk card with live LLM reasoning, protected by an automatic circuit breaker."""
        ctx_hash = ctx.compute_context_hash()

        try:
            client, model = self._get_client_and_model()
            prompt = self._build_adaptive_prompt(ctx)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            raw = (response.text or "").strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]

            parsed = json.loads(raw.strip())
            return SynthesizedRiskItem(
                risk_id=f"RSK-{ctx.kpi_id}",
                causal_risk_title=str(parsed.get("causal_risk_title", "")).strip(),
                technical_failure_mechanism=str(parsed.get("technical_failure_mechanism", "")).strip(),
                actuarial_justification=str(parsed.get("actuarial_justification", "")).strip(),
                remediation_architecture=str(parsed.get("remediation_architecture", "")).strip(),
                context_hash=ctx_hash,
            )
        except Exception as exc:
            logger.warning(
                "CIRCUIT_BREAKER_TRIGGERED: Neurosymbolic LLM synthesis failed for %s (%s). Degrading to deterministic fallback.",
                ctx.kpi_id,
                exc,
            )
            return self.fallback_provider.synthesize_risk(ctx)

    def _build_adaptive_prompt(self, ctx: RiskSynthesisContext) -> str:
        """Constructs an epistemic prompt enforcing the Adaptive Complexity Ceiling."""
        # 1. Complexity Ceiling Matrix based on maturity score
        is_low_maturity = ctx.assessed_score < 2.60
        is_cloud_native = ctx.assessed_score >= 3.80

        if is_low_maturity:
            complexity_rules = """
- ADAPTIVE COMPLEXITY CEILING (LOW MATURITY / TRADITIONAL SME):
  * Strictly FORBIDDEN vocabulary: Do NOT mention Kubernetes, microservices, Zero Trust, service mesh, SIEM, SOAR, or multi-region active-active.
  * Focus strictly on realistic baseline risks: single physical server failure, unmonitored disk exhaustion, manual backup neglect, lack of vendor support contracts, or unmaintained local network switches.
"""
        elif is_cloud_native:
            complexity_rules = """
- ADAPTIVE COMPLEXITY CEILING (HIGH MATURITY / CLOUD-NATIVE):
  * Analyze sophisticated distributed systems failure modes: cross-region state replication lag, split-brain consensus partitions, ephemeral credential expiration, telemetry blind spots, or automated failover race conditions.
"""
        else:
            complexity_rules = """
- ADAPTIVE COMPLEXITY CEILING (MID-TIER / STANDARD ENTERPRISE):
  * Balance infrastructure resilience and operational process: hypervisor host contention, storage array volume saturation, backup catalog verification lags, and change management gaps.
"""

        # 2. Strict Grounding Constraints
        tech_constraint = (
            f"Verified Technology Stack: {', '.join(ctx.verified_tech_stack)}"
            if ctx.verified_tech_stack
            else f"No specific vendor declared. Restrict analysis strictly to generic {ctx.pillar_name} concepts."
        )

        return f"""You are a Principal Enterprise Risk Assessor and Actuary conducting a formal Open FAIR assessment for {ctx.client_name}.
Synthesize an organic, stack-grounded, and mathematically verified Risk Card in target language: {ctx.doc_lang}.

IMMUTABLE ACTUARIAL CONSTANTS (CALCULATED DETERMINISTICALLY BY PYTHON):
- Currency: {ctx.currency_symbol}
- Baseline Hourly Downtime Cost: {ctx.currency_symbol}{ctx.hourly_rate:,.2f}/hr
- Expected Outage Window: {ctx.downtime_minutes} minutes
- Direct Operational Stoppage Loss: {ctx.currency_symbol}{ctx.stoppage_loss:,.2f}
- Emergency Engineering & Recovery Burn: {ctx.currency_symbol}{ctx.recovery_burn:,.2f}
- Contractual SLA / Compliance Notification Penalty: {ctx.currency_symbol}{ctx.penalty_loss:,.2f}
- Total Single Loss Expectancy (SLE): {ctx.currency_symbol}{ctx.total_sle:,.2f}
- Annualized Loss Expectancy (ALE): {ctx.currency_symbol}{ctx.calibrated_ale:,.2f}/year

CLIENT METADATA & CONTEXT:
- Client Name: {ctx.client_name}
- Industry Vertical: {ctx.industry} ({ctx.sub_industry})
- Evaluated Tower: {ctx.tower_name} ({ctx.tower_code})
- Evaluated Pillar: {ctx.pillar_name} ({ctx.pillar_id})
- Assessed Maturity Score: {ctx.assessed_score:.2f} out of 5.00
- {tech_constraint}

{complexity_rules}

RULES:
1. Zero Arithmetic Modification: You MUST cite the exact numbers ({ctx.currency_symbol}{ctx.calibrated_ale:,.0f} ALE, {ctx.currency_symbol}{ctx.total_sle:,.0f} SLE) in the actuarial narrative. Do not round or alter them.
2. Causal Threat Title: Follow format: [Specific Component Failure] leading to [Specific Operational Consequence]. NEVER use generic phrases like "Operational Risk Scenario: ...".
3. Language: Write in 100% fluent {ctx.doc_lang}.

MANDATORY RAW JSON OUTPUT:
{{
  "causal_risk_title": "<Specific causal threat title>",
  "technical_failure_mechanism": "<Concise 2-3 sentence technical sequence of failure>",
  "actuarial_justification": "<Cohesive narrative decomposing the {ctx.currency_symbol}{ctx.total_sle:,.0f} SLE and {ctx.currency_symbol}{ctx.calibrated_ale:,.0f}/year ALE>",
  "remediation_architecture": "<Concrete engineering solution referencing relevant international standards>"
}}
"""
