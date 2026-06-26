# golden-path: ignore
from __future__ import annotations

from pathlib import Path
from assessment_engine.scripts.tools import validate_contracts_schemas as v_schema


def test_normalize_type_annotation():
    assert v_schema.normalize_type_annotation(list[int]) == "list[int]"
    assert v_schema.normalize_type_annotation(dict[str, float]) == "dict[str, float]"
    assert v_schema.normalize_type_annotation(None) == "None"


def test_check_type_compatibility():
    # Direct matches
    assert v_schema.check_type_compatibility("list[int]", "list[int]") is True
    assert v_schema.check_type_compatibility("str", "str") is True

    # Optional wrappers
    assert v_schema.check_type_compatibility("Optional[float]", "float") is True
    assert v_schema.check_type_compatibility("Optional[str]", "str") is True

    # Union wrappers
    assert v_schema.check_type_compatibility("Union[str, None]", "str") is True

    # Fallbacks and dicts
    assert v_schema.check_type_compatibility("dict", "dict") is True
    assert v_schema.check_type_compatibility("list[BlueprintDocumentMeta]", "list[dict]") is True

    # Incompatible types
    assert v_schema.check_type_compatibility("int", "str") is False
    assert v_schema.check_type_compatibility("list[int]", "str") is False


def test_parse_markdown_table_row():
    # Standard row (3 columns)
    row = v_schema.parse_markdown_table_row("| `client_name` | `str` | Name of the client. |")
    assert row is not None
    assert row["field_name"] == "client_name"
    assert row["field_type"] == "str"
    assert row["alias"] is None

    # Aliased row (4 columns)
    row = v_schema.parse_markdown_table_row("| `target_state` | `str` | `capability` | Capacidad evaluada. |")
    assert row is not None
    assert row["field_name"] == "target_state"
    assert row["field_type"] == "str"
    assert row["alias"] == "capability"

    # Header and separator rows (should return None)
    assert v_schema.parse_markdown_table_row("| Campo | Tipo | Descripción |") is None
    assert v_schema.parse_markdown_table_row("|---|---|---|") is None
    assert v_schema.parse_markdown_table_row("Some plain text line") is None


def test_extract_markdown_models_and_tables(tmp_path: Path):
    md_file = tmp_path / "mock_contract.md"
    md_file.write_text(
        """
# Contract document

## Modelo Principal: `MockPayload`

| Campo | Tipo | Descripción |
|---|---|---|
| `client_name` | `str` | Nombre del cliente. |
| `pillars` | `list[dict]` | Lista de pilares. |

### `MockSubModel`

| Campo | Tipo | Alias JSON | Descripción |
|---|---|---|---|
| `target_state` | `str` | `capability` | Capacidad. |
        """,
        encoding="utf-8",
    )

    models = v_schema.extract_markdown_models_and_tables(md_file)
    assert "MockPayload" in models
    assert "MockSubModel" in models

    assert len(models["MockPayload"]) == 2
    assert models["MockPayload"][0]["field_name"] == "client_name"
    assert models["MockPayload"][0]["field_type"] == "str"

    assert len(models["MockSubModel"]) == 1
    assert models["MockSubModel"][0]["field_name"] == "target_state"
    assert models["MockSubModel"][0]["alias"] == "capability"
