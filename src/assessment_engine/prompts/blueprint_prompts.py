from pathlib import Path

def load_prompt_config(filename: str) -> dict:
    """Carga un archivo de configuración de prompt YAML."""
    import yaml  # type: ignore

    # Ubicamos el directorio registry relativo a este archivo
    registry_dir = Path(__file__).resolve().parent / "registry"
    filepath = registry_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"No se encontró el archivo de prompt: {filepath}")

    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_blueprint_architect_instruction() -> str:
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
