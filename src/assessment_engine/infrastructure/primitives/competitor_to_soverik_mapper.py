# core/primitives/competitor_to_soverik_mapper.py

import sqlite3
import json
import re
from typing import List, Dict, Any, Tuple, Set, Union, Optional
from dataclasses import dataclass, field

# ============================================================================
# CONTRATOS PREEXISTENTES (GATE 4 MANDATORIO - INVARIANTES AST PRESERVADOS)
# ============================================================================

@dataclass
class CompetitorDossier:
    compressed_dom_json: str = ""
    extracted_contracts: Dict[str, Any] = field(default_factory=dict)
    business_archetype: str = "direct_consultation"
    operational_forms: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compressed_dom_json": self.compressed_dom_json,
            "extracted_contracts": self.extracted_contracts,
            "business_archetype": self.business_archetype,
            "operational_forms": self.operational_forms,
        }

@dataclass
class SoverikComponentSpec:
    component_name: str
    typescript_interfaces: str
    python_models: str
    css_variables: Dict[str, str]
    wcag_contrast_valid: bool

# ============================================================================
# NUEVAS PRIMITIVAS RELACIONALES (ESTRICTAMENTE ADITIVAS)
# ============================================================================

@dataclass
class RelationalSchemaSpec:
    archetype: str
    ddl_statements: List[str]
    tables: List[str]
    typescript_models: str
    python_models: str
    seed_statements: List[str] = field(default_factory=list)

_SQLITE_RESERVED_WORDS: frozenset[str] = frozenset({
    "add", "all", "alter", "and", "as", "asc", "autoincrement", "between",
    "case", "check", "collate", "column", "commit", "constraint", "create",
    "default", "deferrable", "delete", "desc", "distinct", "drop", "else",
    "escape", "except", "exists", "foreign", "from", "group", "having",
    "in", "index", "insert", "intersect", "into", "is", "join", "limit",
    "not", "null", "on", "or", "order", "primary", "references", "select",
    "set", "table", "then", "to", "transaction", "union", "unique", "update",
    "values", "when", "where"
})

_INTEGER_TOKENS: frozenset[str] = frozenset({
    "doctor_id", "id", "edad", "cantidad", "count", "duracion"
})

_REAL_TOKENS: frozenset[str] = frozenset({
    "metro", "superficie", "presupuesto", "precio", "importe",
    "coste", "total", "amount", "m2"
})

_BOOLEAN_TOKENS: frozenset[str] = frozenset({
    "acepto", "is_", "has_", "activo", "terminos"
})

_CLEAN_IDENTIFIER_REGEX: re.Pattern = re.compile(r"[^a-zA-Z0-9_]")

def _sanitize_column_name(raw_name: str, fallback_idx: int = 1) -> str:
    """Sanitiza identificadores para prevenir colisiones de sintaxis e inyecciones DDL."""
    raw_str = str(raw_name).strip().lower()
    cleaned = _CLEAN_IDENTIFIER_REGEX.sub("_", raw_str)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")

    if not cleaned or cleaned[0].isdigit() or cleaned in _SQLITE_RESERVED_WORDS:
        return f"col_{cleaned or fallback_idx}"
    return cleaned[:64]

def infer_sql_column_type(field_name: str, field_type: str = "text") -> str:
    """Infiere el tipo de afinidad SQL SQLite con V(G) <= 6 y prioridad canónica."""
    norm_name = str(field_name).strip().lower()
    norm_type = str(field_type).strip().lower()

    if any(tok in norm_name for tok in _REAL_TOKENS):
        return "REAL"
    if any(tok in norm_name for tok in _INTEGER_TOKENS):
        return "INTEGER"
    if any(tok in norm_name for tok in _BOOLEAN_TOKENS):
        return "BOOLEAN"

    if norm_type in {"float", "decimal", "real"}:
        return "REAL"
    if norm_type in {"number", "integer", "int"}:
        return "INTEGER"
    if norm_type in {"bool", "boolean", "checkbox"}:
        return "BOOLEAN"

    return "TEXT"

def _map_sql_to_ts(sql_type: str) -> str:
    type_map = {"INTEGER": "number", "REAL": "number", "BOOLEAN": "boolean", "TEXT": "string"}
    return type_map.get(sql_type.upper(), "string")

