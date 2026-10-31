"""Jurisdictional Sovereignty Policy for the Sovereign Assessment Engine.

Maps client regulatory environments and country contexts to concrete territorial
architectural invariants, sovereign cloud stacks, and direct connectivity standards,
featuring Just-In-Time (JIT) dynamic synthesis and out-of-tree atomic caching for
unlisted jurisdictions.
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Protocol, Sequence, Set, Tuple, runtime_checkable

from pydantic import ValidationError

from assessment_engine.domain.schemas.jurisdiction import (
    JurisdictionSovereigntyProfile,
    JurisdictionalRegistry,
)
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = Path(
    os.environ.get(
        "SOVEREIGN_JURISDICTION_CONFIG_PATH",
        str(ROOT / "engine_config" / "policies" / "jurisdictional_sovereignty.json"),
    )
)
RUNTIME_STATE_DIR = Path(
    os.environ.get(
        "ENGINE_RUNTIME_STATE_DIR",
        str(Path(tempfile.gettempdir()) / "sovereign_cache"),
    )
)
DYNAMIC_DIR = Path(
    os.environ.get(
        "SOVEREIGN_DYNAMIC_JURISDICTION_DIR",
        str(RUNTIME_STATE_DIR / "jurisdictions_dynamic"),
    )
)
JIT_PROMPT_PATH = Path(
    os.environ.get(
        "SOVEREIGN_JIT_PROMPT_PATH",
        str(ROOT / "engine_config" / "prompts" / "jurisdiction_jit_synthesis.txt"),
    )
)

_REGISTRY_CACHE: JurisdictionalRegistry | None = None


class ConfigurationError(RuntimeError):
    """Raised when a mandatory sovereign governance configuration file is missing, unreadable, or malformed."""


class RegulatoryOntologyCategory(str, Enum):
    """Multi-partite ontological categories for regulatory and technical frameworks."""

    INTERNATIONAL_STANDARD = "INTERNATIONAL_STANDARD"
    SUPRANATIONAL_DIRECTIVE = "SUPRANATIONAL_DIRECTIVE"
    NATIONAL_STATUTE = "NATIONAL_STATUTE"


EU_27_MEMBER_STATES: Tuple[str, ...] = (
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
)
EU_27_SET: FrozenSet[str] = frozenset(EU_27_MEMBER_STATES)


@dataclass(frozen=True)
class FrameworkClassification:
    """Deterministic classification of a single framework or standard declaration."""

    raw_framework: str
    normalized_token: str
    category: RegulatoryOntologyCategory
    canonical_identifier: str
    sovereign_codes: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class JurisdictionalResolutionResult:
    """Result of multi-partite deterministic jurisdiction resolution."""

    international_standards: Tuple[str, ...] = field(default_factory=tuple)
    supranational_directives: Tuple[str, ...] = field(default_factory=tuple)
    national_statutes: Tuple[str, ...] = field(default_factory=tuple)
    supranational_member_codes: Tuple[str, ...] = field(default_factory=tuple)
    sovereign_nation_codes: Tuple[str, ...] = field(default_factory=tuple)
    effective_jurisdiction_codes: Tuple[str, ...] = field(default_factory=tuple)
    primary_jurisdiction_code: str | None = None
    classifications: Tuple[FrameworkClassification, ...] = field(default_factory=tuple)


def _normalize_token(value: str) -> str:
    """Normalize a string token to uppercase ASCII without diacritics."""
    return (
        unicodedata.normalize("NFKD", value.strip().upper())
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )


class DeterministicJurisdictionResolver:
    """Multi-partite deterministic resolver separating international standards, supranational directives, and national statutes.

    Enforces the core ontological invariant:
      1. INTERNATIONAL_STANDARD (e.g., IEC 62443, ISO 27001, NIST CSF) -> Adds ZERO sovereign ISO-3166 nation-state codes.
      2. SUPRANATIONAL_DIRECTIVE (e.g., NIS2, GDPR, DORA) -> Expands to EU-27 member states or intersects with declared operational footprints.
      3. NATIONAL_STATUTE (e.g., German BSIG, Saudi NCA ECC, US FedRAMP) -> Maps strictly to explicit ISO-3166-1 alpha-2 codes.
    """

    _INTERNATIONAL_STANDARD_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"\b(?:ISA[/\-\s]*)?IEC[\s\-]*62443(?:[\-\dA-Z]*)?\b"), "IEC 62443"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*2700[0-9]\b"), "ISO/IEC 27001"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*2701[78]\b"), "ISO/IEC 27017"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*27701\b"), "ISO/IEC 27701"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*22301\b"), "ISO 22301"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*31000\b"), "ISO 31000"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*42001\b"), "ISO/IEC 42001"),
        (re.compile(r"\bISO(?:[/\s\-]*IEC)?[\s\-]*20000\b"), "ISO/IEC 20000"),
        (re.compile(r"\bNIST[\s\-]*CSF(?:[\s\-]*2(?:\.0)?)?\b"), "NIST CSF"),
        (re.compile(r"\bNIST[\s\-]*CYBERSECURITY[\s\-]*FRAMEWORK\b"), "NIST CSF"),
        (re.compile(r"\bNIST[\s\-]*(?:SP[\s\-]*)?800[\s\-]*53\b"), "NIST SP 800-53"),
        (re.compile(r"\bNIST[\s\-]*(?:SP[\s\-]*)?800[\s\-]*82\b"), "NIST SP 800-82"),
        (re.compile(r"\bNIST[\s\-]*(?:SP[\s\-]*)?800[\s\-]*171\b"), "NIST SP 800-171"),
        (re.compile(r"\bNIST[\s\-]*(?:SP[\s\-]*)?800[\s\-]*207\b"), "NIST SP 800-207"),
        (re.compile(r"\bPCI[\s\-]*DSS\b"), "PCI DSS"),
        (re.compile(r"\bCIS[\s\-]*(?:CONTROLS|BENCHMARKS?)\b"), "CIS Controls"),
        (re.compile(r"\bCOBIT\b"), "COBIT"),
        (re.compile(r"\bTOGAF\b"), "TOGAF"),
        (re.compile(r"\bITIL\b"), "ITIL"),
        (re.compile(r"\bSOC[\s\-]*[123](?:[\s\-]*TYPE[\s\-]*I{1,2})?\b"), "SOC 2"),
        (re.compile(r"\bOWASP\b"), "OWASP"),
        (re.compile(r"\bIEEE[\s\-]*\d+\b"), "IEEE Standard"),
        (re.compile(r"\bIETF[\s\-]*RFC\b"), "IETF RFC"),
        (re.compile(r"\b3GPP\b"), "3GPP"),
        (re.compile(r"\bETSI[\s\-]*EN\b"), "ETSI EN"),
    )

    _SUPRANATIONAL_DIRECTIVE_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"\bNIS[\s\-]*2(?:[\s\-]*DIRECTIVE)?\b"), "NIS2"),
        (re.compile(r"\bDIRECTIVE[\s\-]*(?:\(EU\)[\s\-]*)?2022/2555\b"), "NIS2"),
        (re.compile(r"\bGDPR\b"), "GDPR"),
        (re.compile(r"\bGENERAL[\s\-]*DATA[\s\-]*PROTECTION[\s\-]*REGULATION\b"), "GDPR"),
        (re.compile(r"\bREGULATION[\s\-]*(?:\(EU\)[\s\-]*)?2016/679\b"), "GDPR"),
        (re.compile(r"\bDORA\b"), "DORA"),
        (re.compile(r"\bDIGITAL[\s\-]*OPERATIONAL[\s\-]*RESILIENCE[\s\-]*ACT\b"), "DORA"),
        (re.compile(r"\bREGULATION[\s\-]*(?:\(EU\)[\s\-]*)?2022/2554\b"), "DORA"),
        (re.compile(r"\b(?:EU[\s\-]*)?AI[\s\-]*ACT\b"), "EU AI Act"),
        (re.compile(r"\bCER[\s\-]*DIRECTIVE\b"), "CER Directive"),
        (re.compile(r"\bEIDAS(?:[\s\-]*2(?:\.0)?)?\b"), "eIDAS"),
        (re.compile(r"\bGAIA[\s\-]*X\b"), "GAIA-X"),
        (re.compile(r"\bEUCS\b"), "EUCS"),
        (re.compile(r"\bCYBER[\s\-]*RESILIENCE[\s\-]*ACT\b"), "CRA"),
        (re.compile(r"\bCRA\b"), "CRA"),
    )

    _NATIONAL_STATUTE_PATTERNS: Tuple[Tuple[re.Pattern[str], str, str], ...] = (
        # Germany (DE)
        (re.compile(r"\bBSIG\b"), "BSIG", "DE"),
        (re.compile(r"\bBSI[\s\-]*KRITIS\b"), "BSI KRITIS", "DE"),
        (re.compile(r"\bKRITIS\b"), "BSI KRITIS", "DE"),
        (re.compile(r"\bIT[\s\-]*SIG(?:[\s\-]*2(?:\.0)?)?\b"), "IT-SiG 2.0", "DE"),
        (re.compile(r"\bIT[\s\-]*SICHERHEITSGESETZ\b"), "IT-SiG", "DE"),
        (re.compile(r"\bBSI[\s\-]*C5\b"), "BSI C5", "DE"),
        (re.compile(r"\bBSI[\s\-]*IT[\s\-]*GRUNDSCHUTZ\b"), "BSI IT-Grundschutz", "DE"),
        (re.compile(r"\bIT[\s\-]*GRUNDSCHUTZ\b"), "BSI IT-Grundschutz", "DE"),
        (re.compile(r"\bNIS2UMSUCCG\b"), "NIS2UmsuCG", "DE"),
        (re.compile(r"\bBDSG\b"), "BDSG", "DE"),
        # Saudi Arabia (SA)
        (re.compile(r"\bNCA[\s\-]*ECC\b"), "NCA ECC", "SA"),
        (re.compile(r"\bNCA[\s\-]*CCC\b"), "NCA CCC", "SA"),
        (re.compile(r"\bNCA[\s\-]*OTCC\b"), "NCA OTCC", "SA"),
        (re.compile(r"\bNCA[\s\-]*CSCC\b"), "NCA CSCC", "SA"),
        (re.compile(r"\bSAMA[\s\-]*CSF\b"), "SAMA CSF", "SA"),
        (re.compile(r"\bSDAIA[\s\-]*PDPL\b"), "SDAIA PDPL", "SA"),
        (re.compile(r"\bSAUDI[\s\-]*PDPL\b"), "Saudi PDPL", "SA"),
        # United States (US)
        (re.compile(r"\bFEDRAMP\b"), "FedRAMP", "US"),
        (re.compile(r"\bFISMA\b"), "FISMA", "US"),
        (re.compile(r"\bCMMC(?:[\s\-]*2(?:\.0)?)?\b"), "CMMC", "US"),
        (re.compile(r"\bHIPAA\b"), "HIPAA", "US"),
        (re.compile(r"\bNERC[\s\-]*CIP\b"), "NERC CIP", "US"),
        (re.compile(r"\bSOX\b"), "SOX", "US"),
        (re.compile(r"\bSARBANES[\s\-]*OXLEY\b"), "SOX", "US"),
        (re.compile(r"\bCCPA\b"), "CCPA", "US"),
        (re.compile(r"\bGLBA\b"), "GLBA", "US"),
        (re.compile(r"\bITAR\b"), "ITAR", "US"),
        (re.compile(r"\bCJIS\b"), "CJIS", "US"),
        # Spain (ES)
        (re.compile(r"\bESQUEMA[\s\-]*NACIONAL[\s\-]*DE[\s\-]*SEGURIDAD\b"), "ENS", "ES"),
        (re.compile(r"\bCCN[\s\-]*STIC\b"), "CCN-STIC", "ES"),
        (re.compile(r"\bENS\b"), "ENS", "ES"),
        (re.compile(r"\bLOPDGDD\b"), "LOPDGDD", "ES"),
        (re.compile(r"\bLEY[\s\-]*PIC\b"), "Ley PIC", "ES"),
        # France (FR)
        (re.compile(r"\bSECJNUMCLOUD\b|\bSECNUMCLOUD\b"), "SecNumCloud", "FR"),
        (re.compile(r"\bANSSI[\s\-]*LPM\b"), "ANSSI LPM", "FR"),
        (re.compile(r"\bLPM\b"), "LPM", "FR"),
        (re.compile(r"\bHDS\b"), "HDS", "FR"),
        # United Kingdom (GB)
        (re.compile(r"\bUK[\s\-]*GDPR\b"), "UK GDPR", "GB"),
        (re.compile(r"\bNCSC[\s\-]*CAF\b"), "NCSC CAF", "GB"),
        (re.compile(r"\bCYBER[\s\-]*ESSENTIALS\b"), "Cyber Essentials", "GB"),
        # United Arab Emirates (AE)
        (re.compile(r"\bUAE[\s\-]*IA\b"), "UAE IA", "AE"),
        (re.compile(r"\bNESA\b"), "NESA", "AE"),
        (re.compile(r"\bDESC[\s\-]*ISR\b"), "DESC ISR", "AE"),
        (re.compile(r"\bADHICS\b"), "ADHICS", "AE"),
        # Switzerland (CH)
        (re.compile(r"\bFADP\b|\bNDSG\b|\bREVFADP\b"), "FADP", "CH"),
        (re.compile(r"\bFINMA\b"), "FINMA", "CH"),
        # Italy (IT)
        (re.compile(r"\bACN\b"), "ACN", "IT"),
        (re.compile(r"\bAGID\b"), "AgID", "IT"),
        (re.compile(r"\bPERIMETRO[\s\-]*DI[\s\-]*SICUREZZA[\s\-]*NAZIONALE[\s\-]*CIBERNETICA\b"), "PSNC", "IT"),
        # Netherlands (NL)
        (re.compile(r"\bBIO\b"), "BIO", "NL"),
        # Australia (AU)
        (re.compile(r"\bIRAP\b"), "IRAP", "AU"),
        (re.compile(r"\bACSC[\s\-]*ISM\b"), "ACSC ISM", "AU"),
        (re.compile(r"\bESSENTIAL[\s\-]*EIGHT\b"), "Essential Eight", "AU"),
        (re.compile(r"\bSOCI[\s\-]*ACT\b"), "SOCI Act", "AU"),
        # Singapore (SG)
        (re.compile(r"\bMAS[\s\-]*TRM\b"), "MAS TRM", "SG"),
        (re.compile(r"\bCSA[\s\-]*CCOP\b"), "CSA CCoP", "SG"),
        # Brazil (BR)
        (re.compile(r"\bLGPD\b"), "LGPD", "BR"),
        # Japan (JP)
        (re.compile(r"\bISMAP\b"), "ISMAP", "JP"),
        (re.compile(r"\bAPPI\b"), "APPI", "JP"),
        # Canada (CA)
        (re.compile(r"\bPIPEDA\b"), "PIPEDA", "CA"),
        (re.compile(r"\bITSG[\s\-]*33\b"), "ITSG-33", "CA"),
        # China (CN)
        (re.compile(r"\bMLPS(?:[\s\-]*2(?:\.0)?)?\b"), "MLPS 2.0", "CN"),
        (re.compile(r"\bPIPL\b"), "PIPL", "CN"),
        # India (IN)
        (re.compile(r"\bDPDP[\s\-]*ACT\b|\bDPDPA\b"), "DPDP Act", "IN"),
        (re.compile(r"\bCERT[\s\-]*IN\b"), "CERT-In", "IN"),
        # South Korea (KR)
        (re.compile(r"\bK[\s\-]*ISMS\b|\bISMS[\s\-]*P\b"), "ISMS-P", "KR"),
        (re.compile(r"\bPIPA\b"), "PIPA", "KR"),
        # Mexico (MX)
        (re.compile(r"\bLFPDPPP\b"), "LFPDPPP", "MX"),
        (re.compile(r"\bCNBV\b"), "CNBV", "MX"),
        (re.compile(r"\bSPEI\b"), "SPEI", "MX"),
    )

    _STATIC_COUNTRY_ALIASES: Dict[str, str] = {
        "GERMANY": "DE",
        "DEUTSCHLAND": "DE",
        "DEU": "DE",
        "SPAIN": "ES",
        "ESPANA": "ES",
        "ESP": "ES",
        "FRANCE": "FR",
        "FRA": "FR",
        "ITALY": "IT",
        "ITALIA": "IT",
        "ITA": "IT",
        "NETHERLANDS": "NL",
        "NLD": "NL",
        "BELGIUM": "BE",
        "BEL": "BE",
        "AUSTRIA": "AT",
        "AUT": "AT",
        "POLAND": "PL",
        "POL": "PL",
        "SWEDEN": "SE",
        "SWE": "SE",
        "FINLAND": "FI",
        "FIN": "FI",
        "DENMARK": "DK",
        "DNK": "DK",
        "IRELAND": "IE",
        "IRL": "IE",
        "PORTUGAL": "PT",
        "PRT": "PT",
        "GREECE": "GR",
        "GRC": "GR",
        "CZECHIA": "CZ",
        "CZECH REPUBLIC": "CZ",
        "CZE": "CZ",
        "ROMANIA": "RO",
        "ROU": "RO",
        "HUNGARY": "HU",
        "HUN": "HU",
        "BULGARIA": "BG",
        "BGR": "BG",
        "CROATIA": "HR",
        "HRV": "HR",
        "SLOVAKIA": "SK",
        "SVK": "SK",
        "SLOVENIA": "SI",
        "SVN": "SI",
        "LITHUANIA": "LT",
        "LTU": "LT",
        "LATVIA": "LV",
        "LVA": "LV",
        "ESTONIA": "EE",
        "EST": "EE",
        "LUXEMBOURG": "LU",
        "LUX": "LU",
        "MALTA": "MT",
        "MLT": "MT",
        "CYPRUS": "CY",
        "CYP": "CY",
        "UNITED STATES": "US",
        "UNITED STATES OF AMERICA": "US",
        "USA": "US",
        "UNITED KINGDOM": "GB",
        "GREAT BRITAIN": "GB",
        "UK": "GB",
        "GBR": "GB",
        "SAUDI ARABIA": "SA",
        "KINGDOM OF SAUDI ARABIA": "SA",
        "KSA": "SA",
        "SAU": "SA",
        "UNITED ARAB EMIRATES": "AE",
        "UAE": "AE",
        "ARE": "AE",
        "SWITZERLAND": "CH",
        "CHE": "CH",
        "CANADA": "CA",
        "CAN": "CA",
        "AUSTRALIA": "AU",
        "AUS": "AU",
        "JAPAN": "JP",
        "JPN": "JP",
        "SINGAPORE": "SG",
        "SGP": "SG",
        "BRAZIL": "BR",
        "BRASIL": "BR",
        "BRA": "BR",
        "MEXICO": "MX",
        "MEX": "MX",
        "INDIA": "IN",
        "IND": "IN",
        "CHINA": "CN",
        "CHN": "CN",
        "SOUTH KOREA": "KR",
        "REPUBLIC OF KOREA": "KR",
        "KOR": "KR",
    }

    def __init__(self, registry: JurisdictionalRegistry | None = None) -> None:
        self._registry = registry

    def normalize_country_code(self, country_or_code: str | None) -> str | None:
        """Normalize a country name, alias, or ISO code into an uppercase ISO-3166-1 alpha-2 code."""
        if not country_or_code or not str(country_or_code).strip():
            return None
        c_clean = _normalize_token(str(country_or_code))
        if not c_clean:
            return None

        if c_clean in self._STATIC_COUNTRY_ALIASES:
            return self._STATIC_COUNTRY_ALIASES[c_clean]

        if self._registry is not None:
            extra_config: Dict[str, Any] = (
                self._registry.model_extra if isinstance(self._registry.model_extra, dict) else {}
            )
            country_aliases: Dict[str, str] = (
                getattr(self._registry, "country_aliases", None)
                or extra_config.get("country_aliases", {})
            )
            if isinstance(country_aliases, dict):
                for alias_key, mapped_code in country_aliases.items():
                    if _normalize_token(str(alias_key)) == c_clean:
                        norm_mapped = _normalize_token(str(mapped_code))
                        return self._STATIC_COUNTRY_ALIASES.get(norm_mapped, norm_mapped)

            if c_clean in self._registry.jurisdictions:
                return c_clean

            for code, profile in self._registry.jurisdictions.items():
                if c_clean == _normalize_token(profile.region_code):
                    return code
                name_tokens = [
                    t.strip()
                    for t in re.split(r"[/,\-()\s]+", _normalize_token(profile.name))
                    if t.strip()
                ]
                if c_clean in name_tokens or c_clean == _normalize_token(profile.name):
                    return code

        if len(c_clean) == 2 and c_clean.isalpha():
            return c_clean
        return None

    def normalize_operational_footprints(
        self,
        footprints: Sequence[str] | str | None,
    ) -> Tuple[str, ...]:
        """Normalize one or more declared operational footprints into unique ISO-3166-1 alpha-2 codes."""
        if not footprints:
            return ()
        raw_items: List[str] = (
            [footprints] if isinstance(footprints, str) else list(footprints)
        )
        resolved: List[str] = []
        for item in raw_items:
            if not item or not str(item).strip():
                continue
            parts = [p.strip() for p in re.split(r"[,;|/]+", str(item)) if p.strip()]
            for part in parts:
                norm_part = _normalize_token(part)
                if norm_part in ("EU", "EU-27", "EU27", "EUROPEAN UNION", "EEA"):
                    for eu_code in EU_27_MEMBER_STATES:
                        if eu_code not in resolved:
                            resolved.append(eu_code)
                    continue
                code = self.normalize_country_code(part)
                if code and code not in resolved:
                    resolved.append(code)
        return tuple(resolved)

    def classify_framework(
        self,
        framework: str,
        operational_footprints: Sequence[str] | None = None,
    ) -> List[FrameworkClassification]:
        """Classify a framework string into one or more ontological categories.

        Guarantees that international technical standards (e.g., IEC 62443, ISO 27001, NIST CSF)
        never fabricate national legal jurisdictions.
        """
        if not framework or not framework.strip():
            return []

        normalized = _normalize_token(framework)
        footprint_codes = self.normalize_operational_footprints(operational_footprints)
        results: List[FrameworkClassification] = []

        # 1. Check National Statutes
        for pattern, canonical_name, iso_code in self._NATIONAL_STATUTE_PATTERNS:
            if pattern.search(normalized):
                results.append(
                    FrameworkClassification(
                        raw_framework=framework,
                        normalized_token=normalized,
                        category=RegulatoryOntologyCategory.NATIONAL_STATUTE,
                        canonical_identifier=canonical_name,
                        sovereign_codes=(iso_code,),
                    )
                )

        # Check custom registry framework_mappings only if they are not International Standards or Supranational Directives
        if self._registry is not None and not results:
            extra_config: Dict[str, Any] = (
                self._registry.model_extra if isinstance(self._registry.model_extra, dict) else {}
            )
            framework_mappings: Dict[str, str] = (
                getattr(self._registry, "framework_mappings", None)
                or extra_config.get("framework_mappings", {})
            )
            if isinstance(framework_mappings, dict):
                for keyword, mapped_code in framework_mappings.items():
                    kw_norm = _normalize_token(str(keyword))
                    if not kw_norm:
                        continue
                    if self._is_international_or_supranational_token(kw_norm):
                        continue
                    if re.search(rf"\b{re.escape(kw_norm)}\b", normalized):
                        target_code = str(mapped_code).strip().upper()
                        if target_code in ("EU", "EU-27", "EU27"):
                            continue
                        results.append(
                            FrameworkClassification(
                                raw_framework=framework,
                                normalized_token=normalized,
                                category=RegulatoryOntologyCategory.NATIONAL_STATUTE,
                                canonical_identifier=kw_norm,
                                sovereign_codes=(target_code,),
                            )
                        )

        # 2. Check Supranational Directives
        for pattern, canonical_name in self._SUPRANATIONAL_DIRECTIVE_PATTERNS:
            if pattern.search(normalized):
                eu_intersection = tuple(
                    code for code in footprint_codes if code in EU_27_SET
                )
                expanded_codes = eu_intersection if eu_intersection else EU_27_MEMBER_STATES
                results.append(
                    FrameworkClassification(
                        raw_framework=framework,
                        normalized_token=normalized,
                        category=RegulatoryOntologyCategory.SUPRANATIONAL_DIRECTIVE,
                        canonical_identifier=canonical_name,
                        sovereign_codes=expanded_codes,
                    )
                )

        # 3. Check International Standards -> Strictly ZERO sovereign nation-state codes
        for pattern, canonical_name in self._INTERNATIONAL_STANDARD_PATTERNS:
            if pattern.search(normalized):
                results.append(
                    FrameworkClassification(
                        raw_framework=framework,
                        normalized_token=normalized,
                        category=RegulatoryOntologyCategory.INTERNATIONAL_STANDARD,
                        canonical_identifier=canonical_name,
                        sovereign_codes=(),
                    )
                )

        return results

    def _is_international_or_supranational_token(self, token: str) -> bool:
        """Return True if token matches any known international standard or supranational directive."""
        for pattern, _ in self._INTERNATIONAL_STANDARD_PATTERNS:
            if pattern.search(token):
                return True
        for pattern, _ in self._SUPRANATIONAL_DIRECTIVE_PATTERNS:
            if pattern.search(token):
                return True
        return False

    def resolve(
        self,
        frameworks: Sequence[str] | None = None,
        country: str | None = None,
        operational_footprints: Sequence[str] | None = None,
        language: str | None = None,
    ) -> JurisdictionalResolutionResult:
        """Resolve a multi-partite jurisdictional graph from declared frameworks and operational footprints."""
        combined_footprints: List[str] = []
        if country and str(country).strip():
            combined_footprints.append(str(country).strip())
        if operational_footprints:
            for fp in operational_footprints:
                if fp and str(fp).strip():
                    combined_footprints.append(str(fp).strip())

        normalized_footprints = self.normalize_operational_footprints(combined_footprints)

        classifications: List[FrameworkClassification] = []
        for fw in frameworks or []:
            if fw and str(fw).strip():
                classifications.extend(
                    self.classify_framework(str(fw), operational_footprints=normalized_footprints)
                )

        intl_standards: List[str] = []
        supra_directives: List[str] = []
        nat_statutes: List[str] = []
        supra_member_codes: List[str] = []
        statute_nation_codes: List[str] = []

        for clf in classifications:
            if clf.category == RegulatoryOntologyCategory.INTERNATIONAL_STANDARD:
                if clf.canonical_identifier not in intl_standards:
                    intl_standards.append(clf.canonical_identifier)
                # Invariant: International standards add ZERO sovereign ISO-3166 codes
            elif clf.category == RegulatoryOntologyCategory.SUPRANATIONAL_DIRECTIVE:
                if clf.canonical_identifier not in supra_directives:
                    supra_directives.append(clf.canonical_identifier)
                for code in clf.sovereign_codes:
                    if code not in supra_member_codes:
                        supra_member_codes.append(code)
            elif clf.category == RegulatoryOntologyCategory.NATIONAL_STATUTE:
                if clf.canonical_identifier not in nat_statutes:
                    nat_statutes.append(clf.canonical_identifier)
                for code in clf.sovereign_codes:
                    if code not in statute_nation_codes:
                        statute_nation_codes.append(code)

        # Sovereign nation codes strictly from explicit operational footprints and national statutes
        sovereign_nation_codes: List[str] = []
        for code in normalized_footprints:
            if code not in sovereign_nation_codes:
                sovereign_nation_codes.append(code)
        for code in statute_nation_codes:
            if code not in sovereign_nation_codes:
                sovereign_nation_codes.append(code)

        # Re-intersect supranational member codes if national statutes or footprints establish an EU subset
        if supra_directives:
            eu_footprint_subset = [
                c for c in sovereign_nation_codes if c in EU_27_SET
            ]
            if eu_footprint_subset:
                supra_member_codes = eu_footprint_subset
            else:
                supra_member_codes = list(EU_27_MEMBER_STATES)

        effective_codes: List[str] = []
        for code in sovereign_nation_codes:
            if code not in effective_codes:
                effective_codes.append(code)
        for code in supra_member_codes:
            if code not in effective_codes:
                effective_codes.append(code)

        primary_code: str | None = None
        if normalized_footprints:
            primary_code = normalized_footprints[0]
        elif statute_nation_codes:
            primary_code = statute_nation_codes[0]
        elif supra_member_codes:
            primary_code = self._select_supranational_primary_code(
                supra_member_codes=supra_member_codes,
                language=language,
            )
        elif language:
            primary_code = self._resolve_language_code(language)

        return JurisdictionalResolutionResult(
            international_standards=tuple(intl_standards),
            supranational_directives=tuple(supra_directives),
            national_statutes=tuple(nat_statutes),
            supranational_member_codes=tuple(supra_member_codes),
            sovereign_nation_codes=tuple(sovereign_nation_codes),
            effective_jurisdiction_codes=tuple(effective_codes),
            primary_jurisdiction_code=primary_code,
            classifications=tuple(classifications),
        )

    def _resolve_language_code(self, language: str | None) -> str | None:
        """Resolve a language hint into a registry jurisdiction code if configured."""
        if not language or not language.strip():
            return None
        lang_clean = _normalize_token(language)
        if self._registry is not None:
            extra_config: Dict[str, Any] = (
                self._registry.model_extra if isinstance(self._registry.model_extra, dict) else {}
            )
            language_mappings: Dict[str, str] = (
                getattr(self._registry, "language_mappings", None)
                or extra_config.get("language_mappings", {})
            )
            if isinstance(language_mappings, dict):
                for lang_key, mapped_code in language_mappings.items():
                    if _normalize_token(str(lang_key)) == lang_clean:
                        return str(mapped_code).upper()
            if lang_clean in self._registry.jurisdictions:
                return lang_clean

        default_langs = {
            "ES": "ES",
            "EN": "US",
            "DE": "DE",
            "JA": "JP",
            "FR": "FR",
            "IT": "IT",
            "PT": "BR",
        }
        if lang_clean in default_langs:
            target = default_langs[lang_clean]
            if self._registry is None or target in self._registry.jurisdictions:
                return target
        return None

    def _select_supranational_primary_code(
        self,
        supra_member_codes: Sequence[str],
        language: str | None = None,
    ) -> str | None:
        """Select a primary profile code for a supranational directive when no single country was specified."""
        if not supra_member_codes:
            return None
        if len(supra_member_codes) == 1:
            return supra_member_codes[0]

        lang_code = self._resolve_language_code(language)
        if lang_code and lang_code in supra_member_codes:
            return lang_code

        if self._registry is not None:
            if "EU" in self._registry.jurisdictions:
                return "EU"
            extra_config: Dict[str, Any] = (
                self._registry.model_extra if isinstance(self._registry.model_extra, dict) else {}
            )
            default_code = (
                getattr(self._registry, "default_jurisdiction", None)
                or extra_config.get("default_jurisdiction")
            )
            if (
                isinstance(default_code, str)
                and default_code.upper() in supra_member_codes
                and default_code.upper() in self._registry.jurisdictions
            ):
                return default_code.upper()
            for code in supra_member_codes:
                if code in self._registry.jurisdictions:
                    return code

        return supra_member_codes[0]


def _validate_profile_invariants(code: str, profile: JurisdictionSovereigntyProfile, source: Path) -> None:
    """Verify that a loaded jurisdiction profile contains mandatory non-empty architectural invariants."""
    if not profile.architectural_invariants:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Jurisdiction '{code}' in '{source}' defines zero architectural invariants."
        )


def _is_within_repository_tree(target_dir: Path, repo_root: Path | None = None) -> bool:
    """Return True if target_dir resolves inside the immutable application repository tree."""
    resolved_root = (repo_root or ROOT).resolve()
    resolved_target = target_dir.resolve()
    return resolved_target == resolved_root or resolved_root in resolved_target.parents


@runtime_checkable
class SynthesizedPolicyStorePort(Protocol):
    """Port interface for out-of-tree persistence and retrieval of JIT-synthesized jurisdiction policies."""

    def get(self, code: str) -> JurisdictionSovereigntyProfile | None:
        """Retrieve a previously synthesized jurisdiction profile by ISO region code."""
        ...

    def put(self, code: str, profile: JurisdictionSovereigntyProfile) -> Path:
        """Atomically persist a synthesized jurisdiction profile and return its storage path."""
        ...

    def list_all(self) -> Dict[str, JurisdictionSovereigntyProfile]:
        """Load and validate all synthesized jurisdiction profiles from the backing store."""
        ...


class OutOfTreeSynthesizedPolicyStore:
    """Out-of-tree filesystem adapter for JIT-synthesized policies using POSIX atomic replacement."""

    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        allow_in_tree_override: bool = False,
    ) -> None:
        resolved_dir = Path(state_dir).resolve() if state_dir is not None else self._resolve_default_dir()
        if not allow_in_tree_override and _is_within_repository_tree(resolved_dir):
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Synthesized policy store directory '{resolved_dir}' "
                f"resides inside immutable repository root '{ROOT.resolve()}'. "
                "Configure ENGINE_RUNTIME_STATE_DIR to an isolated out-of-tree volume."
            )
        self._state_dir = resolved_dir

    @staticmethod
    def _resolve_default_dir() -> Path:
        """Resolve the active out-of-tree dynamic policy directory from runtime configuration."""
        env_state_dir = os.environ.get("ENGINE_RUNTIME_STATE_DIR")
        env_dyn_dir = os.environ.get("SOVEREIGN_DYNAMIC_JURISDICTION_DIR")
        if env_dyn_dir:
            candidate = Path(env_dyn_dir).resolve()
        elif env_state_dir:
            candidate = (Path(env_state_dir) / "jurisdictions_dynamic").resolve()
        else:
            candidate = Path(DYNAMIC_DIR).resolve()

        if _is_within_repository_tree(candidate):
            fallback_root = Path(
                os.environ.get(
                    "ENGINE_RUNTIME_STATE_DIR",
                    str(Path(tempfile.gettempdir()) / "sovereign_cache"),
                )
            ).resolve()
            candidate = (fallback_root / "jurisdictions_dynamic").resolve()
        return candidate

    @property
    def state_dir(self) -> Path:
        """Return the resolved out-of-tree storage directory path."""
        return self._state_dir

    def _cache_file_for(self, code: str) -> Path:
        clean_code = code.strip().lower()
        if not clean_code or not re.fullmatch(r"[a-z0-9_\-]+", clean_code):
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Invalid jurisdiction code '{code}' for policy store."
            )
        return self._state_dir / f"{clean_code}.json"

    def get(self, code: str) -> JurisdictionSovereigntyProfile | None:
        """Read and validate a cached jurisdiction profile in fail-closed mode."""
        clean_code = code.strip().upper()
        cache_file = self._cache_file_for(clean_code)
        if not cache_file.exists():
            return None
        if not cache_file.is_file():
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Cached dynamic jurisdiction path '{cache_file}' is not a regular file."
            )
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            profile = JurisdictionSovereigntyProfile.model_validate(cached_data, strict=True)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Corrupted cached dynamic jurisdiction at '{cache_file}': {exc}"
            ) from exc
        _validate_profile_invariants(clean_code, profile, cache_file)
        return profile

    def put(self, code: str, profile: JurisdictionSovereigntyProfile) -> Path:
        """Atomically write a validated jurisdiction profile via tempfile.mkstemp and os.replace."""
        clean_code = code.strip().upper()
        if _is_within_repository_tree(self._state_dir):
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Refusing runtime write into repository tree at '{self._state_dir}'."
            )
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Unable to create dynamic jurisdiction directory '{self._state_dir}': {exc}"
            ) from exc

        cache_file = self._cache_file_for(clean_code)
        _validate_profile_invariants(clean_code, profile, cache_file)
        serialized = json.dumps(profile.model_dump(), indent=2, ensure_ascii=False).encode("utf-8")

        fd: int | None = None
        tmp_path: str | None = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                prefix=f".{clean_code.lower()}_",
                suffix=".tmp",
                dir=str(self._state_dir),
            )
            with os.fdopen(fd, "wb") as tmp_file:
                fd = None
                tmp_file.write(serialized)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(tmp_path, cache_file)
            tmp_path = None
        except OSError as exc:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Failed atomic write for synthesized jurisdiction cache '{cache_file}': {exc}"
            ) from exc
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if tmp_path is not None and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        return cache_file

    def list_all(self) -> Dict[str, JurisdictionSovereigntyProfile]:
        """Load and strictly validate all cached dynamic jurisdiction profiles from state_dir."""
        if not self._state_dir.exists():
            return {}
        if not self._state_dir.is_dir():
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Dynamic jurisdiction path '{self._state_dir}' is not a directory."
            )
        profiles: Dict[str, JurisdictionSovereigntyProfile] = {}
        for dyn_file in sorted(self._state_dir.glob("*.json")):
            if not dyn_file.is_file():
                raise ConfigurationError(
                    f"Fatal Fail-Closed Policy Error: Dynamic jurisdiction entry '{dyn_file}' is not a regular file."
                )
            code = dyn_file.stem.upper()
            try:
                raw_dyn = dyn_file.read_text(encoding="utf-8")
            except OSError as exc:
                raise ConfigurationError(
                    f"Fatal Fail-Closed Policy Error: Unable to read dynamic jurisdiction file '{dyn_file}': {exc}"
                ) from exc
            try:
                p_data = json.loads(raw_dyn)
            except json.JSONDecodeError as exc:
                raise ConfigurationError(
                    f"Fatal Fail-Closed Policy Error: Malformed JSON in dynamic jurisdiction file '{dyn_file}': {exc}"
                ) from exc
            try:
                profile = JurisdictionSovereigntyProfile.model_validate(p_data, strict=True)
            except ValidationError as exc:
                raise ConfigurationError(
                    f"Fatal Fail-Closed Policy Error: Schema validation failed for dynamic jurisdiction '{dyn_file}': {exc}"
                ) from exc
            _validate_profile_invariants(code, profile, dyn_file)
            profiles[code] = profile
        return profiles


def get_default_policy_store() -> SynthesizedPolicyStorePort:
    """Instantiate the default out-of-tree policy store adapter."""
    return OutOfTreeSynthesizedPolicyStore()


def load_verified_registry_fail_closed(
    path: Path | None = None,
    policy_store: SynthesizedPolicyStorePort | None = None,
) -> JurisdictionalRegistry:
    """Load and strictly validate the canonical JurisdictionalRegistry in fail-closed mode.

    Raises:
        ConfigurationError: If the governance policy file is missing, unreadable, malformed,
            fails strict Pydantic schema validation, or defines an empty jurisdiction set.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and path is None and policy_store is None:
        return _REGISTRY_CACHE

    target = Path(path).resolve() if path is not None else CONFIG_PATH.resolve()
    if not target.exists() or not target.is_file():
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Jurisdictional sovereignty registry not found or not a regular file at '{target}'."
        )

    try:
        raw_text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Unable to read jurisdictional registry at '{target}': {exc}"
        ) from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Malformed JSON in jurisdictional registry '{target}': {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Root element of '{target}' must be a JSON object."
        )

    try:
        registry = JurisdictionalRegistry.model_validate(data, strict=True)
    except ValidationError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Schema validation failed for '{target}': {exc}"
        ) from exc

    if not registry.jurisdictions:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Jurisdictional registry '{target}' contains zero active jurisdictions."
        )

    for code, profile in registry.jurisdictions.items():
        _validate_profile_invariants(code, profile, target)

    store = policy_store or get_default_policy_store()
    for code, profile in store.list_all().items():
        if code not in registry.jurisdictions:
            registry.jurisdictions[code] = profile

    if path is None and policy_store is None:
        _REGISTRY_CACHE = registry
    return registry


