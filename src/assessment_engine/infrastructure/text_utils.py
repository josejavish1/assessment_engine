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
    """Normalize a string by removing trailing, prompt-generated phrases. The function first collapses all whitespace sequences into single spaces. It then employs a case-insensitive regular expression to remove trailing phrases that begin with a predefined set of Spanish verbs (e.g., 'evalúa', 'mide', 'cubre'). Finally, any leading or trailing spaces, commas, semicolons, colons, or hyphens are stripped from the result. Args: value (str): The raw string to be normalized. Returns: str: The normalized string. An empty string is returned if the input, after whitespace normalization, is empty."""
    text = normalize_spaces(value)
    if not text:
        return ""
    return re.sub(
        r"\s+(evalua|evalúa|cubre|mide|analiza|describe|responde)\b.*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" ,;:-")


def slugify(value: str) -> str:
    r"""{'docstring': 'Generate a filesystem-safe, ASCII-only slug from a string.\n\nThe function transforms the input string by applying the following sequential\noperations:\n1.  Unicode normalization is performed using the NFKD compatibility form.\n2.  The normalized string is encoded to ASCII, discarding any characters that\n    cannot be represented.\n3.  All sequences of non-alphanumeric characters are collapsed into a single\n    underscore.\n4.  Any leading or trailing underscores are removed.\n5.  The resulting string is converted to lowercase.\n\nFor example, the input "  Ein schönes Mädchen!  " is converted to\n"ein_schones_madchen".\n\nIf the string is empty after these transformations, or if the input is `None`,\nthis function returns a default value of "generic".\n\nArgs:\n    value (str): The string to be converted into a slug.\n\nReturns:\n    str: The generated slug. Contains only lowercase ASCII letters, digits,\n        and underscores, with no leading or trailing underscores.'}."""
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return cleaned or "generic"


def format_currency_custom(
    val: float, vocab: dict[str, Any], doc_lang: str = "es"
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
            to 'es'.

    Returns:
        A string representing the formatted monetary value.
    """
    symbol = vocab.get("currency_symbol", "€")
    format_type = vocab.get(
        "currency_format", "EU"
    )  # Specifies the locale format, e.g., "EU" or "US".
    lang = str(doc_lang or "es").lower()

    # Perform number formatting via direct string and mathematical manipulation to ensure OS-agnostic behavior.
    formatted_num = f"{val:,.2f}"  # Example: "1,234,567.89"

    if format_type == "EU" or lang in ["es", "pt", "fr"]:
        # Swaps the decimal and thousands separators to conform to the European number format.
        formatted_num = (
            formatted_num.replace(",", "X").replace(".", ",").replace("X", ".")
        )

    if lang == "ja":
        # The Japanese Yen (JPY) does not use minor currency units (decimals) in general circulation.
        formatted_num = f"{int(round(val)):,}"
        return f"{formatted_num}{symbol}"

    # Assemble the final formatted string based on the locale-specific standard.
    if lang in ["en", "ja"]:
        return f"{symbol}{formatted_num}"
    else:
        return f"{formatted_num} {symbol}"
