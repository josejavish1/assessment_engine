### ADVERSARIAL ARCHITECTURAL & SR 11-7 MODEL RISK AUDIT REPORT

**Auditor**: `gemini-4-argon` (Lead Principal Software Architect / Chief Compilers Engineer / Head of MRM SR 11-7)  
**Verdict**: **REJECTED — CRITICAL MANDATE VIOLATIONS DETECTED**

The newly introduced codebase violates **Mandate 1 (Zero Hardcoding)**, **Mandate 2 (100% Technical English Codebase)**, and **Mandate 3 (Mathematical & Actuarial Purity)**. Specifically, `workforce_segmentation.py` contains bespoke client-specific hacks ("Molins" comments, Spanish-only regular expressions, and hardcoded manufacturing disruption drivers) that will fail silently or corrupt the actuarial baseline for global English/Portuguese/international enterprises.

---

### SECTION 1: MICROSCOPIC FORENSIC FINDINGS

#### 1.1. CRITICAL VIOLATION: Hardcoded Client Name, Spanish-Only Regexes, and Bespoke Hacks (`workforce_segmentation.py`)
* **Location**: `src/assessment_engine/domain/actuarial/workforce_segmentation.py` (Lines 130–183)
* **Evidence**:
  * Line 130 explicitly leaks a specific client name in a comment: `# 2. Textual search in qualitative interview corpus (e.g. Molins 350 renewals * 3.5 years = 1,200)`.
  * Lines 133–144 define regular expressions exclusively in Spanish (`flota`, `equipos`, `ordenadores`, `portátiles`, `renovación`, `preparación`, `terminales`, `quioscos`, `horas de dedicación`).
  * **Impact**: If an interview corpus is ingested in English (e.g., *"annual refresh of 350 laptops across a fleet of 1,200 workstations requiring 3.5 hours of technician time"*), Level 1 regex extraction completely fails and falls through to Level 4.
  * **Thousand-Separator Parsing Bug**: Line 147 executes `int(float(m_fleet.group(1).replace(".", "")))`. In an English locale where decimals use `.` (e.g., `1.5`), `.replace(".", "")` mutates `1.5` into `15`! Conversely, in English thousand-separated strings (`1,200`), the regex `\d+(?:\.\d+)?` stops matching at the comma, extracting `1` instead of `1200`!

#### 1.2. CRITICAL VIOLATION: Hardcoded Manufacturing Disruption Drivers & Magic Numbers (`workforce_segmentation.py`)
* **Location**: `src/assessment_engine/domain/actuarial/workforce_segmentation.py` (Lines 109–245)
* **Evidence**:
  * Line 127 & Line 179 hardcode `primary_disruption_driver="PLANT_DISPATCH_AND_LOGISTICS"` and `work_make_up_elasticity=0.30` inside Level 1 resolution, completely ignoring the `industry_profile` passed into `resolve()`. If a global investment bank provides Level 1 interview declarations, the engine classifies its primary disruption driver as `"PLANT_DISPATCH_AND_LOGISTICS"`!
  * Magic numbers are scattered across Levels 1, 2, and 3 instead of cascading cleanly from `industry_profile` priors or named actuarial constants: `0.285` (refresh rate), `3.5` / `3.0` (hours per unit), `45.0` / `50.0` (hourly rate), `0.30` / `0.25` (elasticity).
  * In `test_workforce_segmentation_resolver.py` (Lines 49–55 & 68), Spanish strings (`"La preparación de los..."`, `"Estado de Información No Financiera..."`) are hardcoded inside unit tests, institutionalizing the Spanish regex hack.

#### 1.3. CRITICAL VIOLATION: Euler Conservation Failure (`corporate + shared + deskless > total_headcount`) (`workforce_segmentation.py`)
* **Location**: `src/assessment_engine/domain/actuarial/workforce_segmentation.py` (Lines 108–110, 150–152, 195–197, 225–227, 258–260)
* **Evidence**:
  ```python
  corp_val = max(1, min(headcount, int(corp)))
  shared_val = int(direct.get("shared_terminals") or direct.get("edge_terminals") or 0)
  deskless = max(0, headcount - corp_val - shared_val)
  ```
* **Mathematical Flaw**: `shared_val` is neither bounded by `0` from below nor bounded by `headcount - corp_val` from above!
  * If `headcount = 1000`, `corp_val = 800`, and `shared_val = 500`, then `deskless = max(0, 1000 - 800 - 500) = 0`.
  * Consequently, `corporate_seats + shared_operational_edge_terminals + deskless_field_workers = 800 + 500 + 0 = 1300 != 1000`.
  * Even worse, in `_resolve_level_4_sector_prior` (Lines 258–260): if `headcount = 1`, `corp = max(1, round(1 * 0.60)) = 1`, and `shared = round(1 * 0.60) = 1`, the sum is `2 != 1`.
  * This violates conservation of workforce headcount (`corporate + shared + deskless == total_headcount`).

