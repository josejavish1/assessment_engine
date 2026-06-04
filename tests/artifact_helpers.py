from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]


def require_artifact(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"Missing artifact: {path}")
    return path


def require_artifact_es(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"No se encontró el artefacto: {path}")
    return path


def load_json(path: Path) -> Dict[str, Any]:
    return cast(Dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))
