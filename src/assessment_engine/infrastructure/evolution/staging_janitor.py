# core/evolution/staging_janitor.py

import asyncio
import logging
from pathlib import Path
import shutil
import time

logger = logging.getLogger("staging_janitor")

WORKSPACES_ROOT = Path("workspaces")
STAGING_DIR = WORKSPACES_ROOT / ".staging"


def get_staging_dir() -> Path:
    """Return and ensure existence of staging root directory."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return STAGING_DIR


def _is_expired_dir(item: Path, max_age_seconds: float, now: float) -> bool:
    """Check whether directory modification time exceeds TTL threshold."""
    try:
        return (now - item.stat().st_mtime) > max_age_seconds
    except OSError:
        return False


def purge_expired_staging_workspaces(
    max_age_hours: int = 48, staging_path: Path | None = None
) -> int:
    """Scan and purge staging directories exceeding max_age_hours TTL."""
    target_dir = staging_path or get_staging_dir()
    if not target_dir.exists():
        return 0

    now = time.time()
    max_age_seconds = max_age_hours * 3600
    purged_count = 0

    for item in target_dir.iterdir():
        if item.is_dir() and _is_expired_dir(item, max_age_seconds, now):
            shutil.rmtree(item, ignore_errors=True)
            purged_count += 1
            logger.info(f"[StagingJanitor] Purged expired staging workspace: {item.name}")

    return purged_count


def promote_staging_workspace(staging_id: str, final_workspace_dir: Path) -> bool:
    """Promote staging workspace to production destination via atomic directory move."""
    staging_path = get_staging_dir() / staging_id
    if not staging_path.exists() or not staging_path.is_dir():
        return False

    try:
        if final_workspace_dir.exists():
            shutil.rmtree(final_workspace_dir, ignore_errors=True)
        shutil.move(str(staging_path), str(final_workspace_dir))
        logger.info(f"[StagingJanitor] Atomic promotion: {staging_id} -> {final_workspace_dir.name}")
        return True
    except Exception as ex:
        logger.warning(f"[StagingJanitor] Failed atomic promotion of {staging_id}: {ex}")
        return False


def scan_and_revalidate_stale_epistemic_cache(max_age_days: int = 180) -> int:
    """Scan epistemic cache for stale entries exceeding age threshold for SWR refresh."""
    import sqlite3
    db_path = Path("storage/data/epistemic_cache.db")
    if not db_path.exists():
        return 0

    max_age_seconds = max_age_days * 86400.0
    now = time.time()
    stale_count = 0

    try:
        with sqlite3.connect(str(db_path), timeout=5.0) as conn:
            cur = conn.cursor()
            cur.execute("SELECT cache_key, task, sector, cached_at FROM epistemic_cache")
            rows = cur.fetchall()
            for row in rows:
                k, task, sector, cached_at = row
                if (now - float(cached_at)) > max_age_seconds:
                    stale_count += 1
                    logger.info(f"[StagingJanitor] Stale SWR entry detected: '{task[:30]}' ({sector})")
    except Exception as ex:
        logger.debug(f"[StagingJanitor] Note on SWR scan of epistemic_cache: {ex}")

    return stale_count


async def start_staging_janitor_loop(
    interval_seconds: int = 3600, max_age_hours: int = 48
) -> None:
    """Execute continuous background Janitor loop at specified interval."""
    logger.info(f"[StagingJanitor] Janitor daemon started (Interval: {interval_seconds}s, TTL: {max_age_hours}h)")
    while True:
        try:
            purge_expired_staging_workspaces(max_age_hours=max_age_hours)
            scan_and_revalidate_stale_epistemic_cache(max_age_days=180)
        except Exception as ex:
            logger.debug(f"[StagingJanitor] Loop exception note: {ex}")
        await asyncio.sleep(interval_seconds)
