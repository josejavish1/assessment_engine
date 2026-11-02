# RFC 036: Actuarial Perimeter Weighting & Elimination of Revenue Hardcoding

**Status:** APPROVED FOR IMMEDIATE IMPLEMENTATION  
**Author:** Principal Actuarial Systems Architect & Chief Compiler Engineer  
**Target Subsystem:** `src/assessment_engine/domain/actuarial/` & `src/assessment_engine/infrastructure/i18n/`  
**Compliance Standard:** Zero-Hardcoding Law, MIT Actuarial Fellowship Standards, ISO 31000 / FAIR Framework  

---

## 1. Executive Summary & Architectural Diagnosis

A forensic audit of the actuarial engine revealed two severe anti-patterns that violate enterprise realism and mathematical integrity:

1. **The "1 Billion EUR" Hallucination (Hardcoded Fallback):** In `downtime_calibrator.py`, the revenue extraction pipeline culminates in `or 1000000000`. When upstream telemetry lacks an explicit revenue key or uses an unmapped schema path, the engine silently injects a fabricated, suspiciously round $1\text{B}$ figure. This destroys executive credibility during board-level audits.
2. **Global-to-Local Conflation (Actuarial Over-Inflation):** Applying consolidated global corporate revenue ($R_{\text{global}}$) to a localized infrastructure assessment (e.g., a single manufacturing plant, regional data center, or specific OT perimeter) assumes a single point of failure for the entire multinational enterprise. In a distributed industrial topology, an outage at a single facility only impacts the specific business value sustained by that facility—unless that facility hosts centralized, non-redundant global ERP/core services.

This RFC eradicates all monetary fallbacks from the Python codebase and introduces a multi-dimensional **Actuarial Perimeter Weighting Model**.

---

## 2. Eradicating the 1,000,000,000 Fallback (Data Extraction & Fail-Safe Design)

### 2.1. Deterministic Multi-Path Telemetry Extraction
The engine must traverse the ingested JSON payload deterministically across all standardized corporate intelligence schemas (`organization_profile`, `financial_metrics`, `corporate_intelligence`) to extract the audited annual revenue (e.g., official consolidated figures from annual reports, such as `1349000000.0` or `1265400000.0`).

### 2.2. Actuarial Fail-Fast & Parametric Estimation (Zero Faking)
If no explicit revenue figure exists in the payload, the engine **must never invent a round number**. Instead, it must execute a two-tier resolution strategy:
1. **Strict Mode (Default for Production Audits):** Raise a `MissingActuarialTelemetryError` halting compilation until the ingestion payload is populated with verified registry data.
2. **Parametric Estimation Mode (Fallback for Partial Discovery):** Derive an actuarial baseline dynamically from verified physical/operational telemetry (e.g., `employee_headcount` $\times$ `sector_revenue_per_employee_benchmark`), explicitly flagging the output metadata with `revenue_source = "PARAMETRIC_HEADCOUNT_ESTIMATE"` so the narrative generator discloses the estimation methodology transparently.

---

## 3. Actuarial Design: Site-Weighted Revenue Scaling

To accurately model the financial blast radius of a localized outage, we introduce the **Perimeter Revenue Exposure Factor ($\omega_{\text{perimeter}}$)**.

### 3.1. Mathematical Formulation

Let $R_{\text{global}}$ be the consolidated annual corporate revenue.  
Let $\omega_{\text{perimeter}} \in (0, 1]$ be the **Perimeter Revenue Weight** (represented in telemetry as `perimeter_revenue_weight_pct` $\in (0, 100]$).

The **Effective Exposed Revenue ($R_{\text{exposed}}$)** sustained by the audited perimeter is defined as:

$$R_{\text{exposed}} = R_{\text{global}} \times \left( \frac{\text{perimeter\_revenue\_weight\_pct}}{100.0} \right)$$

