"""
Repositorio de prompts para los agentes de Inteligencia de Mercado (OSINT).
"""


def get_regulatory_harvester_prompt(client_name: str) -> str:
    return f"""
    Analiza a la empresa '{client_name}'. Identifica a qué sector pertenece.
    Basado estrictamente en su sector operando en Europa/España, dime cuáles son los marcos normativos de ciberseguridad o resiliencia que le aplican obligatoriamente por ley.
    (Ej: DORA para finanzas, NIS2/PIC para operadores esenciales o energía, ENS para sector público).

    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
    {{
      "sector": "Sector en texto plano",
      "frameworks": ["Ley 1", "Ley 2"],
      "regulatory_pressures": ["Presión regulatoria o de cumplimiento 1", "Presión 2"],
      "source_evidence": "De dónde sacas esta conclusión (noticia, deducción)"
    }}
    """


def get_business_harvester_prompt(client_name: str) -> str:
    return f"""
    Busca noticias recientes o resúmenes de informes de resultados/estrategia de la empresa '{client_name}'.
    1. ¿Cuáles son los objetivos corporativos declarados por su dirección general?
    2. Estima su tamaño de facturación anual y clasifícalo en un 'financial_tier' (Tier 1: >1.000M€, Tier 2: 100M€-1.000M€, Tier 3: <100M€).

    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
    {{
      "ceo_agenda": "Resumen de la agenda del CEO",
      "business_drivers": ["Objetivo 1", "Objetivo 2"],
      "financial_tier": "Tier 1 o Tier 2 o Tier 3",
      "priority_markets": ["Mercado o geografía 1", "Mercado 2"],
      "business_lines": ["B2B", "IoT", "Cloud"],
      "active_transformations": ["Programa de transformación 1", "Programa 2"],
      "business_constraints": ["Restricción financiera u operativa 1", "Restricción 2"],
      "source_evidence": "URL o fuente inferida"
    }}
    """


def get_tech_harvester_prompt(client_name: str) -> str:
    return f"""
    Basado en ofertas de empleo públicas, noticias de alianzas tecnológicas o footprint digital conocido de '{client_name}', ¿qué tecnología clave utilizan o hacia dónde van?
    (Ej: ¿Están migrando a Azure? ¿Usan fuertemente SAP? ¿Servicios industriales OT/IT?).

    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
    {{
      "tech_footprint": "Resumen del ecosistema tecnológico",
      "tech_trends": ["Tendencia 1", "Tendencia 2"],
      "vendor_dependencies": ["Vendor o plataforma dominante 1", "Vendor 2"],
      "operating_constraints": ["Restricción operativa o legado 1", "Restricción 2"],
      "recent_incident_signals": ["Incidente público, outage o señal de resiliencia 1"],
      "source_evidence": "Ofertas de empleo, noticias, inferencias"
    }}
    """


