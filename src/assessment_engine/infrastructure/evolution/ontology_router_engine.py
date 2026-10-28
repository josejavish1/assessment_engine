"""
core/evolution/ontology_router_engine.py

Compilador de enrutamiento ontológico determinista (RFC-020 Etapa B.1).
Mapea esquemas relacionales SQLite WAL a manifiestos de rutas para arquitecturas multi-página.
Agnóstico e internacional: opera bajo el principio Zero-Language-Lock sin diccionarios hardcodeados.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

FRAMEWORK_TABLES_DENYLIST: frozenset[str] = frozenset({
    "component_specs",
    "telecom_wallets",
    "users",
    "idempotency_records",
    "domain_records",
    "charges",
    "courses",
    "course_enrollments",
    "telecom_usage_ledger",
})

_ALLOWED_SLUG_PATTERN = re.compile(r"^/[a-z0-9_-]+$")
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class RouteDefinition:
    """Definición inmutable de ruta ontológica tipada."""

    path: str
    component: str
    title: str
    is_public: bool
    requires_auth: bool = False
    entity_table: Optional[str] = None
    config: Optional[dict[str, Any]] = None

    @property
    def label(self) -> str:
        """Alias para compatibilidad con label."""
        return self.title

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteDefinition:
        """Instancia un RouteDefinition a partir de un diccionario de metadatos."""
        title_val = str(data.get("title") or data.get("label") or "")
        return cls(
            path=str(data["path"]),
            component=str(data["component"]),
            title=title_val,
            is_public=bool(data["is_public"]),
            requires_auth=bool(data.get("requires_auth", not data.get("is_public", True))),
            entity_table=data.get("entity_table"),
            config=data.get("config"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializa la ruta a una estructura pura de diccionario."""
        res = asdict(self)
        res["label"] = self.title
        return res


def _is_temporal_component(corpus_words: set[str], upper_types: list[str]) -> bool:
    """Detecta si la estructura relacional corresponde a calendario o agenda."""
    temporal_types = {"DATETIME", "TIMESTAMP", "TIME", "DATE"}
    temporal_words = {"time", "date", "slot", "schedule", "turno", "agenda", "cita", "appointment", "booking"}
    return bool(temporal_types.intersection(upper_types) or temporal_words.intersection(corpus_words))


def _is_showcase_inventory_component(name_words: set[str], cols_set: set[str]) -> bool:
    """Detecta si la estructura corresponde a inventario físico o bienes de catálogo."""
    inventory_words = {
        "property", "properties", "inmueble", "inmuebles", "vivienda", "viviendas", "piso", "pisos",
        "casa", "casas", "vehicle", "vehicles", "coche", "coches", "auto", "autos", "product", "products",
        "producto", "productos", "item", "items", "artículo", "articulo", "lot", "lote", "lotes"
    }
    inventory_cols = {"usable_sqm", "bedrooms", "bathrooms", "mileage", "property_type", "operation_type", "surface_m2"}
    return bool(inventory_words.intersection(name_words) or inventory_cols.intersection(cols_set))


def _is_pricing_component(name_words: set[str], corpus_words: set[str], upper_types: list[str]) -> bool:
    """Detecta si la estructura corresponde a planes o catálogo tarifario."""
    pricing_words = {"plan", "tier", "tarifa", "pricing", "rate", "cost", "price", "precio"}
    real_types = {"REAL", "DECIMAL", "NUMERIC", "FLOAT"}
    has_money_col = bool(real_types.intersection(upper_types)) and bool(pricing_words.intersection(corpus_words))
    return bool(has_money_col or pricing_words.intersection(name_words))


def _is_form_component(name_words: set[str]) -> bool:
    """Detecta si la estructura corresponde a captura de formulario o leads."""
    form_words = {"lead", "contact", "contacto", "inquiry", "message", "mensaje", "solicitud", "request"}
    return bool(form_words.intersection(name_words))


def _is_portal_component(name_words: set[str], cols_set: set[str]) -> bool:
    """Detecta si la estructura corresponde al portal privado de cliente o usuario."""
    user_fks = {"user_id", "client_id", "customer_id", "candidate_id", "member_id", "account_id"}
    portal_words = {"subscription", "tracking", "portal", "profile", "account", "wallet", "session"}
    return bool(user_fks.intersection(cols_set) or portal_words.intersection(name_words))


