"""Actuarial Input Resolver and Evidence Grounding Service (SR 11-7).

Constructs fully-validated ActuarialFindingInputs and FindingTelemetry objects prior to Monte Carlo simulation.
Eliminates silent defaults, parses booleans strictly, enforces PERT and CMMI bounds, and tags quantification status.
"""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Any, Dict, Optional, Tuple

from assessment_engine.domain.bayesian_fair_copula_engine import (
    EpistemicDissonanceRecord,
    FindingTelemetry,
    OperationalZone,
)
from assessment_engine.domain.models.parameter_lineage import (
    ActuarialFindingInputs,
    DissonanceLineageRecord,
    ParameterConfidenceLevel,
    ParameterProvenanceRecord,
    ParameterSourceType,
    ParameterValidationStatus,
)
from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType


class QuantificationStatus(StrEnum):
    """Explicit status documenting whether financial metrics could be defensibly quantified."""

    QUANTIFIED = "QUANTIFIED"
    ESTIMATED_LOW_CONFIDENCE = "ESTIMATED_LOW_CONFIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED_CONTEXT = "UNSUPPORTED_CONTEXT"
    NOT_QUANTIFIED = "NOT_QUANTIFIED"


def parse_strict_bool(val: Any, default: bool = False) -> bool:
    """Parses a boolean strictly without Python's bool('false') truthiness pitfall."""
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    clean = str(val).strip().lower()
    if clean in ("true", "1", "yes", "t", "y"):
        return True
    if clean in ("false", "0", "no", "f", "n"):
        return False
    return default


