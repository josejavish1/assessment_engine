"""
Darwinian Post-Mortem Distiller & Cognitive Causal Closer — GEMA 28 (SOTA 2026).
Extracts causal root causes from losing A/B variants and closes the evolutionary loop.
Incorporates:
- Strict Hierarchy of Causality: Technical Breakage > Hotspot Frustration > Form Friction > Value Weakness.
- Prescriptive Axiom Synthesis for future generative compilation.
- Structural Contrastive Exemplar extraction (failed snippet vs verified diff).
- Empirical Sectorial Prior computation (Informed Beta conjugate parameters).
- Idempotent persistence to ReflexionLedger in SQLite WAL.
Zero external dependencies ($0.00 cost).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from assessment_engine.infrastructure.evolution.reflexion_ledger import ReflexionLedger, reflexion_ledger
from assessment_engine.infrastructure.primitives.friction_sensor import VariantFrictionSummary

logger = logging.getLogger("assessment_engine.infrastructure.evolution.darwinian_distiller")


@dataclass(frozen=True)
class CausalAttribution:
    """Provide a structured causal diagnosis of variant loss."""
    category: str                   # TECHNICAL_BREAKAGE, HOTSPOT_FRUSTRATION, FORM_FRICTION, VALUE_PROP_WEAKNESS
    root_cause_selector: str
    culprit_metric: str
    prescriptive_axiom: str
    confidence_score: float         # 0.0 a 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)


@dataclass
class DarwinianPostMortemReport:
    """Informe post-mortem consolidado del torneo darwinista."""
    experiment_id: str
    losing_variant: str
    winning_variant: str
    attribution: CausalAttribution
    contrastive_pair: dict[str, str]        # {"failed_snippet": ..., "verified_diff": ...}
    sectorial_prior: tuple[float, float]    # (alpha, beta)
    persisted_to_ledger: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the instance."""
        d = asdict(self)
        d["attribution"] = self.attribution.to_dict()
        return d


def _attribute_technical_breakage(loser: VariantFrictionSummary, sector: str) -> CausalAttribution | None:
    """Priority 1: Technical failure or runtime exceptions."""
    if loser.total_error_clicks < 1:
        return None
    return CausalAttribution(
        category="TECHNICAL_BREAKAGE",
        root_cause_selector="window.onerror",
        culprit_metric=f"{loser.total_error_clicks} error clicks detectados",
        prescriptive_axiom=(
            f"[{sector}] Prohibido desplegar componentes interactivos sin control estricto de excepciones "
            f"en promesas y llamadas de red; provocó la derrota de la variante con {loser.total_error_clicks} errores."
        ),
        confidence_score=0.99,
    )


def _attribute_rage_hotspot(loser: VariantFrictionSummary, sector: str) -> CausalAttribution | None:
    """Priority 2: Concentrated foveal frustration (rage clicks and dead clicks)."""
    if loser.total_rage_clicks < 1 and loser.total_dead_clicks < 1:
        return None
    culprit_desc = f"{loser.total_rage_clicks} rage clicks y {loser.total_dead_clicks} dead clicks"
    return CausalAttribution(
        category="HOTSPOT_FRUSTRATION",
        root_cause_selector="#interactive-action",
        culprit_metric=culprit_desc,
        prescriptive_axiom=(
            f"[{sector}] En elementos interactivos de alta intención, prohibido usar estados visuales "
            f"sin feedback háptico o de carga inmediata (provocó {culprit_desc})."
        ),
        confidence_score=0.92,
    )


def _attribute_form_friction(loser: VariantFrictionSummary, sector: str) -> CausalAttribution | None:
    """Priority 3: Input friction or form abandonment."""
    if loser.total_form_abandonments < 1 and loser.avg_hesitation_ms < 3000.0:
        return None
    return CausalAttribution(
        category="FORM_FRICTION",
        root_cause_selector="input[form]",
        culprit_metric=f"{loser.total_form_abandonments} abandonos, vacilación media de {loser.avg_hesitation_ms}ms",
        prescriptive_axiom=(
            f"[{sector}] En flujos transaccionales y de reserva, prohibido requerir campos complejos sin "
            f"indicadores claros o autocompletado; generó {loser.total_form_abandonments} abandonos de formulario."
        ),
        confidence_score=0.88,
    )


def _attribute_value_weakness(
    loser: VariantFrictionSummary, winner: VariantFrictionSummary, sector: str
) -> CausalAttribution:
    """Priority 4: Ergonomic or value proposition weakness."""
    uplift = round(winner.conversion_rate_pct - loser.conversion_rate_pct, 2)
    return CausalAttribution(
        category="VALUE_PROP_WEAKNESS",
        root_cause_selector="main",
        culprit_metric=f"Déficit relativo de conversión de {uplift}% frente a variante ganadora",
        prescriptive_axiom=(
            f"[{sector}] Priorizar propuestas de valor directas con prueba social cuantitativa y llamada a "
            f"la acción por encima del pliegue visual; superó en +{uplift}% de conversión al enfoque perdedor."
        ),
        confidence_score=0.75,
    )


