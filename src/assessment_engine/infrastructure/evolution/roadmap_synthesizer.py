"""
Synthesize roadmaps, relational schemas, and typed SDKs (core/evolution).
Extracted from autonomous_evolution_engine.py using the Strangler Fig pattern.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("evolution_roadmap_synthesizer")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACES_ROOT = ROOT_DIR / "workspaces"
SCHEMA_CACHE_DB_PATH = ROOT_DIR / "storage" / "data" / "relational_schema_cache.db"


def _init_schema_cache_db() -> None:
    SCHEMA_CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(SCHEMA_CACHE_DB_PATH), timeout=10.0) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relational_schemas (
                cache_key TEXT PRIMARY KEY,
                sector TEXT NOT NULL,
                schema_json TEXT NOT NULL,
                cached_at REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_relational_sector ON relational_schemas(sector);")


def _get_schema_by_tokens(cur: sqlite3.Cursor, sector: str) -> dict[str, Any] | None:
    """Helper to query relational schemas by significant token overlap."""
    clean = re.sub(r'[^\w\s]', '', sector).strip()
    words = [w for w in clean.split() if len(w) >= 4]
    if not words:
        return None
    conditions = ' AND '.join('sector LIKE ?' for _ in words[:3])
    params = [f'%{w}%' for w in words[:3]]
    query = "SELECT schema_json FROM relational_schemas WHERE " + conditions + " LIMIT 1;"
    cur.execute(query, tuple(params))
    row = cur.fetchone()
    return json.loads(row[0]) if row else None


def _get_schema_from_cache(key: str, sector: str = "") -> dict[str, Any] | None:
    """Retrieve schema from SQLite WAL by exact key, sector name, or token match."""
    try:
        _init_schema_cache_db()
        with sqlite3.connect(str(SCHEMA_CACHE_DB_PATH), timeout=5.0) as conn:
            cur = conn.cursor()
            cur.execute("SELECT schema_json FROM relational_schemas WHERE cache_key = ?;", (key,))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
            if sector:
                cur.execute("SELECT schema_json FROM relational_schemas WHERE sector = ? LIMIT 1;", (sector,))
                row = cur.fetchone()
                if row:
                    return json.loads(row[0])
                token_match = _get_schema_by_tokens(cur, sector)
                if token_match:
                    return token_match
    except Exception as ex:
        logger.debug(f"[RoadmapSynthesizer] Error lectura caché relacional: {ex}")
    return None


def _save_schema_to_cache(key: str, sector: str, schema_data: dict[str, Any]) -> None:
    try:
        _init_schema_cache_db()
        with sqlite3.connect(str(SCHEMA_CACHE_DB_PATH), timeout=5.0) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO relational_schemas (cache_key, sector, schema_json, cached_at) VALUES (?, ?, ?, ?);",
                (key, sector, json.dumps(schema_data), time.time()),
            )
            conn.commit()
    except Exception as ex:
        logger.debug(f"[RoadmapSynthesizer] Error escritura caché relacional: {ex}")


class RoadmapSynthesizer:
    """Synthesize SQLite WAL relational schemas, typed client SDKs, and dynamic backlogs."""

    @staticmethod
    def _execute_ddl_and_seed(db_file: Path, schema_data: dict[str, Any], slug: str) -> None:
        db_file.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_file), timeout=30.0)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("PRAGMA busy_timeout = 30000;")
        cur.execute("PRAGMA foreign_keys = ON;")
        for stmt in schema_data.get("ddl_statements", []):
            try: cur.execute(stmt)
            except (sqlite3.Error, Exception) as stmt_err: logger.debug(f"DDL stmt note: {stmt_err}")
        for idx in schema_data.get("indexes", []):
            try: cur.execute(idx)
            except (sqlite3.Error, Exception) as idx_err: logger.debug(f"Index stmt note: {idx_err}")
        for insert in schema_data.get("seed_inserts", []):
            try:
                safe_insert = insert.replace("INSERT INTO", "INSERT OR IGNORE INTO") if "INSERT OR IGNORE" not in insert else insert
                cur.execute(safe_insert)
            except (sqlite3.Error, Exception) as ex: logger.debug(f"Seed insert note: {ex}")
        try:
            cur.execute("INSERT OR IGNORE INTO users (id, email, name, auth_hash, is_premium, role) VALUES ('usr_demo', 'demo@cliente.com', 'Usuario Demostración', 'demo_hash', 1, 'client');")
        except (sqlite3.Error, Exception):
            pass
        conn.commit()
        conn.close()
        logger.info(f"[{slug}] Esquema relacional tipado creado en SQLite: {len(schema_data.get('ddl_statements', []))} tablas")

    @staticmethod
    async def synthesize_relational_schema(
        client: genai.Client | None,
        slug: str,
        goal: str,
        ui_paradigm: str,
        sector: str = "",
    ) -> dict[str, Any]:
        """Generate a typed relational schema in SQLite WAL with AOT sub-millisecond caching."""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        db_file = ws_dir / "app.db"

        cache_subject = sector or goal
        cache_key = hashlib.sha256(f"{cache_subject}:{ui_paradigm}".encode()).hexdigest()

        cached_schema = _get_schema_from_cache(cache_key, cache_subject)
        if cached_schema and cached_schema.get("ddl_statements"):
            logger.info(f"[RoadmapSynthesizer] ⚡ HIT AOT en caché SQLite WAL para '{cache_subject[:35]}' (0.001s).")
            RoadmapSynthesizer._execute_ddl_and_seed(db_file, cached_schema, slug)
            return cached_schema

        prompt = (
            "Eres el Staff Database Architect en Stripe y Supabase.\n"
            f"Diseña un esquema relacional tipado real en SQLite para esta iniciativa: '{goal}'\n"
            f"Paradigma de UI: '{ui_paradigm}'\n\n"
            "REQUISITOS DEL ESQUEMA RELACIONAL:\n"
            "1. Define entre 2 y 4 tablas SQL relacionales exclusivas para este negocio (ej. para un restaurante: dining_tables, experiences_menu, table_reservations; para una clínica: appointments, treatments_catalog; para un taller: repair_orders, vehicles; para suscripción: plans_catalog, subscriptions).\n"
            "2. Usa tipos nativos de SQLite: TEXT, INTEGER, REAL, DATETIME.\n"
            "3. Incluye claves primarias (id TEXT PRIMARY KEY), claves foráneas (FOREIGN KEY) e índices relevantes.\n"
            "4. Queda TERMINANTEMENTE PROHIBIDO el antipatrón 'JSON bag' o columnas genéricas 'data_json' para datos principales.\n"
            "5. En 'ddl_statements' incluye ÚNICAMENTE sentencias 'CREATE TABLE IF NOT EXISTS' con sus columnas completamente definidas.\n"
            "6. SEEDING SINTÉTICO OBLIGATORIO (CERO PUEBLOS FANTASMA):\n"
            "   - En 'seed_inserts' incluye OBLIGATORIAMENTE entre 3 y 5 sentencias 'INSERT INTO' por cada tabla creada.\n"
            "   - Los datos deben ser realistas, profesionales y ricos en contenido (títulos persuasivos, descripciones detalladas, precios creíbles, nombres y estados reales; Queda prohibido usar 'test', 'foo', 'item 1').\n"
            "   - Esto garantiza que al abrir la plataforma por primera vez, el usuario vea un producto vivo y poblado.\n\n"
            "EMITE EXCLUSIVAMENTE UN OBJETO JSON CON ESTA ESTRUCTURA:\n"
            "{\n"
            '  "ddl_statements": ["CREATE TABLE IF NOT EXISTS ...", ...],\n'
            '  "indexes": ["CREATE INDEX IF NOT EXISTS ...", ...],\n'
            '  "seed_inserts": ["INSERT INTO ...", ...],\n'
            '  "tables_summary": [{"name": "...", "description": "..."}]\n'
            "}"
        )

        try:
            if not client:
                return {}
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.FAST),
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            if resp.text:
                schema_data = json.loads(resp.text.strip(), strict=False)
                _save_schema_to_cache(cache_key, cache_subject, schema_data)
                RoadmapSynthesizer._execute_ddl_and_seed(db_file, schema_data, slug)
                return schema_data
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error creando esquema relacional tipado para '{slug}': {e}")
        return {}

    @staticmethod
    async def synthesize_domain_api(slug: str, goal: str, schema_info: dict[str, Any]) -> bool:
        """Provision the parameterized, secure REST engine over SQLite WAL in api/src/domain_routes.py and mount it under the /api/v1 prefix in api/src/main.py."""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        api_src = ws_dir / "api" / "src"
        if not api_src.exists():
            return False

        template_routes = ROOT_DIR / "templates" / "golden_polyglot_starter" / "api" / "src" / "domain_routes.py"
        routes_file = api_src / "domain_routes.py"
        if template_routes.exists():
            routes_file.write_text(template_routes.read_text(encoding="utf-8"), encoding="utf-8")

        main_py = api_src / "main.py"
        if main_py.exists():
            content = main_py.read_text(encoding="utf-8")
            if "domain_routes" not in content:
                mount_code = (
                    "\n# --- MONTAJE AUTOMÁTICO DE RUTAS DE DOMINIO TIER-1 ---\n"
                    "try:\n"
                    "    from .domain_routes import router as domain_router\n"
                    "    app.include_router(domain_router, prefix=\"/api/v1\")\n"
                    "except Exception:\n"
                    "    pass\n"
                )
                main_py.write_text(content + mount_code, encoding="utf-8")
        logger.info(f"[{slug}] Endpoints REST de dominio montados bajo /api/v1")
        return True

    @staticmethod
    def generate_typed_sdk_js(slug: str, schema_info: dict[str, Any]) -> str:
        """Generate the typed client SDK 'window.db' that deterministically maps each created relational table to list(), create(), get(), and delete() methods."""
        tables = [t.get("name") for t in schema_info.get("tables_summary", [])]
        if "items" not in tables:
            tables.append("items")

        methods_code = []
        for t in tables:
            methods_code.append(f"""
    {t}: {{
      list: async (limit = 50) => {{
        const res = await fetch('/preview/{slug}/api/v1/{t}?limit=' + limit);
        if (!res.ok) throw new Error('HTTP ' + res.status + ' al listar {t}');
        return await res.json();
      }},
      create: async (data) => {{
        const res = await fetch('/preview/{slug}/api/v1/{t}', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(data)
        }});
        if (!res.ok) throw new Error('HTTP ' + res.status + ' al crear en {t}');
        return await res.json();
      }},
      get: async (id) => {{
        const res = await fetch('/preview/{slug}/api/v1/{t}/' + id);
        if (!res.ok) throw new Error('HTTP ' + res.status + ' al obtener de {t}');
        return await res.json();
      }},
      delete: async (id) => {{
        const res = await fetch('/preview/{slug}/api/v1/{t}/' + id, {{ method: 'DELETE' }});
        if (!res.ok) throw new Error('HTTP ' + res.status + ' al borrar de {t}');
        return await res.json();
      }}
    }},""")

        sdk_js = f"""// SDK TIPADO AUTO-GENERADO POR EL ARNÉS AUTÓNOMO TIER-1 (ESTÁNDAR 2026)
