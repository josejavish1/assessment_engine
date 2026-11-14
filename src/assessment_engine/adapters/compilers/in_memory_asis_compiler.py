"""Internal Actuarial Calculation & Data Extraction Provider for AST Compilers.

Provides shared pure-function helpers for PayloadToASTBridge and Volume1AsisASTCompiler:
- CMMI maturity band resolution and label formatting
- P90 compound failure hours and tail risk estimation
- Multilingual currency and frequency formatting
- Health check and risk payload extraction logic
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from assessment_engine.domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    resolve_maturity_band,
)
from assessment_engine.domain.services.dynamic_custody_resolver import (
    DynamicCustodyResolver,
)
from assessment_engine.domain.taxonomy_resolver import (
    extract_pillar_identifiers,
    get_taxonomy_resolver,
)
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    get_localized_list,
    t,
)

logger = logging.getLogger(__name__)

LOW_MATURITY_CALIBRATION_THRESHOLD: Final[float] = 2.20
DIVERGENCE_RATIONALE_THRESHOLD: Final[float] = 0.50
DEFAULT_PILLAR_ASSESSMENT_SCORE: Final[float] = 2.50


@lru_cache(maxsize=1)
def _load_cmmi_progression_matrix() -> Mapping[str, Any]:
    """Cached loader for deterministic CMMI progression milestones."""
    repo_root = _find_repo_root()
    matrix_path = repo_root / "engine_config/policies/cmmi_progression_matrix.json"
    if matrix_path.exists():
        try:
            with open(matrix_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return MappingProxyType(data)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed reading cmmi_progression_matrix: %s", exc)
    return MappingProxyType({})


@lru_cache(maxsize=1)
def _load_sota_industry_benchmarks() -> Mapping[str, Any]:
    """Cached loader for SOTA industry and empirical research benchmarks."""
    repo_root = _find_repo_root()
    benchmarks_path = repo_root / "engine_config/frameworks/sota_industry_benchmarks.json"
    if benchmarks_path.exists():
        try:
            with open(benchmarks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return MappingProxyType(data)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed reading sota_industry_benchmarks: %s", exc)
    return MappingProxyType({})


@lru_cache(maxsize=1)
def _load_cross_domain_nexus() -> Mapping[str, Any]:
    """Cached loader for cross-domain blast radius and systemic interdependencies."""
    repo_root = _find_repo_root()
    nexus_path = repo_root / "engine_config/policies/cross_domain_nexus_map.json"
    if nexus_path.exists():
        try:
            with open(nexus_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return MappingProxyType(data)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed reading cross_domain_nexus_map: %s", exc)
    return MappingProxyType({})


def _resolve_localized_catalog_entry(
    catalog: Mapping[str, Any], canonical_pillar_id: str, doc_lang: str
) -> str:
    """Safely resolves a localized narrative string from a pillar catalog with BCP-47 fallback."""
    pillars = catalog.get("pillars")
    if not isinstance(pillars, Mapping):
        return ""
    p_entry = pillars.get(canonical_pillar_id)
    if not isinstance(p_entry, Mapping):
        return ""

    normalized_lang = (doc_lang or "en").strip().lower()
    base_lang = normalized_lang.split("-")[0].split("_")[0]

    text = (
        p_entry.get(doc_lang)
        or p_entry.get(normalized_lang)
        or p_entry.get(base_lang)
        or p_entry.get("en")
        or ""
    )
    return str(text).strip()


def _build_sota_benchmark_paragraph(canonical_pillar_id: str, doc_lang: str) -> str:
    """Retrieves and formats the 4th source SOTA empirical benchmark narrative for the pillar."""
    return _resolve_localized_catalog_entry(
        _load_sota_industry_benchmarks(), canonical_pillar_id, doc_lang
    )


def _build_cross_domain_nexus(canonical_pillar_id: str, doc_lang: str) -> str:
    """Retrieves and formats the cross-domain blast radius narrative for the pillar."""
    return _resolve_localized_catalog_entry(
        _load_cross_domain_nexus(), canonical_pillar_id, doc_lang
    )


def _build_evidence_footnote(
    pillar: dict[str, Any], canonical_pillar_id: str, doc_lang: str
) -> str:
    """Constructs a deterministic, forensic evidence trace footnote for the capability."""
    thought = str(pillar.get("thought_process") or "")
    lit_ev = str(pillar.get("literal_evidence") or "")
    combined_ev = f"{thought} {lit_ev}"

    turn_matches = re.findall(r"(?:Turno|Turn)\s*(\d+)", combined_ev, re.IGNORECASE)
    if turn_matches:
        sorted_turns = sorted(set(turn_matches), key=int)
        turns_display = ", ".join(sorted_turns[:4])
        turns_text = t("evidence_interview_turns", locale=doc_lang, turns=turns_display)
    else:
        turns_text = t("evidence_interview_general", locale=doc_lang)

    sota_cat = _load_sota_industry_benchmarks()
    authority = sota_cat.get("pillars", {}).get(canonical_pillar_id, {}).get("authority", "CMMI v2.0 International Standard")

    p_id = pillar.get("pillar_id") or canonical_pillar_id
    survey_prefix = t("evidence_survey_label", locale=doc_lang)
    return f"{survey_prefix} ({p_id}) · {turns_text} · {authority}"

_CANONICAL_SEVERITY_ENUM_TOKENS: Final[frozenset[str]] = frozenset({
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "ELEVATED",
    "MODERATE",
    "SEVERE",
    "NEGLIGIBLE",
    "INFO",
    "INFORMATIONAL",
    "EXTREME",
    "MAJOR",
    "MINOR",
})

_PUNCTUATION_STRIP_CHARS: Final[str] = " .,;:!?-_()[]{}\"'/\\"
_SUBTOKEN_DELIMITER_RE: Final[re.Pattern[str]] = re.compile(r"([-–—/+])")
_SEVERITY_WORD_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"[\s\-–—/|,:;()\[\]{}]+")
_ROMAN_NUMERAL_RE: Final[re.Pattern[str]] = re.compile(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)$")


_SHORT_SEVERITY_CODE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:P[0-5]|SEV-?[0-5]|S[0-5]|CAT-?(?:I|II|III|IV|V|VI|VII|VIII|IX|X|[1-5])|TIER-?[0-4])$",
    re.IGNORECASE,
)

_CANONICAL_ACRONYM_MAP: Final[Mapping[str, str]] = MappingProxyType({
    # Virtualization, Cloud & Infrastructure
    "SAAS": "SaaS",
    "PAAS": "PaaS",
    "IAAS": "IaaS",
    "DAAS": "DaaS",
    "VDI": "VDI",
    "DEX": "DEX",
    "EUC": "EUC",
    "MDM": "MDM",
    "MAM": "MAM",
    "UEM": "UEM",
    "GPO": "GPO",
    "WSUS": "WSUS",
    "SCCM": "SCCM",
    "MECM": "MECM",
    "OEM": "OEM",
    "TPM": "TPM",
    "UEFI": "UEFI",
    "BIOS": "BIOS",
    "PXE": "PXE",
    "ESXI": "ESXi",
    "VCPU": "vCPU",
    "GRPC": "gRPC",
    "MTLS": "mTLS",
    "NVME": "NVMe",
    "K8S": "K8s",
    "SDWAN": "SD-WAN",
    "CRAC": "CRAC",
    "CRAH": "CRAH",
    "UPS": "UPS",
    "PDU": "PDU",
    "ATS": "ATS",
    "BMS": "BMS",
    "DCIM": "DCIM",
    # Networking & Security
    "API": "API",
    "REST": "REST",
    "TLS": "TLS",
    "SSL": "SSL",
    "IAM": "IAM",
    "PAM": "PAM",
    "MFA": "MFA",
    "SSO": "SSO",
    "RBAC": "RBAC",
    "ABAC": "ABAC",
    "SAML": "SAML",
    "OIDC": "OIDC",
    "LDAP": "LDAP",
    "LDAPS": "LDAPS",
    "AD": "AD",
    "ENTRA": "Entra",
    "CIS": "CIS",
    "NIST": "NIST",
    "ISO": "ISO",
    "IEC": "IEC",
    "ISA": "ISA",
    "CMMI": "CMMI",
    "OWASP": "OWASP",
    "SOC": "SOC",
    "SIEM": "SIEM",
    "SOAR": "SOAR",
    "EDR": "EDR",
    "XDR": "XDR",
    "NDR": "NDR",
    "WAF": "WAF",
    "ZTNA": "ZTNA",
    "SASE": "SASE",
    "NAC": "NAC",
    "DLP": "DLP",
    "CASB": "CASB",
    "PKI": "PKI",
    "HSM": "HSM",
    "KMS": "KMS",
    "WORM": "WORM",
    "LAN": "LAN",
    "WAN": "WAN",
    "WLAN": "WLAN",
    "WIFI": "Wi-Fi",
    "MPLS": "MPLS",
    "BGP": "BGP",
    "OSPF": "OSPF",
    "VLAN": "VLAN",
    "VXLAN": "VXLAN",
    "VPN": "VPN",
    "SAN": "SAN",
    "NAS": "NAS",
    "IOPS": "IOPS",
    "RAID": "RAID",
    "DNS": "DNS",
    "DHCP": "DHCP",
    "NTP": "NTP",
    "SNMP": "SNMP",
    "SMTP": "SMTP",
    "IMAP": "IMAP",
    "POP3": "POP3",
    "SSH": "SSH",
    "RDP": "RDP",
    "SMB": "SMB",
    "NFS": "NFS",
    # Industrial OT & Manufacturing
    "SCADA": "SCADA",
    "PLC": "PLC",
    "ICS": "ICS",
    "DCS": "DCS",
    "RTU": "RTU",
    "HMI": "HMI",
    "OPC-UA": "OPC-UA",
    "CNC": "CNC",
    "IIOT": "IIoT",
    "MES": "MES",
    "PLM": "PLM",
    # Healthcare & Clinical Systems
    "PACS": "PACS",
    "EHR": "EHR",
    "EMR": "EMR",
    "HL7": "HL7",
    "FHIR": "FHIR",
    "DICOM": "DICOM",
    # Banking, Retail & ERP
    "SWIFT": "SWIFT",
    "SEPA": "SEPA",
    "PCI-DSS": "PCI-DSS",
    "POS": "POS",
    "WMS": "WMS",
    "SCM": "SCM",
    "ERP": "ERP",
    "CRM": "CRM",
    "ITSM": "ITSM",
    "CMDB": "CMDB",
    "ITIL": "ITIL",
    # Operations, Resilience & Actuarial FAIR
    "SPOF": "SPOF",
    "MTTR": "MTTR",
    "MTBF": "MTBF",
    "RPO": "RPO",
    "RTO": "RTO",
    "SLA": "SLA",
    "SLO": "SLO",
    "KPI": "KPI",
    "VM": "VM",
    "RAM": "RAM",
    "CPU": "CPU",
    "GPU": "GPU",
    "TPU": "TPU",
    "LLM": "LLM",
    "AI": "AI",
    "ML": "ML",
    "OT": "OT",
    "IT": "IT",
    "DRP": "DRP",
    "BCP": "BCP",
    "FAIR": "FAIR",
    "ALE": "ALE",
    "SLE": "SLE",
    "ARO": "ARO",
    "TEF": "TEF",
    "VULN": "VULN",
    "TCO": "TCO",
    "CI": "CI",
    "CD": "CD",
})

_KNOWN_UPPERCASE_ACRONYMS: Final[frozenset[str]] = frozenset(_CANONICAL_ACRONYM_MAP.keys())

_DESIGNATOR_PREFIX_NOUNS: Final[frozenset[str]] = frozenset({
    "tier", "feed", "zone", "phase", "type", "class", "cat", "category",
    "hall", "room", "block", "line", "bus", "path", "side", "chain", "level",
    "segment", "cluster", "node", "unit",
})

_QUALIFIER_HEADER_TOKENS: Final[frozenset[str]] = frozenset({
    "SEVERITY", "SEV", "IMPACT", "RISK", "LEVEL", "PRIORITY", "TIER", "CATEGORY", "CAT",
    "CLASS", "GRADE", "RATING", "STATUS", "BAND", "SCORE", "TO", "AND", "OR",
})


def _is_severity_enum_token(text: str, doc_lang: str) -> bool:
    """Return True if candidate text is a bare or compound ordinal severity label in canonical or active locale."""
    normalized = str(text or "").strip(_PUNCTUATION_STRIP_CHARS).upper()
    if not normalized:
        return False
    if normalized in _CANONICAL_SEVERITY_ENUM_TOKENS or bool(_SHORT_SEVERITY_CODE_RE.fullmatch(normalized)):
        return True

    localized_tokens = {
        str(tok).strip(_PUNCTUATION_STRIP_CHARS).upper()
        for tok in get_localized_list("severity_enum_tokens", locale=doc_lang, default=[])
        if str(tok).strip(_PUNCTUATION_STRIP_CHARS)
    }
    if normalized in localized_tokens:
        return True

    all_severity_values = _CANONICAL_SEVERITY_ENUM_TOKENS | localized_tokens
    all_severity_qualifiers = all_severity_values | _QUALIFIER_HEADER_TOKENS

    subtokens = [
        tok.strip(_PUNCTUATION_STRIP_CHARS)
        for tok in _SEVERITY_WORD_SPLIT_RE.split(normalized)
        if tok.strip(_PUNCTUATION_STRIP_CHARS)
    ]
    if not subtokens or len(subtokens) > 5:
        return False

    has_core_severity = False
    for sub in subtokens:
        if sub in all_severity_values or bool(_SHORT_SEVERITY_CODE_RE.fullmatch(sub)):
            has_core_severity = True
        elif sub in all_severity_qualifiers or bool(_ROMAN_NUMERAL_RE.fullmatch(sub)) or (sub.isdigit() and 0 <= int(sub) <= 5):
            continue
        else:
            return False

    return has_core_severity


def _decapitalize_single_subtoken(
    subtoken: str,
    *,
    is_post_delimiter: bool = False,
    prev_word_lower: str = "",
) -> str:
    """Decapitalize a single non-delimited word while preserving technical acronyms, designators, and camelCase."""
    punct_chars = ".,;:!?_()[]{}\"'`"
    stripped = subtoken.strip(punct_chars)
    if not stripped:
        return subtoken

    prefix_len = len(subtoken) - len(subtoken.lstrip(punct_chars))
    suffix_len = len(subtoken) - len(subtoken.rstrip(punct_chars))
    leading_punct = subtoken[:prefix_len] if prefix_len > 0 else ""
    trailing_punct = subtoken[len(subtoken) - suffix_len :] if suffix_len > 0 else ""

    # Preserve single-letter uppercase designators or Roman numerals after a delimiter or designator noun
    is_designator_context = is_post_delimiter or (prev_word_lower in _DESIGNATOR_PREFIX_NOUNS)
    if is_designator_context and (
        (len(stripped) == 1 and stripped.isupper())
        or bool(_ROMAN_NUMERAL_RE.fullmatch(stripped))
    ):
        return subtoken

    # Repair corrupted camelCase acronym prefixes (e.g., "pAM" -> "PAM", "cIS" -> "CIS", "mFA" -> "MFA")
    if len(stripped) >= 2 and stripped[0].islower() and stripped[1:].isupper():
        upper_cand = stripped.upper()
        if upper_cand in _CANONICAL_ACRONYM_MAP:
            return f"{leading_punct}{_CANONICAL_ACRONYM_MAP[upper_cand]}{trailing_punct}"
        if len(stripped) <= 5:
            return f"{leading_punct}{upper_cand}{trailing_punct}"

    # Preserve internal camelCase / PascalCase with internal uppercase (e.g., "FortiGate", "OpenShift", "SaaS")
    if any(c.isupper() for c in stripped[1:]) and any(c.islower() for c in stripped):
        return subtoken

    # Canonicalize known technical acronyms
    upper_stripped = stripped.upper()
    if upper_stripped in _CANONICAL_ACRONYM_MAP:
        if stripped.isupper() and len(stripped) > 1:
            return subtoken
        return f"{leading_punct}{_CANONICAL_ACRONYM_MAP[upper_stripped]}{trailing_punct}"

    if len(stripped) > 1 and stripped.isupper():
        return subtoken

    return f"{leading_punct}{stripped.lower()}{trailing_punct}"


def _decapitalize_clause_preserving_acronyms(text: str) -> str:
    """Convert nominal title phrases to sentence-case while preserving technical acronyms across hyphen/slash boundaries."""
    cleaned = str(text or "").strip().rstrip(".")
    if not cleaned:
        return ""

    tokens = cleaned.split()
    reconstructed: list[str] = []
    prev_lower = ""

    for tok in tokens:
        stripped_whole = tok.strip(".,;:!?_()[]{}\"'`")
        if stripped_whole.upper() in _CANONICAL_ACRONYM_MAP:
            canonical_whole = _CANONICAL_ACRONYM_MAP[stripped_whole.upper()]
            replaced = tok.replace(stripped_whole, canonical_whole)
            reconstructed.append(replaced)
            prev_lower = stripped_whole.lower()
            continue

        subparts = _SUBTOKEN_DELIMITER_RE.split(tok)
        processed_parts: list[str] = []
        seen_delimiter = False
        for part in subparts:
            if _SUBTOKEN_DELIMITER_RE.fullmatch(part):
                processed_parts.append(part)
                seen_delimiter = True
            else:
                processed_parts.append(
                    _decapitalize_single_subtoken(
                        part,
                        is_post_delimiter=seen_delimiter,
                        prev_word_lower=prev_lower,
                    )
                )
        reconstructed.append("".join(processed_parts))
        prev_lower = stripped_whole.lower()

    return " ".join(reconstructed)


def _extract_verified_business_risk(
    hc: dict[str, Any],
    domain_label: str,
    doc_lang: str,
) -> str:
    """Extract qualitative operational risk narrative from a finding node,

    strictly prohibiting fallback to categorical severity enums and delegating
    all localized fallback templates to the localization catalog.
    """
    for candidate_key in ("business_risk", "primary_impact", "operational_impact"):
        candidate = str(hc.get(candidate_key) or "").strip()
        if (
            candidate
            and not _is_severity_enum_token(candidate, doc_lang)
            and len(candidate.split()) >= 4
        ):
            return candidate

    default_control_label = t(
        "asis_compiler_default_evaluated_control",
        locale=doc_lang,
    )
    raw_title = str(
        hc.get("capability") or hc.get("title") or hc.get("name") or default_control_label
    ).strip().rstrip(".")
    title = _decapitalize_clause_preserving_acronyms(raw_title)

    raw_finding = str(hc.get("finding") or hc.get("description") or "").strip().rstrip(".")
    if (
        raw_finding
        and not _is_severity_enum_token(raw_finding, doc_lang)
        and len(raw_finding.split()) >= 6
    ):
        formatted_finding = _decapitalize_clause_preserving_acronyms(raw_finding)
        return t(
            "asis_compiler_fallback_business_risk_from_finding",
            locale=doc_lang,
            finding=formatted_finding,
        )

    formatted_domain = _decapitalize_clause_preserving_acronyms(domain_label)
    return t(
        "asis_compiler_fallback_business_risk_from_capability",
        locale=doc_lang,
        capability=title,
        domain=formatted_domain,
    )


def derive_in_memory_fair_risks(
    b_data: dict[str, Any],
    doc_lang: str,
    currency: str,
    rate_mult: float = 1.0,
    active_towers_scope: set[str] | list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Extract and calibrate FAIR risk scenarios directly from in-memory payload.

    Applies DynamicCustodyResolver to prevent actuarial blind spots in partial-scope assessments.

    Returns:
        Tuple of (flat_risks_list, risks_by_pillar_dict).
    """
    resolver = get_taxonomy_resolver()
    risks_data_list: list[dict[str, Any]] = []
    risks_by_pillar: dict[str, list[dict[str, Any]]] = {}

    first_p = str((b_data.get("pillars_analysis") or [{}])[0].get("pillar_id") or "")
    inferred_t = first_p.split(".")[0].upper() if "." in first_p else None
    current_tower_id = str(
        b_data.get("tower_id")
        or b_data.get("document_meta", {}).get("tower_id")
        or inferred_t
        or "T1"
    ).upper()
    norm_scope = {str(t_id).strip().upper() for t_id in active_towers_scope} if active_towers_scope else None
    custody_resolver = DynamicCustodyResolver(
        active_towers_scope=norm_scope,
        localizer=lambda key, **kwargs: t(key, locale=doc_lang, **kwargs),
    )

    root_hourly_rate = float(
        (b_data.get("financial_telemetry") or {}).get("authoritative_hourly_downtime_cost")
        or b_data.get("explicit_hourly_downtime_cost")
        or b_data.get("hourly_burn_rate")
        or 1650.0
    )

    r_counter = 1
    for pillar in b_data.get("pillars_analysis", []):
        p_id, raw_pname = extract_pillar_identifiers(pillar)
        pillar_name = resolver.resolve_pillar_by_any_reference(
            p_id or raw_pname,
            default=(raw_pname or p_id or "Pillar"),
            locale=doc_lang,
            tower_id=current_tower_id,
        )

        for hc in pillar.get("health_check_asis", []):
            finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
            raw_risk = str(hc.get("business_risk") or hc.get("primary_impact") or "").strip()
            if raw_risk and not _is_severity_enum_token(raw_risk, doc_lang) and len(raw_risk.split()) >= 4:
                business_risk = raw_risk
            else:
                business_risk = _extract_verified_business_risk(hc, pillar_name, doc_lang)

            if not finding_text and not business_risk:
                continue

            # Apply dynamic custody resolution (RFC 057)
            resolved_list = custody_resolver.resolve_portfolio([hc], current_tower_id=current_tower_id)
            eff_hc = resolved_list[0] if resolved_list else hc

            from assessment_engine.domain.actuarial.finding_archetype_resolver import (
                EpistemicEvidenceState,
                FindingLossPhysics,
                PolymorphicFindingClassifier,
            )

            physics_profile = PolymorphicFindingClassifier.classify_finding(
                hc=eff_hc,
                tower_id=current_tower_id,
            )

            # Prioritize risk title, capability name, or finding over target_state (RFC 085 Semantic Inversion Fix)
            import re
            raw_cap = str(
                eff_hc.get("title")
                or eff_hc.get("capability")
                or eff_hc.get("name")
                or eff_hc.get("finding")
                or "Operational Risk Scenario"
            )
            raw_cap = re.sub(r"^\[[A-Za-z0-9_-]+\]\s*", "", raw_cap).strip()
            raw_cap = re.sub(r"\s*\([KT]?\d+\)\s*$", "", raw_cap).strip()
            capability = resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)

            # If finding is survey boilerplate, infer concrete technical failure from universal question rubrics
            has_substantive_finding = bool(
                finding_text
                and not _is_placeholder_boilerplate(finding_text)
                and len(finding_text.split()) >= 4
            )
            has_substantive_risk = bool(
                business_risk
                and not _is_placeholder_boilerplate(business_risk)
                and not _is_severity_enum_token(business_risk, doc_lang)
                and len(business_risk.split()) >= 4
            )
            if (
                physics_profile.epistemic_state == EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE
                and (not has_substantive_finding or not has_substantive_risk)
            ):
                from assessment_engine.application.services.question_risk_inferrer import (
                    QuestionRiskInferrer,
                )

                inferrer = QuestionRiskInferrer()
                inferred_risk = inferrer.infer_risk_for_kpi(
                    tower_code=current_tower_id,
                    pillar_id=p_id,
                    pillar_name=pillar_name,
                    kpi_id=eff_hc.get("node_id", p_id),
                    kpi_name=capability,
                    score=float(eff_hc.get("score") or eff_hc.get("cmmi_score") or 1.5),
                    doc_lang=doc_lang,
                )
                finding_text = inferred_risk["finding"]
                business_risk = inferred_risk["business_risk"]
                eff_hc["finding"] = finding_text
                eff_hc["business_risk"] = business_risk
                eff_hc["primary_impact"] = business_risk
                eff_hc["operational_impact"] = business_risk
                eff_hc["threat_event_frequency"] = inferred_risk["threat_event_frequency"]
                eff_hc["recovery_time_hours"] = inferred_risk["recovery_time_hours"]
                eff_hc["direct_replacement_cost"] = inferred_risk["direct_replacement_cost"]
                eff_hc["fair_ale_score"] = inferred_risk["fair_ale_score"]
                eff_hc["fair_p90_score"] = inferred_risk["fair_p90_score"]
                eff_hc["quantification_status"] = "QUANTIFIED"
                # Reclassify with concrete failure mechanism to enter standard FAIR quantification
                physics_profile = PolymorphicFindingClassifier.classify_finding(
                    hc=eff_hc,
                    tower_id=current_tower_id,
                )

            vec = eff_hc.get("actuarial_input_vector") or {}
            vec_out = vec.get("outputs") or {}
            vec_in = vec.get("inputs") or {}

            tef_val = (
                (vec_in.get("tef_pert_mode") or {}).get("effective_value")
                or eff_hc.get("threat_event_frequency")
                or eff_hc.get("tef")
            )
            lm_val = eff_hc.get("loss_magnitude") or eff_hc.get("lm")

            decomp = eff_hc.get("additive_loss_decomposition") or {}
            ownership = str(
                eff_hc.get("ownership_type") or "PRIMARY_CUSTODIAN"
            ).strip().upper()
            is_tangential = (ownership == "TANGENTIAL_CONTRIBUTOR")

            raw_burn_rate = float(
                (vec_in.get("hourly_burn_rate") or {}).get("effective_value")
                or root_hourly_rate
            )

            # 1. Primary Downtime Loss (or labor toil hours for engineering friction)
            if physics_profile.allows_downtime_burn:
                rto_h = float(
                    (vec_in.get("rto_hours_mode") or {}).get("effective_value")
                    or eff_hc.get("recovery_time_hours")
                    or physics_profile.default_rto_hours
                    or 0.0
                )
                raw_alpha = float(
                    (vec_in.get("blast_radius_alpha") or {}).get("effective_value")
                    or physics_profile.blast_radius_factor
                    or 1.0
                )
                alpha = min(1.0, max(0.05, raw_alpha)) if raw_alpha > 0.0 else 1.0
                burn_rate = (
                    max(1.0, round(raw_burn_rate * alpha, 2))
                    if raw_burn_rate > 0
                    else 0.0
                )
            elif (
                physics_profile.loss_physics
                == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION
            ):
                rto_h = float(
                    (vec_in.get("rto_hours_mode") or {}).get("effective_value")
                    or eff_hc.get("recovery_time_hours")
                    or (float(lm_val) * 0.85 if lm_val else 2.0)
                    or 2.0
                )
                burn_rate = 65.0
            else:
                rto_h = 0.0
                burn_rate = 0.0

            effective_unit_rate = round(burn_rate)
            primary_downtime_loss = int(round(rto_h * effective_unit_rate))
            repl_cost_loss = int(
                round(
                    float(
                        (vec_in.get("direct_replacement_cost") or {}).get(
                            "effective_value"
                        )
                        or eff_hc.get("direct_replacement_cost")
                        or 0.0
                    )
                    * rate_mult
                )
            )
            raw_sec = float(
                (vec_in.get("secondary_loss_mean") or {}).get("effective_value")
                or eff_hc.get("secondary_loss_mean")
                or 0.0
            )
            if not physics_profile.allows_secondary_regulatory_fallout:
                sec_weighted_loss = 0
            else:
                sec_weighted_loss = (
                    int(round(0.10 * raw_sec * rate_mult))
                    if raw_sec > 0
                    else (int(round(primary_downtime_loss * 0.15)) if primary_downtime_loss > 0 else 0)
                )

            # SR 11-7 Actuarial 3-Layer Physics Resolution (Topology, Buffer Attenuation, Bow-Tie Escalation)
            enricher = _get_global_topology_enricher()
            topo_profile = None
            if enricher:
                try:
                    topo_profile, _ = enricher.enrich_asset(
                        {
                            "asset_id": eff_hc.get("id") or eff_hc.get("node_id") or f"HC-{r_counter:02d}",
                            "name": capability,
                            "finding": finding_text,
                            "business_risk": business_risk,
                            "capability": raw_cap,
                            "environment": eff_hc.get("environment") or eff_hc.get("environment_tier"),
                            "role": eff_hc.get("architectural_role") or eff_hc.get("role"),
                        }
                    )
                except Exception:
                    topo_profile = None

            if topo_profile:
                from assessment_engine.domain.actuarial.temporal_physics import TemporalPhysicsEngine
                from assessment_engine.domain.schemas.actuarial_contracts import (
                    ArchitecturalRole,
                    EnvironmentTier,
                )

                # Layer 2: Non-Production Zero Outage Invariant (LAB / DEV / TEST)
                if topo_profile.environment_tier in (EnvironmentTier.LAB_DEV_TEST, EnvironmentTier.STAGING_UAT):
                    primary_downtime_loss = 0
                    rto_h = 0.0
                    lab_reconst = TemporalPhysicsEngine.calculate_reconstitution_labor_cost(
                        tech_restoration_hours=float(eff_hc.get("recovery_time_hours") or 4.0),
                        hourly_engineering_rate=65.0,
                    )
                    repl_cost_loss = int(round(lab_reconst))
                    sec_weighted_loss = 0

                # Layer 1: Operational Friction & Telemetry Buffer Attenuation (T4 / T10 / Logs)
                elif topo_profile.architectural_role == ArchitecturalRole.TELEMETRY_LOGGING:
                    tech_h = min(0.5, rto_h if rto_h > 0 else 0.25)
                    eff_down = TemporalPhysicsEngine.calculate_effective_downtime_hours(
                        tech_restoration_hours=tech_h,
                        buffer_hours=1.0,
                        beta=2.0,
                    )
                    primary_downtime_loss = int(round(eff_down * effective_unit_rate))
                    rto_h = eff_down
                    log_reconst = TemporalPhysicsEngine.calculate_reconstitution_labor_cost(
                        tech_restoration_hours=tech_h,
                        hourly_engineering_rate=65.0,
                    )
                    repl_cost_loss = int(round(log_reconst))
                    sec_weighted_loss = 0

                # Layer 2: Bow-Tie Control Plane Escalation (T6 PAM / Shared Root)
                elif topo_profile.architectural_role == ArchitecturalRole.CONTROL_PLANE:
                    control_burn = raw_burn_rate if raw_burn_rate > 0 else float(effective_unit_rate or 0.0)
                    effective_unit_rate = round(control_burn)
                    primary_downtime_loss = int(round(rto_h * effective_unit_rate))
                    sec_weighted_loss = 0

                # Layer 3: Causal Regulatory Gating (Physical cuts carry 0 EUR privacy fines)
                elif "fibra" in finding_text.lower() or "corte de fibra" in (finding_text + " " + business_risk).lower():
                    sec_weighted_loss = 0
                    
                # Layer 4: Operational Resilience Attenuation Model (ORAM) for General DATA_PLANE 
                elif topo_profile.architectural_role == ArchitecturalRole.DATA_PLANE:
                    primary_downtime_loss = int(round(rto_h * effective_unit_rate))

            component_sum_sle = (
                primary_downtime_loss + repl_cost_loss + sec_weighted_loss
            )

            # Telemetry-driven extraction of declared contractual OpEx and fleet volumes (SR 11-7 / Zero-Magic)
            import re
            m_opex = re.search(r"(\d{2,3}(?:\.\d{3})*)\s*€\s+de\s+opex", finding_text + " " + business_risk, re.I)
            m_fleet = re.search(r"(\d{2,4})\s*(?:port[aá]tiles|equipos|laptops|m[aá]quinas)", finding_text + " " + business_risk, re.I)
            fleet_volume = int(m_fleet.group(1)) if m_fleet else int(eff_hc.get("fleet_volume") or 1)

            if m_opex and physics_profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE:
                declared_opex = float(m_opex.group(1).replace(".", ""))
                repl_cost_loss = int(round(declared_opex))
                calc_lef = 1.0
                calc_sle = float(repl_cost_loss)
            elif fleet_volume > 1 and physics_profile.loss_physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION:
                calc_lef = float(fleet_volume)
                # If rto_h was recorded as aggregate fleet hours, normalize per-unit SLE
                if rto_h >= fleet_volume:
                    calc_sle = float(component_sum_sle) / float(fleet_volume)
                else:
                    calc_sle = float(component_sum_sle)
            else:
                # 2. Resolve authoritative LEF
                raw_lef = (
                    decomp.get("mean_lef")
                    or vec_out.get("mean_lef")
                    or eff_hc.get("lef")
                )
                if topo_profile and topo_profile.architectural_role == ArchitecturalRole.CONTROL_PLANE:
                    # Catastrophic control-plane wipeout: 1 every 7 to 10 years (LEF ~ 0.10 - 0.15, IEEE 493 / Uptime)
                    calc_lef = 0.12
                    calc_sle = float(component_sum_sle)
                elif topo_profile and topo_profile.architectural_role == ArchitecturalRole.TELEMETRY_LOGGING:
                    # Operational fleet friction across 60 servers: 12 events/year (1 per month), 2h of technician response
                    calc_lef = 12.0
                    calc_sle = 130.0
                    component_sum_sle = 130
                    primary_downtime_loss = 0
                    repl_cost_loss = 130
                    sec_weighted_loss = 0
                    eff_downtime_hours = 0.0
                elif raw_lef is not None and float(raw_lef) > 0.0:
                    calc_lef = float(raw_lef)
                    calc_sle = float(component_sum_sle)
                else:
                    qual_tef = int(round(float(tef_val))) if tef_val is not None and float(tef_val) > 0.0 else 3
                    qual_vuln = int(round(float(eff_hc.get("vulnerability_level") or eff_hc.get("vulnerability") or 3)))
                    
                    base_lef = float(getattr(physics_profile, "default_lef_annual", 0.10))
                    tef_factor = (qual_tef / 3.0) if qual_tef > 0 else 1.0
                    vuln_factor = (qual_vuln / 3.0) if qual_vuln > 0 else 1.0
                    
                    calc_lef = round(min(3.0, max(0.02, base_lef * tef_factor * vuln_factor)), 3)
                    calc_sle = float(component_sum_sle)

            # 4. Standalone ALE is strictly round(LEF * SLE) for outages, or direct annual waste for FinOps
            if physics_profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE and calc_sle == 0:
                standalone_ale = int(round(float(eff_hc.get("ale") or decomp.get("expected_replacement_cost") or 18500)))
            else:
                standalone_ale = int(round(calc_lef * calc_sle))

            if standalone_ale == 0 and (eff_hc.get("fair_ale_score") or eff_hc.get("fair_ale") or eff_hc.get("ale")):
                standalone_ale = int(round(float(eff_hc.get("fair_ale_score") or eff_hc.get("fair_ale") or eff_hc.get("ale") or 0)))
                if calc_sle == 0 and calc_lef > 0:
                    calc_sle = round(standalone_ale / calc_lef, 2)

            finding_text_lower = (
                str(eff_hc.get("finding") or "")
                + " "
                + str(eff_hc.get("capability") or "")
                + " "
                + str(eff_hc.get("business_risk") or "")
            ).lower()
            is_contractual_opex = any(
                k in finding_text_lower
                for k in [
                    "modelo externalizado cautivo",
                    "operador nos",
                    "broadcom",
                    "licenciamiento vmware",
                    "contrato cautivo",
                    "gasto fijo de licencias",
                    "sobrecoste de suscripción",
                    "autoevaluación proyectaba",
                ]
            )

            is_deterministic = (
                is_contractual_opex
                or eff_hc.get("is_deterministic") is True
                or eff_hc.get("financial_nature") == "DETERMINISTIC_OPEX"
                or physics_profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE
                or (fleet_volume > 1 and physics_profile.loss_physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION)
            )
            ledger_type = (
                "LEDGER_B_DETERMINISTIC_OPEX"
                if is_deterministic
                else "LEDGER_A_STOCHASTIC"
            )

            # 5. Bound Euler diversification discount strictly by physical archetype cap (0% to 25% max)
            if is_deterministic:
                capped_disc = 0
                net_ale_int = standalone_ale
            else:
                max_disc_pct = max(
                    0.0,
                    min(0.25, float(physics_profile.max_euler_ale_discount_pct)),
                )
                raw_requested_net = (
                    decomp.get("net_allocated_ale")
                    or vec_out.get("portfolio_allocated_ale")
                    or eff_hc.get("fair_ale_score")
                    or eff_hc.get("fair_ale")
                )
                if standalone_ale > 0:
                    if raw_requested_net is not None:
                        candidate_net = int(
                            round(float(raw_requested_net) * rate_mult)
                        )
                        raw_disc = max(0, standalone_ale - candidate_net)
                        capped_disc = min(
                            raw_disc, int(round(standalone_ale * max_disc_pct))
                        )
                    else:
                        capped_disc = int(
                            round(standalone_ale * (max_disc_pct * 0.65))
                        )
                    net_ale_int = standalone_ale - capped_disc
                else:
                    capped_disc = 0
                    net_ale_int = (
                        int(round(float(raw_requested_net) * rate_mult))
                        if raw_requested_net is not None
                        else 0
                    )

            intrinsic_ale = float(net_ale_int)
            intrinsic_p90 = float(
                eff_hc.get("fair_p90_score")
                or eff_hc.get("fair_p90")
                or round(net_ale_int * 1.55)
            )

            calibrated_ale = 0.0 if is_tangential else intrinsic_ale
            calibrated_p90 = 0.0 if is_tangential else intrinsic_p90

            reconciled_decomp = {
                **(decomp if isinstance(decomp, dict) else {}),
                "rto_hours": rto_h,
                "hourly_burn_rate": burn_rate,
                "primary_downtime_loss": primary_downtime_loss,
                "expected_downtime_loss": primary_downtime_loss,
                "direct_replacement_loss": repl_cost_loss,
                "expected_replacement_cost": repl_cost_loss,
                "secondary_weighted_loss": sec_weighted_loss,
                "expected_secondary_loss": sec_weighted_loss,
                "stochastic_pert_adjustment": 0,
                "gross_mean_sle": int(round(calc_sle)),
                "mean_lef": round(calc_lef, 4),
                "standalone_ale": standalone_ale,
                "gross_standalone_ale": standalone_ale,
                "euler_diversification_credit": -capped_disc,
                "euler_discount_pct": (
                    round((capped_disc / standalone_ale) * 100.0, 1)
                    if standalone_ale > 0
                    else 0.0
                ),
                "net_allocated_ale": int(round(calibrated_ale)),
                "net_allocated_p90": int(round(calibrated_p90)),
                "is_deterministic": is_deterministic,
                "ledger_type": ledger_type,
                "fleet_volume": fleet_volume,
            }

            from assessment_engine.domain.actuarial.plain_language_narrative import (
                PlainLanguageRiskNarrative,
            )

            # Retrieve industry context from profile if available
            industry_key = "manufacturing"
            if topo_profile:
                # The taxonomy profile could provide the industry context, but typically we fallback to default if not injected
                pass
            
            # Prioritize authentic upstream business risk if present and substantive
            raw_cand_risk = str(eff_hc.get("business_risk") or eff_hc.get("primary_impact") or "").strip()
            is_substantive_risk = bool(
                raw_cand_risk
                and not _is_placeholder_boilerplate(raw_cand_risk)
                and not _is_severity_enum_token(raw_cand_risk, doc_lang)
                and len(raw_cand_risk.split()) >= 6
                and not raw_cand_risk.startswith("• Impacto en la Operación")
                and not raw_cand_risk.startswith("• Operational Impact")
            )
            authentic_risk = raw_cand_risk if is_substantive_risk else None

            final_business_risk = PlainLanguageRiskNarrative.format_plain_narrative(
                tower_code=current_tower_id,
                kpi_name=capability,
                failure_desc=finding_text,
                industry=industry_key,
                sle=float(calc_sle) if calc_sle is not None else 0.0,
                ale=calibrated_ale,
                rto_hours=rto_h,
                hourly_rate=burn_rate,
                doc_lang=doc_lang,
                loss_physics=physics_profile.loss_physics,
                architectural_role=topo_profile.architectural_role if topo_profile else None,
                authentic_business_risk=authentic_risk,
                lef=calc_lef,
                translator=t,
                currency_formatter=lambda val, loc_c: format_currency(val, currency_symbol=currency, locale=loc_c, decimals=0),
            )

            risk_item: dict[str, Any] = {
                "id": eff_hc.get("id", f"RVS{r_counter:02d}"),
                "node_id": eff_hc.get("node_id", f"NODE-{r_counter:03d}"),
                "pillar": pillar_name,
                "pillar_id": p_id,
                "capability": capability,
                "finding": finding_text,
                "business_risk": final_business_risk,
                "primary_impact": final_business_risk,
                "operational_impact": final_business_risk,
                "tef": tef_val,
                "lm": lm_val,
                "lef": round(float(calc_lef), 4) if calc_lef is not None else None,
                "sle": round(float(calc_sle), 2) if calc_sle is not None else None,
                "ale": calibrated_ale,
                "p90": calibrated_p90,
                "intrinsic_ale": intrinsic_ale,
                "intrinsic_p90": intrinsic_p90,
                "actuarial_input_vector": eff_hc.get("actuarial_input_vector"),
                "fair_ale_score": eff_hc.get("fair_ale_score"),
                "fair_p90_score": eff_hc.get("fair_p90_score"),
                "ownership_type": ownership,
                "primary_risk_ref": (str(eff_hc.get("primary_risk_ref") or "").strip() or None) if is_tangential else None,
                "contributing_towers": eff_hc.get("contributing_towers", []) if not is_tangential else [],
                "evidence": eff_hc.get("evidence", ""),
                "mitigation_directive": eff_hc.get("mitigation_directive", ""),
                "initiating_threat": eff_hc.get("initiating_threat", ""),
                "control_vulnerability": eff_hc.get("control_vulnerability", ""),
                "scope_note": eff_hc.get("scope_note", ""),
                "custody_resolution_metadata": eff_hc.get("custody_resolution_metadata", {}),
                "loss_physics": physics_profile.loss_physics.value,
                "epistemic_state": physics_profile.epistemic_state.value,
                "max_euler_ale_discount_pct": physics_profile.max_euler_ale_discount_pct,
                "max_euler_var_discount_pct": physics_profile.max_euler_var_discount_pct,
                "ale_str": format_currency(
                    calibrated_ale,
                    currency_symbol=currency,
                    locale=doc_lang,
                    decimals=0,
                ),
                "p90_str": format_currency(
                    calibrated_p90,
                    currency_symbol=currency,
                    locale=doc_lang,
                    decimals=0,
                ),
            }
            risk_item["additive_loss_decomposition"] = reconciled_decomp
            risk_item["sle"] = float(reconciled_decomp["gross_mean_sle"])
            risk_item["lef"] = float(reconciled_decomp["mean_lef"])
            risk_item["gross_standalone_ale"] = float(
                reconciled_decomp["standalone_ale"]
            )
            risk_item["euler_overlap_adjustment_ale"] = float(
                reconciled_decomp["euler_diversification_credit"]
            )
            risk_item["ale"] = float(reconciled_decomp["net_allocated_ale"])
            risk_item["p90"] = float(reconciled_decomp["net_allocated_p90"])
            risk_item["ale_str"] = format_currency(
                risk_item["ale"],
                currency_symbol=currency,
                locale=doc_lang,
                decimals=0,
            )
            risk_item["p90_str"] = format_currency(
                risk_item["p90"],
                currency_symbol=currency,
                locale=doc_lang,
                decimals=0,
            )

            risks_data_list.append(risk_item)
            risks_by_pillar.setdefault(pillar_name, []).append(risk_item)
            r_counter += 1

    if not risks_data_list:
        unassessed_item: dict[str, Any] = {
            "id": f"RVS{r_counter:02d}",
            "node_id": f"NODE-{r_counter:03d}",
            "pillar": "Unassessed Scope",
            "pillar_id": f"{current_tower_id}.P0",
            "capability": "No empirical risk scenarios identified",
            "finding": "This operational domain contains zero empirical findings in the assessment scope.",
            "business_risk": "Unassessed control environment (No empirical exposure calculated).",
            "tef": None,
            "lm": None,
            "lef": None,
            "sle": None,
            "ale": 0.0,
            "p90": 0.0,
            "intrinsic_ale": 0.0,
            "intrinsic_p90": 0.0,
            "ownership_type": "PRIMARY_CUSTODIAN",
            "epistemic_state": "UNASSESSED_OUT_OF_SCOPE",
            "primary_risk_ref": None,
            "contributing_towers": [],
            "evidence": "Out of scope / unassessed in current telemetry",
            "mitigation_directive": "Collect telemetry and audit controls for this operational domain.",
            "initiating_threat": "Unassessed Scope",
            "control_vulnerability": "Unassessed",
            "primary_impact": "None evaluated",
            "scope_note": "No empirical findings in assessment payload",
            "custody_resolution_metadata": {},
            "ale_str": "UNQUANTIFIED",
            "p90_str": "UNQUANTIFIED",
            "sle_str": "UNQUANTIFIED",
        }
        risks_data_list.append(unassessed_item)
        risks_by_pillar.setdefault("Unassessed Scope", []).append(unassessed_item)

    # Strict Contiguous Index Bijection Assertion (SR 11-7 / Zero-Gap Mandate)
    actual_rvs_ids = [
        str(r.get("id"))
        for r in risks_data_list
        if str(r.get("id", "")).startswith("RVS")
    ]
    expected_rvs_ids = [f"RVS{i:02d}" for i in range(1, len(actual_rvs_ids) + 1)]
    if actual_rvs_ids != expected_rvs_ids:
        raise ValueError(
            f"Index Bijection Violation in Tower {current_tower_id}: "
            f"Generated IDs {actual_rvs_ids} do not match contiguous sequence {expected_rvs_ids}."
        )

    return risks_data_list, risks_by_pillar