def get_auditor_harvester_prompt(dossier_json: str) -> str:
    return f"""
    Eres el Auditor de Calidad Estratégica del Dossier de Inteligencia de este cliente. Aquí tienes el borrador:
    {dossier_json}


    TAREAS:
    0. PRECEDENCIA EPISTÉMICA: Reconoce que toda la información que procesas proviene de OSINT (fuentes públicas, internet). Estos datos son TANGENCIALES y tienen menor peso de verdad que la documentación interna del cliente.
    1. VIGENCIA TEMPORAL: Revisa exhaustivamente las fechas de las noticias, proyectos o incidentes. Si un proyecto, alianza o estrategia tiene más de 3 años de antigüedad y no hay evidencia de continuidad, descártalo o márcalo explícitamente como "Legacy/Obsoleto".
    2. Comprueba la coherencia regulatoria.
    3. Valida el financial_tier.
    4. Genera business_context.transformation_horizon.
    5. Genera tower_overrides.
    6. Completa technology_context y business_context con señales concretas.
    7. Mantén la trazabilidad.
    8. Distingue hechos, inferencias y supuestos en claims. Asígnales a las claims extraídas de OSINT una confidence.score baja (ej. 40-60) a menos que provengan de reportes financieros oficiales muy recientes.


    Devuelve ÚNICAMENTE un JSON válido con la siguiente estructura (MANTENIENDO TODOS LOS CAMPOS DEL BORRADOR MÁS LAS CORRECCIONES):
    {{
      "version": "3.0",
      "client_name": "...",
      "metadata": {{
        "dossier_id": "client-abc123",
        "schema_version": "3.0",
        "created_at": "2026-05-01T00:00:00+00:00",
        "modified_at": "2026-05-01T00:00:00+00:00",
        "last_verified_at": "2026-05-01T00:00:00+00:00 o null",
        "lang": "es",
        "generated_by": "assessment_engine",
        "prompt_version": "intelligence_prompts_v3",
        "timeliness": {{
          "created_at": "2026-05-01T00:00:00+00:00",
          "modified_at": "2026-05-01T00:00:00+00:00",
          "last_verified_at": "2026-05-01T00:00:00+00:00 o null",
          "valid_until": null,
          "stale_after_days": 30
        }}
      }},
      "profile": {{
        "industry": "...",
        "financial_tier": "Tier 1 o Tier 2 o Tier 3",
        "operating_model": "Texto breve o null",
        "regions": ["EU", "UK"],
        "priority_markets": ["España", "Alemania"],
        "business_lines": ["B2B", "Cloud", "IoT"]
      }},
      "regulatory_context": [
        {{
          "name": "...",
          "applicability": "low|medium|high",
          "confidence": {{"score": 80, "label": "high", "method": "custom"}},
          "sources": [{{"source": "..."}}],
          "impacted_domains": ["T5", "T6"]
        }}
      ],
      "business_context": {{
        "ceo_agenda": {{
          "summary": "...",
          "confidence": {{"score": 80, "label": "high", "method": "custom"}},
          "sources": [{{"source": "..."}}],
          "evidence_strength": "high|medium|low"
        }},
        "strategic_priorities": [
          {{
            "name": "...",
            "confidence": {{"score": 70, "label": "high", "method": "custom"}},
            "sources": [{{"source": "..."}}],
            "rationale": "..."
          }}
        ],
        "business_model_signals": ["..."],
        "active_transformations": ["..."],
        "transformation_horizon": {{
          "stage": "H1|H2|H3",
          "label": "...",
          "rationale": "...",
          "confidence": {{"score": 60, "label": "medium", "method": "custom"}},
          "sources": [{{"source": "..."}}]
        }},
        "constraints": ["..."]
      }},
      "technology_context": {{
        "footprint_summary": {{
          "summary": "...",
          "confidence": {{"score": 60, "label": "medium", "method": "custom"}},
          "sources": [{{"source": "..."}}],
          "evidence_strength": "high|medium|low"
        }},
        "technology_drivers": [
          {{
            "name": "...",
            "confidence": {{"score": 60, "label": "medium", "method": "custom"}},
            "sources": [{{"source": "..."}}],
            "rationale": "..."
          }}
        ],
        "vendor_dependencies": ["..."],
        "operating_constraints": ["..."],
        "recent_incident_signals": ["..."]
      }},
      "tower_overrides": {{
        "T1": {{
          "target_maturity": 4.0,
          "business_criticality": {{"score": 80, "label": "high", "method": "custom"}},
          "regulatory_pressure": {{"score": 80, "label": "high", "method": "custom"}},
          "change_urgency": {{"score": 70, "label": "high", "method": "custom"}},
          "rationale": "...",
          "constraints": ["..."],
          "related_claim_ids": ["claim_1"]
        }}
      }},
      "claims": [
        {{
          "claim_id": "claim_1",
          "claim": "...",
          "claim_type": "fact|inference|assumption|scenario|alternative_hypothesis",
          "confidence": {{"score": 70, "label": "high", "method": "custom"}},
          "sources": [{{"source": "..."}}],
          "source_reliability_score": 70,
          "valid_for_domains": ["global", "commercial"],
          "related_towers": ["T5"]
        }}
      ],
      "review": {{
        "human_review_status": "pending|reviewed|approved|rejected",
        "approved_by": null,
        "approved_at": null,
        "review_notes": []
      }},
      "extensions": {{}}
    }}
    IMPORTANTE: `tower_overrides` DEBE usar claves "T1", "T2", etc. y `target_maturity` DEBE ser numérico decimal.
    """
