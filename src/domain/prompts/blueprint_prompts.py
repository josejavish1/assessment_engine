from pathlib import Path
from typing import Any, cast


def load_prompt_config(filename: str) -> dict[str, Any]:
    """Load and deserialize a prompt blueprint from a YAML configuration file.

    The function resolves the file path relative to a 'registry' subdirectory
    located within the same directory as this module. This design ensures that
    prompt blueprint files are located reliably, independent of the process's
    current working directory.

    Args:
        filename (str): The name of the YAML configuration file (e.g.,
            'my_prompt.yaml') to load from the 'registry' directory.

    Returns:
        dict[str, Any]: A dictionary containing the deserialized content of the
            YAML file.

    Raises:
        FileNotFoundError: If the specified `filename` does not exist within the
            'registry' subdirectory.
        yaml.YAMLError: If an error occurs during YAML deserialization.
    """
    import yaml

    # Constructs a path to the 'registry' directory relative to the current module's location. This ensures that prompt blueprint YAML files are resolved reliably, independent of the process's current working directory.
    registry_dir = Path(__file__).resolve().parent / "registry"
    filepath = registry_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"No se encontró el archivo de prompt: {filepath}")

    with filepath.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


def get_blueprint_architect_instruction() -> str:
    """Constructs the instruction prompt for the Blueprint Architect agent from a configuration file.

    This function loads configuration details from 'blueprint_architect_instruction.yaml'
    to assemble a structured, multi-part instructional prompt in Spanish.
    The prompt specifies the agent's role, expertise, mission, and a
    numbered list of critical writing rules derived from the configuration.

    Returns:
        A single string containing the complete, formatted instruction prompt.

    Raises:
        FileNotFoundError: If the 'blueprint_architect_instruction.yaml' file
            cannot be found or accessed by the underlying loader.
        KeyError: If the loaded configuration lacks a required key, such as
            'role', 'expertise', 'mission', or 'critical_rules'.
    """
    config = load_prompt_config("blueprint_architect_instruction.yaml")

    instruction = f"Eres un {config['role']} experto en {config['expertise']}.\n"
    instruction += f"Tu misión es: {config['mission']}\n\n"
    instruction += "REGLAS CRÍTICAS DE REDACCIÓN:\n"
    for idx, rule in enumerate(config["critical_rules"], 1):
        instruction += f"{idx}. {rule}\n"

    return instruction


def get_pilar_architect_prompt(
    tower_name: str,
    pilar_label: str,
    pilar_score: float,
    context_str: str,
    intel_str: str,
    answers_json: str,
    pilar_id: str,
) -> Any:
    """Constructs a structured prompt for a generative model from various inputs.

    This function assembles a detailed, multi-section prompt in Spanish by
    integrating business context, strategic intelligence, and technical findings.
    The prompt's structural template, role definition, and rules are loaded
    from the `blueprint_pilar_architect_prompt.yaml` configuration file.

    Args:
        tower_name: The name of the business tower.
        pilar_label: The descriptive label for the pilar.
        pilar_score: The numerical score assigned to the pilar.
        context_str: A string providing the business context.
        intel_str: A string containing strategic intelligence data ("Minuto Cero").
        answers_json: A JSON-formatted string of client responses to technical
            questions.
        pilar_id: The unique identifier for the pilar.

    Returns:
        A single string containing the fully formatted prompt, ready for use with a
        generative model.

    Raises:
        FileNotFoundError: If the 'blueprint_pilar_architect_prompt.yaml'
            configuration file is not found.
        KeyError: If the configuration file is missing a required key.
    """
    config = load_prompt_config("blueprint_pilar_architect_prompt.yaml")

    prompt = f"Eres un {config['role']}.\n"
    prompt += (
        config["context_description"].format(
            tower_name=tower_name, pilar_label=pilar_label, pilar_score=pilar_score
        )
        + "\n\n"
    )

    prompt += "CONTEXTO DEL NEGOCIO:\n"
    prompt += f"{context_str}\n\n"

    prompt += "ADN ESTRATÉGICO (Minuto Cero):\n"
    prompt += f"{intel_str}\n\n"

    prompt += "HALLAZGOS TÉCNICOS (Respuestas del cliente):\n"
    prompt += f"{answers_json}\n\n"

    prompt += "TAREA:\n"
    prompt += f"{config['task']}\n\n"

    prompt += "REGLAS DE ORO:\n"
    for idx, rule in enumerate(config["golden_rules"], 1):
        prompt += f"{idx}. {rule}\n"

    prompt += f"\n{config.get('handover', '')}\n"
    prompt += "Devuelve la informacion en formato JSON estructurado.\n"

    return str(prompt)