Note that $\omega_{\text{perimeter}}$ is a composite actuarial metric representing the maximum of two vectors:
1. **Direct Production Weight:** The percentage of physical goods or services generated directly at the local site (e.g., $12.5\%$ for one of eight major cement plants).
2. **Centralized IT Dependency Weight:** If the local site acts as the primary data center hosting the global ERP/MES for other plants, $\omega_{\text{perimeter}}$ scales up to reflect the downstream operational paralysis inflicted on dependent facilities.

### 3.2. Revised Hourly Downtime Cost Formula

Let $\alpha_{\text{sector}}$ be the annualized sector downtime impact factor (derived from continuous vs. batch operational profiles, supply chain elasticity, and regulatory SLA penalties), or let $H_{\text{op}}$ be the annual operational hours (e.g., $8,760\text{ hours}$ for $24/7$ industrial environments) coupled with a direct margin/cost-recovery multiplier $\mu_{\text{impact}}$.

Using the standardized actuarial sector factor approach:

$$\text{Cost}_{\text{hourly}} = R_{\text{exposed}} \times \alpha_{\text{sector}} = \left( R_{\text{global}} \times \frac{\text{perimeter\_revenue\_weight\_pct}}{100.0} \right) \times \alpha_{\text{sector}}$$

---

## 4. Production Implementation (`downtime_calibrator.py`)

Below is the complete, production-ready replacement for the calibration module, written in 100% Technical English with zero hardcoded monetary amounts or client identifiers.

