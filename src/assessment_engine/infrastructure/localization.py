from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)

_LOCALES_CACHE: dict[str, Any] | None = None


def load_locales_catalog() -> dict[str, Any]:
    """Load and cache the canonical locales catalog from engine_config/locales.json."""
    global _LOCALES_CACHE
    if _LOCALES_CACHE is not None:
        return _LOCALES_CACHE

    locales_path = ROOT / "engine_config" / "locales.json"
    if not locales_path.exists():
        locales_path = Path("engine_config/locales.json")

    try:
        with open(locales_path, "r", encoding="utf-8-sig") as f:
            _LOCALES_CACHE = json.load(f)
    except Exception as ex:
        logger.warning(f"⚠️ [Localization] Failed to load locales catalog: {ex}. Using fallback.")
        _LOCALES_CACHE = {}

    return _LOCALES_CACHE or {}


def normalize_locale(locale: str | None) -> tuple[str, str]:
    """Normalize a locale tag into a tuple of (full_normalized_tag, base_language_code)."""
    if not locale:
        return "es", "es"
    cleaned = str(locale).strip().lower().replace("-", "_")
    base = cleaned.split("_")[0]
    return cleaned, base


def resolve_base_locale(locale: str | None) -> str:
    """Normalize a locale tag (e.g., 'es_ES', 'es-AR', 'EN_US') to its base code ('es', 'en')."""
    return normalize_locale(locale)[1]


def format_number(value: float, locale: str = "es", decimals: int = 2) -> str:
    """Format a numerical value according to ICU regional standards without external dependencies."""
    norm_loc, base_loc = normalize_locale(locale)
    val_float = float(value)
    abs_val = abs(val_float)
    integer_part = int(abs_val)
    decimal_part = f"{abs_val - integer_part:.{decimals}f}"[2:] if decimals > 0 else ""
    sign = "-" if val_float < 0 else ""

    # Group integer part into thousands
    int_str = str(integer_part)
    groups = []
    while int_str:
        groups.append(int_str[-3:])
        int_str = int_str[:-3]
    groups.reverse()

    if norm_loc in ["de_ch", "fr_ch", "it_ch", "chf"]:
        # Swiss standard: "'" thousands separator, '.' decimal point
        formatted_int = "'".join(groups)
        return f"{sign}{formatted_int}.{decimal_part}" if decimals > 0 else f"{sign}{formatted_int}"
    elif base_loc in ["es", "de"]:
        # Continental Europe: '.' thousands separator, ',' decimal point
        formatted_int = ".".join(groups)
        return f"{sign}{formatted_int},{decimal_part}" if decimals > 0 else f"{sign}{formatted_int}"
    elif base_loc == "fr":
        # French: ' ' thousands separator, ',' decimal point
        formatted_int = " ".join(groups)
        return f"{sign}{formatted_int},{decimal_part}" if decimals > 0 else f"{sign}{formatted_int}"
    else:
        # Anglo-American & Default: ',' thousands separator, '.' decimal point
        formatted_int = ",".join(groups)
        return f"{sign}{formatted_int}.{decimal_part}" if decimals > 0 else f"{sign}{formatted_int}"


def format_currency(
    value: float,
    currency_code: str = "EUR",
    currency_symbol: str | None = None,
    locale: str = "es",
    decimals: int = 2,
) -> str:
    """Format monetary figures with regional currency placement and symbols according to ICU standards."""
    norm_loc, base_loc = normalize_locale(locale)
    code = (currency_code or "EUR").upper()

    sym = currency_symbol or {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "CHF": "CHF",
        "JPY": "¥",
    }.get(code, "€")

    formatted_num = format_number(value, locale=locale, decimals=decimals)

    if code == "CHF" or norm_loc in ["de_ch", "fr_ch", "it_ch"]:
        return f"CHF {formatted_num}"
    elif base_loc in ["es", "de", "fr"]:
        # Suffix format: '1.426,94 €'
        return f"{formatted_num} {sym}"
    else:
        # Prefix format: '$1,426.94', '£1,426.94'
        return f"{sym}{formatted_num}"


def get_localized_string(
    key: str,
    locale: str = "es",
    default: str | None = None,
    **kwargs: Any,
) -> str:
    """Retrieve a localized template string and format it with parameters using locale fallback resolution."""
    catalog = load_locales_catalog()
    base_loc = resolve_base_locale(locale)

    # Resolution hierarchy: exact locale -> base language -> 'en' -> 'es'
    text_template = None
    for loc in [locale, base_loc, "en", "es"]:
        if loc in catalog and isinstance(catalog[loc], dict):
            if key in catalog[loc]:
                text_template = catalog[loc][key]
                break

    if text_template is None:
        text_template = default if default is not None else key

    if not isinstance(text_template, str):
        return str(text_template)

    if kwargs:
        try:
            return text_template.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return text_template

    return text_template


# Canonical internationalization alias
t = get_localized_string


def get_localized_list(
    key: str,
    locale: str = "es",
    default: list[str] | None = None,
) -> list[str]:
    """Retrieve a localized list of strings using locale fallback resolution."""
    catalog = load_locales_catalog()
    base_loc = resolve_base_locale(locale)

    for loc in [locale, base_loc, "en", "es"]:
        if loc in catalog and isinstance(catalog[loc], dict):
            val = catalog[loc].get(key)
            if isinstance(val, list):
                return [str(item) for item in val]

    return default if default is not None else []


def get_archimate_catalog(locale: str = "es") -> dict[str, list[str]]:
    """Retrieve the localized ArchiMate technical deliverables catalog for a given locale."""
    catalog = load_locales_catalog()
    base_loc = resolve_base_locale(locale)

    for loc in [base_loc, "en", "es"]:
        if loc in catalog and "archimate_catalog" in catalog[loc]:
            return catalog[loc]["archimate_catalog"]

    return {}


def get_archimate_fallback_deliverables(locale: str = "es") -> list[str]:
    """Retrieve default architecture deliverables when no catalog keywords match."""
    catalog = load_locales_catalog()
    base_loc = resolve_base_locale(locale)

    for loc in [base_loc, "en", "es"]:
        if loc in catalog and "archimate_fallback_deliverables" in catalog[loc]:
            return catalog[loc]["archimate_fallback_deliverables"]

    if base_loc == "en":
        return [
            "Technical Architecture Design (HLD/LLD)",
            "Testing and Validation Plan",
        ]
    return [
        "Documento de Diseño Técnico (HLD/LLD)",
        "Plan de Pruebas y Validación",
    ]


def apply_vocabulary_substitutions(text: str, locale: str = "es") -> str:
    """Applies declarative style and vocabulary normalizations using regex word boundaries."""
    if not text:
        return text

    import re

    base_loc = resolve_base_locale(locale)
    catalog = load_locales_catalog()
    substitutions = catalog.get(base_loc, {}).get(
        "vocabulary_substitutions", {}
    )
    if not substitutions:
        return text

    res = text
    for pattern_str, repl in substitutions.items():
        res = re.sub(rf"\b{pattern_str}\b", repl, res, flags=re.IGNORECASE)
    return res
