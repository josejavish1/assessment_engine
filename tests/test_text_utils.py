from __future__ import annotations

from assessment_engine.infrastructure.text_utils import clean_text_for_word, slugify


def test_slugify_tier1() -> None:
    assert slugify("Hello World") == "hello_world"


def test_clean_text_tier1() -> None:
    assert clean_text_for_word("  trimmed  ") == "trimmed"