def get_critic_prompt(pilar_label: str, client_name: str, raw_output_json: str) -> Any:
    """Constructs a prompt for an AI model to critique a blueprint draft.

    Loads a prompt configuration from `blueprint_critic_prompt.yaml`, formats it
    with client and pillar-specific details, and appends the raw JSON draft
    for review. The resulting string provides a structured set of instructions for
    an AI model tasked with improving the initial draft.

    Args:
        pilar_label (str): The label of the blueprint pillar being reviewed.
        client_name (str): The name of the client for whom the blueprint is being
            created.
        raw_output_json (str): A string containing the JSON draft to be reviewed by
            the critic model.

    Returns:
        str: The fully formatted prompt string ready to be sent to the AI model.

    Raises:
        FileNotFoundError: If the `blueprint_critic_prompt.yaml` configuration
            file cannot be found by the `load_prompt_config` dependency.
        KeyError: If the loaded YAML configuration lacks a required key, such as
            'role', 'mission', 'review_objectives', or 'handover_instruction'.
    """
    config = load_prompt_config("blueprint_critic_prompt.yaml")

    prompt = (
        f"Eres el {config['role']} del blueprint del pilar '{pilar_label}' para el cliente {client_name}.\n\n"
        f"Recibirás un borrador JSON ya generado. Tu trabajo no es reescribirlo desde cero, sino {config['mission']}\n\n"
    )

    prompt += "OBJETIVOS DE REVISIÓN:\n"
    for idx, objective in enumerate(config["review_objectives"], 1):
        prompt += f"{idx}. {objective}\n"

    prompt += f"\nBORRADOR A REVISAR:\n{raw_output_json}\n\n"
    prompt += config["handover_instruction"]

    return str(prompt)


def get_closing_orchestrator_prompt(
    tower_name: str, pillars_analysis_json: str, intel_str: str, total_ale: float = 0.0
) -> Any:
    r"""{'docstring': "Assembles the final orchestrator prompt for blueprint generation.\n\n    This function constructs a detailed prompt for a large language model by\n    integrating multiple data sources. It combines a consolidated analysis of\n    technology pillars, customer-specific intelligence, and an optional financial\n    mandate derived from the Annualized Loss Expectancy (ALE). The role, tone,\n    and structural requirements for the prompt are externally defined and loaded\n    from a YAML configuration file.\n\n    Args:\n        tower_name: The name of the technology tower being analyzed.\n        pillars_analysis_json: A JSON-formatted string containing the\n            consolidated analysis for all pillars within the specified tower.\n        intel_str: A string containing customer-specific intelligence or context.\n        total_ale: The consolidated Annualized Loss Expectancy (ALE) for the\n            tower. If greater than 0, this value is included as a financial\n            mandate ('Cost of Inaction') in the prompt. Defaults to 0.0.\n\n    Returns:\n        A single string containing the fully constructed prompt, ready for\n        submission to a language model.\n\n    Raises:\n        FileNotFoundError: If the `blueprint_closing_orchestrator_prompt.yaml`\n            configuration file is not found.\n        KeyError: If the loaded YAML configuration is missing required keys\n            such as 'role', 'task_and_tone', or 'structure_requirements'."}."""
    config = load_prompt_config("blueprint_closing_orchestrator_prompt.yaml")

    prompt = f"Eres el {config['role']}. Aquí tienes el análisis de todos los pilares de la torre {tower_name}:\n"
    prompt += f"{pillars_analysis_json}\n\n"

    prompt += f"Basado en esto y en el ADN del cliente: {intel_str}\n\n"
    
    if total_ale > 0:
        prompt += f"MANDATO FINANCIERO (FAIR ALE): La Expectativa de Pérdida Anualizada (ALE) consolidada para los riesgos de esta torre es de {total_ale:,.2f} €. DEBES utilizar este valor explícitamente en el texto del 'Cost of Inaction' (cost_of_inaction) para cuantificar financieramente el riesgo ante el Comité de Dirección.\n\n"

    prompt += "TAREA Y REGLAS DE TONO:\n"
    for rule in config["task_and_tone"]:
        prompt += f"- {rule}\n"

    prompt += "\n"
    for step, desc in config["structure_requirements"].items():
        prompt += f"{step}. {desc}\n"

    prompt += "\nDevuelve la informacion en formato JSON estructurado.\n"
    return str(prompt)


