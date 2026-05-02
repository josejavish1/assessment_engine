"""
Módulo repair_tower_payload_scores.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import logging
import re
import sys
from pathlib import Path

from assessment_engine.scripts.lib.text_utils import clean_text_for_word

logger = logging.getLogger(__name__)


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


def take_sentences(text, max_sentences=1, max_chars=240):
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


def shorten_to_complete_sentence(text, max_words):
    text = clean_text(text)
    if not text:
        return ""

    shortened = take_sentences(text, max_sentences=1, max_chars=max(max_words * 9, 140))
    if shortened and "..." not in shortened:
        return shortened

    return take_sentences(text, max_sentences=2, max_chars=max(max_words * 9, 200))


def infer_short_interpretation(score_value, fallback_summary=""):
    fallback_summary = clean_text(fallback_summary)
    if fallback_summary:
        return shorten_to_complete_sentence(fallback_summary, 26)
    value = safe_float(score_value)
    if value is None:
        return ""
    if value >= 4:
        return "Capacidad sólida, industrializada y sostenida de forma predecible."
    if value >= 3:
        return "Capacidad estandarizada, con base consistente y margen de optimización."
    if value >= 2:
        return (
            "Capacidad parcial, con evidencia limitada y necesidad de sistematización."
        )
    return "Capacidad incipiente o insuficientemente desarrollada."


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 2:
        raise SystemExit(
            "Uso: python -m scripts.tools.repair_tower_payload_scores <template_payload_json>"
        )

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    base = payload_path.parent

    payload = load_json(payload_path)
    scoring = load_json(base / "scoring_output.json")
    findings = load_json(base / "findings.json")
    approved_asis_path = base / "approved_asis.json"
    approved_asis = load_json(approved_asis_path) if approved_asis_path.exists() else {}

    # orden canónico desde el payload ya generado
    current_pillars = payload.get("pillar_score_profile", {}).get("pillars", [])
    pillar_order = []
    pillar_labels = {}

    for p in current_pillars:
        pid = clean_text(p.get("pillar_id"))
        plabel = clean_text(p.get("pillar_label"))
        if pid:
            pillar_order.append(pid)
            pillar_labels[pid] = plabel

    if not pillar_order:
        for p in scoring.get("pillar_scores", []):
            pid = clean_text(p.get("pillar_id"))
            plabel = clean_text(p.get("pillar_name"))
            if pid:
                pillar_order.append(pid)
                pillar_labels[pid] = plabel

    # scoring_output.json
    scoring_map = {}
    for p in scoring.get("pillar_scores", []):
        pid = clean_text(p.get("pillar_id"))
        if not pid:
            continue
        scoring_map[pid] = {
            "pillar_label": clean_text(p.get("pillar_name")),
            "score_exact": safe_float(p.get("score_exact")),
            "score_display": clean_text(p.get("score_display_1d")),
            "weight": clean_text(p.get("weight_pct")),
        }

    # findings.json
    findings_map = {}
    findings_lookup = {}
    for p in findings.get("pillar_findings", []):
        pid = clean_text(p.get("pillar_id"))
        if not pid:
            continue
        findings_map[pid] = {
            "pillar_label": clean_text(p.get("pillar_name")),
            "score_exact": safe_float(p.get("score_exact")),
            "score_display": clean_text(p.get("score_display_1d")),
            "band": clean_text(p.get("current_maturity_band")),
        }
        summary = ""
        gaps = p.get("gaps") or []
        strengths = p.get("strengths") or []
        if gaps:
            summary = (
                clean_text((gaps[0] or {}).get("statement", ""))
                if isinstance(gaps[0], dict)
                else clean_text(gaps[0])
            )
        elif strengths:
            summary = (
                clean_text((strengths[0] or {}).get("statement", ""))
                if isinstance(strengths[0], dict)
                else clean_text(strengths[0])
            )
        findings_lookup[pid] = summary

    # approved_asis.json
    asis_map = {}
    asis_pillars = (
        approved_asis.get("content", {})
        .get("maturity_summary", {})
        .get("pillar_scores", [])
    )
    for p in asis_pillars:
        pid = clean_text(p.get("pillar_id"))
        if not pid:
            continue
        asis_map[pid] = {
            "score_display": clean_text(p.get("score_display_1d")),
            "band": clean_text(p.get("maturity_band")),
        }

    repaired = []
    for pid in pillar_order:
        score_exact = None
        score_display = ""
        band = ""
        weight = ""
        label = pillar_labels.get(pid, "")

        if pid in scoring_map:
            label = label or scoring_map[pid]["pillar_label"]
            score_exact = scoring_map[pid]["score_exact"]
            score_display = scoring_map[pid]["score_display"]
            weight = scoring_map[pid]["weight"]

        if score_exact is None and pid in findings_map:
            score_exact = findings_map[pid]["score_exact"]

        if not score_display and pid in findings_map:
            score_display = findings_map[pid]["score_display"]

        if not score_display and pid in asis_map:
            score_display = asis_map[pid]["score_display"]

        if not score_display and score_exact is not None:
            score_display = format_score(score_exact)

        if pid in findings_map:
            band = findings_map[pid]["band"]

        if not band and pid in asis_map:
            band = asis_map[pid]["band"]

        if not band:
            band = derive_band_from_score(score_exact or score_display)

        repaired.append(
            {
                "pillar_id": pid,
                "pillar_label": label,
                "score_display": score_display,
                "maturity_band": band,
                "weight": weight,
                "executive_reading": infer_short_interpretation(
                    score_exact or score_display, findings_lookup.get(pid, "")
                ),
                "_score_numeric": safe_float(
                    score_exact if score_exact is not None else score_display
                ),
            }
        )

    numeric = [p for p in repaired if p["_score_numeric"] is not None]
    strongest = (
        max(numeric, key=lambda x: x["_score_numeric"])["pillar_label"]
        if numeric
        else ""
    )
    weakest = (
        min(numeric, key=lambda x: x["_score_numeric"])["pillar_label"]
        if numeric
        else ""
    )

    payload["pillar_score_profile"]["pillars"] = [
        {
            "pillar_id": p["pillar_id"],
            "pillar_label": p["pillar_label"],
            "score_display": p["score_display"],
            "maturity_band": p["maturity_band"],
            "weight_pct": p["weight"],
            "executive_reading": p["executive_reading"],
        }
        for p in repaired
    ]

    payload["pillar_score_profile"]["strongest_pillar"] = strongest
    payload["pillar_score_profile"]["weakest_pillars"] = weakest

    payload.setdefault("_build_metadata", {})
    payload["_build_metadata"]["pillar_scores_detected"] = sum(
        1 for p in repaired if p["score_display"]
    )
    payload["_build_metadata"]["pillar_score_source"] = (
        "scoring_output.pillar_scores + findings.pillar_findings"
    )

    # limpia diagnostics de strongest/weakest
    old = payload.get("_build_diagnostics", {}).get("missing_required_bindings", [])
    filtered = [
        x
        for x in old
        if x.get("placeholder") not in {"{{STRONGEST_PILLAR}}", "{{WEAKEST_PILLAR}}"}
    ]
    if not strongest:
        filtered.append(
            {
                "placeholder": "{{STRONGEST_PILLAR}}",
                "source": "pillar_score_profile.strongest_pillar",
            }
        )
    if not weakest:
        filtered.append(
            {
                "placeholder": "{{WEAKEST_PILLAR}}",
                "source": "pillar_score_profile.weakest_pillars",
            }
        )
    payload.setdefault("_build_diagnostics", {})
    payload["_build_diagnostics"]["missing_required_bindings"] = filtered

    payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info("Payload reparado en: %s", payload_path)
    logger.info(
        "pillar_scores_detected = %s",
        payload["_build_metadata"]["pillar_scores_detected"],
    )
    logger.info("strongest = %s", strongest)
    logger.info("weakest = %s", weakest)
    logger.info("pillars:")
    for p in repaired:
        logger.info(
            " - %s | %s | %s | %s",
            p["pillar_label"],
            p["score_display"],
            p["maturity_band"],
            p["weight"],
        )
    logger.info("missing_required_bindings = %d", len(filtered))


if __name__ == "__main__":
    main()
