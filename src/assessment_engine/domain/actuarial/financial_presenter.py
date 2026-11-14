from __future__ import annotations

from typing import Callable, Optional
from pydantic import BaseModel


class FinancialTelemetryReport(BaseModel):
    hourly_rate_formatted: str
    annual_ale_formatted: str
    p90_tail_risk_formatted: str
    max_sle_formatted: str
    max_recovery_hours: float
    tower_name: str
    deterministic_opex_formatted: Optional[str] = None


class DomainFinancialPresenter:
    """
    Tier-1 Financial Presenter.
    Synthesizes fluent executive financial telemetry narratives without the Mad-Libs antipattern.
    Accurately distinguishes between aggregate annual tail risk (P90) and single worst-case loss (Max SLE).
    100% Technical English implementation. Multi-language output handled declaratively via translator.
    """

    @staticmethod
    def format_p015_executive_narrative(
        report: FinancialTelemetryReport,
        locale: str = "en",
        translator: Optional[Callable[..., str]] = None,
    ) -> str:
        """
        Formats an authoritative, CFO-grade narrative explaining:
        1. Direct hourly operational burn rate.
        2. Expected annualized loss (ALE).
        3. Cumulative annual stress scenario (P90) vs. single isolated incident (Max SLE).
        """
        if translator is not None:
            p1 = translator(
                "p015_financial_narrative_fair_standard",
                locale=locale,
                hourly_rate=report.hourly_rate_formatted,
                tower_name=report.tower_name,
                annual_ale=report.annual_ale_formatted,
            )
            is_spanish = str(locale).startswith("es")
            rec_hours_str = f"{report.max_recovery_hours:.1f}".replace(".", ",") if is_spanish else f"{report.max_recovery_hours:.1f}"
            p2 = translator(
                "p015_financial_narrative_stress_scenario",
                locale=locale,
                p90_tail_risk=report.p90_tail_risk_formatted,
                max_sle=report.max_sle_formatted,
                max_recovery_hours=rec_hours_str,
            )
            if report.deterministic_opex_formatted:
                p2 += translator(
                    "p015_financial_narrative_deterministic_opex",
                    locale=locale,
                    deterministic_opex=report.deterministic_opex_formatted,
                )
            return f"{p1}\n\n{p2}"

        # Default canonical Technical English
        p1 = (
            f"Under the international Open FAIR standard, unplanned service downtime incurs a direct operational burn rate of "
            f"**{report.hourly_rate_formatted}** (detailed in Section 4.1). Under standard operating conditions, the technical gaps "
            f"evaluated in **{report.tower_name}** represent an **annualized loss expectancy (ALE) of {report.annual_ale_formatted}**, "
            f"reflecting the expected average friction and incidents over an annual cycle."
        )
        p2 = (
            f"Additionally, under a **severe financial stress scenario (90th Percentile / P90)**, the stochastic accumulation of "
            f"multiple technical contingencies throughout the fiscal year could escalate aggregate domain losses to **{report.p90_tail_risk_formatted}**. "
            f"In terms of immediate operational liquidity, the maximum impact from the worst single isolated incident (Max SLE) is estimated at "
            f"**{report.max_sle_formatted}**, requiring a technical recovery window of up to **{report.max_recovery_hours:.1f} hours**."
        )
        if report.deterministic_opex_formatted:
            p2 += (
                f" To this probabilistic contingency exposure must be added a **fixed operational waste (Deterministic OpEx)** "
                f"of **{report.deterministic_opex_formatted} annually** stemming from captive contracts and unoptimized subscription capacity."
            )
        return f"{p1}\n\n{p2}"