def get_gravity_profiler_prompt(intel_str: str, client_name: str) -> str:
    """Generates a Spanish-language prompt for an LLM to deduce a client's architectural profile.

    This function populates a predefined Spanish-language template to create a prompt
    for a Large Language Model (LLM). The prompt instructs the LLM to assume the
    persona of a 'Tier 1 Mission Critical Architect' and analyze the provided
    client information. The goal is to deduce and extract the client's 'Architectural
    Gravity Profile' into a structured JSON object. This profile includes metrics such as
    on-premise weight, cloud-native weight, regulatory strictness, vendor lock-in
    tolerance, a strategic directive summary, and a recommended target maturity score.

    Args:
        intel_str: A string containing strategic information, technical context,
            or other relevant intelligence about the client.
        client_name: The name of the client, used for contextualization within
            the prompt.

    Returns:
        A formatted, Spanish-language string ready to be used as a prompt for an LLM.
    """
    prompt = (
        f"Eres un Arquitecto de Misión Crítica (Tier 1) analizando el contexto de {client_name}.\n"
        f"Basándote en este ADN Estratégico:\n{intel_str}\n\n"
        "Debes deducir el 'Perfil de Gravedad Arquitectónica' del cliente. Extrae los siguientes valores:\n"
        "- on_premise_weight: 0.0 a 1.0 (Qué porcentaje de carga debe quedarse On-Premise por latencia, regulación o legado SCADA/OT).\n"
        "- cloud_native_weight: 0.0 a 1.0 (Qué porcentaje puede ir a Cloud Público).\n"
        "- regulatory_strictness: 'Alta', 'Media' o 'Baja' (Ej. Operadores críticos como energía o banca son 'Alta').\n"
        "- vendor_lockin_tolerance: 'Alta', 'Media' o 'Baja' (Operadores críticos suelen tener tolerancia 'Baja').\n"
        "- strategic_directive: La directiva resultante en pocas palabras (Ej. 'Sovereign Hybrid Edge', 'Cloud-First Agnostic', 'Strict On-Premise').\n"
        "- recommended_target_maturity: Un número flotante (ej. 4.0, 4.2, 4.5) que represente el nivel de madurez objetivo recomendado basado en la criticidad del negocio y la ambición del cliente.\n"
        "\nDevuelve la información en formato JSON estricto."
    )
    return prompt


