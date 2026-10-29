"""Centralized text-processing utilities for sanitization and normalization.

This module provides a suite of functions designed to prepare text for rendering
in environments with strict character constraints, such as XML and OpenXML (Word) documents.
"""

import html
import re
import unicodedata
from typing import Any


def deep_unescape(obj: Any) -> Any:
    """Recursively unescapes HTML entities within a nested data structure.

    This function traverses a structure of lists and dictionaries. For each
    string value encountered, it applies `html.unescape` to convert named and
    numeric character references (e.g., &gt;, &#62;, &#x3e;) to their
    corresponding Unicode characters. All other data types are preserved as-is.

    The original object is not mutated; a new data structure is returned.

    Example:
        data = {
            "title": "A &amp; B &gt; C",
            "items": ["item one", "item &#8482;"],
            "id": 123
        }
        unescaped_data = deep_unescape(data)
        # unescaped_data is:
        # {
        #     "title": "A & B > C",
        #     "items": ["item one", "item ™"],
        #     "id": 123
        # }

    Args:
        obj (Any): The data structure to process, which may contain nested
            dictionaries, lists, and strings.

    Returns:
        Any: A new data structure with the same shape as the input, but with all
            string values HTML-unescaped.
    """
    if isinstance(obj, dict):
        return {k: deep_unescape(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_unescape(item) for item in obj]
    elif isinstance(obj, str):
        return html.unescape(obj)
    return obj


def normalize_spaces(value: str) -> str:
    """Collapse whitespace sequences to single spaces and strip leading/trailing whitespace."""
    text = str(value or "").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def clean_text_for_word(value: str) -> str:
    """Sanitizes a string for safe inclusion in XML and OpenXML documents.

    This function prepares text for safe embedding within an OpenXML document (e.g.,
    a .docx file) by removing characters and formatting artifacts that can cause
    parsing errors. The process first coerces the input value to a string. It
    then removes illegal XML 1.0 control characters (Unicode code points
    U+0000-U+001F), preserving only tab, newline, and carriage return. Finally,
    it strips common Markdown syntax, such as bold markers (`**`), and trims
    any leading or trailing whitespace from the result.

    Args:
        value: The input data to sanitize. Non-string inputs are converted to
            their string representation.

    Returns:
        A sanitized string compatible with OpenXML. An empty string is returned
        if the input value is falsy.
    """
    if not value:
        return ""

    # Retain only printable characters, tabs, and line breaks to ensure XML compatibility.
    # The OpenXML standard (ECMA-376) disallows most C0 control characters (< U+0020) except for tab, newline, and carriage return.
    text = "".join(ch for ch in str(value) if ch in "\n\t\r" or ord(ch) >= 32)

    # Strip common Markdown artifacts to produce clean text for OpenXML rendering.
    # The current implementation only strips Markdown bold syntax, as it is the most common artifact.
    text = text.replace("**", "")

    return text.strip()


def normalize_tower_name(value: str) -> str:
    """Normalize a string by removing trailing prompt-generated verbs."""
    text = normalize_spaces(value)
    if not text:
        return ""
    norm = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    m = re.search(
        r"\s+(?:evalua|cubre|mide|analiza|describe|responde)\b.*$",
        norm,
        flags=re.IGNORECASE,
    )
    if m:
        text = text[:m.start()]
    return text.strip(" ,;:-")


def slugify(value: str) -> str:
    r"""{'docstring': 'Generate a filesystem-safe, ASCII-only slug from a string.\n\nThe function transforms the input string by applying the following sequential\noperations:\n1.  Unicode normalization is performed using the NFKD compatibility form.\n2.  The normalized string is encoded to ASCII, discarding any characters that\n    cannot be represented.\n3.  All sequences of non-alphanumeric characters are collapsed into a single\n    underscore.\n4.  Any leading or trailing underscores are removed.\n5.  The resulting string is converted to lowercase.\n\nFor example, the input "  Ein schönes Mädchen!  " is converted to\n"ein_schones_madchen".\n\nIf the string is empty after these transformations, or if the input is `None`,\nthis function returns a default value of "generic".\n\nArgs:\n    value (str): The string to be converted into a slug.\n\nReturns:\n    str: The generated slug. Contains only lowercase ASCII letters, digits,\n        and underscores, with no leading or trailing underscores.'}."""
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return cleaned or "generic"


def format_currency_custom(
    val: float, vocab: dict[str, Any], doc_lang: str
) -> str:
    """Formats a numeric value into a locale-aware currency string.

    This function provides OS-agnostic currency formatting by performing direct
    string and mathematical manipulation, avoiding reliance on system locale
    settings. It uses a vocabulary dictionary to control the currency symbol and
    the style of decimal/thousands separators, while the language code governs
    the symbol's placement.

    Special handling is implemented for specific locales. For example, values
    formatted for Japanese Yen ('ja') are rounded to the nearest integer, as
    minor currency units are not typically used.

    Args:
        val: The numeric monetary value to be formatted.
        vocab: A dictionary defining currency properties. Expected keys are:
            'currency_symbol' (str): The symbol to use (e.g., '$', '€').
                Defaults to '€'.
            'currency_format' (str): The number format style, either 'US'
                (e.g., 1,234.56) or 'EU' (e.g., 1.234,56). Defaults to 'EU'.
        doc_lang: An ISO 639-1 language code that dictates symbol placement
            and can override number formatting. For example, 'en' places the
            symbol before the number, while 'es' places it after. Defaults
            to 'en'.

    Returns:
        A string representing the formatted monetary value.
    """
    symbol = vocab.get("currency_symbol", "€")
    code = str(doc_lang or "en").lower().split("_")[0].split("-")[0]
    format_type = vocab.get("currency_format")

    if code == "ja":
        # The Japanese Yen (JPY) does not use minor currency units in general circulation.
        formatted_num = f"{int(round(val)):,}"
        return f"{formatted_num}{symbol}"

    is_us_style = (format_type == "US") or (format_type != "EU" and code == "en")
    if is_us_style:
        formatted_num = f"{val:,.2f}"
        return f"{symbol}{formatted_num}"

    # European / continental style (dot thousands, comma decimal, suffix symbol)
    formatted_num = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted_num} {symbol}"