def _map_sql_to_py(sql_type: str) -> str:
    type_map = {"INTEGER": "int", "REAL": "float", "BOOLEAN": "bool", "TEXT": "str"}
    return type_map.get(sql_type.upper(), "str")

def _extract_archetype(dossier: Any) -> str:
    if isinstance(dossier, dict):
        arch = dossier.get("business_archetype")
        if arch:
            return str(arch).lower()
        contracts = dossier.get("extracted_contracts", {})
        if isinstance(contracts, dict) and contracts.get("business_archetype"):
            return str(contracts["business_archetype"]).lower()
        return "direct_consultation"

    arch = getattr(dossier, "business_archetype", None)
    if arch:
        return str(arch).lower()
    contracts = getattr(dossier, "extracted_contracts", None)
    if isinstance(contracts, dict) and contracts.get("business_archetype"):
        return str(contracts["business_archetype"]).lower()
    return "direct_consultation"

def _extract_forms(dossier: Any) -> List[Dict[str, Any]]:
    if isinstance(dossier, dict):
        forms = dossier.get("operational_forms")
        if forms is not None:
            return list(forms)
        contracts = dossier.get("extracted_contracts", {})
        if isinstance(contracts, dict):
            return list(contracts.get("operational_forms", []))
        return []

    forms = getattr(dossier, "operational_forms", None)
    if forms is not None:
        return list(forms)
    contracts = getattr(dossier, "extracted_contracts", None)
    if isinstance(contracts, dict):
        return list(contracts.get("operational_forms", []))
    return []

def _get_form_fields(form: Any) -> List[Any]:
    if isinstance(form, dict):
        fields = form.get("fields", [])
        if not fields and "name" in form:
            return [form]
        return fields
    return getattr(form, "fields", [])

def _process_field(f: Any, seen: Set[str], columns: List[Tuple[str, str]], idx: int) -> None:
    if isinstance(f, dict):
        name = f.get("name")
        raw_type = f.get("type", "text")
    else:
        name = getattr(f, "name", None)
        raw_type = getattr(f, "type", "text")

    if not name:
        return

    clean_name = _sanitize_column_name(str(name), idx)
    if clean_name in seen:
        return

    seen.add(clean_name)
    sql_type = infer_sql_column_type(clean_name, str(raw_type))
    columns.append((clean_name, sql_type))

def _extract_dynamic_columns(forms: List[Dict[str, Any]], reserved_cols: Set[str]) -> List[Tuple[str, str]]:
    columns: List[Tuple[str, str]] = []
    seen: Set[str] = set(reserved_cols)
    idx = 1

    for form in forms:
        for f in _get_form_fields(form):
            _process_field(f, seen, columns, idx)
            idx += 1

    return columns

def _merge_table_columns(
    base_columns: List[Tuple[str, str, str]],
    dynamic_cols: List[Tuple[str, str]]
) -> str:
    """Merge base columns with dynamic columns, preventing duplicates."""
    cols_dict = {name.lower(): (name, sql_type, default) for name, sql_type, default in base_columns}
    for col_name, sql_type in dynamic_cols:
        lower_c = col_name.lower()
        if lower_c not in cols_dict:
            cols_dict[lower_c] = (col_name, sql_type, "")

    lines = []
    for name, sql_type, default in cols_dict.values():
        def_clause = f" {default}" if default else ""
        lines.append(f"    {name} {sql_type}{def_clause}")
    return ",\n".join(lines)

def _build_appointment_seeds(dossier_dict: dict) -> List[str]:
    brand = dossier_dict.get("brand_name", "Especialista Principal")
    sector = dossier_dict.get("sector", "Consulta Profesional")
    clean_brand = str(brand).replace("'", "''")
    clean_sector = str(sector).replace("'", "''")
    return [
        f"INSERT OR IGNORE INTO especialistas (id, nombre, especialidad, activo) VALUES (1, '{clean_brand}', '{clean_sector}', 1);",
        f"INSERT OR IGNORE INTO citas_agendadas (id, especialista_id, fecha_hora, estado, paciente_nombre) VALUES (1, 1, '2026-10-20 10:00', 'confirmada', 'Cita Inicial Demo');",
    ]

