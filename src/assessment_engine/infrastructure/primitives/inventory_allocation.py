"""
Inventory & Allocation Primitive — GEMA 04 / Radar Primitive 4 (Ticketmaster & DICE Pattern / SOTA 2026).
Engine for atomic seat, capacity, and resource allocations with ephemeral Lease Holds (10-minute TTL).
Enforces strict anti-overbooking mathematical guarantees in high-concurrency environments.
Domain-agnostic: reserves surgery operating theaters, padel courts, event tickets, or hotel beds.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.inventory_allocation")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))


@dataclass
class AllocationResult:
    success: bool
    hold_id: str | None
    resource_id: str
    quantity: int
    expires_at: float | None
    error_reason: str | None = None


class InventoryAllocationPrimitive:
    """
    Implement atomic inventory locking with leases and TTL.
    """

    DEFAULT_HOLD_TTL_SECONDS = 600  # Allow 10 minutes to complete checkout.

    def __init__(self, workspaces_dir: Path | None = None) -> None:
        self.workspaces_dir = workspaces_dir or WORKSPACES_DIR

    def _get_db(self, slug: str) -> sqlite3.Connection:
        db_path = self.workspaces_dir / slug / "app.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory_resources (
                resource_id TEXT PRIMARY KEY,
                total_capacity INT NOT NULL,
                name TEXT NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory_holds (
                hold_id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL REFERENCES inventory_resources(resource_id),
                user_id TEXT NOT NULL,
                quantity INT NOT NULL,
                status TEXT NOT NULL, -- 'HELD', 'CONFIRMED', 'RELEASED'
                expires_at REAL NOT NULL,
                created_at REAL NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        return conn

    def set_resource_capacity(self, slug: str, resource_id: str, total_capacity: int, name: str = "") -> None:
        """Initialize or update the total capacity of a physical or digital resource."""
        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO inventory_resources (resource_id, total_capacity, name)
                VALUES (?, ?, ?)
                ON CONFLICT(resource_id) DO UPDATE SET
                    total_capacity=excluded.total_capacity,
                    name=excluded.name;
            """, (resource_id, total_capacity, name or resource_id))
            conn.commit()
        finally:
            conn.close()

    def acquire_hold(
        self,
        slug: str,
        resource_id: str,
        quantity: int,
        user_id: str,
        ttl_seconds: int | None = None
    ) -> AllocationResult:
        """Atomically lock the requested amount with an expiration TTL.
If the remaining capacity is insufficient, deterministically deny the lock."""
        if quantity <= 0:
            return AllocationResult(False, None, resource_id, 0, None, "Cantidad inválida")

        now = time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self.DEFAULT_HOLD_TTL_SECONDS
        expires_at = now + ttl
        hold_id = f"HLD-{uuid.uuid4().hex[:10].upper()}"

        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE;")

            # 0. Atomically sweep expired reservations before evaluating available capacity.
            cur.execute("""
                UPDATE inventory_holds
                SET status = 'RELEASED'
                WHERE status = 'HELD' AND expires_at <= ?;
            """, (now,))

            cur.execute("SELECT total_capacity FROM inventory_resources WHERE resource_id = ?;", (resource_id,))
            res_row = cur.fetchone()
            if not res_row:
                conn.rollback()
                return AllocationResult(False, None, resource_id, quantity, None, "Recurso no encontrado")

            total_cap = res_row["total_capacity"]

            # 2. Calculate active seats (CONFIRMED or unexpired HELD).
            cur.execute("""
                SELECT COALESCE(SUM(quantity), 0) as occupied
                FROM inventory_holds
                WHERE resource_id = ?
                  AND (status = 'CONFIRMED' OR (status = 'HELD' AND expires_at > ?));
            """, (resource_id, now))
            occupied = cur.fetchone()["occupied"]

            available = total_cap - occupied
            if available < quantity:
                conn.rollback()
                logger.warning(f"[{slug}] Overbooking evitado en '{resource_id}': Disponibles {available}, solicitadas {quantity}")
                return AllocationResult(
                    False, None, resource_id, quantity, None,
                    f"Aforo completo o insuficiente. Plazas disponibles: {available}"
                )

            cur.execute("""
                INSERT INTO inventory_holds (hold_id, resource_id, user_id, quantity, status, expires_at, created_at)
                VALUES (?, ?, ?, ?, 'HELD', ?, ?);
            """, (hold_id, resource_id, user_id, quantity, expires_at, now))

            conn.commit()
            logger.info(f"[{slug}] Bloqueo #{hold_id} adquirido: {quantity} plazas en '{resource_id}' (Expira en {ttl}s)")
            return AllocationResult(True, hold_id, resource_id, quantity, expires_at)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            conn.rollback()
            logger.error(f"[{slug}] Error en asignación atómica: {ex}")
            return AllocationResult(False, None, resource_id, quantity, None, str(ex))
        finally:
            conn.close()

    def confirm_hold(self, slug: str, hold_id: str) -> bool:
        """Promote a temporary hold to confirmed status upon payment."""
        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory_holds
                SET status = 'CONFIRMED'
                WHERE hold_id = ? AND status = 'HELD';
            """, (hold_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def release_hold(self, slug: str, hold_id: str) -> bool:
        """Release a reservation voluntarily before its TTL expires."""
        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory_holds
                SET status = 'RELEASED'
                WHERE hold_id = ? AND status = 'HELD';
            """, (hold_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def sweep_expired_holds(self, slug: str) -> int:
        """Purge expired locks and return capacity to the pool."""
        now = time.time()
        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory_holds
                SET status = 'RELEASED'
                WHERE status = 'HELD' AND expires_at <= ?;
            """, (now,))
            conn.commit()
            purged = cur.rowcount
            if purged > 0:
                logger.info(f"[{slug}] Liberadas {purged} plazas expiradas por TTL.")
            return purged
        finally:
            conn.close()


inventory_allocation = InventoryAllocationPrimitive()
