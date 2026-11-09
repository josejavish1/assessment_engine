"""Domain models for tenant financial profiles and universal risk classification enums.

Provides immutable value objects to parameterize Open FAIR actuarial risk modeling
across all 11 GICS sectors mapped into 6 universal operational archetypes.
Strictly 100% Technical English, zero hardcoding, and zero client coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class IndustryArchetype(str, Enum):
    """Classifies the enterprise operational tempo and downtime dependency profile

    covering all 11 Global Industry Classification Standard (GICS) sectors.
    """

    CONTINUOUS_DIGITAL_FINTECH = "CONTINUOUS_DIGITAL_FINTECH"       # SaaS, FinTech, Banking, Crypto, Telco Core
    PROCESS_MANUFACTURING_OT = "PROCESS_MANUFACTURING_OT"           # Heavy Industry, Materials, Cement, Energy, Utilities
    LIFE_SAFETY_CRITICAL = "LIFE_SAFETY_CRITICAL"                   # Hospitals, Healthcare Networks, Clinical Diagnostics
    HIGH_TEMPO_COMMERCIAL = "HIGH_TEMPO_COMMERCIAL"                 # Omni-Channel Retail, Supermarkets, Airlines, Hospitality
    DEFERRED_NETWORK_LOGISTICS = "DEFERRED_NETWORK_LOGISTICS"       # Freight Forwarding, Cargo, Maritime, Warehousing
    STANDARD_ENTERPRISE_B2B = "STANDARD_ENTERPRISE_B2B"             # B2B Services, Corporate Insurance, Legal, Consulting, Gov

    # Legacy compatibility aliases
    MANUFACTURING_24_7 = "PROCESS_MANUFACTURING_OT"
    FINTECH_CONTINUOUS = "CONTINUOUS_DIGITAL_FINTECH"
    HEALTHCARE_CRITICAL = "LIFE_SAFETY_CRITICAL"
    RETAIL_OMNICHANNEL = "HIGH_TEMPO_COMMERCIAL"
    TELECOMMUNICATIONS = "CONTINUOUS_DIGITAL_FINTECH"
    PUBLIC_SECTOR_GOVERNMENT = "STANDARD_ENTERPRISE_B2B"
    B2B_ENTERPRISE_STANDARD = "STANDARD_ENTERPRISE_B2B"

    @classmethod
    def from_str(cls, raw: str) -> IndustryArchetype:
        """Resolves an industry archetype string safely, defaulting to standard enterprise."""
        if not raw:
            return cls.STANDARD_ENTERPRISE_B2B
        raw_clean = raw.strip().upper()
        for member in cls:
            if member.value == raw_clean or member.name == raw_clean:
                return member

        # Multi-lingual & token-based fuzzy fallback mapping across global verticals
        low = raw.lower()
        if any(w in low for w in ("manufactur", "cement", "industrial", "automotive", "mining", "energy", "utility", "oil", "gas", "chemical", "metal", "steel")):
            return cls.PROCESS_MANUFACTURING_OT
        if any(w in low for w in ("fintech", "bank", "financial", "insurance", "capital", "saas", "software", "telecom", "cloud", "trading")):
            return cls.CONTINUOUS_DIGITAL_FINTECH
        if any(w in low for w in ("health", "pharma", "clinical", "hospital", "life science", "biotech", "medical")):
            return cls.LIFE_SAFETY_CRITICAL
        if any(w in low for w in ("retail", "ecommerce", "supermarket", "grocery", "airline", "hotel", "hospitality", "store", "cpg")):
            return cls.HIGH_TEMPO_COMMERCIAL
        if any(w in low for w in ("logistics", "freight", "shipping", "cargo", "warehouse", "transit", "supply chain", "truck")):
            return cls.DEFERRED_NETWORK_LOGISTICS
        if any(w in low for w in ("gov", "public", "defense", "legal", "consulting", "real estate", "education")):
            return cls.STANDARD_ENTERPRISE_B2B

        return cls.STANDARD_ENTERPRISE_B2B


class SeverityTier(str, Enum):
    """Ordinal qualitative severity tiers for technical and operational risks."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_str(cls, raw: str) -> SeverityTier:
        """Parses a severity string safely, defaulting to MEDIUM."""
        if not raw:
            return cls.MEDIUM
        raw_clean = raw.strip().upper()
        if "CRIT" in raw_clean:
            return cls.CRITICAL
        if "HIGH" in raw_clean:
            return cls.HIGH
        if "MED" in raw_clean:
            return cls.MEDIUM
        if "LOW" in raw_clean:
            return cls.LOW
        return cls.MEDIUM