def _build_estimator_seeds(dossier_dict: dict) -> List[str]:
    vps = dossier_dict.get("value_propositions", [])
    if not vps:
        vps = ["Servicio Estándar"]
    seeds: List[str] = []
    for i, vp in enumerate(vps[:4]):
        clean_name = str(vp).replace("'", "''")
        seeds.append(
            f"INSERT OR IGNORE INTO servicios_catalogo (id, codigo_servicio, nombre, precio_base) VALUES ({i+1}, 'SRV-{i+1:03d}', '{clean_name}', 0.0);"
        )
    return seeds

def _build_transactional_seeds(dossier_dict: dict) -> List[str]:
    plans = dossier_dict.get("pricing_plans", [])
    if not plans:
        plans = [{"title": "Plan Estándar", "price_text": "29€"}, {"title": "Plan Pro", "price_text": "99€"}]
    seeds: List[str] = []
    for p in plans:
        title = p.get("title", "") if isinstance(p, dict) else getattr(p, "title", "")
        price_text = p.get("price_text", "") if isinstance(p, dict) else getattr(p, "price_text", "")
        m = re.search(r"(\d+(?:\.\d+)?)", str(price_text))
        num = float(m.group(1)) if m else 0.0
        sku = re.sub(r"[^a-zA-Z0-9_]", "_", title.lower()).strip("_") or "plan"
        clean_title = title.replace("'", "''")
        seeds.append(
            f"INSERT OR IGNORE INTO planes_tarifas (sku, nombre, importe, moneda) VALUES ('{sku}', '{clean_title}', {num}, 'EUR');"
        )
    return seeds

def _build_consultation_seeds(dossier_dict: dict) -> List[str]:
    channels = dossier_dict.get("conversion_channels", {})
    seeds: List[str] = []
    if "whatsapp" in channels and channels["whatsapp"]:
        target = str(channels["whatsapp"]).replace("'", "''")
        seeds.append(
            f"INSERT OR IGNORE INTO canales_atencion (id, tipo_canal, identificador, activo) VALUES (1, 'whatsapp', '{target}', 1);"
        )
    if "phone" in channels and channels["phone"]:
        target = str(channels["phone"]).replace("'", "''")
        seeds.append(
            f"INSERT OR IGNORE INTO canales_atencion (id, tipo_canal, identificador, activo) VALUES (2, 'phone', '{target}', 1);"
        )
    return seeds

def _build_appointment_schema(dynamic_cols: List[Tuple[str, str]], dossier_dict: Optional[dict] = None) -> RelationalSchemaSpec:
    tables = ["especialistas", "citas_agendadas"]
    base_cols = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", ""),
        ("especialista_id", "INTEGER", "NOT NULL"),
        ("fecha_hora", "TEXT", "DEFAULT ''"),
        ("estado", "TEXT", "NOT NULL DEFAULT 'pendiente'"),
        ("paciente_nombre", "TEXT", "DEFAULT ''"),
    ]
    cols_sql = _merge_table_columns(base_cols, dynamic_cols)

    ddl = [
        """CREATE TABLE IF NOT EXISTS especialistas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    especialidad TEXT NOT NULL,
    activo BOOLEAN DEFAULT 1
);""",
        f"""CREATE TABLE IF NOT EXISTS citas_agendadas (
{cols_sql},
    FOREIGN KEY (especialista_id) REFERENCES especialistas(id)
);"""
    ]

    ts_dyn = ("\n" + "\n".join(f"  {col}?: {_map_sql_to_ts(t)};" for col, t in dynamic_cols)) if dynamic_cols else ""
    py_dyn = ("\n" + "\n".join(f"    {col}: Optional[{_map_sql_to_py(t)}] = None" for col, t in dynamic_cols)) if dynamic_cols else ""

    ts_models = f"""export interface IEspecialistaRecord {{
  id: number;
  nombre: string;
  especialidad: string;
  activo: boolean;
}}

export interface ICitasAgendadasRecord {{
  id: number;
  especialista_id: number;
  fecha_hora: string;
  estado: string;
  paciente_nombre: string;{ts_dyn}
}}"""

    py_models = f"""from dataclasses import dataclass
from typing import Optional

@dataclass
class EspecialistaModel:
    id: int
    nombre: str
    especialidad: str
    activo: bool = True

@dataclass
class CitasAgendadasModel:
    id: int
    especialista_id: int
    fecha_hora: str
    estado: str
    paciente_nombre: str{py_dyn}"""

    seeds = _build_appointment_seeds(dossier_dict or {})
    return RelationalSchemaSpec("appointment_qualified", ddl, tables, ts_models, py_models, seed_statements=seeds)

