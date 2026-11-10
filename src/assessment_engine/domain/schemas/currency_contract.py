"""Declarative Currency Contract and Scale Parity Loader.

Loads the universal multi-tenant currency catalog and purchasing-power parity
multipliers from engine_config/currency_catalog.json, guaranteeing zero I/O side
effects inside core domain calibration modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

_REPO_ROOT = Path(__file__).resolve().parents[4]
_CURRENCY_CATALOG_PATH = _REPO_ROOT / "engine_config" / "currency_catalog.json"


def _load_currency_catalog() -> tuple[str, Mapping[str, float], Mapping[str, str]]:
    default_num = "USD"
    parities: dict[str, float] = {}
    symbols: dict[str, str] = {}
    if _CURRENCY_CATALOG_PATH.is_file():
        try:
            data = json.loads(_CURRENCY_CATALOG_PATH.read_text(encoding="utf-8"))
            default_num = data.get("default_numeraire", "USD")
            parities = data.get("currency_scale_parity", {})
            symbols = data.get("unambiguous_symbol_to_iso", {})
        except Exception:
            pass
    return default_num, MappingProxyType(parities), MappingProxyType(symbols)


DEFAULT_BASE_NUMERAIRE, CURRENCY_SCALE_PARITY, _UNAMBIGUOUS_SYMBOL_TO_ISO = _load_currency_catalog()
