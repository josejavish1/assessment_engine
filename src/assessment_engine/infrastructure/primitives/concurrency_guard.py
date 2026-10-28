"""
Implement Optimistic Concurrency Control (OCC) per RFC 7232. Provide three core capabilities for REST API integrity and performance:
1. Prevent lost updates using ETag and If-Match (HTTP 412 Precondition Failed).
2. Minimize bandwidth and latency using If-None-Match (HTTP 304 Not Modified).
3. Perform field-level 3-way auto-merging for non-conflicting concurrent changes.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.concurrency_guard")


class ConcurrencyGuardPrimitive(CapabilityPrimitive):
    """
    Compile and validate RFC 7232 HTTP preconditions (ETags / OCC) with 3-way field auto-merging.
    """

    @property
    def namespace(self) -> str:
        """Return the namespace."""
        return "concurrency_guard"

    def get_capabilities(self) -> dict[str, Any]:
        """Retrieve the supported capabilities."""
        return {
            "version": "4.2.0",
            "operations": [
                "compute_etag",
                "validate_if_match",
                "validate_if_none_match",
                "try_field_level_merge"
            ],
            "standards": [
                "RFC 7232 HTTP Conditional Requests",
                "Optimistic Concurrency Control (OCC)",
                "HTTP 412 Precondition Failed",
                "HTTP 304 Not Modified",
                "Field-Level 3-Way Non-Conflicting Auto-Merge"
            ]
        }

    @staticmethod
    def _clean_etag_string(tag: str | None) -> str:
        """Strip weak validator prefixes ('W/') and quotes for canonical comparison."""
        if not tag:
            return ""
        cleaned = tag.strip()
        if cleaned.startswith("W/"):
            cleaned = cleaned[2:]
        return cleaned.strip('"')

    @classmethod
    def compute_etag(cls, record: dict[str, Any]) -> str:
        """Compute the RFC 7232 weak cryptographic ETag over the canonical state of the resource.
Any change to any field deterministically alters the hash."""
        if not record or not isinstance(record, dict):
            return 'W/"empty"'

        canonical_str = json.dumps(record, sort_keys=True, ensure_ascii=False)
        hash_digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()[:16]
        return f'W/"{hash_digest}"'

    @classmethod
    def validate_if_match(
        cls,
        current_record: dict[str, Any],
        if_match_header: str | None
    ) -> tuple[bool, str]:
        """Evaluate the If-Match header.
Return (True, 'MATCH') if the version matches or if the header is absent.
Return (False, 'ETAG_MISMATCH') if the record was concurrently modified."""
        if not if_match_header or not if_match_header.strip():
            # Allow standard mutation if If-Match is omitted.
            return True, "NO_HEADER"

        clean_header = cls._clean_etag_string(if_match_header)
        if clean_header == "*":
            return True, "WILDCARD_MATCH"

        current_etag = cls._clean_etag_string(cls.compute_etag(current_record))
        if clean_header == current_etag:
            return True, "MATCH"

        return False, "ETAG_MISMATCH"

    @classmethod
    def validate_if_none_match(
        cls,
        current_record: dict[str, Any],
        if_none_match_header: str | None
    ) -> bool:
        """Evaluate the If-None-Match header to determine whether the client already has a fresh version.
Return True if the resource has not changed (triggers HTTP 304 Not Modified)."""
        if not if_none_match_header or not if_none_match_header.strip():
            return False

        clean_header = cls._clean_etag_string(if_none_match_header)
        current_etag = cls._clean_etag_string(cls.compute_etag(current_record))

        return clean_header == current_etag or clean_header == "*"

    @staticmethod
    def _compute_state_changes(new_state: dict[str, Any], base_state: dict[str, Any], ignored: set[str]) -> dict[str, Any]:
        changes = {}
        for k, v in new_state.items():
            if k in ignored: continue
            if v != base_state.get(k):
                changes[k] = v
        return changes

    @classmethod
    def try_field_level_merge(
        cls,
        current_record: dict[str, Any],
        incoming_updates: dict[str, Any],
        base_snapshot: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any], list[str]]:
        """Perform a 3-way non-conflicting field-level auto-merge.
Evaluate whether the incoming mutation collides with concurrent database changes.
Automatically merge changes if disjoint fields were modified.
Report conflicts if the same field was modified with incompatible values.
Return (success, merged_record, conflicting_fields)."""
        if not base_snapshot or not isinstance(base_snapshot, dict):
            return False, current_record, list(incoming_updates.keys())

        ignored = {"id", "tenant_id", "created_at", "updated_at", "_base_snapshot"}
        user_changes = cls._compute_state_changes(incoming_updates, base_snapshot, ignored)
        db_changes = cls._compute_state_changes(current_record, base_snapshot, ignored)

        conflicts = [k for k in user_changes if k in db_changes and user_changes[k] != db_changes[k]]

        if conflicts:
            return False, current_record, conflicts

        merged = dict(current_record)
        merged.update(user_changes)
        return True, merged, []


concurrency_guard = ConcurrencyGuardPrimitive()