def load_jurisdictional_registry(
    path: Path | None = None,
    policy_store: SynthesizedPolicyStorePort | None = None,
) -> JurisdictionalRegistry:
    """Load and cache the canonical JurisdictionalRegistry from disk using fail-closed enforcement."""
    return load_verified_registry_fail_closed(path=path, policy_store=policy_store)


def infer_jurisdiction_code(
    country: str | None,
    frameworks: List[str] | None,
    language: str | None,
    registry: JurisdictionalRegistry | None = None,
    operational_footprints: Sequence[str] | None = None,
) -> str:
    """Infer the ISO region code deterministically via the Multi-Partite Jurisdictional Resolver.

    Guarantees that international technical standards (e.g., IEC 62443, ISO 27001, NIST CSF)
    never fabricate or collapse to a national jurisdiction (such as DE) via substring matching.
    """
    active_registry = registry or load_verified_registry_fail_closed()
    if not active_registry.jurisdictions:
        raise ConfigurationError(
            "Fatal Fail-Closed Policy Error: Cannot infer jurisdiction code from an empty registry."
        )

    resolver = DeterministicJurisdictionResolver(registry=active_registry)
    resolution = resolver.resolve(
        frameworks=frameworks,
        country=country,
        operational_footprints=operational_footprints,
        language=language,
    )

    if resolution.primary_jurisdiction_code:
        return resolution.primary_jurisdiction_code

    extra_config: Dict[str, Any] = (
        active_registry.model_extra if isinstance(active_registry.model_extra, dict) else {}
    )
    default_code = (
        getattr(active_registry, "default_jurisdiction", None)
        or extra_config.get("default_jurisdiction")
    )
    if isinstance(default_code, str) and default_code.upper() in active_registry.jurisdictions:
        return default_code.upper()

    return next(iter(active_registry.jurisdictions.keys()))


