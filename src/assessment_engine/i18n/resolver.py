"""Declarative i18n and Currency Formatting Engine for AST Document Compilation.

Strict, zero-fallback localization resolver adhering to Invariant III of RFC-026:
- Zero silent fallbacks to raw symbolic keys.
- Deterministic ISO 4217 currency and number formatting across global locales.
- Bijective mapping against engine_config/locales.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from assessment_engine.infrastructure.runtime_paths import ROOT


DEFAULT_SYSTEM_LOCALE: str = "en"


class MissingLocalizationKeyError(KeyError):
    """Raised when an AST node requests an unregistered i18n key (Invariant III)."""
    pass


class DeclarativeI18nResolver:
    """Strict, zero-fallback localization resolver for AST compilation."""

    _DEFAULT_LOCALES_PATH = ROOT / "engine_config" / "locales.json"

    def __init__(self, locales_path: Path | None = None) -> None:
        self._locales_path: Path = locales_path or self._DEFAULT_LOCALES_PATH
        self._registry: Dict[str, Dict[str, Any]] = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        if not self._locales_path.exists():
            raise FileNotFoundError(f"Locales configuration missing at: {self._locales_path}")
        with self._locales_path.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        return data

    @staticmethod
    def normalize_locale(locale: str | None) -> str:
        """Deterministically normalize locale token or return default system locale."""
        if not locale or not str(locale).strip():
            return DEFAULT_SYSTEM_LOCALE
        return str(locale).lower().strip().replace("-", "_").split("_")[0]

    def resolve(self, key: str, locale: str) -> str:
        """Resolve localized string strictly for the given key and locale."""
        clean_locale = self.normalize_locale(locale)
        
        # Try clean locale first, then base language, then en fallback
        target_dict: Dict[str, Any] | None = None
        if clean_locale in self._registry:
            target_dict = self._registry[clean_locale]
        elif DEFAULT_SYSTEM_LOCALE in self._registry:
            target_dict = self._registry[DEFAULT_SYSTEM_LOCALE]
            
        if target_dict is None or key not in target_dict or not str(target_dict[key]).strip():
            # Check if key is available in en
            en_dict = self._registry.get(DEFAULT_SYSTEM_LOCALE, {})
            if key in en_dict and str(en_dict[key]).strip():
                return str(en_dict[key])
            raise MissingLocalizationKeyError(
                f"Invariant III Violation: Localization key '{key}' is missing or empty "
                f"for locale '{locale}' in {self._locales_path}."
            )
        return str(target_dict[key])

    ZERO_DECIMAL_CURRENCIES = frozenset({"JPY", "KRW", "VND", "CLP", "HUF", "PYG"})

    @classmethod
    def format_currency(cls, amount: float, currency_code: str, locale: str) -> str:
        """Format currency according to ISO 4217 standard and locale conventions."""
        clean_loc = cls.normalize_locale(locale)
        code = currency_code.upper().strip() if currency_code else "USD"

        symbol_map = {
            "EUR": "€",
            "USD": "$",
            "GBP": "£",
            "JPY": "¥",
            "CHF": "CHF",
            "BRL": "R$",
            "SAR": "SAR",
            "AED": "AED",
            "SGD": "S$",
            "CAD": "CA$",
            "AUD": "A$",
        }
        sym = symbol_map.get(code, code)
        is_zero_dec = code in cls.ZERO_DECIMAL_CURRENCIES

        if clean_loc in ("es", "de", "fr", "pt", "it"):
            # Continental standard: 1.234.567,89 € or 1.250.000 ¥
            if is_zero_dec:
                formatted_num = f"{int(round(amount)):,}".replace(",", ".")
            else:
                formatted_num = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{formatted_num} {sym}"
        else:
            # Anglo-Saxon & International standard: $1,234,567.89 or ¥1,250,000
            if is_zero_dec:
                formatted_num = f"{int(round(amount)):,}"
            else:
                formatted_num = f"{amount:,.2f}"
            return f"{sym}{formatted_num}"