class BlastRadius(str, Enum):
    """Spatial and systemic scope of asset outage impact."""

    ISOLATED_WORKSTATION = "ISOLATED_WORKSTATION"
    DEPARTMENTAL_SUBNET = "DEPARTMENTAL_SUBNET"
    REGIONAL_FACILITY = "REGIONAL_FACILITY"
    ENTERPRISE_SYSTEMIC = "ENTERPRISE_SYSTEMIC"


class RedundancyState(str, Enum):
    """Degree of active physical and logical fault tolerance."""

    ACTIVE_ACTIVE_HA = "ACTIVE_ACTIVE_HA"
    ACTIVE_PASSIVE_WARM = "ACTIVE_PASSIVE_WARM"
    DEGRADED_MANUAL_FAILOVER = "DEGRADED_MANUAL_FAILOVER"
    SINGLE_POINT_OF_FAILURE = "SINGLE_POINT_OF_FAILURE"


@dataclass(frozen=True)
class TenantFinancialProfile:
    """Immutable domain entity representing an audited enterprise tenant's economic reality."""

    tenant_id: str
    annual_revenue: Decimal
    industry_archetype: IndustryArchetype
    currency_code: str = "USD"
    explicit_hourly_burn_override: Decimal | None = None

    def __post_init__(self) -> None:
        if self.annual_revenue < Decimal("0"):
            raise ValueError(f"annual_revenue cannot be negative: {self.annual_revenue}")
        if self.explicit_hourly_burn_override is not None and self.explicit_hourly_burn_override < Decimal("0"):
            raise ValueError("explicit_hourly_burn_override cannot be negative")

    @property
    def operational_hours_per_year(self) -> Decimal:
        """Returns standard annual productive operational hours based on industry archetype."""
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("8760"),
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("8760"),
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("8760"),
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("8760"),
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("6570"),
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("2080"),
        }
        return mapping.get(self.industry_archetype, Decimal("2080"))

    @property
    def operational_dependency_factor(self) -> Decimal:
        """Fraction of total revenue velocity directly halted by a severe infrastructure disruption."""
        mapping: dict[IndustryArchetype, Decimal] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: Decimal("1.85"),  # SLA penalties + churn multiplier
            IndustryArchetype.PROCESS_MANUFACTURING_OT: Decimal("0.35"),
            IndustryArchetype.LIFE_SAFETY_CRITICAL: Decimal("0.45"),
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: Decimal("0.35"),
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: Decimal("0.22"),
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: Decimal("0.40"),
        }
        return mapping.get(self.industry_archetype, Decimal("0.40"))

    @property
    def physical_damage_step(self) -> Decimal:
        """Step-function physical asset replacement cost for severe industrial / process halts."""
        if self.industry_archetype == IndustryArchetype.PROCESS_MANUFACTURING_OT:
            # Scaled to enterprise revenue: 0.1% of turnover, bounded between 50k and 2M
            step = self.annual_revenue * Decimal("0.001")
            return max(Decimal("50000.00"), min(Decimal("2000000.00"), step))
        return Decimal("0.00")

    @property
    def hourly_downtime_burn(self) -> Decimal:
        """Authoritative hourly business cost during a systemic operational blackout."""
        if self.explicit_hourly_burn_override is not None:
            return self.explicit_hourly_burn_override
        if self.annual_revenue == Decimal("0"):
            return Decimal("50.00")
        base_hourly = self.annual_revenue / self.operational_hours_per_year
        burn = base_hourly * self.operational_dependency_factor
        return max(Decimal("50.00"), burn.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
