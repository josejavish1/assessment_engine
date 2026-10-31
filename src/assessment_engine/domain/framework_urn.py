"""Canonical Framework Identifiers (FrameworkURN) and Deterministic Alias Registry.

Eliminates inconsistent string primitives for regulatory frameworks across API
ingress boundaries, caching layers, and policy evaluation engines by normalizing
all identifiers into strict, immutable URN value objects.

Canonical Format:
    urn:lex:standard:<authority>:<standard_id>:<version>
Example:
    urn:lex:standard:iso-iec:27001:2022
"""

from __future__ import annotations

import re
from threading import RLock
from typing import Any, ClassVar, Final, Mapping
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

_CANONICAL_URN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^urn:lex:standard:(?P<authority>[a-z0-9][a-z0-9-]*):(?P<identifier>[a-z0-9][a-z0-9.-]*):(?P<version>[a-z0-9][a-z0-9.-]*)$"
)

_TOKEN_SANITIZER_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")

# Heuristic regexes for dynamic versioned framework extraction
_ISO_DYNAMIC_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^iso(?:[\s/_-]*iec)?[\s/_:-]*(?P<id>\d{4,5})(?:[\s/_:-]+(?P<ver>\d{4}))?$"
)
_SOC2_DYNAMIC_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?:aicpa[\s/_:-]*)?soc[\s/_:-]*2(?:[\s/_:-]*type[\s/_:-]*(?P<type>i|ii|1|2))?(?:[\s/_:-]*(?P<ver>\d{4}))?$"
)


def _normalize_lookup_key(raw: str) -> str:
    """Collapse arbitrary punctuation and whitespace into a deterministic lookup key."""
    cleaned = raw.strip().lower()
    return _TOKEN_SANITIZER_PATTERN.sub("", cleaned)


def _slugify_segment(raw: str) -> str:
    """Convert an arbitrary string into a valid URN segment slug."""
    slug = _TOKEN_SANITIZER_PATTERN.sub("-", raw.strip().lower()).strip("-")
    return slug or "unspecified"