def _build_estimator_schema(dynamic_cols: List[Tuple[str, str]], dossier_dict: Optional[dict] = None) -> RelationalSchemaSpec:
    tables = ["servicios_catalogo", "solicitudes_lead"]
    base_cols = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", ""),
        ("nombre_cliente", "TEXT", "DEFAULT ''"),
        ("contacto_nombre", "TEXT", "DEFAULT ''"),
        ("contacto_email", "TEXT", "DEFAULT ''"),
        ("metros_cuadrados", "REAL", "DEFAULT 0.0"),
        ("presupuesto_estimado", "REAL", "DEFAULT 0.0"),
        ("tipo_reforma", "TEXT", "DEFAULT 'integral'"),
    ]
    cols_sql = _merge_table_columns(base_cols, dynamic_cols)

    ddl = [
        """CREATE TABLE IF NOT EXISTS servicios_catalogo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_servicio TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    precio_base REAL NOT NULL
);""",
        f"""CREATE TABLE IF NOT EXISTS solicitudes_lead (
{cols_sql}
);"""
    ]

    ts_dyn = ("\n" + "\n".join(f"  {col}?: {_map_sql_to_ts(t)};" for col, t in dynamic_cols)) if dynamic_cols else ""
    py_dyn = ("\n" + "\n".join(f"    {col}: Optional[{_map_sql_to_py(t)}] = None" for col, t in dynamic_cols)) if dynamic_cols else ""

    ts_models = f"""export interface IServicioCatalogoRecord {{
  id: number;
  codigo_servicio: string;
  nombre: string;
  precio_base: number;
}}

export interface ISolicitudLeadRecord {{
  id: number;
  contacto_nombre: string;
  contacto_email: string;
  metros_cuadrados: number;
  presupuesto_estimado: number;
  tipo_reforma: string;{ts_dyn}
}}"""

    py_models = f"""from dataclasses import dataclass
from typing import Optional

@dataclass
class ServicioCatalogoModel:
    id: int
    codigo_servicio: str
    nombre: str
    precio_base: float

@dataclass
class SolicitudLeadModel:
    id: int
    contacto_nombre: str
    contacto_email: str
    metros_cuadrados: float = 0.0
    presupuesto_estimado: float = 0.0
    tipo_reforma: str = 'integral'{py_dyn}"""

    seeds = _build_estimator_seeds(dossier_dict or {})
    return RelationalSchemaSpec("estimator_quote", ddl, tables, ts_models, py_models, seed_statements=seeds)

def _build_transactional_schema(dynamic_cols: List[Tuple[str, str]], dossier_dict: Optional[dict] = None) -> RelationalSchemaSpec:
    tables = ["planes_tarifas", "suscripciones_pedidos"]
    base_cols = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", ""),
        ("plan_id", "INTEGER", "NOT NULL"),
        ("cliente_email", "TEXT", "DEFAULT ''"),
        ("estado_pago", "TEXT", "NOT NULL DEFAULT 'completado'"),
    ]
    cols_sql = _merge_table_columns(base_cols, dynamic_cols)

    ddl = [
        """CREATE TABLE IF NOT EXISTS planes_tarifas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    importe REAL NOT NULL,
    moneda TEXT NOT NULL DEFAULT 'EUR'
);""",
        f"""CREATE TABLE IF NOT EXISTS suscripciones_pedidos (
{cols_sql},
    FOREIGN KEY (plan_id) REFERENCES planes_tarifas(id)
);"""
    ]

    ts_dyn = ("\n" + "\n".join(f"  {col}?: {_map_sql_to_ts(t)};" for col, t in dynamic_cols)) if dynamic_cols else ""
    py_dyn = ("\n" + "\n".join(f"    {col}: Optional[{_map_sql_to_py(t)}] = None" for col, t in dynamic_cols)) if dynamic_cols else ""

    ts_models = f"""export interface IPlanTarifaRecord {{
  id: number;
  sku: string;
  nombre: string;
  importe: number;
  moneda: string;
}}

export interface ISuscripcionPedidoRecord {{
  id: number;
  plan_id: number;
  cliente_email: string;
  estado_pago: string;{ts_dyn}
}}"""

    py_models = f"""from dataclasses import dataclass
from typing import Optional

@dataclass
class PlanTarifaModel:
    id: int
    sku: str
    nombre: str
    importe: float
    moneda: str = 'EUR'

@dataclass
class SuscripcionPedidoModel:
    id: int
    plan_id: int
    cliente_email: str
    estado_pago: str = 'completado'{py_dyn}"""

    seeds = _build_transactional_seeds(dossier_dict or {})
    return RelationalSchemaSpec("transactional_direct", ddl, tables, ts_models, py_models, seed_statements=seeds)

