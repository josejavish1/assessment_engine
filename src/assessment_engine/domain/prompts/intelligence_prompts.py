"""Prompt repository compliant with TIER 1 DIPLOMATIC STANDARDS 2026.

All prompts enforce strict JSON output and schema validation.
"""

JSON_MANDATE = "\n\n### REGLA DE ORO: Devuelve ÚNICAMENTE un bloque de código JSON válido. No incluyas explicaciones, preámbulos ni comentarios fuera del JSON. Debes seguir el esquema solicitado estrictamente."


def get_grounding_harvester_prompt(context_text: str) -> str:
    """Generates a Spanish language model prompt for structured technical fact extraction.

    The prompt instructs the model to act as a staff analyst from NTT DATA. It is
    tasked with parsing the provided context, identifying a dominant hyperscaler
    (Azure, AWS, or GCP), and extracting key technical facts and operational
    restrictions. The prompt mandates a specific JSON structure for the model's
    output.

    Args:
        context_text (str): A string containing the ground truth fragments to be
            embedded into the prompt for analysis.

    Returns:
        str: A complete prompt string in Spanish, directing the language model to
            return a JSON object with 'hyperscaler_dominante',
            'observaciones_clave', and 'restricciones_operativas' keys.
    """
    return f"""
    Eres un ANALISTA STAFF de NTT DATA. Extrae las VERDADES TÉCNICAS desde los fragmentos proporcionados.

    ### FRAGMENTOS DE VERDAD (GROUND TRUTH):
    {context_text}

    REGLA DE ORO: Si algún fragmento menciona un hyperscaler dominante (Azure/AWS/GCP), identifícalo.

    ESTRUCTURA REQUERIDA (JSON):
    {{
      "hyperscaler_dominante": "string",
      "observaciones_clave": [
          {{ "fact": "string", "fragment_id": "UUID del fragmento exacto" }}
      ],
      "restricciones_operativas": [
          {{ "restriction": "string", "fragment_id": "UUID del fragmento" }}
      ]
    }}
    {JSON_MANDATE}
    """


def get_business_harvester_prompt(
    client_name: str, context_text: str, grounding_json: str = "{}"
) -> str:
    """Generate a Spanish-language prompt for business intelligence analysis from client, context, and grounding data."""
    return f"""
    Analiza la agenda del CEO y el contexto de negocio para '{client_name}'.
    Utiliza ÚNICAMENTE los fragmentos validados en el GROUNDING y el CONTEXTO RAG.

    SI BUSCAS EN INTERNET: Debes proporcionar la URL exacta de la fuente en el campo 'source_evidence' o junto al driver.

    GROUNDING: {grounding_json}

    CONTEXTO EXTRAÍDO (RAG):
    {context_text}

    ESTRUCTURA REQUERIDA (JSON):
    {{
      "ceo_agenda": "Resumen ejecutivo de la agenda",
      "business_drivers": [
          {{ "name": "string", "fragment_id": "UUID del fragmento", "external_url": "Opcional: URL si es OSINT" }}
      ],
      "financial_tier": "Tier 1, 2 o 3",
      "priority_markets": ["string"],
      "business_lines": ["string"],
      "active_transformations": ["string"],
      "business_constraints": ["string"],
      "source_evidence": "Cita literal + URL si es externa"
    }}
    {JSON_MANDATE}
    """


def get_tech_harvester_prompt(
    client_name: str, context_text: str, grounding_json: str = "{}"
) -> str:
    """Generate a Spanish-language prompt to investigate a client's technology stack."""
    return f"""
    Investiga el stack tecnológico para '{client_name}'.
    GROUNDING: {grounding_json}

    CONTEXTO EXTRAÍDO (RAG):
    {context_text}

    SI ENCUENTRAS DATOS EN INTERNET: Es obligatorio incluir la URL de la fuente (ej: casos de éxito de AWS, informes técnicos).

    ESTRUCTURA REQUERIDA (JSON):
    {{
      "tech_footprint": "Resumen del footprint + URLs detectadas",
      "tech_trends": ["Tendencias clave"],
      "vendor_dependencies": ["string"],
      "operating_constraints": ["string"],
      "recent_incident_signals": ["string"],
      "source_evidence": "Evidencia detectada con URLs"
    }}
    {JSON_MANDATE}
    """


def get_regulatory_harvester_prompt(
    client_name: str, context_text: str, grounding_json: str = "{}"
) -> str:
    """Constructs a Spanish-language prompt for regulatory analysis using client and context data."""
    return f"""
    Analiza el sector y la regulación para '{client_name}'.

    CONTEXTO EXTRAÍDO (RAG):
    {context_text}

    ESTRUCTURA REQUERIDA (JSON):
    {{
      "sector": "string",
      "frameworks": ["string"],
      "regulatory_pressures": ["string"],
      "source_evidence": "Evidencia detectada"
    }}
    {JSON_MANDATE}
    """


