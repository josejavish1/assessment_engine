"""Language-aware orthographic and diacritical normalization service."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OrthographicNormalizer:
    """Deterministic post-processing filter that restores missing orthographic diacritics.

    Protects technical identifiers, snake_case keys, code blocks, URLs, and applies
    language-specific morphological suffix rules and whole-word dictionaries.
    """

    PROTECTED_KEY_NAMES: set[str] = {
        "id",
        "node_id",
        "code",
        "metric_id",
        "pillar_id",
        "finding_id",
        "currency",
        "currency_code",
        "locale",
        "language",
        "doc_lang",
        "status",
        "severity_code",
        "file_path",
        "url",
        "model_name",
        "timestamp_utc",
    }

    IDENTIFIER_REGEX = re.compile(
        r"^[A-Z0-9_.\-]+$|^[a-z0-9_]+_[a-z0-9_]+$|^https?://|^urn:"
    )

    def __init__(self, lexicon_path: Path) -> None:
        self.lexicon_data: dict[str, Any] = {}
        if lexicon_path.exists():
            try:
                self.lexicon_data = json.loads(lexicon_path.read_text(encoding="utf-8-sig"))
            except Exception as e:
                logger.warning("Failed to load orthographic lexicon from '%s': %s", lexicon_path, e)

    def normalize_payload(self, payload: Any, locale: str) -> Any:
        """Recursively normalizes human-readable string values for the specified ISO locale."""
        lang_key = (locale or "en").split("-")[0].split("_")[0].lower()
        if lang_key not in self.lexicon_data:
            return payload

        rules = self.lexicon_data[lang_key]
        return self._walk(payload, rules, parent_key=None)

    def _walk(self, node: Any, rules: dict[str, Any], parent_key: str | None) -> Any:
        if isinstance(node, dict):
            return {
                k: self._walk(v, rules, parent_key=k)
                for k, v in node.items()
            }
        if isinstance(node, list):
            return [self._walk(item, rules, parent_key=parent_key) for item in node]
        if isinstance(node, str):
            if parent_key in self.PROTECTED_KEY_NAMES or self.IDENTIFIER_REGEX.match(node):
                return node
            return self._normalize_text(node, rules)
        return node

    def _normalize_text(self, text: str, rules: dict[str, Any]) -> str:
        if not text or len(text) < 3:
            return text

        result = text

        # 1. Apply morphological suffix rules while preserving case
        for suffix_rule in rules.get("suffix_rules", []):
            pattern = suffix_rule.get("pattern")
            replacement = suffix_rule.get("replacement")
            if pattern and replacement:
                try:
                    result = re.sub(
                        pattern,
                        lambda m, rep=replacement: self._preserve_suffix_case(m, rep),
                        result,
                        flags=re.IGNORECASE,
                    )
                except Exception as ex:
                    logger.debug("Failed applying suffix rule '%s': %s", pattern, ex)

        # 2. Apply unambiguous whole-word and phrase replacements
        unambiguous: dict[str, str] = rules.get("unambiguous_tokens", {})
        for raw_token, accented_token in unambiguous.items():
            if raw_token.startswith(" ") and raw_token.endswith(" "):
                # Phrase boundary replacement
                result = result.replace(raw_token, accented_token)
            else:
                word_regex = re.compile(rf"\b{re.escape(raw_token)}\b", flags=re.IGNORECASE)
                result = word_regex.sub(
                    lambda m, target=accented_token: self._match_casing(m.group(0), target),
                    result,
                )

        return result

    @staticmethod
    def _match_casing(source: str, target: str) -> str:
        """Preserves the casing of the original source word when applying accents."""
        if source.isupper():
            return target.upper()
        if source and source[0].isupper():
            return target.capitalize()
        return target.lower()

    @staticmethod
    def _preserve_suffix_case(match: re.Match, replacement_template: str) -> str:
        """Preserves casing on suffix regex replacements."""
        full_word = match.group(0)
        expanded = match.expand(replacement_template)
        if full_word.isupper():
            return expanded.upper()
        if full_word and full_word[0].isupper():
            return expanded.capitalize()
        return expanded
