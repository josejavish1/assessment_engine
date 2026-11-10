"""Infrastructure loader for actuarial taxonomy archetypes (Hexagonal Architecture).

Encapsulates filesystem I/O for engine_config/taxonomy_actuarial_archetypes.json,
preserving purity in domain/taxonomy/archetype_registry.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_raw_actuarial_archetypes() -> Dict[str, Any]:
    """Loads raw json dict from engine_config/taxonomy_actuarial_archetypes.json."""
    repo_root = Path(__file__).resolve().parents[3]
    config_path = repo_root / "engine_config" / "taxonomy_actuarial_archetypes.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Actuarial archetypes configuration not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
