"""Multilingual taxonomy resolution and locale-aware formatting service."""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

logger = logging.getLogger(__name__)


class LocalizationResolver:
    """Resolves taxonomy identifiers and formats numbers dynamically by ISO locale."""

    # Locale-specific decimal and thousand separators across global enterprise regions
    LOCALE_NUMERIC_CONVENTIONS: dict[str, tuple[str, str]] = {
        "en": (".", ","),
        "ja": (".", ","),
        "zh": (".", ","),
        "ko": (".", ","),
        "es": (",", "."),
        "pt": (",", "."),
        "de": (",", "."),
        "it": (",", "."),
        "nl": (",", "."),
        "pl": (",", " "),
        "sv": (",", " "),
        "fr": (",", " "),
        "ru": (",", " "),
        "ar": (".", ","),
    }

    def __init__(self, taxonomy_catalog: dict[str, Any], target_language: str) -> None:
        self._catalog = taxonomy_catalog
        # Normalize primary subtag: e.g., 'es-ES' -> 'es', 'en-US' -> 'en'
        self._lang = target_language.split("-")[0].lower() if target_language else "en"
        if self._lang not in self.LOCALE_NUMERIC_CONVENTIONS:
            logger.warning(
                "Language code '%s' not in primary numeric map; falling back to international standard.",
                self._lang,
            )
            self._lang = "en"

    def resolve_tower_label(self, tower_id: str) -> str:
        """Resolves the localized display name for a given Tower ID."""
        node = self._catalog.get("towers", {}).get(tower_id, {})
        return self._extract_localized_string(node, fallback=tower_id)

    def resolve_pillar_label(self, tower_id: str, pillar_id: str) -> str:
        """Resolves the localized display name for a given Pillar ID."""
        node = (
            self._catalog.get("towers", {})
            .get(tower_id, {})
            .get("pillars", {})
            .get(pillar_id, {})
        )
        return self._extract_localized_string(node, fallback=pillar_id)

    def resolve_kpi_label(self, kpi_id: str) -> str:
        """Resolves the full localized string for a KPI identifier (e.g., T2.P1.K3)."""
        node = self._catalog.get("kpis", {}).get(kpi_id, {})
        localized_name = self._extract_localized_string(node, fallback="Unmapped Capability")
        return f"{kpi_id} - {localized_name}"

    def resolve_maturity_tier(self, score: float) -> str:
        """Maps a numerical score (0.0 - 5.0) to its localized maturity tier label."""
        tiers = self._catalog.get("maturity_tiers", {})
        bucket = str(int(Decimal(str(score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
        node = tiers.get(bucket, {})
        return self._extract_localized_string(node, fallback=f"Tier {bucket}")

    def format_decimal(self, value: float, decimal_places: int = 2) -> str:
        """Formats a float according to the target language's typographic conventions."""
        quantizer = Decimal("10") ** -decimal_places if decimal_places > 0 else Decimal("1")
        dec_val = Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)
        raw_str = f"{dec_val:,.{decimal_places}f}" if decimal_places > 0 else f"{int(dec_val):,d}"

        dec_sep, thousand_sep = self.LOCALE_NUMERIC_CONVENTIONS.get(self._lang, (".", ","))
        # Swap via temporary placeholder to avoid replacement collisions
        return (
            raw_str.replace(",", "__THOUSAND__")
            .replace(".", dec_sep)
            .replace("__THOUSAND__", thousand_sep)
        )

    def format_currency(
        self, amount: float, currency_code: str, decimal_places: int = 0
    ) -> str:
        """Formats monetary values with ISO-4217 currency code and locale separators."""
        formatted_num = self.format_decimal(amount, decimal_places=decimal_places)
        return f"{formatted_num} {currency_code.upper()}"

    def _extract_localized_string(self, node: dict[str, Any], fallback: str) -> str:
        """Extracts language-specific text from a taxonomy dictionary node."""
        if not isinstance(node, dict):
            return fallback
        labels = node.get("labels", {})
        return labels.get(self._lang) or labels.get("en") or fallback
