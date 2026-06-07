from pathlib import Path
from typing import Any, Dict

import docx


def extract_core_grounding(docx_path: Path) -> Dict[str, Any]:
    """Extrae entidades críticas del documento de contexto para actuar como anclas de verdad."""
    if not docx_path.exists():
        return {}

    doc = docx.Document(docx_path)
    full_text = "\n".join([para.text for para in doc.paragraphs])

    # Este es un extractor determinista/heurístico inicial que se puede potenciar con IA
    # Pero para un equipo de élite, usamos un Agente de Grounding específico.
    return {
        "text_blob": full_text[:10000],  # Muestra para el agente
        "source": docx_path.name,
    }


def get_grounding_agent_prompt(context_text: str) -> str:
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
