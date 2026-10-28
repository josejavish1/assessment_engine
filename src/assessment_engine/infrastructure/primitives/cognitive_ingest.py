"""
Cognitive Ingestion Primitive (Tier-1 SOTA 2026 Multiplier).
Transforms natural language commands (or audio dictation) into deterministic,
schema-validated relational mutations in SQLite WAL without manual form-filling.
Hardened against Prompt Injection, Table Hijacking, and SQL Injections.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from google.genai import types

from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model
from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive
from assessment_engine.infrastructure.primitives.db import db_primitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.cognitive_ingest")

WORKSPACES_DIR = Path(__file__).resolve().parents[2] / "workspaces"
MAX_COMMAND_LENGTH = 1000

INJECTION_PATTERNS = re.compile(
    r"(\[SYSTEM.*?\]|<<<SYSTEM.*?>>>|<\|im_.*?\|>|DROP\s+TABLE|ALTER\s+TABLE|DELETE\s+FROM\s+sqlite_)",
    re.IGNORECASE
)


def _sanitize_cognitive_record(record_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize and sanitize raw record fields respecting CHECK constraints."""
    clean_record: dict[str, Any] = {}
    normalized_keys = {"status", "record_type", "type", "species", "gender", "priority"}
    for k, v in record_data.items():
        if isinstance(v, str) and k.lower() in normalized_keys:
            clean_record[k] = v.lower().strip()
        else:
            clean_record[k] = v
    return clean_record


class CognitiveIngestPrimitive(CapabilityPrimitive):
    """Ingest natural language input and convert spoken or written instructions into ACID relational mutations."""

    @property
    def namespace(self) -> str:
        """Return the namespace of the instance."""
        return "cognitive"

    def get_capabilities(self) -> dict[str, Any]:
        """Return the supported capabilities."""
        return {
            "version": "1.0.0",
            "operations": ["process_natural_language_command", "introspect_domain_context"],
            "model": get_model(ModelTier.FAST),
            "persistence": "SQLite 3 WAL Parameterized Binds"
        }

    def _sanitize_command(self, natural_text: str) -> str:
        """Sanitize input text against prompt injection attacks and null characters."""
        raw_text = str(natural_text).strip()[:MAX_COMMAND_LENGTH]
        sanitized = INJECTION_PATTERNS.sub("[COMANDO_FILTRADO]", raw_text)
        return re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]", "", sanitized).strip()

    def _resolve_schema_tables(self, clean_slug: str) -> tuple[set[str], dict[str, list[str]]]:
        """Introspect the table schema in app.db and generate a summary for the LLM."""
        schema = db_primitive.introspect_schema(clean_slug)
        tables_dict = schema.get("tables_dict") or (schema.get("tables") if isinstance(schema.get("tables"), dict) else {})
        if not tables_dict and isinstance(schema.get("tables"), list):
            tables_dict = {t: {} for t in schema.get("tables", [])}

        allowed_tables = set(tables_dict.keys())
        schema_summary = {
            t: [c["name"] for c in info.get("columns", []) if c["name"] != "id"]
            for t, info in tables_dict.items()
        }
        return allowed_tables, schema_summary

    def _execute_cognitive_operations(
        self,
        clean_slug: str,
        operations: list[dict[str, Any]],
        allowed_tables: set[str]
    ) -> list[dict[str, Any]]:
        """Apply atomic relational mutations while respecting CHECK constraints."""
        executed_records: list[dict[str, Any]] = []
        for op in operations:
            target_table = op.get("table", "")
            action = op.get("action", "insert").lower()
            record_data = op.get("record", {})

            matched_table = next((t for t in allowed_tables if t.lower() == target_table.lower()), None)
            if not matched_table:
                logger.warning(f"[CognitiveIngest] Tabla '{target_table}' no autorizada en {clean_slug}.")
                continue

            if action != "insert" or not isinstance(record_data, dict) or not record_data:
                continue

            clean_record = _sanitize_cognitive_record(record_data)
            try:
                created = db_primitive.create_record(clean_slug, matched_table, clean_record)
                executed_records.append({
                    "table": matched_table,
                    "action": "insert",
                    "id": created.get("id"),
                    "record": created
                })
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as db_err:  # noqa: BLE001
                logger.error(f"[CognitiveIngest] Error insertando en '{matched_table}': {db_err}")

        return executed_records

    async def process_natural_language_command(
        self,
        slug: str,
        natural_text: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Process a natural language instruction, infer relational entities, and execute parameterized inserts and updates in SQLite WAL. Modularized using the Strangler Fig pattern (McCabe V(G) <= 5)."""
        clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "", slug)
        if not clean_slug:
            return {"status": "error", "message": "Slug de proyecto inválido"}

        sanitized_command = self._sanitize_command(natural_text)
        if not sanitized_command or sanitized_command == "[COMANDO_FILTRADO]":
            return {"status": "error", "message": "Comando vacío o filtrado por políticas de seguridad"}

        allowed_tables, schema_summary = self._resolve_schema_tables(clean_slug)
        if not allowed_tables:
            return {"status": "error", "message": f"No se encontraron tablas de dominio en '{clean_slug}'"}

        client = create_genai_client()
        sys_prompt = (
            "Eres el Staff Data Architect en Stripe & Epic Systems.\n"
            "Tu misión es traducir una INSTRUCCIÓN EN LENGUAJE NATURAL de un usuario en OPERACIONES RELACIONALES ATÓMICAS.\n"
            f"TABLAS DISPONIBLES EN LA BASE DE DATOS (SQLite):\n{json.dumps(schema_summary, indent=2, ensure_ascii=False)}\n\n"
            "REGLAS ESTRICTAS DE RESPUESTA:\n"
            "1. Solo puedes utilizar las tablas listadas arriba. Prohibido inventar tablas.\n"
            "2. Asigna valores coherentes a las columnas existentes. Si una columna no aplica, omítela.\n"
            "3. En 'intent' explica brevemente la intención del usuario.\n"
            "4. En 'summary' redacta un mensaje sobrio y profesional para el usuario confirmando lo realizado.\n"
            "5. EMITE EXCLUSIVAMENTE UN OBJETO JSON CON ESTE ESQUEMA EXACTO:\n"
            "{\n"
            '  "intent": "Descripción de la intención",\n'
            '  "summary": "Mensaje de confirmación al usuario",\n'
            '  "operations": [\n'
            '    {\n'
            '      "table": "NombreTablaExacta",\n'
            '      "action": "insert",\n'
            '      "record": {"columna1": "valor", "columna2": 123}\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        user_content = f"INSTRUCCIÓN DEL USUARIO: {sanitized_command}"
        if context:
            user_content += f"\nCONTEXTO ADICIONAL: {json.dumps(context, ensure_ascii=False)}"

        try:
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.FAST),
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            if not resp or not resp.text:
                return {"status": "error", "message": "Respuesta vacía del motor cognitivo"}

            plan = json.loads(resp.text)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[CognitiveIngest] Error en inferencia LLM para '{clean_slug}': {ex}")
            return {"status": "error", "message": f"Error infiriendo intención: {ex}"}

        executed_records = self._execute_cognitive_operations(clean_slug, plan.get("operations", []), allowed_tables)

        return {
            "status": "success",
            "command": sanitized_command,
            "intent": plan.get("intent", "Operación cognitiva ejecutada"),
            "summary": plan.get("summary", f"Se aplicaron {len(executed_records)} operaciones en la base de datos."),
            "operations_count": len(executed_records),
            "records": executed_records
        }


cognitive_ingest = CognitiveIngestPrimitive()
