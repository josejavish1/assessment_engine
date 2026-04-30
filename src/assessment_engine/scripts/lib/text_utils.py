"""
Módulo text_utils.py.
Proporciona utilidades centralizadas para el saneamiento y normalización de texto,
especialmente para su uso en renderizadores de Word/XML.
"""
import re
import unicodedata

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
    text = "".join(
        ch for ch in str(value)
        if ch in "\n\t\r" or ord(ch) >= 32
    )
    
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
