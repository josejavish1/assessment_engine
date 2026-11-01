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

    def __init__(self, catalog_path: Path | None = None) -> None:
        if catalog_path is None:
            repo_root = Path(__file__).resolve().parents[3]
            catalog_path = repo_root / "engine_config" / "taxonomy_multilingual.json"
        self._catalog_path = catalog_path

    def load_taxonomy_catalog(self) -> Mapping[str, Any]:
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