def get_tower_refiner_prompt(findings_json: str, grounding_json: str = "{}") -> str:
    """Construct a Spanish-language prompt to refine a technical tower analysis for a CIO-level audience."""
    return f"""
    Eres un SOCIO (Partner) de una firma Tier 1. Refina este análisis técnico de TORRE para un CIO.
    MATERIAL: {findings_json}
    GROUNDING: {grounding_json}

    ### MANDATO TIER 1:
    1. SOBRIEDAD EXTREMA: Elimina cualquier rastro de lenguaje emocional o impreciso.
    2. PRESERVACIÓN DE EVIDENCIA: Es CRÍTICO que mantengas todos los 'fragment_id' asociados a cada hallazgo y fortaleza. No los borres.
    3. COHERENCIA ESTRATÉGICA: Asegura que los riesgos identificados en los pilares se reflejen correctamente en el 'assessment_summary'.
    4. FOCO EN VALOR: Reescribe las iniciativas para que suenen como inversiones estratégicas, no solo tareas técnicas.

    ESTRUCTURA DE SALIDA (MANDATORIA):
    Debes devolver un JSON con la estructura EXACTA del input, incluyendo la lista 'pillar_findings' completa.

    {JSON_MANDATE}
    """


def get_global_refiner_prompt(findings_json: str, grounding_json: str = "{}") -> str:
    """Generates a structured prompt for an LLM to synthesize a CEO-level report. This function assembles a detailed, multi-part prompt that instructs a Large Language Model (LLM) to act as a Tier 1 consulting partner. The primary task is to transform a raw, technical analysis into a polished, strategic report suitable for a CEO audience. The generated prompt includes several key components: - A specific persona for the LLM to adopt. - A mandatory "ÉLITE 2026" style guide that dictates tone, semantics, and pragmatic constraints for recommendations. - A strict JSON output structure mandate based on the `GlobalReportPayload` schema, reinforced by an externally defined `JSON_MANDATE` constant. Args: findings_json: A JSON-formatted string containing the raw technical analysis, metrics, and observations to be synthesized into the report. grounding_json: An optional JSON-formatted string providing supplemental context, such as market data or established facts, to ground the LLM's response. Defaults to an empty JSON object string ("{}"). Returns: A complete prompt string formatted for submission to a compatible LLM. Raises: NameError: If the required module-level constant `JSON_MANDATE` is not defined in the scope where this function is called."""
    return f"""
    Eres un SOCIO (Partner) de una firma Tier 1. Refina este análisis técnico para un CEO.
    MATERIAL: {findings_json}
    GROUNDING: {grounding_json}

    ### MANUAL DE ESTILO DE GOBERNANZA (MANDATORIO):
    1. NEUTRALIDAD CONSTRUCTIVA: No juzgues. Describe la "Deuda Técnica Acumulada". Trata al cliente con respeto profesional. Cero auto-crítica.
    2. SANEAMIENTO DE REDUNDANCIAS: Asegura 'Unicidad de Mensaje'. No repitas el resumen ejecutivo en las implicaciones de negocio. Cada sección debe aportar un ángulo nuevo.
    3. FILTRO DE EMPODERAMIENTO: En lugar de pedir un "cambio cultural", pide un "Programa de Empoderamiento Técnico". Habla de liberar el talento actual de NTT DATA hacia la ingeniería de plataforma.
    4. PRAGMATISMO OPERATIVO (ANTI-TORRE DE MARFIL): En los roadmaps a corto plazo (Wave 1 / 0-6 meses), usa verbos como "Diseño", "PoC", "Definición de estándares" o "Piloto". PROHIBIDO proponer "Implantaciones masivas" en infraestructura crítica en menos de 6 meses.
    5. VARIEDAD SEMÁNTICA: Evita la fatiga de la palabra "industrialización". Usa sinónimos como "sistematización", "escalabilidad", "maduración".
    6. REFERENCIAS EXACTAS: Si haces una afirmación sobre el mercado o una métrica, MANTÉN la URL o cita de Gartner/AWS proporcionada por el Technical Researcher.

    ESTRUCTURA DE SALIDA (JSON):
    Debes devolver un objeto con las claves exactas de GlobalReportPayload:
    ['meta', 'executive_summary', 'burning_platform', 'tower_bottom_lines', 'target_vision', 'execution_roadmap', 'executive_decisions']

    MANTÉN la estructura interna de listas y objetos de forma estricta.

    {JSON_MANDATE}
    """


