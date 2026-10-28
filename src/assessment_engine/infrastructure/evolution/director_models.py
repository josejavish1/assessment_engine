"""
Define data models, catalogs, and prescriptive recipes for the Autonomous Product Director.
Decoupled from autonomous_product_director.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from assessment_engine.infrastructure.evolution.epistemic_distiller import ProductStrategyDossier


@dataclass
class ProductGap:
    """Represent a legitimate implementation gap detected against the baseline or audit."""
    id: str
    description: str
    target_module: str
    is_yagni_approved: bool = True  # Determine implementation status via the YAGNI filter (True = implement, False = discard).

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)


@dataclass
class LocalBoundaryScope:
    """Define the mission scope and impact radius on the local codebase (Step 0)."""
    task: str
    symbol_map_summary: str
    impacted_files: list[str] = field(default_factory=list)
    topological_order: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    baseline_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)


@dataclass
class ModulePlan:
    """Define the blueprint of an individual module to synthesize within the mission (Step 2)."""
    id: str
    name: str
    target_file: str
    test_file: str
    purpose: str
    invariants: list[str] = field(default_factory=list)
    is_yagni_approved: bool = True
    veto_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class PrescriptiveRecipe:
    """Represent a formal refactoring recipe issued for an audit finding."""
    rule_id: str
    target_symbol: str
    recommended_pattern: str
    actionable_instructions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)

    def to_prompt_context(self) -> str:
        """Serialize the recipe into a refactoring instruction block for the AI."""
        inst = "\n".join(f"- {i}" for i in self.actionable_instructions)
        forb = "\n".join(f"- {f}" for f in self.forbidden_actions)
        return (
            f"### RECETA PRESCRIPTIVA DE REFACTORIZACIÓN [{self.rule_id}]\n"
            f"**Símbolo Objetivo:** `{self.target_symbol}` | **Patrón:** {self.recommended_pattern}\n\n"
            f"#### INSTRUCCIONES ACCIONABLES OBLIGATORIAS:\n{inst}\n\n"
            f"#### ACCIONES ESTRICTAMENTE PROHIBIDAS (ANTI-REGRESIÓN):\n{forb}\n"
        )


@dataclass
class MissionReport:
    """Represent the final certification report for the completed mission."""
    task: str
    status: str
    iterations: int
    halt_reason: str
    modules_planned: list[ModulePlan]
    dossier: ProductStrategyDossier | None = None
    final_gaps: list[ProductGap] = field(default_factory=list)
    history_hashes: list[str] = field(default_factory=list)
    recipes_applied: list[PrescriptiveRecipe] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return {
            "task": self.task,
            "status": self.status,
            "iterations": self.iterations,
            "halt_reason": self.halt_reason,
            "modules_planned": [m.to_dict() for m in self.modules_planned],
            "dossier": self.dossier.to_dict() if self.dossier else None,
            "final_gaps": [g.to_dict() for g in self.final_gaps],
            "history_hashes": self.history_hashes,
            "recipes_applied": [r.to_dict() for r in self.recipes_applied],
        }


@dataclass(frozen=True)
class LocalCapability:
    domain: str
    native_technology: str
    substitute_name: str
    substitute_purpose: str
    keywords: tuple[str, ...]


LOCAL_CAPABILITIES: dict[str, LocalCapability] = {
    "persistence": LocalCapability(
        domain="Persistencia y Base de Datos",
        native_technology="SQLite WAL local",
        substitute_name="Persistencia Local SQLite WAL (Transcrito)",
        substitute_purpose="Almacenamiento ACID local en SQLite WAL a coste $0.00 y llamadas a endpoints API locales",
        keywords=("firebase", "firestore", "supabase", "mongodb", "postgres cloud", "dynamodb", "couchdb"),
    ),
    "cache": LocalCapability(
        domain="Caché y Estado Reactivo",
        native_technology="Caché en Memoria SWR Local",
        substitute_name="Caché en Memoria SWR Local (Transcrito)",
        substitute_purpose="Caché en memoria RAM local con revalidación en foco a 60 FPS sin dependencias de red",
        keywords=("redis", "memcached", "upstash", "dragonfly"),
    ),
    "search": LocalCapability(
        domain="Búsqueda Full-Text",
        native_technology="SQLite FTS5 nativo",
        substitute_name="Búsqueda Local SQLite FTS5 (Transcrito)",
        substitute_purpose="Índice invertido de búsqueda rápida FTS5 nativo en SQLite a coste $0.00",
        keywords=("algolia", "elasticsearch", "typesense", "meilisearch"),
    ),
    "realtime": LocalCapability(
        domain="Streaming y Notificaciones",
        native_technology="Server-Sent Events (SSE) nativo",
        substitute_name="Streaming Unidireccional SSE (Transcrito)",
        substitute_purpose="Transmisión unidireccional HTTP/2 SSE y revalidación SWR a coste $0.00",
        keywords=("pusher", "socket.io", "ably", "pubnub", "websocket cluster"),
    ),
    "antispam": LocalCapability(
        domain="Protección Anti-Bot y Formularios",
        native_technology="Honeypot Criptográfico HMAC-SHA256",
        substitute_name="Honeypot Criptográfico Anti-Spam (Transcrito)",
        substitute_purpose="Blindaje OWASP OAT-017 con campo señuelo rotativo y HMAC-SHA256 a coste $0.00",
        keywords=("recaptcha", "hcaptcha", "turnstile", "arkose"),
    ),
    "queue": LocalCapability(
        domain="Colas y Tareas Asíncronas",
        native_technology="Cola Transaccional SQLite + Asyncio",
        substitute_name="Cola Transaccional SQLite (Transcrito)",
        substitute_purpose="Cola atómica en SQLite WAL con locks transaccionales y workers asyncio a coste $0.00",
        keywords=("kafka", "rabbitmq", "sqs", "celery", "bullmq"),
    ),
    "storage": LocalCapability(
        domain="Archivos y Documentos",
        native_technology="Almacenamiento Local Estructurado",
        substitute_name="Almacenamiento Efímero Local (Transcrito)",
        substitute_purpose="Almacenamiento en disco local estructurado bajo directorio working/out/ a coste $0.00",
        keywords=("aws s3", "gcs", "azure blob", "cloudinary", "uploadthing"),
    ),
    "auth": LocalCapability(
        domain="Autenticación e Identidad",
        native_technology="W3C Passkeys FIDO2 y Cookies HTTPOnly",
        substitute_name="Autenticación Nativa Passkeys (Transcrito)",
        substitute_purpose="Autenticación biométrica W3C WebAuthn Nivel 3 y tokens firmados con HMAC a coste $0.00",
        keywords=("clerk", "auth0", "stytch", "kinde", "firebase auth"),
    ),
}

FOWLER_RECIPE_BOOK: dict[str, dict[str, Any]] = {
    "ARCH-DEEP-NESTING": {
        "pattern": "Guard Clauses (Early Return)",
        "instructions": (
            "Invertir los condicionales profundamente anidados (if cond:) en cláusulas de guarda con early return (if not cond: return/continue).",
            "Mantener el nivel de indentación máximo en 2 niveles de profundidad.",
            "Desacoplar bloques de control anidados en comprobaciones preliminares al inicio de la función.",
        ),
        "forbidden": (
            "Prohibido capturar excepciones genéricas con 'except Exception: pass' para eludir bloques de control.",
            "Prohibido eliminar validaciones de casos borde o comprobaciones de tipos.",
        ),
    },
    "ARCH-COGNITIVE-OVERLOAD": {
        "pattern": "Extract Method (Funciones Puras Deterministas)",
        "instructions": (
            "Extraer el bloque interior del bucle o el cálculo complejo a una función auxiliar privada con prefijo '_process_*' o '_calculate_*'.",
            "La función auxiliar debe ser pura: recibir sus dependencias explícitamente por argumento y devolver el resultado sin mutar estado global.",
            "Asegurar que la complejidad ciclomática de la función principal baje a V(G) <= 10.",
        ),
        "forbidden": (
            "Prohibido almacenar estado intermedio en variables globales de módulo.",
            "Prohibido cambiar la firma pública ni los tipos de los argumentos de la función original.",
        ),
    },
    "ARCH-GOD-MODULE": {
        "pattern": "Separation of Concerns (Domain Decoupling)",
        "instructions": (
            "Extraer definiciones de modelos Pydantic o dataclasses a un archivo 'schema.py' o 'models.py' satélite.",
            "Extraer funciones auxiliares de bajo nivel a un submódulo 'helpers.py'.",
        ),
        "forbidden": (
            "Prohibido recortar comentarios explicativos o docstrings para reducir SLOC artificialmente.",
        ),
    },
    "SAST-SQL-INJECTION": {
        "pattern": "Parameterized Query Binding (CWE-89 Remediation)",
        "instructions": (
            "Eliminar cualquier concatenación de strings o f-strings en sentencias SQL.",
            "Usar marcadores de posición '?' en SQLite y pasar tupla de parámetros seguros: cursor.execute('... WHERE id = ?;', (val,)).",
        ),
        "forbidden": (
            "Prohibido el escape manual de comillas con .replace(\"'\", \"''\").",
        ),
    },
    "CODE-HYGIENE-UNTYPED": {
        "pattern": "Strict Type Annotations (PEP 484 / PEP 561)",
        "instructions": (
            "Añadir anotaciones de tipo explícitas a todos los argumentos y al tipo de retorno de la función.",
            "Usar tipos de la biblioteca estándar (Path, str, int, dict[str, Any], tuple, etc.).",
        ),
        "forbidden": (
            "Prohibido el uso de 'Any' o casts de bypass sin justificación.",
            "Prohibido eludir comprobaciones con '# type: ignore'.",
        ),
    },
}
