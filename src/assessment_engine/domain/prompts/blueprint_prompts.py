import json
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


def get_blueprint_architect_instruction(
    target_language: str = "Spanish",
) -> str:
    """Constructs the instruction prompt for the Blueprint Architect agent from a configuration file.

    Loads configuration details from 'blueprint_architect_instruction.yaml'
    to assemble a structured instructional prompt, enforcing the target output language.

    Args:
        target_language (str): Target output language for the generated blueprint (e.g. 'Spanish', 'English', 'German', 'Japanese').

    Returns:
        A single string containing the complete, formatted instruction prompt.
    """
    config = load_prompt_config("blueprint_architect_instruction.yaml")

    instruction = (
        f"You are a Principal Enterprise Solutions Architect ({config.get('role', 'Socio Consultor')}) "
        f"with top-tier expertise in {config.get('expertise', 'Enterprise Cloud & Infrastructure Architecture')}.\n"
    )
    instruction += f"Your mission: {config.get('mission', 'Design an actionable, world-class enterprise transformation blueprint')}\n\n"
    instruction += "### CRITICAL LANGUAGE MANDATE:\n"
    instruction += (
        f"You MUST generate all analytical narratives, findings, gap statements, business cases, "
        f"and technical objectives EXCLUSIVELY in {target_language}.\n\n"
    )
    instruction += "CRITICAL ARCHITECTURAL RULES:\n"
    for idx, rule in enumerate(config.get("critical_rules", []), 1):
        instruction += f"{idx}. {rule}\n"

    return instruction


def get_pilar_architect_prompt(
    tower_name: str,
    pilar_label: str,
    pilar_score: float,
    context_str: str = "",
    intel_str: str = "",
    answers_json: str = "[]",
    pilar_id: str = "",
    target_language: str = "Spanish",
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
        target_language: The target output language for generated narratives.

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
        rule_formatted = (
            rule.format(target_language=target_language)
            if "{target_language}" in rule
            else rule
        )
        prompt += f"{idx}. {rule_formatted}\n"

    if "golden_exemplar" in config:
        prompt += "\nEJEMPLAR DE ORO DE REFERENCIA (ESTÁNDAR TIER-1 / MISIÓN CRÍTICA - FNMT CERES):\n"
        prompt += "Este es el estándar exacto de profundidad técnica, rigor regulatorio y nivel de detalle esperado:\n"
        prompt += (
            json.dumps(config["golden_exemplar"], indent=2, ensure_ascii=False) + "\n\n"
        )

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
    """Format and return a technical English prompt for an LLM to deduce a client's 'Architectural Gravity Profile'."""
    prompt = (
        f"You are a Tier-1 Mission-Critical Infrastructure Architect analyzing the enterprise context of {client_name}.\n"
        f"Based on this Strategic DNA:\n{intel_str}\n\n"
        "Deduce the client's 'Architectural Gravity Profile'. Extract the following metrics:\n"
        "- on_premise_weight: 0.0 to 1.0 (Percentage of workload that must remain On-Premise due to latency, regulation, or OT/SCADA).\n"
        "- cloud_native_weight: 0.0 to 1.0 (Percentage suitable for Public Cloud).\n"
        "- regulatory_strictness: 'High', 'Medium', or 'Low' (Critical operators like energy/banking are 'High').\n"
        "- vendor_lockin_tolerance: 'High', 'Medium', or 'Low' (Critical infrastructure operators typically have 'Low').\n"
        "- strategic_directive: Resulting directive in few words (e.g., 'Sovereign Hybrid Edge', 'Cloud-First Agnostic', 'Strict On-Premise').\n"
        "- recommended_target_maturity: Float (e.g. 4.0, 4.2, 4.5) representing target maturity based on criticality and client ambition.\n"
        "\nReturn the information strictly in the requested JSON format."
    )
    return prompt


def get_dependency_resolver_prompt(projects_json: str) -> str:
    """Construct an AI dependency mapping prompt in technical English."""
    prompt = (
        "You are a Solutions and Topological Dependency Architect.\n"
        "Your single mandate is to map technical dependencies among this closed list of approved initiatives.\n"
        f"APPROVED PROJECTS:\n{projects_json}\n\n"
        "STRICT RULES:\n"
        "1. DO NOT invent new projects. Use only exact provided project names.\n"
        "2. Identify if a project is a technical enabler of another (e.g., 'Landing Zone' enables 'Container Platform').\n"
        "3. Return a list of 'ExternalDependency' objects with fields: 'project', 'depends_on', and 'reason'.\n"
        "\nReturn the information strictly in structured JSON."
    )
    return prompt


def get_bid_manager_prompt(
    client_name: str,
    project_name: str,
    project_objective: str,
    project_sizing: str,
    mitigated_risk_impact: str,
    target_language: str = "Spanish",
) -> str:
    """Constructs a Tier-1 prompt to generate an executive project charter JSON."""
    from assessment_engine.infrastructure.config_loader import (
        get_consultant_company_name,
    )

    company = get_consultant_company_name()
    prompt = (
        f"You are a Senior Bid Manager and Principal Solution Architect at {company} preparing a C-Level 'Project Charter' for client {client_name}.\n"
        f"PROJECT: {project_name}\n"
        f"OBJECTIVE: {project_objective}\n"
        f"SIZING: {project_sizing}\n"
        f"MITIGATED RISK: {mitigated_risk_impact}\n\n"
        "STRICT EXECUTION RULES:\n"
        f"1. commercial_name: Rewrite the project name to be a concise, executive charter title EXCLUSIVELY IN {target_language} (maximum 8 words).\n"
        f"2. project_description: Write an executive plain-language description (3-4 lines) explaining clearly what the project delivers EXCLUSIVELY IN {target_language}.\n"
        f"3. smart_objectives: Formulate a quantifiable SMART objective EXCLUSIVELY IN {target_language}.\n"
        f"4. in_scope / out_of_scope: Define strict engineering boundaries. In out_of_scope, include defensive clauses for {company} (e.g. software licenses by client, complex legacy migrations excluded).\n"
        f"5. governance_roles: Define 3-4 critical RACI roles, including client duties (e.g. 'Client: Executive Sponsor and privileged access provisioning').\n"
        f"6. critical_risks: Identify 2 delivery risks and concrete mitigations in {target_language}.\n"
        "7. wbs_breakdown: Generate a comprehensive Work Breakdown Structure (WBS) with delivery phases. Assign realistic effort hours based on project size. MANDATORY: The engineering profile must be strictly one of: 'gerente_cuenta', 'arquitecto', 'experto', 'project_manager', 'tecnico_medio', 'tecnico_junior'.\n"
        "8. capex_estimate: Rigorously estimate initial capital expenditure (CapEx) in network gear, servers, appliances, or baseline licensing. Differentiate from OpEx subscriptions. Prohibit cloning the same estimate across all projects.\n"
        "9. roi_justification: Articulate quantitative ROI based on the mitigated risk (hard/soft operational savings and ALE avoidance).\n"
        f"10. deliverables: MANDATORY to generate 3-4 tangible, operational technical deliverables written in {target_language}. STRICTLY PROHIBITED from generating empty clichés like 'Design Document' or 'Test Plan'. For FinOps deliver 'Cost Allocation Model (Showback/Chargeback)' or 'Cloud Tagging and Rightsizing Policy'; for Architecture deliver 'ARB Governance Charter'; for Infrastructure deliver 'Terraform Manifests' or 'Ansible Playbooks'.\n"
        "\nReturn the information strictly in the requested JSON schema."
    )
    return prompt