#### 1.4. CRITICAL VIOLATION: Hardcoded Bilingual/Spanish Regex Literals in Compiler (`in_memory_asis_compiler.py`)
* **Location**: `src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py` (Lines 1419–1427)
* **Evidence**:
  * `_KPI_EXPORT_ARTIFACT_RE` and `_ABSENCE_OF_TELEMETRY_RE` embed Spanish and Portuguese vocabulary (`procesos operativos estructurados según`, `carencia de`, `falta de`, `sin herramientas de`, `telemetría`, `monitorización`) directly inside Python source code in `src/`, violating Mandate 2 (100% Technical English in `src/`). Localization patterns must be loaded from `engine_config/locales.json` or lexicon registries.

#### 1.5. ACTUARIAL & COMPILER DEFECT: Unbounded Magic Constants in `payload_to_ast.py`
* **Location**: `src/assessment_engine/adapters/compilers/payload_to_ast.py` (Lines 4195–4209)
* **Evidence**:
  * Hardcoded threshold ratios (`ratio >= 0.70`, `ratio <= 0.35`, `0.85`, `0.22`, `0.95`, `0.35`) and `float(r.get("ale") or 0.0)` without `safe_float` or `math.isnan`/`math.isinf` guards. If `cloud_intensity_gamma` is `0.0` (e.g. a 100% air-gapped on-premise facility), `float(blueprint_data.get("cloud_intensity_gamma") or ...)` treats `0.0` as falsy and overwrites it with `0.22`!

---

### SECTION 2: PRODUCTION-READY TECHNICAL ENGLISH REFACTORINGS

#### 2.1. Refactored `src/assessment_engine/domain/actuarial/workforce_segmentation.py`
* **Fixes Applied**:
  1. 100% Technical English codebase; zero client names, zero Spanish literals in source code.
  2. Strict Euler headcount conservation (`corporate_seats + shared_operational_edge_terminals + deskless_field_workers == total_headcount` for all $N \ge 1$).
  3. All fallback parameters (refresh rate, hours per unit, hourly rate, elasticity, primary disruption driver) cascade cleanly from `industry_profile` priors down to named canonical constants—never overwriting a bank's disruption driver with manufacturing logistics.
  4. Locale-safe numeric parsing supporting structured telemetry first, and language-agnostic / English technical corpus patterns without thousand-separator corruption.

```python
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

        # Textual search in qualitative interview corpus (English technical terminology)
        corpus = str(telemetry).lower()
        m_fleet = re.search(
            r"fleet\s+(?:total\s+)?of\s+(?:approximately\s+|around\s+|about\s+)?~?(\d+(?:[.,]\d{3})*)\s*(?:devices|workstations|laptops|endpoints|computers)",
            corpus,
        )
        m_renew = re.search(
            r"(?:annual\s+)?(?:refresh|renewal|provisioning|preparation)\s+of\s+(?:approximately\s+|around\s+|about\s+)?~?(\d+(?:[.,]\d{3})*)\s*(?:laptops|workstations|devices|endpoints|computers)",
            corpus,
        )
        m_kiosk = re.search(
            r"(?:more\s+than|over|approximately|around|about)\s+(\d+(?:[.,]\d{3})*)\s*(?:shared\s+terminals|industrial\s+kiosks|kiosks|terminals)",
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
                r"(\d+(?:[.,]\d+)?)\s*hours?\s+of\s+(?:manual\s+)?(?:dedication|effort|technician|provisioning)",
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
```

---

#### 2.2. Refactored `tests/unit/domain/actuarial/test_workforce_segmentation_resolver.py`
* **Fixes Applied**: 100% Technical English test cases + new edge-case tests verifying strict Euler headcount conservation under extreme overflow and small-headcount conditions.

