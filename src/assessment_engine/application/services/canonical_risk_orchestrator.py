"""Canonical Application-Layer Risk Quantification Service (SR 11-7 SSOT).

Enforces one single production pathway for actuarial loss quantification across both
single-tower and multi-tower assessments via BayesianFairCopulaEngine.
Eradicates split-brain heuristic writers, ensuring all financial metrics originate from
the verified stochastic kernel.
"""

from __future__ import annotations

import json
import logging
import math
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    EpistemicDissonanceRecord,
    FindingTelemetry,
    OperationalZone,
    PortfolioReproductionManifest,
    PortfolioRiskSummary,
    create_reproduction_manifest,
)
from assessment_engine.domain.models.parameter_lineage import (
    ActuarialFindingInputs,
    ActuarialFindingOutputs,
    ActuarialInputVector,
    DissonanceLineageRecord,
    ParameterConfidenceLevel,
    ParameterProvenanceRecord,
    ParameterSourceType,
    ParameterValidationStatus,
)
from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
)

logger = logging.getLogger(__name__)


class QuantificationStatus(StrEnum):
    """Explicit status documenting whether financial metrics could be defensibly quantified."""

    QUANTIFIED = "QUANTIFIED"
    NOT_QUANTIFIED = "NOT_QUANTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED_CONTEXT = "UNSUPPORTED_CONTEXT"


def _safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val) if math.isfinite(val) else default
    try:
        clean = str(val).replace(",", ".").strip()
        f = float(clean)
        return f if math.isfinite(f) else default
    except (ValueError, TypeError):
        return default


