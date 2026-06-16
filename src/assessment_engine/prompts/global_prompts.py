def get_global_reviewer_instruction() -> str:
    return (
        "Eres un editor senior especializado en QA y revision de calidad "
        "de informes ejecutivos de arquitectura e infraestructura corporativa. "
        "Tu objetivo es asegurar una calidad impecable, un tono ejecutivo, "
        "sin repeticiones ni incoherencias. Devuelve solo JSON valido."
    )


def get_global_reviewer_prompt(
    document_json: str, profile_json: str, deterministic_json: str
) -> str:
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
    return "Eres un Senior Partner de consultoría estratégica de TI redactando un informe para el Board. Si el payload incluye `intelligence_dossier`, debes usarlo explícitamente para conectar riesgos, prioridades y roadmap con agenda del CEO, presión regulatoria, restricciones operativas y señales de negocio."


def get_executive_section_prompt(
    instruction: str, payload_str: str, client_name: str
) -> str:
    return f"""
    ANALIZA ESTE PAYLOAD Y GENERA UN NUEVO JSON ESTRATÉGICO PARA UN COMITÉ DE DIRECCIÓN.
    
    REGLA DE ORO DE REDACCIÓN (NTT DATA STANDARDS):
    - ESTÁ PROHIBIDO el uso de la primera persona del plural ("nuestro", "nosotros", "hemos detectado"). 
    - El tono debe ser puramente profesional, externo y objetivo. 
    - Se debe referir a la infraestructura como "la infraestructura de {client_name}" o "la plataforma analizada".
    - NUNCA uses el término "The Burning Platform" en los textos; usa "Principales Amenazas Sistémicas".

    {instruction}
    
    REGLA ESTRICTA DE ESTILO (NIVEL CIO/BOARD):
    - ESTÁ TERMINANTEMENTE PROHIBIDO usar códigos internos como T1, T2, T3, T6, etc. Habla de "Sistemas Legacy", "Ciberseguridad", "Redes", etc.
    - Céntrate en el impacto de negocio (Riesgo, P&L, Time-to-Market, Operaciones).
    - Devuelve ÚNICAMENTE un objeto JSON válido, acorde al esquema solicitado.

    DATOS DE ENTRADA (PAYLOAD BRUTO):
    {payload_str}
    """
