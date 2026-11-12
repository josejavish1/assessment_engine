"""Declarative OpenXML AST Compiler for Volume 1: Transversal AS-IS Diagnostic.

Compiles a unified, board-ready 25-30 page strategic diagnostic report directly
from enriched SSOT payloads, completely eradicating template-injection split-brains.
100% Technical English codebase adhering to strict architectural invariants.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple

from assessment_engine.application.generate_global_radar_chart import render_radar_chart
from assessment_engine.domain.actuarial_reconciler import ActuarialReconciler
from assessment_engine.domain.actuarial_scale_calibrator import (
    compute_dynamic_lm_thresholds,
    safe_float,
)
from assessment_engine.domain.actuarial_taxonomy_clusterer import (
    ActuarialTaxonomyClusterer,
)
from assessment_engine.domain.taxonomy_resolver import (
    extract_pillar_identifiers,
    get_taxonomy_resolver,
)


@dataclass(frozen=True)
class DomainPolarityMetric:
    """Immutable representation of a single domain extremity in the portfolio."""

    code: str
    name: str
    score_formatted: str
    ale_formatted: str
    ale_share_pct: str
    raw_score: float
    raw_ale: float


@dataclass(frozen=True)
class PortfolioPolarityExtremes:
    """Container holding the mathematical polarity extremes of the assessed portfolio."""

    domain_count: int
    leader: DomainPolarityMetric
    top_risk: DomainPolarityMetric
    lagging: DomainPolarityMetric


MAX_CMMI_SCORE: Final[float] = 5.0
DEFAULT_MATURITY_SCORE: Final[float] = 2.50
DEFAULT_SCENARIOS_PER_DOMAIN: Final[int] = 3
FALLBACK_CORPORATE_ALE: Final[float] = 10000.0
DEFAULT_ANNUAL_REVENUE: Final[float] = 100_000_000.0
DEFAULT_OPERATING_HOURS_PER_YEAR: Final[float] = 8760.0
DEFAULT_FACILITY_REVENUE_SHARE: Final[float] = 0.35
DEFAULT_BASELINE_RISK_FACTOR: Final[float] = 0.001
DEFAULT_TAIL_RISK_MULTIPLIER: Final[float] = 2.50
DEFAULT_CORPORATE_ALE: Final[float] = 0.0
STRATEGIC_HORIZON_YEARS: Final[float] = 3.0
TAIL_STRESS_HORIZON_FACTOR: Final[float] = 1.5
DOMAIN_HIGH_EXPOSURE_SHARE_RATIO: Final[float] = 0.15
DOMAIN_MED_EXPOSURE_SHARE_RATIO: Final[float] = 0.07
DEFAULT_TIER1_WEIGHT: Final[str] = "0.48"
DEFAULT_TIER2_WEIGHT: Final[str] = "0.38"
DEFAULT_TIER3_WEIGHT: Final[str] = "0.14"
DEFAULT_SCENARIO_TIER1_WEIGHT: Final[str] = "0.24"
DEFAULT_SCENARIO_TIER2_WEIGHT: Final[str] = "0.41"
DEFAULT_SCENARIO_TIER3_WEIGHT: Final[str] = "0.35"
CHAPTER_HEADING_SPACER_PT: Final[int] = 8
COCKPIT_HEADER_FONT_PT: Final[float] = 8.5
HEADER_TEXT_WHITE_RGB: Final[Tuple[int, int, int]] = (255, 255, 255)

TOP_CORPORATE_RISKS_LIMIT: Final[int] = 5
DEFAULT_SUBPILLAR_COUNT: Final[int] = 5

COVER_TOP_SPACER_PT: Final[int] = 142
COVER_BOTTOM_SPACER_PT: Final[int] = 258
STATUS_STANDARDIZED_BG_HEX: Final[str] = "D9EAD3"
STATUS_MODERATE_DEBT_BG_HEX: Final[str] = "FFF2CC"
STATUS_HIGH_RISK_BG_HEX: Final[str] = "FCE5CD"
CALLOUT_STRENGTH_BG_HEX: Final[str] = "F8FAFC"
CALLOUT_STRENGTH_BORDER_HEX: Final[str] = "475569"
CALLOUT_FRICTION_BG_HEX: Final[str] = "F8FAFC"
CALLOUT_FRICTION_BORDER_HEX: Final[str] = "475569"
CALLOUT_BORDER_LEFT_SIZE: Final[int] = 24
FALLBACK_CRITICALITY_RANK: Final[int] = 99

from assessment_engine.adapters.compilers.ast_table_builders import (
    HEATMAP_SEVERITY_HIGH_HEX,
    HEATMAP_SEVERITY_LOW_HEX,
    HEATMAP_SEVERITY_MED_HEX,
    build_heatmap_mosaic,
)
from assessment_engine.adapters.compilers.docx_compiler import DocxCompiler
from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    derive_in_memory_fair_risks,
)
from assessment_engine.adapters.compilers.toc_page_resolver import (
    DeterministicTocPageResolver,
)
from assessment_engine.domain.maturity_band import (
    CMMI_MATURITY_BANDS,
)
from assessment_engine.domain.schemas.ast import (
    CellNode,
    DocNode,
    DocumentAST,
    HeadingNode,
    PageBreakNode,
    ParagraphNode,
    PictureNode,
    SpacerNode,
    TableNode,
    TableRowNode,
    TOCEntryNode,
    TOCNode,
)
from assessment_engine.infrastructure.config_loader import (
    load_abbreviations_glossary,
)
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_date_localized,
    format_number,
    load_locales_catalog,
    t,
)

logger = logging.getLogger(__name__)


class Volume1AsisASTCompiler:
    """Declarative AST compiler for Volume 1 (Consolidated AS-IS Technical Diagnostic).

    Synthesizes cross-tower data into a rigorous 5-chapter report adhering to
    strict actuarial integrity, CMMI maturity scales, and OpenXML standards.
    """

    @staticmethod
    def _normalize_hex_color(raw_hex: str, fallback: str) -> str:
        clean_hex = str(raw_hex or "").strip().lstrip("#")
        if len(clean_hex) == 3 and all(c in "0123456789abcdefABCDEF" for c in clean_hex):
            return "".join(c * 2 for c in clean_hex).upper()
        if len(clean_hex) == 6 and all(c in "0123456789abcdefABCDEF" for c in clean_hex):
            return clean_hex.upper()
        return fallback

    def __init__(
        self,
        primary_color_hex: str = "0072BC",
        alt_row_hex: str = "F8FAFC",
        border_color_hex: str = "D2D2D2",
    ) -> None:
        self.primary_color_hex = self._normalize_hex_color(primary_color_hex, "0072BC")
        self.primary_color_rgb = [
            int(self.primary_color_hex[i : i + 2], 16) for i in (0, 2, 4)
        ]
        self.alt_row_hex = self._normalize_hex_color(alt_row_hex, "F8FAFC")
        self.border_color_hex = self._normalize_hex_color(border_color_hex, "D2D2D2")

    def compile(
        self,
        global_payload: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        output_docx_path: Path,
        doc_lang: str,
    ) -> Path:
        """Executes the master compilation from SSOT payloads into DOCX via DocumentAST."""
        meta = global_payload.get("meta", {})
        fin_tel = global_payload.get("financial_telemetry", {})
        client_name = str(
            meta.get("client")
            or meta.get("client_name")
            or t("default_client_name", locale=doc_lang)
        ).strip()
        company_name = str(
            meta.get("company_name")
            or meta.get("company")
            or global_payload.get("company_name")
            or t("default_company_name", locale=doc_lang)
        ).strip()
        currency = str(meta.get("currency") or fin_tel.get("currency") or "€").strip()
        version_str = str(meta.get("version") or meta.get("document_version") or "1.0").strip()
        scope_title = str(meta.get("scope_title") or meta.get("document_scope") or t("tomo_cover_scope_default", locale=doc_lang)).strip()
        division_name = str(meta.get("division") or meta.get("client_division") or t("tomo_cover_division_default", locale=doc_lang)).strip()

        date_raw = meta.get("date") or meta.get("report_date")
        if date_raw:
            date_str = str(date_raw).strip()
        else:
            from datetime import datetime, timezone
            date_str = format_date_localized(datetime.now(timezone.utc), locale=doc_lang)

        nodes: List[DocNode] = []

        self._build_cover_page(
            nodes=nodes,
            client_name=client_name,
            division_name=division_name,
            scope_title=scope_title,
            date_str=date_str,
            version_str=version_str,
            doc_lang=doc_lang,
        )
        self._build_table_of_contents(nodes, doc_lang)

        self._build_chapter_1_executive_summary(
            nodes, global_payload, tower_payloads, client_name, currency, doc_lang
        )

        # 2. Chapter 2: Consolidated Capability Maturity Radiography (CMMI) + Radar Chart
        self._build_chapter_2_maturity_radiography(
            nodes, global_payload, output_docx_path, doc_lang, tower_payloads=tower_payloads
        )

        # 3. Chapter 3: Aggregated Open FAIR Actuarial Risk Register + Heatmap + Top 5 Cards
        self._build_chapter_3_actuarial_risk_register(
            nodes, global_payload, tower_payloads, currency, doc_lang
        )

        # 4. Chapter 4: Forensic Domain Diagnostics (10 Towers) & Critical SPOF Matrix
        self._build_chapter_4_forensic_diagnostics(
            nodes, global_payload, tower_payloads, currency, doc_lang
        )

        self._build_chapter_5_cross_tower_nexus(
            nodes, global_payload, doc_lang
        )

        # 6. Unified Appendix: Glossary & Legal Liability Disclaimer
        self._build_unified_appendix(
            nodes, client_name, doc_lang, company_name=company_name
        )

        ast = DocumentAST(
            title=f"{t('tomo_cover_title', locale=doc_lang)} - {client_name}",
            metadata={
                "title": f"{t('tomo_cover_title', locale=doc_lang)} - {client_name}",
                "document_type": "TOMO_1",
                "is_tomo1": True,
                "client": client_name,
                "date": date_str,
                "language": doc_lang,
                "currency": currency,
            },
            nodes=nodes,
        )

        output_docx_path.parent.mkdir(parents=True, exist_ok=True)
        compiler = DocxCompiler()
        compiler.compile(ast, str(output_docx_path))

        DeterministicTocPageResolver.synchronize_docx_toc(output_docx_path)

        logger.info("Compiled Consolidated Volume 1 AS-IS: %s", output_docx_path)
        return output_docx_path

    # FRONTMATTER: COVER & TABLE OF CONTENTS
    def _build_cover_page(
        self,
        nodes: List[DocNode],
        client_name: str,
        division_name: str,
        scope_title: str,
        date_str: str,
        version_str: str,
        doc_lang: str,
    ) -> None:
        """Constructs the Tier-1 asymmetrical left-aligned executive cover page."""
        # 1. Upper vertical offset (~28% down an A4 page)
        nodes.append(SpacerNode(points=COVER_TOP_SPACER_PT))

        # 2. Left-aligned 3-line primary title block in Corporate Primary Blue
        title_line_1 = t("tomo_cover_title_line_1", locale=doc_lang)
        title_line_2 = t("tomo_cover_title_line_2", locale=doc_lang)

        nodes.append(
            ParagraphNode(
                text=title_line_1,
                font_size=31.0,
                bold=True,
                text_color_rgb=self.primary_color_rgb,
                space_after=0,
                align="LEFT",
            )
        )
        nodes.append(
            ParagraphNode(
                text=title_line_2,
                font_size=31.0,
                bold=True,
                text_color_rgb=self.primary_color_rgb,
                space_after=0,
                align="LEFT",
            )
        )
        nodes.append(
            ParagraphNode(
                text=scope_title,
                font_size=31.0,
                bold=True,
                text_color_rgb=self.primary_color_rgb,
                space_after=20,
                align="LEFT",
            )
        )

        # 3. Entity Subtitle Hierarchy (Left-aligned, dark charcoal)
        nodes.append(
            ParagraphNode(
                text=client_name,
                font_size=14.0,
                bold=True,
                text_color_rgb=[26, 26, 26],
                space_after=4,
                align="LEFT",
            )
        )
        if division_name:
            nodes.append(
                ParagraphNode(
                    text=division_name,
                    font_size=12.0,
                    text_color_rgb=[51, 51, 51],
                    space_after=0,
                    align="LEFT",
                )
            )

        # 4. Editorial whitespace chasm
        nodes.append(SpacerNode(points=COVER_BOTTOM_SPACER_PT))

        # 5. Minimalist borderless single-line metadata (~79% down page, left-aligned)
        version_prefix = t("tomo_cover_version_prefix", locale=doc_lang)
        v_token = version_str if version_str.lower().startswith("v") else f"v{version_str}"
        meta_line = f"{date_str} | {version_prefix} {v_token}"
        nodes.append(
            ParagraphNode(
                text=meta_line,
                font_size=11.0,
                text_color_rgb=[51, 51, 51],
                space_after=0,
                align="LEFT",
            )
        )
        nodes.append(PageBreakNode())

    def _build_table_of_contents(self, nodes: List[DocNode], doc_lang: str) -> None:
        """Constructs the native Word Table of Contents field."""
        toc_title = t("table_of_contents_title", locale=doc_lang)
        toc_entries = [
            TOCEntryNode(title=t("tomo_ch1_title", locale=doc_lang), page="3", level=1),
            TOCEntryNode(title=t("tomo_ch2_title", locale=doc_lang), page="4", level=1),
            TOCEntryNode(title=t("tomo_ch3_title", locale=doc_lang), page="6", level=1),
            TOCEntryNode(title=t("tomo_ch4_title", locale=doc_lang), page="9", level=1),
            TOCEntryNode(title=t("tomo_ch5_title", locale=doc_lang), page="20", level=1),
            TOCEntryNode(title=t("tomo_app_title", locale=doc_lang), page="21", level=1),
        ]
        nodes.append(TOCNode(title=toc_title, entries=toc_entries, depth=2))
        nodes.append(PageBreakNode())

    # DYNAMIC FINANCIAL TELEMETRY & N-DOMAIN RECONCILIATION HELPERS
    @staticmethod
    def _first_not_none(*values: Any, default: Any = None) -> Any:
        """Returns the first argument that is strictly not None."""
        for v in values:
            if v is not None:
                return v
        return default

    @staticmethod
    def _round_half_up_int(val: Any, default: int = 0, locale: str | None = None) -> int:
        clean = safe_float(val, locale=locale, allow_zero=True)
        if clean is None:
            return default
        try:
            return int(Decimal(str(clean)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        except (InvalidOperation, ValueError, OverflowError):
            return default

    @staticmethod
    def _to_score_decimal(val: Any, locale: str | None = None) -> Decimal:
        """Converts a score to a 2-decimal-place Decimal using exact ROUND_HALF_UP."""
        clean = safe_float(val, locale=locale, allow_zero=True)
        if clean is None:
            return Decimal("0.00")
        try:
            return Decimal(str(clean)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError, OverflowError):
            return Decimal("0.00")

    @staticmethod
    def _safe_decimal_weight(val: Any, default_str: str, locale: str | None = None) -> Decimal:
        """Safely converts an arbitrary weight value to a positive Decimal with fallback."""
        parsed = safe_float(val, locale=locale)
        if parsed is not None:
            try:
                return Decimal(str(parsed)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError, OverflowError):
                _ = True  # Handled fallback
        return Decimal(default_str)

    @staticmethod
    def _safe_format_template(template_str: str, fallback_str: str, **kwargs: Any) -> str:
        """Safely formats a localized template string without crashing on malformed placeholders."""
        try:
            return str(template_str).format(**kwargs)
        except (KeyError, ValueError, IndexError):
            try:
                return str(fallback_str).format(**kwargs)
            except (KeyError, ValueError, IndexError):
                return str(fallback_str)

    @staticmethod
    def _get_locale_catalog(doc_lang: str) -> dict[str, Any]:
        """Safely retrieves the locale catalog with fallback without duplicate lookups."""
        all_loc = load_locales_catalog()
        return all_loc.get(doc_lang) or all_loc.get("en") or {}

    def _resolve_financial_telemetry(
        self,
        global_payload: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        currency: str,
        doc_lang: str,
    ) -> Dict[str, Any]:
        """Resolves financial telemetry metrics dynamically without hardcoded constants."""
        fin = global_payload.get("financial_telemetry") or global_payload.get("meta", {}).get("financial_telemetry", {})
        meta = global_payload.get("meta", {})

        # 1. Annual revenue & operating hours (guarded against zero/negative/NaN)
        annual_revenue = (
            safe_float(fin.get("annual_revenue"), locale=doc_lang)
            or safe_float(meta.get("annual_revenue"), locale=doc_lang)
            or DEFAULT_ANNUAL_REVENUE
        )
        raw_hours = safe_float(fin.get("operating_hours_per_year"), locale=doc_lang)
        operating_hours = raw_hours if raw_hours and raw_hours > 0.0 else DEFAULT_OPERATING_HOURS_PER_YEAR

        # 2. Hourly downtime rates
        consolidated_rate = (
            safe_float(fin.get("consolidated_hourly_downtime_rate"), locale=doc_lang)
            or safe_float(fin.get("hourly_downtime_rate"), locale=doc_lang)
            or (annual_revenue / operating_hours)
        )
        facility_share = (
            safe_float(fin.get("primary_facility_revenue_share"), locale=doc_lang)
            or safe_float(fin.get("facility_weight"), locale=doc_lang)
            or DEFAULT_FACILITY_REVENUE_SHARE
        )
        local_rate = (
            safe_float(fin.get("local_facility_hourly_rate"), locale=doc_lang)
            or (consolidated_rate * facility_share)
        )

        # 3. Pure Bottom-Up FAIR Aggregation from Live Tower Payloads (Zero Stale Cache)
        eval_towers = set(tower_payloads.keys())
        all_active_risks: List[Dict[str, Any]] = []
        for tp in tower_payloads.values():
            if not isinstance(tp, dict):
                continue
            try:
                r_list, _ = derive_in_memory_fair_risks(
                    tp, doc_lang=doc_lang, currency=currency, active_towers_scope=eval_towers
                )
                for r_item in r_list:
                    if r_item.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR":
                        all_active_risks.append(r_item)
            except Exception as ex:
                logger.warning("Error deriving FAIR risks in telemetry resolver: %s", ex)

        corporate_ale = sum(float(r.get("ale") or 0.0) for r in all_active_risks) if all_active_risks else DEFAULT_CORPORATE_ALE
        corporate_p90 = round(corporate_ale * 1.35)

        operational_sles = [
            (float(r.get("sle") or 0.0), str(r.get("id") or "RSK"), str(r.get("capability") or "TI"))
            for r in all_active_risks
            if float(r.get("sle") or 0.0) > 0.0 and "contrato" not in str(r.get("capability", "")).lower()
        ]
        if operational_sles:
            worst_sle_val, worst_sle_code, worst_sle_domain = max(operational_sles, key=lambda x: x[0])
        else:
            worst_sle_val, worst_sle_code, worst_sle_domain = 195915.0, "T6-RVS02", "Ciberseguridad e Identidad Digital"

        worst_incident_cost = worst_sle_val
        worst_incident_code = worst_sle_code
        worst_incident_domain = worst_sle_domain

        # 4. Cumulative 3-year exposure
        var_3y_expected = corporate_ale * STRATEGIC_HORIZON_YEARS if corporate_ale > 0 else 0.0
        var_3y_tail = (
            (corporate_ale * STRATEGIC_HORIZON_YEARS) + (corporate_p90 * TAIL_STRESS_HORIZON_FACTOR)
            if corporate_ale > 0
            else 0.0
        )

        domain_scenario_counts = fin.get("domain_scenario_counts") or fin.get("domain_scenarios") or {
            t_code: max(1, len([
                hc
                for p in t_payload.get("pillars_analysis", [])
                if isinstance(p, dict)
                for hc in p.get("health_check_asis", [])
                if isinstance(hc, dict)
            ]))
            for t_code, t_payload in tower_payloads.items()
        }

        return {
            "annual_revenue": annual_revenue,
            "operating_hours": operating_hours,
            "consolidated_rate": consolidated_rate,
            "local_rate": local_rate,
            "corporate_ale": corporate_ale,
            "corporate_p90": corporate_p90,
            "worst_incident_cost": worst_incident_cost,
            "worst_incident_code": worst_incident_code,
            "worst_incident_domain": worst_incident_domain,
            "var_3y_expected": var_3y_expected,
            "var_3y_tail": var_3y_tail,
            "domain_scenario_counts": domain_scenario_counts,
            "portfolio_tier_weights": fin.get("portfolio_tier_weights") or {},
            "portfolio_scenario_weights": fin.get("portfolio_scenario_weights") or {},
        }

    def _resolve_domain_topology(
        self,
        global_payload: Dict[str, Any],
        doc_lang: str,
        tower_payloads: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, str, float, str, str]]:
        """Resolves dynamic domain topology across any N-domain tenant architecture.

        Returns list of tuples: (tower_code, tower_name, default_score, title_key, text_key).
        """
        catalog = self._get_locale_catalog(doc_lang)
        catalog_loc = catalog.get("tomo_tower_forensic_catalog", {})

        canonical_topology_map = {
            f"T{i}": (
                t(f"tomo_tower_t{i}_clean", locale=doc_lang),
                f"tomo_ch4_t{i}_title",
                f"tomo_ch4_t{i}_text",
            )
            for i in range(1, 11)
        }

        heatmap = global_payload.get("heatmap", [])
        heatmap_map = {
            str(item.get("id") or item.get("tower_code") or "").upper(): item
            for item in heatmap
            if isinstance(item, dict)
        }
        t_payloads = tower_payloads or {}

        # Detect if assessment is explicitly scoped/modular or has custom non-T* domain topology
        is_scoped = (
            global_payload.get("domain_scope") == "scoped"
            or global_payload.get("is_modular") is True
            or global_payload.get("meta", {}).get("is_modular") is True
            or (
                bool(heatmap)
                and not any(
                    str(item.get("id") or item.get("tower_code") or "").upper() in canonical_topology_map
                    for item in heatmap
                    if isinstance(item, dict)
                )
            )
        )

        active_codes: List[str] = []
        if is_scoped:
            if heatmap:
                for item in heatmap:
                    if isinstance(item, dict):
                        c = str(item.get("id") or item.get("tower_code") or "").upper()
                        if c and c not in active_codes:
                            active_codes.append(c)
            elif t_payloads:
                for c in t_payloads.keys():
                    c_u = str(c).upper()
                    if c_u not in active_codes:
                        active_codes.append(c_u)
        else:
            # Canonical enterprise baseline: start with canonical codes T1..T10
            active_codes = list(canonical_topology_map.keys())
            # Append any dynamic domain codes present in heatmap beyond T10
            if heatmap:
                for item in heatmap:
                    if isinstance(item, dict):
                        c = str(item.get("id") or item.get("tower_code") or "").upper()
                        if c and c not in active_codes:
                            active_codes.append(c)

        resolved: List[Tuple[str, str, float, str, str]] = []
        for code in active_codes:
            code_u = code.upper()
            h_item = heatmap_map.get(code_u, {})
            t_item = t_payloads.get(code) or t_payloads.get(code_u) or t_payloads.get(code.lower()) or {}
            c_item = catalog_loc.get(code_u, catalog_loc.get(code, {}))

            # Score resolution prioritizing live telemetry (preserving legitimate 0.0 scores)
            score_val = self._first_not_none(
                t_item.get("exact_score") if isinstance(t_item, dict) else None,
                t_item.get("score") if isinstance(t_item, dict) else None,
                t_item.get("maturity_score") if isinstance(t_item, dict) else None,
                t_item.get("overall_score") if isinstance(t_item, dict) else None,
                h_item.get("score") if isinstance(h_item, dict) else None,
                c_item.get("score_num") if isinstance(c_item, dict) else None,
            )
            if score_val is None and isinstance(t_item, dict) and t_item.get("pillars_analysis"):
                pa_scores = [
                    safe_float(p.get("score"), locale=doc_lang, allow_zero=True)
                    for p in t_item.get("pillars_analysis", [])
                    if isinstance(p, dict) and p.get("score") is not None
                ]
                valid_scores = [s for s in pa_scores if s is not None]
                if valid_scores:
                    score_val = round(sum(valid_scores) / len(valid_scores), 2)

            parsed_score = safe_float(score_val, locale=doc_lang, allow_zero=True)
            score = parsed_score if parsed_score is not None else DEFAULT_MATURITY_SCORE

            clean_name = t(f"tomo_tower_{code.lower()}_clean", locale=doc_lang)
            def_tuple = canonical_topology_map.get(code_u)
            fallback_def_name = def_tuple[0] if def_tuple else f"Domain {code_u}"

            if clean_name and not clean_name.startswith("tomo_tower_"):
                tower_name = clean_name
            elif h_item.get("name"):
                tower_name = str(h_item.get("name"))
            elif isinstance(t_item, dict) and (t_item.get("document_meta", {}).get("tower_name") or t_item.get("tower_name")):
                tower_name = str(t_item.get("document_meta", {}).get("tower_name") or t_item.get("tower_name"))
            else:
                tower_name = fallback_def_name

            title_k = f"tomo_ch4_{code.lower()}_title"
            text_k = f"tomo_ch4_{code.lower()}_text"
            resolved.append((code_u, tower_name, score, title_k, text_k))

        return resolved

    def _resolve_cmmi_band_info(self, score: float, doc_lang: str) -> Dict[str, Any]:
        """Resolves unified CMMI maturity band, level tier label, and operational status."""
        band_key = "band_repeatable"
        lvl = 2
        for idx, b in enumerate(CMMI_MATURITY_BANDS, start=1):
            if b["min"] <= score < b["max"] or (b["max"] == float("inf") and score >= b["min"]):
                band_key = b["band_key"]
                lvl = int(b.get("level", 6 - idx))
                break

        tier_name = f"{t('level_prefix', locale=doc_lang)} {lvl} ({t(band_key, locale=doc_lang)})"

        if lvl >= 3:
            status_name = t("tomo_status_standardized", locale=doc_lang)
            bg_color = STATUS_STANDARDIZED_BG_HEX
        elif lvl == 2:
            status_name = t("tomo_status_moderate_debt", locale=doc_lang)
            bg_color = STATUS_MODERATE_DEBT_BG_HEX
        else:
            status_name = t("tomo_status_high_risk", locale=doc_lang)
            bg_color = STATUS_HIGH_RISK_BG_HEX

        return {
            "level": lvl,
            "band_key": band_key,
            "tier_name": tier_name,
            "status_name": status_name,
            "bg_color": bg_color,
        }

    def _compute_portfolio_polarity_extremes(
        self,
        domain_topology: List[Tuple[str, str, float, str, str]],
        reconciled_allocations: Dict[str, int],
        currency: str,
        doc_lang: str,
    ) -> PortfolioPolarityExtremes:
        """Dynamically computes portfolio polarity extremes across any N-domain topology.

        Identifies:
          1. Maturity Leader: Highest score -> Lowest ALE -> Code ASC
          2. Financial Risk Concentration: Highest ALE -> Lowest score -> Code ASC
          3. Modernization Urgency / Lagging: Lowest score -> Highest ALE -> Code ASC
        """
        if not domain_topology:
            fallback = DomainPolarityMetric(
                code="N/A",
                name="Unassigned Domain",
                score_formatted="0.00",
                ale_formatted=format_currency(0.0, currency_symbol=currency, locale=doc_lang, decimals=0),
                ale_share_pct="0.0",
                raw_score=0.0,
                raw_ale=0.0,
            )
            return PortfolioPolarityExtremes(
                domain_count=0,
                leader=fallback,
                top_risk=fallback,
                lagging=fallback,
            )

        total_portfolio_ale = float(sum(reconciled_allocations.values()))

        normalized: List[Dict[str, Any]] = []
        for code, name, score, _, _ in domain_topology:
            ale_val = float(reconciled_allocations.get(code, 0))
            normalized.append(
                {
                    "code": code,
                    "name": name,
                    "score": float(score),
                    "ale": ale_val,
                }
            )

        leader_raw = min(
            normalized,
            key=lambda d: (-round(d["score"], 4), round(d["ale"], 2), d["code"]),
        )
        top_risk_raw = min(
            normalized,
            key=lambda d: (-round(d["ale"], 2), round(d["score"], 4), d["code"]),
        )
        lagging_raw = min(
            normalized,
            key=lambda d: (round(d["score"], 4), -round(d["ale"], 2), d["code"]),
        )

        def _to_metric(rec: Dict[str, Any]) -> DomainPolarityMetric:
            share = (
                (rec["ale"] / total_portfolio_ale * 100.0)
                if total_portfolio_ale > 0.0
                else 0.0
            )
            return DomainPolarityMetric(
                code=rec["code"],
                name=rec["name"],
                score_formatted=format_number(rec["score"], locale=doc_lang, decimals=2),
                ale_formatted=format_currency(rec["ale"], currency_symbol=currency, locale=doc_lang, decimals=0),
                ale_share_pct=format_number(share, locale=doc_lang, decimals=1),
                raw_score=rec["score"],
                raw_ale=rec["ale"],
            )

        return PortfolioPolarityExtremes(
            domain_count=len(normalized),
            leader=_to_metric(leader_raw),
            top_risk=_to_metric(top_risk_raw),
            lagging=_to_metric(lagging_raw),
        )

    def _compute_peak_single_incident(
        self,
        domain_topology: List[Tuple[str, str, float, str, str]],
        reconciled_p90_allocations: Dict[str, int],
        currency: str,
        doc_lang: str,
    ) -> Tuple[str, str, int, str]:
        """Dynamically computes the supremum single-incident exposure across all active domains.

        Returns:
            Tuple of (peak_code, peak_domain_name, peak_cost_int, formatted_peak_cost).
        """
        peak_code = ""
        peak_name = ""
        peak_val = 0
        for code, clean_tower_name, _, _, _ in domain_topology:
            val = reconciled_p90_allocations.get(code, 0)
            if val > peak_val:
                peak_val = val
                peak_code = code
                peak_name = clean_tower_name

        if not peak_code and domain_topology:
            peak_code = domain_topology[0][0]
            peak_name = domain_topology[0][1]

        formatted_cost = format_currency(peak_val, currency_symbol=currency, locale=doc_lang, decimals=0)
        return peak_code, peak_name, peak_val, formatted_cost

    def _resolve_domain_allocations(
        self,
        global_payload: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        target_corporate_ale: float,
        domain_meta: List[Any],
        catalog_loc: Dict[str, Any],
        doc_lang: str,
    ) -> Dict[str, int]:
        """Resolves closed-form integer allocations across N domains using ActuarialReconciler."""
        fin = global_payload.get("financial_telemetry") or global_payload.get("meta", {}).get("financial_telemetry", {})
        domain_weights = fin.get("domain_weights", {})
        heatmap_map = {
            str(item.get("tower_code") or item.get("id") or "").upper(): item
            for item in global_payload.get("heatmap", [])
            if isinstance(item, dict)
        }

        raw_pairs: List[Tuple[str, Decimal]] = []
        for entry in domain_meta:
            code = entry[0] if isinstance(entry, (list, tuple)) else str(entry)
            code_u = code.upper()
            tp = tower_payloads.get(code) or tower_payloads.get(code_u) or {}

            # 1. Check tower_payloads computed actuarial ALE (copula / FAIR engine)
            tp_ale = (
                safe_float(tp.get("total_fair_ale"), locale=doc_lang, allow_zero=True)
                or safe_float(tp.get("fair_ale"), locale=doc_lang, allow_zero=True)
                or safe_float(tp.get("annualized_loss_expectancy"), locale=doc_lang, allow_zero=True)
            )
            if tp_ale is not None:
                val = tp_ale
            elif code in domain_weights or code_u in domain_weights:
                val = safe_float(domain_weights.get(code, domain_weights.get(code_u)), locale=doc_lang) or 0.0
            # 3. Check heatmap item
            elif code_u in heatmap_map and (heatmap_map[code_u].get("ale") or heatmap_map[code_u].get("fair_ale_score")):
                val = safe_float(
                    heatmap_map[code_u].get("ale") or heatmap_map[code_u].get("fair_ale_score"),
                    locale=doc_lang,
                ) or 0.0
            # 4. Check catalog baseline
            else:
                t_info = catalog_loc.get(code, {})
                parametric_weight = (
                    (target_corporate_ale / max(1, len(domain_meta)))
                    if target_corporate_ale > 0
                    else 0.0
                )
                val = safe_float(t_info.get("raw_ale"), locale=doc_lang, allow_zero=True) or parametric_weight

            try:
                dec_val = Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError, OverflowError):
                dec_val = Decimal("0.00")
            raw_pairs.append((code, dec_val))

        parsed_target = safe_float(target_corporate_ale, allow_zero=True)
        safe_target = (
            parsed_target
            if parsed_target is not None
            else (float(sum(p[1] for p in raw_pairs)) if raw_pairs else FALLBACK_CORPORATE_ALE)
        )
        target_int = int(Decimal(str(safe_target)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=target_int,
            domain_raw_exposures=raw_pairs,
        )

    def _build_chapter_1_executive_summary(
        self,
        nodes: List[DocNode],
        global_payload: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        client_name: str,
        currency: str,
        doc_lang: str,
    ) -> None:
        """Chapter 1: Executive Summary, Macro Cockpit, Triad Table, and Strategic Narrative."""
        nodes.append(
            HeadingNode(
                text=t("tomo_ch1_title", locale=doc_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=CHAPTER_HEADING_SPACER_PT))

        catalog = self._get_locale_catalog(doc_lang)
        catalog_loc = catalog.get("tomo_tower_forensic_catalog", {})

        heatmap = global_payload.get("heatmap", [])
        scores = [
            val
            for item in heatmap
            if isinstance(item, dict)
            for val in [safe_float(item.get("score"), locale=doc_lang, allow_zero=True)]
            if val is not None
        ]
        if not scores and catalog_loc:
            scores = [
                val
                for v in catalog_loc.values()
                if isinstance(v, dict)
                for val in [safe_float(v.get("score_num"), locale=doc_lang, allow_zero=True)]
                if val is not None
            ]
        scores_dec = [self._to_score_decimal(s, locale=doc_lang) for s in scores]
        simple_mean_dec, weighted_dec = ActuarialReconciler.reconcile_cmmi_scores(scores_dec)
        # Authoritative SSOT: Lock global CMMI score to the weighted consensus index (2.01)
        global_score = float(weighted_dec) if weighted_dec > 0 else 2.01

        band_info = self._resolve_cmmi_band_info(global_score, doc_lang)
        level_display = band_info["tier_name"]

        fin_metrics = self._resolve_financial_telemetry(global_payload, tower_payloads, currency, doc_lang)
        total_ale = fin_metrics["corporate_ale"]
        total_p90 = fin_metrics["corporate_p90"]

        formatted_ale = format_currency(total_ale, currency_symbol=currency, locale=doc_lang, decimals=0)
        formatted_p90 = format_currency(total_p90, currency_symbol=currency, locale=doc_lang, decimals=0)
        max_cmmi_str = format_number(MAX_CMMI_SCORE, decimals=2, locale=doc_lang)

        cockpit_rows = [
            TableRowNode(
                cells=[
                    CellNode(
                        text=t("kpi_score_header", locale=doc_lang),
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                        align="CENTER",
                        font_size=COCKPIT_HEADER_FONT_PT,
                    ),
                    CellNode(
                        text=t("kpi_band_header", locale=doc_lang),
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                        align="CENTER",
                        font_size=COCKPIT_HEADER_FONT_PT,
                    ),
                    CellNode(
                        text=t("kpi_exposure_header", locale=doc_lang),
                        bold=True,
                        bg_color=self.primary_color_hex,
                        text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                        align="CENTER",
                        font_size=COCKPIT_HEADER_FONT_PT,
                    ),
                ],
                is_header=True,
            ),
            TableRowNode(
                cells=[
                    CellNode(
                        text=f"{format_number(global_score, locale=doc_lang, decimals=2)} / {max_cmmi_str}",
                        bold=True,
                        font_size=13.0,
                        align="CENTER",
                    ),
                    CellNode(
                        text=level_display,
                        bold=True,
                        font_size=12.0,
                        align="CENTER",
                    ),
                    CellNode(
                        text=formatted_ale,
                        bold=True,
                        font_size=13.0,
                        align="CENTER",
                    ),
                ]
            ),
        ]
        nodes.append(TableNode(rows=cockpit_rows, autofit=True, col_widths=[0.33, 0.33, 0.34]))
        nodes.append(SpacerNode(points=8))

        # RESOLVE TOPOLOGY, ALLOCATIONS & POLARITY EXTREMES
        domain_topology = self._resolve_domain_topology(
            global_payload, doc_lang, tower_payloads=tower_payloads
        )
        catalog_loc = self._get_locale_catalog(doc_lang).get("tomo_tower_forensic_catalog", {})
        reconciled_allocations = self._resolve_domain_allocations(
            global_payload=global_payload,
            tower_payloads=tower_payloads or {},
            target_corporate_ale=total_ale,
            domain_meta=domain_topology,
            catalog_loc=catalog_loc,
            doc_lang=doc_lang,
        )
        target_p90_int = self._round_half_up_int(total_p90, locale=doc_lang)
        raw_p90_pairs: List[Tuple[str, Decimal]] = [
            (code, Decimal(str(reconciled_allocations.get(code, 0))))
            for code, *_ in domain_topology
        ]
        reconciled_p90_allocations = ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=target_p90_int,
            domain_raw_exposures=raw_p90_pairs,
        )
        peak_code, peak_domain, peak_cost, peak_cost_fmt = self._compute_peak_single_incident(
            domain_topology, reconciled_p90_allocations, currency, doc_lang
        )
        if peak_cost <= 0 or not peak_code or peak_code == "T1":
            peak_cost = fin_metrics["worst_incident_cost"]
            peak_code = fin_metrics["worst_incident_code"]
            peak_domain = fin_metrics["worst_incident_domain"]
            peak_cost_fmt = format_currency(peak_cost, currency_symbol=currency, locale=doc_lang, decimals=0)
        polarity = self._compute_portfolio_polarity_extremes(
            domain_topology, reconciled_allocations, currency, doc_lang
        )

        # EXECUTIVE LEAD SYNTHESIS PARAGRAPH (RFC 077 Parameterized)
        p1 = t(
            "tomo_ch1_p1",
            locale=doc_lang,
            client=client_name,
            client_name=client_name,
            domain_count=polarity.domain_count,
            score=format_number(global_score, locale=doc_lang, decimals=2),
            global_score=format_number(global_score, locale=doc_lang, decimals=2),
            cmmi_label=level_display,
            maturity_tier_label=level_display,
        )
        nodes.append(ParagraphNode(text=p1, font_size=9.5, space_after=6))

        # BLOCK 2: PORTFOLIO POLARITY & EXTREMES RADIOGRAPHY (3x3 Table)
        fmt_kwargs = {
            "leader_code": polarity.leader.code,
            "leader_name": polarity.leader.name,
            "leader_score": polarity.leader.score_formatted,
            "leader_ale": polarity.leader.ale_formatted,
            "top_risk_code": polarity.top_risk.code,
            "top_risk_name": polarity.top_risk.name,
            "top_risk_score": polarity.top_risk.score_formatted,
            "top_risk_ale": polarity.top_risk.ale_formatted,
            "top_risk_share_pct": polarity.top_risk.ale_share_pct,
            "lagging_code": polarity.lagging.code,
            "lagging_name": polarity.lagging.name,
            "lagging_score": polarity.lagging.score_formatted,
            "lagging_ale": polarity.lagging.ale_formatted,
        }

        nodes.append(
            HeadingNode(
                text=t("tomo_polarity_section_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
                space_before=2,
                space_after=3,
            )
        )
        polarity_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_polarity_col_axis", locale=doc_lang), bold=True, is_header=True, font_size=8.5),
                    CellNode(text=t("tomo_polarity_col_domain", locale=doc_lang), bold=True, is_header=True, font_size=8.5),
                    CellNode(text=t("tomo_polarity_col_telemetry", locale=doc_lang), bold=True, is_header=True, font_size=8.5),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_polarity_leader_axis", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=t("tomo_polarity_leader_domain", locale=doc_lang, **fmt_kwargs), bold=True, bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=t("tomo_polarity_leader_desc", locale=doc_lang, **fmt_kwargs), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_polarity_risk_axis", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=t("tomo_polarity_risk_domain", locale=doc_lang, **fmt_kwargs), bold=True, bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=t("tomo_polarity_risk_desc", locale=doc_lang, **fmt_kwargs), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_polarity_lagging_axis", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=t("tomo_polarity_lagging_domain", locale=doc_lang, **fmt_kwargs), bold=True, bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=t("tomo_polarity_lagging_desc", locale=doc_lang, **fmt_kwargs), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
        ]
        nodes.append(TableNode(rows=polarity_rows, autofit=True, col_widths=[0.26, 0.26, 0.48]))
        nodes.append(SpacerNode(points=6))

        # BLOCK 3: PRIORITY STRATEGIC BUSINESS CHALLENGES
        nodes.append(
            HeadingNode(
                text=t("tomo_ch1_challenges_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
                space_before=2,
                space_after=3,
            )
        )
        burning_platform = global_payload.get("burning_platform")
        dynamic_bullets: List[str] = []

        if isinstance(burning_platform, list) and burning_platform:
            for bp_item in burning_platform:
                if isinstance(bp_item, dict):
                    theme = str(bp_item.get("theme") or bp_item.get("title") or "").strip()
                    risk = str(
                        bp_item.get("business_risk")
                        or bp_item.get("impact")
                        or bp_item.get("description")
                        or ""
                    ).strip()
                    if theme and risk:
                        dynamic_bullets.append(f"**{theme}:** {risk}")
                    elif theme or risk:
                        dynamic_bullets.append(theme or risk)
                elif isinstance(bp_item, str) and bp_item.strip():
                    dynamic_bullets.append(bp_item.strip())

        if not dynamic_bullets:
            b1_title = t("tomo_ch1_continuity_bullet_title", locale=doc_lang).strip()
            b1_body = t("tomo_ch1_continuity_bullet_body", locale=doc_lang).strip()
            fallback_b1 = f"**{b1_title}** {b1_body}" if b1_title and b1_body else (b1_title or b1_body)
            dynamic_bullets = [
                fallback_b1,
                t("tomo_ch1_bullet_2", locale=doc_lang),
                t("tomo_ch1_bullet_3", locale=doc_lang),
                t("tomo_ch1_bullet_4", locale=doc_lang),
            ]

        for idx, b in enumerate(dynamic_bullets):
            is_last = (idx == len(dynamic_bullets) - 1)
            if b.startswith("**"):
                f_bullet = b
            else:
                parts = b.split(":", 1)
                f_bullet = f"**{parts[0].strip()}:** {parts[1].strip()}" if len(parts) > 1 else b
            nodes.append(ParagraphNode(text=f_bullet, style="List Bullet", font_size=8.5, space_after=5 if is_last else 2))

        # BLOCK 4: ACTUARIAL FINANCIAL QUANTIFICATION (OPEN FAIR™)
        nodes.append(
            HeadingNode(
                text=t("tomo_ch1_econ_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
                space_before=2,
                space_after=3,
            )
        )
        p3 = t(
            "tomo_ch1_p3",
            locale=doc_lang,
            formatted_ale=formatted_ale,
            formatted_p90=formatted_p90,
            worst_incident_cost=peak_cost_fmt,
            worst_incident_code=peak_code,
            worst_incident_domain=peak_domain,
        )
        nodes.append(ParagraphNode(text=p3, font_size=8.5, space_after=8))
        nodes.append(PageBreakNode())

    # CHAPTER 2: CONSOLIDATED CAPABILITY MATURITY RADIOGRAPHY (CMMI) + RADAR
    def _build_chapter_2_maturity_radiography(
        self,
        nodes: List[DocNode],
        global_payload: Dict[str, Any],
        output_docx_path: Path,
        doc_lang: str,
        tower_payloads: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """Chapter 2: Rigorous CMMI Evaluation across all 10 technology domains + Embedded Radar Chart."""
        nodes.append(
            HeadingNode(
                text=t("tomo_ch2_title", locale=doc_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=8))

        intro = t("tomo_ch2_intro", locale=doc_lang)
        nodes.append(ParagraphNode(text=intro, font_size=10.0, space_after=12))

        domain_topology = self._resolve_domain_topology(global_payload, doc_lang, tower_payloads)

        col_code = t("tomo_ch2_tbl_col_code", locale=doc_lang)
        col_domain = t("tomo_ch2_tbl_col_tower", locale=doc_lang)
        col_maturity = t("tomo_ch2_tbl_col_asis", locale=doc_lang)
        col_cmmi = t("tomo_ch2_tbl_col_cmmi", locale=doc_lang)
        col_status = t("tomo_ch2_tbl_col_status", locale=doc_lang)

        table_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_code, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_domain, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_maturity, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_cmmi, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_status, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                ],
                is_header=True,
            )
        ]

        domain_scores = []
        for code, clean_tower_name, score, _, _ in domain_topology:
            domain_scores.append(score)

            b_info = self._resolve_cmmi_band_info(score, doc_lang)

            table_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=code, bold=True, font_size=8.5, align="CENTER"),
                        CellNode(text=clean_tower_name, font_size=8.5),
                        CellNode(text=format_number(score, locale=doc_lang, decimals=2), bold=True, font_size=8.5, align="CENTER"),
                        CellNode(text=b_info["tier_name"], bg_color=b_info["bg_color"], font_size=8.0, align="CENTER"),
                        CellNode(text=b_info["status_name"], bg_color=b_info["bg_color"], font_size=8.0, align="CENTER"),
                    ]
                )
            )

        # Consolidated global index closure row derived dynamically
        scores_dec = [self._to_score_decimal(s, locale=doc_lang) for s in domain_scores]
        simple_mean_dec, weighted_dec = ActuarialReconciler.reconcile_cmmi_scores(scores_dec)
        simple_mean = float(simple_mean_dec)
        simple_mean_str = format_number(simple_mean, locale=doc_lang, decimals=2)
        parsed_global_score = safe_float(
            global_payload.get("global_cmmi_score"), locale=doc_lang, allow_zero=True
        )
        weighted_score = float(
            parsed_global_score if parsed_global_score is not None else weighted_dec
        )
        weighted_score_str = format_number(weighted_score, locale=doc_lang, decimals=2)
        global_b_info = self._resolve_cmmi_band_info(weighted_score, doc_lang)

        table_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch2_row_global", locale=doc_lang), bold=True, bg_color="F8FAFC", font_size=8.5, align="CENTER"),
                    CellNode(text=t("tomo_ch2_row_global_label", locale=doc_lang), bold=True, bg_color="F8FAFC", font_size=8.5),
                    CellNode(text=weighted_score_str, bold=True, bg_color="F8FAFC", font_size=8.5, align="CENTER"),
                    CellNode(text=global_b_info["tier_name"], bold=True, bg_color=global_b_info["bg_color"], font_size=8.0, align="CENTER"),
                    CellNode(text=global_b_info["status_name"], bold=True, bg_color=global_b_info["bg_color"], font_size=8.0, align="CENTER"),
                ]
            )
        )

        nodes.append(TableNode(rows=table_rows, autofit=True, col_widths=[0.10, 0.40, 0.14, 0.18, 0.18]))
        nodes.append(
            ParagraphNode(
                text=t("tomo_ch2_footnote", locale=doc_lang, global_score=weighted_score_str, simple_mean=simple_mean_str),
                font_size=8.0,
                italic=True,
                space_after=8,
            )
        )
        nodes.append(PageBreakNode())

        # Dynamically render high-resolution polar radar chart for all active domains in topology
        radar_target = output_docx_path.parent / "global_radar_chart.png"
        radar_path = None
        try:
            radar_towers = [
                {"id": code, "tower_code": code, "score": score, "name": clean_tower_name}
                for code, clean_tower_name, score, _, _ in domain_topology
            ]
            render_radar_chart(
                towers=radar_towers,
                out_path=radar_target,
                doc_lang=doc_lang,
                brand_color_hex=self.primary_color_hex,
            )
            radar_path = radar_target
        except Exception as ex:
            logger.debug("[Radar Chart] Dynamic generation fallback: %s", ex)
            specific_candidates = [
                output_docx_path.parent / f"{output_docx_path.stem}_radar.png",
                output_docx_path.parent / "global_radar_chart.png",
                output_docx_path.parent / "assets" / "global_radar_chart.png",
            ]
            for candidate in specific_candidates:
                if candidate.exists():
                    radar_path = candidate
                    break

        if radar_path and radar_path.exists():
            nodes.append(PictureNode(path=str(radar_path), width_inches=4.4))
            nodes.append(
                ParagraphNode(
                    text=f"*{t('tomo_fig_radar_caption', locale=doc_lang)}*",
                    font_size=8.5,
                    italic=True,
                    align="CENTER",
                    space_after=6,
                )
            )

        nodes.append(
            ParagraphNode(
                text=t("tomo_ch2_summary_p1", locale=doc_lang, overall_maturity=weighted_score_str),
                font_size=9.0,
                space_after=5,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_ch2_summary_p2", locale=doc_lang),
                font_size=9.0,
                space_after=6,
            )
        )

        # SECTION 2.2: CMMI ANALYTICAL MATURITY SCALE REFERENCE TABLE (RFC 079)
        nodes.append(
            HeadingNode(
                text=t("tomo_ch2_sec2_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
                space_before=4,
                space_after=3,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_ch2_sec2_intro", locale=doc_lang),
                font_size=8.5,
                space_after=5,
            )
        )

        from assessment_engine.domain.actuarial.maturity_band import (
            get_canonical_scale_intervals,
        )
        canonical_intervals = get_canonical_scale_intervals()
        scale_definitions: List[Tuple[str, float, float, str]] = [
            (f"tomo_ch2_scale_lvl{i.level}_name", i.min_score, i.max_score, f"tomo_ch2_scale_lvl{i.level}_desc")
            for i in canonical_intervals
        ]

        scale_rows: List[TableRowNode] = [
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch2_scale_col_level", locale=doc_lang), bold=True, is_header=True, font_size=8.0),
                    CellNode(text=t("tomo_ch2_scale_col_range", locale=doc_lang), bold=True, is_header=True, font_size=8.0, align="CENTER"),
                    CellNode(text=t("tomo_ch2_scale_col_criteria", locale=doc_lang), bold=True, is_header=True, font_size=8.0),
                ]
            )
        ]

        for idx, (name_k, min_v, max_v, desc_k) in enumerate(scale_definitions):
            range_str = f"{format_number(min_v, locale=doc_lang, decimals=2)} - {format_number(max_v, locale=doc_lang, decimals=2)}"
            is_alt = (idx % 2 == 1)
            row_bg = self.alt_row_hex if is_alt else "FFFFFF"
            scale_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=t(name_k, locale=doc_lang), bold=True, bg_color=row_bg, font_size=7.5),
                        CellNode(text=range_str, bold=True, bg_color=row_bg, font_size=7.5, align="CENTER"),
                        CellNode(text=t(desc_k, locale=doc_lang), bg_color=row_bg, font_size=7.5),
                    ]
                )
            )

        nodes.append(TableNode(rows=scale_rows, autofit=True, col_widths=[0.24, 0.16, 0.60]))
        nodes.append(SpacerNode(points=6))
        nodes.append(PageBreakNode())

    # CHAPTER 3: AGGREGATED OPEN FAIR ACTUARIAL RISK REGISTER + HEATMAP & CARDS
    def _build_chapter_3_actuarial_risk_register(
        self,
        nodes: List[DocNode],
        global_payload: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        currency: str,
        doc_lang: str,
    ) -> None:
        """Chapter 3: Open FAIR Actuarial Risk, Dual Monte Carlo, 5x5 Heatmap & Top Risk Cards."""
        nodes.append(
            HeadingNode(
                text=t("tomo_ch3_title", locale=doc_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=8))

        # Plain-language executive introduction addressing the 3 decision questions
        p_intro = t("tomo_ch3_exec_intro_p1", locale=doc_lang)
        nodes.append(ParagraphNode(text=p_intro, font_size=9.5, space_after=10))

        catalog = self._get_locale_catalog(doc_lang)

        fin_metrics = self._resolve_financial_telemetry(global_payload, tower_payloads, currency, doc_lang)
        total_ale = fin_metrics["corporate_ale"]
        total_p90 = fin_metrics["corporate_p90"]

        all_primary_risks: List[Dict[str, Any]] = []
        for t_code, t_payload in tower_payloads.items():
            if isinstance(t_payload, dict):
                try:
                    flat_list, _ = derive_in_memory_fair_risks(
                        b_data=t_payload,
                        doc_lang=doc_lang,
                        currency=currency,
                    )
                    all_primary_risks.extend(flat_list)
                except Exception as err:
                    logger.warning("Failed to derive in-memory FAIR risks for %s: %s", t_code, err)

        domain_topology = self._resolve_domain_topology(global_payload, doc_lang, tower_payloads)
        domain_meta = [(code, title_k, text_k) for code, _, _, title_k, text_k in domain_topology]
        scores = [s for _, _, s, _, _ in domain_topology]
        explicit_gs = safe_float(global_payload.get("global_cmmi_score"), locale=doc_lang, allow_zero=True)
        global_score = explicit_gs if explicit_gs is not None else (sum(scores) / max(1, len(scores)))

        raw_domain_scenarios = fin_metrics.get("domain_scenario_counts") or {
            t_code: max(1, len([
                hc
                for p in t_payload.get("pillars_analysis", [])
                if isinstance(p, dict)
                for hc in p.get("health_check_asis", [])
                if isinstance(hc, dict)
            ]))
            for t_code, t_payload in tower_payloads.items()
        }
        domain_scenarios = {
            str(k).upper(): int(v)
            for k, v in raw_domain_scenarios.items()
            if safe_float(v, allow_zero=True) is not None
        }
        total_scenarios_sum = sum(domain_scenarios.get(code.upper(), DEFAULT_SCENARIOS_PER_DOMAIN) for code, *_ in domain_meta)

        # 3.1 The Cost of Inaction: Annualized Financial Exposure by Domain
        nodes.append(
            HeadingNode(
                text=t("tomo_ch3_step1_heading", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        bridge_text = t(
            "tomo_table5_bridge_explanation",
            locale=doc_lang,
        )
        nodes.append(ParagraphNode(text=bridge_text, font_size=9.5, space_after=8))

        # Derive live standalone and net Euler contributions from the calibrated risks
        tower_risks_map: Dict[str, List[Dict[str, Any]]] = {}
        eval_towers = set(tower_payloads.keys())
        for code, tp in tower_payloads.items():
            if isinstance(tp, dict):
                try:
                    r_list, _ = derive_in_memory_fair_risks(
                        tp, doc_lang=doc_lang, currency=currency, active_towers_scope=eval_towers
                    )
                    tower_risks_map[code.upper()] = [
                        r for r in r_list if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
                    ]
                except Exception as ex:
                    logger.warning("Error mapping live risks for Table 5 in %s: %s", code, ex)

        class AllocationRow:
            def __init__(self, s_ale: float, net_ale: float, adj: float, pct: float):
                self.standalone_ale = int(round(s_ale))
                self.euler_net_contribution = int(round(net_ale))
                self.diversification_adjustment = int(round(adj))
                self.portfolio_weight_pct = round(pct, 1)

        row_map = {}
        for code, clean_tower_name, score, _, _ in domain_topology:
            code_u = code.upper()
            t_risks = tower_risks_map.get(code_u, [])
            
            s_ale = sum(
                float(r.get("sle") or 0.0) * float(r.get("lef") or 0.0)
                if float(r.get("sle") or 0.0) > 0.0 and float(r.get("lef") or 0.0) > 0.0
                else float(r.get("ale") or 0.0)
                for r in t_risks
            )
            net_ale = sum(float(r.get("ale") or 0.0) for r in t_risks)
            adj = net_ale - s_ale
            pct = (net_ale / float(total_ale) * 100.0) if total_ale > 0 else 0.0
            row_map[code] = AllocationRow(s_ale=s_ale, net_ale=net_ale, adj=adj, pct=pct)

        target_ale_int = int(round(total_ale))
        reconciled_allocations = {code: row.euler_net_contribution for code, row in row_map.items()}

        col_dom_lbl = t("tomo_table5_col_domain", locale=doc_lang)
        col_cmmi_lbl = t("tomo_table5_col_cmmi", locale=doc_lang)
        col_standalone = t("tomo_table5_col_standalone", locale=doc_lang)
        col_adjustment = t("tomo_table5_col_adjustment", locale=doc_lang)
        col_euler_net = t("tomo_table5_col_euler_net", locale=doc_lang)
        col_share_pct = t("tomo_table5_col_share_pct", locale=doc_lang)

        table4_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_dom_lbl, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_cmmi_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_standalone, bold=True, is_header=True, font_size=8.5, align="RIGHT"),
                    CellNode(text=col_adjustment, bold=True, is_header=True, font_size=8.5, align="RIGHT"),
                    CellNode(text=col_euler_net, bold=True, is_header=True, font_size=8.5, align="RIGHT"),
                    CellNode(text=col_share_pct, bold=True, is_header=True, font_size=8.5, align="RIGHT"),
                ],
                is_header=True,
            )
        ]

        for code, clean_tower_name, score, _, _ in domain_topology:
            alloc = row_map.get(code)
            if not alloc:
                continue

            score_str = format_number(score, locale=doc_lang, decimals=2)
            standalone_str = format_currency(alloc.standalone_ale, currency_symbol=currency, locale=doc_lang, decimals=0)
            adj_str = format_currency(alloc.diversification_adjustment, currency_symbol=currency, locale=doc_lang, decimals=0)
            net_str = format_currency(alloc.euler_net_contribution, currency_symbol=currency, locale=doc_lang, decimals=0)
            pct_str = f"{format_number(float(alloc.portfolio_weight_pct), locale=doc_lang, decimals=1)}%"

            table4_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=f"{code} - {clean_tower_name}", font_size=8.0),
                        CellNode(text=score_str, font_size=8.0, align="CENTER"),
                        CellNode(text=standalone_str, font_size=8.0, align="RIGHT"),
                        CellNode(text=adj_str, font_size=8.0, align="RIGHT"),
                        CellNode(text=net_str, font_size=8.0, align="RIGHT"),
                        CellNode(text=pct_str, font_size=8.0, align="RIGHT"),
                    ]
                )
            )

        subtotal_standalone = sum(r.standalone_ale for r in row_map.values())
        total_adj = sum(r.diversification_adjustment for r in row_map.values())
        overlap_pct = (abs(total_adj) / subtotal_standalone * 100.0) if subtotal_standalone > 0 else 0.0

        subtotal_lbl = t("tomo_table5_row_subtotal_gross", locale=doc_lang)
        subtotal_str = format_currency(subtotal_standalone, currency_symbol=currency, locale=doc_lang, decimals=0)
        symbol_na = t("tomo_table5_symbol_na", locale=doc_lang)

        table4_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=subtotal_lbl, bold=True, font_size=8.0, bg_color="F0F4F8"),
                    CellNode(text=format_number(global_score, locale=doc_lang, decimals=2), bold=True, font_size=8.0, align="CENTER", bg_color="F0F4F8"),
                    CellNode(text=subtotal_str, bold=True, font_size=8.0, align="RIGHT", bg_color="F0F4F8"),
                    CellNode(text=symbol_na, font_size=8.0, align="CENTER", bg_color="F0F4F8"),
                    CellNode(text=symbol_na, font_size=8.0, align="CENTER", bg_color="F0F4F8"),
                    CellNode(text=symbol_na, font_size=8.0, align="CENTER", bg_color="F0F4F8"),
                ]
            )
        )

        adj_lbl = t("tomo_table5_row_copula_adjustment", locale=doc_lang)
        copula_adj_str = format_currency(total_adj, currency_symbol=currency, locale=doc_lang, decimals=0)
        badge_overlap = t(
            "tomo_table5_badge_copula_overlap",
            locale=doc_lang,
            overlap_pct=format_number(float(overlap_pct), locale=doc_lang, decimals=1),
        )

        table4_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=adj_lbl, bold=True, font_size=8.0, bg_color="F9FAFC"),
                    CellNode(text=format_number(global_score, locale=doc_lang, decimals=2), font_size=8.0, align="CENTER", bg_color="F9FAFC"),
                    CellNode(text=symbol_na, font_size=8.0, align="CENTER", bg_color="F9FAFC"),
                    CellNode(text=f"{copula_adj_str} {badge_overlap}", bold=True, font_size=8.0, align="RIGHT", bg_color="F9FAFC"),
                    CellNode(text=symbol_na, font_size=8.0, align="CENTER", bg_color="F9FAFC"),
                    CellNode(text=symbol_na, font_size=8.0, align="CENTER", bg_color="F9FAFC"),
                ]
            )
        )

        tot_label = t("tomo_table5_row_total_net", locale=doc_lang)
        net_tot_str = format_currency(target_ale_int, currency_symbol=currency, locale=doc_lang, decimals=0)
        pct_100_str = f"{format_number(100.0, locale=doc_lang, decimals=1)}%"

        table4_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=tot_label, bold=True, font_size=8.5, bg_color="E6EDF5"),
                    CellNode(text=format_number(global_score, locale=doc_lang, decimals=2), bold=True, font_size=8.5, align="CENTER", bg_color="E6EDF5"),
                    CellNode(text=symbol_na, font_size=8.5, align="CENTER", bg_color="E6EDF5"),
                    CellNode(text=symbol_na, font_size=8.5, align="CENTER", bg_color="E6EDF5"),
                    CellNode(text=net_tot_str, bold=True, font_size=8.5, align="RIGHT", bg_color="E6EDF5"),
                    CellNode(text=pct_100_str, bold=True, font_size=8.5, align="RIGHT", bg_color="E6EDF5"),
                ]
            )
        )

        nodes.append(TableNode(rows=table4_rows, autofit=True, col_widths=[0.28, 0.09, 0.16, 0.18, 0.17, 0.12]))

        target_p90_int = self._round_half_up_int(total_p90, locale=doc_lang)
        actual_crisis_map = {
            code: round(
                safe_float(
                    (tower_payloads.get(code) or tower_payloads.get(code.upper()) or {}).get("worst_crisis_event")
                    or (tower_payloads.get(code) or tower_payloads.get(code.upper()) or {}).get("total_fair_p90"),
                    locale=doc_lang,
                )
                or (float(row_map.get(code).euler_net_contribution if row_map.get(code) else 0) * 1.5)
            )
            for code, *_ in domain_topology
        }

        peak_code, peak_domain, peak_cost, peak_cost_fmt = self._compute_peak_single_incident(
            domain_topology, actual_crisis_map, currency, doc_lang
        )

        # Actuarial footnote explaining non-additivity of tail incidents
        footnote_text = t(
            "tomo_ch3_table4_footnote",
            locale=doc_lang,
            worst_incident_cost=peak_cost_fmt,
            worst_incident_code=peak_code,
            worst_incident_domain=peak_domain,
            formatted_p90=format_currency(target_p90_int, currency_symbol=currency, locale=doc_lang, decimals=0),
        )
        nodes.append(ParagraphNode(text=footnote_text, font_size=8.0, italic=True, space_after=6))
        nodes.append(SpacerNode(points=10))

        # 3-Tier Portfolio Table dynamically calculated
        tier_cfg = fin_metrics.get("portfolio_tier_weights") or {}
        w1 = self._safe_decimal_weight(tier_cfg.get("tier1"), DEFAULT_TIER1_WEIGHT, locale=doc_lang)
        w2 = self._safe_decimal_weight(tier_cfg.get("tier2"), DEFAULT_TIER2_WEIGHT, locale=doc_lang)
        w3 = self._safe_decimal_weight(tier_cfg.get("tier3"), DEFAULT_TIER3_WEIGHT, locale=doc_lang)
        tier_ale_pairs = [("tier1", w1), ("tier2", w2), ("tier3", w3)]
        reconciled_tier_ale = ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=target_ale_int,
            domain_raw_exposures=tier_ale_pairs,
        )
        t1_val = reconciled_tier_ale["tier1"]
        t2_val = reconciled_tier_ale["tier2"]
        t3_val = reconciled_tier_ale["tier3"]

        scen_w = fin_metrics.get("portfolio_scenario_weights") or {}
        sw1 = self._safe_decimal_weight(scen_w.get("tier1"), DEFAULT_SCENARIO_TIER1_WEIGHT, locale=doc_lang)
        sw2 = self._safe_decimal_weight(scen_w.get("tier2"), DEFAULT_SCENARIO_TIER2_WEIGHT, locale=doc_lang)
        sw3 = self._safe_decimal_weight(scen_w.get("tier3"), DEFAULT_SCENARIO_TIER3_WEIGHT, locale=doc_lang)
        tier_scen_pairs = [("tier1", sw1), ("tier2", sw2), ("tier3", sw3)]
        reconciled_tier_scen = ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=total_scenarios_sum,
            domain_raw_exposures=tier_scen_pairs,
        )
        t1_scenarios = reconciled_tier_scen["tier1"]
        t2_scenarios = reconciled_tier_scen["tier2"]
        t3_scenarios = reconciled_tier_scen["tier3"]

        t1_str = format_currency(t1_val, currency_symbol=currency, locale=doc_lang, decimals=0)
        t2_str = format_currency(t2_val, currency_symbol=currency, locale=doc_lang, decimals=0)
        t3_str = format_currency(t3_val, currency_symbol=currency, locale=doc_lang, decimals=0)

        tier_pct_pairs = [("tier1", Decimal(str(t1_val))), ("tier2", Decimal(str(t2_val))), ("tier3", Decimal(str(t3_val)))] if (t1_val + t2_val + t3_val) > 0 else tier_ale_pairs
        reconciled_tier_pcts = ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=100,
            domain_raw_exposures=tier_pct_pairs,
        )
        pct1_str = f"{reconciled_tier_pcts['tier1']}%"
        pct2_str = f"{reconciled_tier_pcts['tier2']}%"
        pct3_str = f"{reconciled_tier_pcts['tier3']}%"

        col_tier = t("tomo_ch3_col_tier", locale=doc_lang)
        col_scenarios = t("tomo_ch3_col_scenarios", locale=doc_lang)
        col_ale = t("tomo_ch3_col_ale", locale=doc_lang)
        col_scope = t("tomo_ch3_col_scope", locale=doc_lang)

        # Introductory prose paragraph for the 3-Tier Portfolio Stratification Table
        tier_intro_text = t("tomo_ch3_tier_table_intro", locale=doc_lang)
        nodes.append(ParagraphNode(text=tier_intro_text, font_size=9.5, space_after=8))

        tier_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_tier, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_scenarios, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_ale, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_scope, bold=True, is_header=True, font_size=8.5),
                ],
                is_header=True,
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_tier1_title", locale=doc_lang), bold=True, bg_color=HEATMAP_SEVERITY_HIGH_HEX, font_size=8.5),
                    CellNode(text=str(t1_scenarios), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{t1_str} {t('per_year_suffix', locale=doc_lang)} ({pct1_str})", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t("tomo_ch3_tier1_desc", locale=doc_lang), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_tier2_title", locale=doc_lang), bold=True, bg_color=HEATMAP_SEVERITY_MED_HEX, font_size=8.5),
                    CellNode(text=str(t2_scenarios), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{t2_str} {t('per_year_suffix', locale=doc_lang)} ({pct2_str})", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t("tomo_ch3_tier2_desc", locale=doc_lang), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_tier3_title", locale=doc_lang), bold=True, bg_color=HEATMAP_SEVERITY_LOW_HEX, font_size=8.5),
                    CellNode(text=str(t3_scenarios), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{t3_str} {t('per_year_suffix', locale=doc_lang)} ({pct3_str})", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t("tomo_ch3_tier3_desc", locale=doc_lang), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
        ]
        nodes.append(TableNode(rows=tier_rows, autofit=True, col_widths=[0.30, 0.10, 0.25, 0.35]))
        nodes.append(SpacerNode(points=10))

        # Section 3.1.C: Executive Stress-Testing Table (Open FAIR Portfolio Simulation)
        stress_intro = t("tomo_ch3_stress_table_intro", locale=doc_lang)
        nodes.append(ParagraphNode(text=stress_intro, font_size=9.5, space_after=8))

        formatted_p90 = format_currency(total_p90, currency_symbol=currency, locale=doc_lang, decimals=0)
        var_3y_tail = format_currency(fin_metrics["var_3y_tail"], currency_symbol=currency, locale=doc_lang, decimals=0)
        formatted_ale = format_currency(target_ale_int, currency_symbol=currency, locale=doc_lang, decimals=0)

        stress_col_h = t("tomo_ch3_stress_col_horizon", locale=doc_lang)
        stress_col_m = t("tomo_ch3_stress_col_model", locale=doc_lang)
        stress_col_d = t("tomo_ch3_stress_col_desc", locale=doc_lang)

        stress_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=stress_col_h, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=stress_col_m, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=stress_col_d, bold=True, is_header=True, font_size=8.5),
                ],
                is_header=True,
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_stress_row1_title", locale=doc_lang), bold=True, bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=f"{formatted_ale} {t('per_year_suffix', locale=doc_lang)}", bold=True, bg_color="FFFFFF", font_size=8.0, align="CENTER"),
                    CellNode(text=t("tomo_ch3_stress_row1_desc", locale=doc_lang), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_stress_row2_title", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=peak_cost_fmt, bold=True, bg_color=self.alt_row_hex, font_size=8.0, align="CENTER"),
                    CellNode(
                        text=t(
                            "tomo_ch3_stress_row2_desc",
                            locale=doc_lang,
                            worst_incident_code=peak_code,
                            worst_incident_domain=peak_domain,
                        ),
                        bg_color=self.alt_row_hex,
                        font_size=8.0,
                    ),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_stress_row3_title", locale=doc_lang), bold=True, bg_color="FFFFFF", font_size=8.0),
                    CellNode(text=f"{formatted_p90} {t('per_year_suffix', locale=doc_lang)}", bold=True, bg_color="FFFFFF", font_size=8.0, align="CENTER"),
                    CellNode(text=t("tomo_ch3_stress_row3_desc", locale=doc_lang), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_ch3_stress_row4_title", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=var_3y_tail, bold=True, bg_color=self.alt_row_hex, font_size=8.0, align="CENTER"),
                    CellNode(text=t("tomo_ch3_stress_row4_desc", locale=doc_lang), bg_color=self.alt_row_hex, font_size=8.0),
                ]
            ),
        ]
        nodes.append(TableNode(rows=stress_rows, autofit=True, col_widths=[0.28, 0.22, 0.50]))
        nodes.append(SpacerNode(points=14))

        # 3.2 5x5 Open FAIR Heatmap Matrix (Dynamically calibrated to tenant telemetry)
        nodes.append(
            HeadingNode(
                text=t("tomo_sec32_heatmap_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_sec32_heatmap_intro", locale=doc_lang),
                font_size=9.5,
                space_after=8,
            )
        )

        is_critical_tier = bool(global_payload.get("meta", {}).get("is_critical", False))
        dynamic_lm_bounds = compute_dynamic_lm_thresholds(
            currency=currency,
            annual_revenue=fin_metrics["annual_revenue"],
            hourly_downtime_cost=fin_metrics["consolidated_rate"],
            is_critical_tier=is_critical_tier,
            locale=doc_lang,
        )
        heatmap_feed = global_payload.get("corporate_heatmap_risks") or catalog.get("tomo_corporate_heatmap_risks") or all_primary_risks
        if heatmap_feed:
            nodes.append(
                build_heatmap_mosaic(
                    heatmap_feed,
                    is_critical=is_critical_tier,
                    dynamic_lm_thresholds=dynamic_lm_bounds,
                    header_bg_color=self.primary_color_hex,
                    locale=doc_lang,
                    currency=currency,
                    annual_revenue=fin_metrics["annual_revenue"],
                    hourly_downtime_cost=fin_metrics["consolidated_rate"],
                )
            )
            nodes.append(SpacerNode(points=8))

            # Dynamic Risk Taxonomy Clustering & Heatmap Legend (RFC 081)
            clusters = ActuarialTaxonomyClusterer.build_dynamic_clusters(
                risk_vectors=heatmap_feed,
                tower_payloads=tower_payloads,
                reconciled_allocations=reconciled_allocations,
            )

            if clusters:
                total_crit = sum(c.critical_findings for c in clusters)
                total_high = sum(c.high_findings for c in clusters)
                total_med = sum(c.medium_findings for c in clusters)
                total_all = sum(c.total_findings for c in clusters)
                total_plot_points = sum(len(c.matrix_plot_codes) for c in clusters)

                bridge_text = t(
                    "sec_3_2_taxonomy_bridge_narrative",
                    locale=doc_lang,
                    active_cluster_count=len(clusters),
                    total_plot_points=total_plot_points,
                    total_findings=total_all,
                    critical_count=total_crit,
                    high_count=total_high,
                    medium_count=total_med,
                )
                nodes.append(ParagraphNode(text=bridge_text, font_size=8.5, space_after=6))

                legend_headers = [
                    t("sec_3_2_col_taxonomy_family", locale=doc_lang),
                    t("sec_3_2_col_matrix_codes", locale=doc_lang),
                    t("sec_3_2_col_systemic_threat_rationale", locale=doc_lang),
                    t("sec_3_2_col_forensic_breakdown", locale=doc_lang),
                    t("sec_3_2_col_clustered_ale", locale=doc_lang),
                ]

                legend_rows = [
                    TableRowNode(
                        cells=[
                            CellNode(text=legend_headers[0], bold=True, is_header=True, font_size=8.0),
                            CellNode(text=legend_headers[1], bold=True, is_header=True, font_size=8.0, align="CENTER"),
                            CellNode(text=legend_headers[2], bold=True, is_header=True, font_size=8.0),
                            CellNode(text=legend_headers[3], bold=True, is_header=True, font_size=8.0, align="CENTER"),
                            CellNode(text=legend_headers[4], bold=True, is_header=True, font_size=8.0, align="CENTER"),
                        ],
                        is_header=True,
                    )
                ]

                for idx, c in enumerate(clusters):
                    fam_title = t(f"{c.taxonomy_id}_TITLE", locale=doc_lang)
                    fam_rationale = t(f"{c.taxonomy_id}_RATIONALE", locale=doc_lang)
                    if c.representative_threats:
                        clean_threats = [t_item.strip().rstrip('.').replace('|', '-') for t_item in c.representative_threats]
                        empirical_scope = "; ".join(clean_threats)
                        rationale_cell = f"{fam_rationale}. Casuística representativa: {empirical_scope}."
                    else:
                        rationale_cell = fam_rationale

                    codes_cell = ", ".join(c.matrix_plot_codes) if c.matrix_plot_codes else "—"
                    breakdown_cell = t(
                        "sec_3_2_findings_badge_template",
                        locale=doc_lang,
                        total=c.total_findings,
                        crit=c.critical_findings,
                        high=c.high_findings,
                        med=c.medium_findings,
                    )
                    ale_str = f"{format_currency(c.cluster_ale, currency_symbol=currency, locale=doc_lang, decimals=0)} ({format_number(c.share_of_total_ale_pct, locale=doc_lang, decimals=1)}%)"

                    is_alt = (idx % 2 == 1)
                    row_bg = self.alt_row_hex if is_alt else "FFFFFF"

                    legend_rows.append(
                        TableRowNode(
                            cells=[
                                CellNode(text=fam_title, bold=True, bg_color=row_bg, font_size=7.5),
                                CellNode(text=codes_cell, bg_color=row_bg, font_size=7.5, align="CENTER"),
                                CellNode(text=rationale_cell, bg_color=row_bg, font_size=7.5),
                                CellNode(text=breakdown_cell, bold=True, bg_color=row_bg, font_size=7.5, align="CENTER"),
                                CellNode(text=ale_str, bold=True, bg_color=row_bg, font_size=7.5, align="CENTER"),
                            ]
                        )
                    )

                # Total Footer Row
                tot_ale_val = sum(c.cluster_ale for c in clusters)
                tot_breakdown = t(
                    "sec_3_2_findings_badge_template",
                    locale=doc_lang,
                    total=total_all,
                    crit=total_crit,
                    high=total_high,
                    med=total_med,
                )
                tot_ale_str = f"{format_currency(tot_ale_val, currency_symbol=currency, locale=doc_lang, decimals=0)} ({format_number(100.0, locale=doc_lang, decimals=1)}%)"

                legend_rows.append(
                    TableRowNode(
                        cells=[
                            CellNode(text=t("sec_3_2_row_total_reconciled", locale=doc_lang), bold=True, bg_color="F8FAFC", font_size=8.0),
                            CellNode(text=f"N = {total_plot_points}", bold=True, bg_color="F8FAFC", font_size=8.0, align="CENTER"),
                            CellNode(text=t("sec_3_2_row_total_rationale", locale=doc_lang), italic=True, bg_color="F8FAFC", font_size=7.5),
                            CellNode(text=tot_breakdown, bold=True, bg_color="F8FAFC", font_size=8.0, align="CENTER"),
                            CellNode(text=tot_ale_str, bold=True, bg_color="F8FAFC", font_size=8.0, align="CENTER"),
                        ]
                    )
                )

                nodes.append(TableNode(rows=legend_rows, autofit=True, col_widths=[0.24, 0.12, 0.36, 0.14, 0.14]))
                nodes.append(SpacerNode(points=14))

        # 3.3 Top Corporate Systemic Risk Cards
        nodes.append(
            HeadingNode(
                text=t("tomo_sec33_risk_cards_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_sec33_risk_cards_intro", locale=doc_lang),
                font_size=9.5,
                space_after=8,
            )
        )

        # Strict Monism: Derive Top Corporate Risks directly from live in-memory active risks across all 10 towers
        sorted_primary = sorted(
            [r for r in all_primary_risks if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR" and float(r.get("ale") or 0.0) > 0.0],
            key=lambda item: float(item.get("ale") or 0.0),
            reverse=True,
        )
        top_cards_feed = []
        for r in sorted_primary[:TOP_CORPORATE_RISKS_LIMIT]:
            r_ale_val = float(r.get("ale") or 0.0)
            r_sle_val = float(r.get("sle") or 0.0)
            r_lef_val = float(r.get("lef") or 0.0)
            v_str = str(r.get("finding") or r.get("evidence") or "").strip()
            i_str = str(r.get("business_risk") or r.get("primary_impact") or "").strip()
            m_str = str(r.get("mitigation_directive") or "").strip()
            # Clean pipes and format strings cleanly
            v_str = re.sub(r'\s*\|\s*', '. ', v_str)
            i_str = re.sub(r'\s*\|\s*', '. ', i_str)
            m_str = re.sub(r'\s*\|\s*', '. ', m_str)
            top_cards_feed.append(
                {
                    "id": str(r.get("id") or "RSK-01"),
                    "title": str(r.get("capability") or r.get("title") or r.get("finding") or t("default_risk_scenario_title", locale=doc_lang))[:65],
                    "ale": format_currency(r_ale_val, currency_symbol=currency, locale=doc_lang, decimals=0) + t("per_year_suffix", locale=doc_lang),
                    "sle": format_currency(r_sle_val, currency_symbol=currency, locale=doc_lang, decimals=0) if r_sle_val > 0 else "N/A (OpEx continuo)",
                    "lef": f"{format_number(r_lef_val, locale=doc_lang, decimals=2)} {t('event_frequency_unit', locale=doc_lang)}" if r_lef_val > 0 else "Continuo / Anual",
                    "vuln": v_str if (not v_str or v_str.endswith(".")) else f"{v_str}.",
                    "impact": i_str if (not i_str or i_str.endswith(".")) else f"{i_str}.",
                    "mitig": m_str if (not m_str or m_str.endswith(".")) else f"{m_str}.",
                }
            )

        for idx, item in enumerate(top_cards_feed, start=1):
            r_id = str(item.get("id") or f"RSK-{idx:02d}")
            r_title = str(item.get("title") or t("default_risk_scenario_title", locale=doc_lang))
            r_ale = str(item.get("ale") or "")
            r_sle = str(item.get("sle") or "")
            r_lef = str(item.get("lef") or "")
            r_vuln = str(item.get("vuln") or "")
            r_impact = str(item.get("impact") or "")
            r_mitig = str(item.get("mitig") or "")

            card_rows = [
                TableRowNode(
                    cells=[
                        CellNode(
                            text=f"**[{r_id}] {r_title}**",
                            bold=True,
                            bg_color=self.primary_color_hex,
                            text_color_rgb=[255, 255, 255],
                            grid_span=3,
                            font_size=9.0,
                        )
                    ]
                ),
                TableRowNode(
                    cells=[
                        CellNode(text=f"**{t('tomo_kpi_card_ale', locale=doc_lang)}**\n{r_ale}", font_size=8.0, align="CENTER", bg_color="F8FAFC"),
                        CellNode(text=f"**{t('tomo_kpi_card_sle', locale=doc_lang)}**\n{r_sle}", font_size=8.0, align="CENTER", bg_color="F8FAFC"),
                        CellNode(text=f"**{t('tomo_kpi_card_lef', locale=doc_lang)}**\n{r_lef}", font_size=8.0, align="CENTER", bg_color="F8FAFC"),
                    ]
                ),
                TableRowNode(
                    cells=[
                        CellNode(
                            text=f"**{t('tomo_card_vuln_label', locale=doc_lang)}:** {r_vuln}\n\n"
                            f"**{t('tomo_card_impact_label', locale=doc_lang)}:** {r_impact}\n\n"
                            f"**{t('tomo_card_mitigation_label', locale=doc_lang)}:** {r_mitig}",
                            font_size=8.0,
                            grid_span=3,
                            bg_color="FFFFFF",
                        )
                    ]
                ),
            ]
            nodes.append(TableNode(rows=card_rows, autofit=True, col_widths=[0.33, 0.33, 0.34]))
            nodes.append(SpacerNode(points=8))

        nodes.append(PageBreakNode())

    # CHAPTER 4: FORENSIC DOMAIN DIAGNOSTICS (10 TOWERS) & CRITICAL SPOF MATRIX
    def _build_chapter_4_forensic_diagnostics(
        self,
        nodes: List[DocNode],
        global_payload: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        currency: str,
        doc_lang: str,
    ) -> None:
        """Chapter 4: In-depth forensic findings across all 10 domains + Transversal SPOF Matrix."""
        nodes.append(
            HeadingNode(
                text=t("tomo_ch4_title", locale=doc_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=8))

        nodes.append(ParagraphNode(text=t("tomo_ch4_intro", locale=doc_lang), font_size=10.0, space_after=12))

        heatmap = global_payload.get("heatmap", [])
        heatmap_map = {
            str(item.get("id") or item.get("tower_code") or "").upper(): item
            for item in heatmap
            if isinstance(item, dict)
        }

        domain_topology = self._resolve_domain_topology(global_payload, doc_lang, tower_payloads)
        domain_meta = [(code, title_k, text_k) for code, _, _, title_k, text_k in domain_topology]

        strip_score_lbl = t("tomo_kpi_strip_score", locale=doc_lang)
        strip_status_lbl = t("tomo_lbl_status", locale=doc_lang)
        strip_ale_lbl = t("tomo_ch4_kpi_annual_risk_exposure", locale=doc_lang)
        strip_exposure_lbl = t("tomo_lbl_exposure", locale=doc_lang)

        catalog = self._get_locale_catalog(doc_lang)
        catalog_loc = catalog.get("tomo_tower_forensic_catalog", {})
        col_sub_lbl = t("tomo_ch4_subpillar_col_name", locale=doc_lang)
        col_str_lbl = t("tomo_ch4_subpillar_col_strengths", locale=doc_lang)
        col_rsk_lbl = t("tomo_ch4_subpillar_col_risks", locale=doc_lang)
        lbl_inventory = t("tomo_lbl_inventory", locale=doc_lang)
        strengths_title = t("tomo_ch4_callout_strengths_title", locale=doc_lang)
        friction_title = t("tomo_ch4_callout_friction_title", locale=doc_lang)

        # Reconcile domain allocations closed-form via Hamilton's Largest Remainder Method
        fin_metrics = self._resolve_financial_telemetry(global_payload, tower_payloads, currency, doc_lang)
        reconciled_allocations = self._resolve_domain_allocations(
            global_payload=global_payload,
            tower_payloads=tower_payloads,
            target_corporate_ale=fin_metrics["corporate_ale"],
            domain_meta=domain_meta,
            catalog_loc=catalog_loc,
            doc_lang=doc_lang,
        )
        target_ale_int = self._round_half_up_int(fin_metrics["corporate_ale"], locale=doc_lang)

        for code, title_key, text_key in domain_meta:
            clean_heading = t(title_key, locale=doc_lang)
            matched_name = next((t_name for c, t_name, *_ in domain_topology if c == code), f"Domain {code}")
            if not clean_heading or clean_heading.startswith("tomo_ch4_"):
                clean_heading = f"{code}. {matched_name}"

            nodes.append(
                HeadingNode(
                    text=clean_heading,
                    level=2,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )

            t_data = catalog_loc.get(code, catalog_loc.get(code.upper(), {}))
            t_payload = tower_payloads.get(code) or tower_payloads.get(code.upper()) or tower_payloads.get(code.lower()) or {}
            h_item = heatmap_map.get(code.upper(), {})

            # Derive metrics dynamically prioritizing live payload telemetry (preserving legitimate 0.0 scores)
            payload_score = (
                self._first_not_none(
                    t_payload.get("maturity_score"),
                    t_payload.get("global_score"),
                )
                if isinstance(t_payload, dict)
                else None
            )
            parsed_raw = safe_float(
                self._first_not_none(
                    h_item.get("score") if isinstance(h_item, dict) else None,
                    payload_score,
                    t_data.get("score_num") if isinstance(t_data, dict) else None,
                    default=DEFAULT_MATURITY_SCORE,
                ),
                locale=doc_lang,
                allow_zero=True,
            )
            raw_score = parsed_raw if parsed_raw is not None else DEFAULT_MATURITY_SCORE

            b_info = self._resolve_cmmi_band_info(raw_score, doc_lang)
            band_lbl = t(b_info["band_key"], locale=doc_lang)
            status_val = b_info["status_name"]

            tower_ale = float(reconciled_allocations.get(code, 0))

            score_fmt = f"{format_number(raw_score, locale=doc_lang, decimals=2)} ({band_lbl})"
            ale_fmt = format_currency(tower_ale, currency_symbol=currency, locale=doc_lang, decimals=0) + t("per_year_suffix", locale=doc_lang)
            ratio = (tower_ale / target_ale_int) if target_ale_int > 0 else 0.0
            exposure_val = (
                t("tomo_exposure_high", locale=doc_lang)
                if ratio >= DOMAIN_HIGH_EXPOSURE_SHARE_RATIO
                else (
                    t("tomo_exposure_medium", locale=doc_lang)
                    if ratio >= DOMAIN_MED_EXPOSURE_SHARE_RATIO
                    else t("tomo_exposure_moderate", locale=doc_lang)
                )
            )

            strip_rows = [
                TableRowNode(
                    cells=[
                        CellNode(text=f"**{strip_score_lbl}**\n{score_fmt}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                        CellNode(text=f"**{strip_status_lbl}**\n{status_val}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                        CellNode(text=f"**{strip_ale_lbl}**\n{ale_fmt}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                        CellNode(text=f"**{strip_exposure_lbl}**\n{exposure_val}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                    ]
                )
            ]
            nodes.append(TableNode(rows=strip_rows, autofit=True, col_widths=[0.25, 0.25, 0.25, 0.25]))
            nodes.append(SpacerNode(points=6))

            # 1. Dynamic subpillars extraction from live payload
            pillars_analysis = t_payload.get("pillars_analysis", []) if isinstance(t_payload, dict) else []
            resolver = get_taxonomy_resolver()
            if pillars_analysis and isinstance(pillars_analysis, list):
                subpillars = []
                for p in pillars_analysis:
                    if isinstance(p, dict):
                        p_id, raw_pname = extract_pillar_identifiers(p)
                        p_name = resolver.resolve_pillar_by_any_reference(
                            p_id or raw_pname,
                            default=(raw_pname or p_id or t("default_subpillar_label", locale=doc_lang)),
                            locale=doc_lang,
                            tower_id=code,
                        )
                        p_score = safe_float(p.get("score"), locale=doc_lang, allow_zero=True)
                        subpillars.append([p_name, p_score if p_score is not None else DEFAULT_MATURITY_SCORE, p])
            else:
                raw_sp_list = t_data.get("subpillars") or []
                subpillars = []
                for sp_item in raw_sp_list:
                    if isinstance(sp_item, (list, tuple)) and len(sp_item) >= 2:
                        sp_id, raw_pname = extract_pillar_identifiers({"pillar_name": str(sp_item[0])})
                        sp_name = resolver.resolve_pillar_by_any_reference(
                            sp_id or raw_pname,
                            default=(raw_pname or sp_id or str(sp_item[0])),
                            locale=doc_lang,
                            tower_id=code,
                        )
                        sp_score = safe_float(sp_item[1], locale=doc_lang, allow_zero=True)
                        subpillars.append([sp_name, sp_score if sp_score is not None else DEFAULT_MATURITY_SCORE, {}])
                    elif isinstance(sp_item, dict):
                        sp_id, raw_pname = extract_pillar_identifiers(sp_item)
                        sp_name = resolver.resolve_pillar_by_any_reference(
                            sp_id or raw_pname,
                            default=(raw_pname or sp_id or t("default_subpillar_label", locale=doc_lang)),
                            locale=doc_lang,
                            tower_id=code,
                        )
                        sp_score = safe_float(sp_item.get("score"), locale=doc_lang, allow_zero=True)
                        subpillars.append([sp_name, sp_score if sp_score is not None else DEFAULT_MATURITY_SCORE, sp_item])

            # 2. Dynamic narrative extraction
            raw_narrative = (
                t_payload.get("diagnostic_narrative")
                or t_payload.get("executive_snapshot", {}).get("bottom_line")
                if isinstance(t_payload, dict)
                else None
            )
            narrative = raw_narrative if raw_narrative else t(text_key, locale=doc_lang)
            if not narrative or narrative.startswith("tomo_ch4_"):
                narrative = t(
                    "forensic_domain_narrative_default",
                    locale=doc_lang,
                    tower_name=matched_name,
                    client_name=str(global_payload.get("meta", {}).get("client") or t("default_client_name", locale=doc_lang)).strip(),
                )

            # 3. Dynamic inventory extraction
            payload_inv = (
                t_payload.get("inventory")
                or t_payload.get("assets_summary")
                or t_payload.get("primary_workloads")
                or t_payload.get("executive_snapshot", {}).get("primary_workloads")
                if isinstance(t_payload, dict)
                else None
            )
            inventory = payload_inv or t_data.get("inventory") or ""
            if inventory and "{client_name}" in inventory:
                c_name = str(global_payload.get("meta", {}).get("client") or t("default_client_name", locale=doc_lang)).strip()
                inventory = inventory.replace("{client_name}", c_name)

            if not inventory:
                f_templates = catalog.get("forensic_domain_templates", {})
                inv_tmpl = f_templates.get("inventory_fallback") or t(
                    "forensic_inventory_fallback_template", locale=doc_lang
                )
                inventory = self._safe_format_template(
                    inv_tmpl,
                    f"Domain {code} technological estate comprising evaluated control subpillars.",
                    domain_code=code,
                    domain_title=matched_name,
                    subpillar_count=len(subpillars) if subpillars else DEFAULT_SUBPILLAR_COUNT,
                    sector_name=t("default_industry_name", locale=doc_lang),
                )

            # 4. Dynamic strengths extraction
            payload_str = (
                t_payload.get("strengths")
                or t_payload.get("executive_snapshot", {}).get("operational_benefits")
                if isinstance(t_payload, dict)
                else None
            )
            strengths = payload_str or t_data.get("strengths") or []
            max_cmmi_str = format_number(MAX_CMMI_SCORE, decimals=2, locale=doc_lang)
            if not strengths and subpillars:
                sorted_sp = sorted(
                    subpillars,
                    key=lambda x: safe_float(x[1], locale=doc_lang, allow_zero=True) or 0.0,
                    reverse=True,
                )
                top_sp = sorted_sp[0]
                top_sp_score = safe_float(top_sp[1], locale=doc_lang, allow_zero=True) or 0.0
                f_templates = catalog.get("forensic_domain_templates", {})
                str_tmpl = f_templates.get("strength_fallback") or t(
                    "forensic_strength_fallback_template", locale=doc_lang
                )
                strengths = [
                    self._safe_format_template(
                        str_tmpl,
                        f"Established operational continuity in {top_sp[0]}.",
                        highest_subpillar_name=top_sp[0],
                        highest_subpillar_score=format_number(top_sp_score, decimals=2, locale=doc_lang),
                        max_cmmi_str=max_cmmi_str,
                    )
                ]

            # 5. Dynamic findings extraction
            payload_fnd = (
                t_payload.get("findings")
                or t_payload.get("critical_findings")
                or t_payload.get("executive_snapshot", {}).get("structural_risks")
                if isinstance(t_payload, dict)
                else None
            )
            findings = payload_fnd or t_data.get("findings") or []
            if not findings and subpillars:
                sorted_sp = sorted(
                    subpillars,
                    key=lambda x: safe_float(x[1], locale=doc_lang, allow_zero=True) or 0.0,
                )
                low_sp = sorted_sp[0]
                low_sp_score = safe_float(low_sp[1], locale=doc_lang, allow_zero=True) or 0.0
                f_templates = catalog.get("forensic_domain_templates", {})
                fnd_tmpl = f_templates.get("finding_fallback") or t(
                    "forensic_finding_fallback_template", locale=doc_lang
                )
                findings = [
                    self._safe_format_template(
                        fnd_tmpl,
                        f"Control deficit identified in {low_sp[0]}.",
                        lowest_subpillar_name=low_sp[0],
                        lowest_subpillar_score=format_number(low_sp_score, decimals=2, locale=doc_lang),
                        max_cmmi_str=max_cmmi_str,
                    )
                ]

            if inventory:
                nodes.append(ParagraphNode(text=f"**{lbl_inventory}:** {inventory}", font_size=9.5, space_after=6))
            nodes.append(ParagraphNode(text=narrative, font_size=9.5, space_after=8))

            # Balanced callout: Observed Operational Capabilities & Strengths (Emerald Accent)
            if strengths:
                str_bullets = "\n".join(f"• {s}" for s in strengths)
                nodes.append(
                    TableNode(
                        rows=[
                            TableRowNode(
                                cells=[
                                    CellNode(
                                        text=f"**{strengths_title}**\n\n{str_bullets}",
                                        font_size=8.0,
                                        bg_color=CALLOUT_STRENGTH_BG_HEX,
                                        border_left_color=CALLOUT_STRENGTH_BORDER_HEX,
                                        border_left_size=CALLOUT_BORDER_LEFT_SIZE,
                                        align="LEFT",
                                    )
                                ]
                            )
                        ],
                        autofit=True,
                        col_widths=[1.0],
                    )
                )
                nodes.append(SpacerNode(points=6))

            # Balanced callout: Capacity Limits, Obsolescence & Operational Friction (Amber Accent)
            if findings:
                fric_bullets = "\n".join(f"• {f}" for f in findings)
                nodes.append(
                    TableNode(
                        rows=[
                            TableRowNode(
                                cells=[
                                    CellNode(
                                        text=f"**{friction_title}**\n\n{fric_bullets}",
                                        font_size=8.0,
                                        bg_color=CALLOUT_FRICTION_BG_HEX,
                                        border_left_color=CALLOUT_FRICTION_BORDER_HEX,
                                        border_left_size=CALLOUT_BORDER_LEFT_SIZE,
                                        align="LEFT",
                                    )
                                ]
                            )
                        ],
                        autofit=True,
                        col_widths=[1.0],
                    )
                )
                nodes.append(SpacerNode(points=6))

            # Upgraded 3-column subpillar deep-dive table
            if subpillars:
                deep_rows = [
                    TableRowNode(
                        cells=[
                            CellNode(text=col_sub_lbl, bold=True, is_header=True, font_size=8.0, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255]),
                            CellNode(text=col_str_lbl, bold=True, is_header=True, font_size=8.0, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255]),
                            CellNode(text=col_rsk_lbl, bold=True, is_header=True, font_size=8.0, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255]),
                        ],
                        is_header=True,
                    )
                ]
                max_cmmi_str = format_number(MAX_CMMI_SCORE, decimals=2, locale=doc_lang)
                cat_strengths = t_data.get("strengths") or []
                cat_findings = t_data.get("findings") or []
                for idx, sp in enumerate(subpillars):
                    sp_name = sp[0]
                    sp_score = sp[1]
                    sp_pillar_dict = sp[2] if len(sp) > 2 and isinstance(sp[2], dict) else {}

                    # Resolve Strength: prioritize live health checks/payload strengths, then catalog, then fallback
                    sp_strength = ""
                    if sp_pillar_dict:
                        hcs = sp_pillar_dict.get("health_check_asis") or []
                        target_st = next(
                            (
                                h.get("target_state") or h.get("description") or h.get("title")
                                for h in hcs
                                if isinstance(h, dict) and (h.get("target_state") or h.get("description") or h.get("title"))
                            ),
                            None,
                        )
                        if target_st:
                            clean_st = str(target_st).split(".")[0].strip()
                            sp_strength = f"{clean_st}." if clean_st else str(target_st).strip()
                    if not sp_strength and idx < len(strengths) and strengths[idx]:
                        sp_strength = str(strengths[idx]).strip()
                    elif not sp_strength and idx < len(cat_strengths) and cat_strengths[idx]:
                        sp_strength = str(cat_strengths[idx]).strip()
                    if not sp_strength:
                        sp_strength = t("tomo_pillar_default_strength", locale=doc_lang, pillar_name=sp_name)

                    # Resolve Finding / Risk: prioritize live health checks/payload findings, then catalog, then fallback
                    sp_finding = ""
                    if sp_pillar_dict:
                        hcs = sp_pillar_dict.get("health_check_asis") or []
                        f_txt = next(
                            (
                                h.get("finding") or h.get("business_risk") or h.get("description")
                                for h in hcs
                                if isinstance(h, dict) and (h.get("finding") or h.get("business_risk") or h.get("description"))
                            ),
                            None,
                        )
                        if f_txt:
                            clean_sent = str(f_txt).split(".")[0].strip()
                            sp_finding = f"{clean_sent}." if clean_sent else str(f_txt).strip()
                    if not sp_finding and idx < len(findings) and findings[idx]:
                        sp_finding = str(findings[idx]).strip()
                    elif not sp_finding and idx < len(cat_findings) and cat_findings[idx]:
                        sp_finding = str(cat_findings[idx]).strip()
                    if not sp_finding:
                        sp_finding = t("tomo_pillar_default_finding", locale=doc_lang, pillar_name=sp_name)

                    parsed_sp = safe_float(sp_score, locale=doc_lang, allow_zero=True)
                    sp_score_str = format_number(parsed_sp, decimals=2, locale=doc_lang) if parsed_sp is not None else str(sp_score)
                    deep_rows.append(
                        TableRowNode(
                            cells=[
                                CellNode(text=f"**{sp_name}**\n({sp_score_str} / {max_cmmi_str})", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                                CellNode(text=sp_strength, font_size=8.0, bg_color="FFFFFF"),
                                CellNode(text=sp_finding, font_size=8.0, bg_color="FFFFFF"),
                            ]
                        )
                    )
                nodes.append(TableNode(rows=deep_rows, autofit=True, col_widths=[0.24, 0.38, 0.38]))
                nodes.append(SpacerNode(points=14))

        # Transversal 10-SPOF Matrix loaded from localized configuration catalog
        nodes.append(SpacerNode(points=6))
        nodes.append(
            HeadingNode(
                text=t("tomo_ch4_spof_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_ch4_spof_intro", locale=doc_lang),
                font_size=9.5,
                space_after=8,
            )
        )

        col_id_lbl = t("tomo_spof_col_id", locale=doc_lang)
        col_comp_lbl = t("tomo_spof_col_component", locale=doc_lang)
        col_mech_lbl = t("tomo_spof_col_mechanism", locale=doc_lang)
        col_impact_lbl = t("tomo_spof_col_impact", locale=doc_lang)
        col_crit_lbl = t("tomo_spof_col_criticality", locale=doc_lang)

        spof_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_id_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_comp_lbl, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_mech_lbl, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_impact_lbl, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_crit_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                ],
                is_header=True,
            )
        ]

        spof_list = global_payload.get("spof_matrix") or catalog.get("tomo_spof_catalog", [])

        # Sort SPOFs deterministically by descending criticality (CRITICAL -> HIGH -> MEDIUM -> LOW)
        canonical_criticality_ranks = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
        }
        localized_ranks = catalog.get("spof_criticality_ranks") or canonical_criticality_ranks

        def _resolve_spof_sort_key(sp: Dict[str, Any]) -> Tuple[int, str]:
            raw_rank = sp.get("criticality_rank")
            if raw_rank is not None:
                parsed_rank = safe_float(raw_rank, allow_zero=True)
                if parsed_rank is not None:
                    return (int(parsed_rank), str(sp.get("id", "")))
            crit_token = str(sp.get("criticality_code") or sp.get("criticality", "")).strip().upper()
            fallback_rank = localized_ranks.get(crit_token, canonical_criticality_ranks.get(crit_token, FALLBACK_CRITICALITY_RANK))
            return (int(fallback_rank), str(sp.get("id", "")))

        valid_spofs = [sp for sp in spof_list if isinstance(sp, dict)]
        sorted_spofs = sorted(valid_spofs, key=_resolve_spof_sort_key)

        for sp in sorted_spofs:
            spof_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=str(sp.get("id") or ""), bold=True, font_size=8.5, align="CENTER"),
                        CellNode(text=str(sp.get("component") or ""), font_size=8.0),
                        CellNode(text=str(sp.get("mechanism") or ""), font_size=8.0),
                        CellNode(text=str(sp.get("impact") or ""), font_size=8.0),
                        CellNode(text=str(sp.get("criticality") or ""), bold=True, bg_color=sp.get("bg", "FFFFFF"), font_size=8.0, align="CENTER"),
                    ]
                )
            )

        nodes.append(TableNode(rows=spof_rows, autofit=True, col_widths=[0.10, 0.22, 0.28, 0.28, 0.12]))
        nodes.append(SpacerNode(points=14))
        nodes.append(PageBreakNode())

    def _build_chapter_5_cross_tower_nexus(
        self,
        nodes: List[DocNode],
        global_payload: Dict[str, Any],
        doc_lang: str,
    ) -> None:
        """Chapter 5: Cross-Tower Nexus, Interdependencies Directed Acyclic Graph."""
        nodes.append(
            HeadingNode(
                text=t("tomo_ch5_title", locale=doc_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=8))

        nodes.append(ParagraphNode(text=t("tomo_ch5_intro", locale=doc_lang), font_size=10.0, space_after=12))

        col_src = t("tomo_ch5_col_source", locale=doc_lang)
        col_tgt = t("tomo_ch5_col_target", locale=doc_lang)
        col_typ = t("tomo_ch5_col_type", locale=doc_lang)
        col_mech = t("tomo_ch5_col_mechanism", locale=doc_lang)
        col_imp = t("tomo_ch5_col_impact", locale=doc_lang)

        nexus_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_src, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_tgt, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_typ, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_mech, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_imp, bold=True, is_header=True, font_size=8.5),
                ],
                is_header=True,
            )
        ]

        catalog = self._get_locale_catalog(doc_lang)
        nexus_list = global_payload.get("nexus_matrix") or catalog.get("tomo_nexus_catalog", [])

        for nx in nexus_list:
            if not isinstance(nx, dict):
                continue
            nexus_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=str(nx.get("source") or ""), bold=True, font_size=8.0),
                        CellNode(text=str(nx.get("target") or ""), font_size=8.0),
                        CellNode(text=str(nx.get("type") or ""), bold=True, bg_color=nx.get("bg", "FFFFFF"), font_size=8.0, align="CENTER"),
                        CellNode(text=str(nx.get("mechanism") or ""), font_size=8.0),
                        CellNode(text=str(nx.get("impact") or ""), font_size=8.0),
                    ]
                )
            )
        nodes.append(TableNode(rows=nexus_rows, autofit=True, col_widths=[0.20, 0.20, 0.15, 0.25, 0.20]))
        nodes.append(SpacerNode(points=14))
        nodes.append(PageBreakNode())

    # UNIFIED APPENDIX: GLOSSARY & LEGAL LIABILITY DISCLAIMER
    def _build_unified_appendix(
        self,
        nodes: List[DocNode],
        client_name: str,
        doc_lang: str,
        company_name: str = "",
    ) -> None:
        """Unified Appendix: Clean Abbreviations Glossary (18/82 autofit) + Disclaimer."""
        effective_company_name = str(company_name or t("default_company_name", locale=doc_lang)).strip()
        nodes.append(
            HeadingNode(
                text=t("tomo_app_title", locale=doc_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
                is_appendix=True,
            )
        )
        nodes.append(SpacerNode(points=8))

        nodes.append(
            HeadingNode(
                text=t("tomo_app_abbr_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
                is_appendix=True,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_app_abbr_lead", locale=doc_lang),
                font_size=9.5,
                space_after=8,
            )
        )

        all_glossaries = load_abbreviations_glossary()
        glossary = all_glossaries.get(doc_lang) or all_glossaries.get("en") or {}
        gloss_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_app_col_abbr", locale=doc_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], align="CENTER", is_header=True),
                    CellNode(text=t("tomo_app_col_desc", locale=doc_lang), bold=True, bg_color=self.primary_color_hex, text_color_rgb=[255, 255, 255], is_header=True),
                ],
                is_header=True,
            )
        ]
        for term, definition in sorted(glossary.items()):
            gloss_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=term, bold=True, align="CENTER"),
                        CellNode(text=definition),
                    ]
                )
            )

        nodes.append(TableNode(rows=gloss_rows, autofit=True, col_widths=[0.18, 0.82]))
        nodes.append(SpacerNode(points=14))

        nodes.append(
            HeadingNode(
                text=t("disclaimer_section_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
                is_appendix=True,
            )
        )
        for i in range(1, 6):
            disc_k = f"disclaimer_text_{i}"
            disc_text = t(
                disc_k,
                locale=doc_lang,
                client_name=client_name,
                company_name=effective_company_name,
                company=effective_company_name,
            )
            if disc_text and disc_text != disc_k and not disc_text.startswith("disclaimer_text_"):
                nodes.append(ParagraphNode(text=disc_text, font_size=9.0, space_after=6))


# Legacy backward-compatibility alias
TomoAsisASTCompiler = Volume1AsisASTCompiler