def get_sota_researcher_prompt(
    pillar_name: str, gap_text: str, grounding_json: str = "{}"
) -> str:
    """Constructs a language model prompt to identify a recommended technical solution.

    This function generates a detailed prompt instructing a large language model to
    assume the persona of a staff researcher from a leading technology advisory
    firm. The prompt is engineered to solicit a standard solution for a specified
    technology pillar and problem description. The response is explicitly
    requested in a structured JSON format, detailing the solution name, its
    underlying architectural pattern, its strategic business benefit, and an
    optional, verifiable source reference.

    Args:
        pillar_name: The technology or business domain requiring a technical solution.
        gap_text: A description of the specific problem or capability gap to be
            addressed.
        grounding_json: An optional JSON string providing client-specific context
            to ground the model's response. Defaults to an empty JSON object
            string.

    Returns:
        A string containing the complete, formatted prompt ready for submission
        to a language model.
    """
    return f"""
    Eres un INVESTIGADOR STAFF de Gartner/Forrester especializado en tecnología de vanguardia 2026.
    Tu misión es encontrar la solución técnica recomendada y referencias de mercado para el pilar '{pillar_name}'.

    ### PROBLEMA DETECTADO:
    {gap_text}

    ### CONTEXTO CLIENTE:
    {grounding_json}

    ### MANDATO TIER 1 (FACT-CHECKING):
    1. Busca la tendencia líder de 2026 (ej: AIOps, Platform Engineering, Zero Trust Data Security).
    2. Identifica el "Top Tier" de patrones arquitectónicos AGNÓSTICOS AL VENDOR (Cloud-Native) que resuelven esto. Evita hacer un 'vendor lock-in' extremo con nombres comerciales muy específicos a menos que sea estrictamente necesario.
    3. Explica el "Sustainable Uplift": ¿Qué ventaja competitiva gana el cliente?
    4. REFERENCIA DE MERCADO OPCIONAL: Si, y solo si, conoces una referencia REAL y verificable (ej. un reporte de Gartner, CNCF, NIS2) que sustente esta solución, inclúyela en 'source_reference'. Si vas a inventar una URL o no tienes un dato empírico demostrable, DEJA EL CAMPO VACÍO o con valor nulo. Nunca inventes referencias.

    ESTRUCTURA REQUERIDA (JSON):
    {{
      "sota_solution_name": "Nombre de la solución",
      "architectural_pattern": "Patrón técnico específico",
      "strategic_benefit": "Impacto de negocio a largo plazo",
      "source_reference": "Título del reporte y URL de referencia"
    }}
    {JSON_MANDATE}
    """


def get_technical_analyst_prompt(
    tower_id: str, pillar_name: str, score: float, context: str, evidences: str
) -> str:
    """Constructs a Spanish-language prompt for a generative model to act as a technical analyst.

    This function formats a string that instructs a generative model to analyze
    a specified technical pillar based on a score, context, and supporting
    evidence. The prompt directs the model to ground its analysis in the
    provided evidence fragments and to structure its response as a specific
    JSON object.

    Args:
        tower_id: The identifier for the technical tower. This parameter is
            currently unused in the prompt but is maintained for signature
            compatibility.
        pillar_name: The name of the technical pillar for analysis.
        score: The numerical score assigned to the pillar.
        context: A string providing the background context for the analysis.
        evidences: A string containing pre-formatted evidence fragments. The model
            is instructed to reference these fragments by their identifiers in
            its response.

    Returns:
        A formatted string containing a complete Spanish-language prompt for
        the generative model. The prompt includes role-playing instructions,
        context, evidence, and a mandatory JSON output schema.
    """
    return f"""
    Eres un CONSULTOR STAFF Tier 1. Analiza el pilar '{pillar_name}'.
    Score {score}, Contexto {context}.

    ### EVIDENCIAS DISPONIBLES (FRAGMENTOS):
    {evidences}

    REGLA DE ORO: Tus conclusiones deben estar ancladas a fragmentos reales.

    ESTRUCTURA REQUERIDA (JSON):
    {{
      "strength": "string",
      "strength_fragment_id": "UUID del fragmento que justifica la fortaleza",
      "gap": "string",
      "gap_fragment_id": "UUID del fragmento que justifica la brecha",
      "risk_title": "string",
      "initiatives": [
          {{ "title": "string", "rationale": "string", "horizon": "string" }}
      ]
    }}
    ATENCIÓN: Si no hay un fragmento claro para la fortaleza o la brecha, deja el fragment_id como nulo.
    {JSON_MANDATE}
    """