class FrameworkAliasRegistry:
    """Deterministic, thread-safe registry mapping arbitrary framework aliases to canonical URNs."""

    # Canonical Framework URN Constants
    ISO_27001_2022: Final[str] = "urn:lex:standard:iso-iec:27001:2022"
    ISO_27001_2013: Final[str] = "urn:lex:standard:iso-iec:27001:2013"
    ISO_27701_2019: Final[str] = "urn:lex:standard:iso-iec:27701:2019"
    ISO_27017_2015: Final[str] = "urn:lex:standard:iso-iec:27017:2015"
    ISO_27018_2019: Final[str] = "urn:lex:standard:iso-iec:27018:2019"
    ISO_42001_2023: Final[str] = "urn:lex:standard:iso-iec:42001:2023"
    ISO_22301_2019: Final[str] = "urn:lex:standard:iso:22301:2019"
    ISO_9001_2015: Final[str] = "urn:lex:standard:iso:9001:2015"

    NIST_CSF_2_0: Final[str] = "urn:lex:standard:nist:csf:2.0"
    NIST_CSF_1_1: Final[str] = "urn:lex:standard:nist:csf:1.1"
    NIST_800_53_R5: Final[str] = "urn:lex:standard:nist:sp-800-53:r5"
    NIST_800_53_R4: Final[str] = "urn:lex:standard:nist:sp-800-53:r4"
    NIST_800_171_R2: Final[str] = "urn:lex:standard:nist:sp-800-171:r2"
    NIST_800_171_R3: Final[str] = "urn:lex:standard:nist:sp-800-171:r3"
    NIST_AI_RMF_1_0: Final[str] = "urn:lex:standard:nist:ai-rmf:1.0"

    SOC2_2017: Final[str] = "urn:lex:standard:aicpa:soc-2:2017"
    SOC1_2017: Final[str] = "urn:lex:standard:aicpa:soc-1:2017"

    PCI_DSS_4_0: Final[str] = "urn:lex:standard:pci-ssc:pci-dss:4.0"
    PCI_DSS_3_2_1: Final[str] = "urn:lex:standard:pci-ssc:pci-dss:3.2.1"

    EU_GDPR_2016: Final[str] = "urn:lex:standard:eu:gdpr:2016-679"
    EU_DORA_2022: Final[str] = "urn:lex:standard:eu:dora:2022-2554"
    EU_NIS2_2022: Final[str] = "urn:lex:standard:eu:nis2:2022-2555"
    EU_AI_ACT_2024: Final[str] = "urn:lex:standard:eu:ai-act:2024-1689"

    US_HIPAA_2013: Final[str] = "urn:lex:standard:us-hhs:hipaa:2013"
    US_SOX_2002: Final[str] = "urn:lex:standard:us-congress:sox:2002"
    US_CCPA_2018: Final[str] = "urn:lex:standard:us-ca:ccpa:2018"
    US_CPRA_2020: Final[str] = "urn:lex:standard:us-ca:cpra:2020"
    US_FEDRAMP_R5: Final[str] = "urn:lex:standard:us-gsa:fedramp:r5"

    CIS_CONTROLS_V8: Final[str] = "urn:lex:standard:cis:controls:8.0"
    CIS_CONTROLS_V7: Final[str] = "urn:lex:standard:cis:controls:7.1"

    COBIT_2019: Final[str] = "urn:lex:standard:isaca:cobit:2019"
    CSA_CCM_V4: Final[str] = "urn:lex:standard:csa:ccm:4.0"
    OWASP_ASVS_4_0: Final[str] = "urn:lex:standard:owasp:asvs:4.0"
    OWASP_TOP10_2021: Final[str] = "urn:lex:standard:owasp:top-10:2021"
    ENS_2022: Final[str] = "urn:lex:standard:es-ccn:ens:2022"
    BSI_C5_2020: Final[str] = "urn:lex:standard:de-bsi:c5:2020"
    SWIFT_CSC_2024: Final[str] = "urn:lex:standard:swift:cscf:2024"

    _lock: ClassVar[RLock] = RLock()

    _DEFAULT_ALIAS_MAP: ClassVar[ dict[str, str] ] = {
        # ISO/IEC 27001 (defaults to current 2022 edition unless 2013 is specified)
        "iso27001": ISO_27001_2022,
        "isoiec27001": ISO_27001_2022,
        "iso270012022": ISO_27001_2022,
        "isoiec270012022": ISO_27001_2022,
        "isostandard27001": ISO_27001_2022,
        "iso270012013": ISO_27001_2013,
        "isoiec270012013": ISO_27001_2013,
        # ISO/IEC 27701
        "iso27701": ISO_27701_2019,
        "isoiec27701": ISO_27701_2019,
        "iso277012019": ISO_27701_2019,
        "isoiec277012019": ISO_27701_2019,
        # ISO/IEC 27017 & 27018
        "iso27017": ISO_27017_2015,
        "isoiec27017": ISO_27017_2015,
        "iso270172015": ISO_27017_2015,
        "isoiec270172015": ISO_27017_2015,
        "iso27018": ISO_27018_2019,
        "isoiec27018": ISO_27018_2019,
        "iso270182019": ISO_27018_2019,
        "isoiec270182019": ISO_27018_2019,
        # ISO/IEC 42001
        "iso42001": ISO_42001_2023,
        "isoiec42001": ISO_42001_2023,
        "iso420012023": ISO_42001_2023,
        "isoiec420012023": ISO_42001_2023,
        # ISO 22301 & 9001
        "iso22301": ISO_22301_2019,
        "iso223012019": ISO_22301_2019,
        "iso9001": ISO_9001_2015,
        "iso90012015": ISO_9001_2015,
        # NIST CSF
        "nistcsf": NIST_CSF_2_0,
        "nistcsf2": NIST_CSF_2_0,
        "nistcsf20": NIST_CSF_2_0,
        "nistcybersecurityframework": NIST_CSF_2_0,
        "nistcybersecurityframework20": NIST_CSF_2_0,
        "csf20": NIST_CSF_2_0,
        "nistcsf11": NIST_CSF_1_1,
        "csf11": NIST_CSF_1_1,
        # NIST SP 800-53
        "nist80053": NIST_800_53_R5,
        "nistsp80053": NIST_800_53_R5,
        "nist80053r5": NIST_800_53_R5,
        "nist80053rev5": NIST_800_53_R5,
        "nistsp80053r5": NIST_800_53_R5,
        "nistsp80053rev5": NIST_800_53_R5,
        "sp80053": NIST_800_53_R5,
        "sp80053r5": NIST_800_53_R5,
        "sp80053rev5": NIST_800_53_R5,
        "nist80053r4": NIST_800_53_R4,
        "nist80053rev4": NIST_800_53_R4,
        "nistsp80053r4": NIST_800_53_R4,
        "nistsp80053rev4": NIST_800_53_R4,
        # NIST SP 800-171
        "nist800171": NIST_800_171_R2,
        "nistsp800171": NIST_800_171_R2,
        "nist800171r2": NIST_800_171_R2,
        "nist800171rev2": NIST_800_171_R2,
        "nistsp800171r2": NIST_800_171_R2,
        "nist800171r3": NIST_800_171_R3,
        "nist800171rev3": NIST_800_171_R3,
        "nistsp800171r3": NIST_800_171_R3,
        # NIST AI RMF
        "nistairmf": NIST_AI_RMF_1_0,
        "nistairmf10": NIST_AI_RMF_1_0,
        "airmf": NIST_AI_RMF_1_0,
        "airmf10": NIST_AI_RMF_1_0,
        # SOC 2 & SOC 1
        "soc2": SOC2_2017,
        "soc2type1": SOC2_2017,
        "soc2type2": SOC2_2017,
        "soc2typei": SOC2_2017,
        "soc2typeii": SOC2_2017,
        "aicpasoc2": SOC2_2017,
        "aicpasoc2type2": SOC2_2017,
        "aicpasoc2typeii": SOC2_2017,
        "soc22017": SOC2_2017,
        "soc1": SOC1_2017,
        "aicpasoc1": SOC1_2017,
        "soc12017": SOC1_2017,
        # PCI-DSS
        "pcidss": PCI_DSS_4_0,
        "pci": PCI_DSS_4_0,
        "pcidss4": PCI_DSS_4_0,
        "pcidss40": PCI_DSS_4_0,
        "pcidssv4": PCI_DSS_4_0,
        "pcidssv40": PCI_DSS_4_0,
        "pcidss321": PCI_DSS_3_2_1,
        "pcidssv321": PCI_DSS_3_2_1,
        # European Union Regulations
        "gdpr": EU_GDPR_2016,
        "eugdpr": EU_GDPR_2016,
        "gdpr2016679": EU_GDPR_2016,
        "generaldataprotectionregulation": EU_GDPR_2016,
        "dora": EU_DORA_2022,
        "eudora": EU_DORA_2022,
        "dora2022": EU_DORA_2022,
        "nis2": EU_NIS2_2022,
        "eunis2": EU_NIS2_2022,
        "nis22022": EU_NIS2_2022,
        "euaiact": EU_AI_ACT_2024,
        "aiact": EU_AI_ACT_2024,
        "euaiact2024": EU_AI_ACT_2024,
        # US Regulations & Standards
        "hipaa": US_HIPAA_2013,
        "ushipaa": US_HIPAA_2013,
        "hipaa2013": US_HIPAA_2013,
        "sox": US_SOX_2002,
        "sarbanesoxley": US_SOX_2002,
        "sox2002": US_SOX_2002,
        "ccpa": US_CCPA_2018,
        "caccpa": US_CCPA_2018,
        "ccpa2018": US_CCPA_2018,
        "cpra": US_CPRA_2020,
        "cacpra": US_CPRA_2020,
        "cpra2020": US_CPRA_2020,
        "fedramp": US_FEDRAMP_R5,
        "fedrampr5": US_FEDRAMP_R5,
        "fedramprev5": US_FEDRAMP_R5,
        # CIS Controls
        "cis": CIS_CONTROLS_V8,
        "ciscontrols": CIS_CONTROLS_V8,
        "cisv8": CIS_CONTROLS_V8,
        "cis8": CIS_CONTROLS_V8,
        "ciscontrolsv8": CIS_CONTROLS_V8,
        "ciscontrols8": CIS_CONTROLS_V8,
        "ciscontrols80": CIS_CONTROLS_V8,
        "cisv7": CIS_CONTROLS_V7,
        "cis71": CIS_CONTROLS_V7,
        "ciscontrolsv71": CIS_CONTROLS_V7,
        # ISACA COBIT
        "cobit": COBIT_2019,
        "cobit2019": COBIT_2019,
        "isacacobit": COBIT_2019,
        "isacacobit2019": COBIT_2019,
        # CSA CCM
        "csaccm": CSA_CCM_V4,
        "ccm": CSA_CCM_V4,
        "csaccmv4": CSA_CCM_V4,
        "csaccm40": CSA_CCM_V4,
        "ccmv4": CSA_CCM_V4,
        # OWASP
        "owaspasvs": OWASP_ASVS_4_0,
        "asvs": OWASP_ASVS_4_0,
        "owaspasvs40": OWASP_ASVS_4_0,
        "owasptop10": OWASP_TOP10_2021,
        "owasptop102021": OWASP_TOP10_2021,
        # National Standards (ENS, BSI C5, SWIFT)
        "ens": ENS_2022,
        "ens2022": ENS_2022,
        "bsic5": BSI_C5_2020,
        "c5": BSI_C5_2020,
        "bsic52020": BSI_C5_2020,
        "swiftcsc": SWIFT_CSC_2024,
        "swiftcscf": SWIFT_CSC_2024,
        "swiftcscf2024": SWIFT_CSC_2024,
    }

    _custom_aliases: ClassVar[dict[str, str]] = {}

    @classmethod
    def register_alias(cls, alias: str, canonical_urn: str) -> None:
        """Register a custom alias to a validated canonical FrameworkURN string."""
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError("Framework alias must be a non-empty string.")
        normalized_urn = canonical_urn.strip().lower()
        if not _CANONICAL_URN_PATTERN.match(normalized_urn):
            raise ValueError(
                f"Target URN '{canonical_urn}' does not match canonical schema "
                "'urn:lex:standard:<authority>:<identifier>:<version>'."
            )
        key = _normalize_lookup_key(alias)
        if not key:
            raise ValueError(f"Alias '{alias}' contains no alphanumeric characters.")
        with cls._lock:
            cls._custom_aliases[key] = normalized_urn

    @classmethod
    def get_registered_aliases(cls) -> Mapping[str, str]:
        """Return an immutable snapshot of all active alias mappings."""
        with cls._lock:
            merged = dict(cls._DEFAULT_ALIAS_MAP)
            merged.update(cls._custom_aliases)
            return merged

    @classmethod
    def resolve(cls, raw_input: str) -> str:
        """Deterministically resolve an arbitrary framework identifier or URN into canonical URN form."""
        if not isinstance(raw_input, str):
            raise TypeError(f"Expected string or FrameworkURN, got {type(raw_input).__name__}.")

        cleaned = raw_input.strip()
        if not cleaned:
            raise ValueError("Framework identifier cannot be empty or whitespace.")

        lowered = cleaned.lower()

        # 1. Any input starting with 'urn:' must strictly validate against canonical URN syntax
        if lowered.startswith("urn:"):
            if _CANONICAL_URN_PATTERN.match(lowered):
                return lowered
            raise ValueError(
                f"Invalid canonical FrameworkURN syntax: '{raw_input}'. "
                "Expected 'urn:lex:standard:<authority>:<identifier>:<version>'."
            )

        # 2. Exact deterministic lookup via sanitized alphanumeric key
        lookup_key = _normalize_lookup_key(lowered)
        if not lookup_key:
            raise ValueError(
                f"Framework identifier '{raw_input}' must contain at least one alphanumeric character."
            )

        with cls._lock:
            if lookup_key in cls._custom_aliases:
                return cls._custom_aliases[lookup_key]
            if lookup_key in cls._DEFAULT_ALIAS_MAP:
                return cls._DEFAULT_ALIAS_MAP[lookup_key]

        # 3. Structured pattern matching for ISO/IEC standards with explicit/implicit versions
        iso_match = _ISO_DYNAMIC_PATTERN.match(lowered)
        if iso_match:
            std_id = iso_match.group("id")
            std_ver = iso_match.group("ver") or "latest"
            authority = "iso-iec" if std_id.startswith(("27", "42", "20", "15")) else "iso"
            return f"urn:lex:standard:{authority}:{std_id}:{std_ver}"

        soc2_match = _SOC2_DYNAMIC_PATTERN.match(lowered)
        if soc2_match:
            std_ver = soc2_match.group("ver") or "2017"
            return f"urn:lex:standard:aicpa:soc-2:{std_ver}"

        # 4. Deterministic fallback for custom or proprietary organizational standards
        slug = _slugify_segment(lowered)
        return f"urn:lex:standard:custom:{slug}:v1"


