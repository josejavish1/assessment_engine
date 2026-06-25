"""
Módulo text_utils.py.
Proporciona utilidades centralizadas para el saneamiento y normalización de texto,
especialmente para su uso en renderizadores de Word/XML.
"""

import html
import re
import unicodedata
from typing import Any


def deep_unescape(obj: Any) -> Any:
    """
    Recorre de forma recursiva cualquier estructura de datos (dict, list, str)
    y sanea/des-escapa entidades HTML de todos los strings.
    """
    if isinstance(obj, dict):
        return {k: deep_unescape(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_unescape(item) for item in obj]
    elif isinstance(obj, str):
        return html.unescape(obj)
    return obj


def normalize_spaces(value: str) -> str:
    """Normaliza espacios y saltos de línea."""
    text = str(value or "").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def clean_text_for_word(value: str) -> str:
    """
    Sanea el texto eliminando caracteres de control no compatibles con XML/Word
    y normalizando espacios.
    """
    if not value:
        return ""

    # Mantener solo caracteres imprimibles, tabuladores y saltos de línea
    # Word no admite la mayoría de los caracteres de control < 32 excepto \t, \n, \r
    text = "".join(ch for ch in str(value) if ch in "\n\t\r" or ord(ch) >= 32)

    # Eliminar marcadores de Markdown comunes si se desea un texto limpio para Word
    # Por ahora solo eliminamos negritas de Markdown que a veces se cuelan
    text = text.replace("**", "")

    return text.strip()


def normalize_tower_name(value: str) -> str:
    """
    Normaliza el nombre de una torre, eliminando frases redundantes del prompt.
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
    """Convierte un texto en un slug seguro para nombres de archivos."""
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return cleaned or "generic"


def format_currency_custom(
    val: float, vocab: dict[str, Any], doc_lang: str = "es"
) -> str:
    """
    Formatea una cifra monetaria de forma dinámica e i18n basándose en locales.json.
    Soporta símbolos de divisa y formatos locales (comas/puntos) de forma matemática pura
    sin depender de OS-locale.
    """
    symbol = vocab.get("currency_symbol", "€")
    format_type = vocab.get("currency_format", "EU")  # "EU" o "US"
    lang = str(doc_lang or "es").lower()

    # Formateo numérico matemático puro independiente del SO
    formatted_num = f"{val:,.2f}"  # ej: "1,234,567.89"

    if format_type == "EU" or lang in ["es", "pt", "fr"]:
        # Convertir de standard 1,234,567.89 a europeo 1.234.567,89
        formatted_num = (
            formatted_num.replace(",", "X").replace(".", ",").replace("X", ".")
        )

    if lang == "ja":
        # El yen japonés no utiliza decimales en contextos generales
        formatted_num = f"{int(round(val)):,}"
        return f"{formatted_num}{symbol}"

    # Ensamblar según el estándar del país
    if lang in ["en", "ja"]:
        return f"{symbol}{formatted_num}"
    else:
        return f"{formatted_num} {symbol}"
