"""
Módulo runtime_paths.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def resolve_working_dir() -> Path:
    return ROOT / "working"


def resolve_tower_id(default: str = "T5") -> str:
    return os.environ.get("ASSESSMENT_TOWER_ID", default).strip() or default


def resolve_client_id(default: str = "generic_client") -> str:
    return os.environ.get("ASSESSMENT_CLIENT_ID", default).strip() or default


def resolve_client_dir(default_client: str = "generic_client") -> Path:
    return resolve_working_dir() / resolve_client_id(default_client)


def resolve_case_dir(default_client: str = "generic_client", default_tower: str = "T1") -> Path:
    override = os.environ.get("ASSESSMENT_CASE_DIR", "").strip()
    if override:
        return Path(override).resolve()
    return resolve_client_dir(default_client) / resolve_tower_id(default_tower)


def resolve_tower_definition_file(default_tower: str = "T5") -> Path:
    tower_id = resolve_tower_id(default_tower)
    return ROOT / "engine_config" / "towers" / tower_id / f"tower_definition_{tower_id}.json"
