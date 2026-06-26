"""Defines the primary logic and utilities for the Assessment Engine pipeline."""

import asyncio
import json
import sys
from pathlib import Path

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.prompts.commercial_prompts import (
    get_commercial_agent_prompt,
    get_commercial_orchestrator_instruction,
)
from assessment_engine.domain.schemas.commercial import (
    AccountDirectorOutput,
    DeliveryAndRiskDirectorOutput,
    EngagementManagerOutput,
    LeadSolutionsArchitectOutput,
    PresalesArchitectOutput,
    SalesPartnerOutput,
)
from assessment_engine.infrastructure.ai_client import run_agent
from assessment_engine.infrastructure.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from assessment_engine.infrastructure.config_loader import (
    resolve_model_profile_for_role,
)

ROOT = Path(__file__).resolve().parents[1]


async def call_commercial_agent(
    model_name,
    agent_role,
    instruction,
    payload_str,
    schema_cls,
    client_name="el cliente",
):
    r"""{'docstring': 'Asynchronously invokes a commercial agent to process a payload against a schema.\n\n    Initializes an `Agent` instance with a specified model and instruction set.\n    The function then constructs a formatted prompt containing the payload and\n    executes the agent. It attempts to parse the agent\'s output using the\n    provided schema class. If any exception occurs during execution or parsing,\n    the error is printed to standard output and an empty dictionary is returned.\n\n    Args:\n        model_name (str): The identifier for the language model to be used.\n        agent_role (str): A descriptive role for the agent (e.g., "sales analyst")\n            used in prompt construction.\n        instruction (str): The specific task or command for the agent to execute.\n        payload_str (str): A string representation of the data payload for the\n            agent to process.\n        schema_cls (Type): The class definition (e.g., a Pydantic model) used to\n            validate and structure the agent\'s output.\n        client_name (str): The name of the client. Defaults to "el cliente".\n\n    Returns:\n        Any: An instance of `schema_cls` containing the structured output from the\n            agent on successful execution. Returns an empty dictionary (`{}`) if\n            any exception occurs during the process.'}."""
    agent = Agent(
        model=model_name,
        name=f"commercial_{agent_role.replace(' ', '')[-10:]}",
        instruction=get_commercial_orchestrator_instruction(),
        output_schema=schema_cls,
    )
    app = AdkApp(agent=agent)

    prompt = get_commercial_agent_prompt(
        agent_role=agent_role, instruction=instruction, payload_str=payload_str
    )

    try:
        result = await run_agent(
            app,
            user_id=f"commercial-{agent_role.replace(' ', '')[-10:]}",
            message=prompt,
            schema=schema_cls,
        )
        return result
    except Exception as e:
        print(f"Error parseando sección de {agent_role}: {e}")
        return {}