def _build_consultation_schema(dynamic_cols: List[Tuple[str, str]], dossier_dict: Optional[dict] = None) -> RelationalSchemaSpec:
    tables = ["canales_atencion", "solicitudes_contacto"]
    base_cols = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", ""),
        ("canal_id", "INTEGER", ""),
        ("nombre_remitente", "TEXT", "DEFAULT ''"),
        ("mensaje", "TEXT", "DEFAULT ''"),
    ]
    cols_sql = _merge_table_columns(base_cols, dynamic_cols)

    ddl = [
        """CREATE TABLE IF NOT EXISTS canales_atencion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_canal TEXT NOT NULL,
    identificador TEXT NOT NULL,
    activo BOOLEAN DEFAULT 1
);""",
        f"""CREATE TABLE IF NOT EXISTS solicitudes_contacto (
{cols_sql},
    FOREIGN KEY (canal_id) REFERENCES canales_atencion(id)
);"""
    ]

    ts_dyn = ("\n" + "\n".join(f"  {col}?: {_map_sql_to_ts(t)};" for col, t in dynamic_cols)) if dynamic_cols else ""
    py_dyn = ("\n" + "\n".join(f"    {col}: Optional[{_map_sql_to_py(t)}] = None" for col, t in dynamic_cols)) if dynamic_cols else ""

    ts_models = f"""export interface ICanalAtencionRecord {{
  id: number;
  tipo_canal: string;
  identificador: string;
  activo: boolean;
}}

export interface ISolicitudContactoRecord {{
  id: number;
  canal_id?: number;
  nombre_remitente: string;
  mensaje: string;{ts_dyn}
}}"""

    py_models = f"""from dataclasses import dataclass
from typing import Optional

@dataclass
class CanalAtencionModel:
    id: int
    tipo_canal: str
    identificador: str
    activo: bool = True

@dataclass
class SolicitudContactoModel:
    id: int
    canal_id: Optional[int]
    nombre_remitente: str
    mensaje: str{py_dyn}"""

    seeds = _build_consultation_seeds(dossier_dict or {})
    return RelationalSchemaSpec("direct_consultation", ddl, tables, ts_models, py_models, seed_statements=seeds)

    return RelationalSchemaSpec("direct_consultation", ddl, tables, ts_models, py_models)


# ============================================================================
# CLASE PRINCIPAL DEL MAPPER (PRESERVANDO FIRMAS HISTÓRICAS)
# ============================================================================

