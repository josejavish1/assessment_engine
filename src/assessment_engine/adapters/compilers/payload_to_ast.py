import csv
import html
import json
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Final, List, Mapping, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN_ARCHETYPE: Final[str] = "ENTERPRISE_SYSTEMS"

COLOR_STATUS_ALIGNED: Final[str] = "E2F0D9"
COLOR_STATUS_GAP: Final[str] = "FCE4D6"
COLOR_STATUS_CONSERVATIVE: Final[str] = "D9E1F2"
COLOR_CALLOUT_BG: Final[str] = "F1F5F9"
DIVERGENCE_ALIGNMENT_TOLERANCE: Final[float] = 0.05
DIVERGENCE_ALERT_THRESHOLD: Final[float] = 0.50
DEFAULT_UNASSESSED_PILLAR_SCORE: Final[float] = 2.50


def _safe_float(val: Any, default: float = 0.0, locale: str | None = None) -> float:
    """Defensively parse any numeric string, int, float, or None without crashing or locale corruption."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        from assessment_engine.domain.actuarial_scale_calibrator import (
            safe_float as actuarial_safe_float,
        )
        res = actuarial_safe_float(val, locale=locale, allow_zero=True)
        if res is not None:
            return float(res)
    except Exception:
        pass
    try:
        raw_str = str(val).strip()
        is_euro_style = (locale and any(locale.lower().startswith(p) for p in ("es", "de", "it", "pt", "fr"))) or "€" in raw_str or "EUR" in raw_str
        clean = re.sub(r"^[^\d\-+]+", "", raw_str)
        clean = re.sub(r"[^\d]+$", "", clean).strip()

        if "," in clean and "." in clean:
            if clean.rfind(".") > clean.rfind(","):
                clean = clean.replace(",", "")
            else:
                clean = clean.replace(".", "").replace(",", ".")
            return float(clean)
        if is_euro_style and re.search(r"^\d{1,3}(?:\.\d{3})+$", clean):
            return float(clean.replace(".", ""))
        if re.search(r"^\d{1,3}(?:,\d{3})+$", clean):
            return float(clean.replace(",", ""))
        if re.search(r"^\d+,\d+$", clean):
            return float(clean.replace(",", "."))
        return float(clean)
    except (ValueError, TypeError):
        return default


def _partition_risks_into_tiers(
    risks_data_list: list[dict[str, Any]],
    total_fair_ale: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministically partitions risks into Tier 1 (>=15%), Tier 2 (3-15%), and Tier 3 (<3%)."""
    primary_risks = [
        r
        for r in risks_data_list
        if str(r.get("ownership_type") or "").strip().upper()
        not in ("TANGENTIAL_CONTRIBUTOR", "OUT_OF_SCOPE", "SECONDARY_CONTRIBUTOR")
        and not bool(r.get("is_cross_domain_contamination", False))
    ]
    pool = primary_risks if primary_risks else list(risks_data_list)
    sorted_pool = sorted(
        pool,
        key=lambda x: _safe_float(x.get("ale") or x.get("ale_val") or x.get("fair_ale_score") or 0.0),
        reverse=True,
    )

    t1_threshold = total_fair_ale * 0.15 if total_fair_ale > 0 else 0.0
    t2_threshold = total_fair_ale * 0.03 if total_fair_ale > 0 else 0.0

    t1: list[dict[str, Any]] = []
    t2: list[dict[str, Any]] = []
    t3: list[dict[str, Any]] = []

    for r in sorted_pool:
        r_ale = _safe_float(r.get("ale") or r.get("ale_val") or r.get("fair_ale_score") or 0.0)
        if r_ale >= t1_threshold and r_ale > 0.0:
            t1.append(r)
        elif r_ale >= t2_threshold and r_ale > 0.0:
            t2.append(r)
        else:
            t3.append(r)

    if not t1 and sorted_pool:
        t1_count = max(1, len(sorted_pool) // 4)
        t1 = sorted_pool[:t1_count]
        remaining = sorted_pool[t1_count:]
        t2_count = max(1, len(remaining) // 2) if remaining else 0
        t2 = remaining[:t2_count]
        t3 = remaining[t2_count:]

    return t1, t2, t3

_ARCHETYPE_KEYWORD_RULES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "INFRASTRUCTURE_PHYSICAL",
        (
            "facility",
            "facilities",
            "physical",
            "power",
            "cooling",
            "hvac",
            "ups",
            "datacenter",
            "data center",
            "data hall",
            "cabling",
        ),
    ),
    (
        "INDUSTRIAL_OT",
        (
            "scada",
            "plc",
            "ics",
            "dcs",
            "rtu",
            "hmi",
            "historian",
            "modbus",
            "profinet",
            "opc-ua",
            "cnc",
            "robotics",
            "automation",
            "industrial",
            "factory",
            "manufacturing",
            "plant",
            "telecontrol",
            "weighbridge",
            "bascula",
            "báscula",
            "básculas",
            "expedicion",
            "expedición",
            "dispatch",
            "isa-95",
            "iec 62443",
        ),
    ),
    (
        "FINANCIAL_CORE",
        (
            "banking",
            "core banking",
            "swift",
            "sepa",
            "payment",
            "ledger",
            "clearing",
            "settlement",
            "trading",
        ),
    ),
    (
        "HEALTHCARE_CLINICAL",
        (
            "clinical",
            "hospital",
            "pacs",
            "ehr",
            "emr",
            "hl7",
            "fhir",
            "dicom",
            "biomedical",
        ),
    ),
    (
        "RETAIL_SUPPLY_CHAIN",
        (
            "point of sale",
            "supply chain",
            "omnichannel",
            "warehouse",
            "ecommerce",
            "e-commerce",
            "pos",
            "wms",
            "oms",
            "edi",
            "rfid",
            "inventory",
            "merchandising",
        ),
    ),
    (
        "PUBLIC_SECTOR_GOV",
        (
            "public sector",
            "citizen",
            "e-government",
            "municipal",
            "registry",
            "taxation",
            "defense",
            "customs",
            "agency",
        ),
    ),
    (
        "SECURITY_GOVERNANCE",
        (
            "security",
            "cyber",
            "iam",
            "governance",
            "compliance",
            "audit",
            "risk",
            "drp",
            "bcp",
            "resilience",
            "zero trust",
            "zero-trust",
        ),
    ),
    (
        "DIGITAL_WORKPLACE",
        (
            "workplace",
            "end-user",
            "end user",
            "euc",
            "endpoint",
            "desktop",
            "vdi",
            "intune",
            "autopilot",
            "dex",
            "collaboration",
            "productivity",
            "service desk",
        ),
    ),
    (
        "COMPUTE_PLATFORMS",
        (
            "compute",
            "cloud",
            "virtualization",
            "storage",
            "database",
            "network",
            "platform",
            "kubernetes",
            "middleware",
            "erp",
            "legacy",
            "mainframe",
        ),
    ),
)

_COMPILED_ARCHETYPE_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = tuple(
    (
        archetype,
        re.compile(
            rf"(?<!\w)(?:{'|'.join(re.escape(kw) for kw in sorted(keywords, key=len, reverse=True))})(?!\w)",
            re.IGNORECASE,
        ),
    )
    for archetype, keywords in _ARCHETYPE_KEYWORD_RULES
)


def resolve_domain_archetype(
    domain_id: str,
    blueprint_data: Optional[Mapping[str, Any]] = None,
) -> str:
    """Resolve the ontological domain archetype dynamically from payload metadata or semantic cues.

    Uses boundary-safe pre-compiled regexes across multi-vertical ontologies
    (Physical Infrastructure, Industrial OT/ICS, Security/Governance, Sector Core,
    and Compute Platforms) without hardcoded tower ID lookup tables.
    """
    if blueprint_data:
        doc_meta = blueprint_data.get("document_meta")
        explicit_archetype = str(
            blueprint_data.get("domain_archetype")
            or blueprint_data.get("archetype")
            or (doc_meta.get("domain_archetype") if isinstance(doc_meta, Mapping) else "")
            or ""
        ).strip().upper()
        if explicit_archetype:
            return explicit_archetype

    bp = blueprint_data if isinstance(blueprint_data, Mapping) else {}
    search_corpus = " ".join(
        filter(
            None,
            [
                str(domain_id or ""),
                str(bp.get("tower_name") or ""),
                str(bp.get("domain_name") or ""),
                str(bp.get("title") or ""),
            ],
        )
    )

    scores: list[tuple[int, str]] = []
    for archetype, pattern in _COMPILED_ARCHETYPE_PATTERNS:
        matches = len(pattern.findall(search_corpus))
        if matches > 0:
            scores.append((matches, archetype))

    if scores:
        scores.sort(key=lambda item: (-item[0], item[1]))
        return scores[0][1]

    return DEFAULT_DOMAIN_ARCHETYPE

from assessment_engine.domain.actuarial.downtime_calibrator import (
    ActuarialDowntimeCalibrator,
)
from assessment_engine.domain.schemas import (
    CellNode,
    DocumentAST,
    HeadingNode,
    PageBreakNode,
    ParagraphNode,
    SpacerNode,
    TableNode,
    TableRowNode,
    TOCEntryNode,
    TOCNode,
)
from assessment_engine.domain.schemas.risk_ontology import (
    CausalBowTie,
    ConditionalLossEvent,
    CouplingRegime,
    FairActuarialInput,
)
from assessment_engine.infrastructure.localization import (
    apply_vocabulary_substitutions,
    format_currency,
    format_date_localized,
    format_number,
    get_localized_list,
    load_locales_catalog,
    t,
)


def clean_client_name(client_name: str, locale: Optional[str] = None) -> str:
    """Clean raw client identifier removing version suffixes while preserving corporate casing."""
    target_locale = locale or "en"
    if not client_name or not client_name.strip():
        return t("default_client_name", locale=target_locale)
    import re

    cleaned = re.sub(r"[_-][vV]\d+\b", "", client_name).strip()
    cleaned = cleaned.replace("_", " ")
    if " " not in cleaned:
        cleaned = cleaned.replace("-", " ")
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return t("default_client_name", locale=target_locale)

    # Only force capitalization on fully lowercase words to preserve mixed-case brands (e.g. McKinsey, PwC, JPMorgan)
    words = [w.capitalize() if w.islower() else w for w in cleaned.split(" ")]
    return " ".join(words)


from assessment_engine.adapters.compilers.ast_appendices_builder import (
    build_appendix_c_glossary_and_disclaimer as _build_appendix_c_glossary_and_disclaimer_fn,
)
from assessment_engine.adapters.compilers.ast_appendices_builder import (
    build_cmmi_methodology_and_capabilities as _build_cmmi_methodology_and_capabilities_fn,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_criticality_bullet as _build_criticality_bullet,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_dii_bullet as _build_dii_bullet,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_erc_bullet as _build_erc_bullet,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_feasibility_bullet as _build_feasibility_bullet,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_heatmap_mosaic as _build_heatmap_mosaic,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_lm_scale_table as _build_lm_scale_table,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_regulatory_bullet as _build_regulatory_bullet,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_spof_bullet as _build_spof_bullet,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    build_tef_scale_table as _build_tef_scale_table,
)
from assessment_engine.domain.actuarial_scale_calibrator import (
    compute_dynamic_lm_brackets,
    compute_dynamic_lm_thresholds,
    safe_float,
)

_CRITICAL_DEFICIT_TELEMETRY_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:zero\s+(?:dex|telemetry|real-time|visibility|tooling|error\s+budgets|cmdb)|"
    r"no\s+(?:dex|telemetry|real-time\s+telemetry|automated\s+provisioning|drp|cmdb|error\s+budgets|slis|slos)|"
    r"lack\s+of\s+(?:dex\s+tools|telemetry|formal\s+equipment\s+renewal|monitoring|tracing|apm|clean\s+agent|cmdb|error\s+budgets)|"
    r"absence\s+of\s+(?:a\s+formal\s+equipment\s+renewal|dex\s+tools|telemetry|observability|ashrae|cmdb|error\s+budgets)|"
    r"nula\s+(?:telemetr[íi]a|visibilidad|instrumentaci[óo]n|observabilidad)|"
    r"sin\s+(?:telemetr[íi]a|herramientas\s+dex|visibilidad\s+en\s+tiempo\s+real|ciclo\s+formal\s+de\s+renovaci[óo]n|correlaci[óo]n\s+de\s+eventos|drp|cmdb|error\s+budgets)|"
    r"carece\s+de\s+(?:telemetr[íi]a|visibilidad|instrumentaci[óo]n|herramientas\s+dex|trazabilidad|cmdb)|"
    r"falta\s+de\s+(?:herramientas\s+dex|telemetr[íi]a|ciclo\s+formal\s+de\s+renovaci[óo]n|observabilidad|cmdb)|"
    r"ausencia\s+de\s+(?:un\s+ciclo\s+formal\s+de\s+renovaci[óo]n|herramientas\s+dex|telemetr[íi]a|control\s+de\s+obsolescencia|cmdb|error\s+budgets)|"
    r"inexistencia\s+de\s+(?:telemetr[íi]a|herramientas\s+dex|ciclo\s+formal|cmdb)|"
    r"preparaci[óo]n\s+artesanal|im[áa]genes\s+est[áa]ticas|"
    r"artisanal\s+preparation|static\s+images|"
    r"logrotate|logs?\s+de\s+apache|vaciado\s+manual|matar\s+sesiones|"
    r"scripts?\s+en\s+zabbix|reactiva\s+y\s+manual|ca[íi]da\s+por\s+llenado\s+de\s+disco|"
    r"acometida\s+el[ée]ctrica\s+[úu]nica|single\s+municipal\s+medium-voltage\s+feed)\b",
    re.IGNORECASE,
)

_BROKEN_MAIL_MERGE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:Exposici[óo]n\s+operativa\s+y\s+riesgo\s+de\s+interrupci[óo]n\s+del\s+servicio(?:\s+ante\s+incidencias\s+no\s+contenidas(?:\s+en\s+[^.;]+?)?)?\s*\.\s*|"
    r"Operational\s+exposure\s+and\s+service\s+disruption\s+risk(?:\s+from\s+uncontained\s+incidents(?:\s+in\s+[^.;]+?)?)?\s*\.\s*)",
    re.IGNORECASE,
)

_CONTRADICTORY_PRAISE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:exemplary\s+discipline\s+in\s+(?:corporate\s+)?(?:laptop|equipment)\s+renewal|"
    r"disciplina\s+ejemplar\s+en\s+la\s+renovaci[óo]n\s+de\s+(?:port[áa]tiles|equipos)(?:\s+corporativos)?|"
    r"placing\s+[^.,;]{1,35}?\s+at\s+the\s+(?:boundary|limit|threshold)(?:\s+of\s+(?:the\s+)?(?:bracket|range|tier)\s+of)?\s+level\s+[234]|"
    r"sit\s+at\s+the\s+(?:boundary|limit|threshold)(?:\s+of\s+(?:the\s+)?(?:bracket|range|tier)\s+of)?\s+level\s+[234]|"
    r"situ(?:ando\s+a\s+[^.,;]{1,35}?|[áa]ndose|an)\s+en\s+(?:la\s+frontera|el\s+l[íi]mite|el\s+umbral)(?:\s+de\s+tramo)?\s+del\s+nivel\s+[234]|"
    r"se\s+sit[úu]an?\s+en\s+(?:la\s+frontera|el\s+l[íi]mite|el\s+umbral)(?:\s+de\s+tramo)?\s+del\s+nivel\s+[234]|"
    r"(?:en\s+(?:la\s+frontera|el\s+l[íi]mite|el\s+umbral)(?:\s+de\s+tramo)?|al\s+l[íi]mite(?:\s+de\s+tramo)?)\s+del\s+nivel\s+[234]|"
    r"at\s+the\s+(?:boundary|limit|threshold)(?:\s+of\s+(?:the\s+)?(?:bracket|range|tier))?\s+of\s+level\s+[234]|"
    r"plataforma\s+legacy\s*/\s*mainframe\s*(?:&|y)\s*operaci[óo]n\s+core)",
    re.IGNORECASE,
)

_DANGLING_DISCOURSE_OPENER_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:Aunque\s+la\s+conectividad\s+ha\s+evolucionado\s*,?\s*|"
    r"Although\s+connectivity\s+has\s+evolved\s*,?\s*)",
    re.IGNORECASE,
)


def _sanitize_dangling_discourse_openers(text: str, locale: str) -> str:
    """Repair mid-thought discourse openers that reference unintroduced acronyms (e.g., RODC)."""
    if not text:
        return text
    if _DANGLING_DISCOURSE_OPENER_RE.search(text):
        is_es = str(locale).lower().startswith("es")
        prefix = (
            "En la arquitectura de identidad y controladores de dominio en plantas remotas (RODC), aunque la conectividad ha evolucionado, "
            if is_es
            else "In the remote plant identity and Read-Only Domain Controller (RODC) architecture, although connectivity has evolved, "
        )
        return _DANGLING_DISCOURSE_OPENER_RE.sub(prefix, text, count=1)
    return text


def _synchronize_inline_recalibrated_scores(text: str, locale: str) -> str:
    """Reconcile inline narrative score recalibrations and CMMI level threshold contradictions."""
    if not text:
        return text
    is_es = str(locale).lower().startswith("es")

    def _fix_score_level_clause(match: re.Match[str]) -> str:
        full_str = match.group(0)
        score_str = match.group(1).replace(",", ".")
        try:
            score_val = float(score_str)
        except ValueError:
            return full_str
        correct_label = _resolve_cmmi_maturity_label(score_val, locale=locale)
        replaced = re.sub(
            r"\((?:Nivel|Level)\s*\d\s*[-–—]\s*[^)]+\)",
            f"({correct_label})",
            full_str,
            flags=re.IGNORECASE,
        )
        if score_val < 2.50:
            if is_es:
                replaced = re.sub(
                    r"(?:en\s+(?:la\s+frontera|el\s+l[íi]mite|el\s+umbral)|al\s+l[íi]mite)\s+del\s+nivel\s+[34]",
                    f"dentro del rango operativo de {correct_label}",
                    replaced,
                    flags=re.IGNORECASE,
                )
            else:
                replaced = re.sub(
                    r"(?:at\s+the\s+(?:boundary|limit|threshold)\s+of\s+level\s+[34])",
                    f"within the operational band of {correct_label}",
                    replaced,
                    flags=re.IGNORECASE,
                )
        return replaced

    text = re.sub(
        r"\b(\d[.,]\d{1,2})\s*(?:sobre|out\s+of|/)\s*5[.,]0{1,2}\s*\((?:Nivel|Level)\s*\d\s*[-–—]\s*[^)]+\)[^.;]*",
        _fix_score_level_clause,
        text,
        flags=re.IGNORECASE,
    )
    return text


def _resolve_cmmi_maturity_label(score: float, locale: str) -> str:
    """Resolve deterministic CMMI maturity level label strictly aligned with rubric boundaries:
    1.00 - 1.59: Level 1 (Initial)
    1.60 - 2.59: Level 2 (Managed / Repeatable)
    2.60 - 3.59: Level 3 (Defined)
    3.60 - 4.59: Level 4 (Quantitatively Managed)
    4.60 - 5.00: Level 5 (Optimizing)
    """
    is_es = str(locale).lower().startswith("es")
    val = round(float(score), 2)
    if val < 1.60:
        return "Nivel 1 - Inicial" if is_es else "Level 1 - Initial"
    if val < 2.60:
        return "Nivel 2 - Gestionado" if is_es else "Level 2 - Managed"
    if val < 3.60:
        return "Nivel 3 - Definido" if is_es else "Level 3 - Defined"
    if val < 4.60:
        return "Nivel 4 - Gestionado Cuantitativamente" if is_es else "Level 4 - Quantitatively Managed"
    return "Nivel 5 - Optimizado" if is_es else "Level 5 - Optimizing"


def _reconcile_cmmi_level_mentions_in_prose(text: str, locale: str) -> str:
    """Detect inline score-to-CMMI-level mismatches in prose (e.g. '1.78 (Nivel 1 - Initial)') and correct them."""
    if not text:
        return text
    is_es = str(locale).lower().startswith("es")

    def _replace_score_level(match: re.Match[str]) -> str:
        prefix = match.group(1)
        score_raw = match.group(2)
        suffix = match.group(4)
        score_val = _safe_float(score_raw.replace(",", "."), default=0.0)
        if score_val < 1.0 or score_val > 5.0:
            return match.group(0)
        correct_label = _resolve_cmmi_maturity_label(score_val, locale=locale)
        return f"{prefix}{score_raw}{suffix}{correct_label}"

    pattern = re.compile(
        r"(\b)(\d[.,]\d{1,2})(\s*(?:/\s*5(?:[.,]0+)?\s*)?\(\s*)(Nivel\s+[1-5]\s*[-–—:]\s*[^)]+|Level\s+[1-5]\s*[-–—:]\s*[^)]+)",
        re.IGNORECASE,
    )
    text = pattern.sub(_replace_score_level, text)

    # Also sanitize inverted 'Nivel 1 (Inicial)' or 'Nivel 1 - Initial' preceded by a score within 25 chars
    def _replace_nearby_score_level(match: re.Match[str]) -> str:
        score_raw = match.group(1)
        mid = match.group(2)
        score_val = _safe_float(score_raw.replace(",", "."), default=0.0)
        if score_val < 1.0 or score_val > 5.0:
            return match.group(0)
        correct_label = _resolve_cmmi_maturity_label(score_val, locale=locale)
        return f"{score_raw}{mid}{correct_label}"

    nearby_pattern = re.compile(
        r"\b(\d[.,]\d{2})(\s*(?:puntos|/\s*5[.,]0\b|sobre\s+5[.,]0)?\s*(?:,\s*|\s+situ[áa]ndose\s+en\s+|\s+correspondiente\s+a\s+|\s+clasificado\s+como\s+|\s*[-–—]\s*))"
        r"(?:Nivel\s+[1-5]\s*(?:[-–—:]\s*[A-Za-zÁÉÍÓÚáéíóúñÑ]+|\([A-Za-zÁÉÍÓÚáéíóúñÑ]+\))|Level\s+[1-5]\s*(?:[-–—:]\s*[A-Za-z]+|\([A-Za-z]+\)))",
        re.IGNORECASE,
    )
    text = nearby_pattern.sub(_replace_nearby_score_level, text)

    if is_es:
        text = re.sub(r"\bNivel\s+1\s*[-–—]\s*Initial\b", "Nivel 1 - Inicial", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNivel\s+2\s*[-–—]\s*(?:Managed|Repeatable)\b", "Nivel 2 - Gestionado", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNivel\s+3\s*[-–—]\s*Defined\b", "Nivel 3 - Definido", text, flags=re.IGNORECASE)
    return text


def _reconcile_internal_narrative_contradictions(text: str, locale: str) -> str:
    """Sanitize contradictory boilerplate praise, colloquial interview quotes, and template mashups from prose."""
    if not text:
        return text
    is_es = str(locale).lower().startswith("es")
    text = _reconcile_cmmi_level_mentions_in_prose(text, locale=locale)
    if is_es:
        text = re.sub(
            r"disciplina\s+ejemplar\s+en\s+la\s+renovaci[óo]n\s+de\s+(?:port[áa]tiles|equipos)(?:\s+corporativos)?",
            "gestión reactiva del ciclo de vida del parque de dispositivos",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r",?\s*situando\s+a\s+[^.,;]{1,35}?\s+en\s+(?:la\s+frontera|el\s+l[íi]mite)\s+del\s+nivel\s+[234]",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r",?\s*(?:en\s+(?:la\s+frontera|el\s+l[íi]mite)|al\s+l[íi]mite)\s+del\s+nivel\s+[234]",
            "",
            text,
            flags=re.IGNORECASE,
        )
        # Reconcile "Idle Compute / Over-provisioning" vs "Extreme Rightsizing / Resource Starvation" contradiction
        text = re.sub(
            r"C[óo]mputo\s+Ocioso\s+e\s+Infraestructura\s+Zombi\s*\(\s*sobre-?aprovisionamiento\s*\)",
            "Desequilibrio de Capacidad, Deuda de Licenciamiento y Fricción FinOps",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"c[óo]mputo\s+ocioso\s+e\s+infraestructura\s+zombi\s*\(\s*sobre-?aprovisionamiento\s*\)",
            "desequilibrio de asignación de recursos y fricción de capacidad",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"Plataforma\s+Legacy\s*/\s*Mainframe\s*(?:&|y)\s*Operaci[óo]n\s+Core",
            "Gobernanza y Operación de Sistemas Core",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"Healing\s*&\s*Mean-Time-to-Restore\s*\(MTTR\)\s*Reduction",
            "mediante mecanismos de autorrecuperación y reducción del tiempo medio de restauración (MTTR)",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"([a-záéíóúñüA-ZÁÉÍÓÚÑÜ]{4,})\s+Reduction\b",
            r"\1",
            text,
        )
        text = re.sub(
            r'["«“]\s*Nosotros\s+deber[íi]amos\s+de\s+crear[^"»”]{1,120}?["»”]',
            "la carencia de plantillas estandarizadas de aprovisionamiento",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"La\s+operativa\s+se\s+ve\s+severamente\s+condicionada\s+por\s+la\s+mayor[íi]a\s+de\s+las\s+",
            "La operativa se ve severamente condicionada dado que en la mayoría de las ",
            text,
            flags=re.IGNORECASE,
        )
    else:
        text = re.sub(
            r"exemplary\s+discipline\s+in\s+(?:corporate\s+)?(?:laptop|equipment)\s+renewal",
            "reactive lifecycle management across the endpoint fleet",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r",?\s*placing\s+[^.,;]{1,35}?\s+at\s+the\s+boundary\s+of\s+level\s+3",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"Legacy\s*/\s*Mainframe\s+Platform\s*(?:&|and)\s*Core\s+Operations?",
            "Core Systems Operations & Governance",
            text,
            flags=re.IGNORECASE,
        )
    return text

_EXPLICIT_CALIBRATED_DOWNGRADE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:calibrad[oa]\s+a\s+la\s+baja|ajustad[oa]\s+a|recalibrad[oa]\s+a|"
    r"downgraded\s+to|calibrated\s+(?:down\s+)?to|puntuaci[óo]n\s+auditada\s+de)"
    r"(?:[^0-9]{1,45}?\bde\s+[1-5][.,]\d{1,2}\s+a\s+|[^0-9]{1,45}?)"
    r"\b([1-4][.,]\d{1,2})\b",
    re.IGNORECASE,
)


def _reconcile_replication_topology_prose(text: str, locale: str) -> str:
    """Reconcile contradictory synchronous vs. asynchronous replication statements in prose.

    Prevents boilerplate templates from asserting 'ordinary synchronous replication'
    as a ransomware propagation vector when the architecture relies on asynchronous
    replication without immutable snapshots/WORM.
    """
    if not text:
        return text
    if str(locale).lower().startswith("es"):
        text = re.sub(
            r"replicaci[óo]n\s+s[íi]ncrona\s+ordinaria\s+entre\s+cabinas",
            "replicación entre cabinas sin inmutabilidad criptográfica (WORM/SnapLock)",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"replicaci[óo]n\s+s[íi]ncrona\s+ordinaria",
            "replicación estándar sin bloqueo de inmutabilidad (WORM)",
            text,
            flags=re.IGNORECASE,
        )
    else:
        text = re.sub(
            r"ordinary\s+synchronous\s+replication\s+between\s+arrays",
            "standard array replication lacking cryptographic immutability (WORM/SnapLock)",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"ordinary\s+synchronous\s+replication",
            "standard replication without WORM immutability",
            text,
            flags=re.IGNORECASE,
        )
    return text