async def build_proactive_proposal(model_name, opp, payload_str, client_name):
    """Asynchronously orchestrates multiple AI agents to generate a commercial proposal.

    This coroutine coordinates four concurrent calls to distinct commercial AI
    agents, each responsible for a specific section of a proactive proposal. It
    awaits the completion of all agent tasks and aggregates their structured
    outputs into a single, comprehensive dictionary.

    Args:
        model_name (str): The identifier for the generative AI model to be used by
            the agents.
        opp (dict): A dictionary containing details about the commercial opportunity.
            It is expected to contain an 'initiative' key which provides the
            proposal's title.
        payload_str (str): A serialized data payload, such as a JSON string,
            containing the core context for proposal generation.
        client_name (str): The name of the client for whom the proposal is
            generated.

    Returns:
        dict: A dictionary representing the complete commercial proposal. The
            structure includes keys such as 'initiative_name',
            'context_and_why', 'solution_and_what', 'scope_and_how',
            'delivery_team', 'ai_transformation_strategy',
            'governance_and_assumptions', 'risk_management', 'activation_plan',
            'why_ntt_data', 'investment_and_timeline', and
            'executive_synthesis'.
    """
    opp_name = opp.get("initiative", "Iniciativa Estratégica")
    print(
        f"    -> 🟢 Agente A1 (Engagement Manager): Contexto y Valor para '{opp_name}'..."
    )
    ag1 = await call_commercial_agent(
        model_name,
        "ENGAGEMENT MANAGER",
        f"Genera el contexto y visión para la oportunidad '{opp_name}'.",
        payload_str,
        EngagementManagerOutput,
        client_name,
    )

    print(
        f"    -> 🔵 Agente A2 (Lead Solutions Architect): Alcance Técnico para '{opp_name}'..."
    )
    ag2 = await call_commercial_agent(
        model_name,
        "LEAD SOLUTIONS ARCHITECT",
        f"Genera el alcance y equipo de delivery para la oportunidad '{opp_name}'.",
        payload_str,
        LeadSolutionsArchitectOutput,
        client_name,
    )

    print(
        f"    -> 🟠 Agente A3 (Delivery & Risk Director): Gobierno y Riesgos para '{opp_name}'..."
    )
    ag3 = await call_commercial_agent(
        model_name,
        "DELIVERY & RISK DIRECTOR",
        f"Genera el modelo de gobierno, asunciones y riesgos para la oportunidad '{opp_name}'.",
        payload_str,
        DeliveryAndRiskDirectorOutput,
        client_name,
    )

    print(f"    -> 🔴 Agente A4 (Sales Partner): Pitch Final para '{opp_name}'...")
    ag4 = await call_commercial_agent(
        model_name,
        "SALES PARTNER",
        f"Genera los diferenciadores de NTT Data y el timeline de inversión para la oportunidad '{opp_name}'.",
        payload_str,
        SalesPartnerOutput,
        client_name,
    )

    proposal = {
        "initiative_name": opp_name,
        "context_and_why": ag1.get("context_and_why", {}),
        "solution_and_what": ag1.get("solution_and_what", {}),
        "scope_and_how": ag2.get("scope_and_how", {}),
        "delivery_team": ag2.get("delivery_team", {}),
        "ai_transformation_strategy": ag2.get("ai_transformation_strategy", ""),
        "governance_and_assumptions": ag3.get("governance_and_assumptions", {}),
        "risk_management": ag3.get("risk_management", []),
        "activation_plan": ag3.get("activation_plan", []),
        "why_ntt_data": ag4.get("why_ntt_data", {}),
        "investment_and_timeline": ag4.get("investment_and_timeline", {}),
        "executive_synthesis": ag4.get("executive_synthesis", ""),
    }
    return proposal


def aggregate_blueprint_catalogs(blueprint_paths: list[Path]) -> dict:
    """Aggregates multiple blueprint JSON files into a single structured catalog.

    This function iterates through a list of file paths, each pointing to a JSON
    file representing a 'tower' blueprint. It reads each file using 'utf-8-sig'
    encoding and extracts metadata, summaries, and project initiatives. The
    extracted data is organized into a dictionary keyed by tower ID.

    The process is designed to be robust. If a file cannot be read, contains
    malformed JSON, or an unexpected error occurs during processing, a message
    is printed to standard output, and the function proceeds to the next file.
    Missing keys within a valid JSON structure are handled gracefully by
    substituting default values (e.g., 'UNKNOWN', empty strings, or empty lists).

    Args:
        blueprint_paths (list[Path]): A list of `pathlib.Path` objects, where each
            path points to a blueprint JSON file to be processed.

    Returns:
        dict: A catalog where keys are tower IDs (str) and values are
            dictionaries containing the aggregated information for that tower.
            The structure for each tower's entry is as follows:
            {
                'tower_name': str,
                'executive_bottom_line': str,
                'technical_debt': str,
                'initiatives': [
                    {
                        'name': str | None,
                        'objective': str | None,
                        'sizing': typing.Any,
                        'deliverables': list
                    },
                    ...
                ]
            }
    """
    catalog = {}
    for bp_path in blueprint_paths:
        try:
            with bp_path.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)

            tower_id = data.get("document_meta", {}).get("tower_code", "UNKNOWN")
            tower_name = data.get("document_meta", {}).get("tower_name", "UNKNOWN")

            tower_entry = {
                "tower_name": tower_name,
                "executive_bottom_line": data.get("executive_snapshot", {}).get(
                    "bottom_line", ""
                ),
                "technical_debt": data.get("cross_capabilities_analysis", {}).get(
                    "critical_technical_debt", ""
                ),
                "initiatives": [],
            }

            for pilar in data.get("pillars_analysis", []):
                for proj in pilar.get("projects_todo", []):
                    tower_entry["initiatives"].append(
                        {
                            "name": proj.get("initiative") or proj.get("name"),
                            "objective": proj.get("objective")
                            or proj.get("tech_objective"),
                            "sizing": proj.get("sizing"),
                            "deliverables": proj.get("deliverables", []),
                        }
                    )

            catalog[tower_id] = tower_entry
        except Exception as e:
            print(f"⚠️ Error cargando blueprint {bp_path}: {e}")

    return catalog