def detect_prompt_injection(text: str) -> bool:
    """Scan input text for adversarial prompt injection payloads.

    This acts as a deterministic pre-flight security guardrail before passing
    any untrusted natural language user request to generative models in Vertex AI.

    Returns:
        True if an injection attempt is detected, False otherwise.
    """
    import re

    if not text:
        return False
    patterns = [
        r"ignore\s+previous\s+instructions",
        r"system\s+override",
        r"set\s+is_verified\s+to",
        r"set\s+system\s+score\s+to",
        r"ignore\s+all\s+constraints",
    ]
    text_lower = text.lower()
    return any(re.search(pat, text_lower) for pat in patterns)


def format_date_spanish(date_val: str = None, locale: str = "en") -> str:
    """Formats a date string or ISO date into localized 'Month Year'.

    Maintained for backward-compatibility, delegating directly to format_date_localized.
    """
    from assessment_engine.infrastructure.localization import (
        format_date_localized,
    )

    return format_date_localized(date_val, locale=locale)


class ExecutiveStyleCompressor:
    """Enforces Minto Pyramid / BLUF executive readability on C-level texts.

    1. Prunes bureaucratic throat-clearing openers ('As of today...', 'In quantitative terms...', etc.).
    2. Splits run-on sentences into atomic subject-verb-predicate thoughts (target <= 25 words).
    3. Ensures high information density and direct active voice.
    """

    @classmethod
    def _load_editorial_linter(cls) -> tuple[list[str], dict[str, str]]:
        from assessment_engine.infrastructure.runtime_paths import ROOT
        import json
        p = ROOT / "engine_config/locales_asis_annex.json"
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8")).get("executive_editorial_linter", {})
                return data.get("bureaucratic_openers", []), data.get("buzzword_replacements", {})
            except Exception:
                pass
        return [], {}

    BUREAUCRATIC_OPENERS: list[str] = []
    BUZZWORD_REPLACEMENTS: dict[str, str] = {}

    @classmethod
    def compress_executive_paragraph(cls, text: str, max_words_per_sentence: int = 25) -> str:
        """Cleans bureaucratic fluff, kills consulting buzzwords, and ensures sentences do not exceed max_words_per_sentence."""
        if not text:
            return ""

        if not cls.BUREAUCRATIC_OPENERS:
            cls.BUREAUCRATIC_OPENERS, cls.BUZZWORD_REPLACEMENTS = cls._load_editorial_linter()

        cleaned = text.strip()
        for pat in cls.BUREAUCRATIC_OPENERS:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

        for pat, repl in cls.BUZZWORD_REPLACEMENTS.items():
            cleaned = re.sub(pat, repl, cleaned, flags=re.IGNORECASE)

        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]

        raw_sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", cleaned) if s.strip()
        ]
        compressed_sentences: list[str] = []

        for s in raw_sentences:
            has_period = s.endswith(".")
            core = s[:-1].strip() if has_period else s.strip()
            words = core.split()

            if len(words) <= max_words_per_sentence:
                compressed_sentences.append(core + ".")
                continue

            # Split long run-on sentences on logical clause boundaries
            from assessment_engine.infrastructure.runtime_paths import ROOT
            import json
            split_rules = []
            p_split = ROOT / "engine_config/locales_asis_annex.json"
            if p_split.exists():
                try:
                    split_rules = json.loads(p_split.read_text(encoding="utf-8")).get("sentence_clause_split_rules", [])
                except Exception:
                    pass

            broken = False
            for r_item in split_rules:
                sp = r_item.get("pattern", "")
                parts = re.split(sp, core, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2 and len(parts[0].split()) >= 6:
                    p1 = parts[0].strip()
                    p2 = parts[1].strip()
                    prefix = r_item.get("prefix", "")
                    if p2:
                        p2 = prefix + p2[0].lower() + p2[1:]
                    compressed_sentences.append(p1 + ".")
                    compressed_sentences.append(p2 + ".")
                    broken = True
                    break

            if not broken:
                compressed_sentences.append(core + ".")

        result = " ".join(compressed_sentences)
        # Re-glue split numbers like '2. 40' -> '2.40' and '1. 773. 836' -> '1.773.836'
        result = re.sub(r"(\d+)\.\s+(\d+)", r"\1.\2", result)
        result = re.sub(r"(\d+)\.\s+(\d+)", r"\1.\2", result)
        result = re.sub(r"\.([^\W\d_])", r". \1", result)
        return result


def _load_canonical_tower_names() -> dict[str, tuple[str, str]]:
    defaults = {
        "T1": ("01", "Data_Center"),
        "T2": ("02", "Hybrid_Compute"),
        "T3": ("03", "Networks"),
        "T4": ("04", "Data_Storage"),
        "T5": ("05", "Resilience"),
        "T6": ("06", "Security_Identity"),
        "T7": ("07", "Operations_ITSM"),
        "T8": ("08", "FinOps_Governance"),
        "T9": ("09", "Digital_Workplace"),
        "T10": ("10", "Mainframe_Core"),
    }
    from assessment_engine.infrastructure.runtime_paths import ROOT
    import json

    p = ROOT / "engine_config/locales_asis_annex.json"
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8")).get(
                "canonical_tower_names", {}
            )
            if raw:
                return {k: tuple(v) for k, v in raw.items()}
        except Exception:
            pass
    return defaults


