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
      "source_evidence": "Ofertas de empleo, noticias, inferencias"
    }}
    """

def get_auditor_harvester_prompt(dossier_json: str) -> str:
    return f"""
    Eres el Auditor de Calidad Estratégica del Dossier de Inteligencia de este cliente. Aquí tienes el borrador:
    {dossier_json}

    TAREAS:
    1. Comprueba la coherencia regulatoria. (Ej: DORA es falso para hospitales).
    2. Valida el 'financial_tier'. Si es un gigante cotizado, debe ser Tier 1. Si es una PYME, Tier 3.
    3. Genera el 'transformation_horizon'. Evalúa si necesita Horizonte 1 (Brilliant Basics/Estandarización), Horizonte 2 (Hyperautomation) o Horizonte 3 (AIOps/Zero-Ops) basándote en sus retos.
    4. Genera la 'target_maturity_matrix'. Ajusta las notas objetivo (TO-BE) de las torres T1 a T10 basándote en la criticidad de su sector (Ej: Sanidad/Energía exige T5=4.8 y T6=4.8. Retail puede requerir T9=4.0 y T1=3.0). 
    
    Devuelve ÚNICAMENTE un JSON válido con la siguiente estructura (MANTENIENDO TODOS LOS CAMPOS DEL BORRADOR MÁS LAS CORRECCIONES):
    {{
      "client_name": "...",
      "industry": "...",
      "financial_tier": "...",
      "regulatory_frameworks": ["..."],
      "ceo_agenda": "...",
      "technological_drivers": ["..."],
      "osint_footprint": "...",
      "transformation_horizon": "Horizonte 1, 2 o 3 con breve explicación",
      "target_maturity_matrix": {{"T1": 4.0, "T2": 4.5, "T3": 3.5, "T4": 4.0, "T5": 4.8, "T6": 4.8, "T7": 4.0, "T8": 3.8, "T9": 4.2, "T10": 4.0}},
      "evidences": ["..."]
    }}
    IMPORTANTE: target_maturity_matrix DEBE tener como claves "T1", "T2", etc. y sus valores DEBEN ser NUMEROS DECIMALES.
    """