def _calibrate_pillar_score_from_evidence(pillar_dict: Mapping[str, Any], raw_score: float) -> float:
    """Enforce epistemic consistency between qualitative pillar evidence and numerical maturity score.

    If a pillar sits at or near the default unassessed baseline (e.g., 2.50) or higher,
    but its explicit calibrated score or diagnostic prose testifies to a complete absence
    of foundational telemetry/tooling (Level 1 Initial) or an explicit auditor downgrade,
    cap the score to prevent scoring contradictions between tables and prose.
    """
    for override_key in ("calibrated_score", "audited_score", "auditor_score", "adjusted_score", "final_score"):
        calibrated_override = pillar_dict.get(override_key)
        if calibrated_override is not None:
            cal_val = _safe_float(calibrated_override, default=raw_score)
            if 1.0 <= cal_val < raw_score:
                return cal_val

    evidence_corpus = " ".join(
        str(pillar_dict.get(k) or "")
        for k in (
            "finding",
            "findings",
            "justification",
            "description",
            "narrative",
            "gap_analysis",
            "status",
            "calibration_rationale",
            "divergence_rationale",
            "auditor_notes",
        )
    )

    explicit_match = _EXPLICIT_CALIBRATED_DOWNGRADE_RE.search(evidence_corpus)
    if explicit_match:
        parsed_downgrade = _safe_float(explicit_match.group(1), default=raw_score)
        if 1.0 <= parsed_downgrade < raw_score:
            return parsed_downgrade

    if raw_score >= 2.0 and _CRITICAL_DEFICIT_TELEMETRY_RE.search(evidence_corpus):
        # If prose explicitly states zero telemetry/tooling, cap maturity at 1.25 (Initial)
        if re.search(
            r"\b(?:zero\s+(?:dex|telemetry|tooling)|nula\s+telemetr[íi]a|sin\s+telemetr[íi]a|"
            r"carece\s+de\s+telemetr[íi]a|inexistencia\s+de\s+telemetr[íi]a|sin\s+herramientas\s+dex)\b",
            evidence_corpus,
            re.IGNORECASE,
        ):
            return min(raw_score, 1.25)
        return min(raw_score, 1.50)

    return raw_score


def extract_dimension_boundary_profile(
    pillars_analysis: List[Dict[str, Any]],
    current_maturity_score: float,
    locale: str,
) -> Tuple[str, str, str, str]:
    """Extracts the weakest and strongest dimension names and formatted scores.
    Returns: (strongest_name, strongest_score_str, weakest_name, weakest_score_str)
    """
    valid_dims: List[Tuple[str, float]] = []
    for p in pillars_analysis:
        if not isinstance(p, dict):
            continue
        name = str(p.get("pillar_name") or p.get("name") or "").strip()
        raw_score = p.get("score") if p.get("score") is not None else p.get("maturity_score")
        if name and raw_score is not None:
            try:
                eff_score = _calibrate_pillar_score_from_evidence(p, float(raw_score))
                p["score"] = eff_score
                valid_dims.append((name, eff_score))
            except (ValueError, TypeError):
                continue

    if not valid_dims:
        return "", "", "", ""

    sorted_dims = sorted(valid_dims, key=lambda x: x[1])
    weakest_name, weakest_score = sorted_dims[0]
    strongest_name, strongest_score = sorted_dims[-1]

    strongest_str = format_number(strongest_score, locale=locale, decimals=2)
    weakest_str = format_number(weakest_score, locale=locale, decimals=2)

    return strongest_name, strongest_str, weakest_name, weakest_str


_ENGLISH_KPI_MARKER_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:Retention|Immutability|Verification|Accountability|Adoption|Unit-Economics|"
    r"Economics|Governance|Configuration|Management|Architecture|Compliance|Resilience|"
    r"Optimization|Monitoring|Automation|Operations|Lifecycle|Security|Hardening|"
    r"Provisioning|Integration|Orchestration|Observability|Telemetry|Continuity|"
    r"Recovery|Replication|Tiering|Licensing|Capacity|Performance|Availability|"
    r"Forensic|Audit\s+Trail|Baseline|Drift|Benchmarking|Chargeback|Showback|"
    r"Coverage|Across|Critical|Infrastructure|Resistant|Phishing|Multi-Factor|"
    r"Authentication|Privileged|Access|Endpoint|Detection|Response|Vulnerability|"
    r"Patching|Segmentation|Encryption|Key\s+Management|Backup|Disaster|Testing|"
    r"Incident|Service\s+Desk|Change\s+Control|Problem\s+Management|Release|"
    r"Deployment|Pipeline|Container|Kubernetes|Virtualization|Hypervisor|Storage|"
    r"Network|Firewall|Routing|Switching|Wireless|Bandwidth|Latency|Throughput|"
    r"Redundancy|Failover|Load\s+Balancing|Power|Cooling|Thermal|Environmental|"
    r"Physical\s+Access|Surveillance|Cabling|Rack|UPS|Generator|Substation|"
    r"Enclosure|Benchmark|Alignment|Target|Strategic|Cultural|FinOps|Experience|"
    r"Workspace|Workplace|Collaboration|Productivity|Directory|Identity|Federation|"
    r"Site\s+Reliability|Reliability|Engineering|SRE|Maturity|Budget|Budgets|Toil|"
    r"Backlog|Burndown|Aging|Queue|Ticket|Single\s+Sign-On|Zero\s+Trust|Microsegmentation|Bastion|Vault|Rotation)\b",
    re.IGNORECASE,
)

_CAMELCASE_ARTIFACT_RE: Final[re.Pattern[str]] = re.compile(
    r"\b([a-z])([A-Z]{2,}[a-z0-9]*|[A-Z][a-z0-9]+)(-[A-Z][a-z0-9]+)?\b"
)

_UNRESOLVED_BRACKET_PLACEHOLDER_RE: Final[re.Pattern[str]] = re.compile(
    r"\[\s*(?:INSERT\s+)?(?:Pillar\s*Name|KPI\s*Name|Capability\s*Name|Domain\s*Name|Tower\s*Name|"
    r"Metric\s*Name|Sub-?capability|Dimension|Pilar|Capacidad|Dominio|English\s*KPI\s*Name|"
    r"Control\s*Name|Framework\s*Reference|[^\]]{1,45}?\s*(?:Name|Topic|Field))(?:\s+Here)?\s*\]",
    re.IGNORECASE,
)

_GENERIC_BOILERPLATE_IMPACT_RE: Final[re.Pattern[str]] = re.compile(
    r"Exposici[oó]n\s+operativa\s+y\s+riesgo\s+de\s+interrupci[oó]n\s+del\s+servicio\s+ante\s+incidencias\s+no\s+contenidas\s+en\s+la\s+arquitectura\s+operativa\s+del\s+dominio\.?",
    re.IGNORECASE,
)

_ORPHAN_AMPERSAND_ENGLISH_TAIL_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:\)\s*)?(?:&|\band\b)\s+[A-Z][A-Za-z0-9/\-\s]+(?=[.,;:]|$)"
)

_DANGLING_PREPOSITION_AMPERSAND_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(en|de|por|para|con|ante|sobre|hacia|según)\s*(?:\)\s*)?(?:&|\band\b)\s*[A-Za-z0-9/\-\s]*",
    re.IGNORECASE,
)


def _repair_broken_template_grammar(text: str, locale: str, fallback_label: str = "") -> str:
    """Repairs broken template syntax, dangling prepositions, and orphan English KPI tails."""
    if not text or not isinstance(text, str):
        return text
    if str(locale).lower().startswith("en"):
        return text

    fb = fallback_label or t(
        "domain_control_standard_fallback",
        locale=locale,
    )

    cleaned = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fb, text)
    cleaned = _DANGLING_PREPOSITION_AMPERSAND_RE.sub(rf"\1 {fb}", cleaned)
    cleaned = _ORPHAN_AMPERSAND_ENGLISH_TAIL_RE.sub("", cleaned)

    # Fix double prepositions caused by empty placeholder interpolation (e.g., 'condicionada por en la mayoría')
    cleaned = re.sub(
        r"\b(condicionad[oa]s?\s+por|debido\s+a|causad[oa]s?\s+por|derivad[oa]s?\s+de|asociad[oa]s?\s+a)\s+(en\s+|por\s+|con\s+|ante\s+)",
        r"\1 deficiencias operativas \2",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\b(incidencias\s+no\s+contenidas\s+en)\s*(?:[.,;:]|$)",
        rf"\1 {fb}.",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Remove unmatched closing parentheses left by half-stripped bilingual KPI labels
    if cleaned.count(")") > cleaned.count("("):
        cleaned = re.sub(r"([^\(]*)\)", r"\1", cleaned, count=cleaned.count(")") - cleaned.count("("))

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned

_RAW_ENGLISH_COMPOUND_KPI_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:[A-Z][a-z0-9/+\-]+(?:\s+(?:&|and|or|of|for|in|to|vs\.?|with|by)\s+|\s+)){2,}"
    r"(?:Rate|Governance|Management|Compliance|Architecture|Resilience|Optimization|"
    r"Monitoring|Automation|Operations|Lifecycle|Security|Hardening|Provisioning|"
    r"Integration|Orchestration|Observability|Telemetry|Continuity|Recovery|"
    r"Replication|Tiering|Licensing|Capacity|Performance|Availability|Trail|"
    r"Baseline|Drift|Benchmarking|Chargeback|Showback|Coverage|Authentication|"
    r"Access|Detection|Response|Patching|Segmentation|Encryption|Backup|Testing|"
    r"Control|Pipeline|Virtualization|Storage|Network|Routing|Switching|Redundancy|"
    r"Failover|Balancing|Cooling|Surveillance|Cabling|Alignment|Adoption|Economics|"
    r"Immutability|Verification|Accountability|Score|Index|Ratio|Threshold|SLA|SLO|MTTR|MTTF)\b"
)


def _deduplicate_prose_sentences(raw_txt: str) -> str:
    """Eliminate consecutive or repeated sentences within a paragraph or narrative block."""
    if not raw_txt or len(raw_txt) < 40:
        return raw_txt
    if "\n" in raw_txt and any(p in raw_txt for p in ("1. ", "2. ", "3. ", "4. ")):
        return raw_txt
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", raw_txt) if p.strip()]
    if len(parts) <= 1:
        return raw_txt
    seen: set[str] = set()
    unique_parts: list[str] = []
    for p in parts:
        norm_p = re.sub(r"\s+", " ", p.lower()).strip(" .;:,-")
        if len(norm_p) > 20 and norm_p in seen:
            continue
        if len(norm_p) > 20:
            seen.add(norm_p)
        unique_parts.append(p)
    return " ".join(unique_parts) if unique_parts else raw_txt

_LOCALIZED_KPI_CLAUSE_RE: Final[re.Pattern[str]] = re.compile(
    r"(\b(?:incidencias\s+no\s+contenidas\s+en|deficiencias(?:\s+\w+){0,3}\s+en|"
    r"brechas(?:\s+\w+){0,3}\s+en|vulnerabilidades(?:\s+\w+){0,3}\s+en|"
    r"riesgo(?:s)?(?:\s+\w+){0,4}\s+en|exposición(?:\s+\w+){0,4}\s+en|"
    r"fallos(?:\s+\w+){0,3}\s+en|control(?:es)?\s+de|ámbito\s+de|dominio\s+de|"
    r"factores\s+clave\s+como|aspectos\s+críticos\s+como|métricas\s+como|"
    r"capacidades\s+de|estándares\s+de|procesos\s+de|arquitectura\s+de|"
    r"evaluando\s+dimensiones\s+como|analizando\s+críticamente\s+factores\s+clave\s+como)\s+)"
    r"([A-Za-z][A-Za-z0-9\s,&/\-()]{6,}?)"
    r"(?=[.;:)\n]|$)"
)


def _sanitize_localized_kpi_leaks(
    text: str,
    locale: str,
    fallback_pillar: str = "",
) -> str:
    """Eliminates untranslated English KPI/capability template leaks inside localized sentences."""
    if not text or not isinstance(text, str):
        return text
    norm_loc = str(locale or "en").strip().lower()
    if norm_loc.startswith("en"):
        return text

    resolver = None
    try:
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()
    except Exception:
        resolver = None

    resolved_fallback = str(fallback_pillar or "").strip()
    if resolved_fallback and resolver is not None:
        resolved_fallback = resolver.resolve_pillar_by_any_reference(
            resolved_fallback, default=resolved_fallback, locale=locale
        )
    if resolved_fallback and (
        " & " in resolved_fallback or _ENGLISH_KPI_MARKER_RE.search(resolved_fallback)
    ):
        resolved_fallback = ""

    default_domain_fallback = (
        resolved_fallback
        if resolved_fallback
        else t(
            "generic_operational_domain_fallback",
            locale=locale,
            default="la arquitectura operativa del dominio" if norm_loc.startswith("es") else "the operational domain architecture",
        )
    )

    if _UNRESOLVED_BRACKET_PLACEHOLDER_RE.search(text):
        text = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(default_domain_fallback, text)

    def _replace_clause(match: re.Match[str]) -> str:
        prefix = match.group(1)
        candidate_kpi = match.group(2).strip()
        if " & " not in candidate_kpi and not _ENGLISH_KPI_MARKER_RE.search(candidate_kpi):
            return match.group(0)

        if resolver is not None:
            resolved = resolver.resolve_pillar_by_any_reference(
                candidate_kpi, default="", locale=locale
            )
            if (
                resolved
                and resolved != candidate_kpi
                and " & " not in resolved
                and not _ENGLISH_KPI_MARKER_RE.search(resolved)
            ):
                return f"{prefix}{resolved}"

        if resolved_fallback:
            return f"{prefix}{resolved_fallback}"

        substituted = apply_vocabulary_substitutions(candidate_kpi, locale=locale)
        if substituted != candidate_kpi and not _ENGLISH_KPI_MARKER_RE.search(substituted):
            return f"{prefix}{substituted}"

        default_domain_lbl = t("default_capability_domain_label", locale=locale)
        return f"{prefix}{default_domain_lbl}"

    sanitized = _LOCALIZED_KPI_CLAUSE_RE.sub(_replace_clause, text)
    return apply_vocabulary_substitutions(sanitized, locale=locale)


def resolve_domain_semantics_key(tower_id: str, available_keys: set[str]) -> str:
    """Resolves a tower identifier to its localization semantics key without rigid T1..T10 truncation."""
    raw_id = str(tower_id or "").strip().upper()
    if not raw_id:
        return "DEFAULT"

    if raw_id in available_keys:
        return raw_id

    canonical_match = re.match(r"^(?:T|TOWER[-_\s]*)(\d+)$", raw_id)
    if canonical_match:
        candidate = f"T{int(canonical_match.group(1))}"
        if candidate in available_keys:
            return candidate

    return "DEFAULT"


class ExecutiveNarrativeSynthesizer:
    """Compiles the authoritative Executive Summary for any capability tower (T1-T10).
    Strictly adheres to 100% Technical English Codebase and Zero Hardcoding standards.
    """

    UNRESOLVED_TOKEN_PATTERN = re.compile(r"\{[a-zA-Z0-9_]+\}")

    def __init__(self, locale_code: str) -> None:
        self._locale_code = locale_code

    def synthesize_chapter_one_paragraphs(
        self,
        client_name: str,
        tower_name: str,
        maturity_score: str,
        maturity_tier_label: str,
        primary_workloads_summary: str,
        findings_briefs: List[str],
        hourly_burn_rate_fmt: str,
        net_downtime_hours_fmt: str,
        annual_loss_expectancy_fmt: str,
        p90_downtime_hours_fmt: str,
        p90_var_exposure_fmt: str,
        remediation_horizon_label: str,
        primary_remediation_pillar: str,
        target_maturity_score: str,
        capped_p90_hours_fmt: str = "",
        tower_id: str = "T1",
        strongest_dim_name: str = "",
        strongest_dim_score: str = "",
        weakest_dim_name: str = "",
        weakest_dim_score: str = "",
        archetype: str = "",
        operational_mission: str = "",
        dilemma_anchor: str = "",
        posture_modernization_focus: str = "",
    ) -> List[str]:
        """Synthesizes the executive summary paragraphs for a capability tower."""
        f1 = findings_briefs[0] if len(findings_briefs) > 0 else t("default_critical_vulnerability", locale=self._locale_code)
        f2 = findings_briefs[1] if len(findings_briefs) > 1 else ""
        f3 = findings_briefs[2] if len(findings_briefs) > 2 else ""

        # Clean trailing periods and whitespace for smooth multi-clause synthesis
        f1 = f1.strip().rstrip(".")
        f2 = f2.strip().rstrip(".")
        f3 = f3.strip().rstrip(".")

        capped_hours_val = capped_p90_hours_fmt.strip() or p90_downtime_hours_fmt.strip()

        # Load narrative templates via cached infrastructure catalog (Zero inline disk I/O)
        loc_data = load_locales_catalog()
        loc_branch = loc_data.get(self._locale_code, {})
        tower_semantics_map = loc_branch.get("tower_domain_semantics", {})

        canonical_key = resolve_domain_semantics_key(
            tower_id=str(tower_id),
            available_keys=set(tower_semantics_map.keys()),
        )
        tower_semantics = tower_semantics_map.get(
            canonical_key, tower_semantics_map.get("DEFAULT", {})
        )

        # Dynamically prioritize explicitly provided or payload-injected domain semantics
        resolved_mission = operational_mission.strip() if operational_mission else tower_semantics.get("operational_mission", "")
        resolved_anchor = dilemma_anchor.strip() if dilemma_anchor else tower_semantics.get("dilemma_anchor", "")
        resolved_focus = posture_modernization_focus.strip() if posture_modernization_focus else tower_semantics.get("posture_modernization_focus", "")

        context = {
            "client_name": client_name.strip(),
            "tower_name": tower_name.strip(),
            "operational_mission": resolved_mission,
            "dilemma_anchor": resolved_anchor,
            "posture_modernization_focus": resolved_focus,
            "maturity_score": maturity_score.strip(),
            "maturity_tier_label": maturity_tier_label.strip(),
            "critical_findings_count": str(max(len(findings_briefs), 1)),
            "primary_workloads_summary": primary_workloads_summary.strip(),
            "finding_1_executive_brief": f1,
            "finding_2_executive_brief": f2,
            "finding_3_executive_brief": f3,
            "hourly_burn_rate_fmt": hourly_burn_rate_fmt.strip(),
            "net_downtime_hours_fmt": net_downtime_hours_fmt.strip(),
            "annual_loss_expectancy_fmt": annual_loss_expectancy_fmt.strip(),
            "p90_downtime_hours_fmt": p90_downtime_hours_fmt.strip(),
            "capped_p90_hours_fmt": capped_hours_val,
            "p90_var_exposure_fmt": p90_var_exposure_fmt.strip(),
            "remediation_horizon_label": remediation_horizon_label.strip(),
            "primary_remediation_pillar": primary_remediation_pillar.strip(),
            "target_maturity_score": target_maturity_score.strip(),
            "strongest_dim_name": strongest_dim_name.strip(),
            "strongest_dim_score": strongest_dim_score.strip(),
            "weakest_dim_name": weakest_dim_name.strip(),
            "weakest_dim_score": weakest_dim_score.strip(),
        }

        narrative_section = loc_data.get("executive_summary_narrative", {}).get(self._locale_code, {})

        # Polymorphic Archetype Resolution: Prioritize explicit payload archetype over hardcoded T1..T10 map
        archetypes_branch = loc_data.get("executive_summary_narrative", {}).get("archetypes", {})
        clean_archetype = archetype.strip().upper() if archetype else ""
        if clean_archetype and clean_archetype in archetypes_branch:
            archetype_key = clean_archetype
        else:
            archetype_key = resolve_domain_archetype(domain_id=canonical_key, blueprint_data=loc_data)

        arch_templates = archetypes_branch.get(archetype_key, {}).get(self._locale_code, {})
        en_narrative = loc_data.get("executive_summary_narrative", {}).get("en", {})
        en_arch_templates = archetypes_branch.get(archetype_key, {}).get("en", {})

        p1_tmpl = (
            arch_templates.get("p1_operational_posture")
            or narrative_section.get("p1_operational_posture")
            or en_arch_templates.get("p1_operational_posture")
            or en_narrative.get("p1_operational_posture")
        )
        loc_lead_in = t("findings_lead_in", locale=self._locale_code)
        if loc_lead_in == "findings_lead_in":
            loc_lead_in = ""

        findings_lead_in = (
            arch_templates.get("findings_lead_in")
            or narrative_section.get("findings_lead_in")
            or loc_lead_in
            or en_arch_templates.get("findings_lead_in")
            or en_narrative.get("findings_lead_in")
        )
        p3_tmpl = (
            arch_templates.get("p3_financial_exposure")
            or narrative_section.get("p3_financial_exposure")
            or en_arch_templates.get("p3_financial_exposure")
            or en_narrative.get("p3_financial_exposure")
        )
        p4_tmpl = (
            arch_templates.get("p4_modernization_mandate")
            or narrative_section.get("p4_modernization_mandate")
            or en_arch_templates.get("p4_modernization_mandate")
            or en_narrative.get("p4_modernization_mandate")
        )

        paragraphs = []
        raw_templates = [
            (p1_tmpl, "p1_operational_posture"),
            (findings_lead_in, "findings_lead_in"),
            (p3_tmpl, "p3_financial_exposure"),
            (p4_tmpl, "p4_modernization_mandate"),
        ]
        from collections import defaultdict

        for tmpl, key in raw_templates:
            if tmpl:
                try:
                    safe_context = defaultdict(str, context)
                    rendered = tmpl.format_map(safe_context)
                except Exception as ex:
                    logger.warning("Formatting failed for template '%s': %s", key, ex)
                    rendered = tmpl
                unresolved = self.UNRESOLVED_TOKEN_PATTERN.findall(rendered)
                if unresolved:
                    raise ValueError(f"Unresolved tokens {unresolved} in paragraph '{key}'")
                paragraphs.append(rendered)
            else:
                fallback_p = t(key, locale=self._locale_code, **context)
                if fallback_p == key and key in en_narrative:
                    try:
                        fallback_p = en_narrative[key].format(**context)
                    except (KeyError, ValueError, IndexError) as exc:
                        logger.warning(
                            "Missing format key %s in en_narrative fallback for %s",
                            exc,
                            key,
                        )
                        fallback_p = en_narrative[key]
                paragraphs.append(fallback_p)

        return paragraphs


