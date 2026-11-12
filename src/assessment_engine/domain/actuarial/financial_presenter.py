from __future__ import annotations

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


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
    """

    @staticmethod
    def format_p015_executive_narrative(
        report: FinancialTelemetryReport,
        locale: str = "es"
    ) -> str:
        """
        Formats an authoritative, CFO-grade narrative explaining:
        1. Direct hourly operational burn rate.
        2. Expected annualized loss (ALE).
        3. Cumulative annual stress scenario (P90) vs. single isolated incident (Max SLE).
        """
        if locale.startswith("es"):
            p1 = (
                f"Bajo el estándar internacional Open FAIR™ (Factor Analysis of Information Risk), "
                f"la indisponibilidad no planificada del servicio conlleva un coste operativo directo de "
                f"**{report.hourly_rate_formatted}** (detallado en la Sección 4.1). En condiciones ordinarias, "
                f"las brechas técnicas evaluadas específicamente en el ámbito de **{report.tower_name}** "
                f"representan una **exposición de riesgo latente estimada en {report.annual_ale_formatted} anualizados**, "
                f"cifra que refleja la pérdida media esperada por la fricción operativa e incidencias a lo largo de un año dentro de este dominio."
            )
            p2 = (
                f"Adicionalmente, ante un **escenario de estrés financiero severo (Percentil 90 / P90)**, "
                f"la acumulación estocástica de múltiples contingencias técnicas a lo largo de un ejercicio anual "
                f"podría elevar las pérdidas agregadas del dominio hasta **{report.p90_tail_risk_formatted}**. "
                f"En términos de liquidez operativa inmediata, el impacto económico derivado de la materialización del "
                f"peor incidente individual aislado (Pérdida Máxima por Evento / Max SLE) se estima en **{report.max_sle_formatted}**, "
                f"con un tiempo de recuperación técnica de hasta **{report.max_recovery_hours:.1f} horas**."
            )
            if report.deterministic_opex_formatted:
                p2 += (
                    f" A esta exposición por contingencias probables debe sumarse un **desperdicio operativo fijo (OpEx determinista)** "
                    f"de **{report.deterministic_opex_formatted} anuales** derivado de ineficiencias de suscripción y contratos cautivos."
                )
            return f"{p1}\n\n{p2}"

        # Default English
        p1 = (
            f"Under the international Open FAIR™ standard, unplanned service downtime incurs a direct operational burn rate of "
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
        return f"{p1}\n\n{p2}"
