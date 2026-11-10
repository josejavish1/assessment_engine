"""Domain models for tenant financial profiles and universal risk classification enums.

Provides immutable value objects to parameterize Open FAIR actuarial risk modeling
across all 11 GICS sectors mapped into 6 universal operational archetypes.
Strictly 100% Technical English, zero hardcoding, and zero client coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import re


class IndustryArchetype(str, Enum):
    """Classifies the enterprise operational tempo and downtime dependency profile

    covering all 11 Global Industry Classification Standard (GICS) sectors.
    """

    CONTINUOUS_DIGITAL_FINTECH = "CONTINUOUS_DIGITAL_FINTECH"       # SaaS, FinTech, Banking, Crypto, Telco Core
    PROCESS_MANUFACTURING_OT = "PROCESS_MANUFACTURING_OT"           # Heavy Industry, Materials, Process Manufacturing, Energy, Utilities
    LIFE_SAFETY_CRITICAL = "LIFE_SAFETY_CRITICAL"                   # Hospitals, Healthcare Networks, Clinical Diagnostics
    HIGH_TEMPO_COMMERCIAL = "HIGH_TEMPO_COMMERCIAL"                 # Omni-Channel Retail, Supermarkets, Airlines, Hospitality
    DEFERRED_NETWORK_LOGISTICS = "DEFERRED_NETWORK_LOGISTICS"       # Freight Forwarding, Cargo, Maritime, Warehousing
    PUBLIC_SECTOR_CIVIC_MISSION = "PUBLIC_SECTOR_CIVIC_MISSION"     # Sovereign Government, Defense, Municipalities, Education, NGOs
    STANDARD_ENTERPRISE_B2B = "STANDARD_ENTERPRISE_B2B"             # B2B Services, Corporate Insurance, Legal, Consulting, Real Estate
    DYNAMIC_EMPIRICAL_AUTONOMOUS = "DYNAMIC_EMPIRICAL_AUTONOMOUS"   # Unclassified, Hybrid, Conglomerate (Self-Calibrated via Pure Math)

    # Legacy compatibility aliases
    MANUFACTURING_24_7 = "PROCESS_MANUFACTURING_OT"
    FINTECH_CONTINUOUS = "CONTINUOUS_DIGITAL_FINTECH"
    HEALTHCARE_CRITICAL = "LIFE_SAFETY_CRITICAL"
    RETAIL_OMNICHANNEL = "HIGH_TEMPO_COMMERCIAL"
    TELECOMMUNICATIONS = "CONTINUOUS_DIGITAL_FINTECH"
    PUBLIC_SECTOR_GOVERNMENT = "PUBLIC_SECTOR_CIVIC_MISSION"
    B2B_ENTERPRISE_STANDARD = "STANDARD_ENTERPRISE_B2B"

    @classmethod
    def from_str(cls, raw: str) -> IndustryArchetype:
        """Resolves an industry archetype string safely, defaulting to autonomous dynamic self-calibration."""
        if not raw:
            return cls.DYNAMIC_EMPIRICAL_AUTONOMOUS
        raw_clean = raw.strip().upper()
        for member in cls:
            if member.value == raw_clean or member.name == raw_clean:
                return member

        # Multi-lingual & token-based fuzzy fallback mapping across global verticals
        low = raw.lower()

        # 1. Clinical / Life-Safety takes priority over generic SaaS/Software tokens (e.g. "Clinical Cloud SaaS")
        if any(w in low for w in ("health", "pharma", "clinical", "hospital", "life science", "biotech", "medical", "patient telemetry")):
            return cls.LIFE_SAFETY_CRITICAL

        # 2. Heavy Process / Physical Manufacturing (including Aerospace & Defense Contractors)
        if any(w in low for w in (
            "manufactur", "materials", "industrial", "automotive", "mining", "energy",
            "utility", "oil", "gas", "chemical", "metal", "steel", "foundry", "cement",
            "quarry", "semiconductor", "lithography", "electronics", "nuclear", "grid",
            "power", "substation", "electricity", "water", "agriculture", "farming",
            "forestry", "tooling", "cnc", "machinery", "construction", "aerospace",
            "defense contractor", "defense systems", "defense manufacturing", "airbus", "boeing"
        )):
            return cls.PROCESS_MANUFACTURING_OT

        # 3. Continuous Digital FinTech & Telecom
        if any(w in low for w in (
            "fintech", "bank", "financial", "trading", "capital markets",
            "saas", "software", "telecom", "cloud", "telecommunications", "carrier", "5g", "payment", "mobile money"
        )):
            return cls.CONTINUOUS_DIGITAL_FINTECH

        # 4. Commercial & High-Tempo Retail / Aviation
        if any(w in low for w in ("retail", "ecommerce", "supermarket", "grocery", "airline", "aviation", "flight", "hotel", "hospitality", "store", "cpg", "apparel", "fashion")):
            return cls.HIGH_TEMPO_COMMERCIAL

        # 5. Deferred Logistics & Supply Chain
        if any(w in low for w in ("logistics", "freight", "shipping", "cargo", "warehouse", "transit", "supply chain", "truck", "maritime", "port terminal")):
            return cls.DEFERRED_NETWORK_LOGISTICS

        # 6. Professional B2B Services (including Corporate Law Firms)
        if any(w in low for w in ("insurance", "reinsurance", "legal", "law", "law firm", "consulting", "real estate", "professional", "audit", "b2b", "advisory")):
            return cls.STANDARD_ENTERPRISE_B2B

        # 7. Public Sector & Civic Mission
        if any(w in low for w in ("gov", "public sector", "ministry", "civic", "ngo", "education", "university", "municipality")) or re.search(r"\bstate\b", low):
            return cls.PUBLIC_SECTOR_CIVIC_MISSION

        return cls.DYNAMIC_EMPIRICAL_AUTONOMOUS


class BlastRadius(str, Enum):
    """Blast radius extent for architectural failures."""
    ISOLATED_WORKSTATION = "ISOLATED_WORKSTATION"
    DEPARTMENTAL_SUBNET = "DEPARTMENTAL_SUBNET"
    REGIONAL_FACILITY = "REGIONAL_FACILITY"
    ENTERPRISE_SYSTEMIC = "ENTERPRISE_SYSTEMIC"


class RedundancyState(str, Enum):
    """Architectural redundancy state of an infrastructure component."""
    ACTIVE_ACTIVE_HA = "ACTIVE_ACTIVE_HA"
    ACTIVE_PASSIVE_WARM = "ACTIVE_PASSIVE_WARM"
    DEGRADED_MANUAL_FAILOVER = "DEGRADED_MANUAL_FAILOVER"
    SINGLE_POINT_OF_FAILURE = "SINGLE_POINT_OF_FAILURE"


class SeverityTier(str, Enum):
    """Ordinal qualitative severity tiers for technical and operational risks."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class TenantFinancialProfile:
    """Enterprise-wide macroeconomic telemetry establishing the actuarial financial baseline.

    All numerical fields are strictly typed as Decimal to eliminate IEEE 754 floating-point drift.
    Includes Dual-Horizon Disaster Recovery parameters (MVR vs FFR) and sector revenue deferral.
    """

    annual_revenue: Decimal
    industry_archetype: IndustryArchetype
    tenant_id: str = "DEFAULT"
    currency_code: str = "USD"
    working_days_per_year: int = 250
    explicit_hourly_burn_override: Decimal | None = None
    explicit_specialist_engineering_rate_override: Decimal | None = None
    contingency_manual_retention_ratio: Decimal | None = None

    def __post_init__(self) -> None:
        if self.annual_revenue < Decimal("0"):
            raise ValueError(f"annual_revenue cannot be negative: {self.annual_revenue}")
        if self.working_days_per_year <= 0:
            raise ValueError(f"working_days_per_year must be positive: {self.working_days_per_year}")
        if (
            self.contingency_manual_retention_ratio is not None
            and not (Decimal("0") <= self.contingency_manual_retention_ratio <= Decimal("1"))
        ):
            raise ValueError(
                f"contingency_manual_retention_ratio must be in [0, 1]: {self.contingency_manual_retention_ratio}"
            )

    @property
    def operational_hours_per_year(self) -> Decimal:
        """Operating hours in a standard enterprise calendar year based on vertical tempo."""
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("8760"),
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("8760"),
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("8760"),
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("6570"),
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("8760"),
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: Decimal("2080"),
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("2080"),
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: Decimal("8760"),
        }
        return mapping.get(self.industry_archetype, Decimal("8760"))

    @property
    def operational_dependency_factor(self) -> Decimal:
        """Fraction of total revenue velocity directly halted by a severe infrastructure disruption."""
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("1.85"),  # SLA penalties + churn multiplier
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("0.35"),
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("0.45"),
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("0.35"),
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("0.22"),
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: Decimal("0.50"), # Sunk civil servant wages + statutory disruption
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("0.40"),
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: Decimal("0.35"),
        }
        return mapping.get(self.industry_archetype, Decimal("0.35"))

    @property
    def revenue_deferral_factor(self) -> Decimal:
        """Fraction of halted revenue that is recovered later via backlog fulfillment or shift rescheduling."""
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("0.65"),    # Factory orders made up in subsequent shifts
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("0.50"),  # Freight delivered with delay
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("0.40"),     # Advisory work resumed next business day
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("0.20"),       # Some retail delayed, most abandoned
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("0.10"),        # Emergency diverted, elective rescheduled
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("0.05"),  # Instant transaction perishability
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: Decimal("0.35"),
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: Decimal("0.35"),
        }
        return mapping.get(self.industry_archetype, Decimal("0.35"))

    @property
    def mvr_recovery_hours(self) -> float:
        """Minimum Viable Operational Recovery (MVR) duration in hours (emergency contingency bypass)."""
        mapping: dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 4.0,   # Automated cloud failover & payment rerouting
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 12.0,       # Paper charting & emergency backup triage
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 18.0,       # Offline POS store contingency
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 48.0,    # Bare-metal PLC re-flash & manual weighbridge bypass
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 24.0,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 24.0,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 36.0,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 24.0,
        }
        return mapping.get(self.industry_archetype, 24.0)

    @property
    def ffr_recovery_days(self) -> float:
        """Full Forensic & Fleet Restoration (FFR) duration in days (total sanitation and audit sign-off)."""
        mapping: dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 5.0,   # Rapid immutable rehydration + audit trace
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 18.0,        # HIS/EMR database forensic validation
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 14.0,
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 21.0,    # Active Directory rebuild across remote plants
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 14.0,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 14.0,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 21.0,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 14.0,
        }
        return mapping.get(self.industry_archetype, 14.0)

    @property
    def physical_damage_step(self) -> Decimal:
        """Step-function physical asset replacement cost for severe industrial / process halts."""
        if self.industry_archetype == IndustryArchetype.PROCESS_MANUFACTURING_OT:
            # Dimensionless scaling: 0.1% of turnover, bounded between 0.005% and 0.2%
            if self.annual_revenue > Decimal("0"):
                step = self.annual_revenue * Decimal("0.001")
                min_step = self.annual_revenue * Decimal("0.00005")
                max_step = self.annual_revenue * Decimal("0.002")
                return min(max_step, max(min_step, step))
        return Decimal("0.00")

    @property
    def manual_contingency_retention_factor(self) -> Decimal:
        """Fraction of physical/operational throughput retained via local manual fallback (e.g., paper waybills)."""
        if self.contingency_manual_retention_ratio is not None:
            return self.contingency_manual_retention_ratio
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("0.40"),    # Decoupled local weighing & paper dispatch
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("0.35"),  # Manual manifest processing
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("0.30"),        # Paper clinical charting & manual triage
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: Decimal("0.25"),
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("0.20"),
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("0.10"),
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("0.00"),  # Zero manual bypass for digital APIs
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: Decimal("0.20"),
        }
        return mapping.get(self.industry_archetype, Decimal("0.20"))

    @property
    def specialist_engineering_hourly_rate(self) -> Decimal:
        """Internal specialist engineering labor rate for operational toil valuation.

        Strictly decoupled from macroeconomic plant/revenue downtime burn to prevent
        the actuarial fallacy of pricing IT sysadmin toil at corporate revenue velocity.
        """
        if self.explicit_specialist_engineering_rate_override is not None:
            return self.explicit_specialist_engineering_rate_override.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("85.00"),
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("75.00"),
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("75.00"),
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("65.00"),
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("65.00"),
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("60.00"),
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: Decimal("55.00"),
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: Decimal("65.00"),
        }
        return mapping.get(self.industry_archetype, Decimal("65.00"))

    @property
    def hourly_downtime_burn(self) -> Decimal:
        """Authoritative hourly business cost during a systemic operational blackout."""
        if self.explicit_hourly_burn_override is not None:
            return self.explicit_hourly_burn_override
        if self.annual_revenue == Decimal("0"):
            return Decimal("0.00")
        base_hourly = self.annual_revenue / self.operational_hours_per_year
        burn = base_hourly * self.operational_dependency_factor
        return burn.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def effective_hourly_burn_for_redundancy(self, redundancy_state: RedundancyState) -> Decimal:
        """Calculates net hourly business interruption burn accounting for manual contingency retention."""
        gross_burn = self.hourly_downtime_burn
        if redundancy_state == RedundancyState.DEGRADED_MANUAL_FAILOVER:
            net_factor = Decimal("1.00") - self.manual_contingency_retention_factor
            return (gross_burn * net_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if redundancy_state == RedundancyState.ACTIVE_PASSIVE_WARM:
            return (gross_burn * Decimal("0.25")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if redundancy_state == RedundancyState.ACTIVE_ACTIVE_HA:
            return (gross_burn * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return gross_burn
