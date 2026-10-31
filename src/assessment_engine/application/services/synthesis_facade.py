"""Polymorphic Synthesis Facade and Anti-Corruption Layer (ACL) (RFC-009 / PR-3).

Enables shadow-mode execution, zero-downtime Strangler Fig cutover, and seamless
transformation between formal CEGAR Verified deliverables and legacy consumers.
"""

from __future__ import annotations

import asyncio
from enum import Enum
import logging
import os
from typing import Any, Callable

from assessment_engine.application.services.cegar_synthesis_engine import (
    CegarSynthesisEngine,
)
from assessment_engine.domain.synthesis.oracle import SynthesisContext
from assessment_engine.domain.synthesis.schemas import (
    VerifiedEnterpriseDeliverable,
)

logger = logging.getLogger(__name__)


class SynthesisMode(str, Enum):
    """Runtime strategy selector for deliverable synthesis."""

    LEGACY = "LEGACY"
    SHADOW = "SHADOW"
    CEGAR = "CEGAR"


class SynthesisAntiCorruptionLayer:
    """Translates formal VerifiedEnterpriseDeliverable into legacy consumers' payload format."""

    @classmethod
    def map_verified_to_legacy_dict(
        cls, deliverable: VerifiedEnterpriseDeliverable
    ) -> dict[str, Any]:
        """Transform certified deliverable into backward-compatible dictionary payload."""
        selected_option = next(
            (opt for opt in deliverable.pareto_frontier if opt.option_id == deliverable.selected_equilibrium_option_id),
            deliverable.pareto_frontier[0],
        )

        fin = selected_option.financials

        legacy_roadmap = [
            {
                "phase_index": p.phase_index,
                "title": p.phase_title,
                "duration_weeks": p.duration_weeks,
                "allocated_budget": str(p.allocated_budget),
                "deliverables": list(p.deliverable_artifacts),
                "citations": list(p.evidence_citations),
            }
            for p in deliverable.execution_roadmap
        ]

        legacy_frontier = [
            {
                "option_id": opt.option_id,
                "primary_axis": opt.primary_axis.value,
                "designation": opt.strategy_designation,
                "rationale": opt.architectural_rationale,
                "trade_off": opt.sacrificed_dimension_analysis,
                "tco": str(opt.financials.total_cost_of_ownership),
                "capex": str(opt.financials.capex_allocation),
                "opex": str(opt.financials.opex_allocation),
                "risk_p50": str(opt.financials.risk_exposure_p50),
                "utility_weights": {k.value: v for k, v in opt.utility_weights.items()},
                "evidence_ids": list(opt.supporting_evidence_ids),
            }
            for opt in deliverable.pareto_frontier
        ]

        return {
            "locale": deliverable.bcp47_locale,
            "industry_isic": deliverable.industry_isic_code,
            "executive_thesis": deliverable.executive_thesis,
            "executive_summary": deliverable.executive_thesis,
            "equilibrium_justification": deliverable.equilibrium_justification,
            "selected_option_id": deliverable.selected_equilibrium_option_id,
            "selected_strategy": selected_option.strategy_designation,
            "pareto_frontier": legacy_frontier,
            "execution_roadmap": legacy_roadmap,
            "financials": {
                "currency": fin.currency_iso_4217,
                "tco": str(fin.total_cost_of_ownership),
                "capex": str(fin.capex_allocation),
                "opex": str(fin.opex_allocation),
                "risk_p10": str(fin.risk_exposure_p10),
                "risk_p50": str(fin.risk_exposure_p50),
                "risk_p90": str(fin.risk_exposure_p90),
            },
            "provenance": {
                "engine": "CEGAR_VERIFIED_V1",
                "verified": True,
            },
        }


class PolymorphicSynthesisFacade:
    """Polymorphic entrypoint supporting Legacy, Shadow, and Active CEGAR synthesis."""

    def __init__(
        self,
        cegar_engine: CegarSynthesisEngine,
        legacy_synthesizer: Callable[..., Any] | None = None,
        default_mode: SynthesisMode = SynthesisMode.LEGACY,
    ) -> None:
        """Initialize facade with CEGAR engine, optional legacy callable, and fallback mode."""
        self._cegar_engine = cegar_engine
        self._legacy_synthesizer = legacy_synthesizer
        self._default_mode = default_mode
        self._background_tasks: set[asyncio.Task[Any]] = set()

    def resolve_active_mode(self) -> SynthesisMode:
        """Resolve mode from environment variable SYNTHESIS_ENGINE_MODE or default."""
        env_mode_str = os.environ.get("SYNTHESIS_ENGINE_MODE", "").strip().upper()
        if env_mode_str in SynthesisMode.__members__:
            return SynthesisMode[env_mode_str]
        return self._default_mode

    async def synthesize(
        self,
        context: SynthesisContext,
        evidence_payload: dict[str, Any],
        **legacy_kwargs: Any,
    ) -> dict[str, Any]:
        """Execute synthesis routing according to active feature flag mode.

        Modes:
            LEGACY: Executes legacy synthesis callable.
            SHADOW: Executes legacy synthesis, runs CEGAR asynchronously in background, logs telemetry, returns legacy.
            CEGAR:  Executes CEGAR pipeline, converts via ACL mapper, returns mapped payload.
        """
        mode = self.resolve_active_mode()
        logger.info("Executing PolymorphicSynthesisFacade in mode=%s", mode.value)

        if mode == SynthesisMode.CEGAR:
            verified = await self._cegar_engine.synthesize(context, evidence_payload)
            return SynthesisAntiCorruptionLayer.map_verified_to_legacy_dict(verified)

        # Legacy Execution (for LEGACY and SHADOW modes)
        legacy_result = await self._execute_legacy(context, evidence_payload, **legacy_kwargs)

        if mode == SynthesisMode.SHADOW:
            try:
                task = asyncio.create_task(self._execute_shadow_pass(context, evidence_payload))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except RuntimeError:
                # If running outside an active event loop, await directly
                await self._execute_shadow_pass(context, evidence_payload)

        return legacy_result

    async def _execute_legacy(
        self,
        context: SynthesisContext,
        evidence_payload: dict[str, Any],
        **legacy_kwargs: Any,
    ) -> dict[str, Any]:
        """Execute legacy synthesis pipeline safely."""
        if self._legacy_synthesizer:
            res = await self._legacy_synthesizer(context=context, payload=evidence_payload, **legacy_kwargs)
            return res if isinstance(res, dict) else {"legacy_output": res}
        return {
            "status": "LEGACY_SYNTHESIS_FALLBACK",
            "executive_summary": "Legacy heuristic synthesis generated.",
            "provenance": {"engine": "LEGACY_FALLBACK", "verified": False},
        }

    async def _execute_shadow_pass(
        self,
        context: SynthesisContext,
        evidence_payload: dict[str, Any],
    ) -> None:
        """Execute CEGAR engine in non-blocking shadow mode for telemetry and comparative eval."""
        try:
            logger.info("Starting background shadow CEGAR synthesis pass...")
            shadow_deliverable = await self._cegar_engine.synthesize(context, evidence_payload)
            logger.info(
                "Shadow CEGAR synthesis succeeded: Option=%s TCO=%s",
                shadow_deliverable.selected_equilibrium_option_id,
                shadow_deliverable.pareto_frontier[0].financials.total_cost_of_ownership,
            )
        except Exception as shadow_err:
            logger.warning("Shadow CEGAR synthesis execution error: %s", shadow_err)
