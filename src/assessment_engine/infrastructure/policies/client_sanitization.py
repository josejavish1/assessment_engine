from __future__ import annotations

import re
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _sanitize_text_placeholders(text: str, client_name: str) -> str:
    """Replace client placeholder tokens with the concrete client identifier."""
    placeholders = (
        "[Cliente]", "[CLIENTE]", "[cliente]", "[CLIENT]", "[client]", "[CUSTOMER]", "[customer]"
    )
    for token in placeholders:
        text = text.replace(token, client_name)
    return re.sub(r"\[[Cc]liente\]", client_name, text)


def _sanitize_risk_tree(obj: Any, client_name: str) -> Any:
    """Recursively scrub client placeholders across nested dictionary/list structures."""
    if isinstance(obj, dict):
        return {k: _sanitize_risk_tree(v, client_name) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_risk_tree(x, client_name) for x in obj]
    if isinstance(obj, str):
        return _sanitize_text_placeholders(obj, client_name)
    return obj


class ClientSanitizationPolicy(BaseSovereignPolicy):
    """A policy for sanitizing client-specific placeholders within a data payload."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively substitutes client name placeholders within a data payload."""
        client_name = payload.get("document_meta", {}).get("client_name", "CLIENTE")
        return _sanitize_risk_tree(payload, client_name)
