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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from assessment_engine.domain.actuarial.input_resolver import (
    ActuarialInputResolver,
    QuantificationStatus,
)
from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
    PortfolioReproductionManifest,
    PortfolioRiskSummary,
    create_reproduction_manifest,
)
from assessment_engine.domain.models.parameter_lineage import (
    ActuarialFindingOutputs,
    ActuarialInputVector,
)
from assessment_engine.domain.taxonomy.archetype_registry import (
    get_actuarial_archetype_registry,
)

logger = logging.getLogger(__name__)


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
        global_context: Optional[Any] = None,
        persist_to_disk: bool = False,
        client_id: Optional[str] = None,
        doc_lang: str = "en",
    ) -> Tuple[Dict[str, Dict[str, Any]], Optional[PortfolioReproductionManifest]]:
        """Executes canonical Bayesian FAIR Copula quantification across any number of towers (1 to N)."""
        from assessment_engine.domain.models.global_context import (
            VALID_ISO_CURRENCIES,
            GlobalAssessmentContext,
        )

        valid_ctx: Optional[GlobalAssessmentContext] = None
        if isinstance(global_context, GlobalAssessmentContext):
            valid_ctx = global_context
        elif isinstance(global_context, dict) and global_context:
            try:
                valid_ctx = GlobalAssessmentContext.model_validate(global_context)
            except Exception:
                fin_tel = global_context.get("financial_telemetry") or {}
                raw_c = (
                    str(
                        fin_tel.get("currency")
                        or fin_tel.get("currency_code")
                        or global_context.get("currency")
                        or "EUR"
                    )
                    .strip()
                    .upper()
                )
                if raw_c not in VALID_ISO_CURRENCIES:
                    valid_ctx = None
                else:
                    valid_ctx = GlobalAssessmentContext.create_legacy_generic_context(
                        tenant_id=str(
                            global_context.get("tenant_id") or "DEFAULT_TENANT"
                        ),
                        business_entity_id=str(
                            global_context.get("business_entity_id") or "DEFAULT_ENTITY"
                        ),
                        operating_site_id=str(
                            global_context.get("operating_site_id") or "DEFAULT_SITE"
                        ),
                        currency=raw_c,
                        annual_revenue=_safe_float(fin_tel.get("annual_revenue")),
                        hourly_downtime_cost=_safe_float(
                            fin_tel.get("authoritative_hourly_downtime_cost")
                        ),
                    )
        else:
            valid_ctx = GlobalAssessmentContext.create_legacy_generic_context()

        if valid_ctx is None:
            # Mark unsupported context and abort simulation safely
            for payload in payloads_by_tower.values():
                payload["quantification_status"] = (
                    QuantificationStatus.UNSUPPORTED_CONTEXT.value
                )
                payload["total_fair_ale"] = None
                payload["total_fair_p90"] = None
                payload["total_fair_cvar_90"] = None
                for p in payload.get("pillars_analysis", []):
                    for f in p.get("health_check_asis", []):
                        f["quantification_status"] = (
                            QuantificationStatus.UNSUPPORTED_CONTEXT.value
                        )
                        f["fair_ale_score"] = None
                        f["fair_p90_score"] = None
            return payloads_by_tower, None

        eval_currency = valid_ctx.reporting_currency

        from assessment_engine.infrastructure.parameter_pack_loader import (
            load_actuarial_parameter_pack,
            load_kernel_calibration_pack,
        )

        pack = load_actuarial_parameter_pack()
        cal = load_kernel_calibration_pack()

        actuarial_cfg = {}
        if isinstance(global_context, dict):
            actuarial_cfg = (global_context.get("financial_telemetry") or {}).get(
                "actuarial_calibration"
            ) or {}
        num_sims = int(
            actuarial_cfg.get("simulation_iterations")
            or pack.global_fallbacks.simulation_iterations
        )
        copula_df = int(actuarial_cfg.get("copula_df") or cal.copula_df)

        base_burn_rate = (
            valid_ctx.authoritative_hourly_downtime_cost
            or pack.global_fallbacks.hourly_downtime_cost
        )

        zone_configs = {
            z_id: {
                "burn_mult": z_spec.burn_multiplier,
                "h_max": z_spec.max_annual_outage_hours,
                "retention": z_spec.secondary_loss_retention_factor,
                "ceil_hours": z_spec.catastrophic_recovery_ceiling_hours,
                "repl_ratio": z_spec.emergency_replacement_ratio,
            }
            for z_id, z_spec in pack.operational_zones.items()
        }

        all_telemetry: List[FindingTelemetry] = []
        telemetry_meta: Dict[
            Tuple[str, str], Tuple[FindingTelemetry, Dict[str, Any], Dict[str, Any]]
        ] = {}

        registry = get_actuarial_archetype_registry()

        for t_code, payload in payloads_by_tower.items():
            t_mapping = registry.get_mapping_for_tower(t_code)
            if not t_mapping.quantifiable:
                payload["quantification_status"] = (
                    QuantificationStatus.NOT_QUANTIFIED.value
                )
                payload["total_fair_ale"] = None
                payload["total_fair_p90"] = None
                payload["total_fair_cvar_90"] = None
                for p in payload.get("pillars_analysis", []):
                    for f in p.get("health_check_asis", []):
                        f["quantification_status"] = (
                            QuantificationStatus.NOT_QUANTIFIED.value
                        )
                        f["fair_ale_score"] = None
                        f["fair_p90_score"] = None
                        f["fair_cvar_score"] = None
                continue

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
                tenant_id=valid_ctx.tenant_id,
                legal_entity_id=valid_ctx.business_entity_id,
                operating_site_id=valid_ctx.operating_site_id,
            )

            pillars = payload.get("pillars_analysis") or []
            finding_seq = 0

            for pillar in pillars:
                if not isinstance(pillar, dict):
                    continue
                cmmi_raw = (
                    _safe_float(
                        pillar.get("score") or pillar.get("maturity_score"), default=2.5
                    )
                    or 2.5
                )
                cmmi_pillar = max(1.0, min(5.0, cmmi_raw))

                findings = (
                    pillar.get("health_check_asis") or pillar.get("findings") or []
                )
                for hc in findings:
                    if not isinstance(hc, dict):
                        continue

                    finding_seq += 1
                    f_id = str(hc.get("node_id") or f"{t_code}_F{finding_seq:03d}")
                    hc["node_id"] = f_id

                    inputs_obj, ft, f_status = (
                        ActuarialInputResolver.resolve_finding_inputs(
                            hc=hc,
                            tower_id=t_code,
                            pillar_cmmi=cmmi_pillar,
                            zone=zone,
                            archetype=t_arch,
                            currency_code=eval_currency,
                            annual_revenue=valid_ctx.annual_revenue,
                            annual_it_opex=valid_ctx.annual_it_opex,
                            hourly_wage=valid_ctx.fully_burdened_hourly_rate,
                            parameter_pack=pack,
                            context=valid_ctx,
                        )
                    )
                    all_telemetry.append(ft)
                    telemetry_meta[(t_code, f_id)] = (ft, hc, inputs_obj, f_status)

        if not all_telemetry:
            for payload in payloads_by_tower.values():
                if (
                    payload.get("quantification_status")
                    != QuantificationStatus.NOT_QUANTIFIED.value
                ):
                    payload["quantification_status"] = (
                        QuantificationStatus.INSUFFICIENT_EVIDENCE.value
                    )
                payload["total_fair_ale"] = None
                payload["total_fair_p90"] = None
                payload["total_fair_cvar_90"] = None
                for p in payload.get("pillars_analysis", []):
                    for f in p.get("health_check_asis", []):
                        if (
                            f.get("quantification_status")
                            != QuantificationStatus.NOT_QUANTIFIED.value
                        ):
                            f["quantification_status"] = (
                                QuantificationStatus.INSUFFICIENT_EVIDENCE.value
                            )
                        f["fair_ale_score"] = None
                        f["fair_p90_score"] = None
                        f["fair_cvar_score"] = None
            return payloads_by_tower, None

        # 2. Run BayesianFairCopulaEngine as sole production SSOT
        engine = BayesianFairCopulaEngine(
            calibration_pack=cal,
            num_simulations=num_sims,
            copula_df=copula_df,
        )
        summary: PortfolioRiskSummary = engine.evaluate_portfolio(
            all_telemetry, currency_code=eval_currency
        )

        # 3. Build reproduction manifest with explicit risk scope
        from assessment_engine.domain.bayesian_fair_copula_engine import (
            RiskScopeContext,
        )

        risk_scope = RiskScopeContext(
            tenant_id=valid_ctx.tenant_id,
            legal_entity_id=valid_ctx.business_entity_id,
            operating_site_id=valid_ctx.operating_site_id,
            country_code=valid_ctx.country_code,
            jurisdiction_code=valid_ctx.jurisdiction_code,
            source_currency_code=valid_ctx.source_currency,
            reporting_currency_code=valid_ctx.reporting_currency,
            sector_code=valid_ctx.sector_code,
            subsector_code=valid_ctx.subsector_code,
        )
        manifest = create_reproduction_manifest(
            engine=engine,
            findings=all_telemetry,
            summary=summary,
            currency_code=eval_currency,
            risk_scope=risk_scope,
            assessment_period=valid_ctx.assessment_period,
            parameter_pack_sha256=pack.pack_sha256,
            kernel_calibration_sha256=cal.calibration_sha256,
            context_sha256=valid_ctx.compute_context_sha256(),
        )

        # 4. Populate canonical outputs into payloads
        for t_code, payload in payloads_by_tower.items():
            if t_code not in summary.towers:
                continue
            t_res = summary.towers[t_code]
            finding_results = {f.finding_id: f for f in t_res.findings}
            tower_has_low_conf = False

            for pillar in payload.get("pillars_analysis", []):
                if not isinstance(pillar, dict):
                    continue
                for hc in pillar.get("health_check_asis", []):
                    if not isinstance(hc, dict):
                        continue
                    f_id = hc.get("node_id")
                    if f_id in finding_results:
                        f_res = finding_results[f_id]
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
                            ft_obj, _, resolved_inputs, f_status = meta_tuple
                            hc["quantification_status"] = f_status.value
                            if (
                                f_status
                                == QuantificationStatus.ESTIMATED_LOW_CONFIDENCE
                            ):
                                tower_has_low_conf = True

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
                                inputs=resolved_inputs,
                                outputs=outputs_obj,
                            )
                            hc["actuarial_input_vector"] = input_vector.model_dump(
                                mode="json"
                            )

            # Compute closed-form AdditiveLossDecomposition per finding within this tower
            from assessment_engine.domain.actuarial.euler_allocator import (
                EulerPortfolioAllocator,
            )

            tower_findings_for_decomp: list[dict[str, Any]] = []
            for pillar in payload.get("pillars_analysis", []):
                if not isinstance(pillar, dict):
                    continue
                for hc in pillar.get("health_check_asis", []):
                    if not isinstance(hc, dict):
                        continue
                    f_id = hc.get("node_id")
                    if f_id in finding_results:
                        f_res = finding_results[f_id]
                        tower_findings_for_decomp.append(
                            {
                                "id": f_id,
                                "node_id": f_id,
                                "mean_lef": f_res.mean_lef,
                                "gross_mean_sle": f_res.mean_sle,
                                "gross_standalone_ale": f_res.standalone_ale,
                                "gross_p90": f_res.var_90,
                                "loss_physics": hc.get("loss_physics")
                                or "AVAILABILITY_OUTAGE",
                                "epistemic_state": hc.get("epistemic_state")
                                or "VERIFIED_EMPIRICAL",
                            }
                        )

            tower_decomps = EulerPortfolioAllocator.allocate_findings_within_domain(
                tower_findings_for_decomp, currency_iso=eval_currency
            )
            for pillar in payload.get("pillars_analysis", []):
                if not isinstance(pillar, dict):
                    continue
                for hc in pillar.get("health_check_asis", []):
                    if not isinstance(hc, dict):
                        continue
                    f_id = hc.get("node_id")
                    if f_id in tower_decomps:
                        hc["additive_loss_decomposition"] = tower_decomps[
                            f_id
                        ].to_dict()

            payload["quantification_status"] = (
                QuantificationStatus.ESTIMATED_LOW_CONFIDENCE.value
                if tower_has_low_conf
                else QuantificationStatus.QUANTIFIED.value
            )
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

            if persist_to_disk:
                if not client_id or not str(client_id).strip():
                    raise ValueError(
                        "Multi-Tenant Governance Violation: client_id is mandatory when persist_to_disk is True. "
                        "Silent fallback to 'molins' is strictly prohibited."
                    )
                client_norm = str(client_id).strip()
                code_lower = t_code.lower()
                repo_root = Path(__file__).resolve().parents[4]
                local_dir = repo_root / "working" / client_norm / t_code
                local_path = local_dir / f"blueprint_{code_lower}_payload.json"
                if local_path.exists():
                    try:
                        with open(local_path, "w", encoding="utf-8") as pf:
                            json.dump(payload, pf, indent=2, ensure_ascii=False)
                    except Exception as p_err:
                        logger.error(
                            "Could not persist payload for tower %s: %s", t_code, p_err
                        )
                        raise p_err

                try:
                    from assessment_engine.application.tools.actuarial_ledger_generator import (
                        generate_actuarial_ledger,
                    )

                    generate_actuarial_ledger(t_code, payload)
                except Exception as ledger_err:
                    logger.error(
                        "Could not flush actuarial ledger for tower %s: %s",
                        t_code,
                        ledger_err,
                    )
                    raise ledger_err

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