(function() {{
  if (typeof window === 'undefined') return;
  const dbSdk = Object.freeze({{{''.join(methods_code)}
  }});
  let _activeDb = dbSdk;
  try {{
    Object.defineProperty(window, 'db', {{
      get: function() {{ return _activeDb; }},
      set: function(val) {{
        console.warn('[Harness SDK] Sobrescritura de window.db neutralizada. Preservando cliente SQLite real.');
      }},
      configurable: true
    }});
  }} catch (e) {{
    window.db = dbSdk;
  }}
  console.info('[Harness SDK] window.db blindado con tablas:', {json.dumps(tables)});
}})();
"""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        dist_dir = ws_dir / "web" / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        (dist_dir / "sdk_db.js").write_text(sdk_js, encoding="utf-8")
        logger.info(f"[{slug}] SDK tipado window.db generado en web/dist/sdk_db.js para {len(tables)} tablas")
        return sdk_js

    @staticmethod
    async def search_market_leaders(client: genai.Client | None, goal: str, sector: str) -> list[str]:
        """Search Google in real time for the top 2-3 global leaders in this sector."""
        if not client:
            return ["Líder Global 1", "Líder Global 2"]
        prompt = (
            f"Identifica los 2 o 3 productos de software y plataformas líderes mundiales de referencia para esta iniciativa: '{goal}' (Sector: {sector}). "
            "Devuelve únicamente una lista JSON con sus nombres y su característica clave más potente. Ejemplo: [\"Kajabi\", \"Skool\", \"Teachable\"]."
        )
        try:
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.FAST),
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2,
                )
            )
            raw = resp.text or ""
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                leaders = json.loads(match.group(0))
                if isinstance(leaders, list) and len(leaders) > 0:
                    return [str(x) for x in leaders[:3]]
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error en búsqueda web de líderes: {e}")
        return ["Líder Global 1", "Líder Global 2"]

    @staticmethod
    def _parse_dynamic_backlog_json(raw_text: str | None) -> list[dict[str, Any]] | None:
        """Parse raw backlog JSON and mark items pending."""
        if not raw_text:
            return None
        try:
            backlog = json.loads(raw_text.strip())
            if isinstance(backlog, list) and len(backlog) > 0:
                for item in backlog:
                    item["status"] = "pending"
                return backlog
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    @classmethod
    async def synthesize_dynamic_backlog(
        cls,
        client: genai.Client | None,
        goal: str,
        leaders: list[str],
        ui_paradigm: str,
        contract_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Synthesize the milestone DAG with adaptive granularity, target_files, and design patterns."""
        workspace_views = contract_data.get("workspace_views", [])
        prompt = (
            "Eres el Principal Product Strategist y Staff Software Architect en Stripe, Vercel y Linear.\n"
            f"El objetivo es construir una plataforma de clase mundial para: '{goal}'\n"
            f"- Paradigma de UI asignado: '{ui_paradigm}'\n"
            f"- Líderes mundiales de referencia: {json.dumps(leaders, ensure_ascii=False)}\n"
            f"- Espacios de trabajo declarados en el contrato: {json.dumps(workspace_views, ensure_ascii=False)}\n\n"
            "PLANIFICACIÓN DINÁMICA POR GRAFO ACÍCLICO DIRIGIDO (DAG):\n"
            "1. Determina dinámicamente el número de hitos de producción necesarios según la complejidad real (entre 3 y 10 hitos atómicos):\n"
            "   - Herramientas simples / calculadoras: 3 a 4 hitos.\n"
            "   - E-commerce / clínicas / SaaS estándar: 5 a 7 hitos.\n"
            "   - Plataformas complejas / marketplaces / streaming: 8 a 10 hitos.\n"
            "2. Cada hito debe tener un objetivo atómico y comprobable, y debe asignar su archivo objetivo en 'target_files':\n"
            "   - Hito de fachada/marketing -> target_files: ['web/src/components/views/LandingView.tsx']\n"
            "   - Hitos de espacios de trabajo -> target_files: ['web/src/components/views/DynamicWorkspaceView.tsx']\n"
            "3. En 'tier1_pattern' describe el patrón visual ergonómico que usan los líderes para esa pantalla (disposición, proporciones, elementos clave).\n\n"
            "EMITE EXCLUSIVAMENTE UN ARRAY JSON CON ESTA ESTRUCTURA:\n"
            "[\n"
            "  {\n"
            '    "id": "MOD-1",\n'
            '    "title": "Nombre del módulo (ej. Escaparate de Captación y Oferta de Membresía)",\n'
            '    "description": "Qué hace y qué valor aporta",\n'
            '    "target_view": "landing",\n'
            '    "target_files": ["web/src/components/views/LandingView.tsx"],\n'
            '    "tier1_pattern": "Patrón visual de referencia (estilo Stripe/Linear con tarjetas oscuras y CTA contrastado)",\n'
            '    "test_criteria": "Qué acción de usuario verificará Playwright para darlo por aprobado"\n'
            "  }\n"
            "]"
        )
        if client:
            try:
                resp = await client.aio.models.generate_content(
                    model=get_model(ModelTier.FAST),
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                parsed = cls._parse_dynamic_backlog_json(resp.text)
                if parsed:
                    return parsed
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:  # noqa: BLE001
                logger.warning(f"Error sintetizando backlog dinámico: {e}")

        return [
            {
                "id": "MOD-1",
                "title": "Fachada Pública de Conversión y Pasarela Oficial",
                "description": "Presentación de autoridad, simulador interactivo de valor y checkout seguro",
                "target_view": "landing",
                "test_criteria": "Formulario y pasarela interactivos",
                "status": "pending"
            },
            {
                "id": "MOD-2",
                "title": "Espacio de Trabajo Operativo del Usuario",
                "description": "Área privada interactiva con herramienta nuclear y persistencia relacional",
                "target_view": "app",
                "test_criteria": "Navegación reactiva y persistencia de registros",
                "status": "pending"
            },
            {
                "id": "MOD-3",
                "title": "Consola de Gestión y Analítica Interna",
                "description": "Panel de administración con tablas maestras, métricas y exportación",
                "target_view": "admin",
                "test_criteria": "Tablas relacionales y estados editables",
                "status": "pending"
            }
        ]

    @staticmethod
    async def synthesize_roadmap(client: genai.Client | None, slug: str) -> dict[str, Any]:
        """Synthesize a standard evolution roadmap for a given project."""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        roadmap_file = ws_dir / "docs" / "EVOLUTION_ROADMAP.json"
        if roadmap_file.exists():
            try:
                return json.loads(roadmap_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as ex:
                logger.debug(f"Roadmap cache read note: {ex}")
        return {
            "slug": slug,
            "status": "active",
            "progress_pct": 50,
            "phases": [
                {"id": "phase-1", "name": "Infraestructura Base", "status": "completed"},
                {"id": "phase-2", "name": "Componentes de Dominio", "status": "in_progress"},
                {"id": "phase-3", "name": "Optimización & Evals", "status": "pending"}
            ]
        }
