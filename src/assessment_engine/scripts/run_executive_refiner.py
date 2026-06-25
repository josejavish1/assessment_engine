"""Contains the core logic and primary utilities for the Assessment Engine pipeline."""

import asyncio
import json
import os
import sys
from pathlib import Path

import vertexai
from google.adk.agents import Agent
from pydantic import RootModel
from vertexai.agent_engines import AdkApp

from assessment_engine.prompts.global_prompts import (
    get_executive_refiner_instruction,
    get_executive_section_prompt,
)
from assessment_engine.schemas.global_report import (
    BurningPlatformItem,
    ExecutionRoadmapDraft,
    ExecutiveDecisionsDraft,
    ExecutiveSummaryDraft,
    TargetVisionDraft,
    TowerBottomLineItem,
)
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role

ROOT = Path(__file__).resolve().parents[1]


# Type alias for list-based data structures to improve type-hinting clarity and code readability.
class BurningPlatformList(RootModel):
    """Represent a list of BurningPlatformItem objects as a Pydantic RootModel."""
    root: list[BurningPlatformItem]


class TowerBottomLineList(RootModel):
    """Define a root model for a list of `TowerBottomLineItem` objects."""
    root: list[TowerBottomLineItem]


async def call_llm_for_section(
    model_name,
    section_name,
    instruction,
    payload_str,
    schema_cls,
    client_name="la compañía",
):
    r"""{'docstring': 'Asynchronously executes a language model agent to parse and structure a document section.\n\n    Initializes and configures an `Agent` and `AdkApp` to process a given text\n    payload. It constructs a detailed prompt by combining a base instruction with the\n    section-specific instruction, client name, and payload. The function then\n    invokes the agent asynchronously. Any exceptions encountered during the\n    agent\'s execution or the parsing of its response are caught, logged to standard\n    output, and result in a `None` return value.\n\n    Args:\n        model_name (str): The identifier for the language model to be used.\n        section_name (str): An identifier for the document section being processed,\n            used for naming the agent and logging.\n        instruction (str): A specific directive for the agent on how to process\n            the payload.\n        payload_str (str): The raw string content of the section to be refined.\n        schema_cls (Type[SchemaT]): The class defining the desired output structure,\n            typically a Pydantic model.\n        client_name (str): The name of the client to be inserted into the prompt.\n            Defaults to "la compañía".\n\n    Returns:\n        Optional[SchemaT]: An instance of `schema_cls` populated with the data\n        extracted and refined by the language model, or `None` if an exception\n        occurs during the process.'}."""
    agent = Agent(
        model=model_name,
        name=f"executive_cio_refiner_{section_name}",
        instruction=get_executive_refiner_instruction(),
        output_schema=schema_cls,
    )
    app = AdkApp(agent=agent)

    prompt = get_executive_section_prompt(
        instruction=instruction, payload_str=payload_str, client_name=client_name
    )

    try:
        result = await run_agent(
            app, user_id=f"refiner-{section_name}", message=prompt, schema=schema_cls
        )
        return result
    except Exception as e:
        print(f"Error parseando sección {section_name}: {e}")
        return None


