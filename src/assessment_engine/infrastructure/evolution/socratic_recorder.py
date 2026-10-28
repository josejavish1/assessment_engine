"""
Socratic Calibration Knowledge Base — Ingeniería Inversa de Preguntas Dinámicas.
Almacena en SQLite WAL todos los casos de estudio, prompts, preguntas formuladas por Emergent,
opciones con su etiqueta (Recomendado) y el mapeo exacto hacia nuestras 16 primitivas fullstack.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.evolution.socratic_recorder")

DB_PATH = Path("storage/data/socratic_calibration.db")


def init_socratic_db() -> None:
    """Initialize relational schema in SQLite WAL for Socratic calibration."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB_PATH), timeout=60.0) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS calibration_cases (
                id TEXT PRIMARY KEY,
                domain_name TEXT NOT NULL,
                sector TEXT NOT NULL,
                initial_prompt TEXT NOT NULL,
                agent_reaction TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS calibration_questions (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                question_index INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                options_json TEXT NOT NULL,
                recommended_option TEXT,
                architectural_intent TEXT NOT NULL,
                mapped_primitives_json TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES calibration_cases(id) ON DELETE CASCADE
            );
        """)

        conn.commit()


def record_case(
    case_id: str,
    domain_name: str,
    sector: str,
    initial_prompt: str,
    agent_reaction: str,
    questions: list[dict[str, Any]],
) -> None:
    """Insert or replace full case with associated questions and primitive mappings."""
    init_socratic_db()
    with sqlite3.connect(str(DB_PATH), timeout=60.0) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO calibration_cases (id, domain_name, sector, initial_prompt, agent_reaction)
            VALUES (?, ?, ?, ?, ?);
            """,
            (case_id, domain_name, sector, initial_prompt, agent_reaction),
        )

        cur.execute("DELETE FROM calibration_questions WHERE case_id = ?;", (case_id,))

        for q in questions:
            cur.execute(
                """
                INSERT INTO calibration_questions (
                    id, case_id, question_index, question_text, options_json,
                    recommended_option, architectural_intent, mapped_primitives_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    f"{case_id}_q{q['question_index']}",
                    case_id,
                    q["question_index"],
                    q["question_text"],
                    json.dumps(q["options"], ensure_ascii=False),
                    q.get("recommended_option", ""),
                    q["architectural_intent"],
                    json.dumps(q["mapped_primitives"], ensure_ascii=False),
                ),
            )
        conn.commit()
    invalidate_knowledge_cache()


_KNOWLEDGE_RAM_CACHE: list[dict[str, Any]] | None = None


def invalidate_knowledge_cache() -> None:
    """Invalidate in-memory RAM cache when a new case is recorded."""
    global _KNOWLEDGE_RAM_CACHE
    _KNOWLEDGE_RAM_CACHE = None


def get_all_calibration_knowledge(force_refresh: bool = False) -> list[dict[str, Any]]:
    """Retrieve all calibration cases using single indexed query and 0.05ms RAM cache."""
    global _KNOWLEDGE_RAM_CACHE
    if _KNOWLEDGE_RAM_CACHE is not None and not force_refresh:
        return _KNOWLEDGE_RAM_CACHE

    if not DB_PATH.exists():
        return []

    with sqlite3.connect(str(DB_PATH), timeout=60.0) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                c.id, c.domain_name, c.sector, c.initial_prompt, c.agent_reaction,
                q.id, q.question_index, q.question_text, q.options_json,
                q.recommended_option, q.architectural_intent, q.mapped_primitives_json
            FROM calibration_cases c
            LEFT JOIN calibration_questions q ON c.id = q.case_id
            ORDER BY c.created_at ASC, q.question_index ASC;
            """
        )
        rows = cur.fetchall()

    cases_map: dict[str, dict[str, Any]] = {}
    for r in rows:
        c_id = r[0]
        if c_id not in cases_map:
            cases_map[c_id] = {
                "id": c_id,
                "domain_name": r[1],
                "sector": r[2],
                "initial_prompt": r[3],
                "agent_reaction": r[4],
                "questions": [],
            }
        if r[5] is not None:
            cases_map[c_id]["questions"].append(
                {
                    "question_index": r[6],
                    "question_text": r[7],
                    "options": json.loads(r[8]),
                    "recommended_option": r[9],
                    "architectural_intent": r[10],
                    "mapped_primitives": json.loads(r[11]),
                }
            )

    _KNOWLEDGE_RAM_CACHE = list(cases_map.values())
    return _KNOWLEDGE_RAM_CACHE


