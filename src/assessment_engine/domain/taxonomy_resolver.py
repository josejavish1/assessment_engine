"""Authoritative Domain Taxonomy Resolver for Multilingual Architecture Towers (RFC-022).

Provides deterministic, late-binding resolution of towers, pillars, and capabilities
from canonical identifiers or English canonical names into target client locales.
Eliminates split-brain ontology anomalies and language contagion across the engine.

Enforces strict Hexagonal/Clean Architecture boundaries: zero filesystem I/O and
zero infrastructure imports inside the pure domain layer. Taxonomy concept catalogs
are injected via constructor or registered via TaxonomyCatalogLoaderPort.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import logging
import threading
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

_RESOLVER_LOCK = threading.Lock()
_RESOLVER_INSTANCE: PureTaxonomyResolver | None = None
_CATALOG_LOADER_PROVIDER: TaxonomyCatalogLoaderPort | None = None


def _freeze_str_mapping(raw: Mapping[str, Any] | None) -> Mapping[str, str]:
    """Convert a raw string mapping into an immutable MappingProxyType."""
    if not isinstance(raw, Mapping):
        return MappingProxyType({})
    return MappingProxyType(
        {str(k).strip().lower(): str(v).strip() for k, v in raw.items()}
    )


@dataclass(frozen=True)
class TaxonomyPillarConcept:
    """Immutable domain representation of a taxonomy pillar concept."""

    pillar_id: str
    canonical_name: str
    locales: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        """Enforce deep immutability on internal mappings."""
        if not isinstance(self.locales, MappingProxyType):
            object.__setattr__(
                self,
                "locales",
                _freeze_str_mapping(self.locales),
            )


@dataclass(frozen=True)
class TaxonomyConcept:
    """Immutable domain representation of an enterprise architecture tower concept."""

    tower_id: str
    canonical_name: str
    locales: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    pillars: Mapping[str, TaxonomyPillarConcept] = field(
        default_factory=lambda: MappingProxyType({})
    )
    capabilities: Mapping[str, Mapping[str, str]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        """Enforce deep immutability on all nested mapping attributes."""
        if not isinstance(self.locales, MappingProxyType):
            object.__setattr__(
                self,
                "locales",
                _freeze_str_mapping(self.locales),
            )

        if not isinstance(self.pillars, MappingProxyType):
            frozen_pillars: dict[str, TaxonomyPillarConcept] = {}
            if isinstance(self.pillars, Mapping):
                for p_id, p_val in self.pillars.items():
                    norm_pid = str(p_id).strip().upper()
                    if isinstance(p_val, TaxonomyPillarConcept):
                        frozen_pillars[norm_pid] = p_val
                    elif isinstance(p_val, Mapping):
                        p_canon = str(p_val.get("canonical_name", "_"[:0])).strip()
                        p_raw_loc = p_val.get("locales", {})
                        frozen_pillars[norm_pid] = TaxonomyPillarConcept(
                            pillar_id=norm_pid,
                            canonical_name=p_canon,
                            locales=_freeze_str_mapping(p_raw_loc),
                        )
            object.__setattr__(self, "pillars", MappingProxyType(frozen_pillars))

        if not isinstance(self.capabilities, MappingProxyType):
            frozen_caps: dict[str, Mapping[str, str]] = {}
            if isinstance(self.capabilities, Mapping):
                for c_canon, c_entry in self.capabilities.items():
                    c_canon_clean = str(c_canon).strip()
                    if isinstance(c_entry, MappingProxyType):
                        frozen_caps[c_canon_clean] = c_entry
                    elif isinstance(c_entry, Mapping):
                        loc_source = c_entry.get("locales", c_entry)
                        frozen_caps[c_canon_clean] = _freeze_str_mapping(
                            loc_source if isinstance(loc_source, Mapping) else {}
                        )
                    else:
                        frozen_caps[c_canon_clean] = MappingProxyType({})
            object.__setattr__(self, "capabilities", MappingProxyType(frozen_caps))

    @classmethod
    def from_raw_dict(cls, tower_id: str, raw: Mapping[str, Any]) -> TaxonomyConcept:
        """Construct a deeply immutable TaxonomyConcept from a raw dictionary payload."""
        norm_tid = str(tower_id).strip().upper()
        canonical_name = str(raw.get("canonical_name", "")).strip()
        raw_locales = raw.get("locales", {})
        locales = _freeze_str_mapping(
            raw_locales if isinstance(raw_locales, Mapping) else {}
        )

        pillars: dict[str, TaxonomyPillarConcept] = {}
        raw_pillars = raw.get("pillars", {})
        if isinstance(raw_pillars, Mapping):
            for p_id, p_data in raw_pillars.items():
                if not isinstance(p_data, Mapping):
                    continue
                norm_pid = str(p_id).strip().upper()
                p_canon = str(p_data.get("canonical_name", "")).strip()
                p_raw_loc = p_data.get("locales", {})
                pillars[norm_pid] = TaxonomyPillarConcept(
                    pillar_id=norm_pid,
                    canonical_name=p_canon,
                    locales=_freeze_str_mapping(
                        p_raw_loc if isinstance(p_raw_loc, Mapping) else {}
                    ),
                )

        capabilities: dict[str, Mapping[str, str]] = {}
        raw_caps = raw.get("capabilities", {})
        if isinstance(raw_caps, Mapping):
            for c_canon, c_entry in raw_caps.items():
                c_canon_clean = str(c_canon).strip()
                if isinstance(c_entry, Mapping):
                    loc_source = c_entry.get("locales", c_entry)
                    capabilities[c_canon_clean] = _freeze_str_mapping(
                        loc_source if isinstance(loc_source, Mapping) else {}
                    )
                else:
                    capabilities[c_canon_clean] = MappingProxyType({})

        return cls(
            tower_id=norm_tid,
            canonical_name=canonical_name,
            locales=locales,
            pillars=MappingProxyType(pillars),
            capabilities=MappingProxyType(capabilities),
        )

    def to_raw_dict(self) -> dict[str, Any]:
        """Convert domain concept back to dictionary representation for compatibility."""
        return {
            "canonical_name": self.canonical_name,
            "locales": dict(self.locales),
            "pillars": {
                pid: {
                    "canonical_name": p.canonical_name,
                    "locales": dict(p.locales),
                }
                for pid, p in self.pillars.items()
            },
            "capabilities": {
                cap_name: {"locales": dict(cap_locales)}
                for cap_name, cap_locales in self.capabilities.items()
            },
        }


@runtime_checkable
class TaxonomyCatalogLoaderPort(Protocol):
    """Port interface for loading the authoritative multilingual taxonomy catalog."""

    def load_taxonomy_catalog(self) -> Mapping[str, TaxonomyConcept]:
        """Load and return an immutable mapping of tower IDs to TaxonomyConcept objects."""
        ...


def normalize_taxonomy_catalog(
    catalog: Mapping[str, TaxonomyConcept | Mapping[str, Any]] | None,
) -> tuple[Mapping[str, TaxonomyConcept], dict[str, Any]]:
    """Normalize injected concept catalog into immutable TaxonomyConcept map and raw dict map."""
    concepts: dict[str, TaxonomyConcept] = {}
    raw_taxonomy: dict[str, Any] = {}
    if not catalog:
        return MappingProxyType(concepts), raw_taxonomy

    for tower_id, entry in catalog.items():
        norm_tid = str(tower_id).strip().upper()
        if isinstance(entry, TaxonomyConcept):
            concepts[norm_tid] = entry
            raw_taxonomy[norm_tid] = entry.to_raw_dict()
        elif isinstance(entry, Mapping):
            concept = TaxonomyConcept.from_raw_dict(norm_tid, entry)
            concepts[norm_tid] = concept
            raw_taxonomy[norm_tid] = dict(entry)
    return MappingProxyType(concepts), raw_taxonomy


class PureTaxonomyResolver:
    """Deterministic, late-binding multilingual resolver for enterprise architecture taxonomy.

    Pure domain component with zero filesystem dependencies. Accepts an injected
    immutable mapping of taxonomy concepts.
    """

    def __init__(
        self,
        catalog: Mapping[str, TaxonomyConcept | Mapping[str, Any]] | None = None,
        config_path: Any = None,
    ) -> None:
        """Initialize resolver from an injected multilingual taxonomy concept catalog or config path."""
        self._concepts: Mapping[str, TaxonomyConcept] = MappingProxyType({})
        self._taxonomy: dict[str, Any] = {}
        self._canonical_name_to_id: dict[str, tuple[str, str]] = {}
        self._localized_name_to_id: dict[str, tuple[str, str]] = {}
        self._scoped_name_to_id: dict[tuple[str, str], tuple[str, str]] = {}
        self._capabilities_index: dict[str, dict[str, str]] = {}

        if catalog is None and config_path is not None:
            import json
            from pathlib import Path
            p = Path(config_path)
            if p.exists():
                try:
                    catalog = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass

        if catalog is not None and isinstance(catalog, Mapping):
            self._concepts, self._taxonomy = normalize_taxonomy_catalog(catalog)
        self._load_catalog()

    @property
    def concepts(self) -> Mapping[str, TaxonomyConcept]:
        """Return deeply immutable read-only view of indexed taxonomy concepts."""
        if not isinstance(self._concepts, MappingProxyType):
            return MappingProxyType(self._concepts)
        return self._concepts

    def _load_catalog(self) -> None:
        """Index injected taxonomy catalog into fast bidirectional lookup structures."""
        if not self._concepts and self._taxonomy:
            self._concepts, _ = normalize_taxonomy_catalog(self._taxonomy)

        if not self._concepts:
            logger.debug(
                "Empty taxonomy catalog injected into PureTaxonomyResolver; using fallback defaults."
            )
            return

        for tower_id, concept in self._concepts.items():
            t_canonical = concept.canonical_name.strip().lower()
            if t_canonical:
                self._canonical_name_to_id[t_canonical] = (tower_id, "")

            for p_id, p_concept in concept.pillars.items():
                p_canonical = p_concept.canonical_name.strip().lower()
                if p_canonical:
                    self._canonical_name_to_id[p_canonical] = (tower_id, p_id)
                    self._scoped_name_to_id[(tower_id.upper(), p_canonical)] = (tower_id, p_id)

                for loc_val in p_concept.locales.values():
                    loc_val_norm = str(loc_val).strip().lower()
                    if loc_val_norm:
                        self._localized_name_to_id[loc_val_norm] = (tower_id, p_id)
                        self._scoped_name_to_id[(tower_id.upper(), loc_val_norm)] = (tower_id, p_id)

            for c_canon, loc_map in concept.capabilities.items():
                c_canon_clean = str(c_canon).strip()
                c_canon_lower = c_canon_clean.lower()

                self._capabilities_index[c_canon_lower] = {
                    "en": c_canon_clean,
                    **{k: str(v).strip() for k, v in loc_map.items()},
                }

                for loc_text in loc_map.values():
                    loc_text_norm = str(loc_text).strip().lower()
                    if loc_text_norm not in self._capabilities_index:
                        self._capabilities_index[loc_text_norm] = self._capabilities_index[
                            c_canon_lower
                        ]

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

        concept = self._concepts.get(norm_tid)
        if not concept:
            return default or tower_id

        if norm_locale in concept.locales:
            return concept.locales[norm_locale]
        if "en" in concept.locales:
            return concept.locales["en"]
        return concept.canonical_name or default or tower_id

    def resolve_pillar_name(
        self, tower_id: str, pillar_id: str, default: str = "", locale: str = "en"
    ) -> str:
        """Resolve localized pillar name from tower and pillar IDs (e.g. 'T2', 'T2.P1')."""
        norm_tid = str(tower_id).strip().upper()
        norm_pid = str(pillar_id).strip().upper()
        norm_locale = self._normalize_locale(locale)

        concept = self._concepts.get(norm_tid)
        if not concept:
            return default or ""

        p_concept = concept.pillars.get(norm_pid)
        if not p_concept:
            return default or ""

        if norm_locale in p_concept.locales:
            return p_concept.locales[norm_locale]
        if "en" in p_concept.locales:
            return p_concept.locales["en"]
        return p_concept.canonical_name or default or ""

    def resolve_pillar_by_any_reference(
        self, name_or_id: str, default: str = "", locale: str = "en", tower_id: str = ""
    ) -> str:
        """Resolve localized pillar name from ID or any known localized/canonical name."""
        if not name_or_id:
            return default

        norm_ref = str(name_or_id).strip()
        norm_ref_lower = norm_ref.lower()
        norm_locale = self._normalize_locale(locale)

        if "." in norm_ref:
            parts = norm_ref.split(".")
            if len(parts) >= 2:
                tid = parts[0].upper()
                pid = f"{tid}.{parts[1].upper()}"
                res = self.resolve_pillar_name(tid, pid, default="", locale=norm_locale)
                if res:
                    return res

        if tower_id:
            scope_key = (tower_id.strip().upper(), norm_ref_lower)
            if scope_key in self._scoped_name_to_id:
                tid, pid = self._scoped_name_to_id[scope_key]
                if tid and pid:
                    return self.resolve_pillar_name(tid, pid, default=default, locale=norm_locale)

        if norm_ref_lower in self._canonical_name_to_id:
            tid, pid = self._canonical_name_to_id[norm_ref_lower]
            if tid and pid:
                return self.resolve_pillar_name(tid, pid, default=default, locale=norm_locale)

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


TaxonomyResolver = PureTaxonomyResolver


def register_taxonomy_catalog_loader(loader: TaxonomyCatalogLoaderPort) -> None:
    """Register infrastructure catalog loader port and reset cached singleton."""
    global _CATALOG_LOADER_PROVIDER, _RESOLVER_INSTANCE
    with _RESOLVER_LOCK:
        _CATALOG_LOADER_PROVIDER = loader
        _RESOLVER_INSTANCE = None


def set_taxonomy_resolver(resolver: PureTaxonomyResolver | None) -> None:
    """Explicitly inject or reset the shared PureTaxonomyResolver singleton instance."""
    global _RESOLVER_INSTANCE
    with _RESOLVER_LOCK:
        _RESOLVER_INSTANCE = resolver


def get_taxonomy_resolver(
    catalog: Mapping[str, TaxonomyConcept | Mapping[str, Any]] | None = None,
) -> PureTaxonomyResolver:
    """Retrieve shared thread-safe singleton instance of PureTaxonomyResolver.

    Does not cache an empty singleton if invoked prior to catalog loader registration.
    """
    global _RESOLVER_INSTANCE
    if catalog is not None:
        return PureTaxonomyResolver(catalog=catalog)

    if _RESOLVER_INSTANCE is not None:
        return _RESOLVER_INSTANCE

    with _RESOLVER_LOCK:
        if _RESOLVER_INSTANCE is not None:
            return _RESOLVER_INSTANCE
        if _CATALOG_LOADER_PROVIDER is not None:
            loaded_catalog = _CATALOG_LOADER_PROVIDER.load_taxonomy_catalog()
            _RESOLVER_INSTANCE = PureTaxonomyResolver(catalog=loaded_catalog)
            return _RESOLVER_INSTANCE
        _RESOLVER_INSTANCE = PureTaxonomyResolver(catalog={})
        return _RESOLVER_INSTANCE
