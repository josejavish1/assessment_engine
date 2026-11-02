import logging
logger = logging.getLogger(__name__)
import csv
import html
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, List, Optional

from assessment_engine.infrastructure.localization import (
    apply_vocabulary_substitutions,
    format_currency,
    format_date_localized,
    format_number,
    get_localized_list,
    t,
)

from assessment_engine.domain.schemas.risk_ontology import (
    CausalBowTie,
    ConditionalLossEvent,
    CouplingRegime,
    FairActuarialInput,
)
from assessment_engine.domain.actuarial_calculator import ActuarialEngine

from assessment_engine.domain.schemas.ast import (
    CellNode,
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


def clean_client_name(client_name: str) -> str:
    """Clean raw client identifier removing version suffixes while preserving corporate casing."""
    if not client_name or not client_name.strip():
        return "Client"
    import re

    cleaned = re.sub(r"[_-][vV]\d+\b", "", client_name).strip()
    cleaned = cleaned.replace("_", " ")
    if " " not in cleaned:
        cleaned = cleaned.replace("-", " ")
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return "Client"

    # Only force capitalization on fully lowercase words to preserve mixed-case brands (e.g. McKinsey, PwC, JPMorgan)
    words = [w.capitalize() if w.islower() else w for w in cleaned.split(" ")]
    return " ".join(words)


from assessment_engine.adapters.compilers.ast_appendices_builder import (
    build_cmmi_methodology_and_capabilities as _build_cmmi_methodology_and_capabilities_fn,
    build_appendix_a_custody as _build_appendix_a_custody_fn,
    build_appendix_b_fair_methodology as _build_appendix_b_fair_methodology_fn,
    build_appendix_c_glossary_and_disclaimer as _build_appendix_c_glossary_and_disclaimer_fn,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    TEF_SCALE_DEFINITIONS,
    build_criticality_bullet as _build_criticality_bullet,
    build_dii_bullet as _build_dii_bullet,
    build_erc_bullet as _build_erc_bullet,
    build_feasibility_bullet as _build_feasibility_bullet,
    build_heatmap_mosaic as _build_heatmap_mosaic,
    build_lm_scale_table as _build_lm_scale_table,
    build_regulatory_bullet as _build_regulatory_bullet,
    build_spof_bullet as _build_spof_bullet,
    build_tef_scale_table as _build_tef_scale_table,
)


class ExecutiveNarrativeSynthesizer:
    """Compiles the 4-part Minto Pyramid Executive Summary for any capability tower (T1-T10).
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
    ) -> List[str]:
        """Synthesizes the 4 authoritative executive summary paragraphs for a capability tower."""
        f1 = findings_briefs[0] if len(findings_briefs) > 0 else t("default_critical_vulnerability", locale=self._locale_code)
        f2 = findings_briefs[1] if len(findings_briefs) > 1 else ""
        f3 = findings_briefs[2] if len(findings_briefs) > 2 else ""

        # Clean trailing periods and whitespace for smooth multi-clause synthesis
        f1 = f1.strip().rstrip(".")
        f2 = f2.strip().rstrip(".")
        f3 = f3.strip().rstrip(".")

        context = {
            "client_name": client_name.strip(),
            "tower_name": tower_name.strip(),
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
            "p90_var_exposure_fmt": p90_var_exposure_fmt.strip(),
            "remediation_horizon_label": remediation_horizon_label.strip(),
            "primary_remediation_pillar": primary_remediation_pillar.strip(),
            "target_maturity_score": target_maturity_score.strip(),
        }

        # Load narrative templates from locales.json
        from assessment_engine.infrastructure.runtime_paths import ROOT
        loc_file = ROOT / "engine_config" / "locales.json"
        loc_data = {}
        if loc_file.exists():
            try:
                loc_data = json.loads(loc_file.read_text(encoding="utf-8-sig"))
            except Exception:
                loc_data = {}

        narrative_section = loc_data.get("executive_summary_narrative", {}).get(self._locale_code, {})
        p1_tmpl = narrative_section.get("p1_operational_posture")
        p2_tmpl = (
            narrative_section.get("p2_architectural_dilemma")
            if len(findings_briefs) >= 3
            else narrative_section.get("p2_architectural_dilemma_single")
        )
        p3_tmpl = narrative_section.get("p3_financial_exposure")
        p4_tmpl = narrative_section.get("p4_modernization_mandate")

        paragraphs = []
        for p_idx, tmpl in enumerate([p1_tmpl, p2_tmpl, p3_tmpl, p4_tmpl], 1):
            if tmpl:
                rendered = tmpl.format(**context)
                unresolved = self.UNRESOLVED_TOKEN_PATTERN.findall(rendered)
                if unresolved:
                    raise ValueError(f"Unresolved tokens {unresolved} in paragraph {p_idx}")
                paragraphs.append(rendered)
            else:
                fallback_p = t(f"exec_narrative_p{p_idx}", locale=self._locale_code, **context)
                paragraphs.append(fallback_p)

        return paragraphs


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
        self.company_name = "Consulting Firm"
        self.classification = "Confidential"
        self.disclaimer = ""
        self.primary_color_rgb = [0, 114, 188]  # Primary corporate brand color code.
        self.alt_row_hex = "F2F2F2"

        self.brand_data = {}
        from assessment_engine.infrastructure.config_loader import load_brand_profile

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
        if not annex_file.exists():
            candidates = list(case_dir.glob("approved_annex_*.template_payload.json"))
            if candidates:
                annex_file = candidates[0]

        if annex_file.exists():
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
        client_name = clean_client_name(tower_meta.get("client_name", "Client"))
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

        # Load scoring and global ALE data for interpolation.
        total_fair_ale = blueprint_data.get("total_fair_ale", 0.0)

        # Load scoring output to get exact score deterministically
        scoring_file = case_dir / "scoring_output.json"
        exact_score = None
        if scoring_file.exists():
            try:
                with open(scoring_file, "r", encoding="utf-8-sig") as sf:
                    score_data = json.load(sf)
                    exact_score = score_data.get("tower_score_exact")
            except Exception as e:
                logger.info(f"⚠️ Error loading scoring_output in AST Bridge: {e}")

        global_score = str(exact_score) if exact_score is not None else (
            blueprint_data.get("executive_summary", {})
            .get("global_score", "3.0")
            .split()[0]
        )
        try:
            gs_val = float(global_score)
        except Exception:
            gs_val = 3.0

        from assessment_engine.domain.maturity_band import ANNEX_MATURITY_BANDS, resolve_maturity_band
        band_info = resolve_maturity_band(gs_val, ANNEX_MATURITY_BANDS, locale=meta_lang)
        localized_band_label = band_info.get("label", "Defined")
        level_prefix = t("level_prefix", locale=meta_lang)
        band_key_level_map = {
            "band_initial": 1,
            "band_repeatable": 2,
            "band_defined": 3,
            "band_managed": 4,
            "band_optimized": 5,
        }
        band_key = band_info.get("band_key", "band_defined")
        band_level = band_key_level_map.get(band_key, 3)
        global_band = f"{level_prefix} {band_level} - {localized_band_label}"

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
                text_color_rgb=[0, 114, 188],
                style="cover_subtitle",
                space_after=24,
            )
        )

        nodes.append(SpacerNode(points=30))

        # 3. Client Identity (28.0 pt, Bold, Client Label in #2E404D, Name in #0072BC)
        client_lbl = t("client_lbl", locale=meta_lang)
        nodes.append(
            ParagraphNode(
                text=f"**{client_lbl.strip()}** {client_name.upper()}",
                bold=True,
                font_size=28.0,
                text_color_rgb=[0, 114, 188],
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

        #

    def _build_executive_summary_and_scope(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        import re
        modules_dir = ctx["modules_dir"]
        meta_lang = ctx["meta_lang"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        global_band = ctx["global_band"]
        display_score_str = ctx["display_score_str"]
        global_reading = ctx["global_reading"]
        gs_val = ctx["gs_val"]
        annex_data = ctx.get("annex_data", {})

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
            annex_data.get("executive_summary") if annex_data else {}
        ) or blueprint_data.get("executive_snapshot", {})

        def _safe_float(val: Any, default: float = 0.0) -> float:
            if val is None:
                return default
            if isinstance(val, (int, float)):
                return float(val)
            try:
                clean_val = str(val).replace("$", "").replace("€", "").replace(",", "").strip()
                return float(clean_val)
            except (ValueError, TypeError):
                return default

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

        # -------------------------------------------------------------
        # COMPONENT A: EXECUTIVE KPI SNAPSHOT SCORECARD TABLE (3 COLUMNS)
        # -------------------------------------------------------------
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
                    CellNode(text=t("kpi_score_header", locale=meta_lang), bold=True, is_header=True),
                    CellNode(text=t("kpi_band_header", locale=meta_lang), bold=True, is_header=True),
                    CellNode(text=t("kpi_exposure_header", locale=meta_lang), bold=True, is_header=True),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=score_display, bold=True, align="CENTER", bg_color=self.alt_row_hex),
                    CellNode(text=global_band, bold=True, align="CENTER", bg_color=band_bg),
                    CellNode(text=f"{currency} {ale_formatted} {per_year_suffix}", bold=True, align="CENTER", bg_color="FCE4D6"),
                ]
            ),
        ]
        nodes.append(TableNode(rows=scorecard_rows, col_widths=[0.33, 0.33, 0.34]))
        nodes.append(SpacerNode(points=12))

        # -------------------------------------------------------------
        # COMPONENT B: EXECUTIVE HEADLINE & FLUID MECE NARRATIVE (PROSE)
        # -------------------------------------------------------------
        headline = exec_sum.get("headline", "")
        if headline:
            nodes.append(ParagraphNode(text=f"**{headline}**", font_size=11.5, space_after=8))

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
            from assessment_engine.domain.actuarial.downtime_calibrator import ActuarialDowntimeCalibrator
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
                pass

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
            raise ValueError("Missing 'global_annual_revenue' in financial_telemetry")
            
        perimeter_weight = fin_telemetry.get("perimeter_revenue_weight_pct")
        if perimeter_weight is None:
            raise ValueError("Missing 'perimeter_revenue_weight_pct' in financial_telemetry")
            
        effective_exposed = fin_telemetry.get("effective_exposed_revenue")
        if effective_exposed is None:
            raise ValueError("Missing 'effective_exposed_revenue' in financial_telemetry")
            
        sector_benchmark_source = fin_telemetry.get("sector_benchmark_source")
        if sector_benchmark_source is None:
            raise ValueError("Missing 'sector_benchmark_source' in financial_telemetry")
            
        sector_impact_factor = fin_telemetry.get("hourly_revenue_exposure_factor")
        if sector_impact_factor is None:
            raise ValueError("Missing 'hourly_revenue_exposure_factor' in financial_telemetry")
            
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
        from assessment_engine.domain.actuarial.risk_aggregator import BlastRadiusDeduplicator
        from decimal import Decimal
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
            blueprint_data.get("perimeter_context", {}).get("primary_workloads")
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
                first_pillar_name = str(first_p.get("pillar_name") or first_p.get("name") or "")

        primary_pillar = lead_init or first_pillar_name or t("default_remediation_pillar", locale=meta_lang)
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()
        primary_pillar_resolved = resolver.resolve_pillar_by_any_reference(primary_pillar, default=primary_pillar, locale=meta_lang)
        remediation_horizon = t("default_remediation_horizon", locale=meta_lang)

        synthesizer = ExecutiveNarrativeSynthesizer(locale_code=meta_lang)
        p_texts = synthesizer.synthesize_chapter_one_paragraphs(
            client_name=client_name,
            tower_name=tower_name,
            maturity_score=score_display,
            maturity_tier_label=global_band,
            primary_workloads_summary=primary_workloads,
            findings_briefs=findings_briefs,
            hourly_burn_rate_fmt=f"{currency} {hourly_formatted}",
            net_downtime_hours_fmt=eff_hours_str,
            annual_loss_expectancy_fmt=f"{currency} {ale_formatted}",
            p90_downtime_hours_fmt=p90_hours_str,
            p90_var_exposure_fmt=f"{currency} {p90_formatted}",
            remediation_horizon_label=remediation_horizon,
            primary_remediation_pillar=primary_pillar_resolved,
            target_maturity_score=target_score_str,
        )

        for p_idx, p_text in enumerate(p_texts):
            nodes.append(ParagraphNode(text=p_text, space_after=6 if p_idx < len(p_texts) - 1 else 8))
        nodes.append(SpacerNode(points=8))

        # -------------------------------------------------------------
        # COMPONENT C: EXECUTIVE DIAGNOSTIC TRIAD TABLE (STRENGTH/GAP/BOTTLENECK)
        # -------------------------------------------------------------
        m_strength = str(
            exec_sum.get("message_strength")
            or (blueprint_data.get("pillars_analysis", [{}])[0].get("health_check_asis", [{}])[0].get("capability") if blueprint_data.get("pillars_analysis") else "")
            or t("module_strength_default", locale=meta_lang)
        ).strip()
        m_gap = str(
            exec_sum.get("message_gap")
            or (blueprint_data.get("executive_snapshot", {}).get("structural_risks", [""])[0] if blueprint_data.get("executive_snapshot", {}).get("structural_risks") else "")
            or t("module_gap_default", locale=meta_lang)
        ).strip()
        m_bottleneck = str(
            exec_sum.get("message_bottleneck")
            or (blueprint_data.get("executive_snapshot", {}).get("business_impact", "") if blueprint_data.get("executive_snapshot", {}).get("business_impact") else "")
            or t("module_bottleneck_default", locale=meta_lang)
        ).strip()

        triad_rows = [
            TableRowNode(
                cells=[
                    CellNode(text=t("triad_col_dimension", locale=meta_lang), bold=True, is_header=True, font_size=8.5),
                    CellNode(text=t("triad_col_finding", locale=meta_lang), bold=True, is_header=True, font_size=8.5),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("triad_row_strength", locale=meta_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=m_strength, bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("triad_row_gap", locale=meta_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=m_gap, bg_color="FFFFFF", font_size=8.0),
                ]
            ),
            TableRowNode(
                cells=[
                    CellNode(text=t("triad_row_bottleneck", locale=meta_lang), bold=True, bg_color=self.alt_row_hex, font_size=8.0),
                    CellNode(text=m_bottleneck, bg_color="FFFFFF", font_size=8.0),
                ]
            ),
        ]
        nodes.append(TableNode(rows=triad_rows, col_widths=[0.30, 0.70]))
        nodes.append(SpacerNode(points=4))

        # Executive pacing: Chapter 1 stands strictly alone on Page 1
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

        intro = (annex_data.get("domain_introduction") if annex_data else {}) or {}
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
        if obj:
            nodes.append(ParagraphNode(text=obj, space_after=8))
        else:
            nodes.append(ParagraphNode(text=t("module_intro_scope_unavailable", locale=meta_lang), space_after=8))

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
            nodes.append(ParagraphNode(text=intro_para, space_after=8))

        if included_comps:
            lead_text = t("components_evaluated_lead", locale=meta_lang)
            if lead_text:
                nodes.append(ParagraphNode(text=f"**{lead_text}**", space_after=4))
            for comp in included_comps:
                nodes.append(ParagraphNode(text=comp, style="List Bullet", space_after=2))

        # 2.2 Regulatory and Methodological Framework Table (Auto-fit to window and contents)
        tower_id = str(ctx.get("tower_id") or "T1").upper()
        from assessment_engine.infrastructure.runtime_paths import ROOT
        import json

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
            CellNode(text=t("norm_col_standard", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="LEFT", font_size=9.5),
            CellNode(text=t("norm_col_scope", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="LEFT", font_size=9.5),
            CellNode(text=t("norm_col_purpose", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="LEFT", font_size=9.5),
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

        # 3. Direct Introduction (Accessible and clear executive prose)
        tower_name = str(ctx.get("tower_name") or blueprint_data.get("document_meta", {}).get("tower_name", "Infrastructure Domain"))
        intro_ch3 = t("intro_ch3_technical_diagnosis", locale=meta_lang, tower_name=tower_name)
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
                                bg_color="0072BC",
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            ),
                            CellNode(
                                text=t("maturity_lbl", locale=meta_lang),
                                bold=True,
                                bg_color="0072BC",
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

        # Friendly pedagogical score explanation (replaces robotic resilience string)
        if gs_val < 2.20:
            score_expl_key = "score_explanation_band_low"
        elif gs_val < 3.60:
            score_expl_key = "score_explanation_band_mid"
        else:
            score_expl_key = "score_explanation_band_high"

        max_score_formatted = format_number(5.0, locale=meta_lang, decimals=2)
        score_expl = t(
            score_expl_key,
            locale=meta_lang,
            global_score=display_score_str,
            max_score=max_score_formatted,
            client_name=client_name,
            tower_name=tower_name,
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
                    CellNode(text=col_1_hdr, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255]),
                    CellNode(text=col_2_hdr, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=col_3_hdr, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                ],
                is_header=True,
            )
        ]

        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()

        for s_idx, p in enumerate(sorted(blueprint_data.get("pillars_analysis", []), key=lambda item: item.get("score", 0.0))):
            bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            raw_pid = str(
                p.get("pillar_id")
                or p.get("id")
                or p.get("code")
                or ""
            )
            raw_pname = str(
                p.get("pillar_name")
                or p.get("name")
                or p.get("title")
                or ""
            )
            if not raw_pid:
                for k, v in p.items():
                    if "id" in k.lower() and v:
                        raw_pid = str(v)
                        break
            if not raw_pname:
                for k, v in p.items():
                    if "name" in k.lower() and v:
                        raw_pname = str(v)
                        break

            p_name = resolver.resolve_pillar_by_any_reference(
                raw_pid or raw_pname,
                default=(raw_pname or raw_pid or "Pillar"),
                locale=meta_lang,
            )
            p_score = float(p.get("score", 3.0))
            score_formatted = format_number(p_score, locale=meta_lang, decimals=2)
            
            # Map score to status and color via localized keys
            if p_score >= 4.20:
                p_status = t("status_excellent", locale=meta_lang)
                p_bg_color = "D9F2D9"
            elif p_score >= 3.40:
                p_status = t("status_stable", locale=meta_lang)
                p_bg_color = "E2F0D9"
            elif p_score >= 2.60:
                p_status = t("status_standardized", locale=meta_lang)
                p_bg_color = "FFF3CD"
            elif p_score >= 1.80:
                p_status = t("status_basic", locale=meta_lang)
                p_bg_color = "FCE4D6"
            else:
                p_status = t("status_critical", locale=meta_lang)
                p_bg_color = "F2D9D9"

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
            # 3.4 Cross-Cutting Structural Debt Patterns (domain-routed based on tower unit)
            nodes.append(
                HeadingNode(
                    text=t("cross_cutting_debt_title", locale=meta_lang),
                    level=2,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )
            nodes.append(ParagraphNode(text=t("cross_cutting_debt_intro", locale=meta_lang), italic=True))
            nodes.append(SpacerNode(points=6))
            pattern_keys = [
                f"cross_cutting_debt_{tower_id.lower()}_p{idx}"
                for idx in (1, 2, 3)
            ]
            for p_idx, p_key in enumerate(pattern_keys, 1):
                p_text = t(p_key, default="", locale=meta_lang)
                if not p_text:
                    p_text = t(f"cross_cutting_debt_universal_p{p_idx}", locale=meta_lang)
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
                                        CellNode(text=t("interdep_header_indicator", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255]),
                                        CellNode(text=t("interdep_header_value", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                                        CellNode(text=t("interdep_header_status", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                                    ],
                                    is_header=True,
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_business_criticality_title", locale=meta_lang)),
                                        CellNode(text=f"{business_criticality:.1f}%", align="CENTER"),
                                        CellNode(text=crit_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_reg_pressure_title", locale=meta_lang)),
                                        CellNode(text=f"{regulatory_compliance:.1f}%", align="CENTER"),
                                        CellNode(text=reg_lbl, align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text=t("interdep_op_viability_title", locale=meta_lang)),
                                        CellNode(text=f"{implementation_feasibility:.1f}%", align="CENTER"),
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

        # 4.3 Score Justification Matrix (from CSV or in-memory payload) with fallback mechanism
        csv_mat_candidates = (
            list(modules_dir.glob("*maturity*.csv"))
            + list(modules_dir.glob("*matrix*.csv"))
        ) if modules_dir.exists() else []
        csv_mat_path = csv_mat_candidates[0] if csv_mat_candidates else (modules_dir / "maturity_matrix.csv")
        if csv_mat_path.exists():
            # Ensure header collections are not empty to prevent the generation of malformed tables.
            mat_headers = get_localized_list("justification_table_headers", locale=meta_lang)
            nodes.append(self._parse_csv_generic(csv_mat_path, mat_headers, col_widths=[0.28, 0.14, 0.58]))
        elif blueprint_data and blueprint_data.get("pillars_analysis"):
            from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
                derive_in_memory_maturity_matrix,
            )
            in_mem_rows = derive_in_memory_maturity_matrix(blueprint_data, doc_lang=meta_lang)
            mat_headers = get_localized_list("justification_table_headers", locale=meta_lang)
            header_cells = [
                CellNode(
                    text=h,
                    bold=True,
                    font_size=9.0,
                    bg_color="0072BC",
                    text_color_rgb=[255, 255, 255],
                    align="CENTER",
                )
                for h in mat_headers
            ]
            table_rows = [TableRowNode(cells=header_cells, is_header=True)]
            for r_idx, r_item in enumerate(in_mem_rows):
                bg = self.alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
                score_val = float(r_item["score"])
                formatted_score = format_number(score_val, locale=meta_lang, decimals=2)
                band_label = r_item.get("band_label", "")
                row_cells = [
                    CellNode(text=r_item["pillar_name"], bold=True, font_size=8.5, bg_color=bg),
                    CellNode(text=f"{formatted_score} ({band_label})", font_size=8.5, bg_color=bg, align="CENTER"),
                    CellNode(text=r_item["justification"], font_size=8.5, bg_color=bg),
                ]
                table_rows.append(TableRowNode(cells=row_cells))
            nodes.append(TableNode(rows=table_rows, autofit=True, col_widths=[0.28, 0.14, 0.58]))

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

        # Read the CSV risks first so we have the data for the executive overview
        csv_candidates = list(modules_dir.glob("*.csv")) if modules_dir.exists() else []
        csv_risks_path = next(
            (f for f in csv_candidates if "fair" in f.name.lower() or "risk" in f.name.lower()),
            modules_dir / "fair_risks.csv",
        )
        risks_data_list = []
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
                                "ale": ale_val,
                            }
                            risks_data_list.append(r_item)
                        except (ValueError, IndexError) as row_ex:
                            logger.warning(f"[AST Bridge Warning] Skipped malformed risk row {r_idx}: {row_ex}")
            except (OSError, ValueError, KeyError, AttributeError) as ex:
                logger.warning(f"[AST Bridge Warning] Error reading risks CSV file: {ex}")
        elif blueprint_data and blueprint_data.get("pillars_analysis"):
            from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
                derive_in_memory_fair_risks,
            )
            rate_mult = float(ctx.get("rate_mult", 1.0))
            currency = str(ctx.get("currency") or blueprint_data.get("currency") or "")
            risks_data_list, _ = derive_in_memory_fair_risks(
                blueprint_data, doc_lang=meta_lang, currency=currency, rate_mult=rate_mult
            )

        formatted_ale = format_number(
            total_fair_ale, locale=meta_lang, decimals=0
        )

        # Build executive risks summary paragraph
        primary_risks = [r for r in risks_data_list if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"]
        if primary_risks and total_fair_ale > 0:
            pillar_sums: dict[str, float] = {}
            for r in primary_risks:
                p_name = str(r.get("pillar") or "Pillar")
                pillar_sums[p_name] = pillar_sums.get(p_name, 0.0) + float(r.get("ale") or 0.0)
            highest_pillar = max(pillar_sums, key=lambda k: pillar_sums[k])
            highest_pillar_val = pillar_sums[highest_pillar]
            
            highest_risk = max(primary_risks, key=lambda x: float(x.get("ale") or 0.0))
            highest_risk_id = str(highest_risk.get("id") or "RISK-01")
            highest_risk_cap = str(highest_risk.get("target_state") or highest_risk.get("capability") or "")
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

        nodes.append(ParagraphNode(text=executive_risk_summary))

        # Insert an inline executive methodological note referencing Appendix A.
        nodes.append(
            ParagraphNode(
                text=t("fair_methodology_note", locale=meta_lang),
                italic=True,
                space_after=12,
            )
        )

        return risks_data_list, fair_lookup

    def _build_fair_risk_analysis(self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]]) -> None:
        if not risks_data_list:
            return

        vocab = ctx["vocab"]
        meta_lang = ctx["meta_lang"]
        currency = ctx["currency"]
        is_critical = ctx["is_critical"]

        # 5.1 Generate 5x5 Heatmap (Word-native mosaic)
        nodes.append(
            HeadingNode(
                text=t("exposure_summary_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(_build_heatmap_mosaic(risks_data_list))
        nodes.append(SpacerNode(points=15))

        # 4.2 Risk Inventory Categorization into Three Strategic Portfolios
        nodes.append(SpacerNode(points=12))
        nodes.append(
            HeadingNode(
                text=t("risk_portfolio_tiers_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        primary_risks_total = sum(
            float(r.get("ale") or r.get("ale_val") or 0.0)
            for r in risks_data_list
            if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        )
        total_fair_ale = primary_risks_total if primary_risks_total > 0 else float(ctx.get("total_fair_ale") or 0.0)

        sorted_primary = sorted(
            [r for r in risks_data_list if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"],
            key=lambda x: float(x.get("ale") or x.get("ale_val") or 0.0),
            reverse=True,
        )
        t1_threshold = total_fair_ale * 0.15 if total_fair_ale > 0 else 0.0
        t2_threshold = total_fair_ale * 0.03 if total_fair_ale > 0 else 0.0

        t1_risks = [r for r in sorted_primary if float(r.get("ale") or r.get("ale_val") or 0.0) >= t1_threshold and float(r.get("ale") or 0.0) > 0.0]
        if not t1_risks and sorted_primary:
            t1_risks = sorted_primary[:max(1, len(sorted_primary) // 4)]
        
        t2_risks = [r for r in sorted_primary if t2_threshold <= float(r.get("ale") or r.get("ale_val") or 0.0) < t1_threshold and float(r.get("ale") or 0.0) > 0.0]
        if not t2_risks and len(sorted_primary) > len(t1_risks):
            t2_risks = sorted_primary[len(t1_risks):len(t1_risks) + max(1, len(sorted_primary) // 3)]

        t1_set = set(r.get("id") for r in t1_risks)
        t2_set = set(r.get("id") for r in t2_risks)
        t3_risks = [r for r in risks_data_list if r.get("id") not in t1_set and r.get("id") not in t2_set]

        t1_ids = ", ".join(r.get("id") for r in t1_risks) if t1_risks else "N/A"
        t2_ids = ", ".join(r.get("id") for r in t2_risks) if t2_risks else "N/A"
        t3_ids = ", ".join(r.get("id") for r in t3_risks) if t3_risks else "N/A"

        t1_sum = sum(float(r.get("ale") or r.get("ale_val") or 0.0) for r in t1_risks)
        t1_pct = int(round((t1_sum / total_fair_ale * 100))) if total_fair_ale > 0 else 0

        intro_tiers = t("risk_portfolio_tiers_intro", locale=meta_lang, num_total=len(risks_data_list))
        nodes.append(ParagraphNode(text=intro_tiers, italic=True))
        nodes.append(SpacerNode(points=6))
        nodes.append(ParagraphNode(text=t("risk_portfolio_tier_1_tpl", locale=meta_lang, ids=t1_ids, pct=t1_pct)))
        nodes.append(SpacerNode(points=4))
        nodes.append(ParagraphNode(text=t("risk_portfolio_tier_2_tpl", locale=meta_lang, ids=t2_ids)))
        nodes.append(SpacerNode(points=4))
        nodes.append(ParagraphNode(text=t("risk_portfolio_tier_3_tpl", locale=meta_lang, ids=t3_ids)))
        nodes.append(SpacerNode(points=15))

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
                text=t("detailed_risks_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
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

        # 2. Partition into the 3 Strategic Portfolios
        t1_threshold = total_fair_ale * 0.15 if total_fair_ale > 0 else 0.0
        t2_threshold = total_fair_ale * 0.03 if total_fair_ale > 0 else 0.0

        t1_risks = [
            r for r in sorted_risks
            if float(r.get("ale") or r.get("ale_val") or 0.0) >= t1_threshold
        ]
        if not t1_risks and sorted_risks:
            t1_risks = sorted_risks[:max(1, len(sorted_risks) // 4)]

        t2_risks = [
            r for r in sorted_risks
            if t2_threshold <= float(r.get("ale") or r.get("ale_val") or 0.0) < t1_threshold
        ]
        if not t2_risks and len(sorted_risks) > len(t1_risks):
            t2_risks = sorted_risks[len(t1_risks):len(t1_risks) + max(1, len(sorted_risks) // 3)]

        t1_set = set(r.get("id") for r in t1_risks)
        t2_set = set(r.get("id") for r in t2_risks)
        t3_risks = [r for r in sorted_risks if r.get("id") not in t1_set and r.get("id") not in t2_set]

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

        # 1. Authoritative Actuarial Reconciliation & Scale Calibration
        authoritative_ale = float(hc.get("intrinsic_ale") or hc.get("ale") or hc.get("ale_val") or 0.0)
        raw_tef = float(hc.get("tef") or 1.0)
        raw_lm = float(hc.get("lm") or 1.0)

        annual_divisor = float(blueprint_data.get("annual_downtime_divisor", 67.5))
        hourly_rate = float(
            blueprint_data.get("hourly_downtime_rate")
            or blueprint_data.get("hourly_burn_rate")
            or (total_fair_ale / annual_divisor if total_fair_ale > 0 else 10000.0)
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

        # Preserve empirical monetary SLE from source data if already scaled (> 5.0)
        if raw_lm > 5.0:
            effective_sle_num = raw_lm
            effective_sle_dec = Decimal(str(round(raw_lm, 2)))
            lef = round(authoritative_ale / effective_sle_num, 6) if (authoritative_ale > 0.0 and effective_sle_num > 0.0) else (raw_tef if raw_tef <= 10.0 else 0.20)
            mttr_hours = min(8.0, max(1.0, float(hc.get("downtime_hours") or 3.5)))
        else:
            # Calibrate from ordinal Likert (1-5 scale)
            if raw_tef >= 1.0:
                lef = min(0.50, max(0.08, raw_tef * 0.09))
            else:
                lef = max(0.05, raw_tef)

            mttr_hours = min(8.0, max(1.0, raw_lm * 0.85))
            effective_hourly = hourly_rate * alpha
            if authoritative_ale > 0.0 and lef > 0.0:
                effective_sle_dec = Decimal(str(authoritative_ale)) / Decimal(str(lef))
            else:
                effective_sle_dec = Decimal(str(round(mttr_hours * effective_hourly, 2)))

        base_sle_dec = (effective_sle_dec / Decimal(str(coupling_factor))).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        sle_val = max(Decimal("0.00"), base_sle_dec)

        actuarial_input = FairActuarialInput(
            loss_event_frequency_annual=round(max(0.0001, lef), 6),
            single_loss_magnitude_base=sle_val,
            operational_coupling_factor=coupling_factor,
            coupling_regime=coupling_regime,
            downtime_hours_mean=round(mttr_hours, 1),
            hourly_operational_impact=Decimal(str(round(hourly_rate * alpha, 2))),
        )

        ownership_type = str(hc.get("ownership_type") or "PRIMARY_CUSTODIAN")
        primary_risk_ref = hc.get("primary_risk_ref")
        contributing_towers = hc.get("contributing_towers") or []

        # Scale severity bounds dynamically relative to organizational exposure:
        portfolio_ale_dec = Decimal(str(round(total_fair_ale, 2))) if total_fair_ale > 0 else None
        metrics = ActuarialEngine.evaluate(
            actuarial_input,
            portfolio_total_ale=portfolio_ale_dec,
            ownership_type=ownership_type,
            primary_risk_ref=primary_risk_ref,
            contributing_towers=contributing_towers,
        )

        formatted_ale = format_currency(
            float(metrics.annualized_loss_expectancy),
            currency_symbol=currency,
            locale=meta_lang,
            decimals=0,
        )
        formatted_sle = format_currency(
            float(metrics.effective_sle),
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
        sev_badge_text = t(
            f"risk_card_severity_{metrics.severity_tier.lower()}",
            locale=meta_lang,
        )

        severity_colors = {
            "CRITICAL": "DC2626",
            "HIGH": "B45309",
            "ELEVATED": "1D4ED8",
            "MODERATE": "4B5563",
        }
        severity_bg_hex = severity_colors.get(metrics.severity_tier, "B45309")

        # 2. Causal Bow-Tie 3-Step Scenario Construction
        raw_threat = hc.get("initiating_threat")
        if raw_threat:
            threat_txt = str(raw_threat).strip()
        else:
            threat_txt = t("risk_card_default_threat", locale=meta_lang)

        raw_vuln = hc.get("control_vulnerability") or hc.get("finding")
        vuln_txt = str(raw_vuln or "").strip() or t("risk_card_default_vulnerability", locale=meta_lang)

        raw_impact = str(hc.get("primary_impact") or hc.get("business_risk") or "").strip()
        def_marker = t("defensibility_formula_marker", locale=meta_lang)
        if def_marker and def_marker in raw_impact:
            impact_clean = raw_impact.split(def_marker)[0].strip()
        else:
            impact_clean = raw_impact

        if not impact_clean:
            impact_txt = t("risk_card_default_impact", locale=meta_lang)
        else:
            impact_txt = impact_clean.rstrip(".!?") + "."

        raw_mitigation = hc.get("mitigation_directive") or hc.get("remediation")
        if raw_mitigation:
            directive_txt = str(raw_mitigation).strip()
        else:
            directive_txt = t("risk_card_default_mitigation", locale=meta_lang)

        evidence_txt = str(hc.get("evidence") or "").strip()

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

        # Apply specific styling if this is a tangential contributor
        if metrics.is_deduplicated:
            header_bg = "F1F5F9"
            header_text = [71, 85, 105]
            sev_badge_text = t("risk_card_ownership_badge_tangential", locale=meta_lang)
            sev_badge_bg = "64748B"
        else:
            header_bg = "1B263B"
            header_text = [255, 255, 255]
            sev_badge_bg = severity_bg_hex

        # Resolve plain-language cascade effect
        if coupling_factor >= 1.5:
            cascade_label = t("risk_card_cascade_high", locale=meta_lang)
        elif coupling_factor >= 1.2:
            cascade_label = t("risk_card_cascade_medium", locale=meta_lang)
        else:
            cascade_label = t("risk_card_cascade_low", locale=meta_lang)

        if metrics.is_deduplicated:
            notice_text = t("risk_card_deduplicated_ale_notice", locale=meta_lang).format(
                primary_risk_ref=loss_event.primary_risk_ref
            )
            kpi_row_cells = [
                CellNode(
                    text=f"*{notice_text}*",
                    font_size=9.0,
                    bold=True,
                    bg_color="F8FAFC",
                    text_color_rgb=[51, 65, 85],
                    grid_span=4,
                    width_dxa=9360,
                    align="RIGHT",
                )
            ]
        else:
            kpi_row_cells = [
                CellNode(
                    text=f"**{t('risk_card_ale_label', locale=meta_lang)}**\n{formatted_ale} / {t('year_lbl', locale=meta_lang)}",
                    font_size=8.0,
                    bg_color="F8FAFC",
                    text_color_rgb=[0, 114, 188],
                    grid_span=1,
                    width_dxa=2340,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{t('risk_card_sle_label', locale=meta_lang)}**\n{formatted_sle}",
                    font_size=8.0,
                    bg_color="F8FAFC",
                    grid_span=1,
                    width_dxa=2340,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{t('risk_card_lef_label', locale=meta_lang)}**\n{lef_formatted} {ev_unit}/{t('year_lbl', locale=meta_lang)}\n({return_period_str})",
                    font_size=8.0,
                    bg_color="F8FAFC",
                    grid_span=1,
                    width_dxa=2340,
                    align="CENTER",
                ),
                CellNode(
                    text=f"**{t('risk_card_cascade_label', locale=meta_lang)}**\n{cascade_label}\n(x{coupling_factor:.1f})",
                    font_size=8.0,
                    bg_color="F8FAFC",
                    grid_span=1,
                    width_dxa=2340,
                    align="CENTER",
                ),
            ]

        # Build transparent Actuarial Derivation Box for the CFO
        actuarial_box_text = (
            f"**{t('risk_card_actuarial_breakdown_title', locale=meta_lang)}:**\n"
            f"SLE = (MTTR {mttr_hours:.1f}h × {format_currency(effective_hourly, currency_symbol=currency, locale=meta_lang, decimals=0)}/h) = {formatted_sle}  |  "
            f"ALE = SLE × {lef_formatted} {ev_unit}/{t('year_lbl', locale=meta_lang)} = {formatted_ale}/{t('year_lbl', locale=meta_lang)}"
        )
        if evidence_txt:
            ev_lbl = t("audit_evidence_label", locale=meta_lang)
            actuarial_box_text += f"\n{ev_lbl}: \"{evidence_txt}\""

        card_table = TableNode(
            rows=[
                TableRowNode(
                    cells=[
                        CellNode(
                            text=f"[{loss_event.event_id}] {loss_event.title}\n{loss_event.domain_category}",
                            font_size=9.5,
                            bold=True,
                            bg_color=header_bg,
                            text_color_rgb=header_text,
                            grid_span=3,
                            width_dxa=7020,
                            align="LEFT",
                        ),
                        CellNode(
                            text=f"{sev_badge_text} ({share_pct:.1f}%)",
                            font_size=8.5,
                            bold=True,
                            bg_color=sev_badge_bg,
                            text_color_rgb=[255, 255, 255],
                            grid_span=1,
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
                            grid_span=2,
                            width_dxa=4680,
                            border_left_color="E63946",
                            border_left_size=24,
                            align="LEFT",
                        ),
                        CellNode(
                            text=f"**{t('risk_card_operational_impact_label', locale=meta_lang)}:**\n{impact_txt}",
                            font_size=8.0,
                            bg_color="FFFFFF",
                            grid_span=2,
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
                            bg_color="F8FAFC",
                            grid_span=4,
                            width_dxa=9360,
                            border_left_color="0072BC",
                            border_left_size=24,
                            align="LEFT",
                        ),
                    ],
                    cant_split=True,
                ),
            ],
            column_widths_dxa=[2340, 2340, 2340, 2340],
            keep_together=True,
        )
        return card_table

        #
        # CHAPTER 5: CONCLUSIONS AND COST OF INACTION
        #

    def _build_conclusions_and_appendices(
        self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]] | None = None
    ) -> None:
        self._build_conclusions_chapter(ctx, nodes, risks_data_list or [])
        _build_appendix_b_fair_methodology_fn(
            ctx, nodes, self.primary_color_rgb, self.brand_data, self.alt_row_hex
        )
        _build_appendix_c_glossary_and_disclaimer_fn(ctx, nodes, self.primary_color_rgb)

    def _build_conclusions_chapter(
        self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]]
    ) -> None:
        from assessment_engine.infrastructure.localization import t

        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        meta_lang = ctx["meta_lang"]
        currency = str(
            ctx.get("currency")
            or blueprint_data.get("document_meta", {}).get("currency_code")
            or blueprint_data.get("currency")
            or "USD"
        )

        # 5. Chapter Main Heading: 5. Conclusions & Baseline Diagnostic Synthesis (AS-IS)
        nodes.append(
            HeadingNode(
                text=t("chapter_5_strategic_roadmap", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # 5.1 Observed Structural Maturity Posture
        exact_band = ctx.get("exact_band") or ctx.get("global_band") or "Defined"
        display_score = ctx.get("display_score_str") or "3.00 / 5.00"
        summary_intro = t(
            "conclusions_summary_intro",
            locale=meta_lang,
            client_name=client_name,
            exact_band=exact_band,
            display_score=display_score,
        )
        nodes.append(ParagraphNode(text=summary_intro, space_after=12))

        # 5.2 Vulnerability Concentration Matrix & Operational Urgency Table
        nodes.append(
            HeadingNode(
                text=t("conclusions_urgency_table_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        headers = [
            CellNode(
                text=t("conclusions_col_fragility_domain", locale=meta_lang),
                bold=True,
                bg_color="0F172A",
                text_color_rgb=[255, 255, 255],
                align="LEFT",
                font_size=9.0,
            ),
            CellNode(
                text=t("conclusions_col_vulnerability", locale=meta_lang),
                bold=True,
                bg_color="0F172A",
                text_color_rgb=[255, 255, 255],
                align="LEFT",
                font_size=9.0,
            ),
            CellNode(
                text=t("conclusions_col_annual_exposure", locale=meta_lang),
                bold=True,
                bg_color="0F172A",
                text_color_rgb=[255, 255, 255],
                align="RIGHT",
                font_size=9.0,
            ),
            CellNode(
                text=t("conclusions_col_urgency", locale=meta_lang),
                bold=True,
                bg_color="0F172A",
                text_color_rgb=[255, 255, 255],
                align="CENTER",
                font_size=9.0,
            ),
        ]
        rows = [TableRowNode(cells=headers, is_header=True)]

        primary_risks = [
            r for r in risks_data_list if r.get("ownership_type") != "TANGENTIAL_CONTRIBUTOR"
        ]
        total_ale = sum(float(r.get("ale") or r.get("ale_val") or 0.0) for r in primary_risks)
        if total_ale <= 0.0:
            total_ale = float(ctx.get("total_fair_ale") or 0.0)

        sorted_risks = sorted(
            primary_risks,
            key=lambda x: float(x.get("ale") or x.get("ale_val") or 0.0),
            reverse=True,
        )

        for idx, r in enumerate(sorted_risks[:8]):
            r_ale = float(r.get("ale") or r.get("ale_val") or 0.0)
            formatted_r_ale = format_currency(
                r_ale, currency_symbol=currency, locale=meta_lang, decimals=0
            )
            share_pct = (r_ale / total_ale * 100.0) if total_ale > 0 else 0.0

            if share_pct >= 25.0 or float(r.get("tef", 1.0)) >= 3.0:
                urgency_text = t("urgency_immediate", locale=meta_lang)
                urgency_bg = "FEE2E2"
                urgency_fg = [185, 28, 28]
            elif share_pct >= 15.0 or float(r.get("tef", 1.0)) >= 2.0:
                urgency_text = t("urgency_high", locale=meta_lang)
                urgency_bg = "FEF3C7"
                urgency_fg = [180, 83, 9]
            else:
                urgency_text = t("urgency_moderate", locale=meta_lang)
                urgency_bg = "F1F5F9"
                urgency_fg = [71, 85, 105]

            bg = self.alt_row_hex if idx % 2 == 1 else "FFFFFF"
            dom_name = str(r.get("pillar") or r.get("domain") or "Infrastructure")
            vuln_name = str(
                r.get("capability") or r.get("target_state") or r.get("finding") or "Vulnerability"
            )
            if len(vuln_name) > 65:
                vuln_name = vuln_name[:62] + "..."

            r_id = str(r.get("id") or f"R{idx+1:02d}")
            rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=dom_name, bold=True, bg_color=bg, align="LEFT", font_size=8.5),
                        CellNode(
                            text=f"[{r_id}] {vuln_name}",
                            bg_color=bg,
                            align="LEFT",
                            font_size=8.5,
                        ),
                        CellNode(
                            text=formatted_r_ale,
                            bold=True,
                            bg_color=bg,
                            align="RIGHT",
                            font_size=8.5,
                        ),
                        CellNode(
                            text=urgency_text,
                            bold=True,
                            bg_color=urgency_bg,
                            text_color_rgb=urgency_fg,
                            align="CENTER",
                            font_size=8.0,
                        ),
                    ]
                )
            )

        if len(rows) > 1:
            nodes.append(TableNode(rows=rows))
            nodes.append(SpacerNode(points=16))

        # 5.3 Objective Architectural Synthesis
        formatted_total_ale = format_currency(
            total_ale, currency_symbol=currency, locale=meta_lang, decimals=0
        )
        closing_text = t(
            "conclusions_closing_text",
            locale=meta_lang,
            formatted_ale=formatted_total_ale,
        )
        nodes.append(ParagraphNode(text=closing_text, space_after=12))

        #

    def _parse_markdown_to_nodes(
        self, md_path: Path, skip_level_1: bool = False
    ) -> List[Any]:
        """Parses a Markdown file, converting its content into a sequence of Abstract Syntax Tree (AST) nodes."""
        nodes = []
        if not md_path.exists():
            return nodes

        with open(md_path, "r", encoding="utf-8") as f:
            lines = [html.unescape(line) for line in f.readlines()]

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Sanitization: Replace non-standard vocabulary with canonical terms
            if isinstance(cleaned, str):
                cleaned = apply_vocabulary_substitutions(
                    cleaned, locale=getattr(self, "meta_lang", "en")
                )

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
                        bg_color="0072BC",
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
                for c_idx, val in enumerate(row_data):
                    bold = c_idx == 0
                    align = (
                        "CENTER"
                        if c_idx == 1
                        else ("JUSTIFY" if c_idx == 2 else "LEFT")
                    )
                    
                    val_str = str(val)
                    if isinstance(val_str, str):
                        meta_l = getattr(self, "meta_lang", "en")
                        val_str = apply_vocabulary_substitutions(
                            val_str, locale=meta_l
                        )

                    if c_idx == 0 and isinstance(val_str, str) and val_str.strip():
                        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
                        resolver = get_taxonomy_resolver()
                        val_str = resolver.resolve_pillar_by_any_reference(
                            val_str, default=val_str, locale=getattr(self, "meta_lang", "en")
                        )

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
                        
                    cells.append(
                        CellNode(text=val_str, bold=bold, bg_color=bg, align=align)
                    )
                rows.append(TableRowNode(cells=cells))

        return TableNode(rows=rows, autofit=True, col_widths=col_widths)


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
    from assessment_engine.adapters.compilers.docx_compiler import DocxCompiler

    compiler = DocxCompiler()
    out_p = Path(output_docx_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    compiler.compile(ast, str(out_p))

    # Synchronize physical page numbers into the TOC SDT to eliminate split-brain
    from assessment_engine.adapters.compilers.toc_page_resolver import DeterministicTocPageResolver

    DeterministicTocPageResolver.synchronize_docx_toc(out_p)

    return out_p