class CanonicalRiskOrchestrator:
    """The sole authoritative orchestrator for computing and hydrating financial risk metrics."""

    @classmethod
    def quantify_payloads(
        cls,
        payloads_by_tower: Dict[str, Dict[str, Any]],
        global_context: Optional[Dict[str, Any]] = None,
        persist_to_disk: bool = False,
        client_id: Optional[str] = None,
        doc_lang: str = "en",
    ) -> Tuple[Dict[str, Dict[str, Any]], Optional[PortfolioReproductionManifest]]:
        """Executes canonical Bayesian FAIR Copula quantification across any number of towers (1 to N)."""
        ctx = global_context or {}
        fin_tel = ctx.get("financial_telemetry") or {}
        eval_currency = str(
            fin_tel.get("currency")
            or fin_tel.get("currency_code")
            or ctx.get("currency")
            or "EUR"
        ).strip().upper()

        if not eval_currency or len(eval_currency) > 4:
            eval_currency = "EUR"

        actuarial_cfg = fin_tel.get("actuarial_calibration") or {}
        num_sims = int(actuarial_cfg.get("simulation_iterations") or 8192)
        copula_df = int(actuarial_cfg.get("copula_df") or 4)

        base_burn_rate = _safe_float(
            fin_tel.get("authoritative_hourly_downtime_cost")
            or fin_tel.get("hourly_downtime_rate")
            or fin_tel.get("hourly_burn_rate"),
            default=5000.0,
        ) or 5000.0

        zone_configs = {
            "TIER_1_MISSION_CRITICAL": {
                "burn_mult": 0.60,
                "h_max": 24.0,
                "retention": 1.00,
                "ceil_hours": 24.0,
                "repl_ratio": 0.20,
            },
            "TIER_2_CORE_OPERATIONS": {
                "burn_mult": 0.35,
                "h_max": 48.0,
                "retention": 0.85,
                "ceil_hours": 48.0,
                "repl_ratio": 0.15,
            },
            "TIER_3_INTERNAL_SUPPORT": {
                "burn_mult": 0.15,
                "h_max": 72.0,
                "retention": 0.50,
                "ceil_hours": 72.0,
                "repl_ratio": 0.05,
            },
        }

        all_telemetry: List[FindingTelemetry] = []
        telemetry_meta: Dict[Tuple[str, str], Tuple[FindingTelemetry, Dict[str, Any], Dict[str, Any]]] = {}

        registry = get_actuarial_archetype_registry()

        for t_code, payload in payloads_by_tower.items():
            t_mapping = registry.get_mapping_for_tower(t_code)
            t_arch = t_mapping.primary_archetype

            # Determine operational zone for the tower
            if t_code in ("T1", "T4", "T5", "T10"):
                z_id = "TIER_1_MISSION_CRITICAL"
            elif t_code in ("T2", "T3", "T6", "T8"):
                z_id = "TIER_2_CORE_OPERATIONS"
            else:
                z_id = "TIER_3_INTERNAL_SUPPORT"

            z_spec = zone_configs[z_id]
            derived_hourly_rate = round(base_burn_rate * z_spec["burn_mult"], 2)

            zone = OperationalZone(
                zone_id=z_id,
                hourly_burn_rate=derived_hourly_rate,
                max_annual_outage_hours=z_spec["h_max"],
                secondary_loss_retention_factor=z_spec["retention"],
                catastrophic_recovery_ceiling_hours=z_spec["ceil_hours"],
                emergency_replacement_ratio=z_spec["repl_ratio"],
            )

            pillars = payload.get("pillars_analysis") or []
            finding_seq = 0

            for pillar in pillars:
                if not isinstance(pillar, dict):
                    continue
                cmmi_raw = _safe_float(pillar.get("score") or pillar.get("maturity_score"), default=2.5) or 2.5
                cmmi_pillar = max(1.0, min(5.0, cmmi_raw))

                findings = pillar.get("health_check_asis") or pillar.get("findings") or []
                for hc in findings:
                    if not isinstance(hc, dict):
                        continue

                    finding_seq += 1
                    f_id = str(hc.get("node_id") or f"{t_code}_F{finding_seq:03d}")
                    hc["node_id"] = f_id
                    title = str(hc.get("capability") or hc.get("title") or f"Finding {f_id}")

                    raw_sev = str(hc.get("severity") or hc.get("impact_severity") or "MEDIUM").upper()
                    raw_lm = _safe_float(hc.get("loss_magnitude"))
                    raw_tef = _safe_float(hc.get("threat_event_frequency"))

                    is_spof = bool(hc.get("is_spof") or raw_sev == "CRITICAL")
                    tef_mode = raw_tef if (raw_tef and 0.0 < raw_tef <= 10.0) else 0.30
                    tef_min = _safe_float(hc.get("tef_pert_min"), default=tef_mode * 0.45) or (tef_mode * 0.45)
                    tef_max = _safe_float(hc.get("tef_pert_max"), default=tef_mode * 2.20) or (tef_mode * 2.20)
                    if not (tef_min <= tef_mode <= tef_max):
                        tef_min = min(tef_min, tef_mode)
                        tef_max = max(tef_max, tef_mode)

                    rto_mode = _safe_float(hc.get("recovery_time_hours") or hc.get("rto_hours_mode"), default=4.0) or 4.0
                    rto_min = _safe_float(hc.get("rto_hours_min"), default=rto_mode * 0.45) or (rto_mode * 0.45)
                    rto_max = _safe_float(hc.get("rto_hours_max"), default=rto_mode * 2.50) or (rto_mode * 2.50)
                    if not (rto_min <= rto_mode <= rto_max):
                        rto_min = min(rto_min, rto_mode)
                        rto_max = max(rto_max, rto_mode)

                    lm_factor = (raw_lm / 5.0) if (raw_lm and 0.0 < raw_lm <= 5.0) else 0.50

                    # Polymorphic secondary loss calculation (Vector 5)
                    explicit_sec = _safe_float(hc.get("secondary_loss_mean"))
                    if explicit_sec is not None:
                        sec_mean = explicit_sec
                    elif t_arch == LossArchetypeType.REGULATORY_AND_BREACH:
                        ann_rev = _safe_float(fin_tel.get("annual_revenue") or fin_tel.get("global_annual_revenue"), default=100_000_000.0) or 100_000_000.0
                        max_fine = max(20_000_000.0, ann_rev * 0.04)
                        b2b_damp = _safe_float(fin_tel.get("b2b_exposure_dampener"), default=0.25) or 0.25
                        sec_mean = max_fine * (0.01 + 0.03 * lm_factor) * b2b_damp
                    elif t_arch == LossArchetypeType.CAPITAL_INEFFICIENCY:
                        opex = _safe_float(fin_tel.get("annual_it_opex"), default=5_000_000.0) or 5_000_000.0
                        sec_mean = opex * (0.02 + 0.04 * lm_factor)
                    elif t_arch == LossArchetypeType.PRODUCTIVITY_TOIL:
                        wage = _safe_float(fin_tel.get("fully_burdened_hourly_rate"), default=65.0) or 65.0
                        sec_mean = wage * (20.0 + 30.0 * lm_factor)
                    else:
                        sec_mean = derived_hourly_rate * (1.5 + 2.0 * lm_factor)

                    if is_spof and t_arch == LossArchetypeType.AVAILABILITY_OUTAGE:
                        sec_mean = max(sec_mean, derived_hourly_rate * 2.65)

                    repl_cost = _safe_float(hc.get("direct_replacement_cost"), default=0.0) or 0.0
                    alpha_rad = _safe_float(hc.get("blast_radius_alpha"), default=0.60) or 0.60
                    alpha_rad = max(0.05, min(1.0, alpha_rad))
                    rho_dep = _safe_float(hc.get("shared_dependence_factor"), default=0.30) or 0.30

                    k_failures = int(hc.get("audit_k_failures") or 0)
                    n_trials = int(hc.get("audit_n_trials") or 0)

                    dissonance_obj: Optional[EpistemicDissonanceRecord] = None
                    if hc.get("epistemic_dissonance"):
                        d_dict = hc["epistemic_dissonance"]
                        dissonance_obj = EpistemicDissonanceRecord(
                            record_id=str(d_dict.get("record_id") or f"DISS_{f_id}"),
                            finding_id=f_id,
                            claimed_maturity=float(d_dict.get("claimed_maturity") or cmmi_pillar),
                            empirical_reality_maturity=float(d_dict.get("empirical_reality_maturity") or cmmi_pillar),
                            dissonance_weight=float(d_dict.get("dissonance_weight") or 0.5),
                            transcript_evidence_quote=str(d_dict.get("transcript_evidence_quote") or ""),
                            impact_vector=str(d_dict.get("impact_vector") or "BOTH"),
                        )

                    ft = FindingTelemetry(
                        finding_id=f_id,
                        tower_id=t_code,
                        title=title,
                        cmmi_maturity=cmmi_pillar,
                        zone=zone,
                        tef_pert_min=tef_min,
                        tef_pert_mode=tef_mode,
                        tef_pert_max=tef_max,
                        rto_hours_min=rto_min,
                        rto_hours_mode=rto_mode,
                        rto_hours_max=rto_max,
                        secondary_loss_mean=sec_mean,
                        is_spof=is_spof,
                        shared_dependence_factor=rho_dep,
                        blast_radius_alpha=alpha_rad,
                        catastrophic_rto_hours=zone.catastrophic_recovery_ceiling_hours,
                        direct_replacement_cost=repl_cost,
                        audit_k_failures=k_failures,
                        audit_n_trials=n_trials,
                        dissonance=dissonance_obj,
                    )
                    all_telemetry.append(ft)
                    telemetry_meta[(t_code, f_id)] = (ft, hc, {
                        "derived_hourly_rate": derived_hourly_rate,
                        "raw_tef": raw_tef,
                        "raw_lm": raw_lm,
                    })

        if not all_telemetry:
            for payload in payloads_by_tower.values():
                payload["quantification_status"] = QuantificationStatus.INSUFFICIENT_EVIDENCE.value
                payload["total_fair_ale"] = None
                payload["total_fair_p90"] = None
                payload["total_fair_cvar_90"] = None
                for p in payload.get("pillars_analysis", []):
                    for f in p.get("health_check_asis", []):
                        f["quantification_status"] = QuantificationStatus.INSUFFICIENT_EVIDENCE.value
                        f["fair_ale_score"] = None
                        f["fair_p90_score"] = None
                        f["fair_cvar_score"] = None
            return payloads_by_tower, None

        # 2. Run BayesianFairCopulaEngine as sole production SSOT
        engine = BayesianFairCopulaEngine(
            num_simulations=num_sims,
            copula_df=copula_df,
        )
        summary: PortfolioRiskSummary = engine.evaluate_portfolio(all_telemetry, currency_code=eval_currency)

        # 3. Build reproduction manifest
        manifest = create_reproduction_manifest(
            engine=engine,
            findings=all_telemetry,
            summary=summary,
            currency_code=eval_currency,
        )

        # 4. Populate canonical outputs into payloads
        for t_code, payload in payloads_by_tower.items():
            if t_code not in summary.towers:
                continue
            t_res = summary.towers[t_code]
            payload["quantification_status"] = QuantificationStatus.QUANTIFIED.value
            payload["total_fair_ale"] = t_res.portfolio_allocated_ale
            payload["standalone_fair_ale"] = t_res.standalone_ale
            payload["total_fair_p90"] = t_res.var_90
            payload["total_fair_cvar_90"] = t_res.cvar_90
            payload["total_fair_max"] = t_res.var_99
            payload["total_fair_cvar_99"] = t_res.cvar_99
            payload["primary_fair_ale"] = t_res.primary_ale
            payload["secondary_fair_ale"] = t_res.secondary_ale
            payload["worst_crisis_event"] = t_res.worst_crisis_event
            payload["worst_crisis_rto_hours"] = t_res.worst_crisis_rto_hours

            finding_results = {f.finding_id: f for f in t_res.findings}

            for pillar in payload.get("pillars_analysis", []):
                if not isinstance(pillar, dict):
                    continue
                for hc in pillar.get("health_check_asis", []):
                    if not isinstance(hc, dict):
                        continue
                    f_id = hc.get("node_id")
                    if f_id in finding_results:
                        f_res = finding_results[f_id]
                        hc["quantification_status"] = QuantificationStatus.QUANTIFIED.value
                        hc["fair_ale_score"] = f_res.portfolio_allocated_ale
                        hc["fair_p90_score"] = f_res.var_90
                        hc["fair_cvar_score"] = f_res.cvar_90
                        hc["fair_max_score"] = f_res.var_99
                        hc["fair_cvar_99_score"] = f_res.cvar_99
                        hc["worst_crisis_event"] = f_res.worst_crisis_event
                        hc["worst_crisis_rto_hours"] = f_res.worst_crisis_rto_hours
                        hc["dissonance_applied"] = f_res.dissonance_applied

                        # Build and attach verified ActuarialInputVector
                        meta_tuple = telemetry_meta.get((t_code, f_id))
                        if meta_tuple:
                            ft_obj, _, _ = meta_tuple
                            diss_record = None
                            if ft_obj.dissonance:
                                diss_record = DissonanceLineageRecord(
                                    record_id=ft_obj.dissonance.record_id,
                                    finding_id=ft_obj.dissonance.finding_id,
                                    claimed_maturity=ft_obj.dissonance.claimed_maturity,
                                    empirical_reality_maturity=ft_obj.dissonance.empirical_reality_maturity,
                                    dissonance_weight=ft_obj.dissonance.dissonance_weight,
                                    transcript_evidence_quote=ft_obj.dissonance.transcript_evidence_quote,
                                    impact_vector=ft_obj.dissonance.impact_vector,
                                )

                            inputs_obj = ActuarialFindingInputs(
                                cmmi_maturity=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.cmmi_maturity,
                                    effective_value=ft_obj.cmmi_maturity,
                                    unit="cmmi_index",
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD,
                                    estimation_method="Pillar questionnaire evaluation",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                zone_id=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.zone.zone_id,
                                    effective_value=ft_obj.zone.zone_id,
                                    unit="zone_id",
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="Operational tier criticality mapping",
                                    confidence=ParameterConfidenceLevel.HIGH,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                hourly_burn_rate=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.zone.hourly_burn_rate,
                                    effective_value=ft_obj.zone.hourly_burn_rate,
                                    unit=f"{eval_currency}/hour",
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="Turnover / 8760 * tier ratio",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                max_annual_outage_hours=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.zone.max_annual_outage_hours,
                                    effective_value=ft_obj.zone.max_annual_outage_hours,
                                    unit="hours",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Tier SLA ceiling",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                secondary_loss_retention_factor=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.zone.secondary_loss_retention_factor,
                                    effective_value=ft_obj.zone.secondary_loss_retention_factor,
                                    unit="ratio",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Zone response retention",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                catastrophic_recovery_ceiling_hours=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.zone.catastrophic_recovery_ceiling_hours,
                                    effective_value=ft_obj.zone.catastrophic_recovery_ceiling_hours,
                                    unit="hours",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Disaster recovery boundary",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                emergency_replacement_ratio=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.zone.emergency_replacement_ratio,
                                    effective_value=ft_obj.zone.emergency_replacement_ratio,
                                    unit="ratio",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="SPOF emergency buffer",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                tef_pert_min=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.tef_pert_min,
                                    effective_value=ft_obj.tef_pert_min,
                                    unit="events/year",
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="PERT min from mode * 0.45",
                                    confidence=ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                tef_pert_mode=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.tef_pert_mode,
                                    effective_value=ft_obj.tef_pert_mode,
                                    unit="events/year",
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("threat_event_frequency") else ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Ordinal frequency mapping",
                                    confidence=ParameterConfidenceLevel.MEDIUM if hc.get("threat_event_frequency") else ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                tef_pert_max=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.tef_pert_max,
                                    effective_value=ft_obj.tef_pert_max,
                                    unit="events/year",
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="PERT max from mode * 2.20",
                                    confidence=ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                rto_hours_min=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.rto_hours_min,
                                    effective_value=ft_obj.rto_hours_min,
                                    unit="hours",
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="PERT min from RTO mode * 0.45",
                                    confidence=ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                rto_hours_mode=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.rto_hours_mode,
                                    effective_value=ft_obj.rto_hours_mode,
                                    unit="hours",
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("recovery_time_hours") else ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Explicit recovery time or prior mode",
                                    confidence=ParameterConfidenceLevel.MEDIUM if hc.get("recovery_time_hours") else ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                rto_hours_max=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.rto_hours_max,
                                    effective_value=ft_obj.rto_hours_max,
                                    unit="hours",
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="PERT max from RTO mode * 2.50",
                                    confidence=ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                secondary_loss_mean=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.secondary_loss_mean,
                                    effective_value=ft_obj.secondary_loss_mean,
                                    unit=eval_currency,
                                    source_type=ParameterSourceType.DERIVED,
                                    estimation_method="Polymorphic secondary domain calculation",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                is_spof=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.is_spof,
                                    effective_value=ft_obj.is_spof,
                                    unit="boolean",
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("is_spof") is not None else ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Severity and explicit finding metadata",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                shared_dependence_factor=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.shared_dependence_factor,
                                    effective_value=ft_obj.shared_dependence_factor,
                                    unit="ratio",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Sector intra-tower baseline",
                                    confidence=ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                blast_radius_alpha=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.blast_radius_alpha,
                                    effective_value=ft_obj.blast_radius_alpha,
                                    unit="ratio",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Domain operational scope factor",
                                    confidence=ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                catastrophic_rto_hours=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.catastrophic_rto_hours,
                                    effective_value=ft_obj.catastrophic_rto_hours,
                                    unit="hours",
                                    source_type=ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Zone catastrophic ceiling",
                                    confidence=ParameterConfidenceLevel.MEDIUM,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                direct_replacement_cost=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.direct_replacement_cost,
                                    effective_value=ft_obj.direct_replacement_cost,
                                    unit=eval_currency,
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("direct_replacement_cost") else ParameterSourceType.MODEL_DEFAULT,
                                    estimation_method="Explicit hardware inventory cost",
                                    confidence=ParameterConfidenceLevel.MEDIUM if hc.get("direct_replacement_cost") else ParameterConfidenceLevel.LOW,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                audit_k_failures=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.audit_k_failures,
                                    effective_value=ft_obj.audit_k_failures,
                                    unit="count",
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD,
                                    estimation_method="Audit identified control gaps",
                                    confidence=ParameterConfidenceLevel.HIGH,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                audit_n_trials=ParameterProvenanceRecord(
                                    estimated_value=ft_obj.audit_n_trials,
                                    effective_value=ft_obj.audit_n_trials,
                                    unit="count",
                                    source_type=ParameterSourceType.ASSESSMENT_PAYLOAD,
                                    estimation_method="Evaluated audit control count",
                                    confidence=ParameterConfidenceLevel.HIGH,
                                    validation_status=ParameterValidationStatus.UNCONFIRMED,
                                ),
                                dissonance_record=diss_record,
                            )

                            outputs_obj = ActuarialFindingOutputs(
                                mean_vuln=f_res.mean_vuln,
                                mean_lef=f_res.mean_lef,
                                mean_sle=f_res.mean_sle,
                                standalone_ale=f_res.standalone_ale,
                                portfolio_allocated_ale=f_res.portfolio_allocated_ale,
                                var_90=f_res.var_90,
                                cvar_90=f_res.cvar_90,
                                var_95=f_res.var_95,
                                var_99=f_res.var_99,
                                cvar_99=f_res.cvar_99,
                                worst_crisis_event=f_res.worst_crisis_event,
                                worst_crisis_rto_hours=f_res.worst_crisis_rto_hours,
                            )

                            input_vector = ActuarialInputVector(
                                finding_id=f_id,
                                tower_id=t_code,
                                currency_code=eval_currency,
                                inputs=inputs_obj,
                                outputs=outputs_obj,
                            )
                            hc["actuarial_input_vector"] = input_vector.model_dump(mode="json")

            if persist_to_disk:
                code_lower = t_code.lower()
                client_norm = client_id.strip() if client_id else "molins"
                repo_root = Path(__file__).resolve().parents[4]
                local_dir = repo_root / "working" / client_norm / t_code
                local_path = local_dir / f"blueprint_{code_lower}_payload.json"
                if local_path.exists():
                    try:
                        with open(local_path, "w", encoding="utf-8") as pf:
                            json.dump(payload, pf, indent=2, ensure_ascii=False)
                    except Exception as p_err:
                        logger.warning("Could not persist payload for tower %s: %s", t_code, p_err)

                try:
                    from assessment_engine.application.tools.actuarial_ledger_generator import (
                        generate_actuarial_ledger,
                    )
                    generate_actuarial_ledger(t_code, payload)
                except Exception as ledger_err:
                    logger.warning("Could not flush actuarial ledger for tower %s: %s", t_code, ledger_err)

        return payloads_by_tower, manifest

    @classmethod
    def quantify_single_tower(
        cls,
        tower_id: str,
        blueprint_payload: Dict[str, Any],
        global_context: Optional[Dict[str, Any]] = None,
        persist_to_disk: bool = False,
        client_id: Optional[str] = None,
        doc_lang: str = "en",
    ) -> Dict[str, Any]:
        """Convenience method to execute canonical Bayesian quantification on a single tower."""
        single_map = {tower_id: blueprint_payload}
        quantified_map, _ = cls.quantify_payloads(
            payloads_by_tower=single_map,
            global_context=global_context,
            persist_to_disk=persist_to_disk,
            client_id=client_id,
            doc_lang=doc_lang,
        )
        return quantified_map[tower_id]