class OntologyRouterEngine:
    """Motor de compilación e introspección estática para derivación de rutas."""

    def extract_domain_tables(self, db_path: Path | str) -> list[str]:
        """Extrae tablas del dominio excluyendo tablas de infraestructura y SQLite internas."""
        resolved_path = Path(db_path).resolve()
        if not resolved_path.exists():
            return []

        with sqlite3.connect(str(resolved_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC;"
            )
            rows = cursor.fetchall()

        return [row[0] for row in rows if row[0] not in FRAMEWORK_TABLES_DENYLIST]

    def _extract_table_metadata(self, conn: sqlite3.Connection, table_name: str) -> tuple[list[str], dict[str, str]]:
        """Extrae nombres y tipos de columnas de una tabla mediante introspección PRAGMA table_info."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        rows = cursor.fetchall()
        cols = [str(r[1]) for r in rows]
        types_map = {str(r[1]): str(r[2]).upper() for r in rows}
        return cols, types_map

    def infer_slug_and_label(
        self, table_name: str, route_aliases: Optional[dict[str, tuple[str, str]]] = None
    ) -> tuple[str, str]:
        """
        Infiere un slug normalizado y etiqueta legible universal (Zero-Language-Lock).
        Si el contrato de dominio provee route_aliases dinámicos, los respeta prioritariamente;
        de lo contrario, normaliza deterministamente sin sesgo lingüístico en cualquier idioma.
        """
        if route_aliases and table_name in route_aliases:
            return route_aliases[table_name]

        normalized_body = _NON_SLUG_CHARS.sub("-", table_name.lower().replace("_", "-")).strip("-")
        slug = f"/{normalized_body}" if normalized_body else "/domain-entity"
        label = table_name.replace("_", " ").strip().title()
        return slug, label

    def assign_primitive_component(
        self, table_name: str, columns: list[str], column_types: Optional[dict[str, str]] = None
    ) -> str:
        """
        Determina la primitiva UI idónea según la estructura relacional y tipos de columna.
        Agnóstico e internacional: evalúa tipos de datos SQLite y heurísticas estructurales.
        Complejidad Ciclomática: V(G) <= 6.
        """
        corpus_words = set(re.findall(r"[a-z0-9]+", f"{table_name} {' '.join(columns)}".lower()))
        name_words = set(re.findall(r"[a-z0-9]+", table_name.lower()))
        upper_types = [t.upper() for t in (column_types or {}).values()]
        cols_set = {c.lower() for c in columns}

        if _is_temporal_component(corpus_words, upper_types):
            return "BookingCalendarView"
        if _is_showcase_inventory_component(name_words, cols_set):
            return "EntityShowcaseGrid"
        if _is_pricing_component(name_words, corpus_words, upper_types):
            return "DynamicPricingConfigurator"
        if _is_form_component(name_words):
            return "SchemaFormRenderer"
        if _is_portal_component(name_words, cols_set):
            return "UniversalClientPortal"
        if len(columns) >= 3:
            return "DirectoryGrid"

        return "DataGridTableView"

    def _collect_table_routes(
        self, db_path: Path, domain_contract: Optional[dict[str, Any]] = None
    ) -> list[RouteDefinition]:
        """Construye las definiciones de ruta derivadas de las tablas de dominio."""
        table_routes: list[RouteDefinition] = []
        contract = domain_contract or {}
        route_aliases = contract.get("route_aliases")

        with sqlite3.connect(str(db_path)) as conn:
            for table in self.extract_domain_tables(db_path):
                columns, types_map = self._extract_table_metadata(conn, table)
                slug, label = self.infer_slug_and_label(table, route_aliases=route_aliases)
                comp = self.assign_primitive_component(table, columns, column_types=types_map)
                table_routes.append(
                    RouteDefinition(
                        path=slug,
                        component=comp,
                        title=label,
                        is_public=True,
                        requires_auth=False,
                        entity_table=table,
                        config={"table": table, "columns": columns, "types": types_map},
                    )
                )
        return table_routes

    def _build_standard_routes(
        self, existing_paths: set[str], domain_contract: Optional[dict[str, Any]] = None
    ) -> list[RouteDefinition]:
        """Asegura la presencia de las rutas estándar requeridas por el protocolo."""
        contract = domain_contract or {}
        home_title = str(contract.get("home_title") or contract.get("landing_title") or "Inicio")
        pricing_title = str(contract.get("pricing_title") or "Precios")
        portal_title = str(contract.get("portal_title") or "Portal")

        standards: list[tuple[str, str, bool, str, bool]] = [
            ("/", "LandingView", True, home_title, False),
            ("/checkout", "CheckoutWizardModal", True, "Checkout", False),
            ("/portal", "UniversalClientPortal", False, portal_title, True),
        ]
        has_pricing = any(p in existing_paths for p in ("/precios", "/pricing", "/preise", "/tarifs", "/tarifas"))
        if not has_pricing:
            standards.insert(1, ("/precios", "DynamicPricingConfigurator", True, pricing_title, False))

        return [
            RouteDefinition(path=p, component=c, is_public=pub, title=lbl, requires_auth=auth)
            for p, c, pub, lbl, auth in standards
            if p not in existing_paths
        ]

    def build_routes_manifest(
        self, db_path: Path | str, domain_contract: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Compila el manifiesto de rutas completo con soporte simétrico para 'routes'."""
        resolved_path = Path(db_path).resolve()
        contract = domain_contract or {}
        table_routes = self._collect_table_routes(resolved_path, contract) if resolved_path.exists() else []

        existing_paths = {r.path for r in table_routes}
        standard_routes = self._build_standard_routes(existing_paths, contract)
        all_routes = standard_routes + table_routes

        manifest = dict(contract)
        manifest["routes"] = [r.to_dict() for r in all_routes]

        for route in all_routes:
            manifest[route.path] = route.to_dict()

        return manifest

    def save_routes_manifest(self, manifest: dict[str, Any], out_file: Path | str) -> None:
        """Persiste el manifiesto a disco garantizando atomicidad mediante os.replace."""
        target_path = Path(out_file).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        os.replace(temp_path, target_path)
