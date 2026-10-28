"""
Tombstone Context Condenser Primitive (Tier-1 Infinite-Horizon Session Engine).
Inspired by OpenHands SDK & Anthropic long-horizon agent execution models.
Compresses multi-step execution traces into structured append-only tombstones
without breaking Vertex AI prefix prompt caching (keep_first=2 invariant).
Maintains exact state tracking: USER_CONTEXT, CURRENT_STATE, CODE_CHANGES, TESTS_FAILING, PENDING_TASKS.
Hardened against circular structures, malformed events, and token overflow.
"""

from __future__ import annotations

import copy
import json
import logging
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.context_condenser")

MAX_TOMBSTONE_TEXT_CHARS = 4000
MAX_EVENTS_LIMIT = 500


class ContextCondenser:
    """Condense context for long-horizon autonomous engineering tasks. Prevent context rot by reducing history token usage to ~30-35%. Guard against non-serializable types, circular references, and overflows."""

    def __init__(self, keep_first: int = 2, keep_last: int = 5, trigger_threshold: int = 12) -> None:
        self.keep_first = max(0, keep_first)
        self.keep_last = max(1, keep_last)
        self.trigger_threshold = max(self.keep_first + self.keep_last + 1, trigger_threshold)

    def estimate_tokens(self, data: Any) -> int:
        """Estimate tokens deterministically using a heuristic of ~4 characters per token. Provide fail-safe JSON serialization handling."""
        if isinstance(data, str):
            return max(1, len(data) // 4)
        if isinstance(data, (dict, list)):
            try:
                dumped = json.dumps(data, ensure_ascii=False, default=str)
                return max(1, len(dumped) // 4)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError):# noqa: BLE001
                return max(1, len(str(data)) // 4)
        return 1

    def _process_call_item(
        self, call_dict: dict[str, Any], tools_invoked: list[str], code_changes: list[str]
    ) -> None:
        """Extract the tool name and modified files from a tool call."""
        c_name = str(call_dict.get("name", ""))[:50]
        args = call_dict.get("args", {})
        tools_invoked.append(c_name)
        if c_name in ["replace", "write_file"] and isinstance(args, dict):
            p = str(args.get("file_path", ""))[:200]
            if p and p not in code_changes:
                code_changes.append(p)

    def _process_string_content(
        self, content: str, role: Any, tests_failing: list[str], user_context_snippets: list[str]
    ) -> None:
        """Parse plain text events to extract stack traces and context."""
        if any(err in content for err in ["FAILED", "ERROR", "Traceback"]):
            tests_failing.append(content[:120].strip())
        if role == "user":
            user_context_snippets.append(content[:120].strip())

    def _process_response_item(self, resp_dict: dict[str, Any], tests_failing: list[str]) -> None:
        """Extract execution errors and assertion failures from a tool response."""
        resp = str(resp_dict.get("response", ""))[:200]
        if any(err in resp for err in ["FAILED", "AssertionError", "Exit Code", "Error:"]):
            tests_failing.append(resp.strip())

    def _process_single_content_item(
        self,
        item: dict[str, Any],
        role: Any,
        tools_invoked: list[str],
        code_changes: list[str],
        tests_failing: list[str],
        user_context_snippets: list[str]
    ) -> None:
        """Process an individual entry within an event content list."""
        call_data = item.get("call")
        if isinstance(call_data, dict):
            self._process_call_item(call_data, tools_invoked, code_changes)
            return

        fn_resp = item.get("functionResponse")
        if isinstance(fn_resp, dict):
            self._process_response_item(fn_resp, tests_failing)
            return

        if "text" in item and role == "user":
            user_context_snippets.append(str(item["text"])[:120])

    def _process_event_content(
        self,
        content: Any,
        role: Any,
        tools_invoked: list[str],
        code_changes: list[str],
        tests_failing: list[str],
        user_context_snippets: list[str]
    ) -> None:
        """Parse the content of an individual event to condense traces and failures."""
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    self._process_single_content_item(
                        item, role, tools_invoked, code_changes, tests_failing, user_context_snippets
                    )
        elif isinstance(content, str):
            self._process_string_content(content, role, tests_failing, user_context_snippets)

    def create_tombstone(
        self,
        intermediate_events: list[dict[str, Any]],
        tombstone_index_range: tuple[int, int]
    ) -> dict[str, Any]:
        """Create a structured tombstone event summarizing intermediate steps. Enforce strict text bounds to prevent memory leaks."""
        code_changes: list[str] = []
        tests_failing: list[str] = []
        user_context_snippets: list[str] = []
        tools_invoked: list[str] = []

        for ev in intermediate_events:
            if isinstance(ev, dict):
                self._process_event_content(
                    ev.get("content"),
                    ev.get("role"),
                    tools_invoked,
                    code_changes,
                    tests_failing,
                    user_context_snippets
                )

        tombstone_summary = {
            "tombstone_type": "TOMBSTONE_COMPACTED_HISTORY",
            "index_range": list(tombstone_index_range),
            "events_compacted": len(intermediate_events),
            "tools_invoked_count": len(tools_invoked),
            "USER_CONTEXT": " | ".join(user_context_snippets[-2:])[:300] if user_context_snippets else "Misión de evolución en curso",
            "CURRENT_STATE": f"Ciclos {tombstone_index_range[0]} a {tombstone_index_range[1]} completados con {len(code_changes)} modificaciones de código.",
            "CODE_CHANGES": code_changes[:20],
            "TESTS_FAILING": tests_failing[-3:] if tests_failing else [],
            "PENDING_TASKS": ["Validar build y suite de tests", "Continuar con la directiva actual"]
        }

        compact_text = (
            f"[TOMBSTONE HISTORIAL CONDENSADO: Eventos #{tombstone_index_range[0]} a #{tombstone_index_range[1]}]\n"
            f"USER_CONTEXT: {tombstone_summary['USER_CONTEXT']}\n"
            f"CURRENT_STATE: {tombstone_summary['CURRENT_STATE']}\n"
            f"ARCHIVOS MODIFICADOS: {', '.join(code_changes[:10]) if code_changes else 'Ninguno'}\n"
            f"ÚLTIMOS FALLOS ATENDIDOS: {len(tests_failing)}\n"
            "PENDING_TASKS: Mantener invariantes y ejecutar siguiente ciclo."
        )[:MAX_TOMBSTONE_TEXT_CHARS]

        return {
            "role": "user",
            "type": "tombstone_event",
            "content": [
                {
                    "text": compact_text
                }
            ],
            "_tombstone_meta": tombstone_summary
        }

    def condense(
        self,
        events: list[dict[str, Any]],
        max_events: int | None = None,
        keep_first: int | None = None,
        keep_last: int | None = None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Condense the event list if it exceeds trigger_threshold. Retain strictly:
- First N events (keep_first=2: root directive and ontology to optimize Vertex AI cache)
- Last M events (keep_last=5: immediate context and active turns) Replace the middle segment with a structured tombstone."""
        if not isinstance(events, list):
            return [], {"condensed": False, "error": "events must be a list"}

        # Cap size for safety
        events = events[:MAX_EVENTS_LIMIT]

        k_first = max(0, keep_first if keep_first is not None else self.keep_first)
        k_last = max(1, keep_last if keep_last is not None else self.keep_last)
        threshold = max_events if max_events is not None else self.trigger_threshold

        total_count = len(events)
        initial_tokens = self.estimate_tokens(events)

        if total_count <= threshold or total_count <= (k_first + k_last):
            return copy.deepcopy(events), {
                "condensed": False,
                "initial_events": total_count,
                "final_events": total_count,
                "initial_tokens": initial_tokens,
                "final_tokens": initial_tokens,
                "token_ratio": 1.0
            }

        head = copy.deepcopy(events[:k_first])

        # 2. Extract middle section for tombstone
        intermediate = events[k_first:-k_last]
        tombstone_range = (k_first, total_count - k_last - 1)
        tombstone = self.create_tombstone(intermediate, tombstone_range)

        # 3. Preservar cola reciente (keep_last)
        tail = copy.deepcopy(events[-k_last:])

        condensed_events = head + [tombstone] + tail
        final_tokens = self.estimate_tokens(condensed_events)
        ratio = round(final_tokens / max(1, initial_tokens), 4)

        stats = {
            "condensed": True,
            "initial_events": total_count,
            "final_events": len(condensed_events),
            "events_pruned": len(intermediate),
            "initial_tokens": initial_tokens,
            "final_tokens": final_tokens,
            "token_ratio": ratio,
            "tokens_saved_percent": round((1.0 - ratio) * 100, 2)
        }

        logger.info(
            f"[ContextCondenser] Eventos condensados: {total_count} -> {len(condensed_events)} "
            f"({stats['tokens_saved_percent']}% tokens ahorrados)"
        )

        return condensed_events, stats


context_condenser = ContextCondenser()
