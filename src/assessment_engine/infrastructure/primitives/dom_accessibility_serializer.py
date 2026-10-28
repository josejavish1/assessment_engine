"""
DOM Accessibility Tree (AXTree) Serializer Primitive — SOTA 2026.
Inspired by browser-use/dom and Playwright Accessibility Tree architecture.
Serializes rich web UIs into compact, accessible semantic representations (<1,500 tokens)
with unique numeric indexing [1], [2], [3] for deterministic LLM agent interaction.
Prunes occluded/invisible nodes, suppresses decorative SVGs, and calculates interactive element maps.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.dom_accessibility_serializer")

INTERACTIVE_ROLES = {
    "button", "link", "textbox", "searchbox", "combobox", "checkbox",
    "radio", "tab", "menuitem", "switch", "slider", "option", "treeitem"
}

CONTAINER_ROLES = {
    "generic", "none", "presentation", "group", "region", "section"
}


MAX_NODES_LIMIT = 2000
MAX_NAME_CHARS = 200
ZERO_WIDTH_REGEX = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]")
INJECTION_REGEX = re.compile(r"(\[SYSTEM.*?\]|<<<SYSTEM.*?>>>|<\|im_.*?\|>)", re.IGNORECASE)


class DOMAccessibilitySerializer:
    """Serialize accessibility trees (AXTree) for agent arbitration and evaluation. Convert large HTML dumps (100-300 KB) into compact semantic trees (<2 KB). Guard against node-bomb DoS attacks and sanitize prompt injections."""

    def serialize_accessibility_snapshot(
        self,
        snapshot: dict[str, Any] | None,
        max_depth: int = 15
    ) -> dict[str, Any]:
        """Serialize an accessibility snapshot (Playwright page.accessibility.snapshot format). Generate a structured text representation with unique numerical indices [1], [2]."""
        if not snapshot or not isinstance(snapshot, dict):
            return {
                "tree_text": "(Árbol de accesibilidad vacío)",
                "interactive_elements": {},
                "total_interactive_count": 0,
                "token_estimate": 1,
                "raw_nodes_count": 0
            }

        lines: list[str] = []
        interactive_map: dict[int, dict[str, Any]] = {}
        counter = {"index": 1, "raw_nodes": 0}

        self._traverse_node(snapshot, lines, interactive_map, counter, depth=0, max_depth=max_depth)

        tree_text = "\n".join(lines).strip()
        token_estimate = max(1, len(tree_text) // 4)

        return {
            "tree_text": tree_text,
            "interactive_elements": interactive_map,
            "total_interactive_count": len(interactive_map),
            "token_estimate": token_estimate,
            "raw_nodes_count": counter["raw_nodes"]
        }

    async def serialize_page(
        self,
        page: Any,
        interesting_only: bool = True
    ) -> dict[str, Any]:
        """
        Extract and serialize the AXTree directly from an active Playwright page.
        """
        try:
            if hasattr(page, "accessibility") and page.accessibility is not None:
                snapshot = await page.accessibility.snapshot(interesting_only=interesting_only)
            else:
                snapshot = None
            content_html = await page.content()
            raw_html_bytes = len(content_html.encode("utf-8"))
        except (RuntimeError, ValueError, KeyError, OSError, TypeError, AttributeError) as ex:
            logger.debug(f"[AXTreeSerializer] Error obteniendo snapshot Playwright: {ex}")
            snapshot = None
            raw_html_bytes = 0

        res = self.serialize_accessibility_snapshot(snapshot)
        tree_bytes = len(res["tree_text"].encode("utf-8"))
        compression_ratio = 1.0 - (tree_bytes / max(1, raw_html_bytes)) if raw_html_bytes > 0 else 0.95

        res["raw_html_bytes"] = raw_html_bytes
        res["tree_bytes"] = tree_bytes
        res["compression_ratio"] = round(compression_ratio, 4)
        return res

    def _format_interactive_node(
        self,
        node: dict[str, Any],
        role: str,
        clean_name: str,
        value: Any,
        indent: str,
        counter: dict[str, int],
        interactive_map: dict[int, dict[str, Any]]
    ) -> str:
        """Format an interactive node ([1] button 'Submit') and record its accessible states."""
        idx = counter["index"]
        counter["index"] += 1

        states = [s for s in ["selected", "checked", "disabled", "expanded"] if node.get(s)]
        state_str = f" ({', '.join(states)})" if states else ""
        val_clean = str(value)[:100] if value is not None else ""
        val_str = f' value="{val_clean}"' if value is not None else ""

        interactive_map[idx] = {
            "index": idx,
            "role": role,
            "name": clean_name,
            "value": val_clean if value is not None else None,
            "states": states
        }
        return f'{indent}[{idx}] {role} "{clean_name}"{val_str}{state_str}'

    def _format_content_node(
        self,
        node: dict[str, Any],
        role: str,
        clean_name: str,
        indent: str
    ) -> str:
        """Format semantic content nodes (headings, text, images)."""
        if role.startswith("heading"):
            level = node.get("level", 1)
            return f'{indent}heading {level}: "{clean_name}"'
        if role in ["text", "paragraph", "article", "cell"] and len(clean_name) > 1:
            return f'{indent}{role}: "{clean_name}"'
        if role == "img" and clean_name:
            return f'{indent}img: "{clean_name}"'
        return ""

    def _traverse_node(
        self,
        node: dict[str, Any],
        lines: list[str],
        interactive_map: dict[int, dict[str, Any]],
        counter: dict[str, int],
        depth: int,
        max_depth: int
    ) -> None:
        """Recursively traverse accessibility nodes and extract interactive elements."""
        if depth > max_depth or not isinstance(node, dict) or counter["raw_nodes"] >= MAX_NODES_LIMIT:
            return

        counter["raw_nodes"] += 1
        role = str(node.get("role", "")).lower().strip()
        raw_name = str(node.get("name", "")).strip()
        value = node.get("value")
        children = node.get("children", [])

        # Sanitize invisible characters and injection delimiters in names.
        clean_name = ZERO_WIDTH_REGEX.sub("", raw_name)
        clean_name = INJECTION_REGEX.sub("[TEXTO_REDACTADO]", clean_name)
        clean_name = re.sub(r"\s+", " ", clean_name)[:MAX_NAME_CHARS]

        # Discard invisible, occluded, or generic nodes lacking semantic value.
        if role in CONTAINER_ROLES and not clean_name and not children:
            return

        indent = "  " * depth
        if role in INTERACTIVE_ROLES:
            line_str = self._format_interactive_node(node, role, clean_name, value, indent, counter, interactive_map)
        else:
            line_str = self._format_content_node(node, role, clean_name, indent)

        if line_str:
            lines.append(line_str)

        # Recorrer nodos hijos
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    self._traverse_node(child, lines, interactive_map, counter, depth + 1, max_depth)


dom_accessibility_serializer = DOMAccessibilitySerializer()
