"""Workforce Digital Dependency Segmentation Resolver (SR 11-7 / Open FAIR).

Implements the 4-tier Bayesian hierarchical resolution:
Level 1: Empirical Interview Ground Truth (structured declarations & lifecycle arithmetic).
Level 2: Verified Audited Regulatory Filings (Non-Financial Statements / 10-K / CMDB / AD).
Level 3: Pre-Flight Web Intelligence (OSINT / Workforce Insights / client_intelligence).
Level 4: Bayesian Sector Prior Fallback (industry_profiles/*.json).

Guarantees strict Euler conservation of headcount and 100% zero-regression isolation.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, Final, Optional, Tuple

# Canonical Actuarial Baseline Priors (Open FAIR / Gartner Endpoint Lifecycle Benchmarks)
DEFAULT_CORPORATE_SEAT_RATIO: Final[float] = 0.60
DEFAULT_SHARED_EDGE_RATIO: Final[float] = 0.20
DEFAULT_ANNUAL_REFRESH_RATE: Final[float] = 0.285  # ~3.5-year enterprise lifecycle (1 / 3.5)
DEFAULT_LIFECYCLE_YEARS: Final[float] = 3.5
DEFAULT_HOURS_PER_REFRESH: Final[float] = 3.0
DEFAULT_IT_SUPPORT_HOURLY_RATE: Final[float] = 50.0
DEFAULT_WORK_MAKE_UP_ELASTICITY: Final[float] = 0.25
DEFAULT_DISRUPTION_DRIVER: Final[str] = "SECTOR_MODAL_BASELINE"


class SegmentationSourceType(StrEnum):
    """Provenance class documenting the epistemological origin of workforce numbers."""

    EMPIRICAL_INTERVIEW_GROUND_TRUTH = "EMPIRICAL_INTERVIEW_GROUND_TRUTH"
    VERIFIED_AUDITED_FILING = "VERIFIED_AUDITED_FILING"
    DISCOVERED_PUBLIC_OSINT = "DISCOVERED_PUBLIC_OSINT"
    ESTIMATED_SECTOR_BASELINE = "ESTIMATED_SECTOR_BASELINE"


@dataclass(frozen=True)
class _SectorBaselinePriors:
    """Internal value object holding resolved sector-level priors."""

    corp_ratio: float
    shared_ratio: float
    refresh_rate: float
    hours_per_unit: float
    hourly_rate: float
    elasticity: float
    disruption_driver: str
    industry_name: str


@dataclass(frozen=True)
class WorkforceProfile:
    """Immutable representation of enterprise workforce digital dependency."""

    total_headcount: int
    corporate_seats: int
    shared_operational_edge_terminals: int
    deskless_field_workers: int
    source_type: SegmentationSourceType
    provenance_citation: str
    confidence_score: float
    annual_refresh_units: int
    annual_toil_hours: float
    annual_toil_cost: float
    work_make_up_elasticity: float
    primary_disruption_driver: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_headcount": self.total_headcount,
            "corporate_seats": self.corporate_seats,
            "shared_operational_edge_terminals": self.shared_operational_edge_terminals,
            "deskless_field_workers": self.deskless_field_workers,
            "source_type": self.source_type.value,
            "provenance_citation": self.provenance_citation,
            "confidence_score": self.confidence_score,
            "annual_refresh_units": self.annual_refresh_units,
            "annual_toil_hours": round(self.annual_toil_hours, 1),
            "annual_toil_cost": round(self.annual_toil_cost, 2),
            "work_make_up_elasticity": self.work_make_up_elasticity,
            "primary_disruption_driver": self.primary_disruption_driver,
        }


class WorkforceSegmentationResolver:
    """Pure domain service resolving the 4-tier Bayesian workforce hierarchy."""

    @classmethod
    def resolve(
        cls,
        total_headcount: int,
        client_telemetry: Optional[Dict[str, Any]] = None,
        client_intelligence: Optional[Dict[str, Any]] = None,
        industry_profile: Optional[Dict[str, Any]] = None,
    ) -> WorkforceProfile:
        headcount = max(1, int(total_headcount))
        telemetry = client_telemetry or {}
        intel = client_intelligence or {}
        profile = industry_profile or {}
        priors = cls._extract_sector_priors(profile)

        # LEVEL 1: Empirical Interview Ground Truth & Lifecycle Arithmetic
        l1_profile = cls._try_resolve_level_1_interview(headcount, telemetry, priors)
        if l1_profile is not None:
            return l1_profile

        # LEVEL 2: Verified Audited Regulatory Filings (10-K / Non-Financial Filings / AD)
        l2_profile = cls._try_resolve_level_2_filings(headcount, telemetry, intel, priors)
        if l2_profile is not None:
            return l2_profile

        # LEVEL 3: Pre-Flight Web Intelligence (OSINT / Public Footprint)
        l3_profile = cls._try_resolve_level_3_osint(headcount, intel, priors)
        if l3_profile is not None:
            return l3_profile

        # LEVEL 4: Bayesian Sector Prior Fallback (Safe Default)
        return cls._resolve_level_4_sector_prior(headcount, priors)

    @staticmethod
    def _extract_sector_priors(profile: Dict[str, Any]) -> _SectorBaselinePriors:
        """Extracts sector-specific parameters with safe fallbacks to canonical constants."""
        digital_profile = profile.get("workforce_digital_profile") or {}
        return _SectorBaselinePriors(
            corp_ratio=cls_safe_float(
                digital_profile.get("corporate_seat_ratio"), DEFAULT_CORPORATE_SEAT_RATIO
            ),
            shared_ratio=cls_safe_float(
                digital_profile.get("shared_operational_edge_ratio"), DEFAULT_SHARED_EDGE_RATIO
            ),
            refresh_rate=cls_safe_float(
                digital_profile.get("annual_endpoint_refresh_rate"), DEFAULT_ANNUAL_REFRESH_RATE
            ),
            hours_per_unit=cls_safe_float(
                digital_profile.get("hours_per_manual_refresh"), DEFAULT_HOURS_PER_REFRESH
            ),
            hourly_rate=cls_safe_float(
                digital_profile.get("typical_it_support_hourly_rate"), DEFAULT_IT_SUPPORT_HOURLY_RATE
            ),
            elasticity=cls_safe_float(
                digital_profile.get("work_make_up_elasticity"), DEFAULT_WORK_MAKE_UP_ELASTICITY
            ),
            disruption_driver=str(
                digital_profile.get("primary_disruption_driver") or DEFAULT_DISRUPTION_DRIVER
            ),
            industry_name=str(profile.get("industry") or "General Enterprise"),
        )

    @staticmethod
    def _reconcile_headcount_partition(
        headcount: int, raw_corporate: int, raw_shared: int
    ) -> Tuple[int, int, int]:
        """Enforces strict Euler conservation: corporate + shared + deskless == headcount."""
        corp_val = max(1, min(headcount, int(raw_corporate)))
        remaining_after_corp = max(0, headcount - corp_val)
        shared_val = max(0, min(remaining_after_corp, int(raw_shared)))
        deskless_val = max(0, headcount - corp_val - shared_val)
        return corp_val, shared_val, deskless_val

    @staticmethod
    def _parse_localized_integer(token: str) -> int:
        """Safely parses integer tokens with thousand separators (e.g. '1,200' or '1.200')."""
        cleaned = token.strip()
        if re.match(r"^\d{1,3}(?:[.,]\d{3})+$", cleaned):
            cleaned = re.sub(r"[.,]", "", cleaned)
        else:
            cleaned = cleaned.replace(",", ".")
        return int(round(float(cleaned)))

    @classmethod
    def _try_resolve_level_1_interview(
        cls,
        headcount: int,
        telemetry: Dict[str, Any],
        priors: _SectorBaselinePriors,
    ) -> Optional[WorkforceProfile]:
        """Inspects technical interviews for explicit fleet declarations or refresh arithmetic."""
        direct = telemetry.get("interview_workforce_declarations") or telemetry.get("workforce_split")
        if isinstance(direct, dict):
            corp = direct.get("corporate_seats")
            if corp is None:
                corp = direct.get("office_workers")
            if corp is not None:
                raw_shared = direct.get("shared_terminals")
                if raw_shared is None:
                    raw_shared = direct.get("edge_terminals", 0)
                corp_val, shared_val, deskless = cls._reconcile_headcount_partition(
                    headcount, int(corp), int(raw_shared)
                )
                refresh_raw = direct.get("annual_refresh_units")
                refresh = (
                    max(0, int(refresh_raw))
                    if refresh_raw is not None
                    else int(round(corp_val * priors.refresh_rate))
                )
                hours_per_unit = cls_safe_float(
                    direct.get("hours_per_refresh"), priors.hours_per_unit
                )
                rate = cls_safe_float(
                    direct.get("it_support_hourly_rate"), priors.hourly_rate
                )
                elasticity = cls_safe_float(
                    direct.get("work_make_up_elasticity"), priors.elasticity
                )
                driver = str(
                    direct.get("primary_disruption_driver") or priors.disruption_driver
                )
                total_hours = refresh * hours_per_unit
                total_cost = total_hours * rate
                return WorkforceProfile(
                    total_headcount=headcount,
                    corporate_seats=corp_val,
                    shared_operational_edge_terminals=shared_val,
                    deskless_field_workers=deskless,
                    source_type=SegmentationSourceType.EMPIRICAL_INTERVIEW_GROUND_TRUTH,
                    provenance_citation="Technical interview direct discovery with IT Leadership",
                    confidence_score=0.95,
                    annual_refresh_units=refresh,
                    annual_toil_hours=total_hours,
                    annual_toil_cost=total_cost,
                    work_make_up_elasticity=elasticity,
                    primary_disruption_driver=driver,
                )

        # Textual search in qualitative interview corpus (Language-agnostic and Technical English patterns)
        corpus = str(telemetry).lower()
        m_fleet = re.search(
            r"(?:fleet|flota)\s+(?:total\s+)?(?:of|de)\s+(?:approximately|around|about|unos)?\s*~?(\d+(?:[.,]\d{3})*)\s*(?:devices|workstations|laptops|endpoints|computers|equipos|ordenadores|port[a\u00e1]tiles)",
            corpus,
        )
        m_renew = re.search(
            r"(?:annual\s+)?(?:refresh|renewal|provisioning|preparation|renovaci[o\u00f3]n|preparaci[o\u00f3]n)\s+(?:anual\s+)?(?:of|de)\s+(?:approximately|around|about|los|unos)?\s*~?(\d+(?:[.,]\d{3})*)\s*(?:laptops|workstations|devices|endpoints|computers|port[a\u00e1]tiles|ordenadores|equipos)",
            corpus,
        )
        m_kiosk = re.search(
            r"(?:more\s+than|over|approximately|around|about|m[a\u00e1]s\s+de|unos)\s+(\d+(?:[.,]\d{3})*)\s*(?:shared\s+terminals|industrial\s+kiosks|kiosks|terminals|terminales|quioscos|quioscos\s+industriales)",
            corpus,
        )

        if m_fleet or m_renew:
            lifecycle_years = (
                (1.0 / priors.refresh_rate) if priors.refresh_rate > 0 else DEFAULT_LIFECYCLE_YEARS
            )
            raw_corp = (
                cls._parse_localized_integer(m_fleet.group(1))
                if m_fleet
                else int(round(cls._parse_localized_integer(m_renew.group(1)) * lifecycle_years))
            )
            raw_shared = (
                cls._parse_localized_integer(m_kiosk.group(1))
                if m_kiosk
                else int(round(headcount * priors.shared_ratio))
            )
            corp_val, shared_val, deskless = cls._reconcile_headcount_partition(
                headcount, raw_corp, raw_shared
            )

            refresh_units = (
                cls._parse_localized_integer(m_renew.group(1))
                if m_renew
                else int(round(corp_val * priors.refresh_rate))
            )
            m_hours = re.search(
                r"(\d+(?:[.,]\d+)?)\s*hours?\s+(?:of|de)\s+(?:manual\s+)?(?:dedication|effort|technician|provisioning|dedicaci[o\u00f3]n|t[e\u00e9]cnico)",
                corpus,
            )
            hours_per_unit = (
                float(m_hours.group(1).replace(",", "."))
                if m_hours
                else priors.hours_per_unit
            )
            total_hours = refresh_units * hours_per_unit
            total_cost = total_hours * priors.hourly_rate

            return WorkforceProfile(
                total_headcount=headcount,
                corporate_seats=corp_val,
                shared_operational_edge_terminals=shared_val,
                deskless_field_workers=deskless,
                source_type=SegmentationSourceType.EMPIRICAL_INTERVIEW_GROUND_TRUTH,
                provenance_citation="Forensic interview lifecycle arithmetic (renewals × lifespan)",
                confidence_score=0.92,
                annual_refresh_units=refresh_units,
                annual_toil_hours=total_hours,
                annual_toil_cost=total_cost,
                work_make_up_elasticity=priors.elasticity,
                primary_disruption_driver=priors.disruption_driver,
            )

        return None

    @classmethod
    def _try_resolve_level_2_filings(
        cls,
        headcount: int,
        telemetry: Dict[str, Any],
        intel: Dict[str, Any],
        priors: _SectorBaselinePriors,
    ) -> Optional[WorkforceProfile]:
        """Inspects documentary filings (Non-Financial Disclosures / 10-K / Intune / AD)."""
        doc_data = telemetry.get("regulatory_filings") or intel.get("regulatory_filings") or {}
        if isinstance(doc_data, dict) and doc_data.get("corporate_workforce") is not None:
            raw_shared = int(doc_data.get("shared_terminals") or 0)
            corp, shared, deskless = cls._reconcile_headcount_partition(
                headcount, int(doc_data["corporate_workforce"]), raw_shared
            )
            refresh = int(round(corp * priors.refresh_rate))
            total_hours = refresh * priors.hours_per_unit
            total_cost = total_hours * priors.hourly_rate
            citation = str(
                doc_data.get("citation") or "Audited Non-Financial Information Statement"
            )
            return WorkforceProfile(
                total_headcount=headcount,
                corporate_seats=corp,
                shared_operational_edge_terminals=shared,
                deskless_field_workers=deskless,
                source_type=SegmentationSourceType.VERIFIED_AUDITED_FILING,
                provenance_citation=citation,
                confidence_score=0.90,
                annual_refresh_units=refresh,
                annual_toil_hours=total_hours,
                annual_toil_cost=total_cost,
                work_make_up_elasticity=priors.elasticity,
                primary_disruption_driver="AUDITED_REGULATORY_DISCLOSURE",
            )
        return None

    @classmethod
    def _try_resolve_level_3_osint(
        cls,
        headcount: int,
        intel: Dict[str, Any],
        priors: _SectorBaselinePriors,
    ) -> Optional[WorkforceProfile]:
        """Inspects pre-flight web intelligence / LinkedIn / client_intelligence."""
        wf_intel = (
            (intel.get("profile") or {}).get("workforce_intelligence")
            or intel.get("workforce_intelligence")
        )
        if isinstance(wf_intel, dict) and wf_intel.get("corporate_workforce") is not None:
            raw_shared = int(wf_intel.get("shared_edge_terminals") or 0)
            corp, shared, deskless = cls._reconcile_headcount_partition(
                headcount, int(wf_intel["corporate_workforce"]), raw_shared
            )
            refresh = int(round(corp * priors.refresh_rate))
            total_hours = refresh * priors.hours_per_unit
            total_cost = total_hours * priors.hourly_rate
            citation = str(
                wf_intel.get("evidence_citation") or "OSINT Public Footprint Discovery"
            )
            return WorkforceProfile(
                total_headcount=headcount,
                corporate_seats=corp,
                shared_operational_edge_terminals=shared,
                deskless_field_workers=deskless,
                source_type=SegmentationSourceType.DISCOVERED_PUBLIC_OSINT,
                provenance_citation=citation,
                confidence_score=0.80,
                annual_refresh_units=refresh,
                annual_toil_hours=total_hours,
                annual_toil_cost=total_cost,
                work_make_up_elasticity=priors.elasticity,
                primary_disruption_driver="PUBLIC_INTELLIGENCE_DISCOVERY",
            )
        return None

    @classmethod
    def _resolve_level_4_sector_prior(
        cls,
        headcount: int,
        priors: _SectorBaselinePriors,
    ) -> WorkforceProfile:
        """Fallback to Bayesian Sector Prior from industry profile."""
        raw_corp = max(1, int(round(headcount * priors.corp_ratio)))
        raw_shared = int(round(headcount * priors.shared_ratio))
        corp, shared, deskless = cls._reconcile_headcount_partition(
            headcount, raw_corp, raw_shared
        )
        refresh = int(round(corp * priors.refresh_rate))
        total_hours = refresh * priors.hours_per_unit
        total_cost = total_hours * priors.hourly_rate
        citation = f"Bayesian Sector Prior ({priors.industry_name} Baseline Distribution)"

        return WorkforceProfile(
            total_headcount=headcount,
            corporate_seats=corp,
            shared_operational_edge_terminals=shared,
            deskless_field_workers=deskless,
            source_type=SegmentationSourceType.ESTIMATED_SECTOR_BASELINE,
            provenance_citation=citation,
            confidence_score=0.65,
            annual_refresh_units=refresh,
            annual_toil_hours=total_hours,
            annual_toil_cost=total_cost,
            work_make_up_elasticity=priors.elasticity,
            primary_disruption_driver=priors.disruption_driver,
        )


def cls_safe_float(value: Any, default: float) -> float:
    """Safely converts an arbitrary value to a finite float, preserving 0.0 when explicitly set."""
    if value is None:
        return default
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) and parsed >= 0.0 else default
    except (ValueError, TypeError):
        return default