def _load_jit_prompt_template(registry: JurisdictionalRegistry | None = None) -> str:
    """Load the JIT jurisdiction synthesis prompt template from external configuration."""
    if registry is not None:
        extra_config: Dict[str, Any] = (
            registry.model_extra if isinstance(registry.model_extra, dict) else {}
        )
        inline_template = (
            getattr(registry, "jit_synthesis_prompt_template", None)
            or extra_config.get("jit_synthesis_prompt_template")
        )
        if isinstance(inline_template, str) and inline_template.strip():
            return inline_template

    prompt_file = JIT_PROMPT_PATH.resolve()
    if not prompt_file.exists() or not prompt_file.is_file():
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: JIT synthesis prompt template file missing at '{prompt_file}'."
        )
    try:
        content = prompt_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Unable to read JIT synthesis prompt template at '{prompt_file}': {exc}"
        ) from exc
    if not content:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: JIT synthesis prompt template at '{prompt_file}' is empty."
        )
    return content


def synthesize_jurisdiction_profile_jit(
    country: str,
    frameworks: List[str] | None = None,
    region_code: str | None = None,
    registry: JurisdictionalRegistry | None = None,
    policy_store: SynthesizedPolicyStorePort | None = None,
) -> JurisdictionSovereigntyProfile | None:
    """Synthesize at runtime a formal JurisdictionSovereigntyProfile for an unlisted jurisdiction."""
    if not country or len(country.strip()) < 2:
        raise ConfigurationError(
            "Fatal Fail-Closed Policy Error: Country identifier for JIT synthesis must contain at least 2 characters."
        )
    clean_code = (region_code or country.strip()[:2]).strip().upper()
    store = policy_store or get_default_policy_store()

    cached_profile = store.get(clean_code)
    if cached_profile is not None:
        return cached_profile

    prompt_template = _load_jit_prompt_template(registry=registry)
    prompt = prompt_template.format(
        country=country.strip(),
        frameworks=json.dumps(frameworks or []),
        clean_code=clean_code,
    )

    from assessment_engine.infrastructure.genai_client import (
        ModelTier,
        create_genai_client,
        get_model,
    )

    client = create_genai_client()
    model_name = get_model(ModelTier.FAST)

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
    except RuntimeError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Model invocation failed during JIT synthesis for '{country}': {exc}"
        ) from exc

    raw_output = getattr(response, "text", None)
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Empty model response during JIT synthesis for '{country}'."
        )

    text = raw_output.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        synthesized = json.loads(text)
        profile = JurisdictionSovereigntyProfile.model_validate(synthesized, strict=True)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Synthesized JIT profile for '{country}' failed validation: {exc}"
        ) from exc

    store.put(clean_code, profile)

    logger.info(
        "Successfully synthesized and cached JIT jurisdiction profile for '%s' (%s).",
        country,
        clean_code,
    )
    return profile


