from pathlib import Path


def load_prompt_config(filename: str) -> dict:
    """Loads a prompt configuration from a YAML-formatted file.

    This function resolves an absolute path to the specified filename within a
    'registry' subdirectory, which is expected to exist in the same directory
    as this source file. It then reads the file and parses its YAML content
    using a safe loader.

    Args:
        filename (str): The name of the YAML configuration file to load from the
            'registry' directory.

    Returns:
        dict: A dictionary representing the parsed YAML configuration from the file.

    Raises:
        FileNotFoundError: If the specified file does not exist within the
            'registry' directory.
    """
    import yaml  # type: ignore

    # Establishes the absolute path to the 'registry' directory, which is positioned relative to this source file.
    registry_dir = Path(__file__).resolve().parent / "registry"
    filepath = registry_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"No se encontró el archivo de prompt: {filepath}")

    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_blueprint_architect_instruction() -> str:
    """Construct the instruction prompt for the Blueprint Architect agent.

    This function loads configuration from 'blueprint_architect_instruction.yaml'
    and formats it into a string that defines the agent's persona and
    operational constraints. The prompt includes the agent's role, expertise,
    mission, and a numbered enumeration of critical rules.

    Returns:
        str: The fully formatted instruction prompt as a single string.

    Raises:
        FileNotFoundError: If the 'blueprint_architect_instruction.yaml' file
            cannot be found or accessed.
        KeyError: If the configuration data lacks the required keys: 'role',
            'expertise', 'mission', or 'critical_rules'.
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
) -> str:
    """Assembles a prompt for an AI model by merging a static YAML template with dynamic contextual data.

    This function constructs a detailed text prompt intended for a large language
    model. It loads a base template from a YAML configuration file
    (`blueprint_pilar_architect_prompt.yaml`) which defines the AI's role,
    task, and operational rules. This static configuration is then combined
    with dynamic, request-specific information such as business context,
    strategic intelligence ("Minuto Cero"), and technical findings from client
    answers.

    The final output is a structured string formatted in Spanish, designed to
    guide the AI in generating a structured JSON response.

    Args:
        tower_name: The name of the business tower being analyzed.
        pilar_label: The descriptive label for the specific pilar.
        pilar_score: The numerical score assigned to the pilar.
        context_str: A string providing the overall business context.
        intel_str: A string containing strategic intelligence, also known as
            "Minuto Cero".
        answers_json: A JSON-formatted string of client answers to technical
            questions.
        pilar_id: The unique identifier for the pilar. Note: This argument is
            not currently used in the function's implementation.

    Returns:
        The fully constructed prompt string, ready for submission to an AI model.

    Raises:
        FileNotFoundError: If the `blueprint_pilar_architect_prompt.yaml`
            configuration file cannot be found by the `load_prompt_config` utility.
        KeyError: If the loaded YAML configuration is missing one of the required
            keys: 'role', 'context_description', 'task', or 'golden_rules'.
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

    return prompt


def get_critic_prompt(pilar_label: str, client_name: str, raw_output_json: str) -> str:
    """Constructs a critique prompt for a JSON blueprint draft from a YAML configuration.

    This function loads a prompt template from a YAML configuration file
    (`blueprint_critic_prompt.yaml`) and interpolates it with client-specific
    details and the JSON content to be critiqued. The resulting prompt instructs
    a language model to act as a specialized critic, evaluating the provided JSON
    draft against a set of predefined objectives.

    Args:
        pilar_label: The specific pillar label (e.g., 'Content Strategy') for
            which the blueprint was generated.
        client_name: The name of the client associated with the blueprint.
        raw_output_json: A string representation of the raw JSON blueprint draft
            to be reviewed.

    Returns:
        A fully assembled prompt string formatted for the critic language model.

    Raises:
        FileNotFoundError: If the `blueprint_critic_prompt.yaml` configuration file
            cannot be located by the underlying loader.
        KeyError: If the loaded YAML configuration is missing required keys,
            such as 'role', 'mission', 'review_objectives', or
            'handover_instruction'.
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

    return prompt


def get_closing_orchestrator_prompt(
    tower_name: str, pillars_analysis_json: str, intel_str: str
) -> str:
    r"""{'docstring': "Constructs the final orchestrator prompt for a specified business tower.\n\nThis function assembles a detailed prompt by loading a base template from a YAML configuration file (`blueprint_closing_orchestrator_prompt.yaml`). It then injects tower-specific pillar analysis, customer intelligence, and structured instructions from the configuration into this template. The resulting string is formatted for consumption by a large language model.\n\nArgs:\n    tower_name: The name of the business tower for which the prompt is being\n        generated.\n    pillars_analysis_json: A JSON-formatted string containing the detailed\n        analysis of the tower's pillars.\n    intel_str: A string containing supplementary customer intelligence data.\n\nReturns:\n    A fully-formed prompt string, incorporating all provided inputs and\n    configuration rules, ready for use with an AI model.\n\nRaises:\n    FileNotFoundError: If the 'blueprint_closing_orchestrator_prompt.yaml' \n        configuration file cannot be located by the underlying `load_prompt_config`\n        function.\n    KeyError: If the loaded configuration from the YAML file is missing one or\n        more of the required keys: 'role', 'task_and_tone', or\n        'structure_requirements'."}."""
    config = load_prompt_config("blueprint_closing_orchestrator_prompt.yaml")

    prompt = f"Eres el {config['role']}. Aquí tienes el análisis de todos los pilares de la torre {tower_name}:\n"
    prompt += f"{pillars_analysis_json}\n\n"

    prompt += f"Basado en esto y en el ADN del cliente: {intel_str}\n\n"

    prompt += "TAREA Y REGLAS DE TONO:\n"
    for rule in config["task_and_tone"]:
        prompt += f"- {rule}\n"

    prompt += "\n"
    for step, desc in config["structure_requirements"].items():
        prompt += f"{step}. {desc}\n"

    prompt += "\nDevuelve la informacion en formato JSON estructurado.\n"
    return prompt
