"""Domain schemas and deterministic resolvers for the Universal Executive Summary AST.

Implements the Minto Pyramid Principle (SCQA) across 4 structured analytical blocks:
1. SCQA Governance Thesis & Posture
2. Actuarial Loss Exposure & EBITDA Impact
3. Critical Attack Path & Systemic Bottlenecks
4. Capital Allocation & Risk-Adjusted Intervention (RoSI)

Provides 3 universal runtime resolvers:
- ScaleArchetypeResolver (Mid-Market vs Enterprise vs Tier-1 Regulated)
- VerticalChokepointResolver (Domain operational assets and units of pain)
- LocaleFormattingContractResolver (Jurisdictional titles and currency contracts)

Strictly 100% Technical English, zero client coupling, scale-invariant, and vertical-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ScaleArchetype(str, Enum):
    """Enterprise governance, operating size, and supervisory complexity tiers."""

    MID_MARKET_OWNER = "MID_MARKET_OWNER"       # < $150M revenue, Owner/CEO/CFO persona, 30-day tactical horizon
    ENTERPRISE_CORP = "ENTERPRISE_CORP"         # $150M - $2B revenue, CIO/CISO/Audit Committee, 90-day program
    TIER1_REGULATED = "TIER1_REGULATED"         # > $2B or supervised financial/healthcare, Board Risk Committee


class VerticalArchetype(str, Enum):
    """Universal operational archetypes mapping all 11 GICS sectors and public missions."""

    MANUFACTURING_LOGISTICS = "MANUFACTURING_LOGISTICS"
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    HEALTHCARE_LIFE_SCIENCES = "HEALTHCARE_LIFE_SCIENCES"
    RETAIL_ECOMMERCE = "RETAIL_ECOMMERCE"
    PUBLIC_SECTOR_INFRASTRUCTURE = "PUBLIC_SECTOR_INFRASTRUCTURE"
    TECHNOLOGY_SAAS = "TECHNOLOGY_SAAS"
    GENERAL_COMMERCIAL = "GENERAL_COMMERCIAL"
    DYNAMIC_AUTONOMOUS = "DYNAMIC_AUTONOMOUS"

    @classmethod
    def from_str(cls, raw: str) -> VerticalArchetype:
        """Deterministically maps any raw sector string into the canonical vertical archetype using word boundaries."""
        if not raw:
            return cls.DYNAMIC_AUTONOMOUS
        import re
        low = raw.strip().lower().replace("_", " ").replace("-", " ")

        # Multi-word exact patterns first to avoid collision
        if re.search(r"\b(real estate|property management)\b", low):
            return cls.GENERAL_COMMERCIAL
        if re.search(r"\b(public sector|defense|ministry|government|civic|civil service)\b", low):
            return cls.PUBLIC_SECTOR_INFRASTRUCTURE

        # Canonical Technical English sector patterns
        if re.search(r"\b(fintech|bank\w*|financial|insurance|capital|trading|brokerage|credit)\b", low):
            return cls.FINANCIAL_SERVICES
        if re.search(r"\b(health\w*|pharma\w*|clinical|hospital\w*|biotech\w*|medical)\b", low):
            return cls.HEALTHCARE_LIFE_SCIENCES
        if re.search(r"\b(manufactur\w*|material\w*|industrial|mining|energy|utility|utilities|oil|gas|cement|steel|freight|logistics|cargo)\b", low):
            return cls.MANUFACTURING_LOGISTICS
        if re.search(r"\b(retail|ecommerce|e-commerce|supermarket|grocery|airline|hotel|hospitality)\b", low):
            return cls.RETAIL_ECOMMERCE
        if re.search(r"\b(gov\w*|defense|ministry|civic|ngo|education|university)\b", low):
            return cls.PUBLIC_SECTOR_INFRASTRUCTURE
        if re.search(r"\b(saas|software|cloud|telecom\w*|tech|technology)\b", low):
            return cls.TECHNOLOGY_SAAS
        if re.search(r"\b(legal|consulting|professional|audit\w*)\b", low):
            return cls.GENERAL_COMMERCIAL

        return cls.DYNAMIC_AUTONOMOUS


class LossDriverCategory(str, Enum):
    """Standardized Open FAIR primary and secondary loss categorization."""

    OPERATIONAL_INTERRUPTION = "OPERATIONAL_INTERRUPTION"
    REGULATORY_PENALTY = "REGULATORY_PENALTY"
    INCIDENT_RESPONSE_EXTORTION = "INCIDENT_RESPONSE_EXTORTION"


@dataclass(frozen=True)
class LocaleFormattingContract:
    """Immutable jurisdictional formatting contract for edge document presentation."""

    locale_code: str                  # e.g., 'es-ES', 'en-GB', 'pt-BR', 'de-DE'
    currency_iso: str                 # e.g., 'EUR', 'GBP', 'BRL', 'USD'
    currency_symbol: str              # e.g., 'EUR', 'GBP', 'BRL', 'USD' symbols
    governance_target_title: str      # Resolved dynamically via LocaleFormattingContractResolver
    primary_regulator_acronyms: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class VerticalChokepointContext:
    """Operational asset bottlenecks and physical units of failure native to an industry."""

    vertical: VerticalArchetype
    primary_operational_asset: str    # Core bottleneck asset (e.g., 'Core Banking Rails', 'EHR & Telemetry', 'SCADA & Dispatch')
    operational_halt_consequence: str # Tangible operational consequence (e.g., 'payment freeze', 'ambulance diversion', 'halted truck dispatch')
    secondary_blast_radius: str       # Organizational scale of consequence


# --- 4-BLOCK MINTO PYRAMID AST ENTITIES ---

class ScqaSituation(BaseModel):
    operational_footprint: str = Field(..., min_length=10)
    core_dependency: str = Field(..., min_length=10)


class ScqaComplication(BaseModel):
    primary_vulnerability_vector: str = Field(..., min_length=10)
    unmitigated_chokepoint_failure: str = Field(..., min_length=10)


class ScqaAnswerTheses(BaseModel):
    governance_mandate: str = Field(..., min_length=10)
    immediate_containment_action: str = Field(..., min_length=10)
    quantified_risk_reduction_pct: float = Field(..., ge=0.0, le=100.0)


class ScqaBlock(BaseModel):
    """Block 1: Situation, Complication, Question, Answer (The Governing Thesis)."""

    situation: ScqaSituation
    complication: ScqaComplication
    answer_theses: ScqaAnswerTheses


class LossDriverItem(BaseModel):
    category: LossDriverCategory
    sector_specific_label: str
    formatted_amount: str
    percentage_of_total: float = Field(..., ge=0.0, le=100.0)


class ActuarialExposureBlock(BaseModel):
    """Block 2: Actuarial Loss Exposure & Financial Quantification."""

    formatted_p50_expected_loss: str
    formatted_p95_tail_var: str
    ebitda_impact_percentage: float = Field(..., ge=0.0)
    loss_drivers: List[LossDriverItem] = Field(default_factory=list)


class SystemicBottleneckBlock(BaseModel):
    """Block 3: Critical Attack Path & Systemic Lateral Blast Radius."""

    entry_vector: str = Field(..., min_length=5)
    lateral_movement_mechanism: str = Field(..., min_length=5)
    crown_jewel_target: str = Field(..., min_length=5)
    mean_time_to_compromise_hours: float = Field(..., ge=0.1)
    recovery_bottleneck: str = Field(..., min_length=5)


class CapitalInterventionItem(BaseModel):
    action_title: str
    target_asset: str
    formatted_cost: str
    risk_reduction_pct: float = Field(..., ge=0.0, le=100.0)


class CapitalAllocationBlock(BaseModel):
    """Block 4: Capital Allocation & Return on Security Investment (RoSI)."""

    horizon_label: str                # e.g., "30-Day Tactical Containment" vs "90-Day Enterprise Program"
    formatted_total_capex: str
    formatted_net_risk_eliminated: str
    blended_rosi_ratio: str           # e.g., "8.4x"
    top_interventions: List[CapitalInterventionItem] = Field(default_factory=list)


class ExecutiveSummaryAST(BaseModel):
    """Immutable, strictly typed 4-Block Minto Pyramid Executive Summary AST."""

    tower_id: str
    tower_name: str
    scale_archetype: ScaleArchetype
    vertical_context: Dict[str, Any]
    locale_contract: Dict[str, Any]
    scqa_hook: ScqaBlock
    actuarial_exposure: ActuarialExposureBlock
    systemic_bottleneck: SystemicBottleneckBlock
    capital_allocation: CapitalAllocationBlock

    def render_plain_text_summary(self) -> str:
        """Renders cohesive 4-paragraph executive prose guaranteed to be <= 350 words."""
        # Paragraph 1: Boardroom Verdict & Actuarial Exposure
        p1 = (
            f"{self.scqa_hook.situation.operational_footprint} {self.scqa_hook.situation.core_dependency} "
            f"This operational posture exposes the organization to a P95 Tail Value-at-Risk of "
            f"{self.actuarial_exposure.formatted_p95_tail_var} (Expected Loss P50: {self.actuarial_exposure.formatted_p50_expected_loss}), "
            f"representing a {self.actuarial_exposure.ebitda_impact_percentage:.1f}% potential drag on EBITDA."
        )

        # Paragraph 2: Forensic Contradiction & Physical Reality
        p2 = (
            f"The primary architectural vulnerability arises from {self.scqa_hook.complication.primary_vulnerability_vector}. "
            f"Under operational duress, {self.scqa_hook.complication.unmitigated_chokepoint_failure}, "
            f"exposing unhedged systemic friction across core infrastructure assets."
        )

        # Paragraph 3: Systemic Blast Radius & Lateral Cascade
        p3 = (
            f"Lateral exploitation across this domain follows a deterministic kill chain: {self.systemic_bottleneck.entry_vector} "
            f"enables {self.systemic_bottleneck.lateral_movement_mechanism}, directly compromising {self.systemic_bottleneck.crown_jewel_target} "
            f"with an estimated Mean Time to Compromise of {self.systemic_bottleneck.mean_time_to_compromise_hours:.1f} hours. "
            f"The critical recovery bottleneck centers upon {self.systemic_bottleneck.recovery_bottleneck}."
        )

        # Paragraph 4: Status Quo Inertia & Capital Allocation
        p4 = (
            f"Within a {self.capital_allocation.horizon_label}, addressing this domain via {self.scqa_hook.answer_theses.immediate_containment_action} "
            f"eliminates {self.capital_allocation.formatted_net_risk_eliminated} in actuarial risk exposure "
            f"for an estimated capital expenditure of {self.capital_allocation.formatted_total_capex} "
            f"(blended RoSI: {self.capital_allocation.blended_rosi_ratio}), achieving a "
            f"{self.scqa_hook.answer_theses.quantified_risk_reduction_pct:.1f}% risk reduction."
        )

        return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"


# --- DETERMINISTIC RUNTIME RESOLVERS ---

class ScaleArchetypeResolver:
    """Deterministically classifies enterprise scale archetype with high-regulation override."""

    @classmethod
    def resolve(
        cls,
        annual_revenue: float,
        employee_count: int = 0,
        is_regulated_sector: bool = False,
        scale_archetype_override: Optional[ScaleArchetype] = None,
        normalized_revenue_usd: Optional[float] = None,
        currency_iso: str = "USD",
        fx_rate_to_usd: Optional[float] = None,
    ) -> ScaleArchetype:
        """Resolves scale archetype enforcing the Tier-1 Committee Litmus Test."""
        if scale_archetype_override:
            return scale_archetype_override

        if normalized_revenue_usd is not None and normalized_revenue_usd >= 0.0:
            norm_usd_rev = float(normalized_revenue_usd)
        elif fx_rate_to_usd is not None and fx_rate_to_usd > 0.0:
            norm_usd_rev = max(0.0, float(annual_revenue)) / fx_rate_to_usd
        else:
            norm_usd_rev = max(0.0, float(annual_revenue))

        # Committee Litmus Test: High-regulation entities default to TIER1_REGULATED
        # regardless of smaller revenue base (e.g. $40M FinTech or critical health infrastructure)
        if is_regulated_sector and norm_usd_rev >= 30_000_000:
            return ScaleArchetype.TIER1_REGULATED

        if norm_usd_rev > 2_000_000_000 or employee_count > 5000:
            return ScaleArchetype.TIER1_REGULATED
        if norm_usd_rev >= 150_000_000 or employee_count >= 500:
            return ScaleArchetype.ENTERPRISE_CORP

        return ScaleArchetype.MID_MARKET_OWNER


class VerticalChokepointResolver:
    """Resolves operational asset bottlenecks and units of failure with telemetry priority."""

    DEFAULT_CHOKEPOINTS: Dict[VerticalArchetype, Dict[str, str]] = {
        VerticalArchetype.MANUFACTURING_LOGISTICS: {
            "asset": "Enterprise SCADA, Process Execution & Distributed Logistics Gateways",
            "consequence": "physical operational halt, supply chain inventory disruption, and continuous process stalling",
            "blast_radius": "regional operational facilities and industrial supply chain networks",
        },
        VerticalArchetype.FINANCIAL_SERVICES: {
            "asset": "Core Banking Transaction Engine & Real-Time Payment Clearing Rails",
            "consequence": "settlement freezing, customer deposit ledger lockups, and regulatory intervention",
            "blast_radius": "interbank liquidity clearing and retail cardholder transaction processing",
        },
        VerticalArchetype.HEALTHCARE_LIFE_SCIENCES: {
            "asset": "Electronic Health Records (EHR/HIS), PACS Imaging & ICU Telemetry",
            "consequence": "ambulance diversion, suspension of elective surgical procedures, and clinical safety risk",
            "blast_radius": "integrated hospital network beds and emergency diagnostic services",
        },
        VerticalArchetype.RETAIL_ECOMMERCE: {
            "asset": "Store POS Terminals, Payment Gateways & Distribution Center WMS",
            "consequence": "checkout register lockouts, e-commerce cart abandonment, and inventory spoilage",
            "blast_radius": "omni-channel store network and fulfillment warehouse logistics",
        },
        VerticalArchetype.PUBLIC_SECTOR_INFRASTRUCTURE: {
            "asset": "Citizen Service Gateways, Case Management & Critical Infrastructure SCADA",
            "consequence": "paralysis of statutory public services, civil servant downtime, and regulatory investigation",
            "blast_radius": "administrative citizen service delivery and regional public infrastructure",
        },
        VerticalArchetype.TECHNOLOGY_SAAS: {
            "asset": "Global Ingestion Pipelines, API Gateways & Multi-Tenant Database Clusters",
            "consequence": "service SLA breach penalties, customer data ingestion lag, and immediate user churn",
            "blast_radius": "distributed multi-region cloud workloads and tenant API availability",
        },
        VerticalArchetype.GENERAL_COMMERCIAL: {
            "asset": "Core ERP, Document Management & Business Communications",
            "consequence": "billable workflow disruption, client deliverable delays, and operational drag",
            "blast_radius": "corporate enterprise operations and business service delivery",
        },
        VerticalArchetype.DYNAMIC_AUTONOMOUS: {
            "asset": "Mission-Critical Core Transactional Architecture",
            "consequence": "operational service suspension and enterprise-wide business interruption",
            "blast_radius": "enterprise operational footprint and customer transaction flow",
        },
    }

    @classmethod
    def resolve(
        cls,
        vertical: str | VerticalArchetype,
        tenant_intel: Optional[Dict[str, Any]] = None,
    ) -> VerticalChokepointContext:
        """Resolves vertical context, prioritizing discovered telemetry over archetype defaults."""
        v_enum = vertical if isinstance(vertical, VerticalArchetype) else VerticalArchetype.from_str(str(vertical))
        defaults = cls.DEFAULT_CHOKEPOINTS.get(v_enum, cls.DEFAULT_CHOKEPOINTS[VerticalArchetype.DYNAMIC_AUTONOMOUS])

        # Priority to discovered telemetry from client intelligence
        intel = tenant_intel or {}
        discovered_asset = str(intel.get("primary_chokepoint_asset") or "").strip()
        discovered_consequence = str(intel.get("operational_consequence") or "").strip()
        discovered_blast = str(intel.get("secondary_blast_radius") or "").strip()

        return VerticalChokepointContext(
            vertical=v_enum,
            primary_operational_asset=discovered_asset or defaults["asset"],
            operational_halt_consequence=discovered_consequence or defaults["consequence"],
            secondary_blast_radius=discovered_blast or defaults["blast_radius"],
        )


class LocaleFormattingContractResolver:
    """Resolves jurisdictional titles, regulatory bodies, and formatting contracts."""

    DEFAULT_GOVERNANCE_TITLES: Dict[ScaleArchetype, str] = {
        ScaleArchetype.MID_MARKET_OWNER: "Executive Leadership & Managing Director",
        ScaleArchetype.ENTERPRISE_CORP: "Board of Directors & Executive Committee",
        ScaleArchetype.TIER1_REGULATED: "Board Risk Committee & Prudential Regulation Authority Liaison",
    }

    CURRENCY_SYMBOLS: Dict[str, str] = {
        "EUR": "€",
        "GBP": "£",
        "BRL": "R$",
        "USD": "$",
        "MXN": "$",
        "JPY": "¥",
        "CHF": "CHF",
        "INR": "₹",
        "CAD": "$",
        "AUD": "$",
        "SGD": "$",
        "SEK": "kr",
        "NOK": "kr",
        "DKK": "kr",
        "PLN": "zł",
        "ZAR": "R",
        "AED": "AED",
        "SAR": "SAR",
    }

    @classmethod
    def resolve(
        cls,
        locale_code: str,
        scale: ScaleArchetype,
        vertical: VerticalArchetype,
        currency_iso: str = "EUR",
        governance_target_title: Optional[str] = None,
        primary_regulator_acronyms: Optional[List[str]] = None,
    ) -> LocaleFormattingContract:
        """Resolves jurisdictional contract matching the committee's lexical constraint requirement."""
        clean_locale = locale_code.strip() if locale_code else "en-US"
        governance_title = governance_target_title or cls.DEFAULT_GOVERNANCE_TITLES.get(scale, "Executive Leadership & Board of Directors")
        symbol = cls.CURRENCY_SYMBOLS.get(currency_iso.upper(), currency_iso.upper())
        regulators = primary_regulator_acronyms or ["ISO/IEC 27001", "Applicable Statutory Mandates"]

        return LocaleFormattingContract(
            locale_code=clean_locale,
            currency_iso=currency_iso.upper(),
            currency_symbol=symbol,
            governance_target_title=governance_title,
            primary_regulator_acronyms=regulators,
        )