def resolve_domain_introduction(
    blueprint_data: Dict[str, Any],
    annex_data: Optional[Dict[str, Any]],
    tower_id: str,
    client_name: str,
    meta_lang: str,
) -> Dict[str, Any]:
    """Resolves rich domain objective, platform introduction, and included components

    using a robust 4-tier fallback hierarchy (zero blank sections or error fallbacks).
    """
    import json

    from assessment_engine.infrastructure.runtime_paths import ROOT

    # Tier 1: Explicit annex override
    annex_intro = (annex_data or {}).get("domain_introduction")
    if isinstance(annex_intro, dict) and annex_intro.get("domain_objective"):
        return annex_intro

    bp_intro = blueprint_data.get("domain_introduction")
    if isinstance(bp_intro, dict) and bp_intro.get("domain_objective"):
        return bp_intro

    # Tier 3: Root-level synthesis keys in blueprint
    root_obj = str(
        blueprint_data.get("domain_objective")
        or blueprint_data.get("scope_and_objectives")
        or blueprint_data.get("objective")
        or ""
    ).strip()
    root_intro = str(
        blueprint_data.get("introduction_paragraph")
        or blueprint_data.get("platform_description")
        or blueprint_data.get("description")
        or ""
    ).strip()
    root_comps = (
        blueprint_data.get("included_components")
        or blueprint_data.get("scope_components")
        or blueprint_data.get("components")
        or []
    )

    if root_obj and root_intro:
        return {
            "domain_objective": root_obj,
            "introduction_paragraph": root_intro,
            "included_components": list(root_comps),
        }

    # Tier 4: Deterministic Dynamic Synthesis from Tower Catalog & Active Pillars
    tower_cat_file = ROOT / "engine_config" / "towers" / "tower_catalog.json"
    tower_cat: Dict[str, Any] = {}
    if tower_cat_file.exists():
        try:
            tower_cat = json.loads(tower_cat_file.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            tower_cat = {}

    t_spec = tower_cat.get(tower_id.upper(), {})
    tower_name = str(
        blueprint_data.get("tower_name")
        or t_spec.get("name")
        or tower_id
    ).strip()

    from assessment_engine.infrastructure.localization import t

    comps: List[str] = list(root_comps)
    if not comps:
        for pil in blueprint_data.get("pillars_analysis", []):
            if isinstance(pil, dict):
                p_name = str(pil.get("pillar_name") or pil.get("name") or "").strip()
                if p_name:
                    comps.append(t("default_component_item_template", locale=meta_lang, pillar_name=p_name))

    verified_entities = blueprint_data.get("verified_entities", [])
    extracted_names: list[str] = []
    if isinstance(verified_entities, Sequence) and not isinstance(verified_entities, (str, bytes)):
        for e in verified_entities[:4]:
            if isinstance(e, Mapping):
                name = (
                    e.get("canonical_entity")
                    or e.get("name")
                    or e.get("entity")
                    or e.get("original_token")
                    or ""
                )
                if name:
                    extracted_names.append(str(name).strip())
            elif isinstance(e, str) and e.strip():
                extracted_names.append(e.strip())
    entities_str = ", ".join(extracted_names)

    if not root_obj:
        obj_text = t(
            "default_domain_objective_template",
            locale=meta_lang,
            tower_name=tower_name,
            client_name=client_name,
        )
    else:
        obj_text = root_obj

    if not root_intro:
        entities_clause = (
            t("default_platform_intro_entities_clause", locale=meta_lang, entities=entities_str)
            if entities_str
            else ""
        )
        intro_text = t(
            "default_platform_intro_template",
            locale=meta_lang,
            client_name=client_name,
            entities_clause=entities_clause,
        )
    else:
        intro_text = root_intro

    return {
        "domain_objective": obj_text,
        "introduction_paragraph": intro_text,
        "included_components": comps,
    }


class PayloadToASTBridge:
    """Translates structured JSON payloads and associated markdown modules into a unified Document Abstract Syntax Tree (AST).
    This process maintains semantic identity and structural alignment with the source content."""

    def __init__(
        self,
        brand_profile_path: str = "engine_config/brand_profile.json",
        locales_path: str = "engine_config/locales.json",
    ):
        self.brand_profile_path = Path(brand_profile_path)
        self.locales_path = Path(locales_path)
        self.meta_lang = "en"

        # Load brand profiles, using fallback values to ensure required assets are present.
        self.company_name = ""
        self.classification = "Confidential"
        self.disclaimer = ""
        self.primary_color_rgb = [0, 114, 188]  # Primary corporate brand color code.
        self.alt_row_hex = "F2F2F2"

        self.brand_data = {}
        from assessment_engine.infrastructure.config_loader import load_brand_profile

        if self.locales_path.exists():
            with open(self.locales_path, "r", encoding="utf-8") as f:
                self.loc_data = json.load(f)
        else:
            self.loc_data = {}

        try:
            brand = load_brand_profile(brand_profile_path=self.brand_profile_path)
            self.brand_data = brand
            self.company_name = brand.get("company_name", self.company_name)
            self.classification = brand.get(
                "default_classification", self.classification
            )
            self.disclaimer = brand.get("disclaimer_text", self.disclaimer)
            styling = brand.get("styling", {})
            p_hex = styling.get("primary_color_hex", "0072BC")
            self.alt_row_hex = styling.get("alternate_row_color_hex", self.alt_row_hex)

            #
            r = int(p_hex[0:2], 16)
            g = int(p_hex[2:4], 16)
            b = int(p_hex[4:6], 16)
            self.primary_color_rgb = [r, g, b]
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.warning(f"[AST Bridge Warning] Error resolving primary brand color: {ex}")

    @property
    def primary_color_hex(self) -> str:
        """Returns the primary corporate brand color in 6-character hex format."""
        if len(self.primary_color_rgb) == 3:
            return f"{self.primary_color_rgb[0]:02X}{self.primary_color_rgb[1]:02X}{self.primary_color_rgb[2]:02X}"
        return "0072BC"


    def convert(
        self,
        blueprint_payload_path: str,
        approved_annex_path: str = "",
        override_locale: str | None = None,
        modules_dir: str | Path | None = None,
    ) -> DocumentAST:
        """Consolidates information from input JSON files and associated Markdown/CSV modules
        to generate a complete Document Abstract Syntax Tree (AST)."""
        ctx = self._extract_conversion_context(
            blueprint_payload_path,
            approved_annex_path,
            override_locale=override_locale,
            modules_dir=modules_dir,
        )
        self.meta_lang = ctx.get("meta_lang", "en")
        self.loc_data = {}
        if self.locales_path.exists():
            try:
                self.loc_data = json.loads(self.locales_path.read_text(encoding="utf-8"))
            except Exception:
                self.loc_data = {}
        self.loc_branch = self.loc_data.get(self.meta_lang, {})

        # Enforce universal Unicode Normalization Form C (NFC) across incoming payload context
        import unicodedata

        def _canonicalize_nfc(data: Any) -> Any:
            if isinstance(data, str):
                return unicodedata.normalize("NFC", data)
            if isinstance(data, dict):
                return {k: _canonicalize_nfc(v) for k, v in data.items()}
            if isinstance(data, list):
                return [_canonicalize_nfc(item) for item in data]
            return data

        if "blueprint_data" in ctx and isinstance(ctx["blueprint_data"], dict):
            ctx["blueprint_data"] = _canonicalize_nfc(ctx["blueprint_data"])
        if "annex_data" in ctx and isinstance(ctx["annex_data"], dict):
            ctx["annex_data"] = _canonicalize_nfc(ctx["annex_data"])

        # Authoritative calibration of financial telemetry across all deliverable chapters (Fail-Fast Law 1)
        calibrator = ActuarialDowntimeCalibrator()
        metrics = calibrator.calibrate(ctx["blueprint_data"])
        fin_telemetry = ctx["blueprint_data"].setdefault("financial_telemetry", {})
        fin_telemetry.update({
            "global_annual_revenue": float(metrics.global_annual_revenue),
            "perimeter_revenue_weight_pct": float(metrics.perimeter_revenue_weight_pct),
            "effective_exposed_revenue": float(metrics.effective_exposed_revenue),
            "sector_benchmark_source": metrics.sector_benchmark_source,
            "hourly_revenue_exposure_factor": float(metrics.hourly_revenue_exposure_factor),
            "authoritative_hourly_downtime_cost": float(metrics.calibrated_hourly_downtime_cost),
        })
        ctx["financial_telemetry"] = fin_telemetry
        ctx["annual_revenue"] = float(metrics.global_annual_revenue)
        ctx["hourly_downtime_cost"] = float(metrics.calibrated_hourly_downtime_cost)
        ctx["authoritative_hourly_downtime_cost"] = float(metrics.calibrated_hourly_downtime_cost)

        nodes: List[Any] = []
        self._build_cover_and_toc(ctx, nodes)
        self._build_executive_summary_and_scope(ctx, nodes)
        self._build_systemic_risk_section(ctx, nodes)
        risks_data_list, fair_lookup = self._build_maturity_and_benchmarks(ctx, nodes)
        self._build_fair_risk_analysis(ctx, nodes, risks_data_list)
        self._build_detailed_findings_log(ctx, nodes, risks_data_list, fair_lookup)
        self._build_conclusions_and_appendices(ctx, nodes, risks_data_list)

        return DocumentAST(
            title=f"Technical Annex - Tower {ctx['tower_id']}",
            metadata=ctx["tower_meta"],
            nodes=nodes,
        )

    def _extract_conversion_context(
        self,
        blueprint_payload_path: str,
        approved_annex_path: str,
        override_locale: str | None = None,
        modules_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Extract and prepare all context variables needed for DocumentAST compilation."""
        blueprint_file = Path(blueprint_payload_path)
        annex_file = Path(approved_annex_path) if approved_annex_path else Path("non_existent_annex.json")
        case_dir = blueprint_file.parent
        resolved_modules_dir = Path(modules_dir) if modules_dir else (case_dir / "asis_modules")
        modules_dir = resolved_modules_dir

        #
        with open(blueprint_file, "r", encoding="utf-8-sig") as f:
            blueprint_data = json.load(f)

        client_intel_file = case_dir.parent / "client_intelligence.json"
        intel_data = {}
        if client_intel_file.exists():
            try:
                with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                    intel_data = json.load(cif)
            except Exception as e:
                logger.info(f"⚠️ Error loading client_intelligence in AST Bridge: {e}")

        annex_data: dict[str, Any] = {}
        if approved_annex_path and annex_file.exists():
            try:
                with open(annex_file, "r", encoding="utf-8-sig") as f:
                    annex_data = json.load(f)
            except (OSError, ValueError, KeyError, AttributeError) as ex:
                logger.warning(f"[AST Bridge Warning] Error reading annex_file: {ex}")

        tower_meta = blueprint_data.get("document_meta", {})
        meta_lang = str(override_locale or tower_meta.get("language") or "en").strip().lower()
        from assessment_engine.infrastructure.config_loader import (
            resolve_localized_vocabulary,
        )

        vocab = resolve_localized_vocabulary(meta_lang)

        # Resolve localized brand attributes from canonical vocabulary
        self.classification = vocab.get(
            "default_classification", self.classification
        )
        self.disclaimer = vocab.get("disclaimer_text", self.disclaimer)

        tower_id = str(tower_meta.get("tower_code") or tower_meta.get("tower_id") or "TXX")
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()
        raw_tname = str(tower_meta.get("tower_name") or "").strip()
        if raw_tname and raw_tname != "Unknown":
            tower_name = raw_tname
        else:
            tower_name = resolver.resolve_tower_name(tower_id, default="Unknown", locale=meta_lang)
        client_name = clean_client_name(str(tower_meta.get("client_name") or ""), locale=meta_lang)
        version = tower_meta.get("version", "1.0")
        date_str = format_date_localized(
            tower_meta.get("date"), locale=meta_lang
        )
        currency = (
            tower_meta.get("currency")
            or blueprint_data.get("currency")
            or self.brand_data.get("currency_symbol")
            or vocab.get("default_currency")
            or t("default_currency", locale=meta_lang)
        )
        if not currency or currency == "default_currency":
            currency = "EUR"

        # Dynamically detect organizational scale to apply customized calibration.
        is_critical = self.brand_data.get("styling", {}).get("is_critical", None)
        if is_critical is None:
            is_critical = False # default fallback

        # Derive live authoritative FAIR risks to guarantee 100% mathematical monism across all sections
        from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
            derive_in_memory_fair_risks,
        )
        pre_risks, _ = derive_in_memory_fair_risks(blueprint_data, doc_lang=meta_lang, currency=currency)
        live_annex_ale = sum(
            float(r.get("ale") or 0.0)
            for r in pre_risks
            if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        )
        if live_annex_ale > 0.0:
            total_fair_ale = live_annex_ale
            blueprint_data["total_fair_ale"] = live_annex_ale
            blueprint_data["annualized_loss_expectancy"] = live_annex_ale
        else:
            total_fair_ale = blueprint_data.get("total_fair_ale", 0.0)

        # Respect authoritative survey score from blueprint SSOT (eliminating split-brain with Tomo 1)
        authoritative_raw = (
            blueprint_data.get("overall_score")
            or blueprint_data.get("score")
            or blueprint_data.get("exact_score")
            or blueprint_data.get("maturity_score")
        )
        exact_score = safe_float(authoritative_raw, locale=meta_lang, allow_zero=True)
        if exact_score is None:
            from assessment_engine.application.services.tower_payload_hydrator import (
                TowerPayloadHydrator,
            )

            try:
                exact_score = TowerPayloadHydrator.compute_canonical_score(
                    blueprint_data, doc_lang=meta_lang
                )
            except Exception:
                exact_score = 2.5

        blueprint_data["score"] = exact_score
        blueprint_data["overall_score"] = exact_score

        # Maintain original pillar survey scores without artificial down-clamping
        pa = blueprint_data.get("pillars_analysis") or []
        for p in pa:
            if isinstance(p, dict):
                p_score = safe_float(p.get("score"), locale=meta_lang, allow_zero=True)
                if p_score is None:
                    p_score = 2.5
                p["score"] = p_score
                p["exact_score"] = p_score

        gs_val = float(exact_score)
        global_score = f"{gs_val:.2f}"

        from assessment_engine.domain.maturity_band import (
            ANNEX_MATURITY_BANDS,
            resolve_maturity_band,
        )
        band_info = resolve_maturity_band(gs_val, ANNEX_MATURITY_BANDS, locale=meta_lang)
        _cmmi_es_map = {
            "Initial": "Inicial",
            "Repeatable": "Repetible",
            "Defined": "Definido",
            "Managed": "Gestionado",
            "Optimized": "Optimizado",
            "band_initial": "Inicial",
            "band_repeatable": "Repetible",
            "band_defined": "Definido",
            "band_managed": "Gestionado",
            "band_optimized": "Optimizado",
        }
        band_key = band_info.get("band_key", "band_defined")
        raw_label = band_info.get("label", "Definido")
        localized_band_label = t(band_key, locale=meta_lang)
        level_prefix = t("level_prefix", locale=meta_lang)
        band_key_level_map = {
            "band_initial": 1,
            "band_repeatable": 2,
            "band_defined": 3,
            "band_managed": 4,
            "band_optimized": 5,
        }
        band_level = band_key_level_map.get(band_key, 2)
        global_band = f"{level_prefix} {band_level} ({localized_band_label})"

        pillars_list = blueprint_data.get("pillar_score_profile", {}).get("pillars") or [{}]
        global_reading = (
            pillars_list[0].get("executive_reading")
            or t("resilience_reading_standard", locale=meta_lang)
        )

        formatted_global_score = format_number(gs_val, locale=meta_lang, decimals=2)
        max_score_formatted = format_number(5.0, locale=meta_lang, decimals=2)
        display_score_str = f"{formatted_global_score} / {max_score_formatted}"
        rate_mult = float(blueprint_data.get("rate_multiplier") or blueprint_data.get("rate_mult") or 1.0)

        return {
            "blueprint_file": blueprint_file,
            "annex_file": annex_file,
            "case_dir": case_dir,
            "modules_dir": modules_dir,
            "annex_data": annex_data,
            "blueprint_data": blueprint_data,
            "intel_data": intel_data,
            "tower_meta": tower_meta,
            "meta_lang": meta_lang,
            "vocab": vocab,
            "tower_name": tower_name,
            "tower_id": tower_id,
            "client_name": client_name,
            "company_name": self.company_name,
            "version": version,
            "date_str": date_str,
            "currency": currency,
            "is_critical": is_critical,
            "total_fair_ale": total_fair_ale,
            "rate_mult": rate_mult,
            "exact_score": exact_score,
            "exact_band": global_band,
            "global_score": global_score,
            "global_band": global_band,
            "global_reading": global_reading,
            "gs_val": gs_val,
            "formatted_global_score": formatted_global_score,
            "display_score_str": display_score_str,
        }

    def _build_cover_and_toc(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        vocab = ctx["vocab"]
        tower_name = ctx["tower_name"]
        client_name = ctx["client_name"]
        date_str = ctx["date_str"]
        version = ctx["version"]
        meta_lang = ctx["meta_lang"]
        blueprint_data = ctx.get("blueprint_data", {})

        # 1. Corporate Executive Cover Page
        nodes.append(SpacerNode(points=40))

        # 1. Main Document Title (36.0 pt, Bold, #2E404D)
        title_text = vocab.get("title", "Current State Assessment Report (AS-IS)")
        nodes.append(
            ParagraphNode(
                text=title_text,
                bold=True,
                font_size=36.0,
                text_color_rgb=[46, 64, 77],
                space_after=8,
            )
        )

        # 2. Technical Annex Subtitle (Heading level 1, #0072BC)
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()
        tower_code = blueprint_data.get("document_meta", {}).get("tower_code", "T1")
        if tower_name and tower_name != "Unknown":
            localized_tower_name = tower_name
        else:
            localized_tower_name = resolver.resolve_tower_name(tower_code, default="Unknown", locale=meta_lang)

        annex_prefix = t("annex_technical_prefix", locale=meta_lang)
        nodes.append(
            ParagraphNode(
                text=f"{annex_prefix} {localized_tower_name}",
                bold=True,
                font_size=16.0,
                text_color_rgb=self.primary_color_rgb,
                style="cover_subtitle",
                space_after=24,
            )
        )

        nodes.append(SpacerNode(points=30))

        # 3. Client Identity (28.0 pt, Bold, Client Label in #2E404D, Name in primary brand color)
        client_lbl = t("client_lbl", locale=meta_lang)
        nodes.append(
            ParagraphNode(
                text=f"**{client_lbl.strip()}** {client_name.upper()}",
                bold=True,
                font_size=28.0,
                text_color_rgb=self.primary_color_rgb,
                space_after=24,
            )
        )

        # Store corporate metadata strictly for native first-page footer rendering
        classification_clean = self.classification.replace(" (Tier-1 Assessment)", "")
        version_lbl = t("version_label", locale=meta_lang)
        company_name_upper = self.company_name.upper()
        footer_meta_str = f"{company_name_upper}  |  {date_str}  |  {version_lbl} {version}  |  {classification_clean}"
        ctx["tower_meta"]["cover_footer_metadata"] = footer_meta_str

        nodes.append(PageBreakNode())

        #
        # CHAPTER 2: INDEX / NATIVE TABLE OF CONTENTS
        #
        toc_entries = []
        page_prefix = t("toc_page_prefix", locale=meta_lang)
        for raw_entry in get_localized_list("static_toc_entries", locale=meta_lang):
            parts = raw_entry.split("\t")
            if len(parts) == 2:
                e_title = parts[0].strip()
                e_page = parts[1].strip()
                if e_page.isdigit() and page_prefix:
                    e_page = f"{page_prefix}{e_page}"
                lvl = 2 if e_title.startswith("• ") or e_title.startswith("- ") else 1
                toc_entries.append(TOCEntryNode(title=e_title, page=e_page, level=lvl))
        nodes.append(
            TOCNode(
                title=t("toc_title", locale=meta_lang),
                entries=toc_entries,
                depth=2,
            )
        )
        nodes.append(PageBreakNode())

    def _build_executive_summary_and_scope(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        modules_dir = ctx["modules_dir"]
        meta_lang = ctx["meta_lang"]
        loc_branch = self.loc_branch
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        global_band = ctx["global_band"]
        display_score_str = ctx["display_score_str"]
        global_reading = ctx["global_reading"]
        gs_val = ctx["gs_val"]
        annex_data = ctx.get("annex_data", {})
        tower_id = str(ctx.get("tower_id") or blueprint_data.get("tower_id") or "T1").upper()

        #
        # 3. CHAPTER 1: EXECUTIVE SUMMARY (RFC 030 4-TIER EXECUTIVE VISUAL ARCHITECTURE)
        #
        nodes.append(
            HeadingNode(
                text=t("chapter_1_exec_summary", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        exec_sum = (
            blueprint_data.get("executive_snapshot")
            or (annex_data.get("executive_summary") if annex_data else {})
            or {}
        )

        currency = str(
            ctx.get("currency")
            or blueprint_data.get("document_meta", {}).get("currency_code")
            or blueprint_data.get("currency")
            or "USD"
        )
        total_fair_ale = (
            _safe_float(blueprint_data.get("total_fair_ale"))
            or _safe_float(blueprint_data.get("annualized_loss_expectancy"))
            or _safe_float(blueprint_data.get("fair_risk_profile", {}).get("total_ale"))
            or _safe_float(blueprint_data.get("total_ale"))
            or 0.0
        )
        total_p90 = (
            _safe_float(blueprint_data.get("total_fair_p90"))
            or _safe_float(blueprint_data.get("fair_risk_profile", {}).get("p90_ale"))
            or _safe_float(blueprint_data.get("tail_risk_p90"))
            or 0.0
        )
        ale_formatted = format_number(total_fair_ale, locale=meta_lang, decimals=0)
        p90_formatted = format_number(total_p90, locale=meta_lang, decimals=0)
        per_year_suffix = t("per_year_suffix", locale=meta_lang)

        # COMPONENT A: EXECUTIVE KPI SNAPSHOT SCORECARD TABLE (3 COLUMNS)
        max_score_str = format_number(5.0, locale=meta_lang, decimals=1)
        score_display = (
            display_score_str
            if " / " in display_score_str
            else f"{display_score_str} / {max_score_str}"
        )
        band_bg = "FFF3CD" if gs_val < 3.4 else "E2F0D9"
        scorecard_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=t("kpi_score_header", locale=meta_lang), bold=True, is_header=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=t("kpi_band_header", locale=meta_lang), bold=True, is_header=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=t("kpi_exposure_header", locale=meta_lang), bold=True, is_header=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=score_display, bold=True, align="CENTER", bg_color=self.alt_row_hex),
                    CellNode(text=global_band, bold=True, align="CENTER", bg_color=band_bg),
                    CellNode(
                        text=f"{format_currency(total_fair_ale, currency_symbol=currency, locale=meta_lang, decimals=0)} {per_year_suffix}",
                        bold=True,
                        align="CENTER",
                        bg_color="FCE4D6",
                    ),
                ]
            ),
        ]
        nodes.append(TableNode(rows=scorecard_rows, col_widths=[0.33, 0.33, 0.34]))
        nodes.append(SpacerNode(points=14))

        # COMPONENT B: EXECUTIVE HEADLINE & FLUID MECE NARRATIVE (PROSE)
        headline = exec_sum.get("headline", "")
        if headline:
            nodes.append(ParagraphNode(text=f"**{headline}**", font_size=11.0, space_after=8))

        # Safe extraction of nested telemetry dictionaries
        # Safe extraction of nested telemetry dictionaries
        fin_telemetry = blueprint_data.get("financial_telemetry") or {}
        doc_meta = blueprint_data.get("document_meta") or {}

        # Resolve authoritative corporate hourly downtime cost rate dynamically via ActuarialDowntimeCalibrator
        req_keys = [
            "global_annual_revenue",
            "perimeter_revenue_weight_pct",
            "effective_exposed_revenue",
            "sector_benchmark_source",
            "hourly_revenue_exposure_factor",
            "authoritative_hourly_downtime_cost"
        ]
        if not all(k in fin_telemetry for k in req_keys):
            from assessment_engine.domain.actuarial.downtime_calibrator import (
                ActuarialDowntimeCalibrator,
            )
            calibrator = ActuarialDowntimeCalibrator()
            try:
                metrics = calibrator.calibrate(blueprint_data)
                fin_telemetry.update({
                    "global_annual_revenue": float(metrics.global_annual_revenue),
                    "perimeter_revenue_weight_pct": float(metrics.perimeter_revenue_weight_pct),
                    "effective_exposed_revenue": float(metrics.effective_exposed_revenue),
                    "sector_benchmark_source": metrics.sector_benchmark_source,
                    "hourly_revenue_exposure_factor": float(metrics.hourly_revenue_exposure_factor),
                    "authoritative_hourly_downtime_cost": float(metrics.calibrated_hourly_downtime_cost),
                })
            except Exception:
                _ = True  # Handled fallback

        hourly_rate = float(fin_telemetry.get("authoritative_hourly_downtime_cost") or 0.0)
        if hourly_rate <= 0.0:
            raw_candidates = [
                blueprint_data.get("hourly_downtime_rate"),
                blueprint_data.get("hourly_burn_rate"),
            ]
            for candidate in raw_candidates:
                if candidate is not None:
                    parsed = _safe_float(candidate, default=-1.0)
                    if parsed > 0.0:
                        hourly_rate = parsed
                        break

        if hourly_rate <= 0.0:
            raw_div = blueprint_data.get("annual_downtime_divisor")
            baseline_hours = _safe_float(raw_div, default=0.0)
            if baseline_hours > 0.0 and total_fair_ale > 0.0:
                hourly_rate = total_fair_ale / baseline_hours

        hourly_formatted = format_number(hourly_rate, locale=meta_lang, decimals=2)

        # Calculate equivalent operational friction and recovery hours dynamically
        ale_hours_val = (total_fair_ale / hourly_rate) if hourly_rate > 0.0 else 0.0
        p90_hours_val = (total_p90 / hourly_rate) if hourly_rate > 0.0 else 0.0
        ale_hours_str = format_number(ale_hours_val, locale=meta_lang, decimals=1)
        p90_hours_str = format_number(p90_hours_val, locale=meta_lang, decimals=1)

        tower_name = str(
            ctx.get("tower_name")
            or doc_meta.get("tower_name", "Infrastructure Domain")
        )

        # Count quantified risk scenarios dynamically from payload structures
        risks_list: list[Any] = (
            blueprint_data.get("risk_register")
            or blueprint_data.get("risks")
            or (blueprint_data.get("fair_risk_profile") or {}).get("scenarios")
            or []
        )
        if not risks_list:
            risks_list = [
                hc
                for p in blueprint_data.get("pillars_analysis", [])
                for hc in (p.get("health_check_asis") or [])
            ]
        
        total_findings = max(len(risks_list), 1)
        fallback_vuln = t("default_critical_vulnerability", locale=meta_lang)
        top_risk_title = (
            str(risks_list[0].get("risk_name") or risks_list[0].get("finding") or fallback_vuln)
            if risks_list
            else fallback_vuln
        )

        global_annual_revenue = fin_telemetry.get("global_annual_revenue")
        if global_annual_revenue is None:
            rev_raw = (
                blueprint_data.get("annual_revenue")
                or blueprint_data.get("document_meta", {}).get("annual_revenue")
            )
            global_annual_revenue = _safe_float(rev_raw, default=0.0) if rev_raw is not None else 0.0
            fin_telemetry["global_annual_revenue"] = global_annual_revenue

        perimeter_weight = fin_telemetry.get("perimeter_revenue_weight_pct")
        if perimeter_weight is None:
            perimeter_weight = 100.0
            fin_telemetry["perimeter_revenue_weight_pct"] = perimeter_weight

        effective_exposed = fin_telemetry.get("effective_exposed_revenue")
        if effective_exposed is None:
            effective_exposed = global_annual_revenue
            fin_telemetry["effective_exposed_revenue"] = effective_exposed

        sector_benchmark_source = fin_telemetry.get("sector_benchmark_source")
        if sector_benchmark_source is None:
            sector_benchmark_source = "Gartner / ITIC Global Downtime Benchmark"
            fin_telemetry["sector_benchmark_source"] = sector_benchmark_source
            
        sector_impact_factor = fin_telemetry.get("hourly_revenue_exposure_factor")
        if sector_impact_factor is None:
            sector_impact_factor = 0.40
            fin_telemetry["hourly_revenue_exposure_factor"] = sector_impact_factor
            
        total_capex = fin_telemetry.get("remediation_capex_estimate")
        if total_capex is None:
            total_capex = sum(float(r.get("mitigation_capex", 0)) for r in risks_list)

        global_annual_revenue_formatted = format_number(global_annual_revenue, locale=meta_lang, decimals=0)
        effective_exposed_formatted = format_number(effective_exposed, locale=meta_lang, decimals=0)
        sector_impact_factor_pct = format_number(sector_impact_factor * 100, locale=meta_lang, decimals=4)
        perimeter_weight_str = format_number(perimeter_weight, locale=meta_lang, decimals=2)
        total_capex_formatted = format_number(total_capex, locale=meta_lang, decimals=0)
        
        # Calculate ROSI percentage
        total_ale = fin_telemetry.get("total_annualized_risk_exposure")
        if total_ale is None:
            total_ale = sum(float(r.get("ale", 0)) for r in risks_list)
        
        rosi_percentage = "100"
        if total_capex > 0:
            rosi = ((total_ale - total_capex) / total_capex) * 100
            rosi_percentage = format_number(rosi, locale=meta_lang, decimals=1)

        # Deduplicate downtime hours via Joint Probability (Inclusion-Exclusion Principle)
        from decimal import Decimal

        from assessment_engine.domain.actuarial.risk_aggregator import (
            BlastRadiusDeduplicator,
        )
        raw_hours = [
            Decimal(str(r.get("ale_hours")))
            for r in risks_list
            if r.get("ale_hours") is not None
        ]
        if raw_hours:
            eff_hours_dec = BlastRadiusDeduplicator.compute_effective_downtime(raw_hours)
            eff_hours_str = format_number(float(eff_hours_dec), locale=meta_lang, decimals=1)
        elif ale_hours_val > 0.0:
            eff_hours_str = ale_hours_str
        else:
            eff_hours_str = format_number(0.0, locale=meta_lang, decimals=1)
            
        findings_briefs: List[str] = []
        exec_struct_risks = blueprint_data.get("executive_snapshot", {}).get("structural_risks", [])
        for sr in exec_struct_risks:
            if isinstance(sr, str) and len(sr.strip()) > 15:
                findings_briefs.append(sr.strip())

        if len(findings_briefs) < 3:
            for p in blueprint_data.get("pillars_analysis", []):
                for hc in (p.get("health_check_asis") or []):
                    brief = str(hc.get("finding") or hc.get("risk_observed") or hc.get("business_risk") or "").strip()
                    if brief and len(brief) > 15 and brief not in findings_briefs:
                        findings_briefs.append(brief)
                        if len(findings_briefs) >= 3:
                            break
                if len(findings_briefs) >= 3:
                    break

        if not findings_briefs:
            findings_briefs.append(fallback_vuln)

        primary_workloads = str(
            blueprint_data.get("primary_workloads_summary")
            or blueprint_data.get("primary_workloads")
            or blueprint_data.get("perimeter_context", {}).get("primary_workloads")
            or blueprint_data.get("executive_snapshot", {}).get("bottom_line_focus")
            or t("default_primary_workloads", locale=meta_lang)
        )

        target_score_val = float(blueprint_data.get("target_maturity_score") or blueprint_data.get("target_score") or min(5.0, gs_val + 1.5))
        target_score_str = format_number(target_score_val, locale=meta_lang, decimals=1)

        strat_roadmap = blueprint_data.get("strategic_roadmap")
        lead_init = ""
        if isinstance(strat_roadmap, dict):
            lead_init = str(strat_roadmap.get("lead_initiative", ""))
        elif isinstance(strat_roadmap, list) and strat_roadmap:
            first_item = strat_roadmap[0]
            if isinstance(first_item, dict):
                lead_init = str(first_item.get("initiative") or first_item.get("name") or "")

        first_pillar_name = ""
        pillars_list = blueprint_data.get("pillars_analysis")
        if isinstance(pillars_list, list) and pillars_list:
            first_p = pillars_list[0]
            if isinstance(first_p, dict):
                from assessment_engine.domain.taxonomy_resolver import (
                    extract_pillar_identifiers,
                    get_taxonomy_resolver,
                )
                first_pid, first_pname = extract_pillar_identifiers(first_p)
                first_pillar_name = first_pname or first_pid

        primary_pillar = lead_init or first_pillar_name or t("default_remediation_pillar", locale=meta_lang)
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()
        primary_pillar_resolved = resolver.resolve_pillar_by_any_reference(primary_pillar, default=primary_pillar, locale=meta_lang)
        remediation_horizon = t("default_remediation_horizon", locale=meta_lang)

        from assessment_engine.domain.actuarial.downtime_calibrator import (
            OperationalTailRiskEngine,
        )
        fin_telemetry = blueprint_data.get("financial_telemetry") or {}
        # Domain-scoped local P90 VaR for Tower Annex (aligning exactly with Section 4.3 P108)
        total_p90 = float(
            blueprint_data.get("total_fair_p90")
            or blueprint_data.get("worst_crisis_event")
            or (total_fair_ale * 2.2)
        )
        portfolio_contingency_p90 = float(
            fin_telemetry.get("tail_risk_p90_contingency")
            or fin_telemetry.get("p90_financial_exposure")
            or total_p90
        )
        ceiling_hours = float(
            fin_telemetry.get("operational_recovery_ceiling_hours")
            or blueprint_data.get("operational_recovery_ceiling_hours")
            or 24.0
        )
        tail_decomp = OperationalTailRiskEngine.decompose_tail_risk(
            expected_annual_loss=total_fair_ale,
            var_90_total=total_p90,
            composite_hourly_rate=hourly_rate,
            operational_recovery_ceiling_hours=ceiling_hours,
        )
        capped_p90_hours_str = format_number(tail_decomp.capped_operational_p90_hours, locale=meta_lang, decimals=1)

        hourly_rate_narrative = f"{format_currency(hourly_rate, currency_symbol=currency, locale=meta_lang, decimals=0)}{t('per_hour_suffix', locale=meta_lang)}"

        # Use authoritative pre-clamped score and band from context
        gs_val = ctx["gs_val"]
        global_band = ctx["global_band"]
        display_score_str = ctx["display_score_str"]

        strongest_name, strongest_score_str, weakest_name, weakest_score_str = extract_dimension_boundary_profile(
            pillars_analysis=blueprint_data.get("pillars_analysis", []),
            current_maturity_score=gs_val,
            locale=meta_lang,
        )

        payload_paragraphs = blueprint_data.get("executive_summary_paragraphs")
        has_explicit_paragraphs = (
            isinstance(payload_paragraphs, list)
            and len(payload_paragraphs) >= 4
            and all(isinstance(p, str) and len(p.strip()) > 20 for p in payload_paragraphs)
        )
        if has_explicit_paragraphs:
            p_texts = [str(p).strip() for p in payload_paragraphs[:4]]
        else:
            clean_score_str = format_number(gs_val, locale=meta_lang, decimals=2)
            synthesizer = ExecutiveNarrativeSynthesizer(locale_code=meta_lang)
            p_texts = synthesizer.synthesize_chapter_one_paragraphs(
                client_name=client_name,
                tower_name=tower_name,
                maturity_score=clean_score_str,
                maturity_tier_label=global_band,
                primary_workloads_summary=primary_workloads,
                findings_briefs=findings_briefs,
                hourly_burn_rate_fmt=hourly_rate_narrative,
                net_downtime_hours_fmt=eff_hours_str,
                annual_loss_expectancy_fmt=format_currency(total_fair_ale, currency_symbol=currency, locale=meta_lang, decimals=0),
                p90_downtime_hours_fmt=p90_hours_str,
                capped_p90_hours_fmt=capped_p90_hours_str,
                p90_var_exposure_fmt=format_currency(total_p90, currency_symbol=currency, locale=meta_lang, decimals=0),
                remediation_horizon_label=remediation_horizon,
                primary_remediation_pillar=primary_pillar_resolved,
                target_maturity_score=target_score_str,
                tower_id=tower_id,
                strongest_dim_name=strongest_name,
                strongest_dim_score=strongest_score_str,
                weakest_dim_name=weakest_name,
                weakest_dim_score=weakest_score_str,
                archetype=str(
                    blueprint_data.get("archetype")
                    or blueprint_data.get("domain_archetype")
                    or (
                        lambda: (
                            __import__("assessment_engine.domain.taxonomy.archetype_registry", fromlist=["get_actuarial_archetype_registry"])
                            .get_actuarial_archetype_registry()
                            .get_mapping_for_tower(tower_id)
                            .primary_archetype.value
                        )
                    )()
                ),
                operational_mission=str(blueprint_data.get("operational_mission") or blueprint_data.get("domain_semantics", {}).get("operational_mission") or ""),
                dilemma_anchor=str(blueprint_data.get("dilemma_anchor") or blueprint_data.get("domain_semantics", {}).get("dilemma_anchor") or ""),
                posture_modernization_focus=str(blueprint_data.get("posture_modernization_focus") or blueprint_data.get("domain_semantics", {}).get("posture_modernization_focus") or ""),
            )

        # 1. Paragraph 1: Authentic Domain Diagnostic (Priority to bespoke executive_snapshot.bottom_line)
        from assessment_engine.infrastructure.localization import (
            restore_locale_diacritics,
        )
        bespoke_bottom_line = str(
            blueprint_data.get("executive_snapshot", {}).get("bottom_line") or ""
        ).strip()
        p1_text = (
            bespoke_bottom_line
            if (not has_explicit_paragraphs and len(bespoke_bottom_line) > 40)
            else p_texts[0]
        )
        p1_text = restore_locale_diacritics(p1_text, meta_lang)
        nodes.append(ParagraphNode(text=p1_text, font_size=9.5, space_after=8))

        # 2. Paragraph 2: Lead-in + Structured List Bullets
        nodes.append(ParagraphNode(text=p_texts[1], font_size=9.5, space_after=4, keep_with_next=True))
        active_findings = findings_briefs[:3] if findings_briefs else [t("default_critical_vulnerability", locale=meta_lang)]
        from assessment_engine.infrastructure.localization import (
            restore_locale_diacritics,
        )
        for f_idx, fb in enumerate(active_findings):
            is_last = (f_idx == len(active_findings) - 1)
            b_text = fb.strip().rstrip(".")
            if ":" in b_text:
                parts = b_text.split(":", 1)
                formatted_bullet = f"**{parts[0].strip()}:** {parts[1].strip()}."
            else:
                formatted_bullet = f"{b_text}."
            formatted_bullet = restore_locale_diacritics(formatted_bullet, meta_lang)
            nodes.append(ParagraphNode(text=formatted_bullet, style="List Bullet", font_size=9.5, space_after=8 if is_last else 3))

        # 3. Paragraph 3: Actuarial Latent Exposure
        nodes.append(ParagraphNode(text=p_texts[2], font_size=9.5, space_after=8))

        # 4. Paragraph 4: Pure AS-IS Diagnostic Verdict
        nodes.append(ParagraphNode(text=p_texts[3], font_size=9.5, space_after=10))

        # Executive pacing: Chapter 1 stands strictly alone on Page 3
        nodes.append(PageBreakNode())

        #
        # CHAPTER 2: ASSESSMENT OBJECTIVE AND SCOPE
        #
        nodes.append(
            HeadingNode(
                text=t("chapter_2_methodology", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # Resolve domain introduction with 4-Tier Coalescing Resolution Pipeline (RFC 099)
        from assessment_engine.infrastructure.localization import (
            restore_locale_diacritics,
        )

        intro = resolve_domain_introduction(
            blueprint_data=blueprint_data,
            annex_data=annex_data,
            tower_id=tower_id,
            client_name=client_name,
            meta_lang=meta_lang,
        )
        obj = intro.get("domain_objective", "")
        intro_para = intro.get("introduction_paragraph", "")
        included_comps = intro.get("included_components", [])

        # 2.1 Objective and Scope
        nodes.append(
            HeadingNode(
                text=t("objective_and_scope_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        effective_obj = obj or t(
            "default_domain_objective_template",
            locale=meta_lang,
            tower_name=tower_name,
            client_name=client_name,
        )
        nodes.append(ParagraphNode(text=restore_locale_diacritics(effective_obj, meta_lang), space_after=8))

        # 2.2 Platform Description & Technical Scope
        nodes.append(SpacerNode(points=6))
        nodes.append(
            HeadingNode(
                text=t("platform_description_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        if intro_para:
            nodes.append(ParagraphNode(text=restore_locale_diacritics(intro_para, meta_lang), space_after=8))

        if included_comps:
            lead_text = t("components_evaluated_lead", locale=meta_lang)
            if lead_text:
                nodes.append(ParagraphNode(text=f"**{lead_text}**", space_after=4))
            for comp in included_comps:
                clean_comp = restore_locale_diacritics(comp, meta_lang)
                nodes.append(ParagraphNode(text=clean_comp, style="List Bullet", space_after=2))

        # 2.2 Regulatory and Methodological Framework Table (Auto-fit to window and contents)
        tower_id = str(ctx.get("tower_id") or "T1").upper()
        import json

        from assessment_engine.infrastructure.runtime_paths import ROOT

        tower_cat_file = ROOT / "engine_config" / "towers" / "tower_catalog.json"
        tower_cat: dict[str, Any] = {}
        if tower_cat_file.exists():
            try:
                tower_cat = json.loads(tower_cat_file.read_text(encoding="utf-8-sig"))
            except (json.JSONDecodeError, OSError):
                tower_cat = {}

        t_spec = (tower_cat.get(tower_id) or tower_cat.get("T1")) or {}
        reg_meta = (
            blueprint_data.get("document_meta", {}).get("regulatory_framework")
            or blueprint_data.get("regulatory_framework")
        )
        norm_fw_name = str(reg_meta or t_spec.get("primary_engineering_standard", "ISO/IEC 27001"))
        desc_key = t_spec.get("standard_description_key", "norm_row_iso_desc")
        purp_key = t_spec.get("standard_purpose_key", "norm_row_iso_purp")
        norm_fw_desc = t(desc_key, locale=meta_lang)
        norm_fw_purp = t(purp_key, locale=meta_lang)
        headers_norm = [
            CellNode(text=t("norm_col_standard", locale=meta_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="LEFT", font_size=9.5),
            CellNode(text=t("norm_col_scope", locale=meta_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="LEFT", font_size=9.5),
            CellNode(text=t("norm_col_purpose", locale=meta_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="LEFT", font_size=9.5),
        ]
        norm_rows = [
            TableRowNode(cells=headers_norm, is_header=True),
            TableRowNode(cells=[
                CellNode(text="CMMI for Infrastructure", bold=True, bg_color="FFFFFF", font_size=9.0),
                CellNode(text=t("norm_row_cmmi_desc", locale=meta_lang), bg_color="FFFFFF", font_size=9.0),
                CellNode(text=t("norm_row_cmmi_purp", locale=meta_lang), bg_color="FFFFFF", align="CENTER", font_size=9.0),
            ]),
            TableRowNode(cells=[
                CellNode(text=norm_fw_name, bold=True, bg_color=self.alt_row_hex, font_size=9.0),
                CellNode(text=norm_fw_desc, bg_color=self.alt_row_hex, font_size=9.0),
                CellNode(text=norm_fw_purp, bg_color=self.alt_row_hex, align="CENTER", font_size=9.0),
            ]),
            TableRowNode(cells=[
                CellNode(text="Open FAIR™", bold=True, bg_color="FFFFFF", font_size=9.0),
                CellNode(text=t("norm_row_fair_desc", locale=meta_lang), bg_color="FFFFFF", font_size=9.0),
                CellNode(text=t("norm_row_fair_purp", locale=meta_lang), bg_color="FFFFFF", align="CENTER", font_size=9.0),
            ]),
        ]
        nodes.append(SpacerNode(points=10))
        nodes.append(TableNode(rows=norm_rows, autofit=True, col_widths=[0.28, 0.47, 0.25]))

        # 2.3 & 2.4 CMMI Analytical Maturity Scale & Evaluated Capabilities Allocation
        _build_cmmi_methodology_and_capabilities_fn(ctx, nodes, self.primary_color_rgb)

        # Chapter 2 ends cleanly with dedicated page
        nodes.append(PageBreakNode())

        #
        # CHAPTER 3: TECHNOLOGICAL DIAGNOSIS AND MATURITY DASHBOARD
        #
        nodes.append(
            HeadingNode(
                text=t("chapter_3_diagnosis_cross_cutting", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # 3. Direct Introduction (Tenant Payload Domain Intro -> Localized Universal Fallback)
        from assessment_engine.domain.taxonomy_resolver import (
            extract_pillar_identifiers,
            get_taxonomy_resolver,
        )
        resolver = get_taxonomy_resolver()

        canonical_tower_id = str(ctx.get("tower_id") or blueprint_data.get("document_meta", {}).get("tower_id", "T1")).strip().upper()
        raw_tname = ctx.get("tower_name") or blueprint_data.get("document_meta", {}).get("tower_name", "Infrastructure Domain")
        tower_name = resolver.resolve_tower_name(
            tower_id=canonical_tower_id,
            default=raw_tname,
            locale=meta_lang,
        )
        ch3_archetype = resolve_domain_archetype(domain_id=canonical_tower_id, blueprint_data=blueprint_data)

        # Phase 2 (DEF-04): Decoupled Analytical Maturity Introduction (Zero Paragraph Cloning)
        # Synthesizes an analytical overview based on actual evaluated dimensions
        pillars_list = blueprint_data.get("pillars_analysis") or []
        scored_pillars = [
            p for p in pillars_list
            if isinstance(p, dict) and p.get("score") is not None
        ]
        if scored_pillars:
            sorted_p = sorted(scored_pillars, key=lambda x: float(x.get("score", 0.0)))
            weakest_p = sorted_p[0]
            strongest_p = sorted_p[-1]
            weakest_name = weakest_p.get("pillar_name") or weakest_p.get("pillar_id")
            strongest_name = strongest_p.get("pillar_name") or strongest_p.get("pillar_id")
            weakest_score = float(weakest_p.get("score", 0.0))
            strongest_score = float(strongest_p.get("score", 0.0))
            spread = round(strongest_score - weakest_score, 2)
            
            from assessment_engine.domain.maturity_band import ANNEX_MATURITY_BANDS, resolve_maturity_band
            gs_band = resolve_maturity_band(float(gs_val), ANNEX_MATURITY_BANDS, locale=meta_lang, translator=t)
            band_lbl = gs_band.get("label", "")
            
            if str(meta_lang).startswith("es"):
                intro_ch3 = (
                    f"La evaluación técnica del dominio de {tower_name} sitúa la madurez operativa global en un índice de "
                    f"**{format_number(gs_val, locale=meta_lang, decimals=2)} sobre 5,00 ({band_lbl})** bajo el marco internacional CMMI v2.0. "
                    f"El análisis de dispersión entre capacidades evidencia una asimetría de {spread:.2f} puntos: "
                    f"mientras que la mayor solidez se concentra en **{strongest_name}** ({format_number(strongest_score, locale=meta_lang, decimals=2)}/5,00), "
                    f"el principal punto de fricción operativa y deuda técnica reside en **{weakest_name}** ({format_number(weakest_score, locale=meta_lang, decimals=2)}/5,00), "
                    f"el cual define el cuello de botella estructural del servicio."
                )
            else:
                intro_ch3 = (
                    f"The technical diagnostic for {tower_name} positions the overall operational maturity at an index of "
                    f"**{format_number(gs_val, locale=meta_lang, decimals=2)} out of 5.00 ({band_lbl})** under the international CMMI v2.0 standard. "
                    f"Dispersion analysis across evaluated dimensions reveals an asymmetry of {spread:.2f} points: "
                    f"while the strongest posture is achieved in **{strongest_name}** ({format_number(strongest_score, locale=meta_lang, decimals=2)}/5.00), "
                    f"the primary operational bottleneck and technical debt concentrates in **{weakest_name}** ({format_number(weakest_score, locale=meta_lang, decimals=2)}/5.00)."
                )
        else:
            intro_ch3 = t("intro_ch3_technical_diagnosis", locale=meta_lang, tower_name=tower_name, client_name=client_name)
        nodes.append(ParagraphNode(text=intro_ch3))
        nodes.append(SpacerNode(points=10))

        # Unified Maturity Score Card (Autofit)
        nodes.append(
            TableNode(
                rows=[
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=t("score_lbl", locale=meta_lang),
                                bold=True,
                                bg_color=self.primary_color_hex,
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            ),
                            CellNode(
                                text=t("maturity_lbl", locale=meta_lang),
                                bold=True,
                                bg_color=self.primary_color_hex,
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            ),
                        ],
                        is_header=True,
                    ),
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=display_score_str,
                                bold=True,
                                font_size=16,
                                bg_color="FFF3CD" if gs_val < 3.4 else "D9F2D9",
                                align="CENTER",
                            ),
                            CellNode(
                                text=global_band,
                                bold=True,
                                font_size=12,
                                bg_color="FFF3CD" if gs_val < 3.4 else "D9F2D9",
                                align="CENTER",
                            ),
                        ]
                    ),
                ],
                autofit=True,
                col_widths=[0.5, 0.5],
            )
        )
        nodes.append(SpacerNode(points=5))
        nodes.append(
            ParagraphNode(
                text=t("maturity_scale_legend", locale=meta_lang),
                align="CENTER",
                italic=True,
            )
        )
        nodes.append(SpacerNode(points=8))

        # Friendly pedagogical score explanation (Domain-Specific Tower Resolution with Dynamic Parameter Binding)
        from assessment_engine.domain.taxonomy_resolver import (
            extract_pillar_identifiers,
            get_taxonomy_resolver,
        )
        resolver = get_taxonomy_resolver()

        pillars_list = blueprint_data.get("pillars_analysis", [])
        if pillars_list:
            sorted_by_score = sorted(
                pillars_list,
                key=lambda item: _safe_float(item.get("score"), default=DEFAULT_UNASSESSED_PILLAR_SCORE),
            )
            weakest_p = sorted_by_score[0]
            strongest_p = sorted_by_score[-1]

            raw_w_pid, raw_w_pname = extract_pillar_identifiers(weakest_p)
            weakest_pillar_name = resolver.resolve_pillar_by_any_reference(
                raw_w_pid or raw_w_pname,
                default=(raw_w_pname or raw_w_pid or "Core Capability"),
                locale=meta_lang,
                tower_id=canonical_tower_id,
            )
            weakest_score_val = _safe_float(weakest_p.get("score"), default=DEFAULT_UNASSESSED_PILLAR_SCORE)
            weakest_pillar_score = format_number(weakest_score_val, locale=meta_lang, decimals=2)

            raw_s_pid, raw_s_pname = extract_pillar_identifiers(strongest_p)
            strongest_pillar_name = resolver.resolve_pillar_by_any_reference(
                raw_s_pid or raw_s_pname,
                default=(raw_s_pname or raw_s_pid or "Leading Capability"),
                locale=meta_lang,
                tower_id=canonical_tower_id,
            )
            strongest_score_val = _safe_float(strongest_p.get("score"), default=DEFAULT_UNASSESSED_PILLAR_SCORE)
            strongest_pillar_score = format_number(strongest_score_val, locale=meta_lang, decimals=2)
        else:
            weakest_pillar_name = t("table_header_pillar", locale=meta_lang)
            weakest_pillar_score = "1.00"
            strongest_pillar_name = t("table_header_pillar", locale=meta_lang)
            strongest_pillar_score = "3.00"
            weakest_score_val = 1.00
            strongest_score_val = 3.00

        clean_gs_str = format_number(gs_val, locale=meta_lang, decimals=2)

        dynamic_score_expl = str(
            blueprint_data.get("scorecard_commentary")
            or blueprint_data.get("diagnostic_narrative")
            or ""
        ).strip()
        ch3_commentaries_by_tower = loc_branch.get("ch3_scorecard_by_tower", {})
        tower_comm_tmpl = ch3_commentaries_by_tower.get(canonical_tower_id)

        if dynamic_score_expl and len(dynamic_score_expl) > 20:
            score_expl = dynamic_score_expl
        elif tower_comm_tmpl:
            score_expl = tower_comm_tmpl.format(
                score_val=clean_gs_str,
                maturity_tier_label=global_band,
                client_name=client_name,
                tower_title=tower_name,
                tower_name=tower_name,
                weakest_pillar_name=weakest_pillar_name,
                weakest_pillar_score=weakest_pillar_score,
                strongest_pillar_name=strongest_pillar_name,
                strongest_pillar_score=strongest_pillar_score,
            )
        else:
            # Select data-driven template based on pillar distribution and maturity score
            if not pillars_list or len(pillars_list) == 1:
                scorecard_tmpl_key = "scorecard_contrast_single"
            elif weakest_score_val == strongest_score_val:
                scorecard_tmpl_key = "scorecard_contrast_uniform"
            else:
                if gs_val >= 2.60:
                    scorecard_tmpl_key = "scorecard_contrast_divergent_high"
                elif gs_val >= 2.30:
                    scorecard_tmpl_key = "scorecard_contrast_divergent_mid"
                else:
                    scorecard_tmpl_key = "scorecard_contrast_divergent_low"

            score_expl = t(
                scorecard_tmpl_key,
                locale=meta_lang,
                score_val=clean_gs_str,
                maturity_tier_label=global_band,
                client_name=client_name,
                tower_title=tower_name,
                tower_name=tower_name,
                weakest_pillar_name=weakest_pillar_name,
                weakest_pillar_score=weakest_pillar_score,
                strongest_pillar_name=strongest_pillar_name,
                strongest_pillar_score=strongest_pillar_score,
            )
        nodes.append(ParagraphNode(text=score_expl))
        nodes.append(SpacerNode(points=12))

        # Unified Pillar Maturity Breakdown Table
        col_1_hdr = t("table_header_pillar_capacity", locale=meta_lang)
        col_2_hdr = t("table_header_score_asis", locale=meta_lang)
        col_3_hdr = t("table_header_status_level", locale=meta_lang)

        health_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_1_hdr, bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255]),
                    CellNode(text=col_2_hdr, bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=col_3_hdr, bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                ],
                is_header=True,
            )
        ]

        from assessment_engine.domain.taxonomy_resolver import (
            extract_pillar_identifiers,
            get_taxonomy_resolver,
        )
        resolver = get_taxonomy_resolver()

        for s_idx, p in enumerate(blueprint_data.get("pillars_analysis", [])):
            bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            raw_pid, raw_pname = extract_pillar_identifiers(p)
            p_name = resolver.resolve_pillar_by_any_reference(
                raw_pid or raw_pname,
                default=(raw_pname or raw_pid or "Pillar"),
                locale=meta_lang,
                tower_id=tower_id,
            )
            p_score = float(p.get("score", 3.0))
            score_formatted = format_number(p_score, locale=meta_lang, decimals=2)
            
            # Map score to status and color via localized keys
            from assessment_engine.domain.actuarial.maturity_band import (
                resolve_maturity_interval,
            )
            interval = resolve_maturity_interval(p_score)
            status_map = {
                5: (t("status_excellent", locale=meta_lang), "D9F2D9"),
                4: (t("status_stable", locale=meta_lang), "E2F0D9"),
                3: (t("status_standardized", locale=meta_lang), "FFF3CD"),
                2: (t("status_basic", locale=meta_lang), "FCE4D6"),
                1: (t("status_critical", locale=meta_lang), "F2D9D9"),
            }
            p_status, p_bg_color = status_map[interval.level]

            health_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=p_name, bold=True, bg_color=self.alt_row_hex),
                        CellNode(text=score_formatted, bg_color=bg, align="CENTER"),
                        CellNode(text=p_status, bold=True, bg_color=p_bg_color, align="CENTER"),
                    ]
                )
            )

        nodes.append(TableNode(rows=health_rows, autofit=True, col_widths=[0.48, 0.20, 0.32]))
        nodes.append(SpacerNode(points=16))

    def _build_systemic_risk_section(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        meta_lang = ctx["meta_lang"]
        modules_dir = ctx["modules_dir"]
        intel_data = ctx["intel_data"]
        tower_id = ctx["tower_id"]

        trans_candidates = list(modules_dir.glob("*transversal*.md")) if modules_dir.exists() else []
        trans_path = trans_candidates[0] if trans_candidates else (modules_dir / "transversal_analysis.md")
        if trans_path.exists():
            transversal_title = t("transversal_analysis_title", locale=meta_lang)
            nodes.append(HeadingNode(text=transversal_title, level=2, primary_color_rgb=self.primary_color_rgb))
            nodes.extend(self._parse_markdown_to_nodes(trans_path, skip_level_1=True))
            nodes.append(SpacerNode(points=15))
        else:
            # 3.4 Cross-Cutting Structural Debt Patterns (dynamically synthesized from tenant payload)
            nodes.append(PageBreakNode())
            nodes.append(
                HeadingNode(
                    text=t("cross_cutting_debt_title", locale=meta_lang),
                    level=2,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )
            canonical_tower_id = str(tower_id or "T1").strip().upper()
            catalog = load_locales_catalog().get(meta_lang, {})
            tower_intro_map = catalog.get("cross_cutting_debt_intro_by_tower", {})
            transversal_intro = tower_intro_map.get(canonical_tower_id) or t("cross_cutting_debt_intro", locale=meta_lang)

            nodes.append(ParagraphNode(text=transversal_intro, italic=True))
            nodes.append(SpacerNode(points=6))

            dynamic_patterns = self._extract_dynamic_transversal_patterns(
                ctx=ctx,
                canonical_tower_id=canonical_tower_id,
                meta_lang=meta_lang,
            )
            for p_text in dynamic_patterns:
                nodes.append(ParagraphNode(text=p_text))
                nodes.append(SpacerNode(points=4))
            nodes.append(SpacerNode(points=11))

        # 3.5 Systemic Risk Indicators and Decision Context (MCDA + Monte Carlo + LCBN)
        if intel_data:
            try:
                overrides = intel_data.get("tower_overrides", {}).get(tower_id, {})
                metrics = overrides.get("metrics", {}) if isinstance(overrides, dict) else {}
                business_criticality = float(metrics.get("business_criticality")) if isinstance(metrics, dict) and metrics.get("business_criticality") is not None else None
                regulatory_compliance = float(metrics.get("regulatory_compliance") or 0.0) if isinstance(metrics, dict) else 0.0
                implementation_feasibility = float(metrics.get("implementation_feasibility") or 0.0) if isinstance(metrics, dict) else 0.0
                
                sensitivity = overrides.get("sensitivity_analysis", {}) if isinstance(overrides, dict) else {}
                dii_03 = None
                if isinstance(sensitivity, dict):
                    dii_03 = sensitivity.get("decision_instability_indices", {}).get("dii_threshold_03_pct")
                
                epistemic = intel_data.get("epistemic_graph", {}) if isinstance(intel_data, dict) else {}
                audits = epistemic.get("audits", {}) if isinstance(epistemic, dict) else {}
                erc_dict = audits.get("eigenvector_risk_centrality", {}) if isinstance(audits, dict) else {}
                erc = erc_dict.get(tower_id) if isinstance(erc_dict, dict) else None
                
                spof_by_cascade = audits.get("single_point_of_failure_by_cascade", "") if isinstance(audits, dict) else ""
                spof_by_centrality = audits.get("single_point_of_failure_by_centrality", "") if isinstance(audits, dict) else ""
                
                if business_criticality is not None:
                    # Add heading for Systemic Risk Metrics
                    nodes.append(
                        HeadingNode(
                            text=t("section_interdependence_analysis", locale=meta_lang),
                            level=2,
                            primary_color_rgb=self.primary_color_rgb,
                        )
                    )
                    
                    intro_text_inter = t("interdep_intro_text", locale=meta_lang)
                    nodes.append(ParagraphNode(text=intro_text_inter))
                    
                    for b_text in get_localized_list("interdep_key_bullets", locale=meta_lang):
                        nodes.append(ParagraphNode(text=b_text, style="List Bullet"))
                        
                    concl_text = t("interdep_concl_text", locale=meta_lang)

                    nodes.append(ParagraphNode(text=concl_text))
                    nodes.append(SpacerNode(points=10))

                    # Build the metrics table
                    is_spof = (tower_id == spof_by_cascade or tower_id == spof_by_centrality)
                    spof_status = "YES" if is_spof else "NO"
                    spof_status_text = t("interdep_spof_yes", locale=meta_lang) if is_spof else t("interdep_spof_no", locale=meta_lang)
                    dii_num = float(dii_03) if dii_03 is not None else 0.0
                    dii_val = f"{format_number(dii_num, locale=meta_lang, decimals=1)}%"
                    erc_num = float(erc) if erc is not None else 0.0
                    erc_val = format_number(erc_num, locale=meta_lang, decimals=3)

                    if business_criticality >= 80.0:
                        crit_lbl = t("interdep_status_extreme", locale=meta_lang)
                    elif business_criticality >= 50.0:
                        crit_lbl = t("interdep_status_high", locale=meta_lang)
                    else:
                        crit_lbl = t("interdep_status_medium", locale=meta_lang)

                    if regulatory_compliance >= 80.0:
                        reg_lbl = t("interdep_status_critical", locale=meta_lang)
                    elif regulatory_compliance >= 50.0:
                        reg_lbl = t("interdep_status_moderate", locale=meta_lang)
                    else:
                        reg_lbl = t("interdep_status_standard", locale=meta_lang)

                    if implementation_feasibility >= 60.0:
                        viab_lbl = t("interdep_status_viable", locale=meta_lang)
                    else:
                        viab_lbl = t("interdep_status_complex", locale=meta_lang)

                    if (dii_03 or 0) < 15.0:
                        dii_lbl = t("interdep_status_stable_diag", locale=meta_lang)
                    elif (dii_03 or 0) < 30.0:
                        dii_lbl = t("interdep_status_mod_diag", locale=meta_lang)
                    else:
                        dii_lbl = t("interdep_status_volatile_diag", locale=meta_lang)

                    if (erc or 0) >= 0.50:
                        erc_lbl = t("interdep_status_high_influence", locale=meta_lang)
                    elif (erc or 0) >= 0.20:
                        erc_lbl = t("interdep_status_moderate", locale=meta_lang)
                    else:
                        erc_lbl = t("interdep_status_low_influence", locale=meta_lang)

                    if is_spof:
                        spof_lbl = t("interdep_status_bottleneck", locale=meta_lang)
                    else:
                        spof_lbl = t("interdep_status_not_bottleneck", locale=meta_lang)

                    nodes.append(
                        TableNode(
                            rows=[
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_header_indicator", locale=meta_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255]),
                                        CellNode(text=t("interdep_header_value", locale=meta_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                                        CellNode(text=t("interdep_header_status", locale=meta_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER"),
                                    ],
                                    is_header=True,
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_business_criticality_title", locale=meta_lang)),
                                        CellNode(text=f"{format_number(business_criticality, locale=meta_lang, decimals=1)}%", align="CENTER"),
                                        CellNode(text=crit_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_reg_pressure_title", locale=meta_lang)),
                                        CellNode(text=f"{format_number(regulatory_compliance, locale=meta_lang, decimals=1)}%", align="CENTER"),
                                        CellNode(text=reg_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_op_viability_title", locale=meta_lang)),
                                        CellNode(text=f"{format_number(implementation_feasibility, locale=meta_lang, decimals=1)}%", align="CENTER"),
                                        CellNode(text=viab_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_dii_title", locale=meta_lang)),
                                        CellNode(text=dii_val, align="CENTER"),
                                        CellNode(text=dii_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_erc_title", locale=meta_lang)),
                                        CellNode(text=erc_val, align="CENTER"),
                                        CellNode(text=erc_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_spof_title", locale=meta_lang)),
                                        CellNode(text=spof_status_text, bold=True, align="CENTER", bg_color="F2D9D9" if is_spof else "D9F2D9"),
                                        CellNode(text=spof_lbl, align="CENTER"),
                                    ]
                                ),
                            ]
                        )
                    )
                    nodes.append(SpacerNode(points=10))

                    # Add Glossary / Legend
                    legend_title = t("interdep_gloss_title", locale=meta_lang)
                    nodes.append(ParagraphNode(text=f"**{legend_title}**", bold=True))

                    nodes.append(_build_criticality_bullet(business_criticality, locale=meta_lang))
                    nodes.append(_build_regulatory_bullet(regulatory_compliance, locale=meta_lang))
                    nodes.append(_build_feasibility_bullet(implementation_feasibility, locale=meta_lang))
                    dii_pct = dii_03 if dii_03 is not None else 0.0
                    nodes.append(_build_dii_bullet(dii_pct, locale=meta_lang))
                    erc_val_num = erc if erc is not None else 0.0
                    nodes.append(_build_erc_bullet(erc_val_num, locale=meta_lang))
                    nodes.append(_build_spof_bullet(spof_status, locale=meta_lang))
                    nodes.append(SpacerNode(points=20))
            except Exception as e:
                logger.info(f"⚠️ Error injecting systemic risk metrics in AST Bridge: {e}")

    def _extract_dynamic_transversal_patterns(
        self,
        ctx: dict[str, Any],
        canonical_tower_id: str,
        meta_lang: str,
    ) -> list[str]:
        """Dynamically synthesizes exactly 3 high-impact cross-cutting structural debt patterns

        from the tenant's runtime payload, strictly derived from the lowest-scoring pillars
        and their empirical forensic findings.
        Guarantees 100% zero-hardcoding and zero cross-tenant contamination.
        """
        blueprint_data = ctx.get("blueprint_data") or {}
        pillars_list = blueprint_data.get("pillars_analysis", [])

        from assessment_engine.domain.taxonomy_resolver import (
            extract_pillar_identifiers,
            get_taxonomy_resolver,
        )
        resolver = get_taxonomy_resolver()

        sorted_pillars = sorted(
            pillars_list,
            key=lambda item: _safe_float(item.get("score"), default=DEFAULT_UNASSESSED_PILLAR_SCORE),
        )

        patterns: list[str] = []
        for p_idx, pillar in enumerate(sorted_pillars, 1):
            if len(patterns) >= 3:
                break
            raw_pid, raw_pname = extract_pillar_identifiers(pillar)
            p_name = resolver.resolve_pillar_by_any_reference(
                raw_pid or raw_pname,
                default=(raw_pname or raw_pid or f"Capability {p_idx}"),
                locale=meta_lang,
                tower_id=canonical_tower_id,
            )

            finding_text = ""
            # 1. Prioritize real field health check findings
            hc_list = pillar.get("health_check_asis") or []
            if isinstance(hc_list, list) and hc_list:
                for hc in hc_list:
                    f_cand = str(hc.get("finding") or hc.get("capability") or "").strip()
                    if f_cand:
                        finding_text = f_cand
                        break

            # 2. Check findings array
            if not finding_text:
                findings = pillar.get("findings")
                if findings and isinstance(findings, list):
                    for f_item in findings:
                        if isinstance(f_item, dict) and f_item.get("finding"):
                            finding_text = str(f_item["finding"]).strip()
                            break

            # 3. Check asis_architecture_description diagnostic sentence
            if not finding_text:
                desc = str(pillar.get("asis_architecture_description") or "").strip()
                if desc:
                    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", desc) if s.strip()]
                    if len(sentences) > 1:
                        finding_text = sentences[1]
                    elif sentences:
                        finding_text = sentences[0]

            if not finding_text:
                finding_text = t("diag_summary_default", locale=meta_lang)

            finding_text = finding_text.rstrip(".") + "."
            patterns.append(f"{len(patterns) + 1}. **{p_name}:** {finding_text}")

        # Final safety guarantee of exactly 3 patterns
        while len(patterns) < 3:
            p_idx = len(patterns) + 1
            default_summary = t("diag_summary_default", locale=meta_lang)
            patterns.append(f"{p_idx}. **{t('table_header_pillar', locale=meta_lang)} {p_idx}:** {default_summary}")

        return patterns

    def _build_maturity_and_benchmarks(self, ctx: dict[str, Any], nodes: List[Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        from assessment_engine.infrastructure.localization import (
            format_number,
            get_localized_list,
            t,
        )

        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        case_dir = ctx["case_dir"]
        tower_id = ctx["tower_id"]
        modules_dir = ctx["modules_dir"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        total_fair_ale = ctx["total_fair_ale"]
        currency = ctx["currency"]
        meta_lang = ctx["meta_lang"]
        loc_branch = self.loc_branch

        # RAGE Forensic Verification Injection
        snapshot_file = case_dir / "benchmarks_snapshot.json"
        if snapshot_file.exists():
            try:
                with open(snapshot_file, "r", encoding="utf-8-sig") as sf:
                    snap_data = json.load(sf)
                snapshots = snap_data.get("snapshots", {})
                if snapshots:
                    # Silent Drop: Filter and find valid, verified benchmarks for the current tower
                    valid_snapshots = []
                    for t_id, t_snap in sorted(snapshots.items()):
                        if t_id != tower_id:
                            continue
                        verif_status = t_snap.get("verification_status", "failed")
                        quote = t_snap.get("evidence_quote", "")
                        neg_filters = [f.lower() for f in get_localized_list("negative_evidence_filters", locale=meta_lang, default=["no evidence", "not found"])]
                        if verif_status == "verified" and quote and not any(nf in quote.lower() for nf in neg_filters):
                            valid_snapshots.append((t_id, t_snap))

                    if valid_snapshots:
                        nodes.append(
                            HeadingNode(
                                text=t("rage_traceability_heading", locale=meta_lang),
                                level=2,
                                primary_color_rgb=self.primary_color_rgb,
                            )
                        )
                        intro_text = t("rage_traceability_intro", locale=meta_lang)
                        nodes.append(ParagraphNode(text=intro_text))
                        nodes.append(SpacerNode(points=10))

                        for t_id, t_snap in valid_snapshots:
                            framework_name = t_snap.get(
                                "framework_name",
                                t("rage_framework_fallback", locale=meta_lang),
                            )
                            score = t_snap.get("dynamic_score", 4.0)
                            quote = t_snap.get("evidence_quote", "")
                            url = t_snap.get("evidence_source_url", "")
                            local_path = t_snap.get("local_snapshot_path", "")

                            header_p = t(
                                "rage_tower_header",
                                locale=meta_lang,
                                tower_id=t_id,
                                framework_name=framework_name,
                                score=f"{score:,.1f}",
                            )
                            nodes.append(ParagraphNode(text=header_p))

                            quote_p = t("rage_evidence_extracted", locale=meta_lang, quote=quote)
                            nodes.append(ParagraphNode(text=quote_p))

                            source_p = t("rage_reference_source", locale=meta_lang, url=url)
                            if local_path:
                                source_p += t("rage_local_vault", locale=meta_lang, local_path=local_path)
                            nodes.append(ParagraphNode(text=source_p))
                            nodes.append(SpacerNode(points=10))
            except Exception as ex:
                logger.info(f"⚠️  [RAGE] Failed to inject RAGE report into AST: {ex}")

        # 4.3 Detailed Technical Diagnostic by Capability (Section 3.2 Executive Pillar Cards)
        if blueprint_data and blueprint_data.get("pillars_analysis"):
            from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
                derive_in_memory_maturity_matrix,
            )
            in_mem_rows = derive_in_memory_maturity_matrix(blueprint_data, doc_lang=meta_lang)

            # SECTION 3.2: DETAILED TECHNICAL DIAGNOSTIC BY CAPABILITY (EXECUTIVE PILLAR CARDS)
            nodes.append(SpacerNode(points=16))
            nodes.append(
                HeadingNode(
                    text=t("sec_3_2_detailed_diagnostics_title", locale=meta_lang),
                    level=2,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )
            nodes.append(
                ParagraphNode(
                    text=t("sec_3_2_detailed_diagnostics_intro", locale=meta_lang),
                    font_size=9.5,
                    space_after=12,
                )
            )

            _cmmi_es_map = {
                "Initial": "Inicial", "Repeatable": "Gestionado (Repetible)", "Defined": "Definido",
                "Managed": "Gestionado", "Quantitatively Managed": "Gestionado Cuantitativamente",
                "Optimized": "En Optimización", "Optimizing": "En Optimización",
                "Inicial": "Inicial", "Repetible": "Gestionado (Repetible)", "Definido": "Definido",
                "Gestionado": "Gestionado", "Gestionado Cuantitativamente": "Gestionado Cuantitativamente",
                "Optimizado": "En Optimización",
            }

            for p_idx, r_item in enumerate(in_mem_rows, 1):
                if p_idx in (2, 4):
                    nodes.append(PageBreakNode())
                p_name = r_item.get("pillar_name") or f"{t('table_header_pillar', locale=meta_lang)} {p_idx}"
                nodes.append(
                    HeadingNode(
                        text=f"3.2.{p_idx}. {p_name}",
                        level=3,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )

                cal_val = _safe_float(r_item.get("score"), default=DEFAULT_UNASSESSED_PILLAR_SCORE)
                dec_val = _safe_float(r_item.get("declared_score"), default=cal_val)
                delta_val = round(cal_val - dec_val, 2)
                dec_fmt = format_number(dec_val, locale=meta_lang, decimals=2)
                cal_fmt = format_number(cal_val, locale=meta_lang, decimals=2)
                raw_dec_band = r_item.get("declared_band_label") or ""
                raw_cal_band = r_item.get("band_label") or ""
                is_spanish = str(meta_lang).startswith("es")
                dec_band = _cmmi_es_map.get(raw_dec_band, raw_dec_band) if is_spanish else raw_dec_band
                cal_band = _cmmi_es_map.get(raw_cal_band, raw_cal_band) if is_spanish else raw_cal_band

                dec_display = f"{dec_fmt} ({dec_band})" if dec_band else dec_fmt
                cal_display = f"{cal_fmt} ({cal_band})" if cal_band else cal_fmt

                if abs(delta_val) >= DIVERGENCE_ALERT_THRESHOLD:
                    delta_str = format_number(delta_val, locale=meta_lang, decimals=2)
                    if delta_val < 0:
                        div_badge = t("badge_divergence_gap", locale=meta_lang, delta=delta_str)
                        div_bg = COLOR_STATUS_GAP
                    else:
                        div_badge = t("badge_divergence_conservative", locale=meta_lang, delta=f"+{delta_str}")
                        div_bg = COLOR_STATUS_CONSERVATIVE

                    badge_cells_header = [
                        CellNode(text=t("badge_declared_label", locale=meta_lang), bold=True, is_header=True, font_size=8.5, bg_color=self.alt_row_hex, align="CENTER"),
                        CellNode(text=t("badge_calibrated_label", locale=meta_lang), bold=True, is_header=True, font_size=8.5, bg_color=self.alt_row_hex, align="CENTER"),
                        CellNode(text=t("badge_divergence_label", locale=meta_lang), bold=True, is_header=True, font_size=8.5, bg_color=self.alt_row_hex, align="CENTER"),
                    ]
                    badge_cells_data = [
                        CellNode(text=dec_display, font_size=8.5, align="CENTER"),
                        CellNode(text=cal_display, bold=True, font_size=8.5, align="CENTER"),
                        CellNode(text=div_badge, bold=True, font_size=8.5, align="CENTER", bg_color=div_bg),
                    ]
                    badge_rows = [TableRowNode(cells=badge_cells_header), TableRowNode(cells=badge_cells_data)]
                    nodes.append(TableNode(rows=badge_rows, autofit=True, col_widths=[0.33, 0.33, 0.34]))
                    nodes.append(SpacerNode(points=8))
                else:
                    score_prefix = t("score_label_prefix", locale=meta_lang)
                    nodes.append(
                        ParagraphNode(
                            text=f"**{score_prefix}:** {cal_display}",
                            font_size=9.0,
                            space_after=6,
                        )
                    )

                # Render the authentic, bespoke architectural narrative paragraphs
                desc_paragraphs = r_item.get("architectural_narrative_paragraphs") or []
                if not desc_paragraphs and r_item.get("operational_reality"):
                    desc_paragraphs = [r_item["operational_reality"]]

                for para_idx, para_text in enumerate(desc_paragraphs):
                    is_last = (para_idx == len(desc_paragraphs) - 1)
                    nodes.append(
                        ParagraphNode(
                            text=para_text,
                            font_size=9.5,
                            space_after=14 if is_last else 6,
                        )
                    )
        else:
            csv_mat_candidates = (
                list(modules_dir.glob("*maturity*.csv"))
                + list(modules_dir.glob("*matrix*.csv"))
            ) if modules_dir and modules_dir.exists() else []
            csv_mat_path = csv_mat_candidates[0] if csv_mat_candidates else (modules_dir / "maturity_matrix.csv" if modules_dir else Path("non_existent.csv"))
            if csv_mat_path.exists():
                mat_headers = get_localized_list("justification_table_headers", locale=meta_lang)
                nodes.append(self._parse_csv_generic(csv_mat_path, mat_headers, col_widths=[0.28, 0.14, 0.58]))

        #
        # CHAPTER 4: QUANTITATIVE RISK MATRIX (O-FAIR)
        #
        nodes.append(
            HeadingNode(
                text=t("chapter_4_fair_resilience", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(ParagraphNode(text=t("ch4_methodological_intro", locale=meta_lang), space_after=8))

        # Build a lookup map from blueprint payload findings for detailed FAIR metrics
        fair_lookup = {}
        try:
            for pillar in blueprint_data.get("pillars_analysis", []):
                for hc in pillar.get("health_check_asis", []):
                    cap_name = hc.get("capability")
                    if cap_name:
                        fair_lookup[cap_name] = {
                            "p90": hc.get("fair_p90_score", 0.0),
                            "min": hc.get("fair_min_score", 0.0),
                            "max": hc.get("fair_max_score", 0.0),
                        }
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.warning(f"[AST Bridge Warning] Error reading FAIR metrics from annex data: {ex}")

        # Extract FAIR risks: Authoritative blueprint payload takes precedence as SSOT
        risks_data_list = []
        if blueprint_data and blueprint_data.get("pillars_analysis"):
            from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
                derive_in_memory_fair_risks,
            )
            rate_mult = float(ctx.get("rate_mult", 1.0))
            currency = str(ctx.get("currency") or blueprint_data.get("currency") or "")
            risks_data_list, _ = derive_in_memory_fair_risks(
                blueprint_data, doc_lang=meta_lang, currency=currency, rate_mult=rate_mult
            )
        else:
            # Fallback to CSV if structured payload is absent
            csv_candidates = list(modules_dir.glob("*.csv")) if modules_dir.exists() else []
            csv_risks_path = next(
                (f for f in csv_candidates if "fair" in f.name.lower() or "risk" in f.name.lower()),
                modules_dir / "fair_risks.csv",
            )
            if csv_risks_path.exists():
                try:
                    with open(csv_risks_path, "r", encoding="utf-8-sig") as cf:
                        reader = csv.reader(cf, delimiter=";")
                        next(reader, None)
                        rag_marker = t("evidence_rag_marker", locale=meta_lang)
                        for r_idx, row_data in enumerate(reader):
                            if not row_data or len(row_data) < 6:
                                continue
                            try:
                                pillar_full_name = row_data[0].split(" - ")[0]
                                finding_raw = row_data[1]
                                finding_parts = finding_raw.split(rag_marker) if rag_marker in finding_raw else [finding_raw]
                                finding = finding_parts[0]
                                evidence = finding_parts[1].strip('"') if len(finding_parts) > 1 else ""

                                tef_val = float(str(row_data[3]).replace(",", ".").strip())
                                lm_val = float(str(row_data[4]).replace(",", ".").strip())
                                ale_val = float(str(row_data[5]).replace(",", ".").strip())

                                # Calibrate actuarial LEF and SLE (RFC 055)
                                if tef_val >= 1.0:
                                    calc_lef = min(0.50, max(0.08, tef_val * 0.09))
                                else:
                                    calc_lef = max(0.05, tef_val)
                                calc_sle = ale_val / calc_lef if (ale_val > 0.0 and calc_lef > 0.0) else (lm_val * 5000.0)

                                r_item = {
                                    "id": f"RVS{r_idx + 1:02d}",
                                    "pillar": pillar_full_name,
                                    "capability": row_data[0].split(" - ")[1]
                                    if " - " in row_data[0]
                                    else row_data[0],
                                    "finding": finding,
                                    "evidence": evidence,
                                    "business_risk": row_data[2],
                                    "tef": tef_val,
                                    "lm": lm_val,
                                    "lef": round(calc_lef, 4),
                                    "sle": round(calc_sle, 2),
                                    "ale": ale_val,
                                }
                                risks_data_list.append(r_item)
                            except (ValueError, IndexError) as row_ex:
                                logger.warning(f"[AST Bridge Warning] Skipped malformed risk row {r_idx}: {row_ex}")
                except (OSError, ValueError, KeyError, AttributeError) as ex:
                    logger.warning(f"[AST Bridge Warning] Error reading risks CSV file: {ex}")

        # Synchronize SLE and LEF strictly from authoritative Domain Engine SSOT (Zero Presentation Math)
        for r_item in risks_data_list:
            decomp = r_item.get("additive_loss_decomposition") or {}
            vec_out = (r_item.get("actuarial_input_vector") or {}).get("outputs") or {}

            ssot_sle = (
                decomp.get("gross_mean_sle")
                if decomp.get("gross_mean_sle") is not None
                else (
                    vec_out.get("mean_sle")
                    if vec_out.get("mean_sle") is not None
                    else r_item.get("sle")
                )
            )
            ssot_lef = (
                decomp.get("mean_lef")
                if decomp.get("mean_lef") is not None
                else (
                    vec_out.get("mean_lef")
                    if vec_out.get("mean_lef") is not None
                    else r_item.get("lef")
                )
            )
            ssot_ale = (
                decomp.get("net_allocated_ale")
                if decomp.get("net_allocated_ale") is not None
                else r_item.get("ale")
            )

            if ssot_sle is not None:
                r_item["sle"] = round(float(ssot_sle), 2)
            if ssot_lef is not None:
                r_item["lef"] = round(float(ssot_lef), 4)
            if ssot_ale is not None and r_item.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR":
                r_item["ale"] = round(float(ssot_ale), 2)

        # Build executive risks summary paragraph
        primary_risks = [r for r in risks_data_list if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"]
        actual_cards_sum = sum(float(r.get("ale") or 0.0) for r in primary_risks)
        if actual_cards_sum > 0:
            total_fair_ale = actual_cards_sum

        formatted_ale = format_number(
            total_fair_ale, locale=meta_lang, decimals=0
        )
        if primary_risks and total_fair_ale > 0:
            pillar_sums: dict[str, float] = {}
            for r in primary_risks:
                p_name = str(r.get("pillar") or "Pillar")
                pillar_sums[p_name] = pillar_sums.get(p_name, 0.0) + float(r.get("ale") or 0.0)
            highest_pillar = max(pillar_sums, key=lambda k: pillar_sums[k])
            highest_pillar_val = pillar_sums[highest_pillar]
            
            highest_risk = max(primary_risks, key=lambda x: float(x.get("ale") or 0.0))
            highest_risk_id = str(highest_risk.get("id") or "RISK-01")
            highest_risk_cap = str(highest_risk.get("capability") or highest_risk.get("title") or highest_risk.get("finding") or "Operational Risk")
            highest_risk_ale = float(highest_risk.get("ale") or 0.0)
            highest_risk_pct = (highest_risk_ale / total_fair_ale) * 100.0 if total_fair_ale > 0 else 0.0
            
            # Format sub-amounts
            formatted_pillar_ale = format_number(
                highest_pillar_val, locale=meta_lang, decimals=0
            )
            formatted_risk_ale = format_number(
                highest_risk_ale, locale=meta_lang, decimals=0
            )
            formatted_risk_pct = format_number(
                highest_risk_pct, locale=meta_lang, decimals=1
            )

            executive_risk_summary = t(
                "fair_risk_summary_detailed",
                locale=meta_lang,
                formatted_ale=formatted_ale,
                currency=currency,
                client_name=client_name,
                num_risks=len(risks_data_list),
                highest_pillar=highest_pillar,
                formatted_pillar_ale=formatted_pillar_ale,
                highest_risk_cap=highest_risk_cap,
                highest_risk_id=highest_risk_id,
                formatted_risk_ale=formatted_risk_ale,
                highest_risk_pct=formatted_risk_pct,
            )
        else:
            executive_risk_summary = t(
                "fair_risk_summary_basic",
                locale=meta_lang,
                formatted_ale=formatted_ale,
                currency=currency,
                client_name=client_name,
            )

        # 4.1 Actuarial Quantification Framework & Mathematical Lineage Table
        from assessment_engine.adapters.compilers.strategies.actuarial_receptors import (
            ActuarialReceptorContext,
            ActuarialReceptorFactory,
        )
        from assessment_engine.domain.taxonomy.archetype_registry import (
            get_actuarial_archetype_registry,
        )

        canonical_t_id = str(ctx.get("tower_id") or blueprint_data.get("document_meta", {}).get("tower_id", "T1")).strip().upper()
        try:
            arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(canonical_t_id)
            primary_arch = arch_mapping.primary_archetype
        except (KeyError, ValueError):
            from assessment_engine.domain.taxonomy.archetype_registry import (
                LossArchetypeType,
            )
            primary_arch = LossArchetypeType.AVAILABILITY_OUTAGE

        # Resolve canonical operational archetype from domain financial profile
        from assessment_engine.domain.actuarial.financial_profile import (
            IndustryArchetype,
        )

        raw_sector = str(
            blueprint_data.get("operational_archetype")
            or ctx.get("operational_archetype")
            or blueprint_data.get("industry_vertical")
            or ctx.get("industry_vertical")
            or blueprint_data.get("industry")
            or ctx.get("industry")
            or blueprint_data.get("sub_industry")
            or ctx.get("sub_industry")
            or "DYNAMIC_EMPIRICAL_AUTONOMOUS"
        )
        resolved_archetype = IndustryArchetype.from_str(raw_sector)
        operational_archetype = resolved_archetype.value

        # Resolve delivery model organically from infrastructure telemetry or explicit declaration
        explicit_delivery = str(
            blueprint_data.get("delivery_model")
            or ctx.get("delivery_model")
            or ""
        ).upper()
        if explicit_delivery in ("CLOUD_NATIVE", "ON_PREM_HEAVY", "HYBRID", "CLOUD_NATIVE_ELASTIC", "ON_PREMISE_CORE"):
            delivery_model = explicit_delivery
        else:
            # Derive from financial ratio or canonical archetype defaults
            cloud_spend = float(blueprint_data.get("annual_cloud_spend") or ctx.get("annual_cloud_spend") or 0.0)
            hw_deprec = float(blueprint_data.get("annual_hardware_depreciation") or ctx.get("annual_hardware_depreciation") or 0.0)
            total_spend = cloud_spend + hw_deprec
            if total_spend > 0.0:
                ratio = cloud_spend / total_spend
                delivery_model = "CLOUD_NATIVE" if ratio >= 0.70 else ("ON_PREM_HEAVY" if ratio <= 0.35 else "HYBRID")
            else:
                delivery_model = (
                    "CLOUD_NATIVE"
                    if resolved_archetype == IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH
                    else ("ON_PREM_HEAVY" if resolved_archetype == IndustryArchetype.PROCESS_MANUFACTURING_OT else "HYBRID")
                )

        cloud_intensity_gamma = float(
            blueprint_data.get("cloud_intensity_gamma")
            or (0.85 if "CLOUD" in delivery_model else 0.22)
        )
        buffering_elasticity_beta = float(
            blueprint_data.get("buffering_elasticity_beta")
            or (0.95 if resolved_archetype == IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH else 0.35)
        )

        receptor_ctx = ActuarialReceptorContext(
            total_fair_ale=total_fair_ale,
            currency=currency,
            meta_lang=meta_lang,
            tower_name=str(ctx.get("tower_name") or blueprint_data.get("document_meta", {}).get("tower_name", "Infrastructure Domain")),
            client_name=client_name,
            loc_branch=loc_branch,
            primary_color_rgb=self.primary_color_rgb,
            alt_row_hex=self.alt_row_hex,
            ch4_sec1_title=t("ch4_sec1_title", locale=meta_lang),
            callout_title=t("ch4_epistemic_callout_title", locale=meta_lang),
            callout_body=t("ch4_epistemic_callout_body", locale=meta_lang),
            delivery_model=delivery_model,
            operational_archetype=operational_archetype,
            cloud_intensity_gamma=cloud_intensity_gamma,
            buffering_elasticity_beta=buffering_elasticity_beta,
        )

        strategy = ActuarialReceptorFactory.get_strategy(primary_arch)
        ast_nodes = strategy.build_ast_nodes(receptor_ctx)
        nodes.extend(ast_nodes)

        return risks_data_list, fair_lookup

    def _build_fair_risk_analysis(self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]]) -> None:
        if not risks_data_list:
            return

        vocab = ctx["vocab"]
        meta_lang = ctx["meta_lang"]
        currency = ctx["currency"]
        is_critical = ctx["is_critical"]
        blueprint_data = ctx.get("blueprint_data", {})

        fin_tel = (
            blueprint_data.get("financial_telemetry")
            or ctx.get("financial_telemetry")
            or {}
        )
        annual_rev = (
            safe_float(ctx.get("annual_revenue"))
            or safe_float(blueprint_data.get("annual_revenue"))
            or safe_float(fin_tel.get("annual_revenue"))
        )
        hourly_burn = (
            safe_float(ctx.get("hourly_downtime_cost"))
            or safe_float(ctx.get("hourly_burn_rate"))
            or safe_float(fin_tel.get("authoritative_hourly_downtime_cost"))
            or safe_float(blueprint_data.get("hourly_downtime_rate"))
        )
        dynamic_lm_bounds = compute_dynamic_lm_thresholds(
            currency=currency,
            annual_revenue=annual_rev,
            hourly_downtime_cost=hourly_burn,
            is_critical_tier=is_critical,
            locale=meta_lang,
        )
        dynamic_lm_brackets = compute_dynamic_lm_brackets(
            currency=currency,
            locale=meta_lang,
            annual_revenue=annual_rev,
            hourly_downtime_cost=hourly_burn,
            is_critical_tier=is_critical,
            precomputed_thresholds=dynamic_lm_bounds,
        )

        # Enforce strict SSOT read from additive_loss_decomposition (Zero Presentation Math Mutation)
        for r_item in risks_data_list:
            decomp = r_item.get("additive_loss_decomposition") or {}
            if decomp.get("gross_mean_sle") is not None:
                r_item["sle"] = int(round(float(decomp["gross_mean_sle"])))
            if decomp.get("mean_lef") is not None:
                r_item["lef"] = round(float(decomp["mean_lef"]), 4)
            if decomp.get("net_allocated_ale") is not None and r_item.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR":
                r_item["ale"] = int(round(float(decomp["net_allocated_ale"])))

        # 4.2 Risk Prioritization Matrix & 5x5 Heatmap
        nodes.append(
            HeadingNode(
                text=t("ch4_sec2_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(ParagraphNode(text=t("ch4_sec2_intro", locale=meta_lang), space_after=8))
        nodes.append(
            _build_heatmap_mosaic(
                risks_data_list,
                is_critical=is_critical,
                dynamic_lm_thresholds=dynamic_lm_bounds,
                locale=meta_lang,
                currency=currency,
                annual_revenue=annual_rev,
                hourly_downtime_cost=hourly_burn,
            )
        )

        # 4.2.1 Threat Event Frequency (TEF) Compact Legend (RFC 054)
        nodes.append(SpacerNode(points=6))
        nodes.append(
            ParagraphNode(
                text=f"*{t('legend_tef_caption', locale=meta_lang)}*",
                bold=True,
                font_size=8.5,
                space_before=6,
                space_after=2,
                keep_with_next=True,
            )
        )
        nodes.append(_build_tef_scale_table(vocab, meta_lang, self.alt_row_hex))
        nodes.append(SpacerNode(points=6))

        # 4.2.2 Loss Magnitude (LM) Compact Legend (RFC 054)
        nodes.append(
            ParagraphNode(
                text=f"*{t('legend_lm_caption', locale=meta_lang)}*",
                bold=True,
                font_size=8.5,
                space_before=6,
                space_after=2,
                keep_with_next=True,
            )
        )
        nodes.append(
            _build_lm_scale_table(
                vocab,
                meta_lang,
                currency,
                is_critical,
                self.alt_row_hex,
                lm_brackets=dynamic_lm_brackets,
                dynamic_lm_thresholds=dynamic_lm_bounds,
            )
        )
        nodes.append(SpacerNode(points=12))

        # 4.3 Pure AS-IS Domain Risk Concentration Profile
        nodes.append(PageBreakNode())
        nodes.append(
            HeadingNode(
                text=t("ch4_sec3_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        calibrated_domain_ale = float(ctx.get("total_fair_ale") or 0.0)
        raw_primary_total = sum(
            float(r.get("ale") or r.get("ale_val") or 0.0)
            for r in risks_data_list
            if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        )
        total_fair_ale = calibrated_domain_ale if calibrated_domain_ale > 0.0 else raw_primary_total

        # Proportional normalization via Hare-Niemeyer scaling to guarantee 100% arithmetic identity across sections
        if calibrated_domain_ale > 0.0 and raw_primary_total > 0.0 and abs(calibrated_domain_ale - raw_primary_total) > 0.50:
            scale_factor = calibrated_domain_ale / raw_primary_total
            for r in risks_data_list:
                if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR":
                    raw_val = float(r.get("ale") or r.get("ale_val") or 0.0)
                    scaled_val = round(raw_val * scale_factor, 2)
                    r["ale"] = scaled_val
                    r["ale_val"] = scaled_val

        def _get_ale(item: dict[str, Any]) -> float:
            return float(item.get("ale") or item.get("ale_val") or 0.0)

        t1_risks, t2_risks, t3_risks = _partition_risks_into_tiers(risks_data_list, total_fair_ale)

        from assessment_engine.domain.actuarial_reconciler import ActuarialReconciler
        raw_t1 = Decimal(str(round(sum(_get_ale(r) for r in t1_risks), 2)))
        raw_t2 = Decimal(str(round(sum(_get_ale(r) for r in t2_risks), 2)))
        raw_t3 = Decimal(str(round(sum(_get_ale(r) for r in t3_risks), 2)))

        target_int = int(round(total_fair_ale))
        if target_int > 0 and (raw_t1 + raw_t2 + raw_t3) > 0:
            reconciled_tiers = ActuarialReconciler.reconcile_domain_allocations(
                target_corporate_ale=target_int,
                domain_raw_exposures=[("tier1", raw_t1), ("tier2", raw_t2), ("tier3", raw_t3)],
            )
            t1_sum = float(reconciled_tiers["tier1"])
            t2_sum = float(reconciled_tiers["tier2"])
            t3_sum = float(reconciled_tiers["tier3"])
        else:
            t1_sum = float(raw_t1)
            t2_sum = float(raw_t2)
            t3_sum = float(raw_t3)
        t1_pct = int(round((t1_sum / float(target_int) * 100))) if target_int > 0 else 0

        formatted_ale_ch4 = format_number(total_fair_ale, locale=meta_lang, decimals=0)
        intro_tiers = t(
            "ch4_sec3_intro",
            locale=meta_lang,
            tower_name=str(ctx.get("tower_name") or ""),
            formatted_ale=formatted_ale_ch4,
            currency=currency,
        )
        nodes.append(ParagraphNode(text=intro_tiers, space_after=8))

        yr_suffix = t("per_year_suffix", locale=meta_lang)
        tier_header_bg = self.primary_color_hex

        canonical_t_id = str(ctx.get("tower_id") or blueprint_data.get("document_meta", {}).get("tower_id", "T1")).strip().upper()
        from assessment_engine.domain.taxonomy.archetype_registry import (
            LossArchetypeType,
            get_actuarial_archetype_registry,
        )
        try:
            arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(canonical_t_id)
            primary_arch = arch_mapping.primary_archetype
        except (KeyError, ValueError):
            primary_arch = LossArchetypeType.AVAILABILITY_OUTAGE

        arch_suffix = primary_arch.value.lower()
        t1_fallback_focus = t(f"ch4_tier1_focus_{arch_suffix}", locale=meta_lang, default=t("ch4_tier1_focus", locale=meta_lang))
        t2_fallback_focus = t(f"ch4_tier2_focus_{arch_suffix}", locale=meta_lang, default=t("ch4_tier2_focus", locale=meta_lang))
        t3_fallback_focus = t(f"ch4_tier3_focus_{arch_suffix}", locale=meta_lang, default=t("ch4_tier3_focus", locale=meta_lang))

        def _get_tier_focus_summary(tier_risks_list: list[dict[str, Any]], fallback_str: str) -> str:
            if not tier_risks_list:
                return fallback_str
            caps = []
            for r in tier_risks_list:
                c_name = str(r.get("capability") or r.get("title") or "").strip()
                if c_name and c_name not in caps:
                    caps.append(c_name)
            if caps:
                return ", ".join(caps[:3]) + ("." if len(caps) <= 3 else "...")
            return fallback_str

        t1_focus_str = _get_tier_focus_summary(t1_risks, t1_fallback_focus)
        t2_focus_str = _get_tier_focus_summary(t2_risks, t2_fallback_focus)
        t3_focus_str = _get_tier_focus_summary(t3_risks, t3_fallback_focus)

        # Dual-Ledger Governance Architecture: Ledger A (Stochastic ALE) vs Ledger B (Deterministic OpEx)
        ledger_a_risks = [
            r for r in risks_data_list
            if not r.get("is_deterministic")
            and (r.get("additive_loss_decomposition") or {}).get("ledger_type") != "LEDGER_B_DETERMINISTIC_OPEX"
            and r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        ]
        ledger_b_risks = [
            r for r in risks_data_list
            if (r.get("is_deterministic")
                or (r.get("additive_loss_decomposition") or {}).get("ledger_type") == "LEDGER_B_DETERMINISTIC_OPEX")
            and r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        ]
        ledger_a_sum = sum(float(r.get("ale") or r.get("ale_val") or 0.0) for r in ledger_a_risks)
        ledger_b_sum = sum(float(r.get("ale") or r.get("ale_val") or 0.0) for r in ledger_b_risks)
        is_es_mat = str(meta_lang).startswith("es")

        dual_ledger_rows = [
            TableRowNode(
                cells=[
                    CellNode(
                        text="**Libro Contable / Horizonte Financiero**" if is_es_mat else "**Accounting Ledger / Financial Horizon**",
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=[255, 255, 255],
                        font_size=8.5,
                        align="LEFT",
                    ),
                    CellNode(
                        text="**Exposición Anual**" if is_es_mat else "**Annual Exposure**",
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=[255, 255, 255],
                        font_size=8.5,
                        align="CENTER",
                    ),
                    CellNode(
                        text="**Destino en Estados Financieros (IFRS / GAAP)**" if is_es_mat else "**Financial Statement Impact (IFRS / GAAP)**",
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=[255, 255, 255],
                        font_size=8.5,
                        align="LEFT",
                    ),
                ],
                is_header=True,
            ),
            TableRowNode(
                cells=[
                    CellNode(
                        text="**Libro A: Riesgo Operacional Estocástico** (P < 1.0)" if is_es_mat else "**Ledger A: Stochastic Operational Risk** (P < 1.0)",
                        bg_color="F8FAFC",
                        font_size=8.5,
                    ),
                    CellNode(
                        text=f"**{format_number(ledger_a_sum, locale=meta_lang, decimals=0)} {currency}{yr_suffix}**",
                        bg_color="F8FAFC",
                        align="CENTER",
                        font_size=8.5,
                    ),
                    CellNode(
                        text="Reserva de Capital Económico y Pérdida Máxima Probable (Balance)" if is_es_mat else "Economic Capital Reserve & Probable Maximum Loss (Balance Sheet)",
                        bg_color="F8FAFC",
                        font_size=8.0,
                    ),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(
                        text="**Libro B: Ineficiencia OpEx y Toil Recurrente** (P = 1.0)" if is_es_mat else "**Ledger B: Deterministic OpEx & Toil** (P = 1.0)",
                        bg_color="F1F5F9",
                        font_size=8.5,
                    ),
                    CellNode(
                        text=f"**{format_number(ledger_b_sum, locale=meta_lang, decimals=0)} {currency}{yr_suffix}**",
                        bg_color="F1F5F9",
                        align="CENTER",
                        font_size=8.5,
                    ),
                    CellNode(
                        text="Sobrecoste Recurrente en Cuenta de Resultados (EBITDA Drag)" if is_es_mat else "Recurring Operating Expenditure Leakage (EBITDA Drag)",
                        bg_color="F1F5F9",
                        font_size=8.0,
                    ),
                ]
            ),
        ]
        # Dual Ledger table removed for clarity
        nodes.append(SpacerNode(points=10))

        # Two-Tier Financial Reconciliation Bridge (Red Team Rule 4 & DEF-02)
        # Calculates the direct standalone sum of the risk cards to guarantee 100% mathematical closure
        total_eval_risks = [
            r for r in risks_data_list
            if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        ]
        card_direct_sum = sum(
            round(float(r.get("sle") or 0.0) * float(f"{float(r.get('lef') or 0.0):.2f}"))
            if not r.get("is_deterministic") and float(r.get("sle") or 0.0) > 0.0 and float(r.get("lef") or 0.0) > 0.0
            else float(r.get("ale") or r.get("ale_val") or 0.0)
            for r in total_eval_risks
        )
        simultaneity_delta = round(float(total_fair_ale) - float(card_direct_sum))

        tier_summary_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=t("ch4_tier_table_col_tier", locale=meta_lang), bold=True, bg_color=tier_header_bg, text_color_rgb=[255, 255, 255]),
                    CellNode(text=t("ch4_tier_table_col_count", locale=meta_lang), bold=True, bg_color=tier_header_bg, text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=t("ch4_tier_table_col_ale", locale=meta_lang), bold=True, bg_color=tier_header_bg, text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=t("ch4_tier_table_col_focus", locale=meta_lang), bold=True, bg_color=tier_header_bg, text_color_rgb=[255, 255, 255]),
                ],
                is_header=True,
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("ch4_tier1_label", locale=meta_lang), bold=True, bg_color="FADBD8", font_size=8.5),
                    CellNode(text=str(len(t1_risks)), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{format_number(t1_sum, locale=meta_lang, decimals=0)} {currency}{yr_suffix} ({t1_pct}%)", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t1_focus_str, bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("ch4_tier2_label", locale=meta_lang), bold=True, bg_color="FCF3CF", font_size=8.5),
                    CellNode(text=str(len(t2_risks)), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{format_number(t2_sum, locale=meta_lang, decimals=0)} {currency}{yr_suffix}", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t2_focus_str, bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("ch4_tier3_label", locale=meta_lang), bold=True, bg_color="D5F5E3", font_size=8.5),
                    CellNode(text=str(len(t3_risks)), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{format_number(t3_sum, locale=meta_lang, decimals=0)} {currency}{yr_suffix}", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t3_focus_str, bg_color="FFFFFF", font_size=8.0),
                ]
            ),
        ]

        # Add explicit closing rows for two-tier reconciliation if simultaneity delta exists
        is_es_rpt = str(meta_lang).startswith("es")
        if abs(simultaneity_delta) > 5.0 and card_direct_sum > 0:
            adj_pct = round((simultaneity_delta / card_direct_sum) * 100.0, 1)
            tier_summary_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(
                            text="**Subtotal Exposición Directa (Suma Fichas 4.4)**" if is_es_rpt else "**Direct Exposure Subtotal (Cards Sum 4.4)**",
                            bold=True, bg_color="F8FAFC", font_size=8.5
                        ),
                        CellNode(text=f"**{len(total_eval_risks)}**", align="CENTER", bg_color="F8FAFC", font_size=8.5, bold=True),
                        CellNode(text=f"**{format_number(card_direct_sum, locale=meta_lang, decimals=0)} {currency}{yr_suffix}**", align="CENTER", bg_color="F8FAFC", font_size=8.5, bold=True),
                        CellNode(text="Base de riesgo directo evaluada por separado" if is_es_rpt else "Direct standalone risk base evaluated in isolation", bg_color="F8FAFC", font_size=8.0, italic=True),
                    ]
                )
            )
            tier_summary_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(
                            text="*Corrección por Paradas Solapadas y Dependencias IT*" if is_es_rpt else "*Adjustment for Overlapping Downtime & IT Dependencies*",
                            bg_color="F8FAFC", font_size=8.5, italic=True
                        ),
                        CellNode(text="—", align="CENTER", bg_color="F8FAFC", font_size=8.5),
                        CellNode(text=f"*{format_number(simultaneity_delta, locale=meta_lang, decimals=0)} {currency}{yr_suffix} ({adj_pct:+.1f}%)*", align="CENTER", bg_color="F8FAFC", font_size=8.5, italic=True),
                        CellNode(text="Evita duplicar horas de parada fabril en fallos simultáneos" if is_es_rpt else "Avoids double-counting plant downtime during concurrent outages", bg_color="F8FAFC", font_size=8.0, italic=True),
                    ]
                )
            )
            tier_summary_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(
                            text="**EXPOSICIÓN NETA CONSOLIDADA (Tomo 1 / Cartera)**" if is_es_rpt else "**CONSOLIDATED NET EXPOSURE (Volume 1 / Portfolio)**",
                            bold=True, bg_color="EAECEE", font_size=8.5
                        ),
                        CellNode(text=f"**{len(total_eval_risks)}**", align="CENTER", bg_color="EAECEE", font_size=8.5, bold=True),
                        CellNode(text=f"**{format_number(total_fair_ale, locale=meta_lang, decimals=0)} {currency}{yr_suffix}**", align="CENTER", bg_color="EAECEE", font_size=8.5, bold=True),
                        CellNode(text="Presupuesto de riesgo neto asignado en balance" if is_es_rpt else "Net risk budget allocated on balance sheet", bg_color="EAECEE", font_size=8.0, bold=True),
                    ]
                )
            )
        else:
            tier_summary_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(
                            text="**TOTAL EXPOSICIÓN ANUALIZADA (ALE)**" if is_es_rpt else "**TOTAL ANNUALIZED EXPOSURE (ALE)**",
                            bold=True, bg_color="EAECEE", font_size=8.5
                        ),
                        CellNode(text=f"**{len(total_eval_risks)}**", align="CENTER", bg_color="EAECEE", font_size=8.5, bold=True),
                        CellNode(text=f"**{format_number(total_fair_ale, locale=meta_lang, decimals=0)} {currency}{yr_suffix}**", align="CENTER", bg_color="EAECEE", font_size=8.5, bold=True),
                        CellNode(text="Costes y riesgos acumulados directamente" if is_es_rpt else "Directly accumulated costs and risks", bg_color="EAECEE", font_size=8.0, bold=True),
                    ]
                )
            )
        nodes.append(TableNode(rows=tier_summary_rows, autofit=True, col_widths=[0.28, 0.08, 0.24, 0.40]))
        nodes.append(SpacerNode(points=10))

        # 4.3.1 P90 Tail Risk Disaster Scenario Callout (RFC 058)
        from assessment_engine.domain.actuarial.downtime_calibrator import (
            OperationalTailRiskEngine,
        )
        blueprint_data = ctx.get("blueprint_data") or {}
        fin_telemetry = blueprint_data.get("financial_telemetry") or {}
        canonical_t_id = str(ctx.get("tower_id") or blueprint_data.get("document_meta", {}).get("tower_id", "T1")).strip().upper()
        from assessment_engine.domain.taxonomy.archetype_registry import (
            LossArchetypeType,
            get_actuarial_archetype_registry,
        )
        try:
            arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(canonical_t_id)
            primary_arch = arch_mapping.primary_archetype
        except (KeyError, ValueError):
            primary_arch = LossArchetypeType.AVAILABILITY_OUTAGE
        hourly_rate = float(
            fin_telemetry.get("authoritative_hourly_downtime_cost")
            or blueprint_data.get("hourly_downtime_rate")
            or blueprint_data.get("hourly_burn_rate")
            or 0.0
        )
        if hourly_rate <= 0.0 and total_fair_ale > 0.0:
            raw_div = safe_float(blueprint_data.get("annual_downtime_divisor"), locale=meta_lang, allow_zero=True) or 0.0
            if raw_div > 0.0:
                hourly_rate = total_fair_ale / raw_div

        loc_branch = self.loc_branch

        ceiling_hours = float(
            fin_telemetry.get("operational_recovery_ceiling_hours")
            or blueprint_data.get("operational_recovery_ceiling_hours")
            or OperationalTailRiskEngine.DEFAULT_RECOVERY_CEILING_HOURS
        )
        total_p90_val = float(
            blueprint_data.get("total_fair_p90")
            or blueprint_data.get("fair_risk_profile", {}).get("p90_ale")
            or blueprint_data.get("tail_risk_p90")
            or total_fair_ale
        )
        tail_decomp = OperationalTailRiskEngine.decompose_tail_risk(
            expected_annual_loss=total_fair_ale,
            var_90_total=total_p90_val,
            composite_hourly_rate=hourly_rate,
            operational_recovery_ceiling_hours=ceiling_hours,
        )
        p90_rec_hours_str = format_number(tail_decomp.capped_operational_p90_hours, locale=meta_lang, decimals=1)
        closed_form_p90_total = tail_decomp.primary_operational_p90_loss + tail_decomp.secondary_tail_p90_loss
        p90_contingency_str = format_currency(closed_form_p90_total, currency_symbol=currency, locale=meta_lang, decimals=0)
        direct_stoppage_str = format_currency(tail_decomp.primary_operational_p90_loss, currency_symbol=currency, locale=meta_lang, decimals=0)
        secondary_spend_str = format_currency(tail_decomp.secondary_tail_p90_loss, currency_symbol=currency, locale=meta_lang, decimals=0)

        dynamic_trigger = str(
            blueprint_data.get("compound_failure_trigger")
            or blueprint_data.get("p90_trigger")
            or ""
        ).strip()
        triggers_map = loc_branch.get("tower_p90_triggers", {})
        trigger_text = dynamic_trigger if dynamic_trigger else (triggers_map.get(canonical_t_id) or triggers_map.get("DEFAULT", ""))

        fmt_kwargs = {
            "compound_failure_trigger": trigger_text,
            "p90_recovery_hours": p90_rec_hours_str,
            "p90_total_contingency": p90_contingency_str,
            "direct_stoppage_loss": direct_stoppage_str,
            "secondary_disaster_spend": secondary_spend_str,
        }

        p90_heading = t("p90_callout_title", locale=meta_lang)
        nodes.append(SpacerNode(points=12))
        nodes.append(
            HeadingNode(
                text=p90_heading,
                level=3,
                primary_color_rgb=self.primary_color_rgb,
                keep_with_next=True,
            )
        )
        if primary_arch == LossArchetypeType.CAPITAL_INEFFICIENCY:
            p1_text = t("p90_callout_finops_p1", locale=meta_lang, trigger_text=trigger_text)
            p2_text = t("p90_callout_finops_p2", locale=meta_lang, p90_rec_hours_str=p90_rec_hours_str)
            p3_text = t(
                "p90_callout_finops_p3",
                locale=meta_lang,
                p90_contingency_str=p90_contingency_str,
                direct_stoppage_str=direct_stoppage_str,
                secondary_spend_str=secondary_spend_str,
            )
        elif canonical_t_id == "T10":
            doc_meta = (
                blueprint_data.get("document_meta", {})
                if isinstance(blueprint_data.get("document_meta"), dict)
                else {}
            )
            industry = str(
                blueprint_data.get("industry")
                or doc_meta.get("industry")
                or blueprint_data.get("industry_vertical")
                or ""
            ).lower()
            is_plant = any(
                k in industry
                for k in ("cement", "manufacturing", "logistics", "heavy", "industrial")
            )
            p1_text = t("p90_callout_p1", locale=meta_lang, **fmt_kwargs)
            p2_text = (
                t(
                    "p90_callout_plant_p2",
                    locale=meta_lang,
                    p90_rec_hours_str=p90_rec_hours_str,
                    default=t("p90_callout_p2", locale=meta_lang, **fmt_kwargs),
                )
                if is_plant
                else t("p90_callout_p2", locale=meta_lang, **fmt_kwargs)
            )
            p3_text = t("p90_callout_p3", locale=meta_lang, **fmt_kwargs)
        else:
            p1_text = t("p90_callout_p1", locale=meta_lang, **fmt_kwargs)
            p2_text = t("p90_callout_p2", locale=meta_lang, **fmt_kwargs)
            p3_text = t("p90_callout_p3", locale=meta_lang, **fmt_kwargs)

        from assessment_engine.infrastructure.localization import (
            restore_locale_diacritics,
        )
        nodes.append(ParagraphNode(text=restore_locale_diacritics(p1_text, meta_lang), font_size=10.0, space_after=6))
        nodes.append(ParagraphNode(text=restore_locale_diacritics(p2_text, meta_lang), font_size=10.0, space_after=6))
        nodes.append(ParagraphNode(text=restore_locale_diacritics(p3_text, meta_lang), font_size=10.0, space_after=14))

    def _build_detailed_findings_log(
        self,
        ctx: dict[str, Any],
        nodes: List[Any],
        risks_data_list: list[dict[str, Any]],
        fair_lookup: dict[str, Any],
    ) -> None:
        vocab = ctx["vocab"]
        currency = ctx["currency"]
        meta_lang = ctx["meta_lang"]
        client_name = str(ctx.get("client_name") or "CLIENT")
        blueprint_data = ctx.get("blueprint_data", {})

        # Deduplication invariant: Only primary custodian risks contribute to financial exposure
        primary_risks_total = sum(
            float(r.get("ale") or r.get("ale_val") or 0.0)
            for r in risks_data_list
            if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        )
        total_fair_ale = primary_risks_total if primary_risks_total > 0.0 else float(ctx.get("total_fair_ale") or 0.0)

        if not risks_data_list:
            return

        nodes.append(
            HeadingNode(
                text=t("ch4_sec4_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("ch4_sec4_intro", locale=meta_lang, risk_count=len(risks_data_list)),
                space_after=12,
            )
        )

        # 1. Global ranking: primary risks ranked by ALE descending, tangential risks appended thereafter
        sorted_risks = sorted(
            risks_data_list,
            key=lambda x: (
                x.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR",
                float(x.get("ale") or x.get("ale_val") or 0.0),
            ),
            reverse=True,
        )
        for rank_idx, r in enumerate(sorted_risks, start=1):
            r["global_rank"] = rank_idx
            r_ale = float(r.get("ale") or r.get("ale_val") or 0.0)
            r["share_pct"] = (r_ale / total_fair_ale * 100.0) if total_fair_ale > 0 else 0.0

        # 2. Partition into the 3 Strategic Portfolios (Identical unified partitioning across 4.3 and 4.4)
        t1_risks, t2_risks, t3_risks = _partition_risks_into_tiers(risks_data_list, total_fair_ale)

        portfolios = [
            (1, t("tier_1_catalog_title", locale=meta_lang), t1_risks),
            (2, t("tier_2_catalog_title", locale=meta_lang), t2_risks),
            (3, t("tier_3_catalog_title", locale=meta_lang), t3_risks),
        ]

        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()

        for t_idx, t_title, t_items in portfolios:
            if not t_items:
                continue

            subtotal_ale = sum(
                float(r.get("ale") or r.get("ale_val") or 0.0)
                for r in t_items
                if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
            )
            subtotal_pct = int(round(subtotal_ale / total_fair_ale * 100.0)) if total_fair_ale > 0 else 0
            formatted_subtotal = format_currency(
                subtotal_ale, currency_symbol=currency, locale=meta_lang, decimals=0
            )

            # Portfolio Tier Header
            nodes.append(SpacerNode(points=10))
            nodes.append(
                HeadingNode(
                    text=t_title,
                    level=3,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )
            nodes.append(
                ParagraphNode(
                    text=t(
                        "tier_subtotal_badge",
                        locale=meta_lang,
                        subtotal_ale=formatted_subtotal,
                        pct=subtotal_pct,
                    ),
                    bold=True,
                    italic=True,
                    font_size=9.5,
                    space_after=8,
                )
            )

            for hc in t_items:
                raw_pname = hc.get("pillar", "Pillar")
                p_name = resolver.resolve_pillar_by_any_reference(
                    raw_pname, default=raw_pname, locale=meta_lang
                )

                card_table = self._build_risk_mini_infographic_card(
                    ctx=ctx,
                    hc=hc,
                    t_idx=t_idx,
                    p_name=p_name,
                    total_fair_ale=total_fair_ale,
                )
                nodes.append(card_table)
                nodes.append(SpacerNode(points=12))

    def _build_risk_mini_infographic_card(
        self,
        ctx: dict[str, Any],
        hc: dict[str, Any],
        t_idx: int,
        p_name: str,
        total_fair_ale: float,
    ) -> TableNode:
        """Constructs an executive Open FAIR Mini-Infographic Risk Card AST TableNode."""
        meta_lang = ctx["meta_lang"]
        currency = ctx["currency"]
        blueprint_data = ctx.get("blueprint_data", {})

        raw_id = str(hc.get("id") or "RSK-01").strip()
        r_id = re.sub(r"[^A-Za-z0-9_.\-]", "-", raw_id) or "RSK-01"
        raw_cap = str(hc.get("capability") or "Capability").strip()
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()
        r_cap = resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=meta_lang)
        global_rank = hc.get("global_rank", 1)
        share_pct = float(hc.get("share_pct") or 0.0)

        # In-Place Compact Governance Stub (SR 11-7 Contiguous Index Bijection)
        if hc.get("quantification_status") == "UNQUANTIFIED_MATURITY_GAP":
            card_id = raw_id
            display_title = str(hc.get("title") or r_cap or p_name)
            finding_text = str(hc.get("finding") or "")
            risk_text = str(hc.get("business_risk") or "")
            is_es = str(meta_lang).startswith("es")
            status_badge = (
                "CONTROL DE GOBERNANZA (CUESTIONARIO)"
                if is_es
                else "GOVERNANCE CONTROL GAP (SURVEY)"
            )
            desc_text = (
                f"{finding_text}\n\n_{risk_text}_"
                if risk_text and risk_text != finding_text
                else finding_text
            )
            impact_stub = (
                "Brecha de madurez metodológica detectada en evaluación CMMI. "
                "Requiere telemetría operativa para cuantificación actuarial estocástica (Exposición directa asignada: 0 €/año)."
                if is_es
                else "Governance maturity gap identified in CMMI survey. "
                "Requires field telemetry for stochastic actuarial quantification (Direct exposure assigned: 0 €/yr)."
            )

            return TableNode(
                rows=[
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=f"**[{card_id}] {display_title}**",
                                font_size=9.0,
                                bg_color="F1F5F9",
                                bold=True,
                                grid_span=8,
                                align="LEFT",
                            ),
                            CellNode(
                                text=f"**{status_badge}**",
                                font_size=8.0,
                                bg_color="E2E8F0",
                                grid_span=4,
                                align="RIGHT",
                            ),
                        ],
                        cant_split=True,
                    ),
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=f"**{t('risk_card_vulnerability_label', locale=meta_lang)}:**\n{desc_text}",
                                font_size=8.0,
                                bg_color="FFFFFF",
                                grid_span=8,
                                border_left_color="94A3B8",
                                border_left_size=24,
                                align="LEFT",
                            ),
                            CellNode(
                                text=f"**{t('risk_card_operational_impact_label', locale=meta_lang)}:**\n{impact_stub}",
                                font_size=8.0,
                                bg_color="FFFFFF",
                                grid_span=4,
                                border_left_color="CBD5E1",
                                border_left_size=24,
                                align="LEFT",
                            ),
                        ],
                        cant_split=True,
                    ),
                ],
                cant_split=True,
            )

        # 1. Authoritative Actuarial Reconciliation & Scale Calibration
        authoritative_ale = float(hc.get("intrinsic_ale") or hc.get("ale") or hc.get("ale_val") or 0.0)
        raw_tef = float(hc.get("tef") or 1.0)
        raw_lm = float(hc.get("lm") or 1.0)

        canonical_t_id = str(ctx.get("tower_id") or blueprint_data.get("document_meta", {}).get("tower_id", "T1")).strip().upper()
        from assessment_engine.domain.taxonomy.archetype_registry import (
            LossArchetypeType,
            get_actuarial_archetype_registry,
        )
        try:
            arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(canonical_t_id)
            primary_arch = arch_mapping.primary_archetype
        except (KeyError, ValueError):
            primary_arch = LossArchetypeType.AVAILABILITY_OUTAGE

        fin_telemetry = blueprint_data.get("financial_telemetry") or {}
        tower_rate = (
            fin_telemetry.get("authoritative_hourly_downtime_cost")
            or blueprint_data.get("hourly_burn_rate")
            or blueprint_data.get("hourly_downtime_rate")
        )
        hourly_rate = float(
            tower_rate
            or (ctx.get("financial_telemetry") or {}).get("authoritative_hourly_downtime_cost")
            or ctx.get("authoritative_hourly_downtime_cost")
            or (total_fair_ale / 8760.0 if total_fair_ale > 0 else 0.0)
        )

        if t_idx == 1:
            coupling_regime = CouplingRegime.TIGHT
            coupling_factor = 1.5
            alpha = 0.70
        elif t_idx == 2:
            coupling_regime = CouplingRegime.MODERATE
            coupling_factor = 1.2
            alpha = 0.40
        else:
            coupling_regime = CouplingRegime.LOOSE
            coupling_factor = 1.0
            alpha = 0.20

        vec = hc.get("actuarial_input_vector") or {}
        vec_outputs = vec.get("outputs") or {}
        vec_inputs = vec.get("inputs") or {}

        canonical_ale = float(
            hc.get("ale")
            or hc.get("ale_val")
            or vec_outputs.get("portfolio_allocated_ale")
            or hc.get("fair_ale_score")
            or hc.get("intrinsic_ale")
            or 0.0
        )
        decomp = hc.get("additive_loss_decomposition") or {}
        canonical_sle = float(hc.get("sle") or decomp.get("gross_mean_sle") or vec_outputs.get("mean_sle") or 0.0)
        canonical_lef = float(hc.get("lef") or decomp.get("mean_lef") or vec_outputs.get("mean_lef") or (raw_tef if raw_tef <= 10.0 else 0.20))
        if decomp and decomp.get("rto_hours") is not None:
            eff_recovery_hours = float(decomp["rto_hours"])
        else:
            eff_recovery_hours = float(
                (vec_inputs.get("rto_hours_mode") or {}).get("effective_value")
                or hc.get("recovery_time_hours")
                or (raw_lm * 0.85)
                or 3.5
            )

        if decomp and decomp.get("hourly_burn_rate") is not None:
            domain_hourly_rate = float(decomp["hourly_burn_rate"])
        elif primary_arch == LossArchetypeType.PRODUCTIVITY_TOIL:
            domain_hourly_rate = 65.0
        else:
            domain_hourly_rate = max(round(hourly_rate * alpha, 2), 1.0)
        if decomp and decomp.get("gross_mean_sle"):
            primary_downtime_loss = int(decomp.get("expected_downtime_loss", 0))
            repl_cost_num = int(decomp.get("expected_replacement_cost", 0))
            sec_weighted_loss = int(decomp.get("expected_secondary_loss", 0))
            reconciled_sle = int(decomp["gross_mean_sle"])
            canonical_ale = float(decomp["net_allocated_ale"])
        else:
            primary_downtime_loss = round(eff_recovery_hours * domain_hourly_rate)
            repl_cost_num = round(
                float(
                    (vec_inputs.get("direct_replacement_cost") or {}).get(
                        "effective_value"
                    )
                    or hc.get("direct_replacement_cost")
                    or 0.0
                )
            )
            raw_sec_mean = float(
                (vec_inputs.get("secondary_loss_mean") or {}).get(
                    "effective_value"
                )
                or hc.get("secondary_loss_mean")
                or 0.0
            )
            sec_weighted_loss = (
                round(0.10 * raw_sec_mean) if raw_sec_mean > 0 else 0
            )
            reconciled_sle = (
                primary_downtime_loss + repl_cost_num + sec_weighted_loss
            )

        # In PRODUCTIVITY_TOIL, continuous toil labor must NOT explode into millions of euros
        if primary_arch == LossArchetypeType.PRODUCTIVITY_TOIL and (
            eff_recovery_hours >= 100.0 or reconciled_sle > 100000.0
        ):
            reconciled_sle = round(eff_recovery_hours * domain_hourly_rate)

        sle_val = max(Decimal("0.00"), Decimal(str(reconciled_sle)))

        actuarial_input = FairActuarialInput(
            loss_event_frequency_annual=round(max(0.0001, canonical_lef), 6),
            single_loss_magnitude_base=sle_val,
            operational_coupling_factor=coupling_factor,
            coupling_regime=coupling_regime,
            downtime_hours_mean=max(0.1, round(eff_recovery_hours, 1)),
            hourly_operational_impact=Decimal(str(round(domain_hourly_rate, 2))),
        )

        ownership_type = str(hc.get("ownership_type") or "PRIMARY_CUSTODIAN")
        primary_risk_ref = hc.get("primary_risk_ref")
        contributing_towers = hc.get("contributing_towers") or []

        class RenderMetrics:
            def __init__(self, ale: float, sle: float, lef: float, sev: str, is_dedup: bool = False):
                self.annualized_loss_expectancy = ale
                self.effective_sle = sle
                self.loss_event_frequency = lef
                self.severity_tier = sev
                self.is_deduplicated = is_dedup
                self.return_period_years = round(1.0 / max(0.0001, lef), 1) if lef > 0 else 10.0

        metrics = RenderMetrics(
            ale=canonical_ale,
            sle=float(reconciled_sle),
            lef=canonical_lef,
            sev=str(hc.get("severity") or "MEDIUM").upper(),
            is_dedup=bool(primary_risk_ref and ownership_type == "CONTRIBUTING_FACTOR"),
        )

        formatted_ale = format_currency(
            float(metrics.annualized_loss_expectancy),
            currency_symbol=currency,
            locale=meta_lang,
            decimals=0,
        )
        formatted_sle = format_currency(
            float(reconciled_sle),
            currency_symbol=currency,
            locale=meta_lang,
            decimals=0,
        )
        return_period_str = t(
            "risk_card_return_period_fmt",
            locale=meta_lang,
            years=metrics.return_period_years,
        )
        coupling_str = t(
            f"risk_card_coupling_{coupling_regime.value.lower()}",
            locale=meta_lang,
        )
        sev_key = (
            "moderate"
            if metrics.severity_tier.lower() in ("medium", "moderate")
            else metrics.severity_tier.lower()
        )
        sev_badge_text = t(
            f"risk_card_severity_{sev_key}",
            locale=meta_lang,
            default=metrics.severity_tier.upper(),
        )

        severity_colors = {
            "CRITICAL": "DC2626",
            "HIGH": "B45309",
            "ELEVATED": "1D4ED8",
            "MODERATE": "4B5563",
        }
        severity_bg_hex = severity_colors.get(metrics.severity_tier, "B45309")

        # 2. Causal Bow-Tie 3-Step Scenario Construction
        raw_threat = hc.get("initiating_threat") or hc.get("threat_mechanism") or hc.get("causal_risk_title")
        if raw_threat:
            threat_txt = str(raw_threat).strip()
        else:
            threat_txt = t("risk_card_default_threat", locale=meta_lang)

        raw_vuln = hc.get("technical_failure_mechanism") or hc.get("control_vulnerability") or hc.get("finding")
        vuln_txt = str(raw_vuln or "").strip() or t("risk_card_default_vulnerability", locale=meta_lang)

        raw_impact = str(hc.get("primary_impact") or hc.get("business_risk") or hc.get("operational_impact") or "").strip()
        def_marker = t("defensibility_formula_marker", locale=meta_lang)
        if def_marker and def_marker in raw_impact:
            impact_clean = raw_impact.split(def_marker)[0].strip()
        else:
            impact_clean = raw_impact

        from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
            _extract_verified_business_risk,
            _is_severity_enum_token,
        )

        # Compiler Invariant Gate: Enforce that narrative slots never render bare ordinal enums
        if not impact_clean or _is_severity_enum_token(impact_clean, meta_lang) or len(impact_clean.split()) < 4:
            logger.warning(
                "AST_CONTRACT_VIOLATION: Risk finding '%s' arrived with non-narrative impact token '%s'. Synthesizing verified operational narrative.",
                hc.get("id") or hc.get("node_id", "UNKNOWN"),
                impact_clean,
            )
            impact_clean = _extract_verified_business_risk(hc, p_name, meta_lang)

        impact_txt = impact_clean.rstrip(".!?") + "."

        raw_mitigation = hc.get("remediation_architecture") or hc.get("mitigation_directive") or hc.get("remediation")
        if raw_mitigation:
            directive_txt = str(raw_mitigation).strip()
        else:
            directive_txt = t("risk_card_default_mitigation", locale=meta_lang)

        evidence_txt = str(hc.get("evidence") or "").strip()

        # Restore official grammatical diacritics for target locale (RFC 055)
        from assessment_engine.infrastructure.localization import (
            restore_locale_diacritics,
        )
        r_cap = restore_locale_diacritics(r_cap, meta_lang)
        threat_txt = restore_locale_diacritics(threat_txt, meta_lang)
        vuln_txt = restore_locale_diacritics(vuln_txt, meta_lang)
        impact_txt = restore_locale_diacritics(impact_txt, meta_lang)
        directive_txt = restore_locale_diacritics(directive_txt, meta_lang)

        # 3. Domain Model Schema Validation
        bow_tie = CausalBowTie(
            initiating_threat_event=threat_txt,
            control_vulnerability_gap=vuln_txt,
            primary_asset_impact=impact_txt,
        )
        loss_event = ConditionalLossEvent(
            event_id=r_id,
            title=r_cap,
            domain_category=p_name,
            currency_code=currency,
            causal_chain=bow_tie,
            actuarial_input=actuarial_input,
            mitigation_directive=directive_txt,
            audit_evidence=evidence_txt or None,
            ownership_type=ownership_type,
            primary_risk_ref=primary_risk_ref,
            contributing_towers=contributing_towers,
        )

        if evidence_txt:
            ev_lbl = t("audit_evidence_label", locale=meta_lang)
            directive_txt += f"\n{ev_lbl}: \"{evidence_txt}\""

        lef_formatted = format_number(metrics.loss_event_frequency, locale=meta_lang, decimals=2)
        ev_unit = t("event_frequency_unit", locale=meta_lang)
        tier_prefix = t("portfolio_tier_prefix", locale=meta_lang)

        is_deterministic = bool(
            hc.get("is_deterministic")
            or decomp.get("is_deterministic")
            or hc.get("ledger_type") == "LEDGER_B_DETERMINISTIC_OPEX"
            or decomp.get("ledger_type") == "LEDGER_B_DETERMINISTIC_OPEX"
            or str(hc.get("loss_physics") or "").upper() == "FINOPS_RESOURCE_WASTE"
        )

        # Apply specific styling if this is a tangential contributor or deterministic OpEx
        if metrics.is_deduplicated:
            header_bg = "F1F5F9"
            header_text = [71, 85, 105]
            sev_badge_text = t("risk_card_ownership_badge_tangential", locale=meta_lang)
            sev_badge_bg = "64748B"
        elif is_deterministic:
            header_bg = "1B263B"
            header_text = [255, 255, 255]
            sev_badge_text = t("finops_optimization_badge", locale=meta_lang)
            sev_badge_bg = "0D9488"
        else:
            header_bg = "1B263B"
            header_text = [255, 255, 255]
            sev_badge_bg = severity_bg_hex

        # Canonical LEF from simulation outputs (no artificial mutation in presentation)
        ale_num = float(metrics.annualized_loss_expectancy)
        calibrated_lef = canonical_lef

        # Calculate human-readable return period / frequency (Adaptive Significant Digits)
        if primary_arch == LossArchetypeType.PRODUCTIVITY_TOIL:
            if ale_num > 0 and reconciled_sle > 0:
                est_annual_events = max(1, int(round(ale_num / float(reconciled_sle))))
            else:
                est_annual_events = max(1, int(round(raw_tef * 6.0)))
            ev_str = format_number(float(est_annual_events), locale=meta_lang, decimals=0)
            freq_display = t("kpi_frequency_value_annual", locale=meta_lang, events=ev_str)
            displayed_mult_freq = float(est_annual_events)
        elif calibrated_lef <= 0:
            ev_str = format_number(0.1, locale=meta_lang, decimals=1)
            freq_display = t("kpi_frequency_value_annual", locale=meta_lang, events=ev_str)
            displayed_mult_freq = 0.1
        elif calibrated_lef < 0.1:
            ev_str = format_number(calibrated_lef, locale=meta_lang, decimals=3)
            rec_years = round(1.0 / calibrated_lef, 1)
            years_str = format_number(rec_years, locale=meta_lang, decimals=1)
            freq_display = f"{t('kpi_frequency_value_years', locale=meta_lang, years=years_str)} ({ev_str}/{t('year_lbl', locale=meta_lang)})"
            displayed_mult_freq = float(f"{calibrated_lef:.3f}")
        elif calibrated_lef < 1.0:
            ev_str = format_number(calibrated_lef, locale=meta_lang, decimals=2)
            rec_years = round(1.0 / calibrated_lef, 1)
            years_str = format_number(rec_years, locale=meta_lang, decimals=1)
            freq_display = f"{t('kpi_frequency_value_years', locale=meta_lang, years=years_str)} ({ev_str}/{t('year_lbl', locale=meta_lang)})"
            displayed_mult_freq = float(f"{calibrated_lef:.2f}")
        else:
            ev_str = format_number(calibrated_lef, locale=meta_lang, decimals=2)
            freq_display = t("kpi_frequency_value_annual", locale=meta_lang, events=ev_str)
            displayed_mult_freq = float(f"{calibrated_lef:.2f}")

        # Red Team Rule 4 (Aritmética Transparente de Servilleta para el CTO):
        # En cada ficha técnica individual, el impacto anualizado visible DEBE coincidir con el producto
        # de Frecuencia Mostrada * Coste por Incidente (SLE) para evitar aparentes errores de cálculo.
        if not is_deterministic and reconciled_sle > 0 and displayed_mult_freq > 0:
            card_direct_ale = round(float(reconciled_sle) * float(displayed_mult_freq))
            formatted_ale = format_currency(
                float(card_direct_ale),
                currency_symbol=currency,
                locale=meta_lang,
                decimals=0,
            )
        else:
            formatted_ale = format_currency(
                float(canonical_ale),
                currency_symbol=currency,
                locale=meta_lang,
                decimals=0,
            )

        if metrics.is_deduplicated:
            notice_text = t("actuarial_custody_deduplicated_note", locale=meta_lang).format(
                primary_risk_ref=loss_event.primary_risk_ref
            )
            kpi_row_cells = [
                CellNode(
                    text=f"*{notice_text}*",
                    font_size=9.0,
                    bold=True,
                    bg_color="F8FAFC",
                    text_color_rgb=[51, 65, 85],
                    grid_span=12,
                    width_dxa=9360,
                    align="RIGHT",
                )
            ]
        elif is_deterministic or (reconciled_sle <= 0) or ("desmantelamiento" in vuln_txt.lower()) or ("zombie" in vuln_txt.lower()) or ("nos" in vuln_txt.lower() and "contrato" in vuln_txt.lower()):
            cost_lbl = t("estimated_annual_cost_label", locale=meta_lang)
            type_lbl = t("exposure_type_label", locale=meta_lang)
            waste_lbl = t("it_resource_waste_label", locale=meta_lang)
            plant_lbl = t("plant_impact_label", locale=meta_lang)
            no_outage_lbl = t("zero_plant_outage_label", locale=meta_lang)
            kpi_row_cells = [
                CellNode(
                    text=f"**{cost_lbl}**\n{formatted_ale} / {t('year_lbl', locale=meta_lang)}",
                    font_size=8.5,
                    bg_color="F8FAFC",
                    text_color_rgb=self.primary_color_rgb,
                    grid_span=4,
                    width_dxa=3120,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{type_lbl}**\n{waste_lbl}",
                    font_size=8.5,
                    bg_color="F8FAFC",
                    grid_span=4,
                    width_dxa=3120,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{plant_lbl}**\n{no_outage_lbl}",
                    font_size=8.5,
                    bg_color="F8FAFC",
                    grid_span=4,
                    width_dxa=3120,
                    align="CENTER",
                ),
            ]
        else:
            kpi_row_cells = [
                CellNode(
                    text=f"**{t('risk_card_ale_label', locale=meta_lang)}**\n{formatted_ale} / {t('year_lbl', locale=meta_lang)}",
                    font_size=8.5,
                    bg_color="F8FAFC",
                    text_color_rgb=self.primary_color_rgb,
                    grid_span=4,
                    width_dxa=3120,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{t('risk_card_sle_label', locale=meta_lang)}**\n{formatted_sle}",
                    font_size=8.5,
                    bg_color="F8FAFC",
                    grid_span=4,
                    width_dxa=3120,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{t('kpi_estimated_frequency_label', locale=meta_lang)}**\n{freq_display}",
                    font_size=8.5,
                    bg_color="F8FAFC",
                    grid_span=4,
                    width_dxa=3120,
                    align="CENTER",
                ),
            ]

        # Enforce exact closed-form arithmetic identity: Primary + Replacement + Secondary + Stochastic == SLE (Red Team / SR 11-7)
        eff_h_str = format_number(eff_recovery_hours, locale=meta_lang, decimals=1)
        rate_str = format_currency(domain_hourly_rate, currency_symbol=currency, locale=meta_lang, decimals=0)
        base_rate_str = format_currency(hourly_rate, currency_symbol=currency, locale=meta_lang, decimals=2)
        alpha_pct_str = str(int(round(alpha * 100)))

        decomp = hc.get("additive_loss_decomposition") or {}
        primary_downtime_loss = int(
            round(
                float(
                    decomp.get("primary_downtime_loss", primary_downtime_loss)
                )
            )
        )
        repl_cost_num = int(
            round(float(decomp.get("direct_replacement_loss", repl_cost_num)))
        )
        sec_weighted_loss = int(
            round(float(decomp.get("secondary_weighted_loss", sec_weighted_loss)))
        )
        stochastic_tail_adj = int(
            round(float(decomp.get("stochastic_pert_adjustment", 0)))
        )

        # Strict Additive Identity Invariant: Downtime + Replacement + Secondary + Stochastic == Mean SLE
        reconciled_sle = (
            primary_downtime_loss
            + repl_cost_num
            + sec_weighted_loss
            + stochastic_tail_adj
        )

        # Strict Standalone & Bounded Euler Identity Invariant:
        displayed_mult_freq = round(
            float(decomp.get("mean_lef") or canonical_lef or 0.25), 2
        )
        standalone_base_ale = int(round(displayed_mult_freq * reconciled_sle))
        max_disc_pct = max(
            0.0,
            min(0.25, float(hc.get("max_euler_ale_discount_pct") or 0.20)),
        )

        raw_net_ale = int(
            round(
                float(
                    decomp.get("net_allocated_ale")
                    or canonical_ale
                    or standalone_base_ale
                )
            )
        )
        raw_credit = max(0, standalone_base_ale - raw_net_ale)
        capped_credit = min(
            raw_credit, int(round(standalone_base_ale * max_disc_pct))
        )

        canonical_ale = standalone_base_ale - capped_credit
        euler_delta = -capped_credit

        p_down_str = format_currency(
            primary_downtime_loss,
            currency_symbol=currency,
            locale=meta_lang,
            decimals=0,
        )
        p_repl_str = format_currency(
            repl_cost_num,
            currency_symbol=currency,
            locale=meta_lang,
            decimals=0,
        )
        p_sec_str = format_currency(
            sec_weighted_loss,
            currency_symbol=currency,
            locale=meta_lang,
            decimals=0,
        )
        p_adj_str = "+0 €"

        finding_physics = hc.get("loss_physics") or (
            decomp.get("loss_physics") if decomp else None
        )
        if finding_physics:
            from assessment_engine.domain.actuarial.finding_archetype_resolver import (
                FindingLossPhysics,
            )

            try:
                active_arch = FindingLossPhysics(
                    finding_physics
                ).to_canonical_archetype()
            except ValueError:
                active_arch = primary_arch
        else:
            active_arch = primary_arch

        arch_suffix = active_arch.value.lower()
        sle_key = f"sle_derivation_formula_bullet_{arch_suffix}"
        sle_bullet = t(
            sle_key,
            locale=meta_lang,
            effective_hours=eff_h_str,
            hourly_rate=rate_str,
            alpha_pct=alpha_pct_str,
            base_rate=base_rate_str,
            sle_formatted=formatted_sle,
            primary_formatted=p_down_str,
            replacement_formatted=p_repl_str,
            secondary_formatted=p_sec_str,
            stochastic_formatted=p_adj_str,
            default=t(
                "sle_derivation_formula_bullet",
                locale=meta_lang,
                effective_hours=eff_h_str,
                hourly_rate=rate_str,
                alpha_pct=alpha_pct_str,
                base_rate=base_rate_str,
                sle_formatted=formatted_sle,
                primary_formatted=p_down_str,
                replacement_formatted=p_repl_str,
                secondary_formatted=p_sec_str,
                stochastic_formatted=p_adj_str,
            ),
        )

        # Standalone to Allocated ALE Euler Reconciliation Bridge (guarantees exact mathematical closure)
        standalone_base_ale = (
            round(displayed_mult_freq * reconciled_sle)
            if displayed_mult_freq > 0
            else 0
        )

        # Honest algebraic Euler delta (SR 11-7 compliant)
        euler_delta = round(canonical_ale - standalone_base_ale)
        if is_deterministic:
            euler_line = f"{t('euler_invariant_opex_label', locale=meta_lang)}: 0 {currency}/{t('year_lbl', locale=meta_lang)}"
        elif euler_delta < 0:
            credit_num = abs(euler_delta)
            credit_str = format_currency(
                credit_num, currency_symbol=currency, locale=meta_lang, decimals=0
            )
            euler_line = f"{t('euler_credit_label', locale=meta_lang)}: -{credit_str}/{t('year_lbl', locale=meta_lang)}"
        elif euler_delta > 0:
            surcharge_num = euler_delta
            surcharge_str = format_currency(
                surcharge_num, currency_symbol=currency, locale=meta_lang, decimals=0
            )
            euler_line = f"{t('euler_contagion_label', locale=meta_lang)}: +{surcharge_str}/{t('year_lbl', locale=meta_lang)}"
        else:
            euler_line = f"{t('euler_neutral_label', locale=meta_lang)}: 0 {currency}/{t('year_lbl', locale=meta_lang)}"

        st_ale_str = format_currency(
            standalone_base_ale, currency_symbol=currency, locale=meta_lang, decimals=0
        )
        eul_cr_str = format_currency(
            abs(euler_delta), currency_symbol=currency, locale=meta_lang, decimals=0
        )

        ale_bullet = t(
            "ale_derivation_formula_bullet",
            locale=meta_lang,
            ale_formatted=formatted_ale,
            frequency_text=freq_display,
            sle_formatted=formatted_sle,
            standalone_ale_formatted=st_ale_str,
            euler_line=euler_line,
            euler_credit_formatted=eul_cr_str,
        )
        fallback_pillar_ref = str(
            hc.get("pillar_name")
            or hc.get("pillar")
            or hc.get("domain_name")
            or ""
        ).strip()
        vuln_txt = _sanitize_localized_kpi_leaks(vuln_txt, meta_lang, fallback_pillar=fallback_pillar_ref)
        impact_txt = _sanitize_localized_kpi_leaks(impact_txt, meta_lang, fallback_pillar=fallback_pillar_ref)
        if not str(meta_lang).lower().startswith("en"):
            fallback_clause = fallback_pillar_ref or t(
                "domain_control_standard_fallback",
                locale=meta_lang,
            )
            vuln_txt = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_clause, vuln_txt)
            impact_txt = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_clause, impact_txt)

        act_just = _sanitize_localized_kpi_leaks(
            str(hc.get("actuarial_justification") or "").strip(),
            meta_lang,
            fallback_pillar=fallback_pillar_ref,
        )
        if not str(meta_lang).lower().startswith("en") and act_just:
            act_just = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(
                fallback_pillar_ref or t("domain_control_standard_fallback", locale=meta_lang),
                act_just,
            )
        if act_just:
            actuarial_box_text = f"**{t('risk_card_actuarial_breakdown_title', locale=meta_lang)}:**\n{act_just}\n\n• {sle_bullet}\n• {ale_bullet}"
        else:
            actuarial_box_text = f"**{t('risk_card_actuarial_breakdown_title', locale=meta_lang)}:**\n{sle_bullet}\n{ale_bullet}"
        scope_note = _sanitize_localized_kpi_leaks(
            str(hc.get("scope_note") or "").strip(),
            meta_lang,
            fallback_pillar=fallback_pillar_ref,
        )
        if scope_note:
            actuarial_box_text += f"\n• *{scope_note}*"

        # Deduplicate repeated sentence fragments caused by upstream template concatenation
        def _dedup_clauses(raw_txt: str) -> str:
            if not raw_txt:
                return raw_txt
            if "\n" in raw_txt and any(p in raw_txt for p in ("1. ", "2. ", "3. ", "4. ")):
                return raw_txt
            parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n+", raw_txt) if p.strip()]
            seen: set[str] = set()
            unique_parts: list[str] = []
            for p in parts:
                norm_p = re.sub(r"\s+", " ", p.lower()).strip(" .;:,-")
                if norm_p and norm_p not in seen:
                    seen.add(norm_p)
                    unique_parts.append(p)
            return " ".join(unique_parts) if unique_parts else raw_txt

        vuln_txt = _dedup_clauses(vuln_txt)
        impact_txt = _dedup_clauses(impact_txt)

        if not str(meta_lang).lower().startswith("en"):
            fallback_card_pillar = fallback_pillar_ref or t(
                "domain_control_standard_fallback",
                locale=meta_lang,
            )
            vuln_txt = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_card_pillar, vuln_txt)
            impact_txt = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_card_pillar, impact_txt)
            vuln_txt = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_card_pillar, vuln_txt)
            impact_txt = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_card_pillar, impact_txt)
            # Repair orphaned prepositions from template splicing (e.g., 'condicionada por en la mayoría')
            _orphan_prep_re = re.compile(
                r"\b(condicionad[oa]s?\s+por|debido\s+a|causad[oa]s?\s+por|derivad[oa]s?\s+de|asociad[oa]s?\s+a)\s+(en\s+|por\s+|con\s+|ante\s+)",
                re.IGNORECASE,
            )
            vuln_txt = _orphan_prep_re.sub(r"\1 deficiencias críticas \2", vuln_txt)
            impact_txt = _orphan_prep_re.sub(r"\1 deficiencias críticas \2", impact_txt)

        # Replace generic template boilerplate on FinOps / Governance / Chronic Toil cards with domain-accurate impact
        if _GENERIC_BOILERPLATE_IMPACT_RE.search(impact_txt):
            title_check = f"{loss_event.title} {fallback_pillar_ref}".lower()
            is_es_card = str(meta_lang).lower().startswith("es")
            if any(k in title_check for k in ("finops", "cost", "coste", "econom", "licenc", "presupuest", "tag")):
                impact_txt = (
                    "Ineficiencia financiera estructural, opacidad en la imputación de costes por unidad de negocio (Showback/Chargeback) "
                    "y desviación presupuestaria entre modelos CAPEX/OPEX sin trazabilidad unitaria."
                    if is_es_card
                    else "Structural financial inefficiency, lack of unit-cost attribution (Showback/Chargeback), and unmonitored CAPEX/OPEX budget drift."
                )
            elif any(k in title_check for k in ("dex", "workplace", "puesto", "endpoint", "provisioning", "aprovisionamiento", "toil")):
                impact_txt = (
                    "Fricción operativa crónica en la productividad del empleado, sobrecarga de soporte reactivo N1/N2/N3 y "
                    "exceso de horas de ingeniería dedicadas a tareas manuales repetitivas."
                    if is_es_card
                    else "Chronic operational friction in employee productivity, elevated reactive support ticket volume, and excessive engineering toil on manual tasks."
                )
            else:
                impact_txt = (
                    f"Degradación de los niveles de servicio (SLA), fricción operativa recurrente y sobrecoste de remediación reactiva en {fallback_pillar_ref or 'el dominio evaluado'}."
                    if is_es_card
                    else f"Service level degradation, recurring operational friction, and reactive remediation overhead across {fallback_pillar_ref or 'the assessed domain'}."
                )

        # Normalize corrupted camelCase prefixes, unresolved bracket placeholders, and repair broken template grammar
        vuln_txt = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_pillar_ref or "control del dominio", vuln_txt)
        impact_txt = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_pillar_ref or "control del dominio", impact_txt)
        actuarial_box_text = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_pillar_ref or "control del dominio", actuarial_box_text)
        vuln_txt = _CAMELCASE_ARTIFACT_RE.sub(lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), vuln_txt)
        impact_txt = _CAMELCASE_ARTIFACT_RE.sub(lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), impact_txt)
        actuarial_box_text = _CAMELCASE_ARTIFACT_RE.sub(lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), actuarial_box_text)
        vuln_txt = _repair_broken_template_grammar(vuln_txt, meta_lang, fallback_pillar_ref)
        impact_txt = _repair_broken_template_grammar(impact_txt, meta_lang, fallback_pillar_ref)
        actuarial_box_text = _repair_broken_template_grammar(actuarial_box_text, meta_lang, fallback_pillar_ref)
        fallback_prose_label = fallback_pillar_ref or t(
            "domain_control_standard_fallback",
            locale=meta_lang,
        )
        for _prose_val in (vuln_txt, impact_txt):
            pass
        vuln_txt = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_prose_label, vuln_txt)
        vuln_txt = _CAMELCASE_ARTIFACT_RE.sub(
            lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), vuln_txt
        )
        vuln_txt = _sanitize_localized_kpi_leaks(
            vuln_txt, meta_lang, fallback_pillar=fallback_prose_label
        )
        impact_txt = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_prose_label, impact_txt)
        impact_txt = _CAMELCASE_ARTIFACT_RE.sub(
            lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), impact_txt
        )
        impact_txt = _sanitize_localized_kpi_leaks(
            impact_txt, meta_lang, fallback_pillar=fallback_prose_label
        )
        if not str(meta_lang).lower().startswith("en"):
            vuln_txt = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_prose_label, vuln_txt)
            vuln_txt = _repair_broken_template_grammar(vuln_txt, meta_lang, fallback_prose_label)
            impact_txt = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_prose_label, impact_txt)
            impact_txt = _repair_broken_template_grammar(impact_txt, meta_lang, fallback_prose_label)

        vuln_txt = _deduplicate_prose_sentences(vuln_txt)
        impact_txt = _deduplicate_prose_sentences(impact_txt)

        # Prioritize stack-grounded causal threat title over generic taxonomy labels
        causal_title = str(
            hc.get("causal_risk_title")
            or hc.get("synthesized_title")
            or hc.get("title")
            or ""
        ).strip()
        # Strip any redundant category prefix before colon if present (e.g. 'Operational Risk Scenario: ...')
        if ":" in causal_title and len(causal_title.split(":", 1)[0]) <= 40:
            causal_title = causal_title.split(":", 1)[1].strip()
        display_title = causal_title if len(causal_title) > 10 else loss_event.title
        if display_title.count("(") > display_title.count(")"):
            display_title += ")"
        display_title = _dedup_clauses(display_title)
        display_title = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(
            fallback_pillar_ref or t("domain_control_standard_fallback", locale=meta_lang),
            display_title,
        )
        display_title = _CAMELCASE_ARTIFACT_RE.sub(lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), display_title)
        display_title = _sanitize_localized_kpi_leaks(
            display_title, meta_lang, fallback_pillar=fallback_pillar_ref
        )
        if not str(meta_lang).lower().startswith("en"):
            display_title = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(
                fallback_pillar_ref or t("domain_control_standard_fallback", locale=meta_lang),
                display_title,
            )
            display_title = _repair_broken_template_grammar(
                display_title,
                meta_lang,
                fallback_pillar_ref or t("domain_control_standard_fallback", locale=meta_lang),
            )

        card_table = TableNode(
            rows=[
                TableRowNode(
                    cells=[
                        CellNode(
                            text=f"[{loss_event.event_id}] {display_title}",
                            font_size=9.5,
                            bold=True,
                            bg_color=header_bg,
                            text_color_rgb=header_text,
                            grid_span=9,
                            width_dxa=7020,
                            align="LEFT",
                        ),
                        CellNode(
                            text=f"{sev_badge_text} ({format_number(share_pct, locale=meta_lang, decimals=1)}%)",
                            font_size=8.5,
                            bold=True,
                            bg_color=sev_badge_bg,
                            text_color_rgb=[255, 255, 255],
                            grid_span=3,
                            width_dxa=2340,
                            align="CENTER",
                        ),
                    ],
                    cant_split=True,
                ),
                TableRowNode(
                    cells=kpi_row_cells,
                    cant_split=True,
                ),
                TableRowNode(
                    cells=[
                        CellNode(
                            text=f"**{t('risk_card_vulnerability_label', locale=meta_lang)}:**\n{vuln_txt}",
                            font_size=8.0,
                            bg_color="FFFFFF",
                            grid_span=6,
                            width_dxa=4680,
                            border_left_color="E63946",
                            border_left_size=24,
                            align="LEFT",
                        ),
                        CellNode(
                            text=f"**{t('risk_card_operational_impact_label', locale=meta_lang)}:**\n{impact_txt}",
                            font_size=8.0,
                            bg_color="FFFFFF",
                            grid_span=6,
                            width_dxa=4680,
                            border_left_color="2A9D8F",
                            border_left_size=24,
                            align="LEFT",
                        ),
                    ],
                    cant_split=True,
                ),
                TableRowNode(
                    cells=[
                        CellNode(
                            text=actuarial_box_text,
                            font_size=8.0,
                            bg_color="F8F9FA",
                            grid_span=12,
                            width_dxa=9360,
                            border_left_color="1D3557",
                            border_left_size=24,
                            align="LEFT",
                        ),
                    ],
                    cant_split=True,
                ),
            ],
            column_widths_dxa=[780] * 12,
            keep_together=True,
        )
        return card_table

    def _build_conclusions_and_appendices(
        self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]] | None = None
    ) -> None:
        # Streamlined Unified Appendix (RFC 053): Chapter 5 & Appendix A/B retired; glossary unified
        _build_appendix_c_glossary_and_disclaimer_fn(ctx, nodes, self.primary_color_rgb)

    def _parse_markdown_to_nodes(
        self, md_path: Path, skip_level_1: bool = False
    ) -> List[Any]:
        """Parses a Markdown file, converting its content into a sequence of Abstract Syntax Tree (AST) nodes."""
        nodes = []
        if not md_path.exists():
            return nodes

        with open(md_path, "r", encoding="utf-8") as f:
            lines = [html.unescape(line) for line in f.readlines()]

        seen_paragraphs: set[str] = set()
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Sanitization: Replace non-standard vocabulary, camelCase artifacts, and any leaked English KPI tokens
            if isinstance(cleaned, str):
                doc_locale = getattr(self, "meta_lang", "en")
                fallback_label = t("domain_control_standard_fallback", locale=doc_locale)
                cleaned = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(fallback_label, cleaned)
                cleaned = _CAMELCASE_ARTIFACT_RE.sub(lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), cleaned)
                cleaned = _sanitize_localized_kpi_leaks(cleaned, doc_locale)
                if not str(doc_locale).lower().startswith("en"):
                    cleaned = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(fallback_label, cleaned)
                    cleaned = _repair_broken_template_grammar(cleaned, doc_locale, fallback_label)
                # Repair broken mail-merge punctuation artifacts (e.g. 'fábrica.ç', 'adquisición.en', 'El área.gestiona')
                cleaned = re.sub(
                    r"([a-záéíóúñüA-ZÁÉÍÓÚÑÜ])\.([a-záéíóúñüç])",
                    lambda m: f"{m.group(1)}{m.group(2)}" if m.group(2) == "ç" else f"{m.group(1)} {m.group(2)}",
                    cleaned,
                )
                cleaned = _BROKEN_MAIL_MERGE_RE.sub("", cleaned)
                cleaned = _sanitize_dangling_discourse_openers(cleaned, doc_locale)
                cleaned = _reconcile_replication_topology_prose(cleaned, doc_locale)
                cleaned = _reconcile_internal_narrative_contradictions(cleaned, doc_locale)
                cleaned = _synchronize_inline_recalibrated_scores(cleaned, doc_locale)
                cleaned = _reconcile_cmmi_level_bracket_claims(cleaned, doc_locale)
                cleaned = _deduplicate_prose_sentences(cleaned)
                # Strip dangling English template tokens after prepositions in Spanish prose (e.g., "en Site Reliability Engineering (SRE) Maturity: Error Budgets ." or "en Edge Service Ingress: L4/Conectividad..., WAF .")
                if not str(doc_locale).lower().startswith("en"):
                    cleaned = re.sub(
                        r"\b(en|de|para|sobre|hacia|como)\s+(?:[a-zA-Z][A-Za-z0-9/&()-]+\s*){1,6}:\s*[^.;]{1,95}?(?=\s*[.;]|$)",
                        lambda m: f"{m.group(1)} {fallback_label}",
                        cleaned,
                    )
                    cleaned = re.sub(
                        r"\b(factores\s+clave\s+como)\s+[^.;]+?(?=\s*[.;]|$)",
                        lambda m: f"{m.group(1)} {fallback_label}",
                        cleaned,
                        flags=re.IGNORECASE,
                    )
                    cleaned = re.sub(r"\s+([.,;:])", r"\1", cleaned)

            # Prevent consecutive or duplicate identical narrative paragraphs or benchmark citations
            if not cleaned.startswith("#"):
                norm_line = re.sub(r"\s+", " ", cleaned.lower()).strip(" .;:,-*")
                if len(norm_line) > 35:
                    if norm_line in seen_paragraphs:
                        continue
                    seen_paragraphs.add(norm_line)

            # Exclude special markers for table and mosaic directives from the content processing stream.
            skip_directives = get_localized_list(
                "directive_markers_to_skip",
                locale=getattr(self, "meta_lang", "en"),
                default=[
                    "--- COMPARATIVE TABLE",
                    "KEY_STRENGTHS:",
                    "KEY_GAPS:",
                    "--- END TABLE",
                ],
            )
            if any(marker in cleaned for marker in skip_directives):
                continue

            #
            if cleaned.startswith("# "):
                if not skip_level_1:
                    nodes.append(
                        HeadingNode(
                            text=cleaned[2:],
                            level=1,
                            primary_color_rgb=self.primary_color_rgb,
                        )
                    )
            elif cleaned.startswith("## "):
                nodes.append(
                    HeadingNode(
                        text=cleaned[3:],
                        level=2,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )
            elif cleaned.startswith("### "):
                nodes.append(
                    HeadingNode(
                        text=cleaned[4:],
                        level=3,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )
            elif cleaned.startswith("#### "):
                nodes.append(
                    HeadingNode(
                        text=cleaned[5:],
                        level=4,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )
            #
            elif cleaned.startswith("* ") or cleaned.startswith("- "):
                nodes.append(
                    ParagraphNode(text=cleaned[2:], style="List Bullet", space_after=6)
                )
            #
            elif cleaned.startswith("> "):
                nodes.append(
                    ParagraphNode(text=cleaned[2:], italic=True, space_after=12)
                )
            #
            else:
                nodes.append(ParagraphNode(text=cleaned, space_after=8))

        return nodes

    def _parse_csv_generic(
        self,
        csv_path: Path,
        headers: List[str],
        col_widths: Optional[List[float]] = None,
    ) -> TableNode:
        rows = []
        #
        rows.append(
            TableRowNode(
                cells=[
                    CellNode(
                        text=h,
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=[255, 255, 255],
                        align="CENTER",
                    )
                    for h in headers
                ],
                is_header=True,
            )
        )

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)
            for r_idx, row_data in enumerate(reader):
                if not row_data:
                    continue
                bg = self.alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
                cells = []
                row_pillar_label = ""
                if len(row_data) > 0 and str(row_data[0]).strip():
                    from assessment_engine.domain.taxonomy_resolver import (
                        get_taxonomy_resolver,
                    )
                    resolver = get_taxonomy_resolver()
                    row_pillar_label = resolver.resolve_pillar_by_any_reference(
                        str(row_data[0]).strip(),
                        default=str(row_data[0]).strip(),
                        locale=getattr(self, "meta_lang", "en"),
                    )

                for c_idx, val in enumerate(row_data):
                    bold = c_idx == 0
                    align = (
                        "CENTER"
                        if c_idx == 1
                        else ("JUSTIFY" if c_idx == 2 else "LEFT")
                    )

                    val_str = str(val)
                    if c_idx == 0 and row_pillar_label:
                        val_str = row_pillar_label
                    elif isinstance(val_str, str):
                        meta_l = getattr(self, "meta_lang", "en")
                        fallback_label = row_pillar_label or t(
                            "domain_control_standard_fallback",
                            locale=meta_l,
                        )
                        val_str = _UNRESOLVED_BRACKET_PLACEHOLDER_RE.sub(
                            fallback_label, val_str
                        )
                        val_str = _CAMELCASE_ARTIFACT_RE.sub(
                            lambda m: m.group(1).upper() + m.group(2) + (m.group(3) or ""), val_str
                        )
                        val_str = _sanitize_localized_kpi_leaks(
                            val_str, meta_l, fallback_pillar=fallback_label
                        )
                        if not str(meta_l).lower().startswith("en"):
                            val_str = _RAW_ENGLISH_COMPOUND_KPI_RE.sub(
                                fallback_label, val_str
                            )
                            val_str = _repair_broken_template_grammar(
                                val_str, meta_l, fallback_label
                            )
                        val_str = _BROKEN_MAIL_MERGE_RE.sub("", val_str)
                        val_str = _sanitize_dangling_discourse_openers(val_str, meta_l)
                        val_str = _reconcile_replication_topology_prose(val_str, meta_l)
                        val_str = _reconcile_internal_narrative_contradictions(val_str, meta_l)
                        val_str = _synchronize_inline_recalibrated_scores(val_str, meta_l)
                        val_str = _reconcile_cmmi_level_bracket_claims(val_str, meta_l)
                        val_str = _deduplicate_prose_sentences(val_str)
                        if not str(meta_l).lower().startswith("en"):
                            val_str = re.sub(
                                r"\b(en|de|para|sobre|hacia|como)\s+(?:[a-zA-Z][A-Za-z0-9/&()-]+\s*){1,6}:\s*[^.;]{1,95}?(?=\s*[.;]|$)",
                                lambda m: f"{m.group(1)} {fallback_label}",
                                val_str,
                            )
                            val_str = re.sub(
                                r"\b(factores\s+clave\s+como)\s+[^.;]+?(?=\s*[.;]|$)",
                                lambda m: f"{m.group(1)} {fallback_label}",
                                val_str,
                                flags=re.IGNORECASE,
                            )
                            val_str = re.sub(r"\s+([.,;:])", r"\1", val_str)

                    if c_idx == 2:
                        just_hdr = t("asis_header_score_justification", locale=getattr(self, "meta_lang", "en"))
                        val_str = re.sub(
                            r"\*\*.*?(?:Score|Rating|Evaluation)\s*\(\d+[,.]\d+\):\*\*",
                            f"**{just_hdr}**",
                            val_str
                        )
                        val_str = re.sub(
                            r".*?(?:Score|Rating|Evaluation)\s*\(\d+[,.]\d+\):",
                            just_hdr,
                            val_str
                        )
                    # Repair broken mail-merge punctuation artifacts (e.g. 'fábrica.ç', 'adquisición.en', 'El área.gestiona')
                    val_str = re.sub(
                        r"([a-záéíóúñüA-ZÁÉÍÓÚÑÜ])\.([a-záéíóúñüç])",
                        lambda m: f"{m.group(1)}{m.group(2)}" if m.group(2) == "ç" else f"{m.group(1)} {m.group(2)}",
                        val_str,
                    )

                    cells.append(
                        CellNode(text=val_str, bold=bold, bg_color=bg, align=align)
                    )
                rows.append(TableRowNode(cells=cells))

        return TableNode(rows=rows, autofit=True, col_widths=col_widths)


def _reconcile_cmmi_level_bracket_claims(text: str, locale: str | None = None) -> str:
    """Reconcile CMMI numeric scores with their declared maturity level labels and bracket claims."""
    if not text or not isinstance(text, str):
        return text

    is_es = not str(locale or "en").lower().startswith("en")

    def _level_info(score_val: float) -> tuple[int, str]:
        if score_val < 1.60:
            return 1, ("Inicial" if is_es else "Initial")
        if score_val < 2.60:
            return 2, ("Gestionado" if is_es else "Managed")
        if score_val < 3.60:
            return 3, ("Definido" if is_es else "Defined")
        if score_val < 4.60:
            return 4, ("Cuantitativamente Gestionado" if is_es else "Quantitatively Managed")
        return 5, ("Optimizado" if is_es else "Optimizing")

    def _fix_score_and_parenthetical_level(match: re.Match[str]) -> str:
        prefix = match.group(1)
        score_raw = match.group(2)
        mid = match.group(3)
        score_val = _safe_float(score_raw.replace(",", "."), default=-1.0)
        if score_val < 0.0 or score_val > 5.0:
            return match.group(0)
        lvl_num, lvl_label = _level_info(score_val)
        lvl_word = "Nivel" if is_es else "Level"
        return f"{prefix}{score_raw}{mid}({lvl_word} {lvl_num} - {lvl_label})"

    reconciled = re.sub(
        r"((?:puntuaci[óo]n|madurez|score|rating)[^0-9]{1,35}?)(\d[.,]\d{1,2})(\s*(?:sobre|out\s+of|/)\s*5[.,]00?\s*)\(\s*(?:Nivel|Level)\s*\d\s*(?:[-–—:]\s*[^)]+)?\)",
        _fix_score_and_parenthetical_level,
        text,
        flags=re.IGNORECASE,
    )

    def _fix_inline_score_with_level_claim(match: re.Match[str]) -> str:
        prefix = match.group(1)
        score_raw = match.group(2)
        mid = match.group(3)
        score_val = _safe_float(score_raw.replace(",", "."), default=-1.0)
        if score_val < 0.0 or score_val > 5.0:
            return match.group(0)
        lvl_num, lvl_label = _level_info(score_val)
        lvl_word = "Nivel" if is_es else "Level"
        return f"{prefix}{score_raw}{mid}{lvl_word} {lvl_num} - {lvl_label}"

    reconciled = re.sub(
        r"(\b)(\d[.,]\d{1,2})(\s*(?:/\s*5[.,]00?\s*)?\(\s*)(?:Nivel|Level)\s*\d\s*[-–—:]\s*[^)]+(?=\))",
        _fix_inline_score_with_level_claim,
        reconciled,
        flags=re.IGNORECASE,
    )

    # Neutralize false boundary claims where a Level 1 or Level 2 score claims to border Level 3/4
    reconciled = re.sub(
        r"(,\s*[^.,;]{1,55}?\s+)(?:se\s+sit[úu]an?\s+en\s+(?:el\s+l[íi]mite|la\s+frontera|el\s+umbral)(?:\s+de\s+tramo)?\s+del\s+nivel\s+[345]|sit\s+at\s+the\s+(?:boundary|limit|threshold)\s+of\s+level\s+[345])",
        lambda m: (
            f"{m.group(1)}evidencian brechas estructurales de estandarización operativa"
            if is_es
            else f"{m.group(1)}evidence structural standardization gaps across operations"
        ),
        reconciled,
        flags=re.IGNORECASE,
    )

    # Reconcile contradictory DEX / equipment refresh claims within the same paragraph
    if _CRITICAL_DEFICIT_TELEMETRY_RE.search(reconciled):
        reconciled = re.sub(
            r"(?:mostrando\s+una\s+)?disciplina\s+ejemplar\s+en\s+la\s+renovaci[óo]n\s+de\s+(?:port[áa]tiles|equipos)(?:\s+corporativos)?",
            "presentando brechas operativas en la gestión del ciclo de vida y telemetría de dispositivos",
            reconciled,
            flags=re.IGNORECASE,
        )
        reconciled = re.sub(
            r"(?:showing\s+)?exemplary\s+discipline\s+in\s+(?:corporate\s+)?(?:laptop|equipment)\s+(?:refresh|renewal)",
            "exhibiting operational gaps in endpoint lifecycle management and telemetry",
            reconciled,
            flags=re.IGNORECASE,
        )

    # Repair dangling truncated sentences ending mid-clause without terminal punctuation
    if len(reconciled) > 40 and not reconciled.lstrip().startswith(("#", "*", "-", "|", ">")):
        stripped_end = reconciled.rstrip()
        if re.search(r"\(\s*(?:N\+1\s*/\s*2N\.?|N\+1\.?|2N\.?)$", stripped_end, re.IGNORECASE):
            reconciled = re.sub(
                r"\(\s*(N\+1\s*/\s*2N|N\+1|2N)\.?\s*$",
                r"(\1).",
                stripped_end,
                flags=re.IGNORECASE,
            )
        elif re.search(
            r"\b(?:en\s+tallas\s+S\s+y\s+M|en\s+salas\s+industriales\s+no\s+especializadas|sin\s+especializaci[óo]n\s+t[ée]cnica)$",
            stripped_end,
            re.IGNORECASE,
        ):
            reconciled = f"{stripped_end}."

    return reconciled


def compile_asis_docx_via_ast(
    payload_path: str | Path,
    output_docx_path: str | Path,
    doc_lang: str,
    modules_dir: str | Path | None = None,
) -> Path:
    """Compile deliverable directly into DOCX via declarative AST transformation."""
    bridge = PayloadToASTBridge()
    ast = bridge.convert(
        blueprint_payload_path=str(payload_path),
        approved_annex_path="",
        override_locale=doc_lang,
        modules_dir=modules_dir,
    )

    # Execute EpistemicCompilerBarrier circuit breaker prior to DOCX emission
    from assessment_engine.domain.coherence_gatekeeper import EpistemicCompilerBarrier
    EpistemicCompilerBarrier.assert_zero_defect_invariants(ast, str(payload_path))

    from assessment_engine.adapters.compilers.docx_compiler import DocxCompiler

    compiler = DocxCompiler()
    out_p = Path(output_docx_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    compiler.compile(ast, str(out_p))

    # Synchronize physical page numbers into the TOC SDT to eliminate split-brain
    from assessment_engine.adapters.compilers.toc_page_resolver import (
        DeterministicTocPageResolver,
    )

    DeterministicTocPageResolver.synchronize_docx_toc(out_p)

    return out_p
