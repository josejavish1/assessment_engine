import pytest
from assessment_engine.scripts.lib.text_utils import (
    normalize_spaces,
    clean_text_for_word,
    slugify,
    normalize_tower_name,
)

# Tests for normalize_spaces
def test_normalize_spaces_with_newlines_and_multiple_spaces():
    """Verifies that newlines and multiple spaces are collapsed into single spaces."""
    input_text = "Hello\nWorld  this   is a    test."
    # The regex \s+ might consume leading/trailing spaces, so we test the core behavior.
    expected_output = "Hello World this is a test."
    assert normalize_spaces(input_text).strip() == expected_output

def test_normalize_spaces_with_no_changes_needed():
    """Verifies that a clean string remains unchanged."""
    input_text = "This is a clean string."
    assert normalize_spaces(input_text) == input_text

# Tests for clean_text_for_word
def test_clean_text_for_word_removes_control_characters():
    """Verifies that invalid XML characters are removed."""
    # chr(1) is SOH (Start of Heading), chr(28) is FS (File Separator).
    # Valid whitespace like tab (\t) should be preserved.
    input_text = "Valid text" + chr(1) + " with " + chr(28) + "invalid chars. But with\t a tab."
    expected_output = "Valid text with invalid chars. But with\t a tab."
    assert clean_text_for_word(input_text) == expected_output

def test_clean_text_for_word_with_valid_string():
    """Verifies a valid string is unchanged."""
    input_text = "This string is perfectly valid.\nIt has newlines and\ttabs."
    assert clean_text_for_word(input_text) == input_text

# Tests for slugify
@pytest.mark.parametrize("input_string, expected_slug", [
    ("Informe Global para el Cliente (Año 2026)", "informe_global_para_el_cliente_ano_2026"),
    ("Torre 5: Ciberseguridad!", "torre_5_ciberseguridad"),
    ("  leading & trailing spaces  ", "leading_trailing_spaces"),
    ("!@#$%^&*()", "generic"),
])
def test_slugify(input_string, expected_slug):
    """Tests various cases for the slugify function."""
    assert slugify(input_string) == expected_slug

# Tests for normalize_tower_name
def test_normalize_tower_name_cleans_suffixes():
    """Verifies that suffixes like 'evalúa...' are removed."""
    input_text = "Torre 5: Resiliencia y Continuidad evalúa la capacidad de..."
    expected_output = "Torre 5: Resiliencia y Continuidad"
    assert normalize_tower_name(input_text) == expected_output

def test_normalize_tower_name_with_clean_name():
    """Verifies that a clean tower name is not modified."""
    input_text = "Torre 2: Redes y Cómputo"
    assert normalize_tower_name(input_text) == input_text
