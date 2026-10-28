"""
Provide keyset cursor pagination inspired by Stripe and Relay GraphQL specifications. Ensures three core capabilities:
1. O(1) query seek on indexed B-Trees without offset scanning.
2. Immunity to concurrency drift and phantom rows.
3. Stripe-style range filters and advanced operators (__gte, __lte, __like, __eq).
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.cursor_paginator")


@dataclass(frozen=True)
class KeysetPage:
    """Represent a paginated response container conforming to the Stripe standard."""
    data: list[dict[str, Any]]
    has_more: bool
    next_cursor: str | None
    prev_cursor: str | None
    limit: int


class CursorPaginator(CapabilityPrimitive):
    """
    Compile and execute indexed keyset cursor pagination.
    """

    @property
    def namespace(self) -> str:
        """Return the namespace."""
        return "cursor_paginator"

    def get_capabilities(self) -> dict[str, Any]:
        """Retrieve the supported capabilities."""
        return {
            "version": "4.0.0",
            "operations": [
                "encode_cursor",
                "decode_cursor",
                "compile_keyset_predicate",
                "compile_range_filters",
                "paginate_records"
            ],
            "standards": [
                "Stripe Keyset Pagination API Spec",
                "Stripe Advanced Range Filter Syntax (__gte, __lte, __like)",
                "Relay Cursor Connection Spec",
                "O(1) B-Tree Lexicographical Tuple Comparison"
            ]
        }

    @staticmethod
    def encode_cursor(record_id: str, sort_value: Any) -> str:
        """Serialize a cursor anchor point into an opaque Base64 string."""
        raw = json.dumps({"id": str(record_id), "v": sort_value}, ensure_ascii=False)
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decode_cursor(cursor_str: str | None) -> tuple[str, Any] | None:
        """Decode a Base64 cursor to extract the ID and sort value."""
        if not cursor_str or not cursor_str.strip():
            return None
        try:
            raw = base64.urlsafe_b64decode(cursor_str.strip().encode("utf-8")).decode("utf-8")
            data = json.loads(raw)
            if isinstance(data, dict) and "id" in data and "v" in data:
                return str(data["id"]), data["v"]
        except (ValueError, json.JSONDecodeError, KeyError):
            pass
        return None

    def compile_keyset_predicate(
        self,
        sort_column: str = "created_at",
        id_column: str = "id",
        order: str = "desc",
        starting_after: str | None = None,
        ending_before: str | None = None
    ) -> tuple[str, list[Any]]:
        """Compile the O(1) lexicographical SQL predicate based on the directional cursor.
Cyclomatic complexity in Rank A (V(G) <= 6)."""
        s_col = f'"{sort_column}"'
        i_col = f'"{id_column}"'
        order_upper = order.upper().strip()

        cursor_data = self.decode_cursor(starting_after)
        if cursor_data:
            c_id, c_val = cursor_data
            if order_upper == "DESC":
                pred = f"({s_col} < ? OR ({s_col} = ? AND {i_col} < ?))"
            else:
                pred = f"({s_col} > ? OR ({s_col} = ? AND {i_col} > ?))"
            return pred, [c_val, c_val, c_id]

        cursor_data = self.decode_cursor(ending_before)
        if cursor_data:
            c_id, c_val = cursor_data
            if order_upper == "DESC":
                pred = f"({s_col} > ? OR ({s_col} = ? AND {i_col} > ?))"
            else:
                pred = f"({s_col} < ? OR ({s_col} = ? AND {i_col} < ?))"
            return pred, [c_val, c_val, c_id]

        return "", []

    @staticmethod
    def compile_range_filters(
        query_params: dict[str, Any],
        allowed_columns: set[str],
        reserved_keys: set[str] | None = None
    ) -> tuple[str, list[Any]]:
        """Compile Stripe / Django ORM-style range operators:
- col__gte: >=
- col__lte: <=
- col__gt: >
- col__lt: <
- col__like: LIKE %val%
- col__ne: !=
- col or col__eq: ="""
        reserved = reserved_keys or {
            "limit", "offset", "starting_after", "ending_before",
            "order_by", "order", "envelope", "format"
        }
        clauses: list[str] = []
        params: list[Any] = []
        op_map = {
            "gte": ">=", "lte": "<=", "gt": ">", "lt": "<",
            "ne": "!=", "not": "!=", "eq": "="
        }

        for key, val in query_params.items():
            if key in reserved or val is None or val == "":
                continue

            op = "="
            col_name = key
            val_to_use = val

            if "__" in key:
                parts = key.split("__", 1)
                col_name = parts[0]
                modifier = parts[1].lower()
                
                if modifier in ("like", "contains"):
                    op = "LIKE"
                    val_to_use = f"%{val}%"
                else:
                    op = op_map.get(modifier, "=")

            if col_name in allowed_columns:
                clauses.append(f'"{col_name}" {op} ?')
                params.append(val_to_use)

        if not clauses:
            return "", []

        return " AND ".join(clauses), params

    def paginate_records(
        self,
        items: list[dict[str, Any]],
        limit: int,
        sort_column: str = "created_at",
        id_column: str = "id"
    ) -> KeysetPage:
        """Wrap the list of retrieved records by determining has_more and constructing safe boundary cursors."""
        has_more = len(items) > limit
        paged_items = items[:limit]

        next_cursor = None
        prev_cursor = None

        if paged_items:
            last_item = paged_items[-1]
            last_id = str(last_item.get(id_column, ""))
            last_val = last_item.get(sort_column, last_id)
            if has_more:
                next_cursor = self.encode_cursor(last_id, last_val)

            first_item = paged_items[0]
            first_id = str(first_item.get(id_column, ""))
            first_val = first_item.get(sort_column, first_id)
            prev_cursor = self.encode_cursor(first_id, first_val)

        return KeysetPage(
            data=paged_items,
            has_more=has_more,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            limit=limit
        )


cursor_paginator = CursorPaginator()
