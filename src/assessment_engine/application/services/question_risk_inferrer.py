"""Universal Ontological Question-to-Risk Inferrer (SR 11-7 / CMMI Level Mapping)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from assessment_engine.application.services.actuarial_inference_engine import (
    ActuarialInferenceEngine,
    TenantActuarialProfile,
)


class QuestionRiskInferrer:
    """Translates low maturity questionnaire scores (< 3.0) into concrete technical risks.

    Replaces robotic boilerplate strings with the exact physical failure modes defined
    in the 5-level maturity rubrics across all 193 technical questions.
    """

    def __init__(self, catalog_path: Optional[Path] = None) -> None:
        if catalog_path is None:
            catalog_path = self._default_catalog_path()
        self._catalog_path = catalog_path
        self._catalog: Dict[str, Any] = self._load_catalog(catalog_path)
        self._actuarial_engine = ActuarialInferenceEngine()

    @staticmethod
    def _default_catalog_path() -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            cand = parent / "engine_config" / "taxonomy" / "universal_question_risk_map.json"
            if cand.is_file():
                return cand
        raise FileNotFoundError("Could not locate universal_question_risk_map.json")

    @staticmethod
    def _load_catalog(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Malformed question catalog in {path}: expected dict")
        return data

    def infer_risk_for_kpi(
        self,
        tower_code: str,
        pillar_id: str,
        pillar_name: str,
        kpi_id: str,
        kpi_name: str,
        score: float,
        profile: Optional[TenantActuarialProfile] = None,
        doc_lang: str = "es",
    ) -> Dict[str, Any]:
        """Infers a concrete technical finding and actuarial loss from a low-maturity score."""
        normalized_tower = tower_code.strip().upper()
        clean_kpi = kpi_id.strip()

        # Find matching question in the 193-question catalog
        matched_q = None
        for q_id, q_data in self._catalog.items():
            if clean_kpi and (q_data.get("kpi_id") == clean_kpi or q_id.startswith(f"{clean_kpi}.")):
                matched_q = q_data
                break

        if not matched_q and pillar_id:
            clean_p = pillar_id.strip()
            for q_id, q_data in self._catalog.items():
                if q_data.get("pillar_id") == clean_p or q_id.startswith(f"{clean_p}."):
                    matched_q = q_data
                    break

        # Extract specific failure mode from rubric level 1 or 2
        if matched_q:
            if score <= 1.5:
                failure_desc = matched_q.get("level_1_failure_mode") or matched_q.get("level_2_vulnerability")
            else:
                failure_desc = matched_q.get("level_2_vulnerability") or matched_q.get("level_1_failure_mode")
            q_context = matched_q.get("question_text") or ""
        else:
            failure_desc = f"Absence of technical controls and automated monitoring in {kpi_name}."
            q_context = ""

        # Compute Bayesian latent actuarial metrics
        latent = self._actuarial_engine.calculate_latent_risk(
            tower_code=normalized_tower,
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            profile=profile,
        )

        rto_h = max(4.0, round(latent.single_loss_expectancy / 12000.0, 1))
        repl_cost = round(latent.single_loss_expectancy * 0.35, 2)

        from assessment_engine.domain.actuarial.plain_language_narrative import (
            PlainLanguageRiskNarrative,
        )

        industry_key = (
            profile.industry_vertical
            if profile and profile.industry_vertical
            else "general"
        )
        if profile and getattr(profile, "hourly_burn_rate", None) is not None and float(profile.hourly_burn_rate) > 0:
            derived_hourly_rate = float(profile.hourly_burn_rate)
        elif profile and getattr(profile, "annual_revenue", None) is not None and float(profile.annual_revenue) > 0:
            derived_hourly_rate = round(float(profile.annual_revenue) / 8760.0, 2)
        else:
            derived_hourly_rate = 0.0
        plain_explanation = PlainLanguageRiskNarrative.format_plain_narrative(
            tower_code=normalized_tower,
            kpi_name=kpi_name,
            failure_desc=failure_desc,
            industry=industry_key,
            sle=latent.single_loss_expectancy,
            ale=latent.annual_loss_expectancy,
            rto_hours=rto_h,
            hourly_rate=derived_hourly_rate,
            doc_lang=doc_lang,
        )

        finding_text = f"{failure_desc}"
        business_risk = plain_explanation

        return {
            "node_id": f"{pillar_id}-CANONICAL-01",
            "capability": pillar_name,
            "finding": finding_text,
            "risk_observed": finding_text,
            "impact_severity": "HIGH" if latent.annual_loss_expectancy > 50000.0 else "MEDIUM",
            "impact": "HIGH" if latent.annual_loss_expectancy > 50000.0 else "MEDIUM",
            "severity": "HIGH" if latent.annual_loss_expectancy > 50000.0 else "MEDIUM",
            "business_risk": business_risk,
            "primary_impact": business_risk,
            "threat_event_frequency": max(0.05, round(latent.loss_event_frequency, 2)),
            "loss_magnitude": 3.0,
            "recovery_time_hours": rto_h,
            "direct_replacement_cost": repl_cost,
            "fair_ale_score": latent.annual_loss_expectancy,
            "fair_p90_score": latent.value_at_risk_90,
            "fair_min_score": round(latent.annual_loss_expectancy * 0.25, 2),
            "quantification_status": "QUANTIFIED",
            "epistemic_state": "SURVEY_INFERRED_QUANTIFIED",
        }
