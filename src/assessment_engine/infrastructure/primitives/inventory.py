"""
Canonical Capacity & Allocation Engine — System 06 (Ticketmaster / DICE SOTA 2026).
Consolidated high-concurrency seat, court, and resource allocation suite:
1. Ephemeral Lease Holds with 10-minute TTL.
2. Atomic transactions with BEGIN IMMEDIATE in SQLite WAL.
3. Automated auto-sweep of expired holds (zero capacity leaks).
4. Strict anti-overbooking mathematical guarantees.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.inventory_allocation import (
    InventoryAllocationPrimitive,
    AllocationResult,
    inventory_allocation
)

inventory_engine = inventory_allocation