async def refine_commercial_payload(
    payload,
    blueprints_catalog: dict = None,  # type: ignore
    intelligence_dossier: dict | None = None,
):
    r"""{'docstring': "Orchestrates a multi-agent system to refine a commercial payload.\n\n    This coroutine executes a three-phase process to generate a comprehensive\n    commercial strategy. It first defines a high-level strategy, then qualifies\n    a pipeline of opportunities by cross-referencing this strategy with tactical\n    blueprints, and finally builds detailed proposals for the highest-ranked\n    opportunities. The process leverages distinct agents for each phase: a 'Global\n    Account Director', a 'Presales Architect', and a proposal generation agent.\n\n    Args:\n        payload (dict): The primary input dictionary containing strategic global\n            context and client metadata under a 'meta' key. May also contain\n            an 'intelligence_dossier'.\n        blueprints_catalog (dict | None, optional): A catalog of tactical\n            blueprints providing technical context for opportunity generation.\n            Defaults to None, which is treated as an empty dictionary.\n        intelligence_dossier (dict | None, optional): Specific intelligence data\n            regarding the client. If None, the function attempts to source this\n            data from the `payload` dictionary. Defaults to None.\n\n    Returns:\n        dict: A refined commercial payload. The structure includes metadata,\n            an executive summary, go-to-market strategy, stakeholder map, a\n            qualified opportunity pipeline, and detailed proactive proposals.\n\n    Raises:\n        TypeError: If the internal context constructed from the inputs contains\n            objects that are not JSON-serializable.\n        Exception: Propagates exceptions raised from downstream agent\n            coroutines (`call_commercial_agent`, `build_proactive_proposal`),\n            which may include API errors or data validation failures."}."""
    try:
        model_name = resolve_model_profile_for_role("global_refiner")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    #
    hybrid_context = {
        "strategic_global_context": payload,
        "tactical_tower_blueprints": blueprints_catalog or {},
        "client_intelligence": intelligence_dossier
        or payload.get("intelligence_dossier", {}),
    }
    payload_str = json.dumps(hybrid_context, ensure_ascii=False)
    client_name = payload.get("meta", {}).get("client", "el cliente")

    final_payload = {
        "_generation_metadata": {
            "artifact_type": "commercial_payload",
            "artifact_version": "1.0.0",
        },
        "meta": payload.get("meta", {}),
        "intelligence_dossier": {
            "source_blueprints": list((blueprints_catalog or {}).keys()),
            "client_context": intelligence_dossier
            or payload.get("intelligence_dossier", {}),
        },
    }

    print(
        "\nFase 1: Estrategia de Cuenta (Agente 1: Global Account Director) ----------"
    )
    strategy = await call_commercial_agent(
        model_name,
        "GLOBAL ACCOUNT DIRECTOR",
        "Diseña el Executive Summary Comercial, la Estrategia Go-to-Market y el Mapa de Stakeholders basándote en la visión estratégica global.",
        payload_str,
        AccountDirectorOutput,
        client_name,
    )
    final_payload.update(strategy)

    print(
        "\nFase 2: Calificación de Pipeline (Agente 2: Presales Architect) ----------"
    )
    pipeline = await call_commercial_agent(
        model_name,
        "ENTERPRISE PRESALES ARCHITECT",
        "Analiza el Roadmap Global y CRÚZALO con el catálogo 'tactical_tower_blueprints'. Genera un pipeline de oportunidades combinando las grandes iniciativas con los Quick Wins técnicos detectados en las torres (como pruebas de resiliencia, automatizaciones, análisis BIA, etc.). Evalúa: vendor, revenue type, TCV y Manejo de Objeciones.",
        payload_str,
        PresalesArchitectOutput,
        client_name,
    )
    final_payload["opportunities_pipeline"] = pipeline.get("opportunities_pipeline", [])

    print(
        "\nFase 3: Propuestas Proactivas (Orquestación Multi-Agente) ----------------"
    )
    opps = final_payload.get("opportunities_pipeline", [])
    top_opps = opps[:2]
    proposals = []

    for idx, opp in enumerate(top_opps, start=1):
        print(f"\n  [Orquestando Proposal {idx}/2]")
        proposal = await build_proactive_proposal(
            model_name, opp, payload_str, client_name
        )
        proposals.append(proposal)

    final_payload["proactive_proposals"] = proposals

    return final_payload


