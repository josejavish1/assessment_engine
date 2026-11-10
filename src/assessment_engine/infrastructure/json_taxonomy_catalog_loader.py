"""Infrastructure adapter loading canonical multilingual taxonomy catalog."""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Any, Mapping

from assessment_engine.domain.taxonomy_resolver import TaxonomyCatalogLoaderPort


class JsonTaxonomyCatalogLoader(TaxonomyCatalogLoaderPort):
    """Thread-safe infrastructure adapter loading the canonical multilingual taxonomy catalog."""

    _lock = threading.RLock()
    _cached_catalog: dict[str, Any] | None = None
    _cached_kpis: dict[str, dict[str, str]] | None = None

    def __init__(self, catalog_path: Path | None = None) -> None:
        if catalog_path is None:
            repo_root = Path(__file__).resolve().parents[3]
            catalog_path = repo_root / "engine_config" / "taxonomy_multilingual.json"
        self._catalog_path = catalog_path

    def load_taxonomy_catalog(self) -> Mapping[str, Any]:
        """Load and parse the multilingual taxonomy JSON catalog."""
        with self._lock:
            if self.__class__._cached_catalog is not None:
                return self.__class__._cached_catalog

            if not self._catalog_path.is_file():
                raise FileNotFoundError(
                    f"Canonical multilingual taxonomy catalog not found at: {self._catalog_path}"
                )

            with self._catalog_path.open("r", encoding="utf-8-sig") as fh:
                raw_data: dict[str, Any] = json.load(fh)

            self.__class__._cached_catalog = raw_data
            return raw_data

    def load_leaf_kpis_index(self) -> Mapping[str, Mapping[str, str]]:
        """Loads and caches the index of leaf KPI definitions across all domain towers."""
        with self._lock:
            if self.__class__._cached_kpis is not None:
                return self.__class__._cached_kpis

            kpis: dict[str, dict[str, str]] = {}

            # 1. Load rich multilingual translations from taxonomy_multilingual.json
            raw_catalog = self.load_taxonomy_catalog()
            for t_code, t_val in raw_catalog.items():
                if isinstance(t_val, dict):
                    for p_code, p_val in t_val.get("pillars", {}).items():
                        if isinstance(p_val, dict):
                            for k_code, k_val in p_val.get("kpis", {}).items():
                                if isinstance(k_val, dict):
                                    k_id_clean = k_code.strip().upper()
                                    k_locales = dict(k_val.get("locales", {}))
                                    k_locales["canonical"] = k_val.get("canonical_name", "")
                                    k_locales["pillar_id"] = p_code.strip().upper()
                                    kpis[k_id_clean] = k_locales

            # 2. Index definitions from tower_definition_*.json for missing entries
            repo_root = self._catalog_path.parents[1]
            towers_dir = repo_root / "engine_config" / "towers"
            if towers_dir.is_dir():
                for t_dir in towers_dir.iterdir():
                    if t_dir.is_dir():
                        candidates = [
                            t_dir / f"tower_definition_{t_dir.name.upper()}.json",
                            t_dir / f"tower_definition_{t_dir.name.lower()}.json",
                            t_dir / f"tower_definition_{t_dir.name}.json",
                        ]
                        def_file = next((f for f in candidates if f.exists()), None)
                        if def_file is not None:
                            try:
                                with def_file.open("r", encoding="utf-8-sig") as fh:
                                    t_def = json.load(fh)
                                for p in t_def.get("pillars", []):
                                    p_id = str(p.get("pillar_id") or p.get("id") or "").strip().upper()
                                    for k in p.get("kpis", []):
                                        k_id = str(k.get("kpi_id") or "").strip().upper()
                                        k_name = str(k.get("kpi_name") or "").strip()
                                        if k_id and k_id not in kpis and k_name:
                                            kpis[k_id] = {
                                                "canonical": k_name,
                                                "en": k_name,
                                                "es": k_name,
                                                "pillar_id": p_id,
                                            }
                            except (json.JSONDecodeError, OSError):
                                _ = True  # Handled fallback

            self.__class__._cached_kpis = kpis
            return kpis
