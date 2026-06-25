import asyncio
import glob
import json
import os
import sys
from pathlib import Path

from google.adk.agents import Agent
from pydantic import BaseModel, Field
from vertexai.agent_engines import AdkApp

from infrastructure.ai_client import run_agent


class PriorityAction(BaseModel):
    """Represents a prioritized group of strategic technical initiatives.

    This data model structures a set of related actions under a common theme,
    implementation timeline, and business justification.

    Attributes:
        horizon (str): The implementation time horizon for the initiative. Examples:
            '[Quick Win]', '[Short Term]', '[Medium Term]'.
        title (str): A semantic title for the initiative group. Example: 'End-to-End
            Immutability in Backup and Recovery Systems'.
        actions (list[str]): A list of specific technical actions or projects
            that constitute this initiative group.
        justification (str): The business rationale articulating the strategic
            priority for executing this block of initiatives.
    """
    horizon: str = Field(..., description="The implementation time horizon for the initiative. Examples: '[Quick Win]', '[Short Term]', '[Medium Term]'.")
    title: str = Field(..., description="A semantic title for the initiative group. Example: 'End-to-End Immutability in Backup and Recovery Systems'.")
    actions: list[str] = Field(..., description="A list of bullet points detailing the specific technical actions or projects that constitute this initiative group.")
    justification: str = Field(..., description="The business rationale articulating the strategic priority for executing this block of initiatives.")

class GlobalExecutiveSummary(BaseModel):
    """A data model for the globally synthesized executive summary report.

    This class defines the structured output for a high-level, cross-functional
    analysis of technology risks and recommended actions, suitable for an
    executive audience.

    Attributes:
        executive_context: An introductory paragraph establishing the business
            context, including relevant background such as major outages, critical
            incidents, or systemic risks. The language must be concise,
            executive-level, and impact-oriented.
        cross_tower_synthesis: A list of 3 to 5 bullet points synthesizing the
            most critical cross-functional issues identified across all technology
            verticals. This field must focus on systemic patterns (e.g.,
            technical debt, manual operations, governance gaps) rather than
            isolated vertical-specific problems.
        cost_of_inaction_narrative: A concluding summary paragraph. It must
            explicitly state the total financial Annualized Loss Expectancy (ALE)
            value provided in the input prompt and articulate the unacceptability
            of maintaining the current operational status quo.
        priority_actions_taxonomy: A semantic grouping of prioritized actions and
            projects, structured as a coherent consulting narrative.
    """
    executive_context: str = Field(
        ...,
        description="An introductory paragraph establishing the business context, including relevant background such as major outages, critical incidents, or systemic risks. The language must be concise, executive-level, and impact-oriented."
    )
    cross_tower_synthesis: list[str] = Field(
        ...,
        description="A list of 3 to 5 bullet points synthesizing the most critical cross-functional issues identified across all technology verticals. This field must focus on systemic patterns (e.g., technical debt, manual operations, governance gaps) rather than isolated vertical-specific problems."
    )
    cost_of_inaction_narrative: str = Field(
        ...,
        description="A concluding summary paragraph. It must explicitly state the total financial Annualized Loss Expectancy (ALE) value provided in the input prompt and articulate the unacceptability of maintaining the current operational status quo."
    )
    priority_actions_taxonomy: list[PriorityAction] = Field(
        ...,
        description="A semantic grouping of prioritized actions and projects, structured as a coherent consulting narrative."
    )

