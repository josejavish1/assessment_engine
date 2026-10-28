"""
Canonical Storage Resolution Helper (Google SOTA / Clean Architecture).
Resolves SQLite WAL databases and dynamic persistence artifacts into an isolated storage directory,
preventing root directory clutter while guaranteeing 100% backward compatibility.
"""
from __future__ import annotations

import os
from pathlib import Path

# Repo root directory
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STORAGE_DATA_DIR = _REPO_ROOT / "storage" / "data"


def resolve_db_path(db_name: str) -> Path:
    """
    Resolves the canonical path to an SQLite database file.
    Resolution priority:
    1. Environment variable {CLEAN_NAME}_PATH (e.g., SEATING_STATE_DB_PATH)
    2. STORAGE_DATA_DIR / db_name (canonical isolated location: storage/data/<name>.db)
    3. _REPO_ROOT / db_name (legacy fallback if file already exists in root)
    """
    env_var_name = db_name.upper().replace(".", "_").replace("-", "_") + "_PATH"
    env_path = os.getenv(env_var_name)
    if env_path:
        return Path(env_path).resolve()

    STORAGE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    canonical_path = STORAGE_DATA_DIR / db_name

    root_path = _REPO_ROOT / db_name
    if canonical_path.exists() or not root_path.exists():
        return canonical_path

    # Fallback to legacy root path only if it already exists there and canonical does not
    return root_path
