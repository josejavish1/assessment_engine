"""Workforce Digital Dependency Segmentation Resolver (SR 11-7 / Open FAIR).

Implements the 4-tier Bayesian hierarchical resolution:
Level 1: Empirical Interview Ground Truth (forensic declarations & refresh arithmetic).
Level 2: Verified Audited Regulatory Filings (EINF / 10-K / CMDB / Active Directory).
Level 3: Pre-Flight Web Intelligence (OSINT / LinkedIn Insights / client_intelligence).
Level 4: Bayesian Sector Prior Fallback (industry_profiles/*.json).

Guarantees 100% zero-regression isolation: hermetically sealed, pure domain logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, Optional


class SegmentationSourceType(StrEnum):
    """Provenance class documenting the epistemological origin of workforce numbers."""

    EMPIRICAL_INTERVIEW_GROUND_TRUTH = "EMPIRICAL_INTERVIEW_GROUND_TRUTH"
    VERIFIED_AUDITED_FILING = "VERIFIED_AUDITED_FILING"
    DISCOVERED_PUBLIC_OSINT = "DISCOVERED_PUBLIC_OSINT"
    ESTIMATED_SECTOR_BASELINE = "ESTIMATED_SECTOR_BASELINE"


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

        # ------------------------------------------------------------------
        # LEVEL 1: Empirical Interview Ground Truth & Lifecycle Arithmetic
        # ------------------------------------------------------------------
        l1_profile = cls._try_resolve_level_1_interview(headcount, telemetry)
        if l1_profile is not None:
            return l1_profile

        # ------------------------------------------------------------------
        # LEVEL 2: Verified Audited Regulatory Filings (EINF / 10-K / AD)
        # ------------------------------------------------------------------
        l2_profile = cls._try_resolve_level_2_filings(headcount, telemetry, intel)
        if l2_profile is not None:
            return l2_profile

        # ------------------------------------------------------------------
        # LEVEL 3: Pre-Flight Web Intelligence (OSINT / Public Footprint)
        # ------------------------------------------------------------------
        l3_profile = cls._try_resolve_level_3_osint(headcount, intel)
        if l3_profile is not None:
            return l3_profile

        # ------------------------------------------------------------------
        # LEVEL 4: Bayesian Sector Prior Fallback (Safe Default)
        # ------------------------------------------------------------------
        return cls._resolve_level_4_sector_prior(headcount, profile)

    @classmethod
    def _try_resolve_level_1_interview(
        cls,
        headcount: int,
        telemetry: Dict[str, Any],
    ) -> Optional[WorkforceProfile]:
        """Inspects technical interviews for explicit fleet declarations or refresh arithmetic."""
        # 1. Direct explicit telemetry
        direct = telemetry.get("interview_workforce_declarations") or telemetry.get("workforce_split")
        if isinstance(direct, dict):
            corp = direct.get("corporate_seats") or direct.get("office_workers")
            if corp is not None:
                corp_val = max(1, min(headcount, int(corp)))
                shared_val = int(direct.get("shared_terminals") or direct.get("edge_terminals") or 0)
                deskless = max(0, headcount - corp_val - shared_val)
                refresh = int(direct.get("annual_refresh_units") or round(corp_val * 0.285))
                hours_per_unit = float(direct.get("hours_per_refresh") or 3.5)
                rate = float(direct.get("it_support_hourly_rate") or 45.0)
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
                    work_make_up_elasticity=0.30,
                    primary_disruption_driver="PLANT_DISPATCH_AND_LOGISTICS",
                )

        # 2. Textual search in qualitative interview corpus (e.g. Molins 350 renewals * 3.5 years = 1,200)
        corpus = str(telemetry).lower()
        # Pattern: "renovacion anual de ~?(\d+) portatiles" or "flota total de ~?(\d+) (?:equipos|ordenadores|portatiles)"
        m_fleet = re.search(
            r"flota\s+(?:total\s+)?de\s+(?:aproximadamente\s+|unos\s+)?~?(\d+(?:\.\d+)?)\s*(?:equipos|ordenadores|port[a\u00e1]tiles)",
            corpus,
        )
        m_renew = re.search(
            r"(?:renovaci[o\u00f3]n|preparaci[o\u00f3]n)\s+(?:anual\s+)?de\s+(?:los\s+)?(?:aproximadamente\s+|unos\s+)?~?(\d+(?:\.\d+)?)\s*(?:port[a\u00e1]tiles|ordenadores|equipos)",
            corpus,
        )
        m_kiosk = re.search(
            r"(?:m[a\u00e1]s\s+de|unos|aproximadamente)\s+(\d+(?:\.\d+)?)\s*(?:terminales|quioscos|quioscos industriales)",
            corpus,
        )

        if m_fleet or m_renew:
            corp_val = int(float(m_fleet.group(1).replace(".", ""))) if m_fleet else (
                int(float(m_renew.group(1).replace(".", "")) * 3.5) if m_renew else int(headcount * 0.30)
            )
            corp_val = max(1, min(headcount, corp_val))
            shared_val = int(float(m_kiosk.group(1).replace(".", ""))) if m_kiosk else int(headcount * 0.20)
            deskless = max(0, headcount - corp_val - shared_val)

            refresh_units = int(float(m_renew.group(1).replace(".", ""))) if m_renew else int(round(corp_val / 3.5))
            m_hours = re.search(r"(\d+(?:[.,]\d+)?)\s*horas?\s+de\s+(?:dedicaci[o\u00f3]n|t[e\u00e9]cnico)", corpus)
            hours_per_unit = float(m_hours.group(1).replace(",", ".")) if m_hours else 3.5
            total_hours = refresh_units * hours_per_unit
            total_cost = total_hours * 45.0  # Standard IT tech rate

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
                work_make_up_elasticity=0.30,
                primary_disruption_driver="PLANT_DISPATCH_AND_LOGISTICS",
            )

        return None

    @classmethod
    def _try_resolve_level_2_filings(
        cls,
        headcount: int,
        telemetry: Dict[str, Any],
        intel: Dict[str, Any],
    ) -> Optional[WorkforceProfile]:
        """Inspects documentary filings (EINF / 10-K / Intune / AD)."""
        doc_data = telemetry.get("regulatory_filings") or intel.get("regulatory_filings") or {}
        if isinstance(doc_data, dict) and doc_data.get("corporate_workforce") is not None:
            corp = max(1, min(headcount, int(doc_data["corporate_workforce"])))
            shared = int(doc_data.get("shared_terminals") or 0)
            deskless = max(0, headcount - corp - shared)
            refresh = int(round(corp * 0.285))
            total_hours = refresh * 3.0
            total_cost = total_hours * 50.0
            citation = str(doc_data.get("citation") or "Audited Non-Financial Information Statement (EINF)")
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
                work_make_up_elasticity=0.25,
                primary_disruption_driver="AUDITED_REGULATORY_DISCLOSURE",
            )
        return None

    @classmethod
    def _try_resolve_level_3_osint(
        cls,
        headcount: int,
        intel: Dict[str, Any],
    ) -> Optional[WorkforceProfile]:
        """Inspects pre-flight web intelligence / LinkedIn / client_intelligence."""
        wf_intel = (intel.get("profile") or {}).get("workforce_intelligence") or intel.get("workforce_intelligence")
        if isinstance(wf_intel, dict) and wf_intel.get("corporate_workforce") is not None:
            corp = max(1, min(headcount, int(wf_intel["corporate_workforce"])))
            shared = int(wf_intel.get("shared_edge_terminals") or 0)
            deskless = max(0, headcount - corp - shared)
            refresh = int(round(corp * 0.285))
            total_hours = refresh * 3.0
            total_cost = total_hours * 50.0
            citation = str(wf_intel.get("evidence_citation") or "OSINT Public Footprint Discovery")
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
                work_make_up_elasticity=0.25,
                primary_disruption_driver="PUBLIC_INTELLIGENCE_DISCOVERY",
            )
        return None

    @classmethod
    def _resolve_level_4_sector_prior(
        cls,
        headcount: int,
        profile: Dict[str, Any],
    ) -> WorkforceProfile:
        """Fallback to Bayesian Sector Prior from industry profile."""
        digital_profile = profile.get("workforce_digital_profile") or {}
        corp_ratio = float(digital_profile.get("corporate_seat_ratio") or 0.60)
        shared_ratio = float(digital_profile.get("shared_operational_edge_ratio") or 0.20)
        deskless_ratio = float(digital_profile.get("deskless_field_ratio") or 0.20)
        refresh_rate = float(digital_profile.get("annual_endpoint_refresh_rate") or 0.285)
        hours_per_unit = float(digital_profile.get("hours_per_manual_refresh") or 3.0)
        hourly_rate = float(digital_profile.get("typical_it_support_hourly_rate") or 50.0)
        elasticity = float(digital_profile.get("work_make_up_elasticity") or 0.25)
        driver = str(digital_profile.get("primary_disruption_driver") or "SECTOR_MODAL_BASELINE")

        corp = max(1, int(round(headcount * corp_ratio)))
        shared = int(round(headcount * shared_ratio))
        deskless = max(0, headcount - corp - shared)
        refresh = int(round(corp * refresh_rate))
        total_hours = refresh * hours_per_unit
        total_cost = total_hours * hourly_rate

        industry_name = str(profile.get("industry") or "General Enterprise")
        citation = f"Bayesian Sector Prior ({industry_name} Baseline Distribution)"

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
            work_make_up_elasticity=elasticity,
            primary_disruption_driver=driver,
        )