def get_dependency_resolver_prompt(projects_json: str) -> str:
    """Embed a JSON string of projects into a Spanish-language prompt template for AI dependency resolution."""
    prompt = (
        "Eres un Arquitecto de Dependencias Topológicas (SOTA 2026).\n"
        "Tu única misión es mapear las dependencias técnicas entre esta lista cerrada de proyectos.\n"
        f"PROYECTOS APROBADOS:\n{projects_json}\n\n"
        "REGLAS ESTRICTAS:\n"
        "1. NO PUEDES inventar proyectos nuevos. Solo puedes usar los nombres exactos proporcionados.\n"
        "2. Identifica si un proyecto es habilitador técnico de otro. (Ej: 'Landing Zone' habilita a 'Kubernetes').\n"
        "3. Devuelve una lista de 'ExternalDependency' con campos: 'project' (el que depende), 'depends_on' (el habilitador previo exacto), y 'reason' (razón técnica).\n"
        "\nDevuelve la información en formato JSON estructurado."
    )
    return prompt


def get_bid_manager_prompt(client_name: str, project_name: str, project_objective: str, project_sizing: str, mitigated_risk_impact: str) -> str:
    r"""{'docstring': "Constructs a Spanish-language prompt to generate a project charter JSON.\n\n    The generated prompt instructs a language model to act as a senior Bid Manager\n    and Solution Architect from NTT DATA. It provides the model with specific\n    project details and a strict set of rules for generating a comprehensive\n    project charter in a JSON format.\n\n    Args:\n        client_name: The name of the client for whom the project is intended.\n        project_name: The internal or generic name of the project.\n        project_objective: A high-level description of the project's goal.\n        project_sizing: The estimated size or scale of the project (e.g., 'Small').\n        mitigated_risk_impact: The business or technical risk the project is\n            designed to mitigate.\n\n    Returns:\n        A complete prompt string in Spanish, ready for use with a generative AI."}."""
    prompt = (
        f"Eres un Bid Manager y Solution Architect Senior de NTT DATA preparando un 'Project Charter' a nivel de Comité de Dirección para el cliente {client_name}.\n"
        f"PROYECTO: {project_name}\n"
        f"OBJETIVO: {project_objective}\n"
        f"TALLA (Sizing): {project_sizing}\n"
        f"RIESGO A MITIGAR: {mitigated_risk_impact}\n\n"
        "REGLAS ESTRICTAS (NTT DATA TIER-1 SOTA 2026):\n"
        "1. commercial_name: Reescribe el nombre genérico del proyecto para que sea un título SOTA de alto impacto comercial.\n"
        "2. project_description: Escribe una descripción ejecutiva en lenguaje llano de 3-4 líneas. Explica al CIO exactamente DE QUÉ TRATA el proyecto, sin usar acrónimos técnicos incomprensibles.\n"
        "3. smart_objectives: Escribe un objetivo SMART cuantificable.\n"
        "4. in_scope / out_of_scope: Define los límites estrictos de ingeniería. En out_of_scope, añade cláusulas defensivas para NTT DATA (ej. Licencias a cargo del cliente, migraciones legacy complejas excluidas).\n"
        "5. governance_roles: Define 3-4 roles RACI críticos, INCLUYENDO OBLIGATORIAMENTE los deberes del cliente (ej. 'Cliente: Sponsor y provisión de accesos').\n"
        "6. critical_risks: Identifica 2 riesgos de ejecución y su mitigación.\n"
        "7. wbs_breakdown: Genera un Work Breakdown Structure (WBS) exhaustivo con Fases reales de delivery (ej. Fase 1: HLD, Fase 2: LLD & Build, Fase 3: Migración, Fase 4: Hypercare). "
        "Asigna un esfuerzo en horas realista basado en la talla del proyecto. OBLIGATORIO: Debes incluir al menos una tarea de Gestión de Proyecto (PMO/QA). "
        "OBLIGATORIO: El perfil debe ser estrictamente uno de estos: 'gerente_cuenta', 'arquitecto', 'experto', 'project_manager', 'tecnico_medio', 'tecnico_junior'.\n"
        "8. roi_justification: Redacta un ROI profundo basado en el Riesgo a Mitigar (Hard/Soft savings). Tienes el dato del ALE (Annualized Loss Expectancy) en el riesgo a mitigar si aplica.\n"
        "\nDevuelve la información en el formato JSON estricto."
    )
    return prompt
