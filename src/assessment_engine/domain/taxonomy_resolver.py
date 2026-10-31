"""Authoritative Domain Taxonomy Resolver for Multilingual Architecture Towers (RFC-022).

Provides deterministic, late-binding resolution of towers, pillars, and capabilities
from canonical identifiers or English canonical names into target client locales.
Eliminates split-brain ontology anomalies and language contagion across the engine.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import threading
from typing import Any

logger = logging.getLogger(__name__)

_RESOLVER_LOCK = threading.Lock()
_RESOLVER_INSTANCE: TaxonomyResolver | None = None


def _get_default_taxonomy_path() -> Path:
    """Resolve default multilingual taxonomy path using pure domain filesystem relative path."""
    return Path(__file__).resolve().parents[3] / "engine_config" / "taxonomy_multilingual.json"


class TaxonomyResolver:
    """Deterministic, late-binding multilingual resolver for enterprise architecture taxonomy."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize resolver loading authoritative multilingual taxonomy catalog."""
        self._config_path = config_path or _get_default_taxonomy_path()
        self._taxonomy: dict[str, Any] = {}
        self._canonical_name_to_id: dict[str, tuple[str, str]] = {}
        self._localized_name_to_id: dict[str, tuple[str, str]] = {}
        self._scoped_name_to_id: dict[tuple[str, str], tuple[str, str]] = {}
        self._capabilities_index: dict[str, dict[str, str]] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load and index taxonomy catalog into fast bidirectional lookup structures."""
        if not self._config_path.exists():
            logger.warning(
                "Taxonomy catalog file not found at %s. Resolver will use defaults.",
                self._config_path,
            )
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._taxonomy = json.load(f)
        except (OSError, ValueError) as ex:
            logger.error("Failed to load taxonomy catalog %s: %s", self._config_path, ex)
            return

        # Build reverse lookup indices for resilient O(1) resolution
        for tower_id, t_data in self._taxonomy.items():
            t_canonical = t_data.get("canonical_name", "").strip().lower()
            if t_canonical:
                self._canonical_name_to_id[t_canonical] = (tower_id, "")

            # Index pillars
            for p_id, p_data in t_data.get("pillars", {}).items():
                p_canonical = p_data.get("canonical_name", "").strip().lower()
                if p_canonical:
                    self._canonical_name_to_id[p_canonical] = (tower_id, p_id)
                    self._scoped_name_to_id[(tower_id.upper(), p_canonical)] = (tower_id, p_id)

                for loc_val in p_data.get("locales", {}).values():
                    loc_val_norm = str(loc_val).strip().lower()
                    if loc_val_norm:
                        self._localized_name_to_id[loc_val_norm] = (tower_id, p_id)
                        self._scoped_name_to_id[(tower_id.upper(), loc_val_norm)] = (tower_id, p_id)

            # Index capabilities O(1)
            for c_canon, c_entry in t_data.get("capabilities", {}).items():
                c_canon_clean = str(c_canon).strip()
                c_canon_lower = c_canon_clean.lower()
                loc_map = c_entry.get("locales", c_entry) if isinstance(c_entry, dict) else {}

                # Canonical English entry
                self._capabilities_index[c_canon_lower] = {
                    "en": c_canon_clean,
                    **{k: str(v).strip() for k, v in loc_map.items()},
                }

                # Reverse index for each localized translation
                for loc_code, loc_text in loc_map.items():
                    loc_text_norm = str(loc_text).strip().lower()
                    if loc_text_norm not in self._capabilities_index:
                        self._capabilities_index[loc_text_norm] = self._capabilities_index[c_canon_lower]

    @staticmethod
    def _normalize_locale(locale: str) -> str:
        """Normalize locale string to 2-letter base code."""
        if not locale:
            return "en"
        return str(locale).strip().lower().split("_")[0].split("-")[0]

    def resolve_tower_name(
        self, tower_id: str, default: str = "", locale: str = "en"
    ) -> str:
        """Resolve localized tower name from tower identifier (e.g. 'T1', 'T2')."""
        norm_tid = str(tower_id).strip().upper()
        norm_locale = self._normalize_locale(locale)

        t_data = self._taxonomy.get(norm_tid)
        if not t_data:
            return default or tower_id

        locales_map = t_data.get("locales", {})
        if norm_locale in locales_map:
            return locales_map[norm_locale]
        if "en" in locales_map:
            return locales_map["en"]
        return t_data.get("canonical_name", default or tower_id)

    def resolve_pillar_name(
        self, tower_id: str, pillar_id: str, default: str = "", locale: str = "en"
    ) -> str:
        """Resolve localized pillar name from tower and pillar IDs (e.g. 'T2', 'T2.P1')."""
        norm_tid = str(tower_id).strip().upper()
        norm_pid = str(pillar_id).strip().upper()
        norm_locale = self._normalize_locale(locale)

        t_data = self._taxonomy.get(norm_tid, {})
        pillars_map = t_data.get("pillars", {})
        p_data = pillars_map.get(norm_pid)

        if not p_data:
            return default or pillar_id

        locales_map = p_data.get("locales", {})
        if norm_locale in locales_map:
            return locales_map[norm_locale]
        if "en" in locales_map:
            return locales_map["en"]
        return p_data.get("canonical_name", default or pillar_id)

    def resolve_pillar_by_any_reference(
        self, name_or_id: str, default: str = "", locale: str = "en", tower_id: str = ""
    ) -> str:
        """Resolve localized pillar name from ID or any known localized/canonical name."""
        if not name_or_id:
            return default

        norm_ref = str(name_or_id).strip()
        norm_ref_lower = norm_ref.lower()
        norm_locale = self._normalize_locale(locale)

        # 1. Direct Pillar ID check (e.g. 'T1.P1', 'T2.P3')
        if "." in norm_ref:
            parts = norm_ref.split(".")
            if len(parts) >= 2:
                tid = parts[0].upper()
                pid = f"{tid}.{parts[1].upper()}"
                res = self.resolve_pillar_name(tid, pid, default="", locale=norm_locale)
                if res:
                    return res

        # 2. Scoped check by tower_id to prevent cross-tower name collisions
        if tower_id:
            scope_key = (tower_id.strip().upper(), norm_ref_lower)
            if scope_key in self._scoped_name_to_id:
                tid, pid = self._scoped_name_to_id[scope_key]
                if tid and pid:
                    return self.resolve_pillar_name(tid, pid, default=default, locale=norm_locale)

        # 3. Reverse index check on canonical names
        if norm_ref_lower in self._canonical_name_to_id:
            tid, pid = self._canonical_name_to_id[norm_ref_lower]
            if tid and pid:
                return self.resolve_pillar_name(tid, pid, default=default, locale=norm_locale)

        # 4. Reverse index check on localized names
        if norm_ref_lower in self._localized_name_to_id:
            tid, pid = self._localized_name_to_id[norm_ref_lower]
            if tid and pid:
                return self.resolve_pillar_name(tid, pid, default=default, locale=norm_locale)

        return default or name_or_id

    def resolve_capability_name(
        self, cap_name: str, default: str = "", locale: str = "en"
    ) -> str:
        """Resolve localized capability name from canonical or raw string in O(1)."""
        if not cap_name:
            return default

        norm_cap = str(cap_name).strip()
        norm_cap_lower = norm_cap.lower()
        norm_locale = self._normalize_locale(locale)

        if norm_cap_lower in self._capabilities_index:
            loc_dict = self._capabilities_index[norm_cap_lower]
            if norm_locale in loc_dict:
                return loc_dict[norm_locale]
            if "en" in loc_dict:
                return loc_dict["en"]

        return default or cap_name


def get_taxonomy_resolver() -> TaxonomyResolver:
    """Retrieve shared thread-safe singleton instance of TaxonomyResolver."""
    global _RESOLVER_INSTANCE
    if _RESOLVER_INSTANCE is None:
        with _RESOLVER_LOCK:
            if _RESOLVER_INSTANCE is None:
                _RESOLVER_INSTANCE = TaxonomyResolver()
    return _RESOLVER_INSTANCE