class CompetitorToSoverikMapper:
    COMPONENTS = (
        "BookingCalendarView", "PricingConfigurator", "UniversalAuthModal",
        "DirectoryGrid", "DataGrid", "KanbanBoard", "CheckoutFlow",
        "UserProfile", "DashboardMetrics", "SettingsPanel",
        "NotificationCenter", "NavigationSidebar", "SearchBar",
        "FileUploader", "RichTextEditor", "ActivityFeed"
    )

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS component_specs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT NOT NULL,
                    typescript_interfaces TEXT NOT NULL,
                    python_models TEXT NOT NULL,
                    css_variables TEXT NOT NULL,
                    wcag_contrast_valid BOOLEAN NOT NULL
                )
            """)

    def _save_spec(self, spec: SoverikComponentSpec) -> None:
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("""
                INSERT INTO component_specs (
                    component_name, typescript_interfaces, python_models, css_variables, wcag_contrast_valid
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                spec.component_name,
                spec.typescript_interfaces,
                spec.python_models,
                json.dumps(spec.css_variables),
                spec.wcag_contrast_valid
            ))

    def _calculate_contrast_ratio(self, l1: float, l2: float) -> float:
        lum1 = l1 ** 2.2
        lum2 = l2 ** 2.2
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def map_dossier(self, dossier: CompetitorDossier) -> List[SoverikComponentSpec]:
        specs: List[SoverikComponentSpec] = []
        for comp in self.COMPONENTS:
            spec = self._generate_spec_for_component(comp, dossier)
            self._save_spec(spec)
            specs.append(spec)
        return specs

    def _generate_spec_for_component(self, component_name: str, dossier: CompetitorDossier) -> SoverikComponentSpec:
        css_vars: Dict[str, str] = {}
        for i in range(36):
            lightness = 0.1 + (i * 0.02)
            css_vars[f"--color-{component_name.lower()}-{i}"] = f"oklch({lightness:.2f} 0.1 250)"

        ratio = self._calculate_contrast_ratio(0.1, 0.1 + (35 * 0.02))
        contrast_valid = ratio >= 4.5

        source = str(dossier.extracted_contracts.get("source", "unknown"))

        ts_interface = (
            f"// SISP Contract for {component_name}\n"
            f"export interface I{component_name}State {{\n"
            f"  id: string;\n"
            f"  source: '{source}';\n"
            f"}}\n"
            f"// Reactivity: useMemo/useState native dispatch to FastAPI\n"
            f"export type {component_name}Action = {{ type: 'DISPATCH'; payload: I{component_name}State }};"
        )

        py_model = (
            f"from dataclasses import dataclass\n\n"
            f"@dataclass\n"
            f"class {component_name}Model:\n"
            f"    id: str\n"
            f"    source: str = '{source}'\n"
        )

        return SoverikComponentSpec(
            component_name=component_name,
            typescript_interfaces=ts_interface,
            python_models=py_model,
            css_variables=css_vars,
            wcag_contrast_valid=contrast_valid
        )

    # ------------------------------------------------------------------------
    # MÉTODOS DE ESQUEMA RELACIONAL (ADITIVOS)
    # ------------------------------------------------------------------------

    def generate_relational_schema(self, dossier: Any) -> RelationalSchemaSpec:
        """Genera el esquema relacional DDL, TS y Python según el arquetipo de negocio."""
        archetype = _extract_archetype(dossier)
        forms = _extract_forms(dossier)
        dossier_dict = dossier if isinstance(dossier, dict) else (dossier.to_dict() if hasattr(dossier, "to_dict") else {})

        if archetype == "appointment_qualified":
            reserved = {"id", "especialista_id", "fecha_hora", "estado", "paciente_nombre"}
            dynamic_cols = _extract_dynamic_columns(forms, reserved)
            return _build_appointment_schema(dynamic_cols, dossier_dict)

        if archetype == "estimator_quote":
            reserved = {"id", "contacto_nombre", "contacto_email", "metros_cuadrados", "presupuesto_estimado", "tipo_reforma"}
            dynamic_cols = _extract_dynamic_columns(forms, reserved)
            return _build_estimator_schema(dynamic_cols, dossier_dict)

        if archetype == "transactional_direct":
            reserved = {"id", "plan_id", "cliente_email", "estado_pago"}
            dynamic_cols = _extract_dynamic_columns(forms, reserved)
            return _build_transactional_schema(dynamic_cols, dossier_dict)

        reserved = {"id", "canal_id", "nombre_remitente", "mensaje"}
        dynamic_cols = _extract_dynamic_columns(forms, reserved)
        return _build_consultation_schema(dynamic_cols, dossier_dict)

    def apply_schema_to_db(self, schema_spec: RelationalSchemaSpec, db_path: str = "") -> None:
        """Aplica el esquema DDL garantizando WAL mode, foreign keys y manejo transaccional."""
        target_path = db_path if db_path else self.db_path
        with sqlite3.connect(target_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys = ON;")
            for ddl in schema_spec.ddl_statements:
                cursor.executescript(ddl)
            for seed in getattr(schema_spec, "seed_statements", []):
                cursor.execute(seed)
            conn.commit()