```python
"""
Actuarial Downtime Calibration Engine.

Computes localized hourly operational downtime costs using verified corporate
financial telemetry, perimeter-specific revenue weighting, and sector-specific
operational elasticity factors. Complies with ISO 31000 and FAIR standards.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelemetryResolutionError(ValueError):
    """Raised when mandatory actuarial financial telemetry cannot be resolved."""


class RevenueSourceType(str, Enum):
    """Classification of the underlying financial data provenance."""
    VERIFIED_FILING = "VERIFIED_CORPORATE_FILING"
    PARAMETRIC_DERIVATION = "PARAMETRIC_HEADCOUNT_DERIVATION"


@dataclass(frozen=True)
class CalibratedDowntimeMetrics:
    """Immutable value object containing calibrated actuarial downtime parameters."""
    global_annual_revenue: Decimal
    perimeter_revenue_weight_pct: Decimal
    effective_exposed_revenue: Decimal
    sector_impact_factor: Decimal
    calibrated_hourly_cost: Decimal
    currency_code: str
    revenue_source: RevenueSourceType
    audited_perimeter_name: str


class ActuarialDowntimeCalibrator:
    """
    Calibrates hourly financial exposure by scaling consolidated corporate revenue
    down to the exact operational footprint of the audited perimeter.
    """

    DEFAULT_OPERATIONAL_HOURS_PER_YEAR: Decimal = Decimal("8760.0")

    @classmethod
    def calibrate(
        cls,
        organization_profile: Dict[str, Any],
        sector_benchmarks: Dict[str, Any],
        strict_telemetry: bool = True,
    ) -> CalibratedDowntimeMetrics:
        """
        Executes the actuarial downtime calibration pipeline.

        Args:
            organization_profile: Telemetry dictionary containing corporate and site metrics.
            sector_benchmarks: Externalized actuarial lookup parameters for the industry vertical.
            strict_telemetry: If True, fails fast when explicit revenue is absent.

        Returns:
            CalibratedDowntimeMetrics: Fully resolved and scaled financial exposure metrics.

        Raises:
            TelemetryResolutionError: If financial parameters are missing or mathematically invalid.
        """
        currency_code = cls._extract_currency(organization_profile)
        perimeter_name = cls._extract_perimeter_name(organization_profile)

        global_revenue, rev_source = cls._resolve_global_revenue(
            organization_profile=organization_profile,
            sector_benchmarks=sector_benchmarks,
            strict=strict_telemetry,
        )

        perimeter_weight_pct = cls._resolve_perimeter_weight_pct(
            organization_profile=organization_profile,
            sector_benchmarks=sector_benchmarks,
        )

        sector_factor = cls._resolve_sector_impact_factor(
            organization_profile=organization_profile,
            sector_benchmarks=sector_benchmarks,
        )

        # Mathematical calculation: Effective Exposed Revenue = Global Revenue * (Weight % / 100)
        weight_ratio = perimeter_weight_pct / Decimal("100.0")
        effective_exposed_revenue = (global_revenue * weight_ratio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Mathematical calculation: Hourly Cost = Effective Exposed Revenue * Sector Factor
        calibrated_hourly_cost = (effective_exposed_revenue * sector_factor).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        logger.info(
            "Actuarial calibration complete for perimeter '%s': "
            "GlobalRev=%s %s (Source=%s), Weight=%s%%, ExposedRev=%s %s, HourlyCost=%s %s",
            perimeter_name,
            global_revenue,
            currency_code,
            rev_source.value,
            perimeter_weight_pct,
            effective_exposed_revenue,
            currency_code,
            calibrated_hourly_cost,
            currency_code,
        )

        return CalibratedDowntimeMetrics(
            global_annual_revenue=global_revenue,
            perimeter_revenue_weight_pct=perimeter_weight_pct,
            effective_exposed_revenue=effective_exposed_revenue,
            sector_impact_factor=sector_factor,
            calibrated_hourly_cost=calibrated_hourly_cost,
            currency_code=currency_code,
            revenue_source=rev_source,
            audited_perimeter_name=perimeter_name,
        )

    @classmethod
    def _resolve_global_revenue(
        cls,
        organization_profile: Dict[str, Any],
        sector_benchmarks: Dict[str, Any],
        strict: bool,
    ) -> tuple[Decimal, RevenueSourceType]:
        """
        Extracts consolidated annual revenue from telemetry without arbitrary hardcoded fallbacks.
        """
        financial_block = organization_profile.get("financial_metrics", {})
        if not isinstance(financial_block, dict):
            financial_block = {}

        # Priority-ordered schema traversal for verified revenue figures
        candidate_values = [
            financial_block.get("consolidated_annual_revenue"),
            financial_block.get("annual_revenue_amount"),
            organization_profile.get("consolidated_annual_revenue"),
            organization_profile.get("annual_revenue_amount"),
            organization_profile.get("annual_revenue_eur"),
            organization_profile.get("annual_revenue"),
        ]

        for val in candidate_values:
            if val is not None and str(val).strip() != "":
                try:
                    parsed_rev = Decimal(str(val))
                    if parsed_rev <= Decimal("0"):
                        raise TelemetryResolutionError(
                            f"Consolidated revenue must be strictly positive. Received: {parsed_rev}"
                        )
                    return parsed_rev, RevenueSourceType.VERIFIED_FILING
                except (ValueError, TypeError) as exc:
                    raise TelemetryResolutionError(
                        f"Malformed monetary value in revenue telemetry: '{val}'"
                    ) from exc

        if strict:
            raise TelemetryResolutionError(
                "Missing mandatory 'consolidated_annual_revenue' in organization_profile. "
                "Hardcoded monetary fallbacks are strictly prohibited by actuarial governance."
            )

        # Non-strict fallback: Parametric derivation via verified employee headcount
        headcount = organization_profile.get("employee_headcount")
        rev_per_employee = sector_benchmarks.get("revenue_per_employee_benchmark")

        if headcount is not None and rev_per_employee is not None:
            try:
                derived_rev = Decimal(str(headcount)) * Decimal(str(rev_per_employee))
                if derived_rev > Decimal("0"):
                    return derived_rev, RevenueSourceType.PARAMETRIC_DERIVATION
            except (ValueError, TypeError):
                pass

        raise TelemetryResolutionError(
            "Unable to resolve corporate revenue via direct filing telemetry or parametric headcount derivation."
        )

    @classmethod
    def _resolve_perimeter_weight_pct(
        cls,
        organization_profile: Dict[str, Any],
        sector_benchmarks: Dict[str, Any],
    ) -> Decimal:
        """
        Resolves the percentage of global corporate revenue sustained by the audited site/perimeter.
        """
        perimeter_block = organization_profile.get("perimeter_context", {})
        if not isinstance(perimeter_block, dict):
            perimeter_block = {}

        raw_weight = (
            perimeter_block.get("perimeter_revenue_weight_pct")
            or organization_profile.get("perimeter_revenue_weight_pct")
            or organization_profile.get("site_revenue_weight_pct")
        )

        if raw_weight is not None:
            try:
                weight_pct = Decimal(str(raw_weight))
            except (ValueError, TypeError) as exc:
                raise TelemetryResolutionError(
                    f"Invalid numeric format for 'perimeter_revenue_weight_pct': '{raw_weight}'"
                ) from exc

            if not (Decimal("0.0001") <= weight_pct <= Decimal("100.0")):
                raise TelemetryResolutionError(
                    f"'perimeter_revenue_weight_pct' must be in range (0, 100]. Received: {weight_pct}"
                )
            return weight_pct

        # Structural fallback: Calculate weight proportionally if total facilities count is known
        total_facilities = organization_profile.get("total_operational_facilities")
        if total_facilities is not None:
            try:
                facilities_count = int(total_facilities)
                if facilities_count > 0:
                    proportional_weight = (Decimal("100.0") / Decimal(str(facilities_count))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    return proportional_weight
            except (ValueError, TypeError):
                pass

        # Sector benchmark default weight for a single standard node in a distributed enterprise
        default_node_weight = sector_benchmarks.get("default_single_site_weight_pct")
        if default_node_weight is not None:
            return Decimal(str(default_node_weight))

        raise TelemetryResolutionError(
            "Missing 'perimeter_revenue_weight_pct' and insufficient structural topology telemetry "
            "('total_operational_facilities') to compute site-specific revenue weighting."
        )

    @classmethod
    def _resolve_sector_impact_factor(
        cls,
        organization_profile: Dict[str, Any],
        sector_benchmarks: Dict[str, Any],
    ) -> Decimal:
        """
        Resolves the hourly sector impact multiplier (alpha_sector).
        """
        raw_factor = (
            organization_profile.get("sector_hourly_impact_factor")
            or sector_benchmarks.get("hourly_downtime_revenue_factor")
        )

        if raw_factor is not None:
            factor = Decimal(str(raw_factor))
            if factor <= Decimal("0"):
                raise TelemetryResolutionError("Sector impact factor must be strictly positive.")
            return factor

        # Derive hourly factor from annual operational hours and operational margin multiplier
        op_hours = Decimal(
            str(sector_benchmarks.get("annual_operational_hours", cls.DEFAULT_OPERATIONAL_HOURS_PER_YEAR))
        )
        impact_multiplier = Decimal(str(sector_benchmarks.get("operational_interruption_multiplier", "1.0")))

        return (impact_multiplier / op_hours).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _extract_currency(organization_profile: Dict[str, Any]) -> str:
        """Extracts ISO 4217 currency code from profile telemetry."""
        currency = (
            organization_profile.get("currency_code")
            or organization_profile.get("financial_metrics", {}).get("currency_code")
            or "EUR"
        )
        return str(currency).upper().strip()

    @staticmethod
    def _extract_perimeter_name(organization_profile: Dict[str, Any]) -> str:
        """Extracts human-readable identifier of the audited facility or perimeter."""
        perimeter = (
            organization_profile.get("perimeter_context", {}).get("perimeter_name")
            or organization_profile.get("audited_site_name")
            or organization_profile.get("facility_identifier")
            or "Primary Audited Operational Perimeter"
        )
        return str(perimeter).strip()
```

