"""
Provide bimodal schema compilation and runtime introspection. Maintain schema isomorphism between SQLite and frontend interfaces, enforce pre-flight validation, synthesize strict AOT TypeScript/Zod definitions, and handle UI metadata including conditional visibility, layout sections, and relational widgets.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.schema_engine")


@dataclass
class FieldDefinition:
    """Represent the canonical definition of an entity field."""
    name: str
    type: str  # 'string', 'number', 'boolean', 'date', 'select', 'textarea'
    required: bool = False
    label: str = ""
    widget: str = "text"  # 'text', 'number', 'currency', 'date', 'textarea', 'combobox', 'switch', 'file'
    default: Any = None
    constraints: dict[str, Any] = field(default_factory=dict)
    relation_table: str | None = None
    relation_label_field: str | None = None
    depends_on: dict[str, Any] | None = None
    section: str = "Información General"


@dataclass
class EntitySchema:
    """Represent the complete data schema of a business entity."""
    entity_name: str
    table_name: str
    fields: list[FieldDefinition]
    primary_key: str = "id"
    owner_field: str = "user_id"
    tenant_field: str = "tenant_id"


class SchemaEngine(CapabilityPrimitive):
    """
    Manage schema generation, validation, and introspection.
    """

    @property
    def namespace(self) -> str:
        """Return the namespace identifier."""
        return "schema_engine"

    def get_capabilities(self) -> dict[str, Any]:
        """Retrieve the supported capabilities."""
        return {
            "version": "4.3.0",
            "operations": [
                "introspect_table_schema",
                "validate_payload",
                "synthesize_zod_schema",
                "to_json_schema"
            ],
            "standards": [
                "JSON Schema Draft 7 / 2020-12",
                "Zod TypeScript Schema Generation",
                "Asynchronous Relational Combobox Hints",
                "Declarative Conditional Visibility (ui:dependsOn)",
                "Visual Fieldset Grouping (ui:section)",
                "File Attachment Widget Resolution"
            ]
        }

    def introspect_table_schema(
        self,
        db_path: Path,
        table_name: str,
        contract_hints: dict[str, Any] | None = None
    ) -> EntitySchema | None:
        """Introspect an SQLite table and generate the canonical schema definition. Cyclomatic complexity in Rank A (V(G) <= 8)."""
        if not db_path.exists():
            return None

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if not cur.fetchone():
                return None

            cur.execute(f'PRAGMA table_info("{table_name}");')
            cols = cur.fetchall()

            fields: list[FieldDefinition] = []
            pk_col = "id"

            for c in cols:
                col_name = str(c["name"])
                col_type = str(c["type"] or "TEXT").upper()
                is_not_null = bool(c["notnull"])
                default_val = c["dflt_value"]
                is_pk = bool(c["pk"])

                if is_pk:
                    pk_col = col_name

                field_def = self._infer_field_definition(
                    col_name, col_type, is_not_null, default_val, is_pk, contract_hints
                )
                fields.append(field_def)

            return EntitySchema(
                entity_name=table_name.capitalize(),
                table_name=table_name,
                fields=fields,
                primary_key=pk_col
            )
        finally:
            conn.close()

    def _infer_field_section(self, col_name: str, c_low: str, hints: dict[str, Any] | None) -> str:
        """Infer the grouped visual form section using structural column semantics."""
        if hints and "sections" in hints:
            sec_hint = hints["sections"].get(col_name)
            if sec_hint:
                return str(sec_hint)

        if c_low.endswith(("_cents", "_amount", "_price", "_fee", "_cost", "_rate", "_tax")):
            return "Facturación y Tarifas"
        if c_low.endswith(("_at", "_date", "_time", "_timestamp")):
            return "Fechas y Registro"
        if c_low.startswith(("is_", "has_")) or c_low.endswith(("_status", "_state")):
            return "Estado y Control"
        return "Información General"

    def _infer_textual_or_relational_widget(
        self, col_name: str, c_low: str, required: bool, depends_on: Any, section: str
    ) -> FieldDefinition | None:
        """Infer widgets for file attachments, foreign keys, long text, or email fields using structural suffixes."""
        label = col_name.replace("_", " ").title()
        if c_low.endswith(("_url", "_file", "_image", "_pdf", "_doc", "_avatar", "_path", "_media")):
            return FieldDefinition(
                name=col_name, type="string", required=required, label=label,
                widget="file", depends_on=depends_on, section=section
            )
        if c_low.endswith("_id") and c_low not in ("id", "tenant_id", "user_id"):
            target_rel = c_low[:-3] + "s"
            return FieldDefinition(
                name=col_name, type="string", required=required, label=label,
                widget="combobox", relation_table=target_rel, relation_label_field="name",
                depends_on=depends_on, section=section
            )
        if c_low.endswith(("_notes", "_desc", "_description", "_text", "_comment", "_bio", "_body")) or "CLOB" in c_low:
            return FieldDefinition(
                name=col_name, type="string", required=required, label=label,
                widget="textarea", depends_on=depends_on, section=section
            )
        if c_low.endswith(("_email", "email")):
            return FieldDefinition(
                name=col_name, type="string", required=required, label=label,
                widget="text", constraints={"pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
                depends_on=depends_on, section=section
            )
        return None

    def _infer_numeric_or_temporal_widget(
        self, col_name: str, col_type: str, c_low: str, required: bool, depends_on: Any, section: str
    ) -> FieldDefinition | None:
        """Infer currency, integer, boolean, or date widgets based on naming suffixes and SQL types."""
        label = col_name.replace("_", " ").title()
        is_currency = (
            c_low.endswith(("_cents", "_amount", "_price", "_fee", "_cost", "_rate", "_tax"))
            or any(t in col_type for t in ("REAL", "FLOAT", "NUMERIC", "DECIMAL"))
        )
        if is_currency:
            return FieldDefinition(
                name=col_name, type="number", required=required, label=label,
                widget="currency", constraints={"minimum": 0.0}, depends_on=depends_on, section=section
            )
        if "INT" in col_type:
            if c_low.startswith(("is_", "has_")) or c_low.endswith(("_flag", "_enabled")):
                return FieldDefinition(
                    name=col_name, type="boolean", required=False, label=label,
                    widget="switch", default=False, depends_on=depends_on, section=section
                )
            return FieldDefinition(
                name=col_name, type="number", required=required, label=label,
                widget="number", constraints={"minimum": 0}, depends_on=depends_on, section=section
            )
        is_date = (
            c_low.endswith(("_at", "_date", "_time", "_timestamp"))
            or any(t in col_type for t in ("DATE", "DATETIME", "TIMESTAMP"))
        )
        if is_date:
            return FieldDefinition(
                name=col_name, type="string", required=required, label=label,
                widget="date", depends_on=depends_on, section=section
            )
        return None

    def _infer_field_definition(
        self,
        col_name: str,
        col_type: str,
        is_not_null: bool,
        default_val: Any,
        is_pk: bool,
        hints: dict[str, Any] | None
    ) -> FieldDefinition:
        """Infer the semantic type, constraints, layout section, and UI widget."""
        c_low = col_name.lower()
        system_managed = {"id", "tenant_id", "user_id", "created_at", "updated_at"}
        required = is_not_null and (default_val is None) and (c_low not in system_managed)

        depends_on = None
        if hints and "depends_on" in hints and col_name in hints["depends_on"]:
            depends_on = hints["depends_on"][col_name]

        section = self._infer_field_section(col_name, c_low, hints)

        text_rel = self._infer_textual_or_relational_widget(col_name, c_low, required, depends_on, section)
        if text_rel:
            return text_rel

        num_temp = self._infer_numeric_or_temporal_widget(col_name, col_type, c_low, required, depends_on, section)
        if num_temp:
            return num_temp

        return FieldDefinition(
            name=col_name,
            type="string",
            required=required,
            label=col_name.replace("_", " ").title(),
            widget="text",
            depends_on=depends_on,
            section=section
        )

    def _validate_number_constraints(self, f: FieldDefinition, val: Any) -> list[str]:
        errs = []
        try:
            num_val = float(val)
            if "minimum" in f.constraints and num_val < f.constraints["minimum"]:
                errs.append(f"El campo '{f.name}' debe ser mayor o igual a {f.constraints['minimum']} (recibido: {num_val})")
            if "maximum" in f.constraints and num_val > f.constraints["maximum"]:
                errs.append(f"El campo '{f.name}' debe ser menor o igual a {f.constraints['maximum']}")
        except (ValueError, TypeError):
            errs.append(f"El campo '{f.name}' debe ser un valor numérico válido")
        return errs

    def _validate_field_constraints(self, f: FieldDefinition, val: Any) -> list[str]:
        """Validate numeric and length constraints on an individual field."""
        errs: list[str] = []
        if f.type == "number":
            errs.extend(self._validate_number_constraints(f, val))
        elif f.type == "string" and isinstance(val, str):
            if "min_length" in f.constraints and len(val) < f.constraints["min_length"]:
                errs.append(f"El campo '{f.name}' debe tener al menos {f.constraints['min_length']} caracteres")
        return errs

    def validate_payload(
        self,
        schema: EntitySchema,
        payload: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate a payload against schema constraints. Returns (is_valid, error_list)."""
        if not isinstance(payload, dict):
            return False, ["El cuerpo de la petición debe ser un objeto JSON"]

        errors: list[str] = []
        for f in schema.fields:
            val = payload.get(f.name)
            if f.required and (val is None or val == ""):
                errors.append(f"El campo '{f.name}' es obligatorio")
            elif val is not None:
                errors.extend(self._validate_field_constraints(f, val))

        return len(errors) == 0, errors

    def to_json_schema(self, schema: EntitySchema) -> dict[str, Any]:
        """Serialize the entity to JSON Schema Draft 7 format with ui:section metadata."""
        properties: dict[str, Any] = {}
        required_fields: list[str] = []

        for f in schema.fields:
            prop: dict[str, Any] = {
                "type": f.type,
                "title": f.label,
                "ui:widget": f.widget,
                "ui:section": f.section
            }
            if f.constraints:
                prop.update(f.constraints)
            if f.relation_table:
                prop["ui:relation"] = {
                    "table": f.relation_table,
                    "label_field": f.relation_label_field
                }
            if f.depends_on:
                prop["ui:dependsOn"] = f.depends_on

            properties[f.name] = prop

            if f.required:
                required_fields.append(f.name)

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": schema.entity_name,
            "type": "object",
            "properties": properties,
            "required": required_fields,
            "primaryKey": schema.primary_key
        }

    def synthesize_zod_schema(self, schema: EntitySchema) -> str:
        """Generate strict TypeScript code with Zod validators via ahead-of-time (AOT) synthesis to emit fully typed components without 'any'."""
        lines = [
            "import { z } from 'zod'",
            "",
            f"export const {schema.entity_name}Schema = z.object({{"
        ]

        for f in schema.fields:
            if f.name in (schema.primary_key, schema.tenant_field):
                continue

            zod_type = "z.string()"
            if f.type == "number":
                zod_type = "z.number()"
                if "minimum" in f.constraints:
                    zod_type += f".min({f.constraints['minimum']}, 'Debe ser >= {f.constraints['minimum']}')"
            elif f.type == "boolean":
                zod_type = "z.boolean()"

            if not f.required:
                zod_type += ".optional()"

            lines.append(f"  {f.name}: {zod_type},")

        lines.append("})")
        lines.append("")
        lines.append(f"export type {schema.entity_name}FormValues = z.infer<typeof {schema.entity_name}Schema>")
        return "\n".join(lines)


schema_engine = SchemaEngine()