_CACHED_GATEKEEPER = None


def _find_repo_root() -> Path:
    """Robustly discovers workspace root by ascending directory hierarchy."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "engine_config").exists() and (parent / "pyproject.toml").exists():
            return parent
    return current.parents[4]


def _bootstrap_physics_lexicon() -> None:
    try:
        repo_root = _find_repo_root()
        lex_path = repo_root / "engine_config" / "taxonomy" / "finding_physics_lexicon.json"
        if lex_path.is_file():
            with open(lex_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            from assessment_engine.domain.actuarial.finding_archetype_resolver import (
                register_physics_lexicon,
            )
            register_physics_lexicon(data)
    except Exception as exc:
        logger.debug("Could not bootstrap physics lexicon: %s", exc)


_bootstrap_physics_lexicon()

_CACHED_TOPOLOGY_ENRICHER = None


def _get_global_topology_enricher():
    global _CACHED_TOPOLOGY_ENRICHER
    if _CACHED_TOPOLOGY_ENRICHER is not None:
        return _CACHED_TOPOLOGY_ENRICHER
    try:
        from assessment_engine.domain.actuarial.topology_enricher import TopologyEnricher

        _CACHED_TOPOLOGY_ENRICHER = TopologyEnricher()
    except Exception as exc:
        logger.debug("Could not initialize TopologyEnricher: %s", exc)
    return _CACHED_TOPOLOGY_ENRICHER


def _get_global_gatekeeper():
    global _CACHED_GATEKEEPER
    if _CACHED_GATEKEEPER is not None:
        return _CACHED_GATEKEEPER
    try:
        from assessment_engine.domain.validation.semantic_gatekeeper import (
            OntologicalGatekeeper,
        )
        from assessment_engine.infrastructure.ontology.taxonomy_loader import (
            DomainTaxonomyRegistry,
        )

        repo_root = _find_repo_root()
        ontology_file = repo_root / "engine_config/ontologies/global_tech_ontology.yaml"
        towers_dir = repo_root / "engine_config/towers"
        if ontology_file.exists() and towers_dir.exists():
            registry = DomainTaxonomyRegistry.from_config_directories(ontology_file, towers_dir)
            _CACHED_GATEKEEPER = OntologicalGatekeeper(registry)
            return _CACHED_GATEKEEPER
    except Exception as exc:
        logger.warning("Could not initialize global OntologicalGatekeeper: %s", exc)
    return None


def _resolve_pillar_kpi_fallback(tower_id: str, pillar_id: str, doc_lang: str) -> tuple[str, str]:
    """Provides deterministic KPI-anchored strength and gap narratives when LLM findings are quarantined."""
    try:
        repo_root = _find_repo_root()
        t_id_u = tower_id.upper()
        def_path = repo_root / f"engine_config/towers/{t_id_u}/tower_definition_{t_id_u}.json"
        if not def_path.exists():
            def_path = repo_root / "engine_config/towers" / f"tower_definition_{t_id_u}.json"
        if def_path.exists():
            with open(def_path, "r", encoding="utf-8-sig") as f:
                t_def = json.load(f)
            for p in t_def.get("pillars", []):
                p_code = str(p.get("pillar_id", "")).upper()
                if p_code == pillar_id.upper() or p_code.endswith(f".{pillar_id.upper()}"):
                    kpis = p.get("kpis", [])
                    if kpis:
                        raw_first = str(kpis[0].get("kpi_name", "")).strip()
                        raw_last = str(kpis[-1].get("kpi_name", "")).strip()
                        from assessment_engine.domain.taxonomy_resolver import (
                            get_taxonomy_resolver,
                        )
                        res = get_taxonomy_resolver()
                        first_kpi = res.resolve_capability_name(raw_first, default=raw_first, locale=doc_lang)
                        last_kpi = res.resolve_capability_name(raw_last, default=raw_last, locale=doc_lang)
                        fallback_pos = t("calib_fallback_pos_template", locale=doc_lang, kpi_name=first_kpi)
                        fallback_neg = t("calib_fallback_neg_template", locale=doc_lang, kpi_name=last_kpi)
                        return fallback_pos, fallback_neg
    except Exception:
        # Intentional fallback / handled exception
        _ = True

    return (
        t("calib_fallback_pos_default", locale=doc_lang),
        t("calib_fallback_neg_default", locale=doc_lang),
    )


_CANONICAL_ADVERSATIVE_PREFIXES: Final[tuple[str, ...]] = (
    "however",
    "nevertheless",
    "nonetheless",
    "conversely",
    "although",
    "despite",
    "even so",
    "in spite of",
)

_SENTENCE_SPLIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?])\s+")

_DEFICIT_LEXEMES_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:carece|ausencia|deficit|inexistencia|vulnerabilidad|riesgo|comprometida|roto|rota|falla|"
    r"lacks|absence|deficiency|vulnerable|compromised|broken|fails|outage)\b",
    re.IGNORECASE,
)

_AFFIRMATIVE_LEXEMES_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:cuenta\s+con|dispone\s+de|implementa|garantiza|redundancia|alta\s+disponibilidad|cumple|estandarizado|certificado|mantenido|"
    r"maintains|enforces|provides|redundant|certified|standardized|implemented)\b",
    re.IGNORECASE,
)


def _resolve_adversative_prefixes(doc_lang: str) -> tuple[str, ...]:
    """Retrieve canonical and localized adversative prefixes sorted longest-first."""
    localized = [
        str(item).strip().lower()
        for item in get_localized_list("adversative_connective_prefixes", locale=doc_lang, default=[])
        if str(item).strip()
    ]
    combined = set(_CANONICAL_ADVERSATIVE_PREFIXES).union(localized)
    return tuple(sorted(combined, key=len, reverse=True))


def _starts_with_adversative(sentence: str, prefixes: tuple[str, ...]) -> bool:
    """Return True if sentence begins with an adversative connective."""
    normalized = sentence.strip().lstrip(".,;:!?-_()[]{}\"' ").lower()
    for prefix in prefixes:
        if normalized.startswith(prefix):
            remainder = normalized[len(prefix):]
            if not remainder or remainder[0] in " ,;:.!?-":
                return True
    return False


def _sanitize_strength_clause(
    candidate_text: str,
    fallback_text: str,
    score: float,
    doc_lang: str,
) -> str:
    """Retain only affirmative architectural sentences in operational strength slot."""
    cleaned = str(candidate_text or "").strip()
    if not cleaned:
        return fallback_text

    prefixes = _resolve_adversative_prefixes(doc_lang)
    sentences = [s.strip() for s in _SENTENCE_SPLIT_PATTERN.split(cleaned) if s.strip()]
    affirmative_sentences: list[str] = []

    for s in sentences:
        if _starts_with_adversative(s, prefixes):
            continue
        if score >= 3.0 and _DEFICIT_LEXEMES_PATTERN.search(s) and not _AFFIRMATIVE_LEXEMES_PATTERN.search(s):
            continue
        clean_s = re.split(r";\s*(?:no\s+obstante|sin\s+embargo|however|nevertheless)", s, flags=re.IGNORECASE)[0].strip()
        if len(clean_s.split()) >= 4:
            affirmative_sentences.append(clean_s if clean_s.endswith((".", "!", "?")) else f"{clean_s}.")

    if affirmative_sentences:
        return affirmative_sentences[0]

    return fallback_text


def _sanitize_breach_clause(
    candidate_gap: str,
    fallback_gap: str,
    doc_lang: str,
) -> str:
    """Strip leading adversative connectors from resilience breach clause and enforce sentence casing."""
    cleaned = str(candidate_gap or "").strip()
    if not cleaned or len(cleaned.split()) < 3:
        return fallback_gap

    prefixes = _resolve_adversative_prefixes(doc_lang)
    lowered = cleaned.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            remainder = cleaned[len(prefix):]
            if not remainder or remainder[0] in " ,;:.!?-":
                cleaned = remainder.lstrip(" ,;:-")
                break

    if not cleaned:
        return fallback_gap

    capitalized = cleaned[0].upper() + cleaned[1:]
    if not capitalized.endswith((".", "!", "?")):
        capitalized += "."
    return capitalized


def _build_prescriptive_callout(
    exact_score: float,
    current_tower_id: str,
    canonical_pillar_id: str,
    doc_lang: str,
) -> tuple[str, int, str]:
    """Generates the prescriptive trajectory callout string and milestones for a given score, tower, and granular pillar."""
    typology_map = {
        "T1": "FACILITIES",
        "T2": "COMPUTE",
        "T3": "NETWORK",
        "T4": "STORAGE",
        "T5": "RESILIENCE",
        "T6": "SECURITY",
        "T7": "ITSM",
        "T8": "GOVERNANCE",
        "T9": "WORKPLACE",
        "T10": "LEGACY",
    }
    typ = typology_map.get(current_tower_id.upper(), "GOVERNANCE")

    if exact_score < 2.0:
        target_lvl = 2
        trans_key = "L1_to_L2"
    elif exact_score < 3.0:
        target_lvl = 3
        trans_key = "L2_to_L3"
    elif exact_score < 4.0:
        target_lvl = 4
        trans_key = "L3_to_L4"
    else:
        target_lvl = 5
        trans_key = "L3_to_L4"

    target_band = resolve_maturity_band(float(target_lvl), ANNEX_MATURITY_BANDS, locale=doc_lang)
    target_label = target_band.get("label", str(target_lvl))

    matrix = _load_cmmi_progression_matrix()
    milestones: list[str] = []
    if matrix:
        # 1. Granular 50-Pillar Lookup
        p_data = matrix.get("pillars", {}).get(canonical_pillar_id, {}).get(trans_key, {})
        if isinstance(p_data, dict):
            milestones = p_data.get(doc_lang) or p_data.get("en") or []
        elif isinstance(p_data, list):
            milestones = p_data

        # 2. Tower Typology Fallback
        if not milestones:
            t_data = matrix.get("tower_fallbacks", {}).get(typ, {}).get(trans_key, {})
            if isinstance(t_data, dict):
                milestones = t_data.get(doc_lang) or t_data.get("en") or []
            elif isinstance(t_data, list):
                milestones = t_data

        # 3. Universal Fallback
        if not milestones:
            u_data = matrix.get("universal_default", {}).get(trans_key, {})
            if isinstance(u_data, dict):
                milestones = u_data.get(doc_lang) or u_data.get("en") or []
            elif isinstance(u_data, list):
                milestones = u_data

    header_callout = t("callout_trajectory_title", locale=doc_lang, target_level=target_lvl, target_label=target_label)
    callout_lines = [f"**{header_callout}**"]
    for idx, m in enumerate(milestones, 1):
        callout_lines.append(f"{idx}. {m}")

    return "\n".join(callout_lines), target_lvl, target_label


def _build_operational_reality(pillar: dict[str, Any], doc_lang: str) -> str:
    """Extract clean, fluid operational prose from asis_architecture_description, stripping anaphoric clauses."""
    desc = str(pillar.get("asis_architecture_description") or "").strip()
    if not desc:
        return ""
    sentences = [s.strip() for s in _SENTENCE_SPLIT_PATTERN.split(desc) if s.strip()]
    prefixes = _resolve_adversative_prefixes(doc_lang)
    anaphoric_prefixes = [
        str(item).strip().lower()
        for item in get_localized_list("anaphoric_prefixes", locale=doc_lang, default=[])
        if str(item).strip()
    ]
    escaped_prefixes = [re.escape(p.rstrip(" ,;:.")) for p in prefixes if p.strip()]
    adversative_pattern = (
        re.compile(rf";\s*(?:{'|'.join(escaped_prefixes)})\b", flags=re.IGNORECASE)
        if escaped_prefixes
        else None
    )

    valid_sentences: list[str] = []
    for s in sentences:
        lowered = s.lower()
        is_anaphoric = any(
            lowered.startswith(ap) or lowered.startswith(ap.rstrip())
            for ap in anaphoric_prefixes
        )
        if is_anaphoric or _starts_with_adversative(s, prefixes):
            continue
        clean_s = adversative_pattern.split(s)[0].strip() if adversative_pattern else s.strip()
        if len(clean_s.split()) >= 4:
            valid_sentences.append(clean_s if clean_s.endswith((".", "!", "?")) else f"{clean_s}.")

    if valid_sentences:
        return " ".join(valid_sentences[:2])
    return desc


_CJK_CHAR_RE: Final[re.Pattern[str]] = re.compile(
    r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\uac00-\ud7af]"
)
_SENTENCE_BOUNDARY_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ0-9])|(?<=[。！？])\s*"
)
CJK_CHARS_PER_LEXICAL_UNIT: Final[float] = 2.20


def _get_transition_markers_regex(locale: str) -> re.Pattern[str] | None:
    """Compiles a locale-specific regular expression for discourse transition markers

    loaded dynamically from `engine_config/locales.json`.
    """
    markers = get_localized_list("compiler_transition_markers", locale=locale, default=[])
    if not markers:
        return None
    escaped_markers = [re.escape(str(m).strip()) for m in markers if str(m).strip()]
    if not escaped_markers:
        return None
    pattern = rf"(?:^|\s+)(?:{'|'.join(escaped_markers)})\b"
    return re.compile(pattern, flags=re.IGNORECASE | re.UNICODE)


def _estimate_lexical_units(text: str) -> int:
    """Computes script-agnostic lexical density across Latin, Cyrillic, and CJK scripts."""
    if not text or not text.strip():
        return 0
    cjk_matches = _CJK_CHAR_RE.findall(text)
    cjk_count = len(cjk_matches)
    non_cjk_text = _CJK_CHAR_RE.sub(" ", text)
    space_delimited_words = len(non_cjk_text.split())
    cjk_units = int(round(cjk_count / CJK_CHARS_PER_LEXICAL_UNIT))
    return space_delimited_words + cjk_units


def _chunk_monolithic_paragraph(text: str, doc_lang: str) -> list[str]:
    """Dynamically segments a dense monolithic text into 1, 2, or 3 natural rhythmic paragraphs

    based on lexical unit density and semantic transition pivots across all supported scripts.
    """
    raw = text.strip()
    if not raw:
        return []

    existing_paras = [p.strip() for p in raw.split("\n") if p.strip()]
    if len(existing_paras) > 1 and all(_estimate_lexical_units(p) < 160 for p in existing_paras):
        return existing_paras

    sentences = [s.strip() for s in _SENTENCE_BOUNDARY_RE.split(raw) if s.strip()]
    total_units = sum(_estimate_lexical_units(s) for s in sentences)

    # 1. Short text (< 120 lexical units or <= 2 sentences): 1 concise paragraph
    if total_units < 120 or len(sentences) <= 2:
        return [raw]

    transition_re = _get_transition_markers_regex(doc_lang)

    # 2. Medium text (120 - 240 lexical units or <= 5 sentences): 2 balanced paragraphs
    if total_units <= 240 or len(sentences) <= 5:
        target_split = total_units / 2.0
        best_split_idx = len(sentences) // 2
        best_dist = float("inf")
        cur_u = 0

        for i in range(len(sentences) - 1):
            cur_u += _estimate_lexical_units(sentences[i])
            dist = abs(cur_u - target_split)
            if transition_re and transition_re.search(sentences[i + 1]):
                dist -= 25.0
            if dist < best_dist:
                best_dist = dist
                best_split_idx = i

        joiner = "" if _CJK_CHAR_RE.search(raw) else " "
        p1 = joiner.join(sentences[: best_split_idx + 1])
        p2 = joiner.join(sentences[best_split_idx + 1 :])
        return [p1, p2]

    # 3. Extensive text (> 240 lexical units): 2 or 3 rhythmic paragraphs
    if total_units > 270 and len(sentences) >= 6:
        target_split = total_units / 3.0
        splits: list[int] = []
        cur_u = 0
        for i in range(len(sentences) - 1):
            cur_u += _estimate_lexical_units(sentences[i])
            if len(splits) == 0 and cur_u >= target_split * 0.8:
                splits.append(i)
            elif len(splits) == 1 and cur_u >= target_split * 1.8:
                splits.append(i)
                break
        if len(splits) == 2:
            joiner = "" if _CJK_CHAR_RE.search(raw) else " "
            p1 = joiner.join(sentences[: splits[0] + 1])
            p2 = joiner.join(sentences[splits[0] + 1 : splits[1] + 1])
            p3 = joiner.join(sentences[splits[1] + 1 :])
            return [p1, p2, p3]

    half = len(sentences) // 2
    joiner = "" if _CJK_CHAR_RE.search(raw) else " "
    return [joiner.join(sentences[:half]), joiner.join(sentences[half:])]


_PLACEHOLDER_BOILERPLATE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:Arquitectura y procesos operativos estructurados conforme a los est[áa]ndares de|"
    r"Architecture and operational processes structured in accordance with|"
    r"Arquitetura e processos operacionais estruturados de acordo com)\b",
    re.IGNORECASE,
)

_ORPHAN_PREPOSITION_GLITCH_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(condicionad[oa]s?\s+por|afectad[oa]s?\s+por|limitad[oa]s?\s+por|caracterizad[oa]s?\s+por|impacted\s+by|constrained\s+by)\s+(en\s+|in\s+|at\s+)",
    re.IGNORECASE,
)

_UNTRANSLATED_KPI_TOKEN_LEAK_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:\)\s*&\s*[A-Za-z0-9\-\s]+(?:Mitigation|Management|Governance|Compliance|Optimization|Automation|Resilience|Architecture|Operations|Control|Monitoring)\b|"
    r"\b(?:en|de|para|sobre|con)\s+[A-Z][A-Za-z0-9\-\/]+(?:\s+[A-Z&][A-Za-z0-9\-\/]+){2,})",
)

_TOTAL_ABSENCE_OF_TELEMETRY_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:carece\s+por\s+completo\s+de\s+herramientas|sin\s+herramientas\s+de\s+(?:telemetr[íi]a|monitorizaci[óo]n|medici[óo]n|control|gesti[óo]n)|"
    r"ausencia\s+total\s+de\s+(?:herramientas|telemetr[íi]a|visibilidad|control)|no\s+(?:existen|cuenta\s+con|dispone\s+de)\s+herramientas|"
    r"zero\s+(?:telemetry|monitoring|visibility)\s+tools|completely\s+lacks\s+(?:tools|telemetry|visibility)|"
    r"inexistencia\s+de\s+herramientas\s+de\s+(?:medici[óo]n|telemetr[íi]a|experiencia))\b",
    re.IGNORECASE,
)

_SYNC_REPLICATION_CLAIM_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(replicaci[óo]n\s+s[íi]ncrona\s+ordinaria|ordinary\s+synchronous\s+replication|replicaci[óo]n\s+s[íi]ncrona\s+activa)\b",
    re.IGNORECASE,
)

_ASYNC_WITHOUT_METROCLUSTER_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(sin\s+replicaci[óo]n\s+s[íi]ncrona|r[ée]plica\s+as[íi]ncrona|asynchronous\s+replication|without\s+synchronous\s+replication)\b",
    re.IGNORECASE,
)


def _scrub_template_glitches_and_token_leaks(text: str, doc_lang: str) -> str:
    """Repair copy-paste template glitches, orphan prepositions, and raw framework KPI token leaks."""
    if not text:
        return ""
    cleaned = str(text).strip()
    # Fix broken copy-paste prepositions like "condicionada por en la mayoría" -> "condicionada en la mayoría"
    cleaned = _ORPHAN_PREPOSITION_GLITCH_RE.sub(r"\1 ", cleaned)
    # Strip trailing English KPI placeholder suffixes like ") & Noisy-Neighbor Mitigation"
    cleaned = re.sub(
        r"\)\s*&\s*[A-Za-z0-9\-\s]+(?:Mitigation|Management|Governance|Compliance|Optimization|Automation|Resilience|Architecture|Operations|Control|Monitoring)\b",
        "",
        cleaned,
    )
    # Collapse double spaces or stray punctuation created during scrubbing
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def _reconcile_contradictory_replication_claims(
    paragraphs: list[str], full_context_text: str, doc_lang: str
) -> list[str]:
    """Ensure architectural consistency when asynchronous replication is established in primary evidence."""
    if not paragraphs:
        return paragraphs
    if _ASYNC_WITHOUT_METROCLUSTER_RE.search(full_context_text):
        norm_lang = (doc_lang or "en").strip().lower()
        replacement = (
            "replicación asíncrona programada (sin conmutación síncrona activa)"
            if norm_lang.startswith("es")
            else "scheduled asynchronous replication (without active synchronous failover)"
        )
        return [_SYNC_REPLICATION_CLAIM_RE.sub(replacement, p) for p in paragraphs]
    return paragraphs


def _calibrate_empirical_maturity_score(
    raw_score: float, pillar: dict[str, Any], clean_narrative: str, clean_breach: str
) -> float:
    """Pass-through preserving authoritative upstream SSOT score without presentation mutations."""
    return raw_score


def _is_placeholder_boilerplate(text: str) -> bool:
    """Detect synthetic single-sentence template placeholders that lack empirical telemetry."""
    cleaned = str(text or "").strip()
    if not cleaned:
        return True
    if _PLACEHOLDER_BOILERPLATE_RE.search(cleaned) and _estimate_lexical_units(cleaned) < 28:
        return True
    return False


def _synthesize_empirical_narrative_from_findings(
    pillar: dict[str, Any],
    canonical_pillar_id: str,
    fallback_pos: str,
    fallback_neg: str,
    doc_lang: str,
) -> str:
    """Synthesize a substantive, evidence-grounded architectural narrative when raw description is a placeholder or truncated."""
    findings = pillar.get("health_check_asis") or []
    finding_clauses: list[str] = []
    impact_clauses: list[str] = []

    if isinstance(findings, list):
        for hc in findings[:3]:
            if not isinstance(hc, dict):
                continue
            f_txt = _scrub_template_glitches_and_token_leaks(
                str(hc.get("finding") or hc.get("description") or hc.get("risk_observed") or "").strip().rstrip("."),
                doc_lang,
            ).strip().rstrip(".")
            if f_txt and not _is_placeholder_boilerplate(f_txt) and len(f_txt.split()) >= 5:
                finding_clauses.append(f_txt)
            imp_txt = _scrub_template_glitches_and_token_leaks(
                str(hc.get("business_risk") or hc.get("operational_impact") or hc.get("primary_impact") or "").strip().rstrip("."),
                doc_lang,
            ).strip().rstrip(".")
            if imp_txt and not _is_severity_enum_token(imp_txt, doc_lang) and len(imp_txt.split()) >= 5:
                impact_clauses.append(imp_txt)

    lit_ev = _scrub_template_glitches_and_token_leaks(
        str(pillar.get("literal_evidence") or "").strip().rstrip("."), doc_lang
    ).strip().rstrip(".")
    sota_benchmark = _build_sota_benchmark_paragraph(canonical_pillar_id, doc_lang)
    nexus_narrative = _build_cross_domain_nexus(canonical_pillar_id, doc_lang)

    parts: list[str] = []
    if fallback_pos and len(fallback_pos.split()) >= 5:
        parts.append(fallback_pos.rstrip(".") + ".")

    if finding_clauses:
        parts.append(". ".join(finding_clauses) + ".")
    elif fallback_neg:
        parts.append(fallback_neg.rstrip(".") + ".")

    if lit_ev and len(lit_ev.split()) >= 6 and lit_ev not in " ".join(parts):
        parts.append(lit_ev + ".")

    if impact_clauses:
        parts.append(". ".join(impact_clauses[:2]) + ".")

    if sota_benchmark:
        parts.append(sota_benchmark.rstrip(".") + ".")
    if nexus_narrative and nexus_narrative.rstrip(".") + "." not in parts:
        parts.append(nexus_narrative.rstrip(".") + ".")

    return " ".join(p for p in parts if p).strip()


_KPI_EXPORT_ARTIFACT_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:procesos\s+operativos\s+estructurados\s+seg[úu]n\s+|structured\s+operational\s+processes\s+according\s+to\s+|processos\s+operacionais\s+estruturados\s+segundo\s+)([^.]+)\.\s*",
    re.IGNORECASE,
)

_ABSENCE_OF_TELEMETRY_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:lack\s+of|absence\s+of|no\s+telemetry|zero\s+telemetry|carencia\s+de|falta\s+de|ausencia\s+de|sin\s+herramientas\s+de|inexistencia\s+de)\b.*\b(?:dex|telemetr[íi]a|telemetry|monitoring|monitorizaci[óo]n|observability|observabilidad|tooling|herramientas|dcim|bms)\b",
    re.IGNORECASE,
)


def _reconcile_telemetry_tool_contradictions(
    score: float,
    clean_state: str,
    clean_gap: str,
    fallback_neg: str,
    doc_lang: str,
) -> tuple[float, str]:
    """Scrubs synthetic KPI export headers while preserving authoritative upstream score."""
    scrubbed_state = _KPI_EXPORT_ARTIFACT_RE.sub("", clean_state).strip()
    return score, scrubbed_state or clean_state


def _sanitize_architectural_narrative(
    pillar: dict[str, Any],
    doc_lang: str,
    *,
    canonical_pillar_id: str = "",
    fallback_pos: str = "",
    fallback_neg: str = "",
) -> list[str]:
    """Extracts the authentic architectural narrative, dynamically formatting paragraphs to eliminate cognitive fatigue."""
    desc = str(pillar.get("asis_architecture_description") or "").strip()
    desc = _KPI_EXPORT_ARTIFACT_RE.sub("", desc).strip()
    if _is_placeholder_boilerplate(desc) or _estimate_lexical_units(desc) < 22:
        synthesized = _synthesize_empirical_narrative_from_findings(
            pillar, canonical_pillar_id, fallback_pos, fallback_neg, doc_lang
        )
        if synthesized:
            desc = synthesized if _is_placeholder_boilerplate(desc) else f"{desc.rstrip('.')}." + " " + synthesized

    if not desc:
        return []

    raw_paras = [p.strip() for p in desc.split("\n\n") if p.strip()]

    cleaned_paras: list[str] = []
    for para in raw_paras:
        p_clean = _scrub_template_glitches_and_token_leaks(para, doc_lang)
        p_clean = _KPI_EXPORT_ARTIFACT_RE.sub("", p_clean).strip()
        if _estimate_lexical_units(p_clean) >= 4:
            cleaned_paras.append(p_clean)

    full_ctx = f"{desc} {fallback_pos} {fallback_neg} {pillar.get('literal_evidence', '')}"
    cleaned_paras = _reconcile_contradictory_replication_claims(cleaned_paras, full_ctx, doc_lang)

    return cleaned_paras if cleaned_paras else [_scrub_template_glitches_and_token_leaks(desc, doc_lang)]


_BROKEN_KPI_BOILERPLATE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:Procesos\s+operativos\s+estructurados\s+conforme\s+a\s+[^.?!]*(?:\.\s*of\s+[A-Z][^.?!]*)?|"
    r"Structured\s+operational\s+processes\s+conforming\s+to\s+[^.?!]*|"
    r"ante\s+incidencias\s+no\s+contenidas\s+en\s+[A-Za-z0-9\s/&(),\-]+(?:\.\s*\([^)]+\))?|"
    r"analizando\s+cr[ií]ticamente\s+factores\s+clave\s+como\s+[a-z][A-Za-z0-9\s/&(),\-]+)",
    re.IGNORECASE,
)

_CAMELCASE_PROMPT_LEAK_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:target\s+Architecture\s*\(To-Be\)\s*Roadmap\s+Governance|"
    r"iT\s*&\s*Business\s+Strategic\s+Alignment|"
    r"of\s+Failure\s+Elimination|"
    r"Oversubscription\s*&\s*Latency)\b",
    re.IGNORECASE,
)

_EUC_FOREIGN_DOMAIN_SENTENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:RODCs?|Read-Only\s+Domain\s+Controllers?|tendido\s+de\s+fibra|pulling\s+fiber|"
    r"c[aá]maras?\s+CCTV|CCTV\s+cameras?|Kubernetes|K8s|DBA|bases?\s+de\s+datos|"
    r"database\s+administration|plantillas?\s+de\s+VM|VM\s+templates?|SimpliVity|vSphere|ESXi|"
    r"conduit\s+DCI|fibra\s+oscura|dark\s+fiber|BGP|OSPF|DMVPN|core\s+switch)\b",
    re.IGNORECASE,
)


def _scrub_broken_kpi_boilerplate_clauses(text: str, fallback: str, doc_lang: str) -> str:
    """Removes corrupted English-to-Spanish mail-merge KPI fragments and camelCase framework prompt leaks."""
    if not text:
        return fallback
    cleaned = _BROKEN_KPI_BOILERPLATE_RE.sub("", text)
    cleaned = _CAMELCASE_PROMPT_LEAK_RE.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .,;:-")
    if len(cleaned.split()) < 5:
        return fallback
    return cleaned[0].upper() + cleaned[1:] if cleaned else fallback


def _scrub_foreign_domain_bleed_for_tower(text: str, tower_id: str, fallback: str) -> str:
    """Filters out sentences containing out-of-scope infrastructure/OT/DB bleed in specialized towers."""
    if not text:
        return fallback
    norm_tower = str(tower_id or "").strip().upper()
    if norm_tower in {"T9", "EUC"} or "EUC" in norm_tower or "WORKPLACE" in norm_tower:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        kept = [s for s in sentences if not _EUC_FOREIGN_DOMAIN_SENTENCE_RE.search(s)]
        rejoined = " ".join(kept).strip()
        if len(rejoined.split()) >= 5:
            return rejoined
        return fallback
    return text


def _extract_safe_score(val: Any, default: float = DEFAULT_PILLAR_ASSESSMENT_SCORE) -> float:
    """Defensively parses any numeric string, int, float or None, clamping to valid [1.0, 5.0] CMMI range."""
    if val is None:
        return default
    try:
        f_val = float(val)
        return max(1.0, min(5.0, f_val))
    except (ValueError, TypeError):
        return default


def derive_in_memory_maturity_matrix(
    b_data: dict[str, Any],
    doc_lang: str,
    gatekeeper: Any | None = None,
    taxonomy_registry: Any | None = None,
    localizer: Any | None = None,
) -> list[dict[str, Any]]:
    """Extract and format maturity assessment matrix rows directly from in-memory payload

    with strict ontological gatekeeping and KPI-anchored causal alignment.
    """
    from assessment_engine.domain.ontology.models import ValidationVerdict
    from assessment_engine.domain.validation.semantic_gatekeeper import (
        OntologicalGatekeeper,
    )

    resolver = get_taxonomy_resolver()
    active_gatekeeper = gatekeeper or (
        OntologicalGatekeeper(taxonomy_registry) if taxonomy_registry else _get_global_gatekeeper()
    )
    current_tower_id = str(
        b_data.get("tower_id")
        or b_data.get("document_meta", {}).get("tower_id")
        or b_data.get("document_meta", {}).get("tower_code")
        or ""
    ).upper()

    # First pass: find max delta and min score for the Tri-Modal enrouter defensively
    pillars_list = b_data.get("pillars_analysis", [])
    valid_scores: list[float] = []
    valid_deltas: list[float] = []
    for p in pillars_list:
        if not isinstance(p, dict):
            continue
        e_s = _extract_safe_score(p.get("score"))
        raw_d = p.get("declared_score")
        d_s = _extract_safe_score(raw_d) if raw_d is not None else e_s
        valid_scores.append(e_s)
        valid_deltas.append(abs(e_s - d_s))

    min_score = min(valid_scores) if valid_scores else DEFAULT_PILLAR_ASSESSMENT_SCORE
    max_delta = max(valid_deltas) if valid_deltas else 0.0

    rows: list[dict[str, Any]] = []

    for pillar in pillars_list:
        if not isinstance(pillar, dict):
            continue
        p_id, raw_pname = extract_pillar_identifiers(pillar)
        fallback_pname = t("table_header_pillar", locale=doc_lang)
        pillar_name = resolver.resolve_pillar_by_any_reference(
            p_id or raw_pname,
            default=(raw_pname or p_id or fallback_pname),
            locale=doc_lang,
            tower_id=current_tower_id,
        )

        exact_score = _extract_safe_score(pillar.get("score"))
        raw_declared = pillar.get("declared_score")
        declared_score = _extract_safe_score(raw_declared) if raw_declared is not None else exact_score

        band_info = resolve_maturity_band(exact_score, ANNEX_MATURITY_BANDS, locale=doc_lang)
        band_label = band_info.get("label", "")

        if exact_score < LOW_MATURITY_CALIBRATION_THRESHOLD:
            lbl_pos = t("calib_label_observed_state", locale=doc_lang)
            lbl_neg = t("calib_label_critical_gap", locale=doc_lang)
        else:
            lbl_pos = t("calib_label_operational_strength", locale=doc_lang)
            lbl_neg = t("calib_label_operational_gap", locale=doc_lang)

        fallback_pos, fallback_neg = _resolve_pillar_kpi_fallback(current_tower_id, p_id or "", doc_lang)

        quarantined_count = 0
        norm_p_id = str(p_id or "").strip().upper()
        canonical_p_id = (
            norm_p_id
            if "." in norm_p_id or not current_tower_id
            else f"{current_tower_id}.{norm_p_id}"
        )

        # 1. Resolve and sanitize Observed State / Strength
        asis_desc = (pillar.get("asis_architecture_description") or "").strip()
        if _is_placeholder_boilerplate(asis_desc):
            asis_desc = ""
        if active_gatekeeper and canonical_p_id and asis_desc:
            desc_val = active_gatekeeper.validate_text_for_pillar(
                asis_desc, canonical_p_id, tower_id=current_tower_id
            )
            if desc_val.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN:
                quarantined_count += 1
                asis_desc = ""
        clean_state = _sanitize_strength_clause(asis_desc, fallback_pos, exact_score, doc_lang)

        raw_justification = str(pillar.get("justification") or "").strip()
        if active_gatekeeper and raw_justification:
            just_val = active_gatekeeper.validate_text_for_pillar(
                raw_justification, canonical_p_id, tower_id=current_tower_id
            )
            if just_val.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN:
                quarantined_count += 1
                raw_justification = ""

        if active_gatekeeper and canonical_p_id and clean_state:
            state_val = active_gatekeeper.validate_text_for_pillar(
                clean_state, canonical_p_id, tower_id=current_tower_id
            )
            if state_val.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN:
                quarantined_count += 1
                clean_state = fallback_pos

        # 2. Resolve and sanitize Resilience Breach / Gap
        raw_findings = pillar.get("health_check_asis", [])
        if active_gatekeeper and canonical_p_id:
            sanitized_findings, quarantined = active_gatekeeper.sanitize_pillar_findings(
                canonical_p_id, raw_findings, tower_id=current_tower_id
            )
            quarantined_count += len(quarantined)
        else:
            sanitized_findings = raw_findings
            quarantined = []

        if sanitized_findings:
            top_f = sanitized_findings[0]
            f_text = (top_f.get("finding") or top_f.get("risk_observed") or "").strip()
            clean_f = _scrub_template_glitches_and_token_leaks(
                _sanitize_breach_clause(f_text, fallback_neg, doc_lang), doc_lang
            )
            if active_gatekeeper and canonical_p_id and clean_f:
                f_val = active_gatekeeper.validate_text_for_pillar(
                    clean_f, canonical_p_id, tower_id=current_tower_id
                )
                if f_val.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN:
                    quarantined_count += 1
                    clean_f = _scrub_template_glitches_and_token_leaks(fallback_neg, doc_lang)
        else:
            clean_f = _scrub_template_glitches_and_token_leaks(fallback_neg, doc_lang)

        clean_state = _scrub_broken_kpi_boilerplate_clauses(
            _scrub_template_glitches_and_token_leaks(clean_state, doc_lang),
            _scrub_template_glitches_and_token_leaks(fallback_pos, doc_lang),
            doc_lang,
        )
        clean_f = _scrub_broken_kpi_boilerplate_clauses(
            _scrub_template_glitches_and_token_leaks(clean_f, doc_lang),
            _scrub_template_glitches_and_token_leaks(fallback_neg, doc_lang),
            doc_lang,
        )
        clean_state = _scrub_foreign_domain_bleed_for_tower(
            clean_state, current_tower_id, _scrub_template_glitches_and_token_leaks(fallback_pos, doc_lang)
        )
        clean_f = _scrub_foreign_domain_bleed_for_tower(
            clean_f, current_tower_id, _scrub_template_glitches_and_token_leaks(fallback_neg, doc_lang)
        )

        full_pillar_ctx = f"{clean_state} {clean_f} {pillar.get('literal_evidence', '')}"
        reconciled_states = _reconcile_contradictory_replication_claims([clean_state], full_pillar_ctx, doc_lang)
        if reconciled_states:
            clean_state = reconciled_states[0]
        reconciled_gaps = _reconcile_contradictory_replication_claims([clean_f], full_pillar_ctx, doc_lang)
        if reconciled_gaps:
            clean_f = reconciled_gaps[0]

        exact_score = _calibrate_empirical_maturity_score(exact_score, pillar, clean_state, clean_f)
        exact_score, clean_state = _reconcile_telemetry_tool_contradictions(
            exact_score, clean_state, clean_f, fallback_neg, doc_lang
        )
        # Synchronize calibrated score and CMMI band label back into the source pillar payload so Executive Summary,
        # Table 4, and global averages remain 100% mathematically consistent with Table 5/6.
        pillar["score"] = exact_score
        pillar["calibrated_score"] = exact_score
        if raw_declared is None:
            declared_score = exact_score
            pillar["declared_score"] = exact_score
        band_info = resolve_maturity_band(exact_score, ANNEX_MATURITY_BANDS, locale=doc_lang)
        band_label = band_info.get("label", "")
        pillar["maturity_level"] = band_label
        pillar["band_label"] = band_label

        if exact_score < LOW_MATURITY_CALIBRATION_THRESHOLD:
            lbl_pos = t("calib_label_observed_state", locale=doc_lang)
            lbl_neg = t("calib_label_critical_gap", locale=doc_lang)
        else:
            lbl_pos = t("calib_label_operational_strength", locale=doc_lang)
            lbl_neg = t("calib_label_operational_gap", locale=doc_lang)

        if raw_justification:
            raw_clean = _scrub_template_glitches_and_token_leaks(
                _sanitize_strength_clause(raw_justification, "", exact_score, doc_lang), doc_lang
            )
            justification = raw_clean or _scrub_template_glitches_and_token_leaks(raw_justification, doc_lang)
        elif clean_state:
            justification = f"• **{lbl_pos}:** {clean_state}\n\n• **{lbl_neg}:** {clean_f.rstrip('.')}."
        else:
            justification = f"• **{lbl_neg}:** {clean_f.rstrip('.')}."

        from assessment_engine.infrastructure.localization import (
            restore_locale_diacritics,
        )

        justification = restore_locale_diacritics(justification, doc_lang)

        dec_band_info = resolve_maturity_band(declared_score, ANNEX_MATURITY_BANDS, locale=doc_lang)
        dec_band_label = dec_band_info.get("label", "")

        pillar_for_narrative = dict(pillar)
        pillar_for_narrative["health_check_asis"] = sanitized_findings
        if not asis_desc or (quarantined_count > 0 and clean_state == fallback_pos):
            pillar_for_narrative["asis_architecture_description"] = ""
        if active_gatekeeper and canonical_p_id:
            raw_lit_ev = str(pillar_for_narrative.get("literal_evidence") or "").strip()
            if raw_lit_ev:
                lit_val = active_gatekeeper.validate_text_for_pillar(
                    raw_lit_ev, canonical_p_id, tower_id=current_tower_id
                )
                if lit_val.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN:
                    quarantined_count += 1
                    pillar_for_narrative["literal_evidence"] = ""

        raw_arch_paras = _sanitize_architectural_narrative(
            pillar_for_narrative,
            doc_lang,
            canonical_pillar_id=canonical_p_id,
            fallback_pos=clean_state,
            fallback_neg=clean_f,
        )
        deduped_arch_paras: list[str] = []
        seen_sentences: set[str] = set()
        for raw_p in raw_arch_paras:
            if not raw_p:
                continue
            cleaned_p = _scrub_foreign_domain_bleed_for_tower(
                _scrub_broken_kpi_boilerplate_clauses(raw_p, clean_state or clean_f, doc_lang),
                current_tower_id,
                clean_state or clean_f,
            )
            if not cleaned_p:
                continue
            cleaned_p = re.sub(r"([.)])([A-ZÁÉÍÓÚ])", r"\1 \2", cleaned_p)
            unique_sents: list[str] = []
            for sent in re.split(r"(?<=[.!?])\s+", cleaned_p):
                norm_s = re.sub(r"\W+", "", sent).lower()
                if len(norm_s) > 25 and norm_s in seen_sentences:
                    continue
                if len(norm_s) > 25:
                    seen_sentences.add(norm_s)
                unique_sents.append(sent)
            rejoined_p = " ".join(unique_sents).strip()
            if rejoined_p:
                deduped_arch_paras.append(rejoined_p)
        arch_paras = deduped_arch_paras
        op_reality = arch_paras[0] if arch_paras else ""

        # TRI-MODAL ENROUTER LOGIC (Argon Persona Mandate)
        delta = abs(exact_score - declared_score)
        # We no longer force artificial robotic phrases or Gartner boilerplate via 'is_alpha_hammer'.
        # The narrative relies purely on the LLM's synthesis from 'arch_paras'.

        # Cross-paragraph sentence deduplication to prevent verbatim finding cloning
        final_arch_paras: list[str] = []
        global_seen_sentences: set[str] = set()
        for p_text in arch_paras:
            cleaned_p = re.sub(r"([.)])([A-ZÁÉÍÓÚ])", r"\1 \2", p_text)
            p_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_p) if s.strip()]
            filtered_sents: list[str] = []
            for s in p_sents:
                norm_s = re.sub(r"\W+", "", s).lower()
                if len(norm_s) > 25:
                    if norm_s in global_seen_sentences:
                        continue
                    global_seen_sentences.add(norm_s)
                filtered_sents.append(s)
            reconstructed_p = " ".join(filtered_sents).strip()
            if reconstructed_p:
                final_arch_paras.append(reconstructed_p)
        arch_paras = final_arch_paras

        raw_target = pillar.get("target_score") or pillar.get("target_maturity_level") or pillar.get("target_level")
        if raw_target is not None:
            try:
                target_lvl = max(1, min(5, int(round(float(raw_target)))))
            except (ValueError, TypeError):
                target_lvl = min(5, int(exact_score) + 1)
        else:
            target_lvl = min(5, int(exact_score) + 1)
        target_label = str(target_lvl)

        rows.append(
            {
                "pillar_id": p_id,
                "canonical_pillar_id": canonical_p_id,
                "pillar_name": pillar_name,
                "score": exact_score,
                "declared_score": declared_score,
                "declared_band_label": dec_band_label,
                "score_formatted": format_number(exact_score, locale=doc_lang, decimals=2),
                "band_label": band_label,
                "justification": justification,
                "summary_diagnostic": clean_f,
                "quarantined_findings_count": quarantined_count,
                "operational_reality": op_reality,
                "architectural_narrative_paragraphs": arch_paras,
                "target_level": target_lvl,
                "target_label": target_label,
            }
        )

    if rows:
        total_weight = 0.0
        weighted_sum = 0.0
        for idx, r in enumerate(rows):
            src_pillar = pillars_list[idx] if idx < len(pillars_list) and isinstance(pillars_list[idx], dict) else {}
            raw_w = src_pillar.get("weight") or src_pillar.get("weighting") or src_pillar.get("pillar_weight")
            try:
                w = float(str(raw_w).replace("%", "").strip()) if raw_w is not None else 0.0
            except (ValueError, TypeError):
                w = 0.0
            if w > 0.0:
                total_weight += w
                weighted_sum += float(r["score"]) * w

        if total_weight > 0.0:
            calibrated_avg = round(weighted_sum / total_weight, 2)
        else:
            calibrated_avg = round(sum(float(r["score"]) for r in rows) / len(rows), 2)

        global_band_info = resolve_maturity_band(calibrated_avg, ANNEX_MATURITY_BANDS, locale=doc_lang)
        global_band_label = global_band_info.get("label", "")

        b_data["calibrated_global_score"] = calibrated_avg
        b_data["overall_maturity_score"] = calibrated_avg
        b_data["global_score"] = calibrated_avg
        b_data["global_maturity_band"] = global_band_label
        if isinstance(b_data.get("executive_summary"), dict):
            b_data["executive_summary"]["global_maturity_score"] = calibrated_avg
            b_data["executive_summary"]["overall_score"] = calibrated_avg
            b_data["executive_summary"]["maturity_level"] = global_band_label
            b_data["executive_summary"]["global_maturity_band"] = global_band_label
        if isinstance(b_data.get("maturity_summary"), dict):
            b_data["maturity_summary"]["global_score"] = calibrated_avg
            b_data["maturity_summary"]["average_score"] = calibrated_avg
            b_data["maturity_summary"]["maturity_level"] = global_band_label
            b_data["maturity_summary"]["band_label"] = global_band_label
        if isinstance(b_data.get("document_meta"), dict):
            b_data["document_meta"]["global_maturity_score"] = calibrated_avg
            b_data["document_meta"]["overall_score"] = calibrated_avg
            b_data["document_meta"]["maturity_level"] = global_band_label

    return rows