def parse_strict_float(val: Any) -> Optional[float]:
    """Parses a float, distinguishing None from 0.0, rejecting non-finite values."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val) if math.isfinite(val) else None
    try:
        clean = str(val).replace(",", ".").strip()
        f = float(clean)
        return f if math.isfinite(f) else None
    except (ValueError, TypeError):
        return None


class ActuarialInputResolver:
    """Authoritative input resolver that binds inputs, parameter packs, and telemetry."""

    @classmethod
    def resolve_finding_inputs(
        cls,
        hc: Dict[str, Any],
        tower_id: str,
        pillar_cmmi: float,
        zone: OperationalZone,
        archetype: LossArchetypeType,
        currency_code: str,
        annual_revenue: Optional[float] = None,
        annual_it_opex: Optional[float] = None,
        hourly_wage: Optional[float] = None,
    ) -> Tuple[ActuarialFindingInputs, FindingTelemetry, QuantificationStatus]:
        """Resolves raw finding dict into verified ActuarialFindingInputs and FindingTelemetry."""
        f_id = str(hc.get("node_id") or "UNKNOWN_FINDING")
        title = str(hc.get("capability") or hc.get("title") or f"Finding {f_id}")

        corr_audit = hc.get("last_correction_audit") or {}
        corr_param = corr_audit.get("parameter_name")
        corr_orig = corr_audit.get("original_estimated_value")
        corr_src = corr_audit.get("source")
        corr_rev = corr_audit.get("review_identifier")

        def _build_provenance(
            p_name: str,
            est_val: Any,
            eff_val: Any,
            unit: str,
            default_source: ParameterSourceType,
            default_method: str,
            default_conf: ParameterConfidenceLevel,
        ) -> ParameterProvenanceRecord:
            if corr_param == p_name and corr_orig is not None:
                return ParameterProvenanceRecord(
                    estimated_value=corr_orig,
                    effective_value=eff_val,
                    unit=unit,
                    source_type=ParameterSourceType.CLIENT_CONFIRMED,
                    source_reference=str(corr_src or "Client audit correction"),
                    estimation_method=f"Client override ({corr_rev or 'AUDIT'})",
                    confidence=ParameterConfidenceLevel.HIGH,
                    validation_status=ParameterValidationStatus.CLIENT_OVERRIDDEN,
                    client_override=True,
                )
            return ParameterProvenanceRecord(
                estimated_value=est_val,
                effective_value=eff_val,
                unit=unit,
                source_type=default_source,
                estimation_method=default_method,
                confidence=default_conf,
                validation_status=ParameterValidationStatus.UNCONFIRMED,
                client_override=False,
            )

        # 1. CMMI Maturity
        cmmi_raw = parse_strict_float(hc.get("cmmi_maturity")) or pillar_cmmi
        if not (1.0 <= cmmi_raw <= 5.0):
            cmmi_raw = max(1.0, min(5.0, cmmi_raw))

        cmmi_provenance = _build_provenance(
            p_name="cmmi_maturity",
            est_val=cmmi_raw,
            eff_val=cmmi_raw,
            unit="cmmi_index",
            default_source=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("cmmi_maturity") else ParameterSourceType.QUESTIONNAIRE,
            default_method="Pillar questionnaire evaluation",
            default_conf=ParameterConfidenceLevel.MEDIUM,
        )

        # 2. SPOF boolean
        is_spof = parse_strict_bool(hc.get("is_spof") or (str(hc.get("severity", "")).upper() == "CRITICAL"))
        spof_provenance = _build_provenance(
            p_name="is_spof",
            est_val=is_spof,
            eff_val=is_spof,
            unit="boolean",
            default_source=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("is_spof") is not None else ParameterSourceType.DERIVED,
            default_method="Severity and explicit architecture metadata",
            default_conf=ParameterConfidenceLevel.HIGH if hc.get("is_spof") is not None else ParameterConfidenceLevel.MEDIUM,
        )

        # 3. Threat Event Frequency (PERT)
        raw_tef = parse_strict_float(hc.get("threat_event_frequency"))
        is_explicit_tef = raw_tef is not None and 0.0 < raw_tef <= 10.0
        tef_mode = raw_tef if is_explicit_tef else 0.30

        raw_tef_min = parse_strict_float(hc.get("tef_pert_min"))
        tef_min = raw_tef_min if raw_tef_min is not None else (tef_mode * 0.45)
        raw_tef_max = parse_strict_float(hc.get("tef_pert_max"))
        tef_max = raw_tef_max if raw_tef_max is not None else (tef_mode * 2.20)

        # Enforce PERT min <= mode <= max strictly
        if not (tef_min <= tef_mode <= tef_max):
            tef_min = min(tef_min, tef_mode)
            tef_max = max(tef_max, tef_mode)

        tef_min_rec = _build_provenance(
            p_name="tef_pert_min",
            est_val=tef_min,
            eff_val=tef_min,
            unit="events/year",
            default_source=ParameterSourceType.DERIVED,
            default_method="PERT min from mode * 0.45",
            default_conf=ParameterConfidenceLevel.LOW,
        )
        tef_mode_rec = _build_provenance(
            p_name="tef_pert_mode",
            est_val=tef_mode,
            eff_val=tef_mode,
            unit="events/year",
            default_source=ParameterSourceType.ASSESSMENT_PAYLOAD if is_explicit_tef else ParameterSourceType.MODEL_DEFAULT,
            default_method="Ordinal frequency mapping" if is_explicit_tef else "Benchmark prior mode",
            default_conf=ParameterConfidenceLevel.MEDIUM if is_explicit_tef else ParameterConfidenceLevel.LOW,
        )
        tef_max_rec = _build_provenance(
            p_name="tef_pert_max",
            est_val=tef_max,
            eff_val=tef_max,
            unit="events/year",
            default_source=ParameterSourceType.DERIVED,
            default_method="PERT max from mode * 2.20",
            default_conf=ParameterConfidenceLevel.LOW,
        )

        # 4. Recovery Time Objective (RTO) PERT
        raw_rto = parse_strict_float(hc.get("recovery_time_hours") or hc.get("rto_hours_mode"))
        is_explicit_rto = raw_rto is not None and raw_rto > 0.0
        rto_mode = raw_rto if is_explicit_rto else 4.0

        raw_rto_min = parse_strict_float(hc.get("rto_hours_min"))
        rto_min = raw_rto_min if raw_rto_min is not None else (rto_mode * 0.45)
        raw_rto_max = parse_strict_float(hc.get("rto_hours_max"))
        rto_max = raw_rto_max if raw_rto_max is not None else (rto_mode * 2.50)

        if not (rto_min <= rto_mode <= rto_max):
            rto_min = min(rto_min, rto_mode)
            rto_max = max(rto_max, rto_mode)

        rto_min_rec = _build_provenance(
            p_name="rto_hours_min",
            est_val=rto_min,
            eff_val=rto_min,
            unit="hours",
            default_source=ParameterSourceType.DERIVED,
            default_method="PERT min from RTO mode * 0.45",
            default_conf=ParameterConfidenceLevel.LOW,
        )
        rto_mode_rec = _build_provenance(
            p_name="rto_hours_mode",
            est_val=rto_mode,
            eff_val=rto_mode,
            unit="hours",
            default_source=ParameterSourceType.ASSESSMENT_PAYLOAD if is_explicit_rto else ParameterSourceType.MODEL_DEFAULT,
            default_method="Explicit recovery time" if is_explicit_rto else "Benchmark prior mode",
            default_conf=ParameterConfidenceLevel.MEDIUM if is_explicit_rto else ParameterConfidenceLevel.LOW,
        )
        rto_max_rec = _build_provenance(
            p_name="rto_hours_max",
            est_val=rto_max,
            eff_val=rto_max,
            unit="hours",
            default_source=ParameterSourceType.DERIVED,
            default_method="PERT max from RTO mode * 2.50",
            default_conf=ParameterConfidenceLevel.LOW,
        )

        # 5. Secondary Loss Mean
        explicit_sec = parse_strict_float(hc.get("secondary_loss_mean"))
        raw_lm = parse_strict_float(hc.get("loss_magnitude")) or 2.5
        lm_factor = (raw_lm / 5.0) if (0.0 < raw_lm <= 5.0) else 0.50

        if explicit_sec is not None:
            sec_mean = explicit_sec
            sec_method = "Explicit client loss estimate"
            sec_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            sec_conf = ParameterConfidenceLevel.MEDIUM
        elif archetype == LossArchetypeType.REGULATORY_AND_BREACH:
            rev = annual_revenue or 100_000_000.0
            max_fine = max(20_000_000.0, rev * 0.04)
            sec_mean = max_fine * (0.01 + 0.03 * lm_factor) * 0.25
            sec_method = "Statutory fine exposure model (prior)"
            sec_source = ParameterSourceType.MODEL_DEFAULT
            sec_conf = ParameterConfidenceLevel.LOW
        elif archetype == LossArchetypeType.CAPITAL_INEFFICIENCY:
            opex = annual_it_opex or 5_000_000.0
            sec_mean = opex * (0.02 + 0.04 * lm_factor)
            sec_method = "IT OpEx capital drag model (prior)"
            sec_source = ParameterSourceType.MODEL_DEFAULT
            sec_conf = ParameterConfidenceLevel.LOW
        elif archetype == LossArchetypeType.PRODUCTIVITY_TOIL:
            wage = hourly_wage or 65.0
            sec_mean = wage * (20.0 + 30.0 * lm_factor)
            sec_method = "Burdened wage toil hours model (prior)"
            sec_source = ParameterSourceType.MODEL_DEFAULT
            sec_conf = ParameterConfidenceLevel.LOW
        else:
            sec_mean = zone.hourly_burn_rate * (1.5 + 2.0 * lm_factor)
            sec_method = "Outage disruption factor (prior)"
            sec_source = ParameterSourceType.MODEL_DEFAULT
            sec_conf = ParameterConfidenceLevel.LOW

        if is_spof and archetype == LossArchetypeType.AVAILABILITY_OUTAGE:
            sec_mean = max(sec_mean, zone.hourly_burn_rate * 2.65)

        sec_provenance = ParameterProvenanceRecord(
            estimated_value=round(sec_mean, 2),
            effective_value=round(sec_mean, 2),
            unit=currency_code,
            source_type=sec_source,
            estimation_method=sec_method,
            confidence=sec_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 6. Physical asset direct replacement cost
        repl_cost = parse_strict_float(hc.get("direct_replacement_cost")) or 0.0
        repl_provenance = ParameterProvenanceRecord(
            estimated_value=repl_cost,
            effective_value=repl_cost,
            unit=currency_code,
            source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("direct_replacement_cost") else ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Explicit replacement cost" if hc.get("direct_replacement_cost") else "Default zero physical cost",
            confidence=ParameterConfidenceLevel.MEDIUM if hc.get("direct_replacement_cost") else ParameterConfidenceLevel.LOW,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 7. Correlation & scope factors
        alpha_rad = parse_strict_float(hc.get("blast_radius_alpha")) or 0.60
        alpha_rad = max(0.05, min(1.0, alpha_rad))
        alpha_provenance = ParameterProvenanceRecord(
            estimated_value=alpha_rad,
            effective_value=alpha_rad,
            unit="ratio",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Operational scope factor",
            confidence=ParameterConfidenceLevel.LOW,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        rho_dep = parse_strict_float(hc.get("shared_dependence_factor")) or 0.30
        rho_dep = max(0.0, min(1.0, rho_dep))
        rho_provenance = ParameterProvenanceRecord(
            estimated_value=rho_dep,
            effective_value=rho_dep,
            unit="ratio",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Sector intra-tower baseline",
            confidence=ParameterConfidenceLevel.LOW,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 8. Audit evidence
        k_failures = int(hc.get("audit_k_failures") or 0)
        n_trials = int(hc.get("audit_n_trials") or 0)
        if k_failures > n_trials:
            n_trials = k_failures

        k_rec = ParameterProvenanceRecord(
            estimated_value=k_failures,
            effective_value=k_failures,
            unit="count",
            source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("audit_k_failures") else ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Audit identified control gaps",
            confidence=ParameterConfidenceLevel.HIGH if hc.get("audit_k_failures") else ParameterConfidenceLevel.LOW,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        n_rec = ParameterProvenanceRecord(
            estimated_value=n_trials,
            effective_value=n_trials,
            unit="count",
            source_type=ParameterSourceType.ASSESSMENT_PAYLOAD if hc.get("audit_n_trials") else ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Evaluated audit control count",
            confidence=ParameterConfidenceLevel.HIGH if hc.get("audit_n_trials") else ParameterConfidenceLevel.LOW,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 9. Operational zone records
        zone_id_rec = ParameterProvenanceRecord(
            estimated_value=zone.zone_id,
            effective_value=zone.zone_id,
            unit="zone_id",
            source_type=ParameterSourceType.DERIVED,
            estimation_method="Criticality mapping",
            confidence=ParameterConfidenceLevel.HIGH,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        burn_rec = ParameterProvenanceRecord(
            estimated_value=zone.hourly_burn_rate,
            effective_value=zone.hourly_burn_rate,
            unit=f"{currency_code}/hour",
            source_type=ParameterSourceType.DERIVED,
            estimation_method="Derived tier hourly burn rate",
            confidence=ParameterConfidenceLevel.MEDIUM,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        max_h_rec = ParameterProvenanceRecord(
            estimated_value=zone.max_annual_outage_hours,
            effective_value=zone.max_annual_outage_hours,
            unit="hours",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Zone SLA cap",
            confidence=ParameterConfidenceLevel.MEDIUM,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        ret_rec = ParameterProvenanceRecord(
            estimated_value=zone.secondary_loss_retention_factor,
            effective_value=zone.secondary_loss_retention_factor,
            unit="ratio",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Zone retention factor",
            confidence=ParameterConfidenceLevel.MEDIUM,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        ceil_rec = ParameterProvenanceRecord(
            estimated_value=zone.catastrophic_recovery_ceiling_hours,
            effective_value=zone.catastrophic_recovery_ceiling_hours,
            unit="hours",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Zone recovery ceiling",
            confidence=ParameterConfidenceLevel.MEDIUM,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        repl_ratio_rec = ParameterProvenanceRecord(
            estimated_value=zone.emergency_replacement_ratio,
            effective_value=zone.emergency_replacement_ratio,
            unit="ratio",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Emergency replacement ratio",
            confidence=ParameterConfidenceLevel.MEDIUM,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        cat_rto_rec = ParameterProvenanceRecord(
            estimated_value=zone.catastrophic_recovery_ceiling_hours,
            effective_value=zone.catastrophic_recovery_ceiling_hours,
            unit="hours",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Catastrophic RTO ceiling",
            confidence=ParameterConfidenceLevel.MEDIUM,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        diss_record = None
        dissonance_obj = None
        if hc.get("epistemic_dissonance"):
            d_dict = hc["epistemic_dissonance"]
            diss_record = DissonanceLineageRecord(
                record_id=str(d_dict.get("record_id") or f"DISS_{f_id}"),
                finding_id=f_id,
                claimed_maturity=float(d_dict.get("claimed_maturity") or cmmi_raw),
                empirical_reality_maturity=float(d_dict.get("empirical_reality_maturity") or cmmi_raw),
                dissonance_weight=float(d_dict.get("dissonance_weight") or 0.5),
                transcript_evidence_quote=str(d_dict.get("transcript_evidence_quote") or ""),
                impact_vector=str(d_dict.get("impact_vector") or "BOTH"),
            )
            dissonance_obj = EpistemicDissonanceRecord(
                record_id=diss_record.record_id,
                finding_id=f_id,
                claimed_maturity=diss_record.claimed_maturity,
                empirical_reality_maturity=diss_record.empirical_reality_maturity,
                dissonance_weight=diss_record.dissonance_weight,
                transcript_evidence_quote=diss_record.transcript_evidence_quote,
                impact_vector=diss_record.impact_vector,
            )

        inputs_obj = ActuarialFindingInputs(
            cmmi_maturity=cmmi_provenance,
            zone_id=zone_id_rec,
            hourly_burn_rate=burn_rec,
            max_annual_outage_hours=max_h_rec,
            secondary_loss_retention_factor=ret_rec,
            catastrophic_recovery_ceiling_hours=ceil_rec,
            emergency_replacement_ratio=repl_ratio_rec,
            tef_pert_min=tef_min_rec,
            tef_pert_mode=tef_mode_rec,
            tef_pert_max=tef_max_rec,
            rto_hours_min=rto_min_rec,
            rto_hours_mode=rto_mode_rec,
            rto_hours_max=rto_max_rec,
            secondary_loss_mean=sec_provenance,
            is_spof=spof_provenance,
            shared_dependence_factor=rho_provenance,
            blast_radius_alpha=alpha_provenance,
            catastrophic_rto_hours=cat_rto_rec,
            direct_replacement_cost=repl_provenance,
            audit_k_failures=k_rec,
            audit_n_trials=n_rec,
            dissonance_record=diss_record,
        )

        telemetry_obj = FindingTelemetry(
            finding_id=f_id,
            tower_id=tower_id,
            title=title,
            cmmi_maturity=float(inputs_obj.cmmi_maturity.effective_value),
            zone=zone,
            tef_pert_min=float(inputs_obj.tef_pert_min.effective_value),
            tef_pert_mode=float(inputs_obj.tef_pert_mode.effective_value),
            tef_pert_max=float(inputs_obj.tef_pert_max.effective_value),
            rto_hours_min=float(inputs_obj.rto_hours_min.effective_value),
            rto_hours_mode=float(inputs_obj.rto_hours_mode.effective_value),
            rto_hours_max=float(inputs_obj.rto_hours_max.effective_value),
            secondary_loss_mean=float(inputs_obj.secondary_loss_mean.effective_value),
            is_spof=bool(inputs_obj.is_spof.effective_value),
            shared_dependence_factor=float(inputs_obj.shared_dependence_factor.effective_value),
            blast_radius_alpha=float(inputs_obj.blast_radius_alpha.effective_value),
            catastrophic_rto_hours=zone.catastrophic_recovery_ceiling_hours,
            direct_replacement_cost=float(inputs_obj.direct_replacement_cost.effective_value),
            audit_k_failures=int(inputs_obj.audit_k_failures.effective_value),
            audit_n_trials=int(inputs_obj.audit_n_trials.effective_value),
            dissonance=dissonance_obj,
        )

        # Status determination (Phase 3 Rule 14)
        if is_explicit_tef and is_explicit_rto:
            status = QuantificationStatus.QUANTIFIED
        else:
            status = QuantificationStatus.ESTIMATED_LOW_CONFIDENCE

        return inputs_obj, telemetry_obj, status
