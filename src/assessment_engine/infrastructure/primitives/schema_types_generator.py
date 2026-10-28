"""
Automated Schema-to-TypeScript Generator — System 01 (Tier-1 SOTA 2026).
Introspects SQLite WAL database schemas and emits strictly-typed TypeScript interfaces
matching Supabase / TanStack contracts (Row, Insert, Update, Database).
Eliminates LLM column hallucinations and runtime type drift.
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.db import db_primitive

logger = logging.getLogger("schema_types_generator")

SQLITE_TO_TS_MAP: dict[str, str] = {
    "integer": "number",
    "int": "number",
    "smallint": "number",
    "bigint": "number",
    "numeric": "number",
    "real": "number",
    "float": "number",
    "double": "number",
    "text": "string",
    "varchar": "string",
    "char": "string",
    "clob": "string",
    "blob": "string",
    "boolean": "boolean",
    "bool": "boolean",
    "datetime": "string",
    "date": "string",
    "timestamp": "string",
}


def map_sqlite_type_to_ts(raw_type: str) -> str:
    """Map raw SQLite column type to strict TypeScript primitive."""
    cleaned = re.sub(r"\(.*?\)", "", raw_type).strip().lower()
    return SQLITE_TO_TS_MAP.get(cleaned, "string")


def _pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r"[^a-zA-Z0-9]", name)
    return "".join(p.capitalize() for p in parts if p) or "Entity"


def _generate_table_interfaces(table_name: str, columns: list[dict[str, Any]]) -> str:
    """Generate Row, Insert, and Update TypeScript interfaces for a single table."""
    pascal = _pascal_case(table_name)
    row_fields: list[str] = []
    insert_fields: list[str] = []
    update_fields: list[str] = []

    for col in columns:
        col_name = col.get("name", "col")
        c_type = map_sqlite_type_to_ts(col.get("type", "TEXT"))
        is_nullable = not col.get("notnull", False)
        has_default = col.get("default") is not None or col.get("pk", False)

        type_str = f"{c_type} | null" if is_nullable else c_type
        row_fields.append(f'    "{col_name}": {type_str};')

        is_opt = "?" if (is_nullable or has_default) else ""
        insert_fields.append(f'    "{col_name}"{is_opt}: {type_str};')

        update_fields.append(f'    "{col_name}"?: {type_str};')

    row_body = "\n".join(row_fields)
    insert_body = "\n".join(insert_fields)
    update_body = "\n".join(update_fields)

    return (
        f"export interface {pascal}Row {{\n{row_body}\n}}\n\n"
        f"export interface {pascal}Insert {{\n{insert_body}\n}}\n\n"
        f"export interface {pascal}Update {{\n{update_body}\n}}\n"
    )


def generate_typescript_schema(schema_dict: dict[str, Any]) -> str:
    """Generate complete isomorphic Database TypeScript contract from introspected schema."""
    tables_meta = schema_dict.get("tables", {})
    interfaces_code: list[str] = [
        "/**",
        " * Automatically Generated TypeScript Database Schema.",
        " * Emitted by Autonomuos SchemaTypesGenerator from SQLite WAL.",
        " * Strict parity with PostgREST / Supabase contract standards.",
        " */",
        "",
    ]

    database_tables: list[str] = []

    for table_name, meta in sorted(tables_meta.items()):
        columns = meta.get("columns", [])
        interfaces_code.append(_generate_table_interfaces(table_name, columns))

        pascal = _pascal_case(table_name)
        database_tables.append(
            f'      "{table_name}": {{\n'
            f"        Row: {pascal}Row;\n"
            f"        Insert: {pascal}Insert;\n"
            f"        Update: {pascal}Update;\n"
            f"      }};"
        )

    db_tables_block = "\n".join(database_tables) if database_tables else "      [key: string]: never;"

    interfaces_code.extend([
        "export interface Database {",
        "  public: {",
        "    Tables: {",
        db_tables_block,
        "    };",
        "  };",
        "}",
        "",
    ])

    return "\n".join(interfaces_code)


def emit_schema_types(slug: str, out_file: Path) -> Path:
    """Introspect SQLite WAL schema for a project slug and write strictly-typed schema.ts."""
    schema_meta = db_primitive.introspect_schema(slug)
    ts_code = generate_typescript_schema(schema_meta)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ts_code, encoding="utf-8")
    return out_file


def cli_main() -> None:
    """CLI runner to generate TypeScript types from SQLite WAL."""
    parser = argparse.ArgumentParser(description="Emit TypeScript types from SQLite WAL schema")
    parser.add_argument("--slug", required=True, help="Slug del proyecto a introspeccionar")
    parser.add_argument("--out", type=Path, required=True, help="Ruta de destino del archivo schema.ts")
    args = parser.parse_args()

    out_path = emit_schema_types(args.slug, args.out)
    logger.info(f"✓ Tipos TypeScript emitidos correctamente en: {out_path}")


if __name__ == "__main__":
    cli_main()