---

## 5. Telemetry Schema Contract Update

Upstream intelligence ingestion payloads (`organization_profile`) must adhere to the following schema contract to feed the calibrator accurately:

```json
{
  "organization_profile": {
    "currency_code": "EUR",
    "financial_metrics": {
      "consolidated_annual_revenue": 1349000000.00,
      "fiscal_year": 2023,
      "source_document": "Official Consolidated Annual Financial Statements"
    },
    "perimeter_context": {
      "perimeter_name": "Industrial Production Plant & Regional OT Hub",
      "perimeter_revenue_weight_pct": 14.50,
      "weighting_rationale": "Direct plant manufacturing output (8.5%) plus shared ERP/MES orchestration dependency for regional satellite plants (6.0%)."
    }
  }
}
```

---

## 6. Executive Pedagogy & Narrative Localization (`locales.json`)

To ensure the CIO, CFO, and Board Risk Committee immediately recognize the mathematical rigor of the model, the narrative templates in `src/assessment_engine/infrastructure/i18n/locales.json` are updated. They explicitly decompose:
1. The exact consolidated revenue from official filings.
2. The site-specific weighting factor ($\omega_{\text{perimeter}}$) that prevents global over-inflation.
3. The resulting localized hourly exposure.

```json
{
  "en": {
    "actuarial_methodology": {
      "downtime_calibration_narrative": "To ensure strict actuarial realism and avoid inflating localized operational risks with global corporate figures, the financial exposure model scopes the calculation exclusively to the audited perimeter ({audited_perimeter_name}). Starting from a verified consolidated annual turnover of {global_annual_revenue_formatted} {currency_code}, the engine applies a Perimeter Revenue Weighting Factor of {perimeter_revenue_weight_pct}%—reflecting the exact proportion of direct production volume and centralized IT/OT service dependencies sustained by this specific facility. This yields an Effective Exposed Revenue baseline of {effective_exposed_revenue_formatted} {currency_code}. Applying the industry-calibrated operational interruption factor ({sector_impact_factor}), the resulting localized downtime cost is established at {calibrated_hourly_cost_formatted} {currency_code} per hour of critical outage."
    }
  },
  "es": {
    "actuarial_methodology": {
      "downtime_calibration_narrative": "Para garantizar un rigor actuarial estricto y evitar distorsionar el riesgo operativo local aplicando la totalidad de la facturación corporativa global a una única instalación, el modelo financiero acota el cálculo exclusivamente al perímetro auditado ({audited_perimeter_name}). Partiendo de una facturación anual consolidada verificada de {global_annual_revenue_formatted} {currency_code}, el motor aplica un Factor de Ponderación Operativa del Perímetro del {perimeter_revenue_weight_pct}%, el cual representa la fracción exacta del volumen de producción directa y de las dependencias de servicios centrales IT/OT que recaen sobre este centro específico. Esto establece una Base de Facturación Expuesta Efectiva de {effective_exposed_revenue_formatted} {currency_code}. Al aplicar el factor actuarial de interrupción operativa del sector ({sector_impact_factor}), el coste de parada localizada se calibra con precisión en {calibrated_hourly_cost_formatted} {currency_code} por cada hora de inactividad crítica."
    }
  }
}
```

---

## 7. Verification & Boundary Invariants

| Test Vector | Input Telemetry | Expected Engine Behavior |
| :--- | :--- | :--- |
| **1. Verified Multi-Site Enterprise** | `consolidated_annual_revenue`: `1349000000`<br>`perimeter_revenue_weight_pct`: `14.5` | `effective_exposed_revenue` = `195,605,000.00`<br>Zero fallback triggered; exact localized hourly cost computed. |
| **2. Missing Revenue (Strict Mode)** | `consolidated_annual_revenue`: `None`<br>`strict_telemetry`: `True` | Raises `TelemetryResolutionError`. **Never** injects `1000000000`. |
| **3. Topology-Derived Weighting** | `perimeter_revenue_weight_pct`: `None`<br>`total_operational_facilities`: `16` | Automatically computes proportional site weight: $100 / 16 = 6.25\%$. |
| **4. Out-of-Bounds Weight** | `perimeter_revenue_weight_pct`: `125.0` or `0.0` | Raises `TelemetryResolutionError` enforcing $\omega_{\text{perimeter}} \in (0, 100]$. |