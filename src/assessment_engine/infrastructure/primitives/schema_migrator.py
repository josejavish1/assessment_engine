"""
Declarative SQLite Schema Migration Engine — GEMA 08 (SOTA 2026).
Compares expected domain entity models against current SQLite PRAGMA table_info.
Generates and executes non-destructive ALTER TABLE ADD COLUMN migrations at startup.
Guarantees zero data loss when the evolution engine adds new properties to existing tables.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.schema_migrator")


class SchemaMigratorPrimitive:
    """
    Migrador declarativo seguro de esquemas SQLite.
    """

    def align_table_schema(
        self,
        db_path: Path,
        table_name: str,
        desired_columns: dict[str, str]
    ) -> dict[str, Any]:
        """Inspect 'table_name' and add any missing columns using ALTER TABLE. 'desired_columns': {'column_name': 'TEXT DEFAULT ""'}"""
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if not cur.fetchone():
                # Tabla no existe, crear desde cero
                col_defs = [f'"{col}" {col_type}' for col, col_type in desired_columns.items()]
                create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id TEXT PRIMARY KEY, {", ".join(col_defs)});'
                cur.execute(create_sql)
                conn.commit()
                return {"status": "created", "table": table_name, "columns_added": list(desired_columns.keys())}

            cur.execute(f'PRAGMA table_info("{table_name}");')
            existing_cols = {row[1] for row in cur.fetchall()}

            added = []
            for col, col_type in desired_columns.items():
                if col not in existing_cols:
                    alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {col_type};'
                    cur.execute(alter_sql)
                    added.append(col)

            conn.commit()
            if added:
                logger.info(f"[SchemaMigrator] Columnas agregadas a '{table_name}': {added}")
            return {
                "status": "aligned",
                "table": table_name,
                "columns_added": added,
                "existing_columns_count": len(existing_cols)
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.error(f"[SchemaMigrator] Error migrando tabla {table_name}: {ex}")
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()


schema_migrator = SchemaMigratorPrimitive()
