"""Provides centralized utilities for text sanitization and normalization. These functions prepare text for rendering in XML-based document formats, such as Office Open XML (OOXML), by handling character encoding, whitespace, and control character constraints."""

import re
import unicodedata


def normalize_spaces(value: str) -> str:
    """Consolidate all whitespace characters in a string to single spaces and remove leading/trailing whitespace."""
    text = str(value or "").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def clean_text_for_word(value: str) -> str:
    """Sanitizes a string for use in Office Open XML (OOXML) documents.

    The function ensures the string is compliant with the ECMA-376 standard by
    removing illegal XML characters. It filters out most ASCII control characters
    (ordinal value < 32) while preserving tab, newline, and carriage return.
    Additionally, it strips common residual Markdown syntax, such as bold
    markers ('**'), and removes leading and trailing whitespace.

    Args:
        value: The input value to be sanitized. Non-string values are coerced
            to their string representation before processing.

    Returns:
        The sanitized string suitable for OOXML inclusion. An empty string is
        returned if the input value is falsy (e.g., None, "").
    """
    if not value:
        return ""

    #
    # Filters out control characters that are invalid within Office Open XML (OOXML) documents. The ECMA-376 standard prohibits most control characters (ASCII < 32), permitting only tab (\t), newline (\n), and carriage return (\r).
    text = "".join(ch for ch in str(value) if ch in "\n\t\r" or ord(ch) >= 32)

    # Strips common Markdown syntax artifacts to prevent them from being rendered as literal characters in the target document format.
    # This normalization is currently scoped to remove Markdown bold syntax ('**'), a frequently observed residual artifact from upstream text generation sources.
    text = text.replace("**", "")

    return text.strip()


def normalize_tower_name(value: str) -> str:
    """Normalize a tower name by removing common instructional phrases.

    This function processes a raw tower name string to generate a more concise
    and canonical identifier. The normalization process involves three steps:
    1.  Internal whitespace is collapsed into single spaces.
    2.  Any trailing text starting with a set of Spanish instruction verbs
        (e.g., 'evalua', 'cubre', 'mide', 'analiza', 'describe') is removed
        using a case-insensitive match.
    3.  Leading and trailing whitespace and punctuation (',', ';', ':', '-')
        are stripped from the result.

    Args:
        value: The raw tower name string to normalize.

    Returns:
        A normalized version of the tower name, or an empty string if the input
        is or becomes empty after processing.
    """
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
    """Generate a URL- and filename-safe slug from a given value.

    Converts a value to a URL-safe slug. The input is coerced to a string,
    Unicode-normalized (NFKD), and stripped of non-ASCII characters.
    Subsequently, sequences of non-alphanumeric characters are replaced by a
    single underscore, leading/trailing underscores are removed, and the entire
    result is converted to lowercase.

    Example:
        `slugify('  Héllo World! -- ')` returns `'hello_world'`.

    Args:
        value (str): The input to be slugified. Non-string types are coerced
            to their string representation.

    Returns:
        str: The resulting slug. Returns 'generic' if the process results in an
            empty string.
    """
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return cleaned or "generic"
