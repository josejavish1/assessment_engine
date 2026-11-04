"""Declarative OpenXML AST Compiler for Volume 1: Transversal AS-IS Diagnostic.

Compiles a unified, board-ready 25-30 page strategic diagnostic report directly
from enriched SSOT payloads, completely eradicating template-injection split-brains.
100% Technical English codebase adhering to strict architectural invariants.
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Final, List, Mapping, Optional, Tuple

from assessment_engine.domain.actuarial_reconciler import ActuarialReconciler
from assessment_engine.domain.actuarial_scale_calibrator import (
    compute_dynamic_lm_thresholds,
    safe_float,
)

MAX_CMMI_SCORE: Final[float] = 5.0
FALLBACK_CORPORATE_ALE: Final[float] = 10000.0
DEFAULT_ANNUAL_REVENUE: Final[float] = 100_000_000.0
DEFAULT_OPERATING_HOURS_PER_YEAR: Final[float] = 8760.0
DEFAULT_FACILITY_REVENUE_SHARE: Final[float] = 0.35
DEFAULT_BASELINE_RISK_FACTOR: Final[float] = 0.001
DEFAULT_TAIL_RISK_MULTIPLIER: Final[float] = 2.50
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

from assessment_engine.adapters.compilers.ast_table_builders import (
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

    CANONICAL_DOMAIN_SCENARIO_BASELINE: Final[Mapping[str, int]] = MappingProxyType({
        "T1": 3,
        "T2": 4,
        "T3": 3,
        "T4": 2,
        "T5": 4,
        "T6": 3,
        "T7": 2,
        "T8": 3,
        "T9": 2,
        "T10": 3,
    })

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

        # 0. Frontmatter: Cover Page & TOC
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

        # 1. Chapter 1: Transversal Executive Summary & Board Memo
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

        # 5. Chapter 5: Cross-Tower Nexus & Systemic Interdependencies
        self._build_chapter_5_cross_tower_nexus(
            nodes, global_payload, doc_lang
        )

        # 6. Unified Appendix: Glossary & Legal Liability Disclaimer
        self._build_unified_appendix(
            nodes, client_name, doc_lang
        )

        ast = DocumentAST(
            title=f"{t('tomo_cover_title', locale=doc_lang)} - {client_name}",
            metadata={
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

    # =========================================================================
    # FRONTMATTER: COVER & TABLE OF CONTENTS
    # =========================================================================
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
        nodes.append(SpacerNode(points=142))

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

        # 4. Editorial whitespace chasm (~258 pt)
        nodes.append(SpacerNode(points=258))

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

    # =========================================================================
    # DYNAMIC FINANCIAL TELEMETRY & N-DOMAIN RECONCILIATION HELPERS
    # =========================================================================
    @staticmethod
    def _first_not_none(*values: Any, default: Any = None) -> Any:
        """Returns the first argument that is strictly not None."""
        for v in values:
            if v is not None:
                return v
        return default

    @staticmethod
    def _round_half_up_int(val: Any, default: int = 0) -> int:
        clean = safe_float(val, allow_zero=True)
        if clean is None:
            return default
        try:
            return int(Decimal(str(clean)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        except (InvalidOperation, ValueError, OverflowError):
            return default

    @staticmethod
    def _safe_decimal_weight(val: Any, default_str: str, locale: str | None = None) -> Decimal:
        """Safely converts an arbitrary weight value to a positive Decimal with fallback."""
        parsed = safe_float(val, locale=locale)
        if parsed is not None:
            try:
                return Decimal(str(parsed)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError, OverflowError):
                pass
        return Decimal(default_str)

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

        # 3. Corporate ALE & P90 tail risk (reconciled with live tower FAIR scenarios)
        corporate_ale = (
            safe_float(fin.get("total_fair_ale"), locale=doc_lang)
            or safe_float(fin.get("corporate_ale"), locale=doc_lang)
            or safe_float(global_payload.get("total_fair_ale"), locale=doc_lang)
        )
        derived_p90_sum = 0.0
        if corporate_ale is None:
            tower_ales: List[float] = []
            eval_towers = set(tower_payloads.keys())
            for tp in tower_payloads.values():
                if not isinstance(tp, dict):
                    continue
                explicit_t_ale = safe_float(tp.get("annualized_loss_expectancy"), locale=doc_lang)
                if explicit_t_ale is not None:
                    tower_ales.append(explicit_t_ale)
                else:
                    try:
                        r_list, _ = derive_in_memory_fair_risks(
                            tp, doc_lang=doc_lang, currency=currency, active_towers_scope=eval_towers
                        )
                        for r_item in r_list:
                            if r_item.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR":
                                r_ale = safe_float(r_item.get("ale"), locale=doc_lang)
                                r_p90 = safe_float(r_item.get("p90"), locale=doc_lang)
                                if r_ale is not None:
                                    tower_ales.append(r_ale)
                                if r_p90 is not None:
                                    derived_p90_sum += r_p90
                    except Exception as ex:
                        logger.debug("Fallback deriving FAIR risks in telemetry resolver: %s", ex)

            baseline_factor = (
                safe_float(fin.get("baseline_risk_factor"), locale=doc_lang)
                or DEFAULT_BASELINE_RISK_FACTOR
            )
            corporate_ale = sum(tower_ales) if tower_ales else (annual_revenue * baseline_factor)

        tail_multiplier = (
            safe_float(fin.get("tail_risk_multiplier"), locale=doc_lang)
            or DEFAULT_TAIL_RISK_MULTIPLIER
        )
        corporate_p90 = (
            safe_float(fin.get("total_fair_p90"), locale=doc_lang)
            or safe_float(fin.get("corporate_p90_tail_risk"), locale=doc_lang)
            or safe_float(global_payload.get("total_fair_p90"), locale=doc_lang)
            or (derived_p90_sum if derived_p90_sum > 0.0 else None)
            or (corporate_ale * tail_multiplier)
        )

        # 4. Cumulative 3-year exposure
        var_3y_expected = corporate_ale * STRATEGIC_HORIZON_YEARS
        var_3y_tail = (corporate_ale * STRATEGIC_HORIZON_YEARS) + (corporate_p90 * TAIL_STRESS_HORIZON_FACTOR)

        domain_scenario_counts = (
            fin.get("domain_scenario_counts")
            or fin.get("domain_scenarios")
            or self.CANONICAL_DOMAIN_SCENARIO_BASELINE
        )

        return {
            "annual_revenue": annual_revenue,
            "operating_hours": operating_hours,
            "consolidated_rate": consolidated_rate,
            "local_rate": local_rate,
            "corporate_ale": corporate_ale,
            "corporate_p90": corporate_p90,
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
        all_catalogs = load_locales_catalog()
        catalog = all_catalogs.get(doc_lang) or all_catalogs.get("en", {})
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

            # Score resolution prioritizing live telemetry
            score_val = (
                h_item.get("score")
                if (h_item and h_item.get("score") is not None)
                else (
                    t_item.get("maturity_score") or t_item.get("global_score")
                    if (isinstance(t_item, dict) and (t_item.get("maturity_score") is not None or t_item.get("global_score") is not None))
                    else c_item.get("score_num")
                )
            )
            score = float(score_val if score_val is not None else 2.50)

            # Name resolution
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
                lvl = int(b.get("level", idx))
                break

        tier_name = f"{t('level_prefix', locale=doc_lang)} {lvl} ({t(band_key, locale=doc_lang)})"

        if lvl >= 3:
            status_name = t("tomo_status_standardized", locale=doc_lang)
            bg_color = "D9EAD3"
        elif lvl == 2:
            status_name = t("tomo_status_moderate_debt", locale=doc_lang)
            bg_color = "FFF2CC"
        else:
            status_name = t("tomo_status_high_risk", locale=doc_lang)
            bg_color = "FCE5CD"

        return {
            "level": lvl,
            "band_key": band_key,
            "tier_name": tier_name,
            "status_name": status_name,
            "bg_color": bg_color,
        }

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
            # 1. Check explicit domain_weights in telemetry
            if code in domain_weights or code_u in domain_weights:
                val = safe_float(domain_weights.get(code, domain_weights.get(code_u)), locale=doc_lang) or 0.0
            # 2. Check tower_payloads
            elif (code in tower_payloads or code_u in tower_payloads) and (
                tower_payloads.get(code, tower_payloads.get(code_u, {})).get("annualized_loss_expectancy") is not None
            ):
                val = safe_float(
                    tower_payloads.get(code, tower_payloads.get(code_u))["annualized_loss_expectancy"],
                    locale=doc_lang,
                ) or 0.0
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
                    else FALLBACK_CORPORATE_ALE
                )
                val = safe_float(t_info.get("raw_ale"), locale=doc_lang) or parametric_weight

            try:
                dec_val = Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError, OverflowError):
                dec_val = Decimal("0.00")
            raw_pairs.append((code, dec_val))

        safe_target = safe_float(target_corporate_ale) or float(sum(p[1] for p in raw_pairs)) or FALLBACK_CORPORATE_ALE
        target_int = int(Decimal(str(safe_target)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=target_int,
            domain_raw_exposures=raw_pairs,
        )

    # =========================================================================
    # CHAPTER 1: TRANSVERSAL EXECUTIVE SUMMARY & BOARD MEMO
    # =========================================================================
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

        catalog = load_locales_catalog().get(doc_lang, load_locales_catalog().get("en", {}))
        catalog_loc = catalog.get("tomo_tower_forensic_catalog", {})

        heatmap = global_payload.get("heatmap", [])
        scores = [
            val
            for item in heatmap
            if isinstance(item, dict)
            for val in [safe_float(item.get("score"), locale=doc_lang)]
            if val is not None
        ]
        if not scores and catalog_loc:
            scores = [
                val
                for v in catalog_loc.values()
                if isinstance(v, dict)
                for val in [safe_float(v.get("score_num"), locale=doc_lang)]
                if val is not None
            ]
        scores_dec = [Decimal(f"{float(s):.2f}") for s in scores]
        simple_mean_dec, weighted_dec = ActuarialReconciler.reconcile_cmmi_scores(scores_dec)
        explicit_global_score = safe_float(global_payload.get("global_cmmi_score"), locale=doc_lang)
        global_score = float(
            explicit_global_score if explicit_global_score is not None else weighted_dec
        )

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
                        text=t("kpi_exposure_header", locale=doc_lang) + " (ALE P50)",
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
        nodes.append(SpacerNode(points=14))

        triad_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=t("triad_col_dimension", locale=doc_lang), bold=True, is_header=True, font_size=8.5),
                    CellNode(text=t("triad_col_finding", locale=doc_lang), bold=True, is_header=True, font_size=8.5),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_triad_strength_title", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(
                        text=t("tomo_triad_strength_desc", locale=doc_lang),
                        bg_color="FFFFFF",
                        font_size=8.0,
                    ),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_triad_gap_title", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(
                        text=t("tomo_triad_gap_desc", locale=doc_lang),
                        bg_color="FFFFFF",
                        font_size=8.0,
                    ),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("tomo_triad_bottleneck_title", locale=doc_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(
                        text=t("tomo_triad_bottleneck_desc", locale=doc_lang),
                        bg_color="FFFFFF",
                        font_size=8.0,
                    ),
                ]
            ),
        ]
        nodes.append(TableNode(rows=triad_rows, autofit=True, col_widths=[0.28, 0.72]))
        nodes.append(SpacerNode(points=16))

        headline = t("tomo_ch1_headline", locale=doc_lang, client_name=client_name)
        nodes.append(ParagraphNode(text=f"**{headline}**", font_size=11.0, space_after=8))

        p1 = t("tomo_ch1_p1", locale=doc_lang, client_name=client_name, global_score=format_number(global_score, locale=doc_lang, decimals=2))
        nodes.append(ParagraphNode(text=p1, font_size=9.5, space_after=8))

        lead_in = t("tomo_ch1_lead_in", locale=doc_lang)
        nodes.append(ParagraphNode(text=lead_in, font_size=9.5, space_after=4, keep_with_next=True))

        local_rate_str = format_currency(fin_metrics["local_rate"], currency_symbol=currency, locale=doc_lang, decimals=0) + t("per_hour_suffix", locale=doc_lang)
        consolidated_rate_str = format_currency(fin_metrics["consolidated_rate"], currency_symbol=currency, locale=doc_lang, decimals=2) + t("per_hour_suffix", locale=doc_lang)
        b1_title = t("tomo_ch1_continuity_bullet_title", locale=doc_lang)
        b1_body = t(
            "tomo_ch1_continuity_bullet_body",
            locale=doc_lang,
            local_site_hourly_rate=local_rate_str,
            consolidated_hourly_rate=consolidated_rate_str,
        )
        bullet_1_text = f"{b1_title} {b1_body}"

        bullets = [
            bullet_1_text,
            t("tomo_ch1_bullet_2", locale=doc_lang),
            t("tomo_ch1_bullet_3", locale=doc_lang),
            t("tomo_ch1_bullet_4", locale=doc_lang),
        ]
        for idx, b in enumerate(bullets):
            is_last = (idx == len(bullets) - 1)
            parts = b.split(":", 1)
            f_bullet = f"**{parts[0].strip()}:** {parts[1].strip()}" if len(parts) > 1 else b
            nodes.append(ParagraphNode(text=f_bullet, style="List Bullet", font_size=9.0, space_after=8 if is_last else 3))

        p3 = t("tomo_ch1_p3", locale=doc_lang, formatted_ale=formatted_ale, formatted_p90=formatted_p90)
        nodes.append(ParagraphNode(text=p3, font_size=9.5, space_after=10))
        nodes.append(PageBreakNode())

    # =========================================================================
    # CHAPTER 2: CONSOLIDATED CAPABILITY MATURITY RADIOGRAPHY (CMMI) + RADAR
    # =========================================================================
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
        scores_dec = [Decimal(f"{s:.2f}") for s in domain_scores]
        simple_mean_dec, weighted_dec = ActuarialReconciler.reconcile_cmmi_scores(scores_dec)
        simple_mean = float(simple_mean_dec)
        simple_mean_str = format_number(simple_mean, locale=doc_lang, decimals=2)
        weighted_score = float(self._first_not_none(global_payload.get("global_cmmi_score"), weighted_dec))
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

        # Deterministic search for radar chart strictly in tenant output directory
        radar_path = None
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
            nodes.append(PictureNode(path=str(radar_path), width_inches=5.2))
            nodes.append(
                ParagraphNode(
                    text=f"*{t('tomo_fig_radar_caption', locale=doc_lang)}*",
                    font_size=8.5,
                    italic=True,
                    align="CENTER",
                    space_after=14,
                )
            )

        nodes.append(
            ParagraphNode(
                text=t("tomo_ch2_summary_p1", locale=doc_lang, overall_maturity=weighted_score_str),
                font_size=9.5,
                space_after=8,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("tomo_ch2_summary_p2", locale=doc_lang),
                font_size=9.5,
                space_after=12,
            )
        )
        nodes.append(PageBreakNode())

    # =========================================================================
    # CHAPTER 3: AGGREGATED OPEN FAIR ACTUARIAL RISK REGISTER + HEATMAP & CARDS
    # =========================================================================
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

        catalog = load_locales_catalog().get(doc_lang, load_locales_catalog().get("en", {}))
        catalog_loc = catalog.get("tomo_tower_forensic_catalog", {})

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

        domain_scenarios = fin_metrics.get("domain_scenario_counts") or self.CANONICAL_DOMAIN_SCENARIO_BASELINE
        total_scenarios_sum = sum(domain_scenarios.get(code, 3) for code, *_ in domain_meta)

        # 3.1 The Cost of Inaction: Annualized Financial Exposure by Domain
        nodes.append(
            HeadingNode(
                text=t("tomo_ch3_step1_heading", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        bridge_text = t(
            "tomo_ch3_sec31_reconciliation_bridge",
            locale=doc_lang,
            total_scenarios=total_scenarios_sum,
            total_domains=len(domain_meta),
        )
        nodes.append(ParagraphNode(text=bridge_text, font_size=9.5, space_after=8))

        reconciled_allocations = self._resolve_domain_allocations(
            global_payload=global_payload,
            tower_payloads=tower_payloads,
            target_corporate_ale=total_ale,
            domain_meta=domain_meta,
            catalog_loc=catalog_loc,
            doc_lang=doc_lang,
        )

        target_ale_int = self._round_half_up_int(total_ale)

        col_dom_lbl = t("tomo_ch3_table4_col_domain", locale=doc_lang)
        col_scen_lbl = t("tomo_ch3_table4_col_scenarios_count", locale=doc_lang)
        col_ann_lbl = t("tomo_ch3_table4_col_annual_exposure", locale=doc_lang)
        col_sev_lbl = t("tomo_ch3_table4_col_severe_event", locale=doc_lang)
        col_pct_lbl = t("tomo_ch3_table4_col_share_pct", locale=doc_lang)

        table4_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=col_dom_lbl, bold=True, is_header=True, font_size=8.5),
                    CellNode(text=col_scen_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_ann_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_sev_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                    CellNode(text=col_pct_lbl, bold=True, is_header=True, font_size=8.5, align="CENTER"),
                ],
                is_header=True,
            )
        ]

        target_p90_int = self._round_half_up_int(total_p90)
        raw_p90_pairs: List[Tuple[str, Decimal]] = [
            (code, Decimal(str(reconciled_allocations.get(code, 0))))
            for code, *_ in domain_meta
        ]
        reconciled_p90_allocations = ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=target_p90_int,
            domain_raw_exposures=raw_p90_pairs,
        )

        # Reconcile percentage shares across domains to strictly sum to 100.0%
        raw_pct_pairs: List[Tuple[str, Decimal]] = [
            (
                code,
                (Decimal(str(reconciled_allocations.get(code, 0))) / Decimal(str(target_ale_int)) * Decimal("1000"))
                if target_ale_int > 0
                else Decimal(str(round(1000.0 / max(1, len(domain_topology)), 2))),
            )
            for code, *_ in domain_topology
        ]
        reconciled_pct_tenths = ActuarialReconciler.reconcile_domain_allocations(
            target_corporate_ale=1000,
            domain_raw_exposures=raw_pct_pairs,
        )

        for code, clean_tower_name, _, _, _ in domain_topology:
            sc_count = domain_scenarios.get(code, 3)
            d_ale = reconciled_allocations.get(code, 0)
            d_p95 = reconciled_p90_allocations.get(code, 0)
            d_pct_val = reconciled_pct_tenths.get(code, 100) / 10.0
            d_pct_str = f"{format_number(d_pct_val, locale=doc_lang, decimals=1)}%"

            table4_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=f"{code} — {clean_tower_name}", font_size=8.0),
                        CellNode(text=str(sc_count), font_size=8.0, align="CENTER"),
                        CellNode(text=format_currency(d_ale, currency_symbol=currency, locale=doc_lang, decimals=0), font_size=8.0, align="CENTER"),
                        CellNode(text=format_currency(d_p95, currency_symbol=currency, locale=doc_lang, decimals=0), font_size=8.0, align="CENTER"),
                        CellNode(text=d_pct_str, font_size=8.0, align="CENTER"),
                    ]
                )
            )

        total_p95_sum = target_p90_int
        tot_label = t("tomo_ch3_table4_total_row_label", locale=doc_lang, total_domains=len(domain_meta))
        pct_100_str = f"{format_number(100.0, locale=doc_lang, decimals=1)}%"
        table4_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=tot_label, bold=True, bg_color="F8FAFC", font_size=8.5),
                    CellNode(text=str(total_scenarios_sum), bold=True, bg_color="F8FAFC", font_size=8.5, align="CENTER"),
                    CellNode(text=format_currency(target_ale_int, currency_symbol=currency, locale=doc_lang, decimals=0), bold=True, bg_color="F8FAFC", font_size=8.5, align="CENTER"),
                    CellNode(text=format_currency(total_p95_sum, currency_symbol=currency, locale=doc_lang, decimals=0), bold=True, bg_color="F8FAFC", font_size=8.5, align="CENTER"),
                    CellNode(text=pct_100_str, bold=True, bg_color="F8FAFC", font_size=8.5, align="CENTER"),
                ]
            )
        )
        nodes.append(TableNode(rows=table4_rows, autofit=True, col_widths=[0.32, 0.14, 0.22, 0.20, 0.12]))
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

        tier_pct_pairs = [("tier1", Decimal(str(t1_val))), ("tier2", Decimal(str(t2_val))), ("tier3", Decimal(str(t3_val)))]
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
                    CellNode(text=t("tomo_ch3_tier1_title", locale=doc_lang), bold=True, bg_color="FADBD8", font_size=8.5),
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
                    CellNode(text=t("tomo_ch3_tier3_title", locale=doc_lang), bold=True, bg_color="D5F5E3", font_size=8.5),
                    CellNode(text=str(t3_scenarios), bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=f"{t3_str} {t('per_year_suffix', locale=doc_lang)} ({pct3_str})", bold=True, bg_color="FFFFFF", align="CENTER", font_size=8.5),
                    CellNode(text=t("tomo_ch3_tier3_desc", locale=doc_lang), bg_color="FFFFFF", font_size=8.0),
                ]
            ),
        ]
        nodes.append(TableNode(rows=tier_rows, autofit=True, col_widths=[0.30, 0.10, 0.25, 0.35]))
        nodes.append(SpacerNode(points=8))

        loss_note = t("tomo_ch3_loss_composition_note", locale=doc_lang)
        nodes.append(
            ParagraphNode(
                text=loss_note,
                font_size=8.5,
                italic=True,
                text_color_rgb=[100, 100, 100],
                space_after=14,
            )
        )

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

        dynamic_lm_bounds = compute_dynamic_lm_thresholds(
            currency=currency,
            annual_revenue=fin_metrics["annual_revenue"],
            hourly_downtime_cost=fin_metrics["consolidated_rate"],
            is_critical_tier=bool(global_payload.get("meta", {}).get("is_critical", False)),
            locale=doc_lang,
        )
        heatmap_feed = global_payload.get("corporate_heatmap_risks") or catalog.get("tomo_corporate_heatmap_risks") or all_primary_risks
        if heatmap_feed:
            nodes.append(
                build_heatmap_mosaic(
                    heatmap_feed,
                    dynamic_lm_thresholds=dynamic_lm_bounds,
                    header_bg_color=self.primary_color_hex,
                    locale=doc_lang,
                    currency=currency,
                )
            )
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

        top_cards_feed = global_payload.get("corporate_top_risks")

        if not top_cards_feed and all_primary_risks:
            sorted_primary = sorted(
                all_primary_risks,
                key=lambda item: safe_float(item.get("ale") or item.get("ale_val"), locale=doc_lang, allow_zero=True) or 0.0,
                reverse=True,
            )
            top_cards_feed = []
            for r in sorted_primary[:5]:
                raw_sle = self._round_half_up_int(r.get("sle"))
                clean_lef = safe_float(r.get("lef"), locale=doc_lang, allow_zero=True) or 0.0
                raw_lef = Decimal(str(clean_lef)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                reconciled = ActuarialReconciler.reconcile_scenario_card(raw_sle, raw_lef)
                v_str = str(r.get("finding") or r.get("evidence") or "").strip()
                i_str = str(r.get("business_risk") or r.get("primary_impact") or "").strip()
                m_str = str(r.get("mitigation_directive") or "").strip()
                top_cards_feed.append(
                    {
                        "id": str(r.get("id") or "RSK-01"),
                        "title": str(r.get("capability") or r.get("finding") or t("default_risk_scenario_title", locale=doc_lang))[:65],
                        "ale": format_currency(reconciled["ale_p50"], currency_symbol=currency, locale=doc_lang, decimals=0) + t("per_year_suffix", locale=doc_lang),
                        "sle": format_currency(reconciled["sle"], currency_symbol=currency, locale=doc_lang, decimals=0),
                        "lef": f"{format_number(float(reconciled['lef']), locale=doc_lang, decimals=2)} {t('event_frequency_unit', locale=doc_lang)}",
                        "vuln": v_str if (not v_str or v_str.endswith(".")) else f"{v_str}.",
                        "impact": i_str if (not i_str or i_str.endswith(".")) else f"{i_str}.",
                        "mitig": m_str if (not m_str or m_str.endswith(".")) else f"{m_str}.",
                    }
                )

        if not top_cards_feed:
            top_cards_feed = catalog.get("tomo_top_risks_catalog", [])

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

        nodes.append(SpacerNode(points=10))
        formatted_p90 = format_currency(total_p90, currency_symbol=currency, locale=doc_lang, decimals=0)
        var_3y_expected = format_currency(fin_metrics["var_3y_expected"], currency_symbol=currency, locale=doc_lang, decimals=0)
        var_3y_tail = format_currency(fin_metrics["var_3y_tail"], currency_symbol=currency, locale=doc_lang, decimals=0)

        nodes.append(
            HeadingNode(
                text=t("tomo_ch3_p90_title", locale=doc_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(ParagraphNode(text=t("tomo_ch3_p90_1", locale=doc_lang), font_size=9.5, space_after=6))
        nodes.append(ParagraphNode(text=t("tomo_ch3_p90_2", locale=doc_lang, formatted_p90=formatted_p90), font_size=9.5, space_after=6))
        nodes.append(ParagraphNode(text=t("tomo_ch3_p90_3", locale=doc_lang, formatted_p90=formatted_p90), font_size=9.5, space_after=6))
        nodes.append(ParagraphNode(text=t("tomo_ch3_p90_4", locale=doc_lang, var_3y_expected=var_3y_expected, var_3y_tail=var_3y_tail), font_size=9.5, space_after=12))
        nodes.append(PageBreakNode())

    # =========================================================================
    # CHAPTER 4: FORENSIC DOMAIN DIAGNOSTICS (10 TOWERS) & CRITICAL SPOF MATRIX
    # =========================================================================
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

        catalog = load_locales_catalog().get(doc_lang, load_locales_catalog().get("en", {}))
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
        target_ale_int = self._round_half_up_int(fin_metrics["corporate_ale"])

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

            # Derive metrics dynamically prioritizing live payload telemetry
            payload_score = (
                t_payload.get("maturity_score")
                or t_payload.get("global_score")
                if isinstance(t_payload, dict)
                else None
            )
            raw_score = float(self._first_not_none(h_item.get("score"), payload_score, t_data.get("score_num"), default=2.50))

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
                        CellNode(text=f"**{strip_score_lbl}:** {score_fmt}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                        CellNode(text=f"**{strip_status_lbl}:** {status_val}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                        CellNode(text=f"**{strip_ale_lbl}:** {ale_fmt}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                        CellNode(text=f"**{strip_exposure_lbl}:** {exposure_val}", font_size=8.0, bg_color="F8FAFC", align="CENTER"),
                    ]
                )
            ]
            nodes.append(TableNode(rows=strip_rows, autofit=True, col_widths=[0.25, 0.25, 0.25, 0.25]))
            nodes.append(SpacerNode(points=6))

            # 1. Dynamic subpillars extraction from live payload
            pillars_analysis = t_payload.get("pillars_analysis", []) if isinstance(t_payload, dict) else []
            if pillars_analysis and isinstance(pillars_analysis, list):
                subpillars = []
                for p in pillars_analysis:
                    if isinstance(p, dict):
                        p_name = (
                            p.get("pillar_name")
                            or p.get("name")
                            or t("default_subpillar_label", locale=doc_lang)
                        )
                        p_score = safe_float(p.get("score"), locale=doc_lang, allow_zero=True)
                        subpillars.append([p_name, p_score if p_score is not None else 2.50])
            else:
                subpillars = t_data.get("subpillars") or []

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
                    client_name=str(global_payload.get("meta", {}).get("client") or "Organization").strip(),
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
            if not inventory:
                f_templates = catalog.get("forensic_domain_templates", {})
                inv_tmpl = f_templates.get("inventory_fallback") or "Scoped technological estate for {domain_code} ({domain_title}), encompassing {subpillar_count} evaluated control subpillars."
                inventory = inv_tmpl.format(
                    domain_code=code,
                    domain_title=matched_name,
                    subpillar_count=len(subpillars) if subpillars else 5,
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
                sorted_sp = sorted(subpillars, key=lambda x: float(x[1]) if isinstance(x[1], (int, float, Decimal)) else 0.0, reverse=True)
                top_sp = sorted_sp[0]
                f_templates = catalog.get("forensic_domain_templates", {})
                str_tmpl = (
                    f_templates.get("strength_fallback")
                    or f"Established baseline operational continuity in {{highest_subpillar_name}} (maturity index {{highest_subpillar_score}}/{max_cmmi_str})."
                )
                strengths = [
                    str_tmpl.format(
                        highest_subpillar_name=top_sp[0],
                        highest_subpillar_score=format_number(float(top_sp[1]), decimals=2, locale=doc_lang),
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
                sorted_sp = sorted(subpillars, key=lambda x: float(x[1]) if isinstance(x[1], (int, float, Decimal)) else 0.0)
                low_sp = sorted_sp[0]
                f_templates = catalog.get("forensic_domain_templates", {})
                fnd_tmpl = (
                    f_templates.get("finding_fallback")
                    or f"Control deficit in {{lowest_subpillar_name}} (maturity index {{lowest_subpillar_score}}/{max_cmmi_str})."
                )
                findings = [
                    fnd_tmpl.format(
                        lowest_subpillar_name=low_sp[0],
                        lowest_subpillar_score=format_number(float(low_sp[1]), decimals=2, locale=doc_lang),
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
                                        bg_color="F0FDFA",
                                        border_left_color="0D9488",
                                        border_left_size=24,
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
                                        bg_color="FFFBEB",
                                        border_left_color="D97706",
                                        border_left_size=24,
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
                for idx, sp in enumerate(subpillars):
                    sp_name = sp[0]
                    sp_score = sp[1]
                    sp_strength = strengths[idx] if idx < len(strengths) else ""
                    sp_finding = findings[idx] if idx < len(findings) else ""
                    sp_score_str = format_number(float(sp_score), decimals=2, locale=doc_lang) if isinstance(sp_score, (int, float, Decimal)) else str(sp_score)
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
            fallback_rank = localized_ranks.get(crit_token, canonical_criticality_ranks.get(crit_token, 99))
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

    # =========================================================================
    # CHAPTER 5: CROSS-TOWER NEXUS & SYSTEMIC INTERDEPENDENCIES
    # =========================================================================
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

        catalog = load_locales_catalog().get(doc_lang, load_locales_catalog().get("en", {}))
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

    # =========================================================================
    # UNIFIED APPENDIX: GLOSSARY & LEGAL LIABILITY DISCLAIMER
    # =========================================================================
    def _build_unified_appendix(
        self, nodes: List[DocNode], client_name: str, doc_lang: str
    ) -> None:
        """Unified Appendix: Clean Abbreviations Glossary (18/82 autofit) + Disclaimer."""
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

        glossary = load_abbreviations_glossary().get(doc_lang, load_abbreviations_glossary().get("en", {}))
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
        for disc_k in ("disclaimer_text_1", "disclaimer_text_2", "disclaimer_text_3", "disclaimer_text_4"):
            disc_text = t(disc_k, locale=doc_lang, client_name=client_name, company=client_name)
            nodes.append(ParagraphNode(text=disc_text, font_size=9.0, space_after=6))


# Legacy backward-compatibility alias
TomoAsisASTCompiler = Volume1AsisASTCompiler
