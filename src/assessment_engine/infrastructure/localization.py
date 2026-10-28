from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)

_LOCALES_CACHE: dict[str, Any] | None = None
_LOCALES_MTIME: float | None = None

DYNAMIC_LOCALES_DIR = ROOT / "engine_config" / "locales_dynamic"
if not DYNAMIC_LOCALES_DIR.exists():
    DYNAMIC_LOCALES_DIR = Path("engine_config/locales_dynamic")


class DynamicLocaleSynthesizer:
    """Just-In-Time (JIT) synthesizer that dynamically generates UI dictionary translations for any language on Earth."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or DYNAMIC_LOCALES_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize_locale(self, target_locale: str) -> dict[str, Any]:
        import json
        import re

        clean_loc = (
            target_locale.lower().strip().replace("-", "_").split("_")[0]
            if target_locale
            else "en"
        )
        cache_file = self.cache_dir / f"{clean_loc}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and len(data) >= 50:
                        return data
            except Exception as ex:
                logger.debug(f"[JIT Locale] Error reading cached locale: {ex}")

        catalog = load_locales_catalog()
        ref_en = catalog.get("en", {})
        if not ref_en:
            return {}

        try:
            from assessment_engine.infrastructure.genai_client import (
                ModelTier,
                create_genai_client,
                get_model,
            )

            client = create_genai_client()
            model_name = get_model(ModelTier.FAST)

            prompt = f"""You are a certified executive business translator specializing in C-level management reports.
Translate the following JSON dictionary of professional executive technical report UI titles, headings, and labels from English into target language: '{clean_loc}'.
Preserve the exact same JSON keys and formatting placeholders (e.g. {{amount}}, {{capability}}).
Return ONLY the raw valid JSON with the exact same keys:

{json.dumps(ref_en, indent=2, ensure_ascii=False)}"""

            response = client.models.generate_content(
                model=model_name, contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)

            synthesized = json.loads(text)
            if isinstance(synthesized, dict) and len(synthesized) >= 50:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(synthesized, f, indent=2, ensure_ascii=False)
                logger.info(
                    f"✅ [JIT Locale] Successfully synthesized and cached new locale dictionary for '{clean_loc}'."
                )
                return synthesized
        except Exception as ex:
            logger.warning(
                f"⚠️ [JIT Locale] Failed to dynamically synthesize locale '{clean_loc}': {ex}. Using English fallback."
            )

        return ref_en


def load_locales_catalog() -> dict[str, Any]:
    """Load and cache the canonical locales catalog from engine_config/locales.json and dynamic locales."""
    global _LOCALES_CACHE, _LOCALES_MTIME

    locales_path = ROOT / "engine_config" / "locales.json"
    if not locales_path.exists():
        locales_path = Path("engine_config/locales.json")

    current_mtime = locales_path.stat().st_mtime if locales_path.exists() else None
    if _LOCALES_CACHE is not None and current_mtime == _LOCALES_MTIME:
        return _LOCALES_CACHE

    try:
        with open(locales_path, "r", encoding="utf-8-sig") as f:
            _LOCALES_CACHE = json.load(f)
            _LOCALES_MTIME = current_mtime
    except Exception as ex:
        logger.warning(f"⚠️ [Localization] Failed to load locales catalog: {ex}. Using fallback.")
        _LOCALES_CACHE = {}

    # Auto-load any dynamically synthesized and cached locales
    dynamic_dir = ROOT / "engine_config" / "locales_dynamic"
    if not dynamic_dir.exists():
        dynamic_dir = Path("engine_config/locales_dynamic")
    if dynamic_dir.exists():
        for loc_file in dynamic_dir.glob("*.json"):
            lang_code = loc_file.stem.lower()
            if lang_code not in _LOCALES_CACHE:
                try:
                    with open(loc_file, "r", encoding="utf-8-sig") as lf:
                        _LOCALES_CACHE[lang_code] = json.load(lf)
                except Exception as ex:
                    logger.debug("Error leyendo locale dinámico %s: %s", loc_file, ex)

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

    # JIT Synthesis: If the requested language is uncataloged, dynamically generate it on the fly
    if base_loc not in catalog and base_loc not in ["es", "en"]:
        dynamic_dict = DynamicLocaleSynthesizer().synthesize_locale(base_loc)
        if dynamic_dict:
            catalog[base_loc] = dynamic_dict

    # Resolution hierarchy: exact locale -> base language -> 'en' -> fallback
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
            "Infrastructure as Code (IaC / Terraform) Manifests",
            "Parameterized Operational Runbook and RACI Matrix",
            "Observability, Telemetry, and Alerting Dashboard",
        ]
    return [
        "Manifiestos de Infraestructura como Código (IaC / Terraform)",
        "Runbook Operativo Parametrizado y Matriz RACI",
        "Cuadro de Mando de Observabilidad, Telemetría y Alertas",
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


ISO_LANGUAGE_NAMES: dict[str, str] = {
    "es": "Spanish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "pt": "Portuguese",
    "it": "Italian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "ar": "Arabic",
    "ru": "Russian",
}


def resolve_target_language_name(locale_code: str | None) -> str:
    """Resolves an ISO-639-1 / BCP-47 locale code to its standardized English name for generative prompt projection."""
    if not locale_code:
        return "Spanish"
    base_loc = resolve_base_locale(locale_code)
    return ISO_LANGUAGE_NAMES.get(base_loc, base_loc.capitalize())


MONTH_NAMES: dict[str, dict[int, str]] = {
    "es": {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    },
    "en": {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    },
    "de": {
        1: "Januar", 2: "Februar", 3: "März", 4: "April",
        5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
        9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
    },
    "fr": {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
    },
    "it": {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre",
    },
    "pt": {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    },
    "ja": {
        1: "1月", 2: "2月", 3: "3月", 4: "4月",
        5: "5月", 6: "6月", 7: "7月", 8: "8月",
        9: "9月", 10: "10月", 11: "11月", 12: "12月",
    },
}


def format_date_localized(date_val: str | None = None, locale: str = "es") -> str:
    """Formats a date string or ISO date into localized 'Month Year' conforming to regional grammar standards."""
    from datetime import datetime

    base_loc = resolve_base_locale(locale)
    months_map = MONTH_NAMES.get(base_loc, MONTH_NAMES["en"])

    if not date_val or not str(date_val).strip():
        now = datetime.now()
        if base_loc == "ja":
            return f"{now.year}年{months_map[now.month]}"
        return f"{months_map[now.month]} {now.year}"

    cleaned = str(date_val).strip()
    try:
        dt = datetime.fromisoformat(cleaned)
        if base_loc == "ja":
            return f"{dt.year}年{months_map[dt.month]}"
        return f"{months_map[dt.month]} {dt.year}"
    except (ValueError, TypeError):
        pass

    return cleaned