class DarwinianDistiller:
    """
    Distill root causes and close the cognitive loop in ReflexionLedger.
    """

    def attribute_causality(
        self, loser: VariantFrictionSummary, winner: VariantFrictionSummary, sector: str = "SaaS"
    ) -> CausalAttribution:
        """Apply the strict deterministic causality hierarchy."""
        attr = _attribute_technical_breakage(loser, sector)
        if attr:
            return attr

        attr = _attribute_rage_hotspot(loser, sector)
        if attr:
            return attr

        attr = _attribute_form_friction(loser, sector)
        if attr:
            return attr

        return _attribute_value_weakness(loser, winner, sector)

    def extract_contrastive_pair(
        self, loser_code: str, winner_code: str, root_selector: str
    ) -> dict[str, str]:
        """Extract the structural contrastive pair between losing and winning code."""
        if loser_code and winner_code:
            failed_snippet = loser_code[:600]
            verified_diff = (
                f"// DIFF GANADOR (SUPERÓ LA FRICCIÓN EN '{root_selector}'):\n"
                f"{winner_code[:600]}"
            )
        else:
            failed_snippet = f"// Patrón defectuoso identificado en selector: {root_selector}"
            verified_diff = f"// Solución ganadora validada sin fricción para selector: {root_selector}"

        return {
            "failed_snippet": failed_snippet,
            "verified_diff": verified_diff,
        }

    def compute_sectorial_prior(
        self, loser: VariantFrictionSummary, winner: VariantFrictionSummary
    ) -> tuple[float, float]:
        """Calculate informed conjugate Beta distribution parameters for the sector."""
        total_conv = loser.total_conversions + winner.total_conversions
        total_sess = loser.total_sessions + winner.total_sessions

        if total_sess <= 0:
            return (1.0, 1.0)

        # Scale to a baseline sample size (N=50) to prevent overweighting future data.
        raw_rate = max(0.01, min(0.99, total_conv / float(total_sess)))
        effective_n = 50.0
        alpha = round(max(1.0, raw_rate * effective_n), 2)
        beta = round(max(1.0, (1.0 - raw_rate) * effective_n), 2)
        return (alpha, beta)

    def analyze_defeat(
        self,
        experiment_id: str,
        loser: VariantFrictionSummary,
        winner: VariantFrictionSummary,
        loser_code: str = "",
        winner_code: str = "",
        sector: str = "SaaS",
    ) -> DarwinianPostMortemReport:
        """Perform a complete causal autopsy of the loss and synthesize the post-mortem report."""
        attribution = self.attribute_causality(loser, winner, sector)
        contrastive = self.extract_contrastive_pair(loser_code, winner_code, attribution.root_cause_selector)
        prior = self.compute_sectorial_prior(loser, winner)

        return DarwinianPostMortemReport(
            experiment_id=experiment_id,
            losing_variant=loser.variant_id,
            winning_variant=winner.variant_id,
            attribution=attribution,
            contrastive_pair=contrastive,
            sectorial_prior=prior,
            persisted_to_ledger=False,
            metadata={
                "sector": sector,
                "loser_conversion_pct": loser.conversion_rate_pct,
                "winner_conversion_pct": winner.conversion_rate_pct,
                "friction_delta": round(winner.friction_index - loser.friction_index, 1),
            },
        )

    def persist_to_reflexion_ledger(
        self, report: DarwinianPostMortemReport, ledger: ReflexionLedger | None = None
    ) -> bool:
        """
        Record the causal anti-pattern and contrastive pair into ReflexionLedger idempotently.
        """
        target_ledger = ledger or reflexion_ledger
        sig = f"EXP_LOSS_{report.experiment_id}_{report.losing_variant}"

        target_ledger.record_failure(
            category=report.attribution.category,
            error_signature=sig,
            target_file="LandingView.tsx",
            corrective_axiom=report.attribution.prescriptive_axiom,
            culprit_pattern=report.attribution.root_cause_selector,
        )

        target_ledger.record_contrastive_exemplar(
            category=report.attribution.category,
            task_hint=f"Torneo {report.experiment_id} ({report.metadata.get('sector', 'SaaS')})",
            failed_snippet=report.contrastive_pair["failed_snippet"],
            verified_diff=report.contrastive_pair["verified_diff"],
        )

        report.persisted_to_ledger = True
        logger.info(
            f"[DarwinianDistiller] Autopsia {report.experiment_id} grabada en ReflexionLedger: "
            f"categoría={report.attribution.category}, prior={report.sectorial_prior}"
        )
        return True


# Canonical singleton instance (WASI / MCP).
darwinian_distiller = DarwinianDistiller()