class JurisdictionalSovereigntyPolicy(BaseSovereignPolicy):
    """Enforces territorial architectural sovereignty across knowledge graphs and deliverables."""

    def __init__(
        self,
        registry: JurisdictionalRegistry | None = None,
        policy_store: SynthesizedPolicyStorePort | None = None,
    ) -> None:
        self.policy_store: SynthesizedPolicyStorePort = policy_store or get_default_policy_store()
        self.registry = registry or load_verified_registry_fail_closed(policy_store=self.policy_store)
        if not self.registry.jurisdictions:
            raise ConfigurationError(
                "Fatal Fail-Closed Policy Error: JurisdictionalSovereigntyPolicy initialized with an empty registry."
            )
        self.resolver = DeterministicJurisdictionResolver(registry=self.registry)

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject jurisdictional invariants into the epistemic graph and enrich document payload."""
        meta = payload.setdefault("document_meta", {})
        client_name = meta.get("client_name", "CLIENT")
        tower_code = meta.get("tower_code", "T0")

        # Extract context
        country_hint = (
            meta.get("country")
            or meta.get("region_code")
            or payload.get("jurisdiction")
        )
        operational_footprints = (
            meta.get("operational_footprints")
            or meta.get("countries")
            or payload.get("operational_footprints")
            or []
        )
        if isinstance(operational_footprints, str):
            operational_footprints = [operational_footprints]

        frameworks = (
            meta.get("regulatory_context")
            or meta.get("regulatory_frameworks")
            or []
        )
        if isinstance(frameworks, str):
            frameworks = [frameworks]

        language = meta.get("language") or meta.get("doc_lang")

        resolution = self.resolver.resolve(
            frameworks=frameworks,
            country=country_hint,
            operational_footprints=operational_footprints,
            language=language,
        )

        code = infer_jurisdiction_code(
            country=country_hint,
            frameworks=frameworks,
            language=language,
            registry=self.registry,
            operational_footprints=operational_footprints,
        )
        profile: JurisdictionSovereigntyProfile | None = self.registry.jurisdictions.get(code)

        # Runtime JIT Resolution if unlisted and country_hint is provided
        if profile is None and country_hint:
            profile = synthesize_jurisdiction_profile_jit(
                str(country_hint),
                frameworks,
                region_code=code,
                registry=self.registry,
                policy_store=self.policy_store,
            )
            if profile is not None:
                self.registry.jurisdictions[code] = profile

        if profile is None:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: No verified JurisdictionSovereigntyProfile resolved for code '{code}'."
            )

        if not profile.architectural_invariants:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Resolved jurisdiction '{code}' contains zero architectural invariants."
            )

        # 1. Enrich payload metadata with multi-partite ontological resolution
        meta["jurisdiction_code"] = code
        meta["jurisdiction_name"] = profile.name
        meta["jurisdictional_sovereignty"] = profile.model_dump()
        meta["jurisdictional_ontology"] = {
            "international_standards": list(resolution.international_standards),
            "supranational_directives": list(resolution.supranational_directives),
            "national_statutes": list(resolution.national_statutes),
            "supranational_member_codes": list(resolution.supranational_member_codes),
            "sovereign_nation_codes": list(resolution.sovereign_nation_codes),
            "effective_jurisdiction_codes": list(resolution.effective_jurisdiction_codes),
        }

        # 2. Augment target projects with jurisdictional deliverables
        primary_invariant = profile.architectural_invariants[0]
        for pillar in payload.get("pillars_analysis", []):
            for proj in pillar.get("projects_todo", []):
                deliverables = proj.setdefault("deliverables", [])
                d_item = f"Architectural Sovereignty Verification: {primary_invariant}"
                if d_item not in deliverables:
                    deliverables.append(d_item)

        # 3. Inject semantic multi-partite sovereignty triples into the epistemic graph
        for std in resolution.international_standards:
            graph.inject_triple(
                subject=client_name,
                predicate="ALIGNS_WITH_INTERNATIONAL_STANDARD",
                object_val=std,
                source="SOVEREIGNTY_POLICY",
                confidence=1.0,
            )

        for directive in resolution.supranational_directives:
            graph.inject_triple(
                subject=client_name,
                predicate="SUBJECT_TO_SUPRANATIONAL_DIRECTIVE",
                object_val=directive,
                source="SOVEREIGNTY_POLICY",
                confidence=1.0,
            )

        for statute in resolution.national_statutes:
            graph.inject_triple(
                subject=client_name,
                predicate="GOVERNED_BY_NATIONAL_STATUTE",
                object_val=statute,
                source="SOVEREIGNTY_POLICY",
                confidence=1.0,
            )

        graph.inject_triple(
            subject=client_name,
            predicate="BOUND_TO_JURISDICTION",
            object_val=profile.name,
            source="SOVEREIGNTY_POLICY",
            confidence=1.0,
        )

        for provider in profile.sovereign_cloud_providers[:2]:
            graph.inject_triple(
                subject=tower_code,
                predicate="QUALIFIED_SOVEREIGN_PROVIDER",
                object_val=provider,
                source="SOVEREIGNTY_POLICY",
                confidence=0.9,
            )

        for i, inv in enumerate(profile.architectural_invariants, 1):
            graph.inject_triple(
                subject=tower_code,
                predicate=f"ENFORCES_JURISDICTIONAL_INVARIANT_{i}",
                object_val=inv,
                source="SOVEREIGNTY_POLICY",
                confidence=0.95,
            )

        return payload
