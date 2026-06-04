import logging
from typing import Dict, List

from google.adk.agents import Agent
from pydantic import BaseModel, Field
from vertexai.agent_engines import AdkApp

from infrastructure.ai_client import run_agent

logger = logging.getLogger(__name__)


class EpistemicTriple(BaseModel):
    subject: str = Field(description="Entidad o concepto principal, e.g., 'REDEIA'")
    predicate: str = Field(
        description="Atributo o relación, e.g., 'CLOUD_PROVIDER', 'MAIN_HYPERSCALER', 'INDUSTRY'"
    )
    object_val: str = Field(
        description="Valor del atributo, e.g., 'AWS', 'Azure', 'Energy'"
    )


class EpistemicTriplesList(BaseModel):
    triples: List[EpistemicTriple] = Field(default_factory=list)


INSTRUCTION = """
Eres un analizador epistémico de élite (Information Extraction).
Tu único objetivo es extraer "hechos absolutos" del texto proporcionado y convertirlos en Tripletas (Sujeto, Predicado, Objeto).
Concéntrate exclusivamente en datos clave de arquitectura tecnológica (Cloud Providers, Herramientas Core, Regulaciones, Estrategias a nivel C-Level).
Extrae afirmaciones rotundas. Ignora dudas o suposiciones débiles.
Normaliza el 'predicate' usando nombres en MAYÚSCULAS y separados por guiones bajos (e.g., CLOUD_PROVIDER_PRINCIPAL, REGULACION_APLICABLE).
"""


async def extract_triples_from_text(
    text: str, model_name: str = "gemini-2.5-flash"
) -> List[Dict[str, str]]:
    """Extrae tripletas de conocimiento de un texto crudo usando Gemini Flash."""
    try:
        agent = Agent(
            name="epistemic_extractor",
            model=model_name,
            instruction=INSTRUCTION,
            output_schema=EpistemicTriplesList,
        )
        app = AdkApp(agent=agent)

        prompt = f"Analiza este texto y extrae TODAS las tripletas tecnológicas y estratégicas relevantes:\n\n{text[:15000]}"

        result = await run_agent(
            app, user_id="extractor_system", message=prompt, schema=EpistemicTriplesList
        )

        if result and "triples" in result:
            return list(result["triples"])
        return []
    except Exception as e:
        logger.error(f"Fallo en la extracción epistémica: {e}")
        return []
