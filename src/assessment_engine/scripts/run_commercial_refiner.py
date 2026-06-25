"""Orchestrates the commercial refiner pipeline for the Assessment Engine.

This module provides the primary entry point for executing the commercial data refinement process. It integrates various system components to process and enhance commercial data against predefined assessment criteria.
"""

import asyncio
import json
import sys
from pathlib import Path

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.prompts.commercial_prompts import (
    get_commercial_agent_prompt,
    get_commercial_orchestrator_instruction,
)
from assessment_engine.schemas.commercial import (
    AccountDirectorOutput,
    DeliveryAndRiskDirectorOutput,
    EngagementManagerOutput,
    LeadSolutionsArchitectOutput,
    PresalesArchitectOutput,
    SalesPartnerOutput,
)
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role

ROOT = Path(__file__).resolve().parents[1]


async def call_commercial_agent(
    model_name,
    agent_role,
    instruction,
    payload_str,
    schema_cls,
    client_name="el cliente",
):
    """Asynchronously executes a configured agent to process a payload against a schema.

    Initializes and runs an `Agent` instance to process a string payload
    according to a given role and instruction. The function constructs a prompt,
    invokes the agent, and attempts to parse the output into a dictionary that
    conforms to the provided schema class. All exceptions encountered during
    agent execution or output parsing are caught, an error message is printed
    to standard output, and an empty dictionary is returned.

    Args:
        model_name (str): The identifier for the language model to be used by the agent.
        agent_role (str): A string defining the functional role of the agent, used
            for prompt generation and user identification.
        instruction (str): The specific instruction detailing the agent's task.
        payload_str (str): The string-formatted data payload for the agent to process.
        schema_cls (Type): The class defining the structure of the expected output,
            typically a Pydantic `BaseModel`.
        client_name (str): The name of the client. This parameter is reserved for
            future use and does not currently affect function behavior.

    Returns:
        Dict[str, Any]: A dictionary conforming to `schema_cls` containing the
            agent's processed output. Returns an empty dictionary if any exception
            occurs during execution.
    """
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
    """Asynchronously orchestrates a sequence of specialized agents to construct a commercial proposal.

    This function sequentially invokes four distinct commercial agents (Engagement
    Manager, Lead Solutions Architect, Delivery & Risk Director, and Sales Partner)
    to generate specific sections of a proactive commercial proposal. The outputs
    from each agent are then aggregated into a single, structured dictionary.

    Args:
        model_name (str): The identifier for the language model to be used by the agents.
        opp (dict): A dictionary containing details of the commercial opportunity.
            It is expected to contain an 'initiative' key for the proposal name.
        payload_str (str): A serialized string containing the core contextual data
            to be processed by the agents.
        client_name (str): The name of the client for whom the proposal is generated.

    Returns:
        dict: A dictionary containing the fully assembled commercial proposal with
            the following structure:
            - initiative_name (str): Name of the initiative.
            - context_and_why (dict): Context and value proposition.
            - solution_and_what (dict): Proposed solution details.
            - scope_and_how (dict): Technical scope and approach.
            - delivery_team (dict): Proposed delivery team structure.
            - ai_transformation_strategy (str): AI transformation narrative.
            - governance_and_assumptions (dict): Governance model and assumptions.
            - risk_management (list): Identified risks.
            - activation_plan (list): High-level activation plan.
            - why_ntt_data (dict): Differentiators and company value.
            - investment_and_timeline (dict): Investment and timeline details.
            - executive_synthesis (str): A concise executive summary.
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
    """Aggregates technical blueprint JSON files into a unified catalog dictionary.

    Parses a list of JSON files, each representing a technical blueprint, and
    compiles their contents into a single dictionary. The function extracts
    metadata, executive summaries, technical debt assessments, and project
    initiatives based on an expected schema within each JSON file.

    The resulting catalog is keyed by the `tower_code` from each blueprint's
    `document_meta` section. If a file cannot be read or parsed, a warning
    is printed to the console, and that file is skipped.

    Args:
        blueprint_paths: A list of `pathlib.Path` objects, where each path
            points to a blueprint JSON file.

    Returns:
        A dictionary mapping tower codes to their aggregated blueprint data.
        Each value is a dictionary containing the tower's 'tower_name' (str),
        'executive_bottom_line' (str), 'technical_debt' (str), and a list of
        'initiatives'. Each initiative in the list is a dictionary with keys
        for 'name', 'objective', 'sizing', and 'deliverables'.
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
    blueprints_catalog: dict = None,  #
    intelligence_dossier: dict | None = None,
):
    r"""["Asynchronously orchestrates a multi-agent AI system to generate a commercial payload.\n\n    This function coordinates a sequence of calls to specialized AI agents to\n    construct a comprehensive commercial strategy document. The process involves\n    three primary phases:\n    1.  Strategy Generation: Generates a high-level executive summary, a\n        go-to-market strategy, and a stakeholder map.\n    2.  Pipeline Qualification: Analyzes the strategy against a catalog of\n        technical blueprints to produce a qualified sales pipeline.\n    3.  Proposal Construction: Builds detailed, proactive proposals for the\n        top opportunities identified in the pipeline.\n\n    Args:\n        payload: The primary input dictionary containing the strategic\n            context and client metadata.\n        blueprints_catalog: A catalog of tactical technical blueprints for\n            cross-referencing against the global strategy. If not provided, an\n            empty dictionary is used.\n        intelligence_dossier: Specific intelligence data regarding the client.\n            If not provided, the function attempts to source this information\n            from `payload.get('intelligence_dossier')`.\n\n    Returns:\n        A dictionary containing the fully refined commercial payload. This\n        includes the generated strategy components, an 'opportunities_pipeline'\n        list, and a 'proactive_proposals' list for the top identified\n        opportunities."]."""
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
        "Analiza el Roadmap Global y CRÚZALO con el catálogo 'tactical_tower_blueprints'. Genera un pipeline de oportunidades combinando las grandes iniciativas con los Quick Wins técnicos detectados en las torres (como Chaos Engineering, automatizaciones, BIA, etc.). Evalúa: vendor, revenue type, TCV y Manejo de Objeciones.",
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
    """Executes the commercial refiner process based on a client's global payload.

    This function serves as the main entry point for the command-line script. It
    orchestrates the reading of a primary payload file, discovers and aggregates
    associated technical blueprint payloads from subdirectories, and incorporates
    a client intelligence dossier if available. The combined data is processed
    asynchronously to produce a final commercial report, which is serialized to
    `commercial_report_payload.json` in the client's root directory.

    Args:
        argv: A list of command-line arguments. If None, `sys.argv` is used.
            The script expects a single argument: the path to the global
            payload JSON file.

    Returns:
        None. The function's output is written to a file as a side effect.

    Raises:
        SystemExit: If the path to the global payload file is not provided as a
            command-line argument.
        FileNotFoundError: If the global payload file specified in `argv` does
            not exist.
        json.JSONDecodeError: If the global payload file contains malformed JSON.
    """
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python run_commercial_refiner.py <global_payload_json>")
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    client_dir = payload_path.parent

    with payload_path.open("r", encoding="utf-8") as f:
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
