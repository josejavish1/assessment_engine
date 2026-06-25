from pathlib import Path
from typing import Any, Dict

import docx


def extract_core_grounding(docx_path: Path) -> Dict[str, Any]:
    """Extracts core grounding information from a DOCX document.

    Reads a Microsoft Word (.docx) file to extract a baseline data set for
    grounding purposes. The function retrieves the source filename and a
    truncated text blob derived from the document's paragraphs. The text
    extraction concatenates all paragraph text and truncates the result to a
    fixed character limit.

    Args:
        docx_path: The file system path to the input .docx document.

    Returns:
        A dictionary containing grounding data: 'text_blob' (the first
        10,000 characters of the document's concatenated paragraph text) and
        'source' (the document's filename). Returns an empty dictionary if the
        file at `docx_path` does not exist.

    Raises:
        docx.opc.exceptions.OpcError: If the file is not a valid or
            uncorrupted .docx file.
    """
    if not docx_path.exists():
        return {}

    doc = docx.Document(docx_path)
    full_text = "\n".join([para.text for para in doc.paragraphs])

    # The current implementation is a deterministic, heuristic-based extractor. Future iterations may integrate a dedicated AI model for more sophisticated and context-aware entity extraction.
    # This heuristic-based extractor serves as a baseline. For more complex scenarios, a specialized Grounding Agent should be implemented to replace this logic.
    return {
        "text_blob": full_text[:10000],  # Generates a representative data sample to facilitate agent-based processing, ensuring the agent has sufficient context.
        "source": docx_path.name,
    }


def get_grounding_agent_prompt(context_text: str) -> str:
    """Generate a Spanish-language prompt to extract technology stack details from the provided text."""
    return f"""
    Eres un ANALISTA DE EXTRACCIÓN DE VERDAD (Grounding). Tu misión es leer el siguiente documento interno de un cliente y extraer las 'VERDADES INMUTABLES' de su stack tecnológico.

    DOCUMENTO INTERNO:
    {context_text}

    EXTRAE ÚNICAMENTE ESTOS CAMPOS EN UN JSON:
    1. 'hyperscaler_dominante': (AWS, Azure, Google Cloud, etc.)
    2. 'erp_principal': (SAP, Oracle, etc.)
    3. 'vendors_criticos': Lista de proveedores mencionados explícitamente como estratégicos.
    4. 'tecnologias_core': Lista de tecnologías clave mencionadas.

    REGLA DE ORO: Si el documento no menciona algo, pon null. No inventes nada.
    """