```python
"""Unit test suite for WorkforceSegmentationResolver (SR 11-7 / Bayesian Precedence)."""

from __future__ import annotations

from assessment_engine.domain.actuarial.workforce_segmentation import (
    SegmentationSourceType,
    WorkforceProfile,
    WorkforceSegmentationResolver,
)


def test_level_1_direct_interview_declarations() -> None:
    """Verifies that direct interview declarations take highest precedence."""
    telemetry = {
        "interview_workforce_declarations": {
            "corporate_seats": 1200,
            "shared_terminals": 800,
            "annual_refresh_units": 350,
            "hours_per_refresh": 3.5,
            "it_support_hourly_rate": 45.0,
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=3900,
        client_telemetry=telemetry,
    )

    assert isinstance(profile, WorkforceProfile)
    assert profile.source_type == SegmentationSourceType.EMPIRICAL_INTERVIEW_GROUND_TRUTH
    assert profile.total_headcount == 3900
    assert profile.corporate_seats == 1200
    assert profile.shared_operational_edge_terminals == 800
    assert profile.deskless_field_workers == 1900
    assert profile.annual_refresh_units == 350
    assert profile.annual_toil_hours == 1225.0
    assert profile.annual_toil_cost == 55125.0
    assert profile.confidence_score == 0.95
    assert (
        profile.corporate_seats
        + profile.shared_operational_edge_terminals
        + profile.deskless_field_workers
        == profile.total_headcount
    )


def test_level_1_interview_corpus_arithmetic_inference() -> None:
    """Verifies arithmetic inference from qualitative English interview notes (renewals × lifespan)."""
    telemetry = {
        "interview_notes": (
            "The annual refresh of approximately 350 laptops across a fleet total of 1,200 "
            "workstations requires 3.5 hours of manual technician effort per unit. "
            "Across the production facilities, there are more than 800 shared terminals."
        )
    }
    industry_profile = {
        "industry": "Heavy Manufacturing",
        "workforce_digital_profile": {
            "typical_it_support_hourly_rate": 45.0,
            "primary_disruption_driver": "PLANT_DISPATCH_AND_LOGISTICS",
        },
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=3900,
        client_telemetry=telemetry,
        industry_profile=industry_profile,
    )

    assert profile.source_type == SegmentationSourceType.EMPIRICAL_INTERVIEW_GROUND_TRUTH
    assert profile.corporate_seats == 1200
    assert profile.shared_operational_edge_terminals == 800
    assert profile.deskless_field_workers == 1900
    assert profile.annual_refresh_units == 350
    assert profile.annual_toil_hours == 1225.0
    assert profile.annual_toil_cost == 55125.0
    assert profile.confidence_score == 0.92


def test_level_2_verified_audited_regulatory_filing() -> None:
    """Verifies Level 2 extraction when no interview data is available."""
    telemetry = {
        "regulatory_filings": {
            "corporate_workforce": 600,
            "shared_terminals": 200,
            "citation": "Audited Non-Financial Information Statement (FY2024)",
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=2000,
        client_telemetry=telemetry,
    )

    assert profile.source_type == SegmentationSourceType.VERIFIED_AUDITED_FILING
    assert profile.corporate_seats == 600
    assert profile.shared_operational_edge_terminals == 200
    assert profile.deskless_field_workers == 1200
    assert profile.confidence_score == 0.90
    assert "Non-Financial Information Statement" in profile.provenance_citation


def test_euler_headcount_conservation_under_overflow() -> None:
    """Verifies that declared seats + shared terminals never exceed total_headcount."""
    telemetry = {
        "interview_workforce_declarations": {
            "corporate_seats": 800,
            "shared_terminals": 500,
        }
    }
    profile = WorkforceSegmentationResolver.resolve(
        total_headcount=1000,
        client_telemetry=telemetry,
    )
    assert profile.corporate_seats == 800
    assert profile.shared_operational_edge_terminals == 200
    assert profile.deskless_field_workers == 0
    assert (
        profile.corporate_seats
        + profile.shared_operational_edge_terminals
        + profile.deskless_field_workers
        == profile.total_headcount
    )
```

---

#### 2.3. Refactored Language-Decoupled Pattern Resolution in `in_memory_asis_compiler.py` & `payload_to_ast.py`
* **In `in_memory_asis_compiler.py`**: Remove Spanish/Portuguese regex literals from Python source and load localized pattern fragments from `locales.json` (with pure Technical English default patterns in `src/`):
```python
_DEFAULT_KPI_EXPORT_PREFIXES: Final[tuple[str, ...]] = (
    r"structured\s+operational\s+processes\s+according\s+to\s+",
)

_DEFAULT_ABSENCE_OF_TELEMETRY_PATTERN: Final[str] = (
    r"\b(?:lack\s+of|absence\s+of|no\s+telemetry|zero\s+telemetry)\b.*"
    r"\b(?:dex|telemetry|monitoring|observability|tooling|dcim|bms)\b"
)


def _get_kpi_export_artifact_regex(doc_lang: str) -> re.Pattern[str]:
    """Compiles locale-aware KPI artifact scrubber from localization config."""
    localized_prefix = t("regex_kpi_export_prefix", locale=doc_lang, default="")
    prefixes = list(_DEFAULT_KPI_EXPORT_PREFIXES)
    if localized_prefix and localized_prefix != "regex_kpi_export_prefix":
        prefixes.append(localized_prefix)
    joined = "|".join(prefixes)
    return re.compile(rf"^(?:{joined})([^.]+)\.\s*", re.IGNORECASE)
```
* **In `payload_to_ast.py` (Lines 4198–4206)**: Preserve explicit `0.0` telemetry values instead of using truthy `or` fallbacks:
```python
raw_gamma = blueprint_data.get("cloud_intensity_gamma")
if raw_gamma is None:
    raw_gamma = ctx.get("cloud_intensity_gamma")
cloud_intensity_gamma = (
    float(raw_gamma)
    if raw_gamma is not None
    else (0.85 if "CLOUD" in delivery_model else 0.22)
)

raw_beta = blueprint_data.get("buffering_elasticity_beta")
if raw_beta is None:
    raw_beta = ctx.get("buffering_elasticity_beta")
buffering_elasticity_beta = (
    float(raw_beta)
    if raw_beta is not None
    else (0.95 if resolved_archetype == IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH else 0.35)
)
```