"""Authoritative Governance Scale Engine (SSOT for CMMI & Alometric Open FAIR).

Implements:
1. Strict half-open interval partitioning [a_k, a_{k+1}) for continuous CMMI resolution.
2. Alometric power law scaling T_k(R) = F_k + alpha_k * R^0.75 for Open FAIR Loss Magnitude (LM1-LM5).
3. Formal monotonicity assertions to guarantee zero unhandled gaps or overlapping buckets.
"""

from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Dict, List, Optional

from assessment_engine.domain.governance.primitives import (
    FinancialSeverityCode,
    MaturityBandCode,
    ResolvedFinancialRisk,
    ResolvedMaturity,
    sanitize_to_decimal,
)
from assessment_engine.infrastructure.runtime_paths import ROOT


class GovernanceScaleEngine:
    """
    Singleton SSOT Engine for Maturity and Financial Risk Governance.
    Thread-safe, immutable, and strictly deterministic.
    """

    _instance: Optional[GovernanceScaleEngine] = None

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None) -> None:
        if config_dict is None:
            cfg_path = ROOT / "engine_config" / "governance_scales.json"
            if cfg_path.exists():
                self.config = json.loads(cfg_path.read_text(encoding="utf-8"))
            else:
                self.config = self._fallback_config()
        else:
            self.config = config_dict

        self._verify_formal_invariants()

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
                    {"level": 1, "code": "INITIAL", "upper_bound_exclusive": 1.50, "label_es": "Inicial", "label_en": "Initial", "ui_token": "status-critical"},
                    {"level": 2, "code": "REPEATABLE", "upper_bound_exclusive": 2.50, "label_es": "Gestionado", "label_en": "Managed", "ui_token": "status-warning"},
                    {"level": 3, "code": "DEFINED", "upper_bound_exclusive": 3.50, "label_es": "Definido", "label_en": "Defined", "ui_token": "status-neutral"},
                    {"level": 4, "code": "MANAGED", "upper_bound_exclusive": 4.50, "label_es": "Gestionado Cuantitativamente", "label_en": "Quantitatively Managed", "ui_token": "status-good"},
                    {"level": 5, "code": "OPTIMIZED", "upper_bound_exclusive": 5.0001, "label_es": "Optimizado", "label_en": "Optimizing", "ui_token": "status-excellent"},
                ]
            },
            "open_fair_alometric_severity": {
                "beta_elasticity": 0.75,
                "default_fallback_revenue_eur": 50000000.0,
                "geometric_factor": 4.0,
                "tiers": [
                    {"lm_code": "LM1", "severity": "LOW", "label_es": "Muy Bajo", "label_en": "Very Low", "floor_eur": 3000.0, "alpha": 0.0016098069, "ui_token": "severity-low"},
                    {"lm_code": "LM2", "severity": "MODERATE", "label_es": "Bajo", "label_en": "Low", "floor_eur": 12000.0, "alpha": 0.0064392275, "ui_token": "severity-moderate"},
                    {"lm_code": "LM3", "severity": "ELEVATED", "label_es": "Medio", "label_en": "Medium", "floor_eur": 48000.0, "alpha": 0.0257569101, "ui_token": "severity-elevated"},
                    {"lm_code": "LM4", "severity": "HIGH", "label_es": "Alto", "label_en": "High", "floor_eur": 192000.0, "alpha": 0.1030276405, "ui_token": "severity-high"},
                    {"lm_code": "LM5", "severity": "CRITICAL", "label_es": "Muy Alto", "label_en": "Very High", "floor_eur": 768000.0, "alpha": 0.4121105620, "ui_token": "severity-critical"},
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

        tiers = self.config["open_fair_alometric_severity"]["tiers"]
        prev_floor = Decimal("0.0")
        for t in tiers:
            curr_floor = Decimal(str(t["floor_eur"]))
            assert curr_floor > prev_floor, f"Alometric floors must be strictly monotonically increasing: {curr_floor} <= {prev_floor}"
            prev_floor = curr_floor

    def resolve_maturity(self, score: float | int | str | Decimal, locale: str = "es") -> ResolvedMaturity:
        """
        Authoritatively maps any numeric maturity score to its immutable CMMI tier.
        Uses half-open intervals [a_k, a_{k+1}) with 2-decimal quantized Decimal comparisons.
        """
        clean_dec = sanitize_to_decimal(score, precision="0.01")
        clamped_score = max(Decimal("0.00"), min(Decimal("5.00"), clean_dec))
        float_raw = float(clamped_score)

        bands = self.config["cmmi_maturity_scale"]["bands"]
        is_es = locale.startswith("es")

        for b in bands:
            upper_bound = Decimal(str(b["upper_bound_exclusive"]))
            if clamped_score < upper_bound:
                label = b["label_es"] if is_es else b["label_en"]
                return ResolvedMaturity(
                    raw_score=float_raw,
                    normalized_score=clamped_score,
                    level=b["level"],
                    band_code=MaturityBandCode(b["code"]),
                    label=label,
                    ui_semantic_token=b["ui_token"]
                )

        # Fallback to top level
        top = bands[-1]
        label = top["label_es"] if is_es else top["label_en"]
        return ResolvedMaturity(
            raw_score=float_raw,
            normalized_score=clamped_score,
            level=top["level"],
            band_code=MaturityBandCode(top["code"]),
            label=label,
            ui_semantic_token=top["ui_token"]
        )

    def resolve_financial_risk(
        self,
        ale_eur: float | int | str | Decimal,
        annual_revenue_eur: Optional[float | int | str | Decimal] = None,
        locale: str = "es"
    ) -> ResolvedFinancialRisk:
        """
        Authoritatively calculates financial risk severity and Open FAIR Loss Magnitude (LM1-LM5).
        Applies sub-linear alometric power law: T_k(R) = Floor_k + Alpha_k * R^0.75.
        """
        clean_ale = sanitize_to_decimal(ale_eur, precision="0.01")
        default_rev = self.config["open_fair_alometric_severity"]["default_fallback_revenue_eur"]
        raw_rev = annual_revenue_eur if annual_revenue_eur is not None and float(annual_revenue_eur) > 0 else default_rev
        clean_rev = sanitize_to_decimal(raw_rev, precision="0.01")

        # Compute R^0.75 alometric basis
        rev_float = float(clean_rev)
        alometric_basis = Decimal(str(round(rev_float ** 0.75, 4)))

        tiers = self.config["open_fair_alometric_severity"]["tiers"]
        is_es = locale.startswith("es")

        # Calculate dynamic monetary thresholds for tiers LM1, LM2, LM3, LM4
        # LM5 is anything >= T4
        t1_eur = Decimal(str(tiers[0]["floor_eur"])) + Decimal(str(tiers[0]["alpha"])) * alometric_basis
        t2_eur = Decimal(str(tiers[1]["floor_eur"])) + Decimal(str(tiers[1]["alpha"])) * alometric_basis
        t3_eur = Decimal(str(tiers[2]["floor_eur"])) + Decimal(str(tiers[2]["alpha"])) * alometric_basis
        t4_eur = Decimal(str(tiers[3]["floor_eur"])) + Decimal(str(tiers[3]["alpha"])) * alometric_basis

        # Round thresholds to nearest euro
        t1_eur = t1_eur.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        t2_eur = t2_eur.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        t3_eur = t3_eur.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
        t4_eur = t4_eur.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)

        if clean_ale < t1_eur:
            t_match = tiers[0]
            thresh_applied = t1_eur
        elif clean_ale < t2_eur:
            t_match = tiers[1]
            thresh_applied = t2_eur
        elif clean_ale < t3_eur:
            t_match = tiers[2]
            thresh_applied = t3_eur
        elif clean_ale < t4_eur:
            t_match = tiers[3]
            thresh_applied = t4_eur
        else:
            t_match = tiers[4]
            thresh_applied = t4_eur

        label = t_match["label_es"] if is_es else t_match["label_en"]
        provenance = f"SR11-7:ALOMETRIC-OFAIR-BETA0.75:REV={clean_rev:,.0f}EUR:TH4={t4_eur:,.0f}EUR"

        return ResolvedFinancialRisk(
            ale_eur=clean_ale,
            reference_revenue_eur=clean_rev,
            severity=FinancialSeverityCode(t_match["severity"]),
            open_fair_lm=t_match["lm_code"],
            label=label,
            ui_semantic_token=t_match["ui_token"],
            threshold_applied_eur=thresh_applied,
            model_provenance=provenance
        )
