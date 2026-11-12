from __future__ import annotations

import json
import logging
import re
from typing import Any, List

from assessment_engine.adapters.compilers.ast_table_builders import (
    build_lm_scale_table,
    build_tef_scale_table,
)
from assessment_engine.domain.schemas.ast import (
    CellNode,
    HeadingNode,
    ParagraphNode,
    SpacerNode,
    TableNode,
    TableRowNode,
)
from assessment_engine.infrastructure.localization import get_localized_list, t

logger = logging.getLogger(__name__)


def _get_appendix_strip_regex() -> str:
    from assessment_engine.infrastructure.runtime_paths import ROOT
    p = ROOT / "engine_config/locales_asis_annex.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get(
                "appendix_strip_regex", r"^(?:Appendix|Ap\u00e9ndice|Annexe|Anhang|\u4ed8\u9332)\s*[A-Z][.:]\s*"
            )
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug("[Fallback] Handled exception: %s", ex)
    return r"^(?:Appendix|Ap\u00e9ndice|Annexe|Anhang|\u4ed8\u9332)\s*[A-Z][.:]\s*"


def build_cmmi_methodology_and_capabilities(
    ctx: dict[str, Any],
    nodes: List[Any],
    primary_color_rgb: Any,
    heading_key: str = "maturity_scale_title",
) -> None:
    """Builds CMMI 5-Level Maturity Scale and Evaluated Capabilities Allocation for Chapter 2."""
    meta_lang = ctx["meta_lang"]
    tower_id = ctx["tower_id"]
    blueprint_data = ctx["blueprint_data"]

    # 2.3 Five-Level Analytical Maturity Scale (CMMI)
    nodes.append(SpacerNode(points=6))
    nodes.append(
        HeadingNode(
            text=t(heading_key, locale=meta_lang),
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text=t("maturity_scale_intro", locale=meta_lang),
            space_after=4,
            font_size=10.5,
            text_color_rgb=[46, 64, 77],
        )
    )
    from assessment_engine.domain.governance import GovernanceScaleEngine
    from assessment_engine.infrastructure.localization import format_number

    engine = GovernanceScaleEngine.get_instance()
    bands = engine.config.get("cmmi_maturity_scale", {}).get("bands", [])

    prev_bound = 1.00
    for idx, b in enumerate(bands):
        level_num = b["level"]
        upper_bound = float(b["upper_bound_exclusive"])
        min_score = 1.00 if idx == 0 else prev_bound
        max_score = 5.00 if idx == len(bands) - 1 else round(upper_bound - 0.01, 2)
        prev_bound = upper_bound

        min_fmt = format_number(min_score, locale=meta_lang, decimals=2)
        max_fmt = format_number(max_score, locale=meta_lang, decimals=2)

        band_token = b.get("label_token", f"band_{level_num}")
        level_prefix = t("level_prefix", locale=meta_lang, default="Nivel" if meta_lang.startswith("es") else "Level")

        if meta_lang.startswith("es") and level_num == 2:
            band_label = "Administrado"
        else:
            band_label = t(band_token, locale=meta_lang, default=b.get("default_label", ""))

        desc = t(f"cmmi_desc_level_{level_num}", locale=meta_lang, default="")

        bullet_text = (
            f"**{level_prefix} {level_num} - {band_label} ({min_fmt} - {max_fmt}):** {desc}"
            if desc
            else f"**{level_prefix} {level_num} - {band_label} ({min_fmt} - {max_fmt})**"
        )
        nodes.append(
            ParagraphNode(
                text=bullet_text,
                style="List Bullet",
                space_after=2,
                font_size=10.5,
                text_color_rgb=[46, 64, 77],
            )
        )

    # 2.4 Evaluated Capabilities and Pillar Weight Allocation
    nodes.append(SpacerNode(points=6))
    nodes.append(
        HeadingNode(
            text=t("evaluated_capabilities_title", locale=meta_lang),
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text=t("evaluated_capabilities_intro", locale=meta_lang),
            space_after=4,
            font_size=10.5,
            text_color_rgb=[46, 64, 77],
        )
    )

    from assessment_engine.infrastructure.runtime_paths import ROOT
    tower_def_file = (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id.lower()}.json"
    )
    if not tower_def_file.exists():
        tower_def_file = (
            ROOT
            / "engine_config"
            / "towers"
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )

    t_def = {}
    if tower_def_file.exists():
        try:
            with open(tower_def_file, "r", encoding="utf-8-sig") as tdf:
                t_def = json.load(tdf)
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug("[Fallback] Handled exception: %s", ex)

    pillars_list = t_def.get("pillars", []) if isinstance(t_def, dict) else []
    if not pillars_list:
        pillars_list = blueprint_data.get("pillars_analysis", [])

    from assessment_engine.domain.taxonomy_resolver import (
        extract_pillar_identifiers,
        get_taxonomy_resolver,
    )
    resolver = get_taxonomy_resolver()

    for p_idx, p in enumerate(pillars_list):
        raw_pid, raw_pname = extract_pillar_identifiers(p)
        p_name = resolver.resolve_pillar_by_any_reference(
            raw_pid or raw_pname,
            default=raw_pname or raw_pid or "Pillar",
            locale=meta_lang,
            tower_id=tower_id,
        )
        p_weight = int(p.get("weight_pct", p.get("weight", 20)))
        kpi_list = p.get("kpis", [])
        distinct_names = []
        for kpi in kpi_list:
            raw_kname = kpi.get("kpi_name", "KPI").strip()
            k_id = kpi.get("kpi_id", "").strip()
            loc_kname = kpi.get(f"kpi_name_{meta_lang}") or resolver.resolve_capability_name(
                k_id or raw_kname, default="", locale=meta_lang
            )
            if loc_kname and loc_kname.strip():
                distinct_names.append(loc_kname.strip())
            elif raw_kname:
                distinct_names.append(raw_kname)

        if distinct_names and len(distinct_names) == len(kpi_list):
            formatted_names = [
                n[0].lower() + n[1:] if n and not n.isupper() and len(n) > 4 else n
                for n in distinct_names
            ]
            and_str = t("connector_and", locale=meta_lang)
            if len(formatted_names) > 1:
                kpi_str = ", ".join(formatted_names[:-1]) + and_str + formatted_names[-1]
            else:
                kpi_str = formatted_names[0]
        elif kpi_list:
            # Syntactic Grouping (Argon Phase 2): Group IDs under a single clean noun phrase
            first_k = kpi_list[0].get("kpi_id", "")
            last_k = kpi_list[-1].get("kpi_id", "")
            range_label = f"({first_k} - {last_k})" if first_k and last_k and first_k != last_k else f"({first_k})"
            kpi_str = f"{p_name} operational controls and verified standards {range_label}"
        else:
            kpi_str = t("lbl_default_pillar_kpis", locale=meta_lang)

        weight_lbl = t("lbl_weight", locale=meta_lang)
        verb_intro = t(f"pillar_intro_{p_idx % 5}", locale=meta_lang)
        p_bullet_text = t(
            "pillar_bullet_evaluates_format",
            locale=meta_lang,
            name=p_name,
            weight_lbl=weight_lbl,
            weight=p_weight,
            verb_intro=verb_intro,
            kpi_str=kpi_str,
        )
        nodes.append(
            ParagraphNode(
                text=p_bullet_text,
                style="List Bullet",
                space_after=3,
                font_size=10.5,
                text_color_rgb=[46, 64, 77],
            )
        )