class FrameworkURN(str):
    """Immutable, canonical Value Object representing a normalized regulatory framework identifier.

    Subclasses `str` so it remains 100% backwards-compatible with string operations,
    dictionary keys, JSON serialization, SQLite parameter binding, and regex matching,
    while enforcing canonical URN normalization at instantiation and API ingress.
    """

    __slots__ = ("_authority", "_identifier", "_version")

    _authority: str
    _identifier: str
    _version: str

    def __new__(cls, value: str | FrameworkURN) -> FrameworkURN:
        if isinstance(value, FrameworkURN):
            return value
        canonical = FrameworkAliasRegistry.resolve(value)
        match = _CANONICAL_URN_PATTERN.match(canonical)
        if not match:
            raise ValueError(f"Failed to construct valid FrameworkURN from '{value}'.")
        instance = super().__new__(cls, canonical)
        object.__setattr__(instance, "_authority", match.group("authority"))
        object.__setattr__(instance, "_identifier", match.group("identifier"))
        object.__setattr__(instance, "_version", match.group("version"))
        return instance

    @classmethod
    def from_alias(cls, alias: str | FrameworkURN) -> FrameworkURN:
        """Explicit factory method to resolve an arbitrary alias into a FrameworkURN."""
        return cls(alias)

    @property
    def urn(self) -> str:
        """Return the canonical URN string primitive."""
        return str(self)

    @property
    def authority(self) -> str:
        """Issuing standards body or regulatory authority (e.g., 'iso-iec', 'nist', 'eu')."""
        return self._authority

    @property
    def identifier(self) -> str:
        """Standard or regulation code within the authority (e.g., '27001', 'csf', 'gdpr')."""
        return self._identifier

    @property
    def version(self) -> str:
        """Revision, publication year, or enactment identifier (e.g., '2022', '2.0', 'r5')."""
        return self._version

    def __repr__(self) -> str:
        return f"FrameworkURN('{super().__str__()}')"

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrameworkURN):
            return super().__eq__(other)
        if isinstance(other, str):
            try:
                other_canonical = FrameworkAliasRegistry.resolve(other)
                return super().__eq__(other_canonical)
            except ValueError:
                return False
        return False

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Integrate natively with Pydantic v2 validation and serialization pipelines."""
        return core_schema.no_info_after_validator_function(
            cls._validate_pydantic,
            core_schema.str_schema(min_length=1),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema_obj: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """Publish OpenAPI / JSON Schema metadata for canonical FrameworkURN fields."""
        json_schema = handler(core_schema_obj)
        json_schema.update(
            {
                "type": "string",
                "format": "urn",
                "pattern": _CANONICAL_URN_PATTERN.pattern,
                "examples": [
                    FrameworkAliasRegistry.ISO_27001_2022,
                    FrameworkAliasRegistry.NIST_CSF_2_0,
                    FrameworkAliasRegistry.SOC2_2017,
                ],
                "description": (
                    "Canonical regulatory framework URN "
                    "(e.g., 'urn:lex:standard:iso-iec:27001:2022'). "
                    "Accepts common aliases at ingress and normalizes them automatically."
                ),
            }
        )
        return json_schema

    @classmethod
    def _validate_pydantic(cls, value: Any) -> FrameworkURN:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(value)
        raise ValueError(f"Expected string or FrameworkURN, received {type(value).__name__}.")


def normalize_framework_urn(framework: str | FrameworkURN) -> FrameworkURN:
    """Helper function to normalize a single framework string or URN into a FrameworkURN."""
    return FrameworkURN(framework)


def normalize_framework_list(
    frameworks: list[str | FrameworkURN] | tuple[str | FrameworkURN, ...],
) -> list[FrameworkURN]:
    """Normalize and deduplicate a sequence of framework identifiers while preserving order."""
    seen: set[str] = set()
    normalized: list[FrameworkURN] = []
    for item in frameworks:
        urn_obj = FrameworkURN(item)
        urn_str = str(urn_obj)
        if urn_str not in seen:
            seen.add(urn_str)
            normalized.append(urn_obj)
    return normalized


__all__ = [
    "FrameworkAliasRegistry",
    "FrameworkURN",
    "normalize_framework_list",
    "normalize_framework_urn",
]
