import logging
from typing import Dict, List

from google.adk.agents import Agent
from pydantic import BaseModel, Field
from vertexai.agent_engines import AdkApp

from infrastructure.ai_client import run_agent

logger = logging.getLogger(__name__)


class EpistemicTriple(BaseModel):
    """Represent an epistemic knowledge triplet as a (subject, predicate, object) structure."""

    subject: str = Field(
        description="The subject of the knowledge triplet, representing the primary entity or concept. Example: 'REDEIA'."
    )
    predicate: str = Field(
        description="The predicate of the knowledge triplet, defining the attribute or relationship that links the subject to the object. Examples: 'CLOUD_PROVIDER', 'MAIN_HYPERSCALER', 'INDUSTRY'."
    )
    object_val: str = Field(
        description="The object of the knowledge triplet, representing the value associated with the subject's attribute or relationship. Examples: 'AWS', 'Azure', 'Energy'."
    )


class EpistemicTriplesList(BaseModel):
    """Model a list of epistemic triples."""

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
    """Asynchronously extracts knowledge triplets from unstructured text using a generative model.

    The function queries a specified generative AI model to parse technological and
    strategic information from the input text. Input is truncated to the first
    15,000 characters to adhere to model context limits and manage latency.
    All exceptions during the extraction process are caught internally, logged, and
    result in an empty list being returned.

    Args:
        text: The unstructured source text from which to extract triplets.
        model_name: The identifier for the generative model to use.

    Returns:
        A list of dictionaries, each representing a (subject, predicate, object)
        triplet. Returns an empty list if no triplets are found or if an
        internal error occurs during processing.
    """
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