def find_relevant_cases(query_text: str, sector: str | None = None, limit: int = 3) -> list[dict[str, Any]]:
    """Find nearest reference cases using token overlap and sector matching."""
    all_cases = get_all_calibration_knowledge()
    if not all_cases:
        return []

    tokens = set(re.findall(r"\w+", (query_text + " " + (sector or "")).lower()))
    scored_cases: list[tuple[float, dict[str, Any]]] = []

    for c in all_cases:
        c_tokens = set(re.findall(r"\w+", (c["domain_name"] + " " + c["sector"] + " " + c["initial_prompt"]).lower()))
        intersection = len(tokens & c_tokens)
        union = len(tokens | c_tokens)
        jaccard = intersection / union if union else 0.0
        if sector and sector.lower() in c["sector"].lower():
            jaccard += 0.3
        scored_cases.append((jaccard, c))

    scored_cases.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_cases[:limit]]


_SECTOR_ALIASES_MAP: dict[str, str] | None = None


def _get_sector_aliases_map() -> dict[str, str]:
    """Lazy load canonical sector alias index into RAM cache (280 KB)."""
    global _SECTOR_ALIASES_MAP
    if _SECTOR_ALIASES_MAP is None:
        p = Path(__file__).resolve().parent / "sector_aliases.json"
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _SECTOR_ALIASES_MAP = data.get("alias_to_sector", {})
            except Exception:
                _SECTOR_ALIASES_MAP = {}
        else:
            _SECTOR_ALIASES_MAP = {}
    return _SECTOR_ALIASES_MAP


