"""Integration test suite for quantitative SSOT and mathematical invariants.

Validates that for all on-disk tower payloads, sum_product(pillars.score, pillars.weight) == tower.score
within strict floating-point quantization tolerances across any topology.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import pytest

from assessment_engine.domain.validation.mathematical_integrity import (
    assert_tower_mathematical_integrity,
)

EXCLUDED_DIR_NAMES = frozenset({"out", "backup", "backups", "baseline", "shadow", "pre_argon", "pre_rebuild"})
EXCLUDED_DIR_PREFIXES = ("backup_", "baseline_", "shadow_", "pre_argon_", "pre_rebuild_")
EXCLUDED_DIR_SUFFIXES = ("_backup", "_backups", "_baseline", "_legacy", "_old", "_archive")


def _is_excluded_path(relative_parts: Tuple[str, ...]) -> bool:
    """Checks directory tokens relative to working/ using exact token, prefix, and suffix matching.

    Prevents false-positive substring exclusions (e.g. 'out' matching 'rollout' or 'south').
    """
    for part in relative_parts[:-1]:
        lower_part = part.lower()
        if (
            lower_part in EXCLUDED_DIR_NAMES
            or lower_part.startswith(EXCLUDED_DIR_PREFIXES)
            or lower_part.endswith(EXCLUDED_DIR_SUFFIXES)
        ):
            return True
    return False


def get_all_active_tower_payloads() -> List[Tuple[str, Path]]:
    """Discovers all active blueprint tower payloads under working/ directory,

    ignoring legacy out/, backup, and snapshot directories.
    """
    repo_root = Path(__file__).resolve().parents[2]
    working_dir = repo_root / "working"
    if not working_dir.exists():
        return []

    discovered: List[Tuple[str, Path]] = []
    for payload_path in sorted(working_dir.rglob("blueprint_*_payload.json")):
        rel_parts = payload_path.relative_to(working_dir).parts
        if _is_excluded_path(rel_parts):
            continue
        try:
            with open(payload_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict) or not data.get("pillars_analysis"):
                continue
        except Exception:
            continue
        tower_code = payload_path.stem.replace("blueprint_", "").replace("_payload", "").upper()
        discovered.append((f"{payload_path.parent.name}/{tower_code}", payload_path))

    return discovered


ACTIVE_PAYLOADS = get_all_active_tower_payloads()


def test_active_payloads_discovery_guard() -> None:
    """Verifies active payloads were discovered or skips gracefully if clean environment."""
    if not ACTIVE_PAYLOADS:
        pytest.skip("No active tenant payloads discovered under working/ directory.")


@pytest.mark.skipif(len(ACTIVE_PAYLOADS) == 0, reason="No active payloads in working/")
@pytest.mark.parametrize(
    "label,payload_path",
    ACTIVE_PAYLOADS if ACTIVE_PAYLOADS else [("EMPTY_FIXTURE", Path("/dev/null"))],
)
def test_tower_payload_dot_product_invariant(label: str, payload_path: Path) -> None:
    """Guarantees that for every active tower payload:

    sum_product(pillars.score, pillars.weight) == tower.score.
    """
    if label == "EMPTY_FIXTURE":
        pytest.skip("No active tenant payloads to evaluate in clean environment.")

    with open(payload_path, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)

    assert_tower_mathematical_integrity(payload)