def get_auditor_harvester_prompt(dossier_json: str, grounding_json: str = "{}") -> str:
    """Constructs a prompt for a large language model to consolidate an intelligence dossier.

    The generated prompt instructs the model to assume the persona of a senior
    auditor. It provides the model with a primary dossier and supplementary
    grounding data, mandating the consolidation of this information according to
    a strict protocol. This protocol enforces specific rules for evidence
    citation, regulatory impact analysis, source prioritization, and financial
    data precision. The final output is required to conform to the
    `ClientDossierV3` JSON schema.

    Args:
        dossier_json: A JSON-formatted string representing the primary intelligence
            dossier to be consolidated.
        grounding_json: A JSON-formatted string containing supplementary data to
            support the consolidation. Defaults to an empty JSON object string.

    Returns:
        A fully formatted prompt string ready for submission to a large
        language model.
    """
    return f"""
    Eres un AUDITOR SENIOR NTT DATA. Tu misión es consolidar el Dossier de Inteligencia.
    MATERIAL: {dossier_json}
    GROUNDING: {grounding_json}

    ### PROTOCOLO DE EXCELENCIA (TIER 1):
    1. HUMANIZACIÓN DE EVIDENCIAS: No uses "claims[X]". Usa el Título de la fuente entre corchetes, ej: [Redeia - Informe Anual 2024].
    2. MATRIZ DE IMPACTO REGULATORIO: Cada ley en 'regulatory_context' debe incluir su Nivel de Impacto (Crítico, Alto, Medio).
    3. FILTRO DE AUTORIDAD: Prioriza la información de PDFs oficiales y webs corporativas sobre vídeos de YouTube o blogs. Si hay contradicción, manda el documento oficial.
    4. PRECISIÓN FINANCIERA: Si el EBITDA o Ingresos están en los claims, asegúrate de que aparezcan las cifras exactas.

    ESTRUCTURA DE SALIDA: JSON idéntico al esquema ClientDossierV3.
    {JSON_MANDATE}
    """


def get_adversary_harvester_prompt(
    dossier_json: str, grounding_json: str = "{}"
) -> str:
    """Construct a Spanish-language LLM prompt to identify defects in a dossier against grounding data."""
    return f"""
    Analiza este Dossier: {dossier_json}.
    Busca:
    1. Referencias técnicas ilegibles (ej: claims[X]) que deban ser humanizadas.
    2. Leyes sin impacto definido.
    3. Alucinaciones o contradicciones con el GROUNDING: {grounding_json}.
    Devuelve JSON: {{ 'objections': [{{ 'severity': 'string', 'reason': 'string' }}] }}.
    {JSON_MANDATE}
    """


def get_judge_harvester_prompt(dossier_json: str, objections_json: str) -> str:
    """Constructs a prompt for a language model to refine a JSON dossier.

    The generated prompt instructs a language model to act as a final technical
    authority ('Juez Supremo'). It applies a given set of corrections from an
    objections object to a source dossier object. The prompt enforces a strict set
    of governance mandates, including:

    -   Source Citation: All claims must cite the human-readable source title.
    -   Impact Level: Legal items must specify an impact level (e.g., Critical,
        High, Medium).
    -   Claim Integrity: The original 'claims' section, including all objects
        and URLs, must be preserved without modification.
    -   Entity Specificity: Named entities such as software, vendors, financial
        quantities, or project names must be maintained with their original
        specificity and not be generalized.

    The model is explicitly commanded to return only the corrected JSON object,
    which must adhere to the ClientDossierV3 schema.

    Args:
        dossier_json (str): A JSON-formatted string representing the source
            dossier to be corrected.
        objections_json (str): A JSON-formatted string containing the objections
            to apply to the dossier.

    Returns:
        str: A complete, formatted string prompt ready for use with a language
            model.
    """
    return f"""
    Juez Supremo: Genera la versión FINAL de máxima autoridad técnica.
    Toma el dossier y aplica las correcciones basadas en las objeciones.

    DOSSIER: {dossier_json}
    OBJECIONES: {objections_json}

    ### MANDATOS CRÍTICOS (TIER 1 GOBERNANZA):
    1. CITAS HUMANAS: Asegura que cada afirmación cite la fuente por su nombre [Título], no por su índice.
    2. IMPACTO: No permitas leyes sin su nivel de impacto (Crítico/Alto/Medio).
    3. INTEGRIDAD DE CLAIMS: MANTÉN la sección 'claims' con todos sus objetos y URLs reales. NO modifiques ni vacíes este campo bajo ninguna circunstancia.
    4. MANDATO DE ENTIDADES (PRECISIÓN TÉCNICA): Tienes prohibido generalizar nombres de software, vendors, cantidades financieras o nombres de proyectos. Si el material fuente menciona 'Dynatrace' o '689 M€', el informe final DEBE mencionar 'Dynatrace' o '689 M€', no 'herramienta de monitorización' o 'buenos resultados'. La precisión es sagrada.

    Debes devolver ÚNICAMENTE el objeto JSON raíz con las claves de ClientDossierV3.
    {JSON_MANDATE}
    """
