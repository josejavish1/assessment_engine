from __future__ import annotations

import json
from pathlib import Path

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


def require_existing_group(
    candidate_groups: list[tuple[Path, ...]],
    *,
    skip_message: str,
) -> tuple[Path, ...]:
    for group in candidate_groups:
        if all(path.exists() for path in group):
            return group
    pytest.skip(skip_message, allow_module_level=True)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