async def synthesize_global_asis(working_dir: str):
    """Asynchronously aggregates tower data to synthesize a global executive summary.

    This coroutine scans the specified working directory for JSON payloads that
    match the pattern `T*/blueprint_*_payload.json`. It extracts and aggregates
    financial risk metrics (FAIR ALE), individual tower summaries, and proposed
    project initiatives from each payload file. This data is then consolidated
    with business context loaded from an optional `client_intelligence.json` file.

    A comprehensive prompt is constructed from the aggregated data and submitted
    to an external generative AI agent. The agent's structured JSON response is
    subsequently written to `global_asis_executive_summary.json` within the
    working directory.

    Note:
        Exceptions during file I/O or AI agent interaction are caught and
        logged to standard output, preventing process termination. Malformed JSON
        in `client_intelligence.json` is silently ignored.

    Args:
        working_dir (str): The path to the root working directory containing
            tower subdirectories and input JSON files.

    Returns:
        None. The function's output is persisted to a file as a side effect.
    """
    print("🚀 Iniciando Global Executive Synthesizer (SOTA 2026)...")
    
    payloads = []
    total_ale_global = 0.0
    tower_summaries = []
    all_projects = []
    
    search_pattern = os.path.join(working_dir, "T*", "blueprint_*_payload.json")
    for file_path in glob.glob(search_pattern):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            payloads.append(data)
            
            total_ale_global += data.get("total_fair_ale", 0.0)
            snapshot = data.get("executive_snapshot", {})
            tower_summaries.append(
                f"--- TORRE: {data.get('document_meta', {}).get('tower_name')} ---\n"
                f"{snapshot.get('bottom_line', '')}\n"
            )
            
            for pilar in data.get("pillars_analysis", []):
                for proj in pilar.get("projects_todo", []):
                    all_projects.append(f"- [{proj.get('sizing', 'N/A')}] {proj.get('initiative', proj.get('name', ''))}: {proj.get('objective', '')}")

            
    if not payloads:
        print("❌ No payloads found for synthesis.")
        return

    client_name = payloads[0].get("document_meta", {}).get("client_name", "Cliente")
    
    # Establishes the foundational business context from client intelligence data, which is a prerequisite for all subsequent synthesis and analytical operations.
    intel_str = "Operador de infraestructura crítica."
    intel_path = Path(working_dir) / "client_intelligence.json"
    if intel_path.exists():
        try:
            intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
            intel_str = json.dumps(intel_data.get("business_context", {}), indent=2)
        except Exception:
            pass

    prompt = (
        f"Eres el Socio Director de Arquitectura Empresarial de NTT DATA.\n"
        f"Tu misión es redactar el Resumen Ejecutivo Global (AS-IS) para el Comité de Dirección de {client_name}.\n\n"
        f"ANTECEDENTES DEL CLIENTE:\n{intel_str}\n\n"
        f"RESÚMENES TÉCNICOS POR TORRE:\n{''.join(tower_summaries)}\n\n"
        f"LISTADO BRUTO DE PROYECTOS PROPUESTOS (Talla S/M/L):\n{chr(10).join(all_projects)}\n\n"
        f"MANDATO MATEMÁTICO (COI): El sumatorio total de la exposición financiera al riesgo (FAIR ALE) es de {total_ale_global:,.2f} € anuales.\n\n"
        "INSTRUCCIONES (PATRÓN SOTA PLANNER-EXECUTOR):\n"
        "1. No hagas un 'copia-pega' de las torres. Busca patrones transversales.\n"
        "2. Redacta el 'executive_context' anclando al directivo en su realidad de negocio (apagones, regulaciones).\n"
        "3. Redacta las viñetas de 'cross_tower_synthesis' explicando los problemas sistémicos (ej. silos, procesos manuales).\n"
        "4. Redacta el 'cost_of_inaction_narrative' inyectando el valor exacto en euros que te he dado, con un tono urgente y comercial.\n"
        "5. Genera el 'priority_actions_taxonomy' analizando el listado bruto de proyectos. Agrupa los más críticos (especialmente los Quick Wins o talla S/M) en bloques semánticos (ej. 'Refuerzo de resiliencia'), define su horizonte, redacta las acciones concretas en base a los proyectos, y escribe una justificación narrativa para el directivo.\n"
        "Responde EXCLUSIVAMENTE con el JSON solicitado."
    )

    try:
        synthesizer_agent = Agent(
            name="global_executive_synthesizer",
            model="gemini-2.5-pro",
            instruction="Eres un Socio Director de NTT DATA experto en redacción ejecutiva. Devuelve estrictamente el JSON pedido.",
            output_schema=GlobalExecutiveSummary,
        )
        app_synthesizer = AdkApp(agent=synthesizer_agent)
        
        result = await run_agent(
            app_synthesizer,
            user_id="global_synthesizer",
            message=prompt,
            schema=GlobalExecutiveSummary,
        )
        
        if result:
            out_path = Path(working_dir) / "global_asis_executive_summary.json"
            out_path.write_text(json.dumps(result, indent=4, ensure_ascii=False), encoding="utf-8-sig")
            print(f"✅ Síntesis Ejecutiva Global guardada en: {out_path}")
        else:
            print("⚠️ El agente no devolvió resultados.")
            
    except Exception as e:
        print(f"⚠️ Error en Global Executive Synthesizer: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python run_global_synthesizer.py <working_dir>")
        sys.exit(1)
    asyncio.run(synthesize_global_asis(sys.argv[1]))
