"""Implements the primary logic and utilities for the Assessment Engine pipeline, specifically for processing and reconciling tower payload scores."""

import json
import logging
import re
import sys
from pathlib import Path

from infrastructure.text_utils import clean_text_for_word

logger = logging.getLogger(__name__)


from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a UTF-8 encoded JSON file from a specified path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


from typing import Any


def clean_text(value: Any) -> Any:
    """Clean a value by passing it to `clean_text_for_word`."""
    return clean_text_for_word(value)


from typing import Any


def safe_float(value: Any) -> Any:
    r"""{'docstring': 'Attempt to convert a value to a float, handling various input types.\n\nThis function processes `None`, numeric (`int`, `float`), and string-like\ninputs. For string inputs, it removes percentage signs and replaces commas\nwith periods to normalize the format before attempting the conversion.\n\nArgs:\n    value (Any): The input value to be converted to a float.\n\nReturns:\n    Optional[float]: The converted floating-point number, or `None` if the\n        input is `None` or if the conversion fails.'}."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_text(value).replace("%", "").replace(",", ".")
    try:
        return float(text)
    except Exception:
        return None


from typing import Any


def format_score(value: Any) -> Any:
    """Format a value as a string rounded to one decimal place."""
    num = safe_float(value)
    if num is None:
        return ""
    return f"{round(num, 1):.1f}"


from typing import Any


def derive_band_from_score(score: Any) -> Any:
    """Maps a numerical score to a predefined descriptive band.

    The function converts the input score to a float and assigns it to one of
    five categorical bands based on its value.

    The score-to-band mapping is as follows:
        - score < 2: "Nivel 1 - Inicial"
        - 2 <= score < 3: "Nivel 2 - Básico"
        - 3 <= score < 4: "Nivel 3 - Estandarizado"
        - 4 <= score < 5: "Nivel 4 - Optimizado"
        - score >= 5: "Nivel 5 - Avanzado"

    Args:
        score (Any): The input score to classify. It is internally converted
            to a float for comparison.

    Returns:
        str: The descriptive band name corresponding to the score. Returns an
            empty string if the input cannot be converted to a float.
    """
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


from typing import Any


def truncate_words(text: Any, max_words: Any) -> Any:
    """Truncate a string to a specified maximum number of words.

    The input text is first normalized using an external `clean_text` function.
    If the resulting word count exceeds `max_words`, the string is truncated
    to that limit. Trailing punctuation is stripped from the final word before
    an ellipsis ("...") is appended.

    Args:
        text (str): The input string to process and potentially truncate.
        max_words (int): The maximum number of words to retain.

    Returns:
        str: The processed string, appended with "..." if the original word
            count exceeded `max_words`. Returns an empty string if the
            cleaned text is empty.

    Raises:
        TypeError: If `max_words` is not a type comparable to an integer.
    """
    text = clean_text(text)
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" ,;:.") + "..."


from typing import Any


def take_sentences(text: Any, max_sentences: Any = 1, max_chars: Any = 240) -> Any:
    """Extract a text snippet constrained by sentence and character counts.

    The function cleans the input text and splits it into sentences using '.', '!',
    or '?' as delimiters. It then constructs a snippet by sequentially appending
    sentences until either the `max_sentences` count is reached or the addition
    of another sentence would cause the total length to exceed `max_chars`.

    The `max_chars` limit is not enforced for the first sentence; a single
    sentence longer than this limit will be returned. If the sentence splitting
    and cleaning process yields no content, the function falls back to a hard
    character truncation of the original cleaned text. The returned string is
    guaranteed to end with a sentence-terminating punctuation mark, with a
    period ('.') appended if necessary.

    Args:
        text (str): The source text from which to extract the snippet.
        max_sentences (int): The maximum number of sentences to include.
        max_chars (int): The target maximum number of characters. This limit is
            not strictly enforced if the first sentence of the text exceeds it.

    Returns:
        str: The extracted snippet. Returns an empty string if the input `text` is
            or becomes empty after cleaning.

    Raises:
        TypeError: If `text` is not a string or if `max_sentences` or `max_chars`
            are not integers.
    """
    text = clean_text(text)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out: list[Any] = []
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


from typing import Any


def shorten_to_complete_sentence(text: Any, max_words: Any) -> Any:
    """Truncates a string to one or two complete sentences based on a word-count estimate.

    The function first preprocesses the input string. It then performs a two-pass
    extraction. The first pass attempts to retrieve a single, complete sentence
    within a character limit derived from `max_words` (specifically, `max(max_words * 9, 140)`).

    If the result from the first pass is truncated (as determined by the presence
    of an ellipsis), a second, more lenient pass is executed. This fallback
    extracts up to two complete sentences using a larger character limit of
    `max(max_words * 9, 200)` to better ensure a complete thought is captured.

    Args:
        text (str): The input string to be truncated.
        max_words (int): The approximate maximum word count used to calculate the
            character limit for truncation.

    Returns:
        str: The truncated string, consisting of one or two complete sentences.
            Returns an empty string if the input text is empty after cleaning.

    Raises:
        TypeError: If `max_words` is not a numeric type that supports
            multiplication.
    """
    text = clean_text(text)
    if not text:
        return ""

    shortened = take_sentences(text, max_sentences=1, max_chars=max(max_words * 9, 140))
    if shortened and "..." not in shortened:
        return shortened

    return take_sentences(text, max_sentences=2, max_chars=max(max_words * 9, 200))


from typing import Any


def infer_short_interpretation(score_value: Any, fallback_summary: Any = "") -> Any:
    r"""{'docstring': 'Derives a qualitative interpretation from a numerical score or fallback text.\n\nIf a non-empty `fallback_summary` is provided, it is prioritized, cleaned,\nand truncated to a complete sentence not exceeding a character limit.\nOtherwise, the numerical `score_value` is mapped to a predefined,\nSpanish-language qualitative descriptor based on a set of thresholds.\n\nArgs:\n    score_value (Any): The numerical score to interpret, such as an int,\n        float, or string representation of a number. This argument is used\n        only if `fallback_summary` is not provided or is an empty string.\n    fallback_summary (Any): Optional text that takes precedence over\n        `score_value` as the source for the interpretation. Expected to be\n        a string-like object.\n\nReturns:\n    str: The derived interpretation. This is either a truncated version of\n        the `fallback_summary`, a predefined Spanish phrase corresponding to\n        the `score_value`, or an empty string if `score_value` is not\n        convertible to a number and no `fallback_summary` is available.'}."""
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
    """Consolidates pillar data from multiple source files into a main payload JSON.

    This function reads a main payload JSON file and merges pillar-related data
    from `scoring_output.json`, `findings.json`, and optionally
    `approved_asis.json`, assuming they reside in the same directory. It
    establishes a canonical pillar order and then, for each pillar, selects
    the best available data for scores, maturity bands, and weights based on a
    defined source precedence.

    The function calculates the strongest and weakest pillars from the consolidated
    scores. Finally, it overwrites the original payload file with the enriched
    pillar profile, updated build metadata, and revised diagnostic information.

    Args:
        argv: A list of command-line arguments. Expects a single argument
            representing the path to the target payload JSON file. If `None`,
            `sys.argv` is used as the source for arguments.

    Raises:
        SystemExit: If the number of command-line arguments is not two (the
            script name and one path).
        FileNotFoundError: If the required payload, scoring, or findings JSON
            files are not found.
        json.JSONDecodeError: If any of the input files contain malformed JSON.
    """
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

    # Establishes a canonical ordering based on the previously generated payload to ensure deterministic processing and output consistency.
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

    #
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

    #
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

    #
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

    # Clears diagnostic data from 'strongest' and 'weakest' sections to reduce payload size and conform to the final output schema.
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
