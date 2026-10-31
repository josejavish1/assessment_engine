import logging
logger = logging.getLogger(__name__)
import csv
import html
import json
import re
from pathlib import Path
from typing import Any, List

from assessment_engine.infrastructure.localization import (
    apply_vocabulary_substitutions,
    format_date_localized,
    format_number,
    get_localized_list,
    t,
)

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
    build_appendix_a_glossary as _build_appendix_a_glossary_fn,
    build_appendix_b_disclaimer as _build_appendix_b_disclaimer_fn,
    build_appendix_c_custody as _build_appendix_c_custody_fn,
    build_appendix_d_methodology as _build_appendix_d_methodology_fn,
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
        self.company_name = "Consultora"
        self.classification = "Confidencial"
        self.disclaimer = ""
        self.primary_color_rgb = [0, 114, 188]  # Primary corporate brand color code.
        self.alt_row_hex = "F2F2F2"

        self.brand_data = {}
        from assessment_engine.infrastructure.config_loader import load_brand_profile

        self.meta_lang = "en"
        try:
            brand = load_brand_profile()
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

            logger.debug(f"[Fallback] Handled exception: {ex}")


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

        nodes: List[Any] = []
        self._build_cover_and_toc(ctx, nodes)
        self._build_executive_summary_and_scope(ctx, nodes)
        self._build_systemic_risk_section(ctx, nodes)
        risks_data_list, fair_lookup = self._build_maturity_and_benchmarks(ctx, nodes)
        self._build_fair_risk_analysis(ctx, nodes, risks_data_list)
        self._build_detailed_findings_log(ctx, nodes, risks_data_list, fair_lookup)
        self._build_conclusions_and_appendices(ctx, nodes)

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

        if annex_file.exists():
            try:
                with open(annex_file, "r", encoding="utf-8-sig") as f:
                    json.load(f)
            except (OSError, ValueError, KeyError, AttributeError) as ex:

                logger.debug(f"[Fallback] Handled exception: {ex}")

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

        tower_name = tower_meta.get("tower_name", "Unknown")
        tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
        client_name = clean_client_name(tower_meta.get("client_name", "Client"))
        version = tower_meta.get("version", "1.0")
        date_str = format_date_localized(
            tower_meta.get("date"), locale=meta_lang
        )
        currency = tower_meta.get("currency") or self.brand_data.get("currency_symbol") or "USD"

        # Dynamically detect organizational scale to apply customized calibration.
        is_critical = self.brand_data.get("styling", {}).get("is_critical", None)
        if is_critical is None:
            is_critical = False # default fallback

        # Load scoring and global ALE data for interpolation.
        total_fair_ale = blueprint_data.get("total_fair_ale", 0.0)

        # Load scoring output to get exact score and band deterministically
        scoring_file = case_dir / "scoring_output.json"
        exact_score = None
        exact_band = None
        if scoring_file.exists():
            try:
                with open(scoring_file, "r", encoding="utf-8-sig") as sf:
                    score_data = json.load(sf)
                    exact_score = score_data.get("tower_score_exact")
                    exact_band = score_data.get("maturity_band_from_exact", {}).get("label")
            except Exception as e:
                logger.info(f"⚠️ Error loading scoring_output in AST Bridge: {e}")

        global_score = str(exact_score) if exact_score is not None else (
            blueprint_data.get("executive_summary", {})
            .get("global_score", "3.0")
            .split()[0]
        )
        global_band = exact_band if exact_band is not None else blueprint_data.get("executive_summary", {}).get(
            "global_band", t("band_defined", locale=meta_lang)
        )
        global_reading = (
            blueprint_data.get("pillar_score_profile", {})
            .get("pillars", [{}])[0]
            .get("executive_reading", "Standard Governance.")
        )

        try:
            gs_val = float(global_score)
        except Exception:
            gs_val = 3.0

        formatted_global_score = format_number(gs_val, locale=meta_lang, decimals=2)
        max_score_formatted = format_number(5.0, locale=meta_lang, decimals=2)
        display_score_str = f"{formatted_global_score} / {max_score_formatted}" 

        nodes: List[Any] = []

        return {
            "blueprint_file": blueprint_file,
            "annex_file": annex_file,
            "case_dir": case_dir,
            "modules_dir": modules_dir,
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
            "exact_score": exact_score,
            "exact_band": exact_band,
            "global_score": global_score,
            "global_band": global_band,
            "global_reading": global_reading,
            "gs_val": gs_val,
            "formatted_global_score": formatted_global_score,
            "display_score_str": display_score_str,
        }

    def _build_cover_and_toc(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        tower_name = ctx["tower_name"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        client_name = ctx["client_name"]
        date_str = ctx["date_str"]
        version = ctx["version"]
        meta_lang = ctx["meta_lang"]
        # 1. Corporate Cover Page
        #
        nodes.append(SpacerNode(points=120))

        # Title and Subtitle
        title_text = vocab.get("title", "Current State Assessment Report (AS-IS)")
        nodes.append(ParagraphNode(text=title_text, bold=True, space_after=12))
        nodes.append(
            HeadingNode(
                text=f"Technical Annex: {tower_name}",
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        nodes.append(SpacerNode(points=120))

        # Client (Project info is removed)
        client_lbl = vocab.get("client_lbl", "Cliente:\n")
        nodes.append(
            ParagraphNode(
                text=f"{client_lbl}{client_name.upper()}", bold=True, space_after=120
            )
        )

        classification_clean = self.classification.replace(" (Tier-1 Assessment)", "")

        # Date and classification
        nodes.append(
            ParagraphNode(
                text=f"{date_str} | Version {version} | {classification_clean}",
                italic=True,
                text_color_rgb=[150, 150, 150],
            )
        )
        nodes.append(PageBreakNode())

        #
        # CHAPTER 2: INDEX / TABLE OF CONTENTS
        #
        nodes.append(
            HeadingNode(
                text=vocab.get("toc_title", "Contenido"),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=10))
        
        # Build an elegant, highly polished, static-rendered executive Table of Contents
        for entry in get_localized_list("static_toc_entries", locale=meta_lang):
            nodes.append(ParagraphNode(text=entry))
        
        nodes.append(PageBreakNode())

        #

    def _build_executive_summary_and_scope(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        modules_dir = ctx["modules_dir"]
        meta_lang = ctx["meta_lang"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        global_band = ctx["global_band"]
        display_score_str = ctx["display_score_str"]
        global_reading = ctx["global_reading"]
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        # 3. CHAPTER 1: EXECUTIVE SUMMARY
        #
        resumen_path = modules_dir / "02_resumen_ejecutivo.md"
        if resumen_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(resumen_path))
        else:
            nodes.append(
                HeadingNode(
                    text=t("chapter_1_exec_summary", locale=meta_lang),
                    level=1,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )
            nodes.append(
                ParagraphNode(text=t("module_exec_summary_unavailable", locale=meta_lang))
            )

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

        intro_path = modules_dir / "01_introduccion.md"
        if intro_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(intro_path, skip_level_1=True))
        else:
            nodes.append(
                ParagraphNode(text=t("module_intro_scope_unavailable", locale=meta_lang))
            )

        # Section 2.3 (Strategic Business Context) has been symmetrically removed from tower-specific reports, as strategic alignment and traceability registry belong exclusively in the Global Consolidated Report, per Gartner standards.

        #
        # CHAPTER 3: TECHNOLOGICAL DIAGNOSIS AND PLATFORM ANALYSIS
        #
        nodes.append(
            HeadingNode(
                text=t("chapter_3_diagnosis_cross_cutting", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # 3.0 Direct Introduction (Consulting-grade synthesis)
        intro_ch3 = t("intro_ch3_technical_diagnosis", locale=meta_lang)
        nodes.append(ParagraphNode(text=intro_ch3))
        nodes.append(SpacerNode(points=10))

        # We completely bypass dumping 03_descripcion_plataforma.md to prevent repetitive walls of text.

        nodes.append(PageBreakNode())

        #
        # CHAPTER 4: MATURITY PROFILE AND GENERAL EVALUATION
        #
        nodes.append(
            HeadingNode(
                text=t("section_evaluation_maturity", locale=meta_lang),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # 4.1 Global Dashboard
        nodes.append(
            HeadingNode(
                text=t("dashboard_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("dashboard_intro", locale=meta_lang)
            )
        )

        #
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
                ]
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
        nodes.append(SpacerNode(points=10))

        # Read resilience data.
        res_reading = t("resilience_reading", locale=meta_lang)
        nodes.append(ParagraphNode(text=f"**{res_reading}** {global_reading}"))
        nodes.append(SpacerNode(points=15))

        health_title = t("health_matrix_title", locale=meta_lang)
        nodes.append(
            HeadingNode(
                text=health_title,
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=t("maturity_matrix_section_intro", locale=meta_lang),
                italic=True,
            )
        )
        nodes.append(SpacerNode(points=10))

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

        for s_idx, p in enumerate(sorted(blueprint_data.get("pillars_analysis", []), key=lambda item: item.get("score", 0.0))):
            bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
            resolver = get_taxonomy_resolver()
            raw_pname = p.get("pillar_name", p.get("pilar_name", "Pillar"))
            p_name = resolver.resolve_pillar_by_any_reference(
                p.get("pillar_id") or p.get("pilar_id") or raw_pname,
                default=raw_pname,
                locale=meta_lang,
            )
            p_score = float(p.get("score", 3.0))
            
            score_formatted = format_number(p_score, locale=meta_lang, decimals=2)
            
            # Map score to status and color
            if p_score >= 4.20:
                p_status = "Excellent (A)"
                p_bg_color = "D9F2D9"
            elif p_score >= 3.40:
                p_status = "Stable (B)"
                p_bg_color = "E2F0D9"
            elif p_score >= 2.60:
                p_status = "Standardized (C)"
                p_bg_color = "FFF3CD"
            elif p_score >= 1.80:
                p_status = "Basic (D)"
                p_bg_color = "FCE4D6"
            else:
                p_status = "Critical (F)"
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

        nodes.append(TableNode(rows=health_rows))
        nodes.append(SpacerNode(points=15))


    def _build_systemic_risk_section(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        meta_lang = ctx["meta_lang"]
        modules_dir = ctx["modules_dir"]
        intel_data = ctx["intel_data"]
        tower_id = ctx["tower_id"]
        transversal_title = t("transversal_analysis_title", locale=meta_lang)
        nodes.append(HeadingNode(text=transversal_title, level=2, primary_color_rgb=self.primary_color_rgb))
        trans_path = modules_dir / "05_transversal.md"
        if trans_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(trans_path, skip_level_1=True))
        nodes.append(SpacerNode(points=20))

        # 3.5 Systemic Risk Indicators and Decision Context (MCDA + Monte Carlo + LCBN)
        if intel_data:
            try:
                overrides = intel_data.get("tower_overrides", {}).get(tower_id, {})
                metrics = overrides.get("metrics", {}) if isinstance(overrides, dict) else {}
                business_criticality = metrics.get("business_criticality") if isinstance(metrics, dict) else None
                regulatory_compliance = metrics.get("regulatory_compliance") if isinstance(metrics, dict) else None
                implementation_feasibility = metrics.get("implementation_feasibility") if isinstance(metrics, dict) else None
                
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
                    dii_val = f"{dii_03:.1f}%" if dii_03 is not None else "0,0%"
                    erc_val = f"{erc:.3f}" if erc is not None else "0,000"

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
        client_name = ctx["client_name"]
        meta_lang = ctx["meta_lang"]
        # 4.2 Radar Chart
        nodes.append(
            HeadingNode(
                text=t("radar_title", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        radar_path = case_dir / "pillar_radar_chart.generated.png"
        if radar_path.exists():
            nodes.append(PictureNode(path=str(radar_path), width_inches=6.0))
            nodes.append(SpacerNode(points=15))

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
                        if verif_status == "verified" and quote and "no se encontraron" not in quote.lower() and "no se ha encontrado" not in quote.lower():
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
        csv_mat_path = modules_dir / "04_matriz_madurez.csv"
        if csv_mat_path.exists():
            # Ensure header collections are not empty to prevent the generation of malformed tables.
            mat_headers = get_localized_list("justification_table_headers", locale=meta_lang)
            nodes.append(self._parse_csv_generic(csv_mat_path, mat_headers))
        elif blueprint_data and blueprint_data.get("pillars_analysis"):
            from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
                derive_in_memory_maturity_matrix,
            )
            in_mem_rows = derive_in_memory_maturity_matrix(blueprint_data, doc_lang=meta_lang)
            mat_headers = get_localized_list("justification_table_headers", locale=meta_lang)
            header_cells = [
                CellNode(text=h, bold=True, font_size=9.0, bg_color="0072BC", align="CENTER")
                for h in mat_headers
            ]
            table_rows = [TableRowNode(cells=header_cells, is_header=True)]
            for r_idx, r_item in enumerate(in_mem_rows):
                bg = self.alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
                int_score = int(round(r_item["score"]))
                row_cells = [
                    CellNode(text=r_item["pillar_name"], bold=True, font_size=8.5, bg_color=bg),
                    CellNode(text=f"{int_score} ({r_item['band_label']})", font_size=8.5, bg_color=bg, align="CENTER"),
                    CellNode(text=r_item["justification"], font_size=8.5, bg_color=bg),
                ]
                table_rows.append(TableRowNode(cells=row_cells))
            nodes.append(TableNode(rows=table_rows))

        nodes.append(PageBreakNode())

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

            logger.debug(f"[Fallback] Handled exception: {ex}")

        # Read the CSV risks first so we have the data for the executive overview
        csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
        risks_data_list = []
        if csv_risks_path.exists():
            try:
                with open(csv_risks_path, "r", encoding="utf-8-sig") as cf:
                    reader = csv.reader(cf, delimiter=";")
                    next(reader)
                    for r_idx, row_data in enumerate(reader):
                        if not row_data or len(row_data) < 6:
                            continue
                        pilar_full_name = row_data[0].split(" - ")[0]
                        finding_raw = row_data[1]
                        finding_parts = finding_raw.split("\n\nEvidencia Forense Literal (Audit RAG):\n")
                        finding = finding_parts[0]
                        evidence = finding_parts[1].strip('"') if len(finding_parts) > 1 else ""

                        r_item = {
                            "id": f"RVS{r_idx + 1:02d}",
                            "pilar": pilar_full_name,
                            "capability": row_data[0].split(" - ")[1]
                            if " - " in row_data[0]
                            else row_data[0],
                            "finding": finding,
                            "evidence": evidence,
                            "business_risk": row_data[2],
                            "tef": float(row_data[3]),
                            "lm": float(row_data[4]),
                            "ale": float(row_data[5]),
                        }
                        risks_data_list.append(r_item)
            except (OSError, ValueError, KeyError, AttributeError) as ex:
                logger.debug(f"[Fallback] Handled exception: {ex}")
        elif blueprint_data and blueprint_data.get("pillars_analysis"):
            from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
                derive_in_memory_fair_risks,
            )
            rate_mult = float(ctx.get("rate_mult", 1.0))
            currency = ctx.get("currency", "€")
            risks_data_list, _ = derive_in_memory_fair_risks(
                blueprint_data, doc_lang=meta_lang, currency=currency, rate_mult=rate_mult
            )

        formatted_ale = format_number(
            total_fair_ale, locale=meta_lang, decimals=0
        )

        # Build executive risks summary paragraph
        if risks_data_list and total_fair_ale > 0:
            pillar_sums: dict[str, float] = {}
            for r in risks_data_list:
                p_name = str(r.get("pillar") or "Pillar")
                pillar_sums[p_name] = pillar_sums.get(p_name, 0.0) + float(r.get("ale") or 0.0)
            highest_pillar = max(pillar_sums, key=lambda k: pillar_sums[k])
            highest_pillar_val = pillar_sums[highest_pillar]
            
            highest_risk = max(risks_data_list, key=lambda x: float(x.get("ale") or 0.0))
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
            
            executive_risk_summary = t(
                "fair_risk_summary_detailed",
                locale=meta_lang,
                formatted_ale=formatted_ale,
                currency=currency,
                client_name=client_name,
                num_risks=len(risks_data_list),
                highest_pilar=highest_pillar,
                formatted_pilar_ale=formatted_pillar_ale,
                highest_risk_cap=highest_risk_cap,
                highest_risk_id=highest_risk_id,
                formatted_risk_ale=formatted_risk_ale,
                highest_risk_pct=highest_risk_pct,
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

        # 5.2 Methodological Legends (TEF & LM Scales)
        nodes.append(
            HeadingNode(
                text=t("methodological_legends_title", locale=meta_lang),
                level=3,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        nodes.append(
            HeadingNode(
                text=t("tef_title", locale=meta_lang),
                level=4,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(_build_tef_scale_table(vocab, meta_lang, self.alt_row_hex))
        nodes.append(SpacerNode(points=15))

        nodes.append(
            HeadingNode(
                text=t("lm_title", locale=meta_lang),
                level=4,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(_build_lm_scale_table(vocab, meta_lang, currency, is_critical, self.alt_row_hex))
        nodes.append(SpacerNode(points=10))

        if is_critical:
            nodes.append(
                ParagraphNode(
                    text=t("sector_calibration_note", locale=meta_lang),
                    italic=True,
                    space_after=12,
                )
            )
            nodes.append(SpacerNode(points=10))
        else:
            nodes.append(SpacerNode(points=10))


    def _build_detailed_findings_log(self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]], fair_lookup: dict[str, Any]) -> None:
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        currency = ctx["currency"]
        meta_lang = ctx["meta_lang"]
        # 5.3 Detailed Log Segmented by Domain (in multiple independent tables)
        if risks_data_list:
            nodes.append(
                HeadingNode(
                    text=t("detailed_risks_title", locale=meta_lang),
                    level=2,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )

            # Group risks by pillar.
            risks_by_pillar = {}
            for r in risks_data_list:
                p_name = r.get("pillar") or r.get("pilar", "Pillar")
                if p_name not in risks_by_pillar:
                    risks_by_pillar[p_name] = []
                risks_by_pillar[p_name].append(r)

            for p_name, pillar_risks in risks_by_pillar.items():
                # Display all identified technical risks for full analytical completeness
                pillar_risks_filtered = pillar_risks
                if not pillar_risks_filtered:
                    continue

                pilar_header = t("detailed_risks_pilar_title", locale=meta_lang) + p_name
                nodes.append(
                    HeadingNode(
                        text=pilar_header,
                        level=3,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )

                headers_table = get_localized_list("detailed_risks_headers", locale=meta_lang)
                risk_rows = [
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=h,
                                bold=True,
                                bg_color="0072BC",
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            )
                            for h in headers_table
                        ],
                        is_header=True,
                    )
                ]

                for s_idx, hc in enumerate(pillar_risks_filtered):
                    bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"

                    # Deduplicate or clean up repetitive prose between finding and evidence to improve readability
                    find_clean = (hc['finding'] or "").strip()
                    ev_clean = (hc.get("evidence") or "").strip()
                    
                    # Heuristic check for high redundancy: prefix/suffix overlap or substring
                    is_redundant = False
                    if ev_clean and find_clean:
                        ev_lower = ev_clean.lower()
                        find_lower = find_clean.lower()
                        if ev_lower in find_lower or find_lower in ev_lower:
                            is_redundant = True
                        elif ev_clean[:35].lower() == find_clean[:35].lower() or ev_clean[-35:].lower() == find_clean[-35:].lower():
                            is_redundant = True

                    v_lbl = t("vulnerability_identified_label", locale=meta_lang)
                    imp_lbl = t("it_operational_impact_label", locale=meta_lang)
                    desc_raw = (
                        f"**{v_lbl}**\n{find_clean}\n\n"
                        f"**{imp_lbl}**\n{hc['business_risk']}"
                    )
                    desc_text = apply_vocabulary_substitutions(
                        desc_raw, locale=meta_lang
                    )

                    #
                    tef = hc["tef"]
                    lm = hc["lm"]
                    ale = hc["ale"]
                    cap_name = hc["capability"]

                    # Fetch detailed FAIR metrics from lookup map
                    fair_metrics = fair_lookup.get(cap_name, {})
                    p90_val = fair_metrics.get("p90", 0.0) or 0.0
                    min_val = fair_metrics.get("min", 0.0) or 0.0
                    max_val = fair_metrics.get("max", 0.0) or 0.0

                    formatted_p90 = format_number(
                        p90_val, locale=meta_lang, decimals=0
                    )
                    formatted_min = format_number(
                        min_val, locale=meta_lang, decimals=0
                    )
                    formatted_max = format_number(
                        max_val, locale=meta_lang, decimals=0
                    )
                    formatted_ale_item = format_number(
                        ale, locale=meta_lang, decimals=0
                    )

                    calc_txt = "N/A"
                    bg_severe = bg
                    if ale and ale > 0:
                        calc_txt = (
                            f"**{t('calc_quant_exposure_title', locale=meta_lang)}**\n"
                            f"• {t('calc_tef_lbl', locale=meta_lang)}: {tef:.1f} / 5.0\n"
                            f"• {t('calc_lm_lbl', locale=meta_lang)}: {lm:.1f} / 5.0\n\n"
                            f"**{t('calc_projected_exposure_title', locale=meta_lang)}**\n"
                            f"• {t('calc_ale_lbl', locale=meta_lang)}: **{formatted_ale_item} {currency}**\n"
                            f"• {t('calc_worst_case_lbl', locale=meta_lang)}: {formatted_p90} {currency}\n"
                            f"• {t('calc_loss_range_lbl', locale=meta_lang)}: {formatted_min} {currency} - {formatted_max} {currency}"
                        )

                        risk_score = tef * lm
                        if risk_score >= 15 or ale >= 1000000:
                            bg_severe = "F8D7DA"  # Light Red
                        elif risk_score >= 10 or ale >= 250000:
                            bg_severe = "FFF3CD"  # Light Amber
                        elif risk_score >= 5 or ale >= 50000:
                            bg_severe = "E2E3E5"  # Light Gray

                    risk_rows.append(
                        TableRowNode(
                            cells=[
                                CellNode(
                                    text=hc["id"],
                                    bold=True,
                                    bg_color=self.alt_row_hex,
                                    align="CENTER",
                                ),
                                CellNode(text=desc_text, bg_color=bg, align="JUSTIFY"),
                                CellNode(
                                    text=calc_txt,
                                    bold=True,
                                    bg_color=bg_severe,
                                    align="RIGHT",
                                ),
                            ]
                        )
                    )

                nodes.append(TableNode(rows=risk_rows))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 5: CONCLUSIONS AND COST OF INACTION
        #

    def _build_conclusions_and_appendices(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        self._build_conclusions_chapter(ctx, nodes)
        nodes.append(PageBreakNode())
        _build_appendix_a_glossary_fn(ctx, nodes, self.primary_color_rgb)
        _build_appendix_b_disclaimer_fn(ctx, nodes, self.primary_color_rgb)
        _build_appendix_c_custody_fn(ctx, nodes, self.primary_color_rgb)
        _build_appendix_d_methodology_fn(
            ctx, nodes, self.primary_color_rgb, self.brand_data, self.alt_row_hex
        )

    def _build_conclusions_chapter(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        from assessment_engine.infrastructure.localization import t

        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        modules_dir = ctx["modules_dir"]
        meta_lang = ctx["meta_lang"]
        # 5.1 Transformation Paradigm (Promoted here from Chapter 4 as it represents a TO-BE vision)
        nodes.append(
            HeadingNode(
                text=t("transformation_paradigm_heading", locale=meta_lang),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        cca_data = blueprint_data.get("cross_capabilities_analysis", {}) if isinstance(blueprint_data, dict) else {}
        not_def_lbl = t("lbl_not_defined", locale=meta_lang)
        paradigm_text = cca_data.get("transformation_paradigm", not_def_lbl) if isinstance(cca_data, dict) else not_def_lbl
        nodes.append(ParagraphNode(text=paradigm_text, italic=True))
        nodes.append(SpacerNode(points=15))

        # 5.2 Next Steps and Impact of Inaction
        concl_path = modules_dir / "07_conclusiones.md"
        if concl_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(concl_path))

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
            if (
                "--- TABLA COMPARATIVA" in cleaned
                or "FORTALEZAS_CLAVE:" in cleaned
                or "BRECHAS_CLAVE:" in cleaned
                or "--- FIN TABLA" in cleaned
            ):
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

    def _extract_key_bullets_from_md(
        self, md_path: Path, section_marker: str
    ) -> List[str]:
        """Parses the conclusions file to extract identified strengths and weaknesses, structuring them for inclusion in the SWOT analysis table."""
        if not md_path.exists():
            return []
        with open(md_path, "r", encoding="utf-8") as f:
            lines = [html.unescape(line) for line in f.readlines()]
        bullets = []
        recording = False
        for line in lines:
            cleaned = line.strip()
            if section_marker in cleaned:
                recording = True
                continue
            if recording:
                if (
                    cleaned.startswith("BRECHAS_CLAVE:")
                    or cleaned.startswith("FORTALEZAS_CLAVE:")
                    or "--- FIN TABLA" in cleaned
                ):
                    break
                if cleaned.startswith("* ") or cleaned.startswith("- "):
                    bullets.append(cleaned[2:])
        return bullets

    def _parse_csv_generic(self, csv_path: Path, headers: List[str]) -> TableNode:
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

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  #
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

                    if c_idx == 2:
                        just_hdr = t("asis_header_score_justification", locale=getattr(self, "meta_lang", "en"))
                        val_str = re.sub(
                            r"\*\*.*?(?:Nota|Score|Evaluation)\s*\(\d+[,.]\d+\):\*\*",
                            f"**{just_hdr}**",
                            val_str
                        )
                        val_str = re.sub(
                            r".*?(?:Nota|Score|Evaluation)\s*\(\d+[,.]\d+\):",
                            just_hdr,
                            val_str
                        )
                        
                    cells.append(
                        CellNode(text=val_str, bold=bold, bg_color=bg, align=align)
                    )
                rows.append(TableRowNode(cells=cells))

        return TableNode(rows=rows)


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
    return out_p