def _match_canonical_alias_fast_path(
    words: list[str], alias_map: dict[str, str], all_cases: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Stage 1: Match canonical sector aliases using bigrams and unigrams."""
    from assessment_engine.infrastructure.evolution.orthogonal_archetypes import ARCHETYPE_STOP_WORDS

    matched_sector = None
    for i in range(len(words)):
        if i + 1 < len(words):
            bigram = f"{words[i]} {words[i+1]}"
            if bigram in alias_map and not any(w in ARCHETYPE_STOP_WORDS for w in bigram.split()):
                matched_sector = alias_map[bigram]
                break
        if words[i] in alias_map and words[i] not in ARCHETYPE_STOP_WORDS and len(words[i]) > 3:
            matched_sector = alias_map[words[i]]
            break

    if not matched_sector:
        return None

    matched_l = matched_sector.lower()
    matched_tokens = set(re.findall(r"\w+", matched_l)) - {"y", "de", "e", "la", "el", "en", "para", "con"}
    for c in all_cases:
        c_sec = c.get("sector", "").lower()
        c_tokens = set(re.findall(r"\w+", c_sec))
        if c_sec == matched_l or matched_l in c_sec or c_sec in matched_l or len(matched_tokens & c_tokens) >= 2:
            return c
    return None


GENERIC_STOP_WORDS: frozenset[str] = frozenset({
    "en", "los", "las", "con", "de", "del", "un", "una", "unos", "unas", "para", "por", "y", "el", "la", "que", "es",
    "como", "quiero", "crear", "plataforma", "hacer", "sistema", "portal", "web", "app", "tipo",
    "estilo", "servicio", "online", "digital", "nuevo", "nueva", "montar", "lanzar", "poner", "abrir",
    "iniciar", "desarrollar", "programar", "construir", "diseñar", "armar", "tener", "necesito",
    "gustaria", "quisiera", "deseo", "software", "sitio", "página", "pagina", "negocio", "empresa", "algo"
})


def _match_jaccard_fallback(
    words: list[str], all_cases: list[dict[str, Any]], threshold: float
) -> dict[str, Any] | None:
    """Stage 2: Fallback Jaccard search over extracted core keyword tokens."""
    q_keywords = {w for w in words if len(w) > 3 and w not in GENERIC_STOP_WORDS}
    if not q_keywords:
        return None

    best_similarity = 0.0
    best_case: dict[str, Any] | None = None

    for c in all_cases:
        c_prompt = c.get("initial_prompt", "")
        c_keywords = {w for w in re.findall(r"\w+", c_prompt.lower()) if len(w) > 3 and w not in GENERIC_STOP_WORDS}
        if not c_keywords:
            continue
        
        intersection = len(q_keywords & c_keywords)
        union = len(q_keywords | c_keywords)
        similarity = intersection / union if union > 0 else 0.0

        if similarity > best_similarity:
            best_similarity = similarity
            best_case = c

    if best_similarity >= threshold and best_case:
        return best_case
    return None


def check_semantic_cache(query_text: str, threshold: float = 0.80) -> dict[str, Any] | None:
    """Two-stage semantic cache using canonical aliases and Jaccard fallback."""
    clean_q = query_text.lower().strip()
    words = re.findall(r"\w+", clean_q)
    alias_map = _get_sector_aliases_map()
    all_cases = get_all_calibration_knowledge()

    match_alias = _match_canonical_alias_fast_path(words, alias_map, all_cases)
    if match_alias:
        return match_alias

    return _match_jaccard_fallback(words, all_cases, threshold)


def save_calibration_to_cache(
    prompt: str,
    domain_name: str,
    sector: str,
    questions: list[dict[str, Any]],
    welcome_insight: str = "",
) -> None:
    """Persist successfully calibrated result into SQLite WAL semantic cache."""
    import hashlib
    clean_p = prompt.strip().lower()
    case_id = f"socr_{hashlib.sha256(clean_p.encode('utf-8')).hexdigest()[:12]}"
    record_case(
        case_id=case_id,
        domain_name=domain_name,
        sector=sector,
        initial_prompt=prompt,
        agent_reaction=welcome_insight,
        questions=questions,
    )


def seed_reference_cases() -> None:
    """Seed initial golden reference calibration cases if table is uninitialized."""
    case_1_questions = [
        {
            "question_index": 1,
            "question_text": "¿Qué alcance quieres para la web de Nocturnus?",
            "options": [
                {"label": "Landing inmersiva de una página", "description": "hero cinematográfico, suites, experiencias, chef, biblioteca y solicitud de plaza", "is_recommended": True},
                {"label": "Multi-página", "description": "secciones separadas con navegación propia para suites, experiencias y contacto", "is_recommended": False},
                {"label": "Landing + zona privada", "description": "además, acceso reservado para huéspedes confirmados", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado por el usuario", "is_recommended": False},
            ],
            "recommended_option": "Landing inmersiva de una página",
            "architectural_intent": "Topología visual y profundidad de enrutamiento (Single Page vs Multi-route)",
            "mapped_primitives": ["DynamicSchemaForms", "LandingView"],
        },
        {
            "question_index": 2,
            "question_text": "¿En qué idioma va el contenido?",
            "options": [
                {"label": "Español", "description": "todo el contenido en español", "is_recommended": True},
                {"label": "Inglés", "description": "estética internacional de lujo", "is_recommended": False},
                {"label": "Bilingüe", "description": "selector ES/EN en la web", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado", "is_recommended": False},
            ],
            "recommended_option": "Español",
            "architectural_intent": "Localización i18n y tono del copywriting (Directo vs Internacional)",
            "mapped_primitives": ["IntlFormatter", "DomainContract"],
        },
        {
            "question_index": 3,
            "question_text": "¿Cómo se gestionan las solicitudes de estancia?",
            "options": [
                {"label": "Formulario con panel de administración", "description": "las solicitudes se guardan y las revisas en un panel privado", "is_recommended": True},
                {"label": "Solo formulario de contacto", "description": "sin panel, respuestas manuales por email", "is_recommended": False},
                {"label": "Sin formulario", "description": "solo botón de acceso-solicitud decorativo", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado", "is_recommended": False},
            ],
            "recommended_option": "Formulario con panel de administración",
            "architectural_intent": "Persistencia de base de datos y topología bimodal (Client Portal + Admin Panel)",
            "mapped_primitives": ["DynamicSchemaForms", "RebacEngine", "AuditTrailLedger"],
        },
        {
            "question_index": 4,
            "question_text": "¿Quieres pagos para reservar plaza?",
            "options": [
                {"label": "Sin pagos", "description": "la estancia se confirma de forma privada, como en el lujo real", "is_recommended": True},
                {"label": "Stripe para depósito", "description": "pago de reserva de test con tarjeta", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado", "is_recommended": False},
            ],
            "recommended_option": "Sin pagos",
            "architectural_intent": "Motor de monetización y pasarela de cobro (Checkout vs Private Concierge)",
            "mapped_primitives": ["CheckoutWizardModal", "CommunicationsHubView"],
        },
    ]

    record_case(
        case_id="case_nocturnus_vault",
        domain_name="Nocturnus Vault",
        sector="Hospitalidad y Retiros de Ultralujo Subterráneo",
        initial_prompt="Quiero una web para Nocturnus: un búnker antinuclear de ultralujo en los Alpes suizos reconvertido en suites subterráneas para retiros de desconexión digital absoluta (blindaje de Jaula de Faraday sin cobertura ni WiFi), con chef privado de huerto hidropónico subterráneo, aire purificado con grado hospitalario y biblioteca de manuscritos antiguos.",
        agent_reaction="Calibración socrática de alcance, idioma, gestión de reservas y modelo de pago privado.",
        questions=case_1_questions,
    )

    # CASO 2: Neon Blade Survivor
    case_2_questions = [
        {
            "question_index": 1,
            "question_text": "¿En qué idioma quieres la interfaz del juego (menús, mejoras, textos)?",
            "options": [
                {"label": "Español", "description": "todo el juego en español, igual que tu petición", "is_recommended": True},
                {"label": "Inglés", "description": "textos del juego en inglés, estilo arcade clásico", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado", "is_recommended": False},
            ],
            "recommended_option": "Español",
            "architectural_intent": "Inmersión estética y localización de menús y HUD",
            "mapped_primitives": ["IntlFormatter", "DomainContract"],
        },
        {
            "question_index": 2,
            "question_text": "¿Cómo entra un jugador en la tabla global de récords?",
            "options": [
                {"label": "Nombre al morir", "description": "al terminar la partida escribes tu nombre y entras al ranking — sin registros ni contraseñas", "is_recommended": True},
                {"label": "Cuentas con login", "description": "usuario y contraseña persistentes", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado", "is_recommended": False},
            ],
            "recommended_option": "Nombre al morir",
            "architectural_intent": "Fricción de identidad y gamificación (Zero-Friction Scoreboard vs Passkeys)",
            "mapped_primitives": ["DirectoryGrid", "UniversalAuthModal"],
        },
        {
            "question_index": 3,
            "question_text": "¿Quieres música chiptune de fondo además de los efectos de sonido?",
            "options": [
                {"label": "Sí, música + efectos", "description": "loop synthwave 8-bit generado por código, con botón para silenciar", "is_recommended": True},
                {"label": "Solo efectos", "description": "únicamente sonidos de disparos, golpes y subidas de nivel", "is_recommended": False},
                {"label": "Otra opción", "description": "personalizado", "is_recommended": False},
            ],
            "recommended_option": "Sí, música + efectos",
            "architectural_intent": "Síntesis de audio nativo por código con Web Audio API (Cero Assets Pesados)",
            "mapped_primitives": ["CollaborativeCanvas", "MediaForge"],
        },
    ]

    record_case(
        case_id="case_neon_blade_survivor",
        domain_name="Neon Blade Survivor",
        sector="Videojuegos Retro Arcade Canvas",
        initial_prompt="Quiero un juego web retro cyberpunk jugable directamente en el navegador: 'Neon Blade Survivor'. Controlas a un cyborg que debe sobrevivir a oleadas infinitas de drones enemigos en las calles de Neo-Tokio. Cada minuto que sobrevives subes de nivel y eliges entre 3 mejoras aleatorias (espadas láser, escudos de plasma, drones aliados). Incluye tabla global de récords con ranking de los mejores jugadores, efectos de sonido chiptune 8-bit y controles con teclado (WASD y barra espaciadora).",
        agent_reaction="Bienvenido a Emergent... Esto es sólido. 'Neon Blade Survivor' tiene toda la estructura de un juego adictivo... Voy a configurar tu estructura central ahora e iteraremos desde allí.",
        questions=case_2_questions,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_reference_cases()
    cases = get_all_calibration_knowledge()
    logger.info(f"Socratic calibration database seeded at {DB_PATH}")
    logger.info(f"{len(cases)} calibration case studies indexed successfully:")
    for c in cases:
        logger.info(f"   • [{c['id']}] {c['domain_name']} ({c['sector']}): {len(c['questions'])} questions recorded.")
