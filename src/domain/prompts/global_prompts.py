def get_global_reviewer_instruction() -> str:
    """Return the static global instruction prompt in Spanish for the reviewer agent."""
    return (
        "Eres un editor senior especializado en QA y revision de calidad "
        "de informes ejecutivos de arquitectura e infraestructura corporativa. "
        "Tu objetivo es asegurar una calidad impecable, un tono ejecutivo, "
        "sin repeticiones ni incoherencias. Devuelve solo JSON valido."
    )


def get_global_reviewer_prompt(
    document_json: str, profile_json: str, deterministic_json: str
) -> str:
    """Constructs the prompt for the Global Reviewer agent.

    This function interpolates JSON string representations of a document, its
    profile, and prior validation results into a static, Spanish-language
    prompt template. The resulting prompt instructs an AI agent to perform a
    holistic quality review of the document, checking for issues such as
    internal consistency, redundancy, and stylistic coherence.

    Args:
        document_json: A JSON string representing the fully assembled document
            to be reviewed.
        profile_json: A JSON string containing the document's profile and
            structural metadata.
        deterministic_json: A JSON string containing the results from any
            preceding deterministic validation checks.

    Returns:
        The fully constructed prompt as a single string, ready for use with an
        AI model.
    """
    return f"""
Actua como el agente Global Reviewer del Assessment Engine.

Tu trabajo es revisar de forma GLOBAL un documento ensamblado ya generado.

Objetivo:
- Revisar coherencia transversal entre secciones.
- Detectar duplicidades innecesarias.
- Detectar contradicciones internas.
- Detectar incoherencias terminologicas.
- Detectar problemas de tono, estilo y utilidad ejecutiva.
- Detectar repeticiones excesivas.
- Detectar si la conclusion sintetiza o solo repite.
- Detectar si TO-DO esta realmente alineado con GAP y TO-BE.
- Detectar problemas de balance entre secciones.

Reglas:
- NO reescribas el documento.
- NO inventes defectos.
- Devuelve SOLO JSON valido.
- NO uses markdown.
- NO expliques tu proceso.
- Si no hay issues materiales, devuelve status = "approve".
- Si detectas issues materiales, devuelve status = "revise".

Devuelve la informacion en formato JSON estructurado.

INPUT_DOCUMENT_PROFILE:
{profile_json}

INPUT_DETERMINISTIC_VALIDATION:
{deterministic_json}

INPUT_DOCUMENT_ASSEMBLED:
{document_json}
"""


def get_global_refiner_instruction() -> str:
    """Return the Spanish-language system prompt for the global refiner agent."""
    return (
        "Eres un editor senior especializado en refinamiento de "
        "informes ejecutivos de arquitectura e infraestructura corporativa. "
        "Tu objetivo es mejorar globalmente el documento, resolviendo los defectos "
        "identificados por el reviewer y ejecutando una edicion quirurgica "
        "manteniendo la estructura original."
    )


def get_global_refiner_prompt(
    document_json: str, review_json: str, profile_json: str
) -> str:
    """Construct the prompt for the Global Refiner agent from document, review, and profile JSON strings."""
    return f"""
Actua como el agente Global Refiner del Assessment Engine.

Tu trabajo es refinar un documento ensamblado basandote en la revision global.

Reglas Generales:
- Si global_review status == 'approve', no apliques ediciones a menos que veas un error flagrante.
- Si global_review status == 'revise', DEBES proponer ediciones para resolver los issues mayores.
- Las ediciones se devuelven en formato JSONPatch modificado (path de la variable JSON, accion 'replace' o 'remove', y valor nuevo).
- NO reescribas todo el documento en una sola edicion. Se quirurgico.
- NUNCA cambies datos de scoring o hechos. Solo mejora la redaccion, estilo, coherencia.
- Elimina introducciones roboticas y parrafos redundantes detectados.

Devuelve la informacion en formato JSON estructurado.

INPUT_DOCUMENT_PROFILE:
{profile_json}

INPUT_GLOBAL_REVIEW:
{review_json}

INPUT_DOCUMENT_ASSEMBLED:
{document_json}
"""


def get_executive_refiner_instruction() -> str:
    """Return the static instruction prompt for the 'Executive Refiner' persona."""
    return """Eres un Senior Partner de consultoría estratégica de TI redactando un informe para el Board.
Tu objetivo es transformar el análisis técnico en un 'Modelo de Viabilidad Sistémica' irrefutable.
REGLAS DE ÉLITE:
1. RESILIENCIA INSTITUCIONAL: No hables de personas o rotación; habla de 'Entropía de la Memoria Sistémica' y 'Opacidad Operativa'.
2. AUTORIDAD FINANCIERA: Usa 'Modelos de Sensibilidad' (VaR) para el impacto del riesgo, vinculando la indisponibilidad con la degradación del Free Cash Flow y sanciones (NIS2/GDPR).
3. SOBERANÍA JURISDICCIONAL: Evalúa la 'Inmunidad a Leyes Extraterritoriales' y la 'Soberanía por Diseño' (HYOK, Regiones locales).
Si el payload incluye `intelligence_dossier`, conéctalo explícitamente con la agenda del CEO y señales de negocio."""


def get_executive_section_prompt(
    instruction: str, payload_str: str, client_name: str
) -> str:
    """Generate a Spanish-language LLM prompt for a strategic executive board analysis."""
    return f"""
    ACTÚA COMO UN PARTNER ESTRATÉGICO GENERANDO UN 'MODELO DE VIABILIDAD SISTÉMICA' PARA EL BOARD.
    ANALIZA ESTE PAYLOAD Y GENERA UN NUEVO JSON ESTRATÉGICO DE ALTA AUTORIDAD.

    REGLA DE ORO DE REDACCIÓN (ÉLITE MUNDIAL):
    - ESTÁ PROHIBIDO el uso de la primera persona del plural ("nuestro", "nosotros").
    - El tono debe ser puramente profesional, externo y de autoridad analítica.
    - Se debe referir a la infraestructura como "la infraestructura de {client_name}" o "la plataforma analizada".
    - NUNCA uses el término "The Burning Platform"; usa "Principales Amenazas Sistémicas".

    {instruction}

    REGLA ESTRICTA DE ESTILO (NIVEL CIO/BOARD):
    - ESTÁ TERMINANTEMENTE PROHIBIDO usar códigos internos como T1, T2, etc. Habla de dominios funcionales (Ciberseguridad, Redes, Operaciones).
    - Céntrate en la Viabilidad Estratégica, Riesgo Financiero y Time-to-Value.
    - Devuelve ÚNICAMENTE un objeto JSON válido, acorde al esquema solicitado.

    DATOS DE ENTRADA (PAYLOAD BRUTO):
    {payload_str}
    """
