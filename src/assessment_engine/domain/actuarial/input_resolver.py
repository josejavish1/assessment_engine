"""Actuarial Input Resolver and Evidence Grounding Service (SR 11-7).

Constructs fully-validated ActuarialFindingInputs and FindingTelemetry objects prior to Monte Carlo simulation.
Eliminates silent defaults, parses booleans strictly, enforces PERT and CMMI bounds, and tags quantification status.
"""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Any, Dict, Optional, Tuple

from assessment_engine.domain.actuarial.parameter_pack_loader import (
    ActuarialParameterPack,
    create_default_actuarial_parameter_pack,
)
from assessment_engine.domain.bayesian_fair_copula_engine import (
    EpistemicDissonanceRecord,
    FindingTelemetry,
    OperationalZone,
)
from assessment_engine.domain.models.global_context import GlobalAssessmentContext
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


def parse_strict_bool(val: Any, field_name: str = "boolean_field") -> bool:
    """Parses a boolean strictly, raising ValueError on invalid or unparseable inputs."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        if val in (0, 0.0):
            return False
        if val in (1, 1.0):
            return True
        raise ValueError(
            f"Numeric value {val} cannot be unambiguously parsed as bool for '{field_name}'"
        )
    if isinstance(val, str):
        clean = val.strip().lower()
        if clean in ("true", "1", "yes", "t", "y"):
            return True
        if clean in ("false", "0", "no", "f", "n"):
            return False
    raise ValueError(f"Invalid boolean value for '{field_name}': {val!r}")


def parse_strict_float(val: Any, field_name: str = "float_field") -> Optional[float]:
    """Parses a float, distinguishing None from 0.0, rejecting non-finite values."""
    if val is None:
        return None
    if isinstance(val, bool):
        raise ValueError(
            f"Boolean value {val!r} passed for numeric field '{field_name}'"
        )
    if isinstance(val, (int, float)):
        if not math.isfinite(val):
            raise ValueError(f"Non-finite numeric value {val!r} for '{field_name}'")
        return float(val)
    try:
        clean = str(val).replace(",", ".").strip()
        f = float(clean)
        if not math.isfinite(f):
            raise ValueError(f"Non-finite numeric string {val!r} for '{field_name}'")
        return f
    except (ValueError, TypeError) as err:
        raise ValueError(
            f"Could not parse float for '{field_name}' from {val!r}"
        ) from err


class ActuarialInputResolver:
    """Authoritative input resolver that binds inputs, parameter packs, and telemetry."""

    def __init__(self, parameter_pack: Optional[ActuarialParameterPack] = None) -> None:
        self.parameter_pack = (
            parameter_pack or create_default_actuarial_parameter_pack()
        )

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
        parameter_pack: Optional[ActuarialParameterPack] = None,
        context: Optional[GlobalAssessmentContext] = None,
    ) -> Tuple[ActuarialFindingInputs, FindingTelemetry, QuantificationStatus]:
        """Resolves raw finding dict into verified ActuarialFindingInputs and FindingTelemetry."""
        resolver = cls(parameter_pack=parameter_pack)
        pack = resolver.parameter_pack
        ctx = context or GlobalAssessmentContext.create_legacy_generic_context(
            currency=currency_code
        )

        f_id = str(hc.get("node_id") or "UNKNOWN_FINDING")
        title = str(hc.get("capability") or hc.get("title") or f"Finding {f_id}")

        corr_audit = hc.get("last_correction_audit") or {}
        corr_param = corr_audit.get("parameter_name")
        corr_orig = corr_audit.get("original_estimated_value")
        corr_src = corr_audit.get("source")
        corr_rev = corr_audit.get("review_identifier")

        # Tower defaults from parameter pack (or global fallbacks)
        tower_spec = pack.towers.get(tower_id)
        global_fb = pack.global_fallbacks

        material_parameters_explicit = True

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

        # 1. CMMI Maturity (Strict range [1.0, 5.0])
        cmmi_explicit = hc.get("cmmi_maturity")
        if cmmi_explicit is not None:
            cmmi_val = parse_strict_float(cmmi_explicit, "cmmi_maturity")
            if cmmi_val is None or not (1.0 <= cmmi_val <= 5.0):
                raise ValueError(
                    f"cmmi_maturity must be in [1.0, 5.0], got {cmmi_explicit}"
                )
            cmmi_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            cmmi_conf = ParameterConfidenceLevel.HIGH
        elif pillar_cmmi is not None and 1.0 <= pillar_cmmi <= 5.0:
            cmmi_val = float(pillar_cmmi)
            cmmi_source = ParameterSourceType.QUESTIONNAIRE
            cmmi_conf = ParameterConfidenceLevel.MEDIUM
        else:
            cmmi_val = float(global_fb.cmmi_maturity_level)
            cmmi_source = ParameterSourceType.MODEL_DEFAULT
            cmmi_conf = ParameterConfidenceLevel.LOW
            material_parameters_explicit = False

        cmmi_provenance = _build_provenance(
            p_name="cmmi_maturity",
            est_val=cmmi_val,
            eff_val=cmmi_val,
            unit="cmmi_index",
            default_source=cmmi_source,
            default_method="Pillar questionnaire evaluation"
            if cmmi_source == ParameterSourceType.QUESTIONNAIRE
            else "Benchmark default",
            default_conf=cmmi_conf,
        )

        # 2. SPOF boolean (Strict parsing)
        raw_spof = hc.get("is_spof")
        if raw_spof is not None:
            is_spof = parse_strict_bool(raw_spof, "is_spof")
            spof_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            spof_conf = ParameterConfidenceLevel.HIGH
        elif "severity" in hc:
            is_spof = str(hc.get("severity", "")).upper() == "CRITICAL"
            spof_source = ParameterSourceType.DERIVED
            spof_conf = ParameterConfidenceLevel.MEDIUM
        else:
            is_spof = False
            spof_source = ParameterSourceType.MODEL_DEFAULT
            spof_conf = ParameterConfidenceLevel.LOW

        spof_provenance = _build_provenance(
            p_name="is_spof",
            est_val=is_spof,
            eff_val=is_spof,
            unit="boolean",
            default_source=spof_source,
            default_method="Severity and explicit architecture metadata",
            default_conf=spof_conf,
        )

        # 3. Threat Event Frequency (PERT)
        raw_tef = hc.get("threat_event_frequency")
        if raw_tef is not None:
            parsed_tef = parse_strict_float(raw_tef, "threat_event_frequency")
            if parsed_tef is None or parsed_tef <= 0.0:
                raise ValueError(f"tef_annual must be strictly > 0.0, got {raw_tef}")
            tef_mode = parsed_tef
            tef_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            tef_conf = ParameterConfidenceLevel.HIGH
            is_explicit_tef = True
        else:
            default_base_tef = (
                tower_spec.default_tef_annual if tower_spec else global_fb.tef_annual
            )
            sev = str(hc.get("severity", "HIGH")).upper()
            mult = getattr(pack.severity_tef_multipliers, sev, 1.0)
            tef_mode = default_base_tef * mult
            tef_source = ParameterSourceType.MODEL_DEFAULT
            tef_conf = ParameterConfidenceLevel.LOW
            is_explicit_tef = False
            material_parameters_explicit = False

        raw_tef_min = hc.get("tef_pert_min")
        raw_tef_max = hc.get("tef_pert_max")
        if raw_tef_min is not None and raw_tef_max is not None:
            tef_min = parse_strict_float(raw_tef_min, "tef_pert_min")
            tef_max = parse_strict_float(raw_tef_max, "tef_pert_max")
            if tef_min is None or tef_max is None or tef_min <= 0.0 or tef_max <= 0.0:
                raise ValueError(
                    f"TEF PERT bounds must be > 0.0, got min={raw_tef_min}, max={raw_tef_max}"
                )
            if not (tef_min <= tef_mode <= tef_max):
                raise ValueError(
                    f"PERT ordering violated for TEF: min ({tef_min}) <= mode ({tef_mode}) <= max ({tef_max})"
                )
            tef_min_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            tef_max_source = ParameterSourceType.ASSESSMENT_PAYLOAD
        else:
            tef_min = tef_mode * pack.pert_dispersion.tef_min_ratio
            tef_max = tef_mode * pack.pert_dispersion.tef_max_ratio
            tef_min_source = ParameterSourceType.DERIVED
            tef_max_source = ParameterSourceType.DERIVED

        tef_min_rec = _build_provenance(
            p_name="tef_pert_min",
            est_val=tef_min,
            eff_val=tef_min,
            unit="events/year",
            default_source=tef_min_source,
            default_method="PERT min from mode dispersion",
            default_conf=tef_conf,
        )
        tef_mode_rec = _build_provenance(
            p_name="tef_pert_mode",
            est_val=tef_mode,
            eff_val=tef_mode,
            unit="events/year",
            default_source=tef_source,
            default_method="Ordinal frequency mapping"
            if is_explicit_tef
            else "Parameter pack prior mode",
            default_conf=tef_conf,
        )
        tef_max_rec = _build_provenance(
            p_name="tef_pert_max",
            est_val=tef_max,
            eff_val=tef_max,
            unit="events/year",
            default_source=tef_max_source,
            default_method="PERT max from mode dispersion",
            default_conf=tef_conf,
        )

        # 4. Recovery Time Objective (RTO) PERT
        raw_rto = (
            hc.get("recovery_time_hours")
            if hc.get("recovery_time_hours") is not None
            else hc.get("rto_hours_mode")
        )
        if raw_rto is not None:
            parsed_rto = parse_strict_float(raw_rto, "recovery_time_hours")
            if parsed_rto is None or parsed_rto <= 0.0:
                raise ValueError(f"rto_hours must be strictly > 0.0, got {raw_rto}")
            rto_mode = parsed_rto
            rto_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            rto_conf = ParameterConfidenceLevel.HIGH
            is_explicit_rto = True
        else:
            rto_mode = (
                tower_spec.default_rto_hours if tower_spec else global_fb.rto_hours
            )
            rto_source = ParameterSourceType.MODEL_DEFAULT
            rto_conf = ParameterConfidenceLevel.LOW
            is_explicit_rto = False
            material_parameters_explicit = False

        raw_rto_min = hc.get("rto_hours_min")
        raw_rto_max = hc.get("rto_hours_max")
        if raw_rto_min is not None and raw_rto_max is not None:
            rto_min = parse_strict_float(raw_rto_min, "rto_hours_min")
            rto_max = parse_strict_float(raw_rto_max, "rto_hours_max")
            if rto_min is None or rto_max is None or rto_min <= 0.0 or rto_max <= 0.0:
                raise ValueError(
                    f"RTO PERT bounds must be > 0.0, got min={raw_rto_min}, max={raw_rto_max}"
                )
            if not (rto_min <= rto_mode <= rto_max):
                raise ValueError(
                    f"PERT ordering violated for RTO: min ({rto_min}) <= mode ({rto_mode}) <= max ({rto_max})"
                )
            rto_min_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            rto_max_source = ParameterSourceType.ASSESSMENT_PAYLOAD
        else:
            rto_min = rto_mode * pack.pert_dispersion.rto_min_ratio
            rto_max = rto_mode * pack.pert_dispersion.rto_max_ratio
            rto_min_source = ParameterSourceType.DERIVED
            rto_max_source = ParameterSourceType.DERIVED

        rto_min_rec = _build_provenance(
            p_name="rto_hours_min",
            est_val=rto_min,
            eff_val=rto_min,
            unit="hours",
            default_source=rto_min_source,
            default_method="PERT min from RTO mode dispersion",
            default_conf=rto_conf,
        )
        rto_mode_rec = _build_provenance(
            p_name="rto_hours_mode",
            est_val=rto_mode,
            eff_val=rto_mode,
            unit="hours",
            default_source=rto_source,
            default_method="Explicit recovery time"
            if is_explicit_rto
            else "Parameter pack prior mode",
            default_conf=rto_conf,
        )
        rto_max_rec = _build_provenance(
            p_name="rto_hours_max",
            est_val=rto_max,
            eff_val=rto_max,
            unit="hours",
            default_source=rto_max_source,
            default_method="PERT max from RTO mode dispersion",
            default_conf=rto_conf,
        )

        # 5. Direct Replacement Cost (Strict non-negative, valid 0.0 preserved)
        raw_repl = hc.get("direct_replacement_cost")
        if raw_repl is not None:
            parsed_repl = parse_strict_float(raw_repl, "direct_replacement_cost")
            if parsed_repl is None or parsed_repl < 0.0:
                raise ValueError(
                    f"direct_replacement_cost cannot be negative, got {raw_repl}"
                )
            repl_raw_val = parsed_repl
            repl_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            repl_conf = ParameterConfidenceLevel.HIGH
        else:
            repl_raw_val = (
                tower_spec.default_direct_replacement_cost
                if tower_spec
                else global_fb.direct_replacement_cost
            )
            repl_source = ParameterSourceType.MODEL_DEFAULT
            repl_conf = ParameterConfidenceLevel.LOW
            material_parameters_explicit = False

        repl_cost, repl_rate, repl_snap = ctx.normalize_monetary_amount_with_provenance(
            repl_raw_val,
            source_curr=hc.get("currency")
            or (
                ctx.source_currency
                if repl_source == ParameterSourceType.ASSESSMENT_PAYLOAD
                else pack.base_currency
            ),
        )

        repl_provenance = ParameterProvenanceRecord(
            estimated_value=repl_cost,
            effective_value=repl_cost,
            unit=ctx.reporting_currency,
            source_type=repl_source,
            estimation_method="Explicit replacement cost"
            if repl_source == ParameterSourceType.ASSESSMENT_PAYLOAD
            else "Parameter pack default",
            confidence=repl_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 6. Secondary Loss Mean (Strict non-negative, normalized FX)
        raw_sec = hc.get("secondary_loss_mean")
        if raw_sec is not None:
            parsed_sec = parse_strict_float(raw_sec, "secondary_loss_mean")
            if parsed_sec is None or parsed_sec < 0.0:
                raise ValueError(
                    f"secondary_loss_mean cannot be negative, got {raw_sec}"
                )
            sec_raw_val = parsed_sec
            sec_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            sec_conf = ParameterConfidenceLevel.HIGH
            sec_method = "Explicit secondary loss estimate"
        else:
            raw_lm = parse_strict_float(hc.get("loss_magnitude")) or 2.5
            lm_factor = (raw_lm / 5.0) if (0.0 < raw_lm <= 5.0) else 0.50
            if archetype == LossArchetypeType.REGULATORY_AND_BREACH:
                rev = annual_revenue or global_fb.annual_revenue_default
                max_fine = max(
                    global_fb.statutory_max_fine_ceiling,
                    rev * global_fb.statutory_max_fine_revenue_pct,
                )
                sec_raw_val = max_fine * (0.005 + 0.015 * lm_factor) * 0.05
                sec_method = "Statutory fine exposure model (prior)"
            elif archetype == LossArchetypeType.CAPITAL_INEFFICIENCY:
                opex = annual_it_opex or global_fb.annual_it_opex_default
                sec_raw_val = opex * (0.005 + 0.010 * lm_factor) * 0.25
                sec_method = "IT OpEx capital drag model (prior)"
            elif archetype == LossArchetypeType.PRODUCTIVITY_TOIL:
                wage = hourly_wage or global_fb.hourly_wage_default
                sec_raw_val = wage * (10.0 + 15.0 * lm_factor)
                sec_method = "Burdened wage toil hours model (prior)"
            else:
                sec_raw_val = zone.hourly_burn_rate * (0.5 + 1.0 * lm_factor)
                sec_method = "Outage disruption factor (prior)"
            sec_source = ParameterSourceType.MODEL_DEFAULT
            sec_conf = ParameterConfidenceLevel.LOW
            if is_spof and archetype == LossArchetypeType.AVAILABILITY_OUTAGE:
                sec_raw_val = max(sec_raw_val, zone.hourly_burn_rate * 2.65)

        sec_mean, _, _ = ctx.normalize_monetary_amount_with_provenance(
            sec_raw_val,
            source_curr=hc.get("currency")
            or (
                ctx.source_currency
                if sec_source == ParameterSourceType.ASSESSMENT_PAYLOAD
                else pack.base_currency
            ),
        )

        sec_provenance = ParameterProvenanceRecord(
            estimated_value=round(sec_mean, 2),
            effective_value=round(sec_mean, 2),
            unit=ctx.reporting_currency,
            source_type=sec_source,
            estimation_method=sec_method,
            confidence=sec_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 7. Correlation & scope factors (Strict range [0.0, 1.0], preserving 0.0)
        raw_alpha = hc.get("blast_radius_alpha")
        if raw_alpha is not None:
            parsed_alpha = parse_strict_float(raw_alpha, "blast_radius_alpha")
            if parsed_alpha is None or not (0.0 <= parsed_alpha <= 1.0):
                raise ValueError(
                    f"blast_radius_alpha must be in [0.0, 1.0], got {raw_alpha}"
                )
            alpha_rad = parsed_alpha
            alpha_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            alpha_conf = ParameterConfidenceLevel.HIGH
        else:
            alpha_rad = (
                tower_spec.default_control_effectiveness_alpha
                if tower_spec
                else global_fb.control_effectiveness_alpha
            )
            alpha_source = ParameterSourceType.MODEL_DEFAULT
            alpha_conf = ParameterConfidenceLevel.LOW

        alpha_provenance = ParameterProvenanceRecord(
            estimated_value=alpha_rad,
            effective_value=alpha_rad,
            unit="ratio",
            source_type=alpha_source,
            estimation_method="Explicit blast radius alpha"
            if alpha_source == ParameterSourceType.ASSESSMENT_PAYLOAD
            else "Parameter pack baseline",
            confidence=alpha_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        raw_rho = hc.get("shared_dependence_factor")
        if raw_rho is not None:
            parsed_rho = parse_strict_float(raw_rho, "shared_dependence_factor")
            if parsed_rho is None or not (0.0 <= parsed_rho < 1.0):
                raise ValueError(
                    f"shared_dependence_factor must be in [0.0, 1.0), got {raw_rho}"
                )
            rho_dep = parsed_rho
            rho_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            rho_conf = ParameterConfidenceLevel.HIGH
        else:
            rho_dep = (
                tower_spec.default_intra_domain_correlation_rho
                if tower_spec
                else global_fb.intra_domain_correlation_rho
            )
            rho_source = ParameterSourceType.MODEL_DEFAULT
            rho_conf = ParameterConfidenceLevel.LOW

        rho_provenance = ParameterProvenanceRecord(
            estimated_value=rho_dep,
            effective_value=rho_dep,
            unit="ratio",
            source_type=rho_source,
            estimation_method="Explicit shared dependence factor"
            if rho_source == ParameterSourceType.ASSESSMENT_PAYLOAD
            else "Parameter pack baseline",
            confidence=rho_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )

        # 8. Audit evidence (Strict counts without silent modifications)
        raw_k = hc.get("audit_k_failures")
        raw_n = hc.get("audit_n_trials")
        if raw_k is not None or raw_n is not None:
            if raw_k is None or raw_n is None:
                raise ValueError(
                    "audit_k_failures and audit_n_trials must both be provided if one is present"
                )
            if isinstance(raw_k, bool) or isinstance(raw_n, bool):
                raise ValueError(
                    "audit_k_failures and audit_n_trials must be integers, not booleans"
                )
            try:
                k_failures = int(raw_k)
                n_trials = int(raw_n)
            except (ValueError, TypeError) as err:
                raise ValueError(
                    f"audit counts must be valid integers: k={raw_k}, n={raw_n}"
                ) from err

            if k_failures < 0 or n_trials <= 0:
                raise ValueError(
                    f"Invalid audit counts: k={k_failures} (must be >=0), n={n_trials} (must be >0)"
                )
            if k_failures > n_trials:
                raise ValueError(
                    f"audit_k_failures ({k_failures}) cannot exceed audit_n_trials ({n_trials})"
                )
            k_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            n_source = ParameterSourceType.ASSESSMENT_PAYLOAD
            audit_conf = ParameterConfidenceLevel.HIGH
        else:
            k_failures = 0
            n_trials = 0
            k_source = ParameterSourceType.MODEL_DEFAULT
            n_source = ParameterSourceType.MODEL_DEFAULT
            audit_conf = ParameterConfidenceLevel.LOW

        k_rec = ParameterProvenanceRecord(
            estimated_value=k_failures,
            effective_value=k_failures,
            unit="count",
            source_type=k_source,
            estimation_method="Audit control gap observations",
            confidence=audit_conf,
            validation_status=ParameterValidationStatus.UNCONFIRMED,
        )
        n_rec = ParameterProvenanceRecord(
            estimated_value=n_trials,
            effective_value=n_trials,
            unit="count",
            source_type=n_source,
            estimation_method="Audit evaluated control trials",
            confidence=audit_conf,
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
            unit=f"{ctx.reporting_currency}/hour",
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
                claimed_maturity=float(d_dict.get("claimed_maturity") or cmmi_val),
                empirical_reality_maturity=float(
                    d_dict.get("empirical_reality_maturity") or cmmi_val
                ),
                dissonance_weight=float(d_dict.get("dissonance_weight") or 0.5),
                transcript_evidence_quote=str(
                    d_dict.get("transcript_evidence_quote") or ""
                ),
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
            shared_dependence_factor=float(
                inputs_obj.shared_dependence_factor.effective_value
            ),
            blast_radius_alpha=float(inputs_obj.blast_radius_alpha.effective_value),
            catastrophic_rto_hours=zone.catastrophic_recovery_ceiling_hours,
            direct_replacement_cost=float(
                inputs_obj.direct_replacement_cost.effective_value
            ),
            audit_k_failures=int(inputs_obj.audit_k_failures.effective_value),
            audit_n_trials=int(inputs_obj.audit_n_trials.effective_value),
            dissonance=dissonance_obj,
        )

        # Status determination (Evidence Matrix)
        # If any material parameter fell back to parameter pack -> ESTIMATED_LOW_CONFIDENCE
        if is_explicit_tef and is_explicit_rto and material_parameters_explicit:
            status = QuantificationStatus.QUANTIFIED
        else:
            status = QuantificationStatus.ESTIMATED_LOW_CONFIDENCE

        return inputs_obj, telemetry_obj, status