CANONICAL_TOWER_NAMES: dict[str, tuple[str, str]] = _load_canonical_tower_names()


def get_canonical_tower_filenames(
    tower_id: str,
    client_name: str | None = None,
    date_str: str | None = None,
    locale: str | None = None,
) -> tuple[str, str]:
    """Returns concise, executive (AS-IS, TO-BE) filenames with underscores in the document's target language."""
    import os
    from datetime import datetime

    from assessment_engine.infrastructure.localization import t

    doc_lang = (locale or os.environ.get("ASSESSMENT_DOC_LANG") or "en").lower()
    prefix = t("file_prefix_annex", locale=doc_lang)

    num, name = CANONICAL_TOWER_NAMES.get(
        tower_id, (tower_id.replace("T", "").zfill(2), tower_id)
    )

    if client_name:
        c_part = client_name.strip().replace(" ", "_")
        d_part = date_str or datetime.now().strftime("%Y%m")
        return (
            f"{c_part}_{d_part}_{prefix}_{num}_{name}_ASIS.docx",
            f"{c_part}_{d_part}_{prefix}_{num}_{name}_TOBE.docx",
        )

    return f"{prefix}_{num}_{name}_ASIS.docx", f"{prefix}_{num}_{name}_TOBE.docx"


def get_canonical_global_filename(
    client_name: str,
    date_str: str | None = None,
    locale: str | None = None,
) -> str:
    """Returns the concise executive consolidated global report filename with underscores in target language."""
    import os
    from datetime import datetime

    from assessment_engine.infrastructure.localization import t

    doc_lang = (locale or os.environ.get("ASSESSMENT_DOC_LANG") or "en").lower()
    report_name = t(
        "file_name_consolidated_report",
        locale=doc_lang,
    )

    c_part = client_name.strip().replace(" ", "_")
    d_part = date_str or datetime.now().strftime("%Y%m")
    return f"{c_part}_{d_part}_{report_name}.docx"


def get_canonical_tomo_filename(
    client_name: str,
    tomo: str,
    date_str: str | None = None,
    locale: str | None = None,
) -> str:
    """Returns the concise executive filename for a specific strategic volume (ASIS, TOBE, TODO) with underscores."""
    import os
    from datetime import datetime

    from assessment_engine.infrastructure.localization import t

    doc_lang = (locale or os.environ.get("ASSESSMENT_DOC_LANG") or "en").lower()
    t_map = {
        "asis": "tomo_1_title",
        "tobe": "tomo_2_title",
        "todo": "tomo_3_title",
    }
    t_key = t_map.get(tomo.lower(), "tomo_1_title")
    tomo_name = t(t_key, locale=doc_lang)

    c_part = client_name.strip().replace(" ", "_")
    d_part = date_str or datetime.now().strftime("%Y%m")
    return f"{c_part}_{d_part}_{tomo_name}.docx"

