from __future__ import annotations

import json
import logging
import re
from pathlib import Path
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
                "appendix_strip_regex", r"^Appendix\s+[A-Z]:\s*"
            )
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug("[Fallback] Handled exception: %s", ex)
    return r"^Appendix\s+[A-Z]:\s*"


def build_appendix_a_glossary(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix A: Glossary and List of Abbreviations."""
    vocab = ctx["vocab"]
    case_dir = ctx["case_dir"]
    meta_lang = ctx["meta_lang"]

    default_title = t("appendix_a_default_title", locale=meta_lang)
    app_a_title = re.sub(
        _get_appendix_strip_regex(),
        "",
        vocab.get("appendix_a_title", default_title),
    )
    nodes.append(
        HeadingNode(text=app_a_title, level=1, primary_color_rgb=primary_color_rgb)
    )
    default_intro = t("appendix_a_default_intro", locale=meta_lang)
    nodes.append(
        ParagraphNode(
            text=vocab.get(
                "appendix_a_intro",
                default_intro,
            )
        )
    )

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
                logger.debug(f"[Fallback] Handled exception: {ex}")

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
        for term, definition in sorted(glossary.items()):
            rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=term, bold=True, align="CENTER"),
                        CellNode(text=definition),
                    ]
                )
            )
        nodes.append(TableNode(rows=rows))
    except Exception as ex:
        logger.warning(f"Error loading glossary: {ex}")


def build_appendix_b_disclaimer(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix B: Regulatory & Liability Disclaimer."""
    vocab = ctx["vocab"]
    meta_lang = ctx.get("meta_lang", "en")
    default_title = t("appendix_b_default_title", locale=meta_lang)
    app_b_title = re.sub(
        _get_appendix_strip_regex(),
        "",
        vocab.get("appendix_b_title", default_title),
    )
    nodes.append(
        HeadingNode(text=app_b_title, level=1, primary_color_rgb=primary_color_rgb)
    )
    for i in range(1, 6):
        disc_text = vocab.get(f"disclaimer_text_{i}", "")
        if disc_text:
            nodes.append(ParagraphNode(text=disc_text))
            nodes.append(SpacerNode(points=8))


def build_appendix_c_custody(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix C: Chain of Custody & Document Provenance Registry."""
    vocab = ctx["vocab"]
    meta_lang = ctx.get("meta_lang", "en")
    default_title = t("appendix_c_default_title", locale=meta_lang)
    app_c_title = re.sub(
        _get_appendix_strip_regex(),
        "",
        vocab.get("appendix_c_title", default_title),
    )
    nodes.append(
        HeadingNode(text=app_c_title, level=1, primary_color_rgb=primary_color_rgb)
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


def build_appendix_d_methodology(
    ctx: dict[str, Any],
    nodes: List[Any],
    primary_color_rgb: Any,
    brand_data: dict[str, Any],
    alt_row_hex: str,
) -> None:
    """Builds Appendix D: Assessment Methodology (Maturity Models & Open FAIR Standards)."""
    vocab = ctx["vocab"]
    meta_lang = ctx["meta_lang"]
    currency = ctx["currency"]
    tower_id = ctx["tower_id"]
    blueprint_data = ctx["blueprint_data"]

    default_d_title = t("methodology_default_chapter_title", locale=meta_lang)
    app_d_title = re.sub(
        _get_appendix_strip_regex(),
        "",
        vocab.get(
            "methodology_chapter_title",
            default_d_title,
        ),
    )
    nodes.append(
        HeadingNode(text=app_d_title, level=1, primary_color_rgb=primary_color_rgb)
    )

    nodes.append(
        HeadingNode(
            text=t("maturity_methodology_title", locale=meta_lang),
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text=t("maturity_scale_intro", locale=meta_lang)
        )
    )
    levels = get_localized_list("maturity_scale_levels", locale=meta_lang)
    for lvl in levels:
        nodes.append(ParagraphNode(text=lvl, style="List Bullet"))

    nodes.append(SpacerNode(points=10))
    nodes.append(
        HeadingNode(
            text=t("evaluated_capabilities_title", locale=meta_lang),
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text=t("evaluated_capabilities_intro", locale=meta_lang)
        )
    )

    tower_def_file = (
        Path("engine_config/towers")
        / tower_id
        / f"tower_definition_{tower_id.lower()}.json"
    )
    if not tower_def_file.exists():
        tower_def_file = (
            Path("engine_config/towers")
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )

    t_def = {}
    if tower_def_file.exists():
        try:
            with open(tower_def_file, "r", encoding="utf-8-sig") as tdf:
                t_def = json.load(tdf)
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug(f"[Fallback] Handled exception: {ex}")

    pillars_list = t_def.get("pillars", []) if isinstance(t_def, dict) else []
    if not pillars_list:
        pillars_list = blueprint_data.get("pillars_analysis", [])

    from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
    resolver = get_taxonomy_resolver()

    for p_idx, p in enumerate(pillars_list):
        raw_pname = p.get("pillar_name", p.get("pilar_name", "Pillar"))
        p_name = resolver.resolve_pillar_by_any_reference(
            p.get("pillar_id") or p.get("pilar_id") or raw_pname,
            default=raw_pname,
            locale=meta_lang,
        )
        p_weight = int(p.get("weight_pct", p.get("weight", 20)))
        kpi_names = []
        for kpi in p.get("kpis", []):
            raw_kname = kpi.get("kpi_name", "KPI").strip()
            loc_kname = resolver.resolve_capability_name(raw_kname, default=raw_kname, locale=meta_lang)
            k_name = loc_kname
            if k_name and not k_name.isupper() and len(k_name) > 4:
                k_name = k_name[0].lower() + k_name[1:]
            kpi_names.append(k_name)

        and_str = t("connector_and", locale=meta_lang)
        if len(kpi_names) > 1:
            kpi_str = ", ".join(kpi_names[:-1]) + and_str + kpi_names[-1]
        elif kpi_names:
            kpi_str = kpi_names[0]
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
        nodes.append(ParagraphNode(text=p_bullet_text, style="List Bullet"))

    # D.2 Quantitative Risk Methodology (FAIR)
    nodes.append(SpacerNode(points=15))
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

    nodes.append(SpacerNode(points=10))
    nodes.append(
        HeadingNode(
            text=t("systemic_resilience_indicators_title", locale=meta_lang),
            level=3,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(ParagraphNode(text=t("systemic_resilience_intro", locale=meta_lang)))
    indicators = get_localized_list("systemic_resilience_indicators_list", locale=meta_lang)
    for ind in indicators:
        nodes.append(ParagraphNode(text=ind, style="List Bullet"))
