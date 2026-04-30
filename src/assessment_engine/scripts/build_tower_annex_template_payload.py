"""
Módulo build_tower_annex_template_payload.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import re
import sys
from pathlib import Path

from assessment_engine.scripts.lib.text_utils import normalize_tower_name, clean_text_for_word
from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.scripts.lib.contract_utils import save_versioned_payload

ROOT = Path(__file__).resolve().parents[3]

PROFILE_SETTINGS = {
    "short": {
        "pillar_exec_words": 24,
        "summary": {
            "asis_sentences": 2,
            "asis_chars": 420,
            "risks_sentences": 2,
            "risks_chars": 360,
            "conclusion_sentences": 2,
            "conclusion_chars": 360,
            "strength_hint_sentences": 1,
            "strength_hint_chars": 220,
            "gap_sentences": 1,
            "gap_chars": 260,
        },
        "sections": {
            "asis_narrative_sentences": 3,
            "asis_narrative_chars": 650,
            "asis_strengths_limit": 5,
            "asis_gaps_limit": 6,
            "asis_impacts_limit": 4,
            "risks_intro_sentences": 2,
            "risks_intro_chars": 420,
            "risks_limit": 5,
            "risks_closing_sentences": 2,
            "risks_closing_chars": 320,
            "target_capabilities_limit": 6,
            "gap_rows_limit": 5,
            "todo_intro_sentences": 2,
            "todo_intro_chars": 420,
            "todo_limit": 8,
            "conclusion_final_sentences": 2,
            "conclusion_final_chars": 420,
            "conclusion_exec_sentences": 2,
            "conclusion_exec_chars": 360,
            "conclusion_focus_limit": 5,
            "conclusion_closing_sentences": 1,
            "conclusion_closing_chars": 260,
        },
    },
    "long": {
        "pillar_exec_words": 48,
        "summary": {
            "asis_sentences": 3,
            "asis_chars": 760,
            "risks_sentences": 3,
            "risks_chars": 620,
            "conclusion_sentences": 3,
            "conclusion_chars": 620,
            "strength_hint_sentences": 2,
            "strength_hint_chars": 420,
            "gap_sentences": 2,
            "gap_chars": 420,
        },
        "sections": {
            "asis_narrative_sentences": 6,
            "asis_narrative_chars": 1800,
            "asis_strengths_limit": 12,
            "asis_gaps_limit": 12,
            "asis_impacts_limit": 10,
            "risks_intro_sentences": 4,
            "risks_intro_chars": 900,
            "risks_limit": 12,
            "risks_closing_sentences": 4,
            "risks_closing_chars": 900,
            "target_capabilities_limit": 14,
            "gap_rows_limit": 12,
            "todo_intro_sentences": 4,
            "todo_intro_chars": 900,
            "todo_limit": 12,
            "conclusion_final_sentences": 4,
            "conclusion_final_chars": 900,
            "conclusion_exec_sentences": 4,
            "conclusion_exec_chars": 760,
            "conclusion_focus_limit": 10,
            "conclusion_closing_sentences": 2,
            "conclusion_closing_chars": 420,
        },
    },
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clean_text(value):
    return clean_text_for_word(value)


def safe_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_text(value).replace("%", "").replace(",", ".")
    try:
        return float(text)
    except Exception:
        return None


def format_score(value):
    num = safe_float(value)
    if num is None:
        return ""
    return f"{round(num, 1):.1f}"


def derive_band_from_score(score):
    value = safe_float(score)
    if value is None:
        return ""
    if value < 2:
        return "Nivel 1 - Inicial"
    if value < 3:
        return "Nivel 2 - Básico"
    if value < 4:
        return "Nivel 3 - Estandarizado"
    if value < 5:
        return "Nivel 4 - Optimizado"
    return "Nivel 5 - Avanzado"


def truncate_words(text, max_words):
    text = clean_text(text)
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" ,;:.") + "..."


def shorten_to_complete_sentence(text, max_words):
    text = clean_text(text)
    if not text:
        return ""

    shortened = take_sentences(text, max_sentences=1, max_chars=max(max_words * 9, 140))
    if shortened and "..." not in shortened:
        return shortened

    return take_sentences(text, max_sentences=2, max_chars=max(max_words * 9, 200))


def take_sentences(text, max_sentences=2, max_chars=420):
    text = clean_text(text)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for part in parts:
        part = clean_text(part)
        if not part:
            continue
        candidate = " ".join(out + [part]).strip()
        if len(candidate) > max_chars and out:
            break
        out.append(part)
        if len(out) >= max_sentences:
            break
    result = " ".join(out).strip()
    if not result:
        result = text[:max_chars].rstrip(" ,;:")
    if result and result[-1] not in ".!?":
        result += "."
    return result


def humanize_case_id(case_id):
    case_id = clean_text(case_id)
    if not case_id:
        return ""
    parts = re.split(r"[_\-\s]+", case_id)
    return " ".join(p.capitalize() for p in parts if p)


def priority_rank(value):
    text = clean_text(value).lower()
    if text in ["muy alta", "critical", "critica"]:
        return 0
    if text in ["alta", "high"]:
        return 1
    if text in ["media", "medium"]:
        return 2
    if text in ["baja", "low"]:
        return 3
    return 9


def dedupe_preserve_order(items):
    seen = set()
    out = []
    for item in items:
        key = clean_text(item)
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def join_clean(items, fallback=""):
    values = [clean_text(x) for x in items if clean_text(x)]
    return ", ".join(values) if values else fallback


def extract_statement(value):
    if isinstance(value, dict):
        return clean_text(value.get("statement", ""))
    if isinstance(value, list):
        if not value:
            return ""
        return extract_statement(value[0])
    return clean_text(value)


def first_non_empty(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def flatten_target_capabilities(
    tobe_section, max_items=6, include_operating_model=False
):
    out = []
    seen = set()

    for pillar in tobe_section.get("target_capabilities_by_pillar", []):
        for cap in pillar.get("target_capabilities", []):
            text = clean_text(cap)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
            if len(out) >= max_items:
                return out

    for principle in tobe_section.get("architecture_principles", []):
        text = clean_text(principle)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
        if len(out) >= max_items:
            return out

    if include_operating_model:
        for implication in tobe_section.get("operating_model_implications", []):
            text = clean_text(implication)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
            if len(out) >= max_items:
                return out

    return out[:max_items]


def build_pillar_map(scoring, findings, profile_name="short"):
    profile = PROFILE_SETTINGS.get(profile_name, PROFILE_SETTINGS["short"])
    findings_map = {}
    for item in findings.get("pillar_findings", []):
        pid = clean_text(item.get("pillar_id"))
        if not pid:
            continue
        findings_map[pid] = item

    pillars = []
    for item in scoring.get("pillar_scores", []):
        pid = clean_text(item.get("pillar_id"))
        pname = clean_text(item.get("pillar_name"))
        score_exact = safe_float(item.get("score_exact"))
        score_display = clean_text(item.get("score_display_1d")) or format_score(
            score_exact
        )
        weight_pct = clean_text(item.get("weight_pct"))
        f = findings_map.get(pid, {})

        strengths = [
            extract_statement(x) for x in f.get("strengths", []) if extract_statement(x)
        ]
        gaps = [extract_statement(x) for x in f.get("gaps", []) if extract_statement(x)]
        band = clean_text(f.get("current_maturity_band")) or derive_band_from_score(
            score_exact
        )

        exec_words = profile["pillar_exec_words"]
        if score_exact is not None and score_exact >= 3 and strengths:
            executive_reading = shorten_to_complete_sentence(strengths[0], exec_words)
        elif gaps:
            executive_reading = shorten_to_complete_sentence(gaps[0], exec_words)
        elif strengths:
            executive_reading = shorten_to_complete_sentence(strengths[0], exec_words)
        else:
            executive_reading = ""

        pillars.append(
            {
                "pillar_id": pid,
                "pillar_label": pname,
                "score_exact": score_exact,
                "score_display": score_display,
                "maturity_band": band,
                "weight_pct": weight_pct,
                "executive_reading": executive_reading,
                "strengths": strengths,
                "gaps": gaps,
            }
        )
    return pillars, findings_map


def build_executive_summary(annex, pillars, findings_map, profile_name="short"):
    profile = PROFILE_SETTINGS.get(profile_name, PROFILE_SETTINGS["short"])
    cfg = profile["summary"]
    sections = annex.get("sections", {})
    asis = sections.get("asis", {})
    risks = sections.get("risks", {})
    conclusion = sections.get("conclusion", {})

    global_score = clean_text(annex.get("summary", {}).get("score_display"))
    global_band = clean_text(annex.get("summary", {}).get("maturity_band"))
    target = clean_text(annex.get("summary", {}).get("target_maturity"))

    numeric = [p for p in pillars if p.get("score_exact") is not None]
    strongest = max(numeric, key=lambda x: x["score_exact"]) if numeric else None
    min_score = min(p["score_exact"] for p in numeric) if numeric else None
    weakest_list = (
        [p for p in numeric if abs(p["score_exact"] - min_score) < 0.11]
        if numeric
        else []
    )

    p1 = take_sentences(
        asis.get("executive_narrative", ""),
        max_sentences=cfg["asis_sentences"],
        max_chars=cfg["asis_chars"],
    )
    p2 = take_sentences(
        first_non_empty(
            risks.get("introduction", ""), risks.get("closing_summary", "")
        ),
        max_sentences=cfg["risks_sentences"],
        max_chars=cfg["risks_chars"],
    )
    p3 = take_sentences(
        first_non_empty(
            conclusion.get("executive_message", ""),
            conclusion.get("final_assessment", ""),
        ),
        max_sentences=cfg["conclusion_sentences"],
        max_chars=cfg["conclusion_chars"],
    )

    summary_body_parts = [x for x in [p1, p2, p3] if clean_text(x)]

    strength_hint = ""
    if strongest:
        f = findings_map.get(strongest["pillar_id"], {})
        strengths = [
            extract_statement(x) for x in f.get("strengths", []) if extract_statement(x)
        ]
        if strengths:
            strength_hint = take_sentences(
                strengths[0],
                max_sentences=cfg["strength_hint_sentences"],
                max_chars=cfg["strength_hint_chars"],
            )

    message_strength = ""
    if strongest:
        if strength_hint:
            message_strength = f"{strongest['pillar_label']} es el pilar con mejor desempeño y constituye la base más sólida actual. {strength_hint}"
        else:
            message_strength = f"{strongest['pillar_label']} es el pilar con mejor desempeño y constituye la base más sólida actual."

    first_gap = ""
    gaps = dedupe_preserve_order(asis.get("gaps", []))
    if not gaps:
        # Fallback to pillar gaps
        for p in pillars:
            gaps.extend(p.get("gaps", []))
        gaps = dedupe_preserve_order(gaps)

    if gaps:
        first_gap = gaps[0]

    message_gap = (
        take_sentences(
            first_gap,
            max_sentences=cfg["gap_sentences"],
            max_chars=cfg["gap_chars"],
        )
        if first_gap
        else ""
    )

    weakest_labels = [p["pillar_label"] for p in weakest_list]
    if len(weakest_labels) == 1:
        weakest_str = weakest_labels[0]
    elif len(weakest_labels) == 2:
        weakest_str = f"{weakest_labels[0]} y {weakest_labels[1]}"
    else:
        weakest_str = ", ".join(weakest_labels)

    if any("Disaster Recovery" in x for x in weakest_labels) or any(
        "Cyber Recovery" in x for x in weakest_labels
    ):
        message_bottleneck = "La principal limitación estructural está en la recuperación demostrada extremo a extremo: existe capacidad, pero no una validación sistemática, repetible y orquestada."
    else:
        message_bottleneck = (
            take_sentences(
                first_gap,
                max_sentences=cfg["gap_sentences"],
                max_chars=cfg["gap_chars"],
            )
            if first_gap
            else ""
        )

    headline = (
        f"Resumen ejecutivo de la torre {clean_text(annex.get('tower_name', ''))}"
        or "Resumen ejecutivo de la torre"
    )

    return {
        "global_score": global_score,
        "global_band": global_band,
        "target_maturity": target,
        "headline": headline,
        "summary_body": "\n\n".join(summary_body_parts),
        "message_strength": message_strength,
        "message_gap": message_gap,
        "message_bottleneck": message_bottleneck,
        "_strongest": strongest["pillar_label"] if strongest else "",
        "_weakest_labels": weakest_labels,
    }


def build_key_business_impacts(annex, profile_name="short"):
    profile = PROFILE_SETTINGS.get(profile_name, PROFILE_SETTINGS["short"])
    max_items = 3 if profile_name == "short" else 5

    candidates = []
    asis = (annex.get("sections") or {}).get("asis", {})
    risks = (annex.get("sections") or {}).get("risks", {})
    conclusion = (annex.get("sections") or {}).get("conclusion", {})

    candidates.extend(asis.get("operational_implications", []) or [])

    raw_risks = risks.get("risks") or risks.get("risk_items") or []
    for item in raw_risks:
        impact = clean_text(item.get("impact") or item.get("business_impact", ""))
        risk = clean_text(item.get("risk") or item.get("risk_name", ""))
        if impact and risk:
            candidates.append(f"{impact}: {risk}")
        elif risk:
            candidates.append(risk)

    candidates.extend(conclusion.get("priority_focus_areas", []) or [])

    impacts = []
    for item in dedupe_preserve_order(candidates):
        condensed = take_sentences(
            item,
            max_sentences=1,
            max_chars=profile["summary"]["gap_chars"],
        )
        if condensed:
            impacts.append(condensed)
        if len(impacts) >= max_items:
            break
    return impacts


def build_pillar_score_profile(scoring, findings, pillars, exec_summary):
    weights = []
    for p in pillars:
        if p["weight_pct"]:
            weights.append(f"{p['pillar_label']} {p['weight_pct']}%")
    method_note = (
        "Escala 0–5. El score de cada pilar se calcula como agregación ponderada de sus KPIs. "
        f"El score global de la torre se obtiene por agregación ponderada de pilares: {'; '.join(weights)}."
    )

    weakest_labels = exec_summary["_weakest_labels"]
    if len(weakest_labels) == 1:
        weakest_str = weakest_labels[0]
    elif len(weakest_labels) == 2:
        weakest_str = f"{weakest_labels[0]} y {weakest_labels[1]}"
    else:
        weakest_str = ", ".join(weakest_labels)

    strongest = exec_summary["_strongest"]

    if any("Disaster Recovery" in x for x in weakest_labels) or any(
        "Cyber Recovery" in x for x in weakest_labels
    ):
        profile_intro = (
            f"La torre presenta su mejor comportamiento relativo en {strongest}, pero concentra su mayor debilidad en "
            f"{weakest_str}, lo que confirma que la brecha principal no está en la existencia de capacidades, sino en su demostración operativa."
        )
        structural_reading = "La debilidad estructural de la torre no está en la copia del dato, sino en la recuperación demostrada, orquestada y validada de extremo a extremo."
    else:
        profile_intro = f"La torre muestra un desempeño comparativamente más sólido en {strongest}, pero mantiene rezagos relevantes en {weakest_str}."
        structural_reading = "La principal brecha estructural se concentra en los bloques de menor madurez y limita la fiabilidad operativa del conjunto."

    return {
        "profile_intro": profile_intro,
        "scoring_method_note": method_note,
        "radar_chart": "",
        "strongest_pillar": strongest,
        "weakest_pillars": weakest_str,
        "structural_reading": structural_reading,
        "pillars": [
            {
                "pillar_id": p["pillar_id"],
                "pillar_label": p["pillar_label"],
                "score_display": p["score_display"],
                "maturity_band": p["maturity_band"],
                "executive_reading": p["executive_reading"],
                "weight_pct": p["weight_pct"],
            }
            for p in pillars
        ],
    }


def build_sections(annex, pillars_data, profile_name="short"):
    profile = PROFILE_SETTINGS.get(profile_name, PROFILE_SETTINGS["short"])
    cfg = profile["sections"]
    sections = annex.get("sections", {})
    asis = sections.get("asis", {})
    risks = sections.get("risks", {})
    tobe = sections.get("tobe", {})
    gap = sections.get("gap", {})
    todo = sections.get("todo", {})
    conclusion = sections.get("conclusion", {})

    todo_items = sorted(
        todo.get("todo_items", []),
        key=lambda x: (
            priority_rank(x.get("priority", "")),
            len(x.get("dependencies", []) or []),
            clean_text(x.get("initiative", "")),
        ),
    )[: cfg["todo_limit"]]

    normalized_initiatives = []
    for idx, item in enumerate(todo_items, start=1):
        normalized_initiatives.append(
            {
                "sequence": idx,
                "initiative": clean_text(item.get("initiative", "")),
                "objective": clean_text(item.get("objective", "")),
                "priority": clean_text(item.get("priority", "")),
                "expected_outcome": clean_text(item.get("expected_outcome", "")),
                "dependencies_display": ", ".join(
                    [
                        clean_text(x)
                        for x in item.get("dependencies", [])
                        if clean_text(x)
                    ]
                )
                or "Sin dependencias explícitas",
            }
        )

    # Risk mapping with fallback to risk_items
    raw_risks = risks.get("risks")
    if not raw_risks:
        raw_risks = risks.get("risk_items", [])
    
    risk_rows = []
    for item in raw_risks[: cfg["risks_limit"]]:
        risk_text = clean_text(item.get("risk") or item.get("risk_name", ""))
        impact_text = clean_text(item.get("impact") or item.get("business_impact", ""))
        mitigation_text = clean_text(item.get("mitigation_summary") or item.get("technical_root_cause", ""))
        
        risk_rows.append(
            {
                "risk": risk_text,
                "impact": impact_text,
                "probability": clean_text(item.get("probability", "") or item.get("severity", "")),
                "mitigation_summary": mitigation_text,
            }
        )

    gap_rows = []
    for item in gap.get("gap_items", [])[: cfg["gap_rows_limit"]]:
        key_gap = clean_text(item.get("key_gap", ""))
        if profile_name == "long":
            operational_implication = clean_text(
                item.get("operational_implication", "")
            )
            if operational_implication:
                key_gap = f"{key_gap} Implicación operativa: {operational_implication}"
        gap_rows.append(
            {
                "pillar": clean_text(item.get("pillar", "")),
                "as_is_summary": clean_text(item.get("as_is_summary", "")),
                "target_state": clean_text(item.get("target_state", "")),
                "key_gap": key_gap,
            }
        )

    # AS-IS collection with fallbacks
    strengths = dedupe_preserve_order(asis.get("strengths", []))
    if not strengths:
        for p in pillars_data:
            strengths.extend(p.get("strengths", []))
    strengths = dedupe_preserve_order(strengths)[: cfg["asis_strengths_limit"]]

    gaps = dedupe_preserve_order(asis.get("gaps", []))
    if not gaps:
        for p in pillars_data:
            gaps.extend(p.get("gaps", []))
    gaps = dedupe_preserve_order(gaps)[: cfg["asis_gaps_limit"]]

    impacts = dedupe_preserve_order(asis.get("operational_implications", []))
    if not impacts:
        # Fallback to per-pillar operational_impact in refined JSON
        for p in asis.get("pillars", []):
            impacts.append(p.get("operational_impact", ""))
    impacts = dedupe_preserve_order(impacts)[: cfg["asis_impacts_limit"]]

    return {
        "asis": {
            "narrative": take_sentences(
                asis.get("executive_narrative", ""),
                max_sentences=cfg["asis_narrative_sentences"],
                max_chars=cfg["asis_narrative_chars"],
            ),
            "strengths": strengths,
            "gaps": gaps,
            "operational_impacts": impacts,
        },
        "risks": {
            "introduction": take_sentences(
                risks.get("introduction", ""),
                max_sentences=cfg["risks_intro_sentences"],
                max_chars=cfg["risks_intro_chars"],
            ),
            "risks": risk_rows,
            "closing_summary": take_sentences(
                risks.get("closing_summary", ""),
                max_sentences=cfg["risks_closing_sentences"],
                max_chars=cfg["risks_closing_chars"],
            ),
        },
        "gap": {
            "introduction": take_sentences(
                tobe.get("introduction", ""),
                max_sentences=cfg["risks_intro_sentences"],
                max_chars=cfg["risks_intro_chars"],
            ),
            "target_capabilities": flatten_target_capabilities(
                tobe,
                max_items=cfg["target_capabilities_limit"],
                include_operating_model=(profile_name == "long"),
            ),
            "gap_rows": gap_rows,
            "closing_summary": "",
        },
        "tobe": {
            "vision": take_sentences(
                tobe.get("vision", ""),
                max_sentences=2,
            ),
            "design_principles": dedupe_preserve_order(tobe.get("architecture_principles", [])),
        },
        "todo": {
            "introduction": take_sentences(
                todo.get("introduction", ""),
                max_sentences=cfg["todo_intro_sentences"],
                max_chars=cfg["todo_intro_chars"],
            ),
            "priority_initiatives": normalized_initiatives,
            "closing_summary": "",
        },
        "conclusion": {
            "final_assessment": take_sentences(
                conclusion.get("final_assessment", ""),
                max_sentences=cfg["conclusion_final_sentences"],
                max_chars=cfg["conclusion_final_chars"],
            ),
            "executive_message": take_sentences(
                conclusion.get("executive_message", ""),
                max_sentences=cfg["conclusion_exec_sentences"],
                max_chars=cfg["conclusion_exec_chars"],
            ),
            "priority_focus_areas": dedupe_preserve_order(
                conclusion.get("priority_focus_areas", [])
            )[: cfg["conclusion_focus_limit"]],
            "closing_statement": take_sentences(
                conclusion.get("closing_statement", ""),
                max_sentences=cfg["conclusion_closing_sentences"],
                max_chars=cfg["conclusion_closing_chars"],
            ),
        },
    }


def build_extended_sections(annex):
    sections = annex.get("sections", {})
    asis = sections.get("asis", {})
    risks = sections.get("risks", {})
    tobe = sections.get("tobe", {})
    gap = sections.get("gap", {})
    todo = sections.get("todo", {})
    conclusion = sections.get("conclusion", {})

    maturity_summary = asis.get("maturity_summary", {}) or {}
    
    # Risks with fallback to risk_items
    raw_risks = risks.get("risks")
    if not raw_risks:
        raw_risks = risks.get("risk_items", [])

    detailed_risks = []
    for item in raw_risks:
        detailed_risks.append(
            {
                "risk": clean_text(item.get("risk") or item.get("risk_name", "")),
                "cause": clean_text(item.get("cause") or item.get("technical_root_cause", "")),
                "impact": clean_text(item.get("impact") or item.get("business_impact", "")),
                "probability": clean_text(item.get("probability") or item.get("severity", "")),
                "mitigation_summary": clean_text(item.get("mitigation_summary", "")),
                "affected_pillars_display": join_clean(
                    item.get("affected_pillars", []) or item.get("related_pillars", []), "Sin pilares explícitos"
                ),
            }
        )

    target_capabilities_by_pillar = []
    for pillar in tobe.get("target_capabilities_by_pillar", []):
        target_capabilities_by_pillar.append(
            {
                "pillar": clean_text(pillar.get("pillar", "")),
                "target_capabilities": dedupe_preserve_order(
                    pillar.get("target_capabilities", [])
                ),
            }
        )

    detailed_gaps = []
    for item in gap.get("gap_items", []):
        detailed_gaps.append(
            {
                "pillar": clean_text(item.get("pillar", "")),
                "as_is_summary": clean_text(item.get("as_is_summary", "")),
                "target_state": clean_text(item.get("target_state", "")),
                "key_gap": clean_text(item.get("key_gap", "")),
                "operational_implication": clean_text(
                    item.get("operational_implication", "")
                ),
            }
        )

    detailed_todo = []
    todo_items = sorted(
        todo.get("todo_items", []),
        key=lambda x: (
            priority_rank(x.get("priority", "")),
            len(x.get("dependencies", []) or []),
            clean_text(x.get("initiative", "")),
        ),
    )
    for idx, item in enumerate(todo_items, start=1):
        detailed_todo.append(
            {
                "sequence": idx,
                "initiative": clean_text(item.get("initiative", "")),
                "objective": clean_text(item.get("objective", "")),
                "priority": clean_text(item.get("priority", "")),
                "related_pillars_display": join_clean(
                    item.get("related_pillars", []), "Sin pilares explícitos"
                ),
                "expected_outcome": clean_text(item.get("expected_outcome", "")),
                "dependencies_display": join_clean(
                    item.get("dependencies", []), "Sin dependencias explícitas"
                ),
            }
        )

    return {
        "asis": {
            "executive_narrative": clean_text(asis.get("executive_narrative", "")),
            "current_maturity_band": clean_text(
                first_non_empty(
                    maturity_summary.get("current_maturity_band"),
                    maturity_summary.get("maturity_band"),
                )
            ),
            "current_score_reference": clean_text(
                first_non_empty(
                    maturity_summary.get("current_score_reference"),
                    maturity_summary.get("current_score"),
                )
            ),
            "strengths": dedupe_preserve_order(asis.get("strengths", [])),
            "gaps": dedupe_preserve_order(asis.get("gaps", [])),
            "operational_impacts": dedupe_preserve_order(
                asis.get("operational_implications", [])
            ),
        },
        "risks": {
            "introduction": clean_text(risks.get("introduction", "")),
            "risk_details": detailed_risks,
            "closing_summary": clean_text(risks.get("closing_summary", "")),
        },
        "tobe": {
            "introduction": clean_text(tobe.get("introduction", "")),
            "target_maturity_level": clean_text(
                (tobe.get("target_maturity", {}) or {}).get("recommended_level", "")
            ),
            "target_score_reference": clean_text(
                (tobe.get("target_maturity", {}) or {}).get(
                    "recommended_score_reference", ""
                )
            ),
            "target_maturity_justification": clean_text(
                (tobe.get("target_maturity", {}) or {}).get("justification", "")
            ),
            "target_capabilities_by_pillar": target_capabilities_by_pillar,
            "architecture_principles": dedupe_preserve_order(
                tobe.get("architecture_principles", [])
            ),
            "operating_model_implications": dedupe_preserve_order(
                tobe.get("operating_model_implications", [])
            ),
        },
        "gap": {
            "introduction": clean_text(gap.get("introduction", "")),
            "cross_cutting_gap_summary": dedupe_preserve_order(
                gap.get("cross_cutting_gap_summary", [])
            ),
            "gap_items": detailed_gaps,
        },
        "todo": {
            "introduction": clean_text(todo.get("introduction", "")),
            "todo_items": detailed_todo,
            "closing_summary": clean_text(todo.get("closing_summary", "")),
        },
        "conclusion": {
            "final_assessment": clean_text(conclusion.get("final_assessment", "")),
            "executive_message": clean_text(conclusion.get("executive_message", "")),
            "priority_focus_areas": dedupe_preserve_order(
                conclusion.get("priority_focus_areas", [])
            ),
            "closing_statement": clean_text(conclusion.get("closing_statement", "")),
        },
    }


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) not in (2, 3, 4, 5):
        raise SystemExit(
            "Uso: python -m scripts.build_tower_annex_template_payload <approved_annex_refined_json> [output_json] [client_name] [short|long]"
        )

    input_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    output_path = (
        Path((argv if argv is not None else sys.argv)[2]).resolve()
        if len(argv if argv is not None else sys.argv) >= 3
        else input_path.with_name("approved_annex_t5.template_payload.json")
    )
    explicit_client_name = clean_text((argv if argv is not None else sys.argv)[3]) if len(argv if argv is not None else sys.argv) >= 4 else ""
    profile_name = clean_text((argv if argv is not None else sys.argv)[4]).lower() if len(argv if argv is not None else sys.argv) == 5 else "short"
    if profile_name not in PROFILE_SETTINGS:
        raise SystemExit(f"Perfil no soportado: {profile_name}")

    annex = load_json(input_path)
    base = input_path.parent
    scoring = load_json(base / "scoring_output.json")
    findings = load_json(base / "findings.json")

    client_name = explicit_client_name or humanize_case_id(annex.get("case_id", ""))

    pillars, findings_map = build_pillar_map(
        scoring, findings, profile_name=profile_name
    )
    exec_summary = build_executive_summary(
        annex, pillars, findings_map, profile_name=profile_name
    )
    key_business_impacts = build_key_business_impacts(
        annex, profile_name=profile_name
    )
    profile = build_pillar_score_profile(scoring, findings, pillars, exec_summary)
    sections = build_sections(annex, pillars, profile_name=profile_name)

    payload_dict = {
        "_generation_metadata": {
            "artifact_type": "annex_template_payload",
            "artifact_version": "1.0.0",
        },
        "document_meta": {
            "tower_code": clean_text(annex.get("tower_id", "")),
            "tower_name": normalize_tower_name(annex.get("tower_name", "")),
            "client_name": client_name,
            "report_variant": profile_name,
        },
        "executive_summary": {
            "global_score": exec_summary["global_score"],
            "global_band": exec_summary["global_band"],
            "target_maturity": exec_summary["target_maturity"],
            "headline": exec_summary["headline"],
            "summary_body": exec_summary["summary_body"],
            "message_strength": exec_summary["message_strength"],
            "message_gap": exec_summary["message_gap"],
            "message_bottleneck": exec_summary["message_bottleneck"],
            "key_business_impacts": key_business_impacts,
        },
        "domain_introduction": {
            "introduction_paragraph": f"Este anexo presenta los resultados del assessment para la torre {normalize_tower_name(annex.get('tower_name', ''))}.",
            "technological_domain": normalize_tower_name(annex.get('tower_name', '')),
            "domain_objective": "Optimización y transformación tecnológica.",
            "evaluated_capabilities": [],
            "included_components": []
        },
        "pillar_score_profile": profile,
        "sections": sections,
    }

    try:
        # Validar y normalizar mediante Pydantic (Hito B4)
        payload = AnnexPayload.model_validate(payload_dict)
        save_versioned_payload(output_path, payload, "annex_template_payload")
    except Exception as e:
        print(f"⚠️ Fallo de contrato B4 (Best effort): {e}")
        output_path.write_text(
            json.dumps(payload_dict, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    
    print("Template payload generado en:", output_path)
    print("Pillars:", len(profile["pillars"]))
    print("Initiatives:", len(sections["todo"]["priority_initiatives"]))


if __name__ == "__main__":
    main()