def build_appendix_a_custody(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix A: Chain of Custody & Document Provenance Registry."""
    vocab = ctx["vocab"]
    meta_lang = ctx.get("meta_lang", "en")
    app_a_title = t("ast_appendix_custody_title", locale=meta_lang)
    nodes.append(
        HeadingNode(
            text=app_a_title,
            level=1,
            primary_color_rgb=primary_color_rgb,
            is_appendix=True,
        )
    )
    default_intro = t("appendix_c_default_intro", locale=meta_lang)
    nodes.append(
        ParagraphNode(
            text=vocab.get(
                "appendix_c_intro",
                default_intro,
            )
        )
    )
    nodes.append(SpacerNode(points=8))

    client_name = str(ctx.get("client_name") or "CLIENT").upper()
    tower_name = str(ctx.get("tower_name") or "Tower")
    alt_row_hex = "F8FAFC"

    headers = [
        CellNode(text=t("custody_col_code", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER", font_size=8.5),
        CellNode(text=t("custody_col_source", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="LEFT", font_size=8.5),
        CellNode(text=t("custody_col_desc", locale=meta_lang), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="LEFT", font_size=8.5),
    ]
    rows = [TableRowNode(cells=headers, is_header=True)]

    client_slug = re.sub(r"[^a-z0-9]+", "_", client_name.lower()).strip("_")
    raw_items = get_localized_list("custody_sources_items", locale=meta_lang)
    for idx, item in enumerate(raw_items):
        bg = alt_row_hex if idx % 2 == 1 else "FFFFFF"
        if isinstance(item, dict):
            c_code = item.get("code", "")
            c_src = item.get("source", "").replace("{client_slug}", client_slug)
            c_desc = item.get("desc", "").replace("{tower_name}", tower_name).replace("{client_name}", client_name)
        else:
            c_code, c_src, c_desc = "", "", ""
        rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=c_code, bold=True, bg_color=bg, align="CENTER", font_size=8.0),
                    CellNode(text=c_src, bg_color=bg, align="LEFT", font_size=8.0),
                    CellNode(text=c_desc, bg_color=bg, align="LEFT", font_size=8.0),
                ]
            )
        )
    nodes.append(TableNode(rows=rows))
    nodes.append(SpacerNode(points=15))


def build_appendix_b_fair_methodology(
    ctx: dict[str, Any],
    nodes: List[Any],
    primary_color_rgb: Any,
    brand_data: dict[str, Any],
    alt_row_hex: str,
) -> None:
    """Builds Appendix B: Quantitative Risk Modeling Methodology (Open FAIR™ Standard)."""
    vocab = ctx["vocab"]
    meta_lang = ctx["meta_lang"]
    currency = ctx["currency"]
    blueprint_data = ctx["blueprint_data"]

    app_b_title = t("ast_appendix_fair_title", locale=meta_lang)
    nodes.append(
        HeadingNode(
            text=app_b_title,
            level=1,
            primary_color_rgb=primary_color_rgb,
            is_appendix=True,
        )
    )

    nodes.append(
        HeadingNode(
            text=t("appendix_fair_title", locale=meta_lang),
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(ParagraphNode(text=t("appendix_fair_intro", locale=meta_lang)))
    nodes.append(ParagraphNode(text=t("appendix_fair_fallacy", locale=meta_lang)))

    is_critical = brand_data.get("styling", {}).get("is_critical", None)
    if is_critical is None:
        is_critical = (
            blueprint_data.get("document_meta", {}).get(
                "enterprise_scale_critical", False
            )
            if isinstance(blueprint_data, dict)
            else False
        )

    nodes.append(SpacerNode(points=8))
    nodes.append(
        HeadingNode(
            text=t("tef_scale_title", locale=meta_lang),
            level=3,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(build_tef_scale_table(vocab, meta_lang, alt_row_hex))

    nodes.append(SpacerNode(points=10))
    nodes.append(
        HeadingNode(
            text=t("lm_scale_title", locale=meta_lang),
            level=3,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        build_lm_scale_table(
            vocab, meta_lang, currency, is_critical, alt_row_hex
        )
    )
    nodes.append(SpacerNode(points=15))


def build_appendix_c_glossary_and_disclaimer(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix C: Glossary of Terms and Legal Liability Disclaimer."""
    vocab = ctx["vocab"]
    case_dir = ctx["case_dir"]
    meta_lang = ctx["meta_lang"]

    app_c_title = t("ast_appendix_glossary_disclaimer_title", locale=meta_lang)
    nodes.append(
        HeadingNode(
            text=app_c_title,
            level=1,
            primary_color_rgb=primary_color_rgb,
            is_appendix=True,
        )
    )

    default_glossary_title = t("appendix_a_default_title", locale=meta_lang)
    nodes.append(
        HeadingNode(
            text=re.sub(_get_appendix_strip_regex(), "", default_glossary_title),
            level=2,
            primary_color_rgb=primary_color_rgb,
            is_appendix=True,
        )
    )
    default_intro = t("appendix_a_default_intro", locale=meta_lang)
    nodes.append(
        ParagraphNode(
            text=vocab.get("appendix_a_intro", default_intro)
        )
    )
    nodes.append(SpacerNode(points=6))

    from assessment_engine.infrastructure.config_loader import (
        load_abbreviations_glossary,
    )

    try:
        full_glossary = load_abbreviations_glossary()
        client_glossary_path = case_dir / "client_abbreviations_glossary.json"
        if client_glossary_path.exists():
            try:
                with open(client_glossary_path, "r", encoding="utf-8-sig") as cgf:
                    client_glossary = json.load(cgf)
                    for lang, terms in client_glossary.items():
                        if lang in full_glossary:
                            full_glossary[lang].update(terms)
                        else:
                            full_glossary[lang] = terms
            except (OSError, ValueError, KeyError, AttributeError) as ex:
                logger.debug("[Fallback] Handled exception: %s", ex)

        candidate_keys = [meta_lang, "en"]
        lang_key = next((k for k in candidate_keys if k in full_glossary), "en")
        glossary = full_glossary.get(lang_key, full_glossary.get("en", {}))

        default_headers = get_localized_list("appendix_a_headers", locale=meta_lang)
        headers = vocab.get("appendix_a_headers") or default_headers
        rows = [
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
        ]
        # Collect full textual corpus of the document to filter relevant glossary terms dynamically
        doc_corpus_parts = []
        for n in nodes:
            if hasattr(n, "text") and n.text:
                doc_corpus_parts.append(str(n.text))
        bp_data = ctx.get("blueprint_data") or {}
        doc_corpus = " ".join(doc_corpus_parts) + " " + json.dumps(bp_data)

        filtered_terms = {}
        for term, definition in glossary.items():
            if re.search(r"\b" + re.escape(term) + r"\b", doc_corpus):
                filtered_terms[term] = definition

        if not filtered_terms:
            filtered_terms = dict(list(glossary.items())[:10])

        for term, definition in sorted(filtered_terms.items()):
            rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=term, bold=True, align="CENTER"),
                        CellNode(text=definition),
                    ]
                )
            )
        nodes.append(TableNode(rows=rows, autofit=True, col_widths=[0.18, 0.82]))
    except Exception as ex:
        logger.warning(f"Error loading glossary: {ex}")

    # C.2 Legal Liability Disclaimer
    nodes.append(SpacerNode(points=14))
    default_disclaimer_title = t("appendix_b_default_title", locale=meta_lang)
    nodes.append(
        HeadingNode(
            text=re.sub(_get_appendix_strip_regex(), "", default_disclaimer_title),
            level=2,
            primary_color_rgb=primary_color_rgb,
            is_appendix=True,
        )
    )
    client_name = str(ctx.get("client_name") or ctx.get("client") or "CLIENT").upper()
    company_name = str(ctx.get("company_name") or ctx.get("company") or vocab.get("default_company_name") or "").strip()
    for i in range(1, 6):
        disc_text = vocab.get(f"disclaimer_text_{i}", "")
        if disc_text:
            interpolated = (
                disc_text.replace("{client_name}", client_name)
                .replace("{company_name}", company_name)
                .replace("{company}", company_name)
            )
            nodes.append(ParagraphNode(text=interpolated))
            nodes.append(SpacerNode(points=8))


# Backward compatibility aliases for legacy callers and tests
build_appendix_a_glossary = build_appendix_c_glossary_and_disclaimer
build_appendix_b_disclaimer = build_appendix_c_glossary_and_disclaimer
build_appendix_c_custody = build_appendix_a_custody

def build_appendix_d_methodology(
    ctx: dict[str, Any],
    nodes: List[Any],
    primary_color_rgb: Any,
    brand_data: dict[str, Any],
    alt_row_hex: str,
) -> None:
    """Builds Appendix D: Assessment Methodology (both CMMI Maturity and Open FAIR standards)."""
    build_cmmi_methodology_and_capabilities(
        ctx, nodes, primary_color_rgb, heading_key="maturity_methodology_title"
    )
    build_appendix_b_fair_methodology(ctx, nodes, primary_color_rgb, brand_data, alt_row_hex)
