"""Domain-safe resolution of configuration paths without infrastructure dependencies."""
from __future__ import annotations

import os
from pathlib import Path


def resolve_domain_engine_config_dir() -> Path:
    """Return the absolute path to the project's 'engine_config' directory.

    Prioritizes ENGINE_CONFIG_DIR environment variable if set, falling back
    to repository root / 'engine_config'.
    """
    env_dir = os.environ.get("ENGINE_CONFIG_DIR", "").strip()
    if env_dir:
        return Path(env_dir).resolve()
    return Path(__file__).resolve().parents[3] / "engine_config"


def resolve_domain_root_dir() -> Path:
    """Return the absolute path to the project's root repository directory."""
    env_dir = os.environ.get("REPO_ROOT", "").strip()
    if env_dir:
        return Path(env_dir).resolve()
    return Path(__file__).resolve().parents[3]
