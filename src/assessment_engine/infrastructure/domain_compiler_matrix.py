"""
Provide the capability taxonomy and dispatch matrix for the Neural Domain Compiler (RFC-015). Decoupled from domain_compiler.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

from typing import Any

CAPABILITY_TAXONOMY_MATRIX: dict[str, dict[str, Any]] = {
    "identity_security": {
        "keywords": ["auth", "login", "usuario", "user", "cuenta", "cliente", "portal", "acceso", "perfil", "socio"],
        "gems": ["csrf_hmac_guard", "passkeys_webauthn", "security_headers", "cookie_hardening"],
        "description": "Protección de identidad bancaria, tokens CSRF HMAC y autenticación biométrica WebAuthn",
        "invariants": [
            {
                "id": "CAP-AUTH-01",
                "name": "Defensa Anti-CSRF",
                "rule": "Toda mutación de estado debe estar firmada con token HMAC",
                "property_assertion": "csrf_guard.verify_token(req) is True",
            },
            {
                "id": "CAP-AUTH-02",
                "name": "Autenticación Biométrica W3C",
                "rule": "Soporte FIDO2 / Passkeys para acceso passwordless",
                "property_assertion": "webauthn.verify_credential(cred) is True",
            },
        ],
    },
    "omniscient_search": {
        "keywords": ["search", "buscar", "búsqueda", "catálogo", "directorio", "filtro", "artículo", "producto", "pista", "inventario", "consulta"],
        "gems": ["fts5_search", "in_memory_micro_cache", "speculative_preloader"],
        "description": "Búsqueda de texto completo SQLite FTS5 con ranking BM25 en <1ms y micro-caché LRU",
        "invariants": [
            {
                "id": "CAP-SRCH-01",
                "name": "Búsqueda Full-Text Sub-Milimétrica",
                "rule": "Búsqueda BM25 en SQLite sin latencia de red ni infraestructura externa",
                "property_assertion": "search_latency_ms < 5.0",
            },
        ],
    },
    "gdpr_compliance": {
        "keywords": ["salud", "médic", "clínic", "paciente", "historial", "legal", "factura", "tarjeta", "contrato", "veterinari", "odontolog", "privacidad"],
        "gems": ["column_encryption", "data_erasure_cascade", "data_portability_exporter", "audit_trail"],
        "description": "Cifrado AES-256 de campos sensibles, Derecho al Olvido (RGPD Art. 17) y Portabilidad (Art. 20)",
        "invariants": [
            {
                "id": "CAP-GDPR-01",
                "name": "Derecho al Olvido RGPD Art. 17",
                "rule": "Purga atómica de PII y anonimización irreversible de historial",
                "property_assertion": "data_erasure_cascade.erase_user_pii(...)['status'] == 'ok'",
            },
            {
                "id": "CAP-GDPR-02",
                "name": "Cifrado en Reposo de Datos Sensibles",
                "rule": "Cifrado simétrico autenticado Fernet de columnas médicas y fiscales",
                "property_assertion": "is_encrypted(db.column) is True",
            },
        ],
    },
    "high_concurrency_commerce": {
        "keywords": ["pago", "precio", "reserva", "tarifa", "compra", "pedido", "checkout", "suscripción", "cart", "pista", "tienda"],
        "gems": ["pricing_rules", "inventory_allocation", "signed_urls"],
        "description": "Aritmética monetaria exacta en céntimos, lease-holds con TTL y URLs temporales firmadas",
        "invariants": [
            {
                "id": "CAP-COMM-01",
                "name": "Aritmética Monetaria Exacta",
                "rule": "Cálculo en céntimos enteros sin desviación de coma flotante IEEE-754",
                "property_assertion": "isinstance(cents, int)",
            },
            {
                "id": "CAP-COMM-02",
                "name": "Anti-Sobreventa de Capacidad",
                "rule": "Lease-holds con TTL para franjas horarias y plazas concurrentes",
                "property_assertion": "active_holds <= max_capacity",
            },
        ],
    },
    "performance_devops": {
        "keywords": ["*"],
        "gems": ["sqlite_performance_tuning", "health_probes", "openmetrics_exporter"],
        "description": "Afinación SQLite WAL (PRAGMA busy_timeout=5000), sondas k8s /healthz y métricas Prometheus",
        "invariants": [
            {
                "id": "CAP-PERF-01",
                "name": "Afinación SQLite de Alta Concurrencia",
                "rule": "Modo WAL con busy_timeout=5000 y mmap de 256MB",
                "property_assertion": "journal_mode == 'wal'",
            },
        ],
    },
    "spatial_geodesic": {
        "keywords": ["map", "mapa", "geo", "ubicación", "gps", "distancia", "ruta", "dirección", "envío", "reparto", "coordenada"],
        "gems": ["geo_engine", "spatial_index", "osm_tiles"],
        "description": "Cálculo geodésico Haversine, proyección Web Mercator EPSG:3857 y clustering aglomerativo",
        "invariants": [
            {
                "id": "CAP-GEO-01",
                "name": "Cálculo Geodésico Exacto Haversine",
                "rule": "Distancias con radio terrestre de 6371.0088 km",
                "property_assertion": "haversine_distance >= 0.0",
            },
        ],
    },
    "inventory_seating": {
        "keywords": ["asiento", "butaca", "aforo", "teatro", "evento", "cine", "concierto", "plaza", "seating", "estadio"],
        "gems": ["inventory_allocation", "lease_hold"],
        "description": "Bloqueo atómico transaccional de aforo con lease-holds de 10 min en SQLite WAL",
        "invariants": [
            {
                "id": "CAP-SEAT-01",
                "name": "Anti-Colisión de Asientos (Lease-Hold)",
                "rule": "Reserva temporal con expiración automática de 10 minutos para evitar doble reserva",
                "property_assertion": "lease_expires_at > current_timestamp",
            },
        ],
    },
    "document_assembly_legal": {
        "keywords": ["contrato", "factura", "legal", "documento", "pdf", "firmar", "verifactu", "plantilla"],
        "gems": ["pdf_document_assembler", "verifactu_qr"],
        "description": "Visor WYSIWYG legal, paginación W3C @media print y código QR Veri*Factu",
        "invariants": [
            {
                "id": "CAP-DOC-01",
                "name": "Inmutabilidad Legal y Sellado Veri*Factu",
                "rule": "Sellado criptográfico HMAC-SHA256 y renderizado vectorial de código QR",
                "property_assertion": "verify_document_hmac(doc) is True",
            },
        ],
    },
    "realtime_collaboration": {
        "keywords": ["pizarra", "canvas", "dibujo", "colaborativo", "tiempo real", "cursores", "whiteboard", "figura"],
        "gems": ["realtime_sse", "crdt_sync"],
        "description": "Lienzo 2D interactivo a 60 FPS con presencia de cursores en vivo vía SSE a coste $0.00",
        "invariants": [
            {
                "id": "CAP-COLLAB-01",
                "name": "Sincronización Reactiva SSE a Coste $0.00",
                "rule": "Transmisión de trazos y presencia sin servidores WebSockets propietarios",
                "property_assertion": "sse_bus.is_active is True",
            },
        ],
    },
    "org_rebac_governance": {
        "keywords": ["organigrama", "jerarquía", "departamento", "sede", "rebac", "rol", "permiso", "zanzibar", "equipo"],
        "gems": ["rebac_engine", "materialized_path"],
        "description": "Árbol jerárquico Materialized Path en SQLite WAL y matriz ReBAC Nivel 3",
        "invariants": [
            {
                "id": "CAP-REBAC-01",
                "name": "Aislamiento Jerárquico ReBAC Nivel 3",
                "rule": "Evaluación de permisos mediante tuplas de relación Zanzibar con recursión acotada",
                "property_assertion": "rebac_engine.evaluate(subject, action, resource) is not None",
            },
        ],
    },
    "agentic_ai_copilot": {
        "keywords": ["ia", "asistente", "copilot", "chat", "rag", "bot", "agente", "inteligencia"],
        "gems": ["genai_client", "realtime_sse"],
        "description": "Asistente contextual con canal de streaming SSE reactivo y parser sintáctico local",
        "invariants": [
            {
                "id": "CAP-COPILOT-01",
                "name": "Streaming Reactivo Token a Token",
                "rule": "Entrega fluida mediante SSE sin buffering de proxies intermedios",
                "property_assertion": "stream_chunk_latency_ms < 100.0",
            },
        ],
    },
    "telecom_communications": {
        "keywords": ["whatsapp", "sms", "notificación", "mensaje", "aviso", "monedero", "telecom"],
        "gems": ["communications_bus", "telecom_wallet"],
        "description": "Envío WhatsApp QR / Cloud API y SMS gestionado con monedero B2B en SQLite WAL (RFC-014)",
        "invariants": [
            {
                "id": "CAP-TEL-01",
                "name": "Arbitraje B2B y Monedero Inmutable",
                "rule": "Cobro anticipado sobre balance en SQLite WAL con deducción atómica",
                "property_assertion": "wallet_balance >= message_cost",
            },
        ],
    },
    "telemetry_analytics": {
        "keywords": ["analítica", "kpi", "métrica", "dashboard", "gráfico", "telemetría", "estadística"],
        "gems": ["openmetrics_exporter", "kpi_aggregator"],
        "description": "Cuadro de mando analítico reactivo con sparklines SVG nativos sin dependencias",
        "invariants": [
            {
                "id": "CAP-KPI-01",
                "name": "Agregación Temporal Exacta",
                "rule": "Cálculo en una sola pasada SQL de métricas financieras y operativas",
                "property_assertion": "kpi_total_revenue >= 0",
            },
        ],
    },
    "temporal_booking": {
        "keywords": ["cita", "calendario", "agenda", "horario", "turno", "reserva de cita", "booking"],
        "gems": ["booking_slots", "ical_sync"],
        "description": "Motor de cálculo de franjas horarias libres O(1) y sincronización Webcal RFC 5545",
        "invariants": [
            {
                "id": "CAP-BOOK-01",
                "name": "Anti-Solapamiento de Citas",
                "rule": "Validación de slots libres en tiempo constante sin conflictos de concurrencia",
                "property_assertion": "has_overlap is False",
            },
        ],
    },
    "workflow_fsm": {
        "keywords": ["kanban", "tablero", "estado", "workflow", "fase", "proceso", "etapa"],
        "gems": ["workflow_engine", "state_machine"],
        "description": "Máquina de estados finita determinista (DFA) con transiciones atómicas y tablero Kanban",
        "invariants": [
            {
                "id": "CAP-FSM-01",
                "name": "Transición de Estado Válida (DFA)",
                "rule": "Toda mutación de etapa debe estar declarada en el grafo de estados",
                "property_assertion": "is_valid_transition(from_state, to_state) is True",
            },
        ],
    },
    "social_community": {
        "keywords": ["comunidad", "foro", "comentario", "hilo", "muro", "discusión", "feed", "miembro"],
        "gems": ["threaded_discussion", "directory_grid"],
        "description": "Hilos recursivos SQL CTE y directorio de miembros con gamificación",
        "invariants": [
            {
                "id": "CAP-SOC-01",
                "name": "Jerarquía de Discusión Recursiva",
                "rule": "Árbol de respuestas ilimitado en una sola consulta SQL CTE sin bucles infinitos",
                "property_assertion": "comment_depth <= 10",
            },
        ],
    },
}
