# golden-path: ignore
from __future__ import annotations

from assessment_engine.infrastructure.text_utils import (
    clean_text_for_word,
    deep_unescape,
    format_currency_custom,
    normalize_spaces,
    normalize_tower_name,
    slugify,
)


def test_slugify_tier1() -> None:
    # 1. --- ARRANGE & ACT & ASSERT ---
    assert slugify("Hello World") == "hello_world"
    assert slugify("  Ein schönes Mädchen!  ") == "ein_schones_madchen"
    assert slugify(None) == "generic"
    assert slugify("") == "generic"


def test_clean_text_tier1() -> None:
    # 2. --- ARRANGE & ACT & ASSERT ---
    assert clean_text_for_word("  trimmed  ") == "trimmed"
    assert clean_text_for_word("") == ""
    assert clean_text_for_word("Some **bold** text") == "Some bold text"
    # Ensure control characters < 32 (except tab, newline, CR) are stripped
    assert (
        clean_text_for_word("Line with\x00 null and control \x1f")
        == "Line with null and control"
    )


def test_deep_unescape() -> None:
    # 3. --- ARRANGE ---
    data = {
        "title": "A &amp; B &gt; C",
        "items": ["item one", "item &#8482;"],
        "id": 123,
    }
    expected = {"title": "A & B > C", "items": ["item one", "item ™"], "id": 123}

    # --- ACT ---
    result = deep_unescape(data)

    # --- ASSERT ---
    assert result == expected


def test_normalize_spaces() -> None:
    # 4. --- ARRANGE & ACT & ASSERT ---
    assert normalize_spaces("  hello   world  \n  next  ") == "hello world next"
    assert normalize_spaces("") == ""


def test_normalize_tower_name() -> None:
    # 5. --- ARRANGE & ACT & ASSERT ---
    assert (
        normalize_tower_name("Infraestructura de Red evalúa controles")
        == "Infraestructura de Red"
    )
    assert (
        normalize_tower_name("CPD de respaldo mide resiliencia:") == "CPD de respaldo"
    )
    assert normalize_tower_name("  ") == ""


def test_format_currency_custom() -> None:
    # 6. --- ARRANGE ---
    vocab_eu = {"currency_symbol": "€", "currency_format": "EU"}
    vocab_us = {"currency_symbol": "$", "currency_format": "US"}

    # --- ACT & ASSERT ---
    # Spanish / European formatting (dot as thousands, comma as decimal, symbol at end)
    assert format_currency_custom(1234.56, vocab_eu, "es") == "1.234,56 €"

    # English / US formatting (comma as thousands, dot as decimal, symbol at start)
    assert format_currency_custom(1234.56, vocab_us, "en") == "$1,234.56"

    # Japanese formatting (rounded to nearest integer, JPY symbol at end)
    assert format_currency_custom(1234.56, {"currency_symbol": "¥"}, "ja") == "1,235¥"


import re

from hypothesis import given
from hypothesis import strategies as st


@given(st.text())
def test_slugify_property_based(val: str) -> None:
    """Property-based fuzz test for slugify.

    Asserts that no matter what garbage, Unicode, or control character input is passed,
    slugify never crashes and always maintains its formal architectural invariants.
    """
    # --- ACT ---
    result = slugify(val)

    # --- ASSERT ---
    # 1. Invariant: Must contain only lowercase letters, digits, or single underscores
    assert re.match(r"^[a-z0-9_]+$", result) is not None, (
        f"Slug contains illegal characters: {result}"
    )

    # 2. Invariant: Must not have double underscores
    assert "__" not in result

    # 3. Invariant: Must not have leading or trailing underscores
    assert not result.startswith("_"), f"Slug has leading underscore: {result}"
    assert not result.endswith("_"), f"Slug has trailing underscore: {result}"

    # 4. Invariant: Must never be empty
    assert len(result) > 0, "Slug cannot be empty"