async def refine_executive_payload(payload):
    """Asynchronously orchestrates the generation of a structured executive report from a raw data payload.

    This function serves as an asynchronous orchestrator that sequentially invokes
    a Large Language Model (LLM) via the Vertex AI SDK to generate distinct
    sections of an executive report. It initializes the Vertex AI client using
    `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` environment variables and
    resolves the appropriate generative model name. The input payload is
    serialized to a JSON string to serve as the context for a series of LLM
    calls, each targeting a specific report section. The final output is a
    composite dictionary containing both select original data from the input and
    the newly generated, structured content.

    Args:
        payload (dict): The input dictionary containing the raw data and metadata
            to be refined. This payload is used as the context for the LLM and
            is expected to contain keys such as `meta`, `visuals`, `heatmap`,
            and `intelligence_dossier`.

    Returns:
        dict: A dictionary representing the complete report. It includes keys
            copied from the input `payload` (`meta`, `visuals`, `heatmap`,
            `intelligence_dossier`) and the newly generated sections
            (`executive_summary`, `burning_platform`, `tower_bottom_lines`,
            `target_vision`, `execution_roadmap`, `executive_decisions`). A
            generated section key is omitted if its generation fails or returns
            no content.

    Raises:
        ValueError: If the `GOOGLE_CLOUD_PROJECT` environment variable is not set.
        TypeError: If the input `payload` contains objects that are not JSON
            serializable.
        Exception: Propagates exceptions from underlying Vertex AI API calls,
            which may include errors related to authentication, permissions,
            invalid arguments, or network timeouts.
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    vertexai.init(project=project, location=location)

    try:
        model_name = resolve_model_profile_for_role("global_refiner")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    payload_str = json.dumps(payload, ensure_ascii=False)
    client_name = payload.get("meta", {}).get("client", "la compañía")

    final_payload = {
        "meta": payload.get("meta", {}),
        "visuals": payload.get("visuals", {}),
        "heatmap": payload.get("heatmap", []),
        "intelligence_dossier": payload.get("intelligence_dossier", {}),
    }

    print("Iteración 1: Generando Executive Summary...")
    exec_summary = await call_llm_for_section(
        model_name,
        "executive_summary",
        "Genera un resumen ejecutivo de impacto.",
        payload_str,
        ExecutiveSummaryDraft,
        client_name,
    )
    if exec_summary:
        final_payload["executive_summary"] = exec_summary

    print("Iteración 2: Generando Burning Platform...")
    burning = await call_llm_for_section(
        model_name,
        "burning_platform",
        "Genera la lista de principales riesgos sistémicos.",
        payload_str,
        BurningPlatformList,
        client_name,
    )
    if burning:
        final_payload["burning_platform"] = burning

    print("Iteración 3: Generando Tower Bottom Lines...")
    bottom_lines = await call_llm_for_section(
        model_name,
        "tower_bottom_lines",
        "Genera una lista de objetos para cada una de las torres. Cada objeto DEBE tener los campos originales ('id', 'name', 'score', 'band', 'status_color') MÁS un campo 'bottom_line' (una frase contundente de diagnóstico).",
        payload_str,
        TowerBottomLineList,
        client_name,
    )
    if bottom_lines:
        final_payload["tower_bottom_lines"] = bottom_lines

    print("Iteración 4: Generando Target Vision y Principios...")
    vision = await call_llm_for_section(
        model_name,
        "target_vision",
        """Los principios deben reflejar reglas de oro de arquitectura y negocio basadas en los gaps detectados. Los pilares estratégicos deben explicar el 'por qué' de la transformación, no solo nombrar proyectos.
        IMPORTANTE REDACCIÓN: No utilices guiones largos (─ o —) ni punto y coma (;) en ningún campo de texto. Utiliza frases directas, separadas por puntos, sin enumeraciones ocultas dentro de los párrafos.""",
        payload_str,
        TargetVisionDraft,
        client_name,
    )
    if vision:
        final_payload["target_vision"] = vision

    print("Iteración 5: Generando Roadmap y Ejecución...")
    roadmap = await call_llm_for_section(
        model_name,
        "execution_roadmap",
        """Genera el plan de ejecución a 36 meses distribuyendo las iniciativas en horizontes lógicos.""",
        payload_str,
        ExecutionRoadmapDraft,
        client_name,
    )
    if roadmap:
        final_payload["execution_roadmap"] = roadmap

    print("Iteración 6: Generando Executive Decisions...")
    decisions = await call_llm_for_section(
        model_name,
        "executive_decisions",
        """Genera la lista de decisiones ejecutivas inmediatas (financieras, orgánicas, o de vendor).""",
        payload_str,
        ExecutiveDecisionsDraft,
        client_name,
    )
    if decisions:
        final_payload["executive_decisions"] = decisions

    return final_payload


def main(argv: list[str] | None = None) -> None:
    """Run the executive payload refinement process on a specified JSON file.

    This function serves as the main entry point for the command-line interface.
    It reads a JSON object from a file path specified via a command-line
    argument, processes it using the `refine_executive_payload` coroutine, and
    overwrites the original file with the refined JSON object.

    Args:
        argv: A list of command-line arguments. If `None`, `sys.argv` is used.
            The list is expected to contain the script name followed by the path
            to the target JSON payload file.

    Raises:
        SystemExit: If the path to the payload JSON file is not provided.
        FileNotFoundError: If the file at the specified path does not exist.
        PermissionError: If the file cannot be read from or written to due to
            insufficient permissions.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python run_executive_refiner.py <payload_json>")
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    with payload_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    final_payload = asyncio.run(refine_executive_payload(payload))

    with payload_path.open("w", encoding="utf-8") as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Payload refinado guardado en: {payload_path}")


if __name__ == "__main__":
    main()
