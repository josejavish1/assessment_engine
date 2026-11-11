"""Upstream Assessment Valuation and Presentation DTO Assembler Service (SR 11-7).

Executes canonical risk quantification, resolves custody boundaries, allocates portfolio
diversification benefits via Euler decomposition, and projects immutable PresentationPortfolioDTO
and PresentationTowerDTO instances for downstream compilers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from assessment_engine.application.dtos.presentation_dtos import (
    EpistemicState,
    ExecutiveFinancialBridgeDTO,
    OwnershipType,
    PresentationFindingDTO,
    PresentationPillarDTO,
    PresentationPortfolioDTO,
    PresentationTowerDTO,
)
from assessment_engine.application.services.canonical_risk_orchestrator import (
    CanonicalRiskOrchestrator,
)
from assessment_engine.domain.actuarial.euler_allocator import (
    EulerPortfolioAllocator,
)
from assessment_engine.domain.models.global_context import GlobalAssessmentContext

logger = logging.getLogger(__name__)


class AssessmentValuationOrchestrator:
    """Authoritative application orchestrator preparing read-only DTOs for compilers."""

    @classmethod
    def assemble_presentation_portfolio(
        cls,
        payloads_by_tower: Dict[str, Dict[str, Any]],
        global_context: Optional[GlobalAssessmentContext | Dict[str, Any]] = None,
        doc_lang: str = "en",
    ) -> Tuple[PresentationPortfolioDTO, Dict[str, Dict[str, Any]]]:
        """Quantifies assessment and projects immutable presentation read-models."""
        # 1. Execute single canonical risk quantification SSOT
        quantified_payloads, manifest = CanonicalRiskOrchestrator.quantify_payloads(
            payloads_by_tower=payloads_by_tower,
            global_context=global_context,
            persist_to_disk=False,
            doc_lang=doc_lang,
        )

        valid_ctx: Optional[GlobalAssessmentContext] = None
        if isinstance(global_context, GlobalAssessmentContext):
            valid_ctx = global_context
        elif isinstance(global_context, dict) and global_context:
            try:
                valid_ctx = GlobalAssessmentContext.model_validate(global_context)
            except Exception:
                valid_ctx = GlobalAssessmentContext.create_legacy_generic_context()
        else:
            valid_ctx = GlobalAssessmentContext.create_legacy_generic_context()

        currency_iso = valid_ctx.reporting_currency
        currency_sym = "€" if currency_iso == "EUR" else "$"
        tenant_id = valid_ctx.tenant_id

        # 2. Extract portfolio outputs from manifest or summary
        expected_portfolio = manifest.expected_portfolio_outputs if manifest else {}
        corp_ale = expected_portfolio.get("total_portfolio_ale")
        corp_p90 = expected_portfolio.get("portfolio_var_90")
        corp_max = expected_portfolio.get("portfolio_var_99")
        var_3y = corp_ale * 3.0 if corp_ale is not None else None
        var_3y_stress = corp_p90 * 1.5 if corp_p90 is not None else None

        # 3. Assemble PresentationTowerDTOs
        tower_dtos: List[PresentationTowerDTO] = []
        standalone_ales_for_euler: Dict[str, float] = {}

        for t_code, payload in quantified_payloads.items():
            t_name = str(payload.get("tower_name") or payload.get("domain_name") or f"Tower {t_code}")
            t_score = payload.get("score")
            t_band = str(payload.get("overall_band") or payload.get("band") or "UNASSESSED")
            status_color = "red" if (t_score is not None and t_score < 2.0) else "amber" if (t_score is not None and t_score < 3.5) else "green" if t_score is not None else "grey"

            s_ale = payload.get("standalone_fair_ale")
            s_p90 = payload.get("total_fair_p90")
            s_max = payload.get("total_fair_max")
            if s_ale is not None:
                standalone_ales_for_euler[t_code] = float(s_ale)

            # Assemble pillars and findings
            pillar_dtos: List[PresentationPillarDTO] = []
            tower_all_findings: List[PresentationFindingDTO] = []

            for pillar in payload.get("pillars_analysis", []):
                p_id = str(pillar.get("pilar_id") or pillar.get("pillar_id") or "UNKNOWN_PILLAR")
                p_name = str(pillar.get("name") or p_id)
                p_score = pillar.get("score")
                p_band = str(pillar.get("band") or "UNASSESSED")
                p_color = "red" if (p_score is not None and p_score < 2.0) else "amber" if (p_score is not None and p_score < 3.5) else "green" if p_score is not None else "grey"

                finding_dtos: List[PresentationFindingDTO] = []
                for hc in pillar.get("health_check_asis", []):
                    f_id = str(hc.get("node_id") or "UNKNOWN_FINDING")
                    cap = str(hc.get("capability") or f_id)
                    f_desc = str(hc.get("finding") or "")
                    r_desc = str(hc.get("business_risk") or "")

                    # Ownership & Custody
                    raw_owner = str(hc.get("ownership_type") or "PRIMARY_CUSTODIAN").upper()
                    owner_type = OwnershipType.TANGENTIAL_CONTRIBUTOR if raw_owner == "TANGENTIAL_CONTRIBUTOR" else OwnershipType.PRIMARY_CUSTODIAN
                    primary_ref = hc.get("primary_risk_ref")
                    contrib_towers = tuple(hc.get("contributing_towers") or ())

                    # Canonical metrics
                    vec = hc.get("actuarial_input_vector") or {}
                    vec_out = vec.get("outputs") or {}
                    vec_in = vec.get("inputs") or {}

                    f_ale = vec_out.get("portfolio_allocated_ale") or hc.get("fair_ale_score")
                    f_p90 = vec_out.get("var_90") or hc.get("fair_p90_score")
                    f_sle = vec_out.get("mean_sle")
                    f_lef = vec_out.get("mean_lef") or hc.get("threat_event_frequency")
                    f_tef = (vec_in.get("tef_pert_mode") or {}).get("effective_value")
                    f_rto = (vec_in.get("rto_hours_mode") or {}).get("effective_value") or hc.get("recovery_time_hours")

                    # Formatted display strings
                    ale_str = f"{f_ale:,.0f} {currency_sym}" if f_ale is not None else "UNQUANTIFIED"
                    p90_str = f"{f_p90:,.0f} {currency_sym}" if f_p90 is not None else "UNQUANTIFIED"
                    sle_str = f"{f_sle:,.0f} {currency_sym}" if f_sle is not None else "UNQUANTIFIED"
                    ret_str = f"{round(1.0 / max(0.0001, float(f_lef)), 1)} yrs" if (f_lef is not None and float(f_lef) > 0) else "N/A"

                    f_dto = PresentationFindingDTO(
                        finding_id=f_id,
                        node_id=f_id,
                        tower_id=t_code,
                        pillar_id=p_id,
                        pillar_name=p_name,
                        capability_name=cap,
                        finding_narrative=f_desc,
                        business_risk_narrative=r_desc,
                        ownership_type=owner_type,
                        primary_risk_ref=primary_ref,
                        contributing_towers=contrib_towers,
                        cmmi_score=hc.get("score"),
                        target_cmmi_score=hc.get("target_score"),
                        cmmi_band_label=str(hc.get("maturity_band") or "UNASSESSED"),
                        tef_annual=f_tef,
                        vulnerability_prob=vec_out.get("mean_vuln"),
                        lef_annual=f_lef,
                        sle_mean=f_sle,
                        ale_expected=f_ale,
                        p90_var=f_p90,
                        max_probable_loss=vec_out.get("var_99"),
                        rto_hours=f_rto,
                        risk_tier_label=str(hc.get("risk_tier") or "UNQUANTIFIED"),
                        ale_display=ale_str,
                        p90_display=p90_str,
                        sle_display=sle_str,
                        return_period_display=ret_str,
                    )
                    finding_dtos.append(f_dto)
                    tower_all_findings.append(f_dto)

                pillar_dtos.append(
                    PresentationPillarDTO(
                        pillar_id=p_id,
                        pillar_name=p_name,
                        cmmi_score=p_score,
                        cmmi_band_label=p_band,
                        status_color_token=p_color,
                        findings=tuple(finding_dtos),
                    )
                )

            epistemic_state = (
                EpistemicState.INSUFFICIENT_TELEMETRY
                if not tower_all_findings
                else EpistemicState.EMPIRICAL_OBSERVED
            )

            t_dto = PresentationTowerDTO(
                tower_id=t_code,
                tower_name=t_name,
                currency_iso=currency_iso,
                currency_symbol=currency_sym,
                locale=doc_lang,
                epistemic_state=epistemic_state,
                overall_cmmi_score=t_score,
                overall_cmmi_band=t_band,
                status_color_token=status_color,
                standalone_ale=s_ale,
                standalone_p90=s_p90,
                standalone_max_loss=s_max,
                euler_net_ale=payload.get("total_fair_ale"),
                pillars=tuple(pillar_dtos),
                all_findings=tuple(tower_all_findings),
            )
            tower_dtos.append(t_dto)

        # 4. Optional Euler Allocation decomposition
        if len(standalone_ales_for_euler) > 1 and corp_ale is not None:
            try:
                euler_results = EulerPortfolioAllocator.allocate_portfolio(
                    target_consolidated_ale=int(round(corp_ale)),
                    standalone_exposures={k: int(round(v)) for k, v in standalone_ales_for_euler.items()},
                )
                alloc_map = {r.tower_id: r for r in euler_results.allocations}
                updated_towers: List[PresentationTowerDTO] = []
                for t in tower_dtos:
                    if t.tower_id in alloc_map:
                        al = alloc_map[t.tower_id]
                        updated_towers.append(
                            t.model_copy(
                                update={
                                    "euler_net_ale": float(al.euler_net_contribution),
                                    "diversification_adjustment": float(al.diversification_adjustment),
                                    "portfolio_share_pct": float(al.portfolio_weight_pct),
                                }
                            )
                        )
                    else:
                        updated_towers.append(t)
                tower_dtos = updated_towers
            except Exception as e:
                logger.warning("Euler portfolio allocation warning: %s", e)

        # 5. Build Executive Financial Bridge DTO
        bridge_dto = ExecutiveFinancialBridgeDTO(
            epistemic_state=EpistemicState.EMPIRICAL_OBSERVED if corp_ale else EpistemicState.INSUFFICIENT_TELEMETRY,
            annual_revenue=valid_ctx.annual_revenue,
            hourly_downtime_cost=valid_ctx.authoritative_hourly_downtime_cost,
            annual_value_protected=corp_ale,
            three_year_value_protected=var_3y,
        )

        portfolio_dto = PresentationPortfolioDTO(
            tenant_id=tenant_id,
            currency_iso=currency_iso,
            currency_symbol=currency_sym,
            locale=doc_lang,
            corporate_ale=corp_ale,
            corporate_p90=corp_p90,
            corporate_max_loss=corp_max,
            var_3y_expected=var_3y,
            var_3y_stress=var_3y_stress,
            towers=tuple(tower_dtos),
            financial_bridge=bridge_dto,
        )

        return portfolio_dto, quantified_payloads
