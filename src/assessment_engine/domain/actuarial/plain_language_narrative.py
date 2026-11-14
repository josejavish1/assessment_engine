"""Plain-Language Technical and Operational Narrative Formatter.

Transforms technical risk findings into intuitive business narratives:
1. Operational Impact: What concrete business capability or production process is interrupted.
2. Economic Justification: Defensible derivation of single loss event impact and annualized risk.

Strictly 100% Technical English in implementation, fully decoupled from concrete locales.
All language templates reside declaratively in localization catalogs.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional


_DEFAULT_ENGLISH_COST_TEMPLATES: Mapping[str, str] = {
    "narrative_header_operational_impact": "• Operational Impact:",
    "narrative_header_economic_cost": "• Economic Cost Justification:",
    "narrative_cost_just_outage_major": "In an unexpected contingency affecting primary infrastructure, service restoration requires {rto_hours} hours of technical triage, incurring an event impact of {sle_formatted}. Given an estimated frequency of {freq_str}, annualized exposure is {ale_formatted}/year.",
    "narrative_cost_just_outage_minor": "In an unexpected contingency, an operational downtime of {rto_hours} hours is estimated with an event impact of {sle_formatted}. Given an estimated recurrence of {freq_str}, annualized exposure is {ale_formatted}/year.",
    "narrative_cost_just_finops_and_obsolescence": "An annual economic inefficiency of {ale_formatted}/year is estimated from idle capacity and avoidable commitments.",
    "narrative_cost_just_engineering_velocity": "During service requests or maintenance windows, financial impact materializes as lost engineering hours ({sle_formatted} per event). Given a recurrence of {freq_str}, annualized net exposure is {ale_formatted}/year.",
    "narrative_cost_just_compliance_and_governance": "Financial exposure reflects remediation equipment, technical triage, and compliance governance ({sle_formatted} per event). Given an estimated frequency of {freq_str}, annualized net exposure is {ale_formatted}/year.",
}


class PlainLanguageRiskNarrative:
    """Formats enterprise risk cards into an intuitive, plain-language business narrative."""

    @classmethod
    def format_plain_narrative(
        cls,
        tower_code: str,
        kpi_name: str,
        failure_desc: str,
        industry: str,
        sle: float,
        ale: float,
        rto_hours: float,
        hourly_rate: float,
        doc_lang: str = "en",
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Constructs an intuitive plain-language business impact narrative."""
        normalized_tower = tower_code.strip().upper()
        norm_ind = industry.strip().lower()
        if "health" in norm_ind or "sanid" in norm_ind or "hospit" in norm_ind:
            ind_key = "healthcare"
        elif "bank" in norm_ind or "banc" in norm_ind or "financ" in norm_ind:
            ind_key = "banking"
        elif "retail" in norm_ind or "comerc" in norm_ind or "tiend" in norm_ind:
            ind_key = "retail"
        else:
            ind_key = "manufacturing"

        translator = kwargs.get("translator") or kwargs.get("localizer")
        if not callable(translator):
            def translator(key: str, **params: Any) -> str:
                tmpl = _DEFAULT_ENGLISH_COST_TEMPLATES.get(key, str(params.get("default") or key))
                try:
                    return tmpl.format(**params)
                except Exception:
                    return tmpl

        loss_physics = kwargs.get("loss_physics")
        authentic_business_risk = kwargs.get("authentic_business_risk")
        lef = kwargs.get("lef")

        eff_lef = float(lef) if lef is not None and float(lef) > 0 else (ale / sle if ale > 0 and sle > 0 else 0.0)

        is_spanish = str(doc_lang).lower().startswith("es")
        if eff_lef > 0:
            if eff_lef >= 1.0:
                ev_str = f"{eff_lef:.2f}".replace(".", ",") if is_spanish else f"{eff_lef:.2f}"
                freq_str = translator(
                    "narrative_freq_times_per_year",
                    locale=doc_lang,
                    freq=ev_str,
                    default=f"unas {ev_str} veces al año" if is_spanish else f"approximately {ev_str} times per year",
                )
            else:
                years_between = round(1.0 / eff_lef, 1)
                yr_str = f"{years_between:.1f}".replace(".", ",") if is_spanish else f"{years_between:.1f}"
                freq_str = translator(
                    "narrative_freq_years_between",
                    locale=doc_lang,
                    years=yr_str,
                    default=f"aproximadamente 1 vez cada {yr_str} años" if is_spanish else f"approximately once every {yr_str} years",
                )
        else:
            freq_str = translator(
                "narrative_freq_continuous",
                locale=doc_lang,
                default="de forma continua en cada ejercicio presupuestario" if is_spanish else "continuously across each budget cycle",
            )

        currency_fmt = kwargs.get("currency_formatter")
        if callable(currency_fmt):
            ale_fmt = currency_fmt(ale, doc_lang)
            sle_fmt = currency_fmt(sle, doc_lang)
        else:
            sign_a = "-" if ale < 0 else ""
            sign_s = "-" if sle < 0 else ""
            sa = f"{round(abs(ale)):,}".replace(",", ".") if is_spanish else f"{round(abs(ale)):,}"
            ss = f"{round(abs(sle)):,}".replace(",", ".") if is_spanish else f"{round(abs(sle)):,}"
            ale_fmt = f"{sign_a}{sa} €" if is_spanish else f"{sign_a}€{sa}"
            sle_fmt = f"{sign_s}{ss} €" if is_spanish else f"{sign_s}€{ss}"

        rto_str = f"{max(0.5, rto_hours):.1f}".replace(".", ",") if is_spanish else f"{max(0.5, rto_hours):.1f}"
        rto_formatted = f"{rto_hours:.1f}".replace(".", ",") if is_spanish else f"{rto_hours:.1f}"

        norm_physics = str(getattr(loss_physics, "value", loss_physics) or "").upper()

        # Operational Impact
        if authentic_business_risk:
            op_text = authentic_business_risk
        elif norm_physics in ("FINOPS_RESOURCE_WASTE", "ASSET_OBSOLESCENCE_AND_INTEGRITY") or (sle <= 0 and rto_hours <= 0):
            op_text = translator("narrative_op_impact_finops_and_obsolescence", locale=doc_lang)
        elif norm_physics == "ENGINEERING_VELOCITY_FRICTION":
            op_text = translator("narrative_op_impact_engineering_velocity", locale=doc_lang)
        elif norm_physics == "REGULATORY_AND_BREACH" or rto_hours <= 0.0:
            op_text = translator("narrative_op_impact_compliance_and_governance", locale=doc_lang)
        else:
            # Resolve declarative industry disruption template from catalog
            ind_template = translator(f"industry_disruptions_{ind_key}_{normalized_tower}", locale=doc_lang)
            if not ind_template or ind_template.startswith("industry_disruptions_"):
                ind_template = translator(f"industry_disruptions_{ind_key}_default", locale=doc_lang)
            if ind_template and not ind_template.startswith("industry_disruptions_"):
                try:
                    op_text = ind_template.format(rto_h=max(0.5, rto_hours))
                except Exception:
                    op_text = ind_template
            else:
                # Closed-world analytical formulation: dynamically ground on the evaluated capability, sector, and finding
                clean_desc = str(failure_desc or "").strip().rstrip(".")
                if ind_key == "healthcare":
                    op_text = translator(
                        "narrative_op_risk_healthcare",
                        locale=doc_lang,
                        kpi_name=kpi_name,
                        clean_desc=clean_desc,
                    )
                elif ind_key == "banking":
                    op_text = translator(
                        "narrative_op_risk_banking",
                        locale=doc_lang,
                        kpi_name=kpi_name,
                        clean_desc=clean_desc,
                    )
                else:
                    if clean_desc and not clean_desc.lower().startswith("finding"):
                        op_text = translator(
                            "narrative_op_risk_general_desc",
                            locale=doc_lang,
                            kpi_name=kpi_name,
                            clean_desc=clean_desc,
                        )
                    else:
                        op_text = translator(
                            "narrative_op_risk_general_sla",
                            locale=doc_lang,
                            kpi_name=kpi_name,
                        )

        # Economic Justification
        if norm_physics in ("FINOPS_RESOURCE_WASTE", "ASSET_OBSOLESCENCE_AND_INTEGRITY") or (sle <= 0 and rto_hours <= 0):
            cost_text = translator("narrative_cost_just_finops_and_obsolescence", locale=doc_lang, ale_formatted=ale_fmt)
        elif norm_physics == "ENGINEERING_VELOCITY_FRICTION":
            cost_text = translator(
                "narrative_cost_just_engineering_velocity",
                locale=doc_lang,
                sle_formatted=sle_fmt,
                freq_str=freq_str,
                ale_formatted=ale_fmt,
            )
        elif norm_physics == "REGULATORY_AND_BREACH" or rto_hours <= 0.0:
            cost_text = translator(
                "narrative_cost_just_compliance_and_governance",
                locale=doc_lang,
                sle_formatted=sle_fmt,
                freq_str=freq_str,
                ale_formatted=ale_fmt,
            )
        else:
            if rto_hours >= 4.0:
                cost_text = translator(
                    "narrative_cost_just_outage_major",
                    locale=doc_lang,
                    rto_hours=rto_formatted,
                    sle_formatted=sle_fmt,
                    freq_str=freq_str,
                    ale_formatted=ale_fmt,
                )
            else:
                cost_text = translator(
                    "narrative_cost_just_outage_minor",
                    locale=doc_lang,
                    rto_hours=rto_str,
                    sle_formatted=sle_fmt,
                    freq_str=freq_str,
                    ale_formatted=ale_fmt,
                )

        op_hdr = translator("narrative_header_operational_impact", locale=doc_lang)
        cost_hdr = translator("narrative_header_economic_cost", locale=doc_lang)

        return f"{op_hdr}\n{op_text}\n\n{cost_hdr}\n{cost_text}"