def main(argv: list[str] | None = None) -> None:
    """Orchestrates the commercial refinement of a global payload from the command line.

    This function serves as the main entry point for the refinement process. It reads a specified global payload JSON file, discovers and aggregates context from related files within the same parent directory, invokes the core asynchronous refining logic, and writes the resulting commercial report to a new JSON file.

    The expected directory structure is as follows:
    - A parent directory (e.g., 'client_data/').
    - The input payload (e.g., 'client_data/global_payload.json').
    - Technical blueprint subdirectories (e.g., 'client_data/T01/', 'client_data/T02/').
    - An optional client intelligence file ('client_data/client_intelligence.json').

    Args:
        argv: A list of command-line arguments. If `None`, `sys.argv` is used.
            The list is expected to contain the script name followed by the path
            to the input global payload JSON file.

    Returns:
        None. The function's output is a side effect: the refined payload is
        written to `commercial_report_payload.json` in the same directory
        as the input payload, and progress is printed to standard output.

    Raises:
        FileNotFoundError: If the specified global payload JSON file does not exist.
        json.JSONDecodeError: If the global payload or any of the discovered
            context files (blueprints, client intelligence) contain malformed JSON.
    """
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python run_commercial_refiner.py <global_payload_json>")
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    client_dir = payload_path.parent

    with payload_path.open("r", encoding="utf-8-sig") as f:
        payload = json.load(f)

    #
    blueprint_paths = list(client_dir.glob("T*/blueprint_*_payload.json"))
    print(
        f"🔍 Encontrados {len(blueprint_paths)} blueprints técnicos para el contexto híbrido."
    )
    catalog = aggregate_blueprint_catalogs(blueprint_paths)
    intelligence_path = client_dir / "client_intelligence.json"
    intelligence_dossier = {}
    if intelligence_path.exists():
        intelligence_dossier = build_client_context_packet(
            load_client_intelligence(intelligence_path)
        )

    final_payload = asyncio.run(
        refine_commercial_payload(
            payload,
            blueprints_catalog=catalog,
            intelligence_dossier=intelligence_dossier,
        )
    )

    output_path = payload_path.parent / "commercial_report_payload.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Payload comercial refinado guardado en: {output_path}")


if __name__ == "__main__":
    main()
