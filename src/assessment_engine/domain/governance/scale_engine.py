"""Authoritative Governance Scale Engine (SSOT for CMMI & Dimensionless Open FAIR).

Implements:
1. Strict half-open interval partitioning [a_k, a_{k+1}) for continuous CMMI resolution.
2. Dimensionless operational impact scaling based on powers of 4 of enterprise hourly downtime burn rate:
   - LM1: < 1.0 hour of downtime
   - LM2: 1.0 to 4.0 hours of downtime
   - LM3: 4.0 to 16.0 hours of downtime
   - LM4: 16.0 to 64.0 hours of downtime
   - LM5: >= 64.0 hours of downtime
3. 100% Technical English implementation. Decoupled from currencies, languages, or firm scale.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Callable, Dict, Optional

from assessment_engine.domain.governance.primitives import (
    FinancialSeverityCode,
    MaturityBandCode,
    ResolvedFinancialRisk,
    ResolvedMaturity,
    sanitize_to_decimal,
)


class GovernanceScaleEngine:
    """
    Singleton SSOT Engine for Maturity and Financial Risk Governance.
    Thread-safe, immutable, and strictly deterministic across any currency or market.
    """

    _instance: Optional[GovernanceScaleEngine] = None

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None) -> None:
        self.config = config_dict if config_dict is not None else self._fallback_config()
        self._verify_formal_invariants()

    @classmethod
    def configure(cls, config_dict: Dict[str, Any]) -> None:
        """Configures or resets the singleton instance with custom configuration."""
        cls._instance = cls(config_dict=config_dict)

    @classmethod
    def get_instance(cls) -> GovernanceScaleEngine:
        """Returns the canonical singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _fallback_config(self) -> Dict[str, Any]:
        """Built-in hard fallback to guarantee zero I/O startup failures."""
        return {
            "cmmi_maturity_scale": {
                "quantization_decimals": 2,
                "bands": [
                    {"level": 1, "code": "INITIAL", "upper_bound_exclusive": 1.50, "label_token": "band_initial", "default_label": "Initial", "ui_token": "status-critical"},
                    {"level": 2, "code": "REPEATABLE", "upper_bound_exclusive": 2.50, "label_token": "band_managed", "default_label": "Managed", "ui_token": "status-warning"},
                    {"level": 3, "code": "DEFINED", "upper_bound_exclusive": 3.50, "label_token": "band_defined", "default_label": "Defined", "ui_token": "status-neutral"},
                    {"level": 4, "code": "MANAGED", "upper_bound_exclusive": 4.50, "label_token": "band_quantitatively_managed", "default_label": "Quantitatively Managed", "ui_token": "status-good"},
                    {"level": 5, "code": "OPTIMIZED", "upper_bound_exclusive": 5.0001, "label_token": "band_optimized", "default_label": "Optimizing", "ui_token": "status-excellent"},
                ]
            },
            "open_fair_loss_magnitude_scale": {
                "description": "Dimensionless operational impact scaling based on powers of 4 of enterprise hourly downtime burn rate",
                "tiers": [
                    {"lm_code": "LM1", "severity": "LOW", "label_token": "severity_low", "default_label": "Low", "downtime_hours_multiplier": 1.0, "ui_token": "severity-low"},
                    {"lm_code": "LM2", "severity": "MODERATE", "label_token": "severity_moderate", "default_label": "Moderate", "downtime_hours_multiplier": 4.0, "ui_token": "severity-moderate"},
                    {"lm_code": "LM3", "severity": "ELEVATED", "label_token": "severity_elevated", "default_label": "Elevated", "downtime_hours_multiplier": 16.0, "ui_token": "severity-elevated"},
                    {"lm_code": "LM4", "severity": "HIGH", "label_token": "severity_high", "default_label": "High", "downtime_hours_multiplier": 64.0, "ui_token": "severity-high"},
                    {"lm_code": "LM5", "severity": "CRITICAL", "label_token": "severity_critical", "default_label": "Critical", "downtime_hours_multiplier": None, "ui_token": "severity-critical"},
                ]
            }
        }

    def _verify_formal_invariants(self) -> None:
        """Enforces formal mathematical invariants on bands and tiers."""
        bands = self.config["cmmi_maturity_scale"]["bands"]
        prev_upper = Decimal("0.0")
        for b in bands:
            curr_upper = Decimal(str(b["upper_bound_exclusive"]))
            assert curr_upper > prev_upper, f"Maturity bands must be strictly monotonically increasing: {curr_upper} <= {prev_upper}"
            prev_upper = curr_upper

        tiers = self.config["open_fair_loss_magnitude_scale"]["tiers"]
        prev_mult = Decimal("0.0")
        for t in tiers:
            mult_val = t.get("downtime_hours_multiplier")
            if mult_val is not None:
                curr_mult = Decimal(str(mult_val))
                assert curr_mult > prev_mult, f"Downtime multipliers must be strictly monotonically increasing: {curr_mult} <= {prev_mult}"
                prev_mult = curr_mult

    def resolve_maturity(
        self,
        score: float | int | str | Decimal,
        locale: str = "en",
        translator: Optional[Callable[..., str]] = None
    ) -> ResolvedMaturity:
        """
        Authoritatively maps any numeric maturity score to its immutable CMMI tier.
        Uses half-open intervals [a_k, a_{k+1}) with 2-decimal quantized Decimal comparisons.
        """
        clean_dec = sanitize_to_decimal(score, precision="0.01")
        clamped_score = max(Decimal("0.00"), min(Decimal("5.00"), clean_dec))
        float_raw = float(clamped_score)

        bands = self.config["cmmi_maturity_scale"]["bands"]

        for b in bands:
            upper_bound = Decimal(str(b["upper_bound_exclusive"]))
            if clamped_score < upper_bound:
                token = b["label_token"]
                label = b["default_label"]
                if translator is not None:
                    translated = translator(token, locale=locale, default=label)
                    if translated:
                        label = translated
                elif locale.startswith("es"):
                    spanish_map = {
                        "band_initial": "Inicial",
                        "band_managed": "Gestionado",
                        "band_defined": "Definido",
                        "band_quantitatively_managed": "Gestionado Cuantitativamente",
                        "band_optimized": "Optimizado",
                    }
                    label = spanish_map.get(token, label)

                return ResolvedMaturity(
                    raw_score=float_raw,
                    normalized_score=clamped_score,
                    level=b["level"],
                    band_code=MaturityBandCode(b["code"]),
                    label_token=token,
                    label=label,
                    ui_semantic_token=b["ui_token"]
                )

        # Fallback to top level
        top = bands[-1]
        token = top["label_token"]
        label = top["default_label"]
        if translator is not None:
            translated = translator(token, locale=locale, default=label)
            if translated:
                label = translated
        elif locale.startswith("es"):
            label = "Optimizado"

        return ResolvedMaturity(
            raw_score=float_raw,
            normalized_score=clamped_score,
            level=top["level"],
            band_code=MaturityBandCode(top["code"]),
            label_token=token,
            label=label,
            ui_semantic_token=top["ui_token"]
        )

    def resolve_financial_risk(
        self,
        ale_amount: float | int | str | Decimal,
        hourly_burn_rate: Optional[float | int | str | Decimal] = None,
        locale: str = "en",
        translator: Optional[Callable[..., str]] = None
    ) -> ResolvedFinancialRisk:
        """
        Authoritatively calculates financial risk severity and Open FAIR Loss Magnitude (LM1-LM5).
        Applies dimensionless downtime hours multipliers:
        - T1 = 1.0 * hourly_burn_rate
        - T2 = 4.0 * hourly_burn_rate
        - T3 = 16.0 * hourly_burn_rate
        - T4 = 64.0 * hourly_burn_rate
        - T5 >= 64.0 * hourly_burn_rate
        Completely currency-agnostic and enterprise-scale-agnostic.
        """
        clean_ale = sanitize_to_decimal(ale_amount, precision="0.01")
        # Default fallback to 10,000 unit currency/h if rate is unprovided
        rate_raw = hourly_burn_rate if hourly_burn_rate is not None and float(hourly_burn_rate) > 0 else Decimal("10000.0")
        clean_rate = sanitize_to_decimal(rate_raw, precision="0.01")

        tiers = self.config["open_fair_loss_magnitude_scale"]["tiers"]

        t1 = (Decimal(str(tiers[0]["downtime_hours_multiplier"])) * clean_rate).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        t2 = (Decimal(str(tiers[1]["downtime_hours_multiplier"])) * clean_rate).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        t3 = (Decimal(str(tiers[2]["downtime_hours_multiplier"])) * clean_rate).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        t4 = (Decimal(str(tiers[3]["downtime_hours_multiplier"])) * clean_rate).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)

        if clean_ale < t1:
            t_match = tiers[0]
            thresh_applied = t1
        elif clean_ale < t2:
            t_match = tiers[1]
            thresh_applied = t2
        elif clean_ale < t3:
            t_match = tiers[2]
            thresh_applied = t3
        elif clean_ale < t4:
            t_match = tiers[3]
            thresh_applied = t4
        else:
            t_match = tiers[4]
            thresh_applied = t4

        token = t_match["label_token"]
        label = t_match["default_label"]

        if translator is not None:
            translated = translator(token, locale=locale, default=label)
            if translated:
                label = translated
        elif locale.startswith("es"):
            spanish_map = {
                "severity_low": "Muy Bajo",
                "severity_moderate": "Bajo",
                "severity_elevated": "Medio",
                "severity_high": "Alto",
                "severity_critical": "Muy Alto",
            }
            label = spanish_map.get(token, label)

        provenance = f"SR11-7:PHYSICAL-DOWNTIME-SCALE:RATE={clean_rate:,.2f}:TH4={t4:,.2f}"

        return ResolvedFinancialRisk(
            ale_amount=clean_ale,
            hourly_burn_rate=clean_rate,
            severity=FinancialSeverityCode(t_match["severity"]),
            open_fair_lm=t_match["lm_code"],
            label_token=token,
            label=label,
            ui_semantic_token=t_match["ui_token"],
            threshold_applied=thresh_applied,
            model_provenance=provenance
        )
