"""
Golden Path: FastAPI Endpoint Template
Description: Plantilla base para nuevos endpoints en assessment_engine.
Usage: Usar como esqueleto SIEMPRE que se requiera crear una nueva ruta de API.

Reglas Arquitectónicas:
1. Siempre usar dependencias inyectadas para la lógica de base de datos/servicios.
2. Todo el código de negocio debe ir dentro del bloque 'Business Logic'.
3. Devolver siempre modelos Pydantic validados o Raise HTTPException.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict

from assessment_engine.lib.telemetry import tracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/resource", tags=["Resource"])

class ResourceRequest(BaseModel):
    """Esquema de entrada."""
    data: str

class ResourceResponse(BaseModel):
    """Esquema de salida."""
    status: str
    result: Dict[str, Any]

@tracer.start_as_current_span("endpoint.create_resource")
@router.post("/", response_model=ResourceResponse)
async def create_resource(request: ResourceRequest):
    """
    Crea un nuevo recurso.
    """
    logger.info("Recibida petición para crear recurso: %s", request.data)
    
    try:
        # --- START OF BUSINESS LOGIC ---
        # El agente debe insertar la lógica de negocio específica aquí.
        
        processed_result = {"input": request.data, "action": "processed"}
        
        # --- END OF BUSINESS LOGIC ---
        
        logger.info("Recurso procesado con éxito.")
        return ResourceResponse(status="success", result=processed_result)
        
    except ValueError as ve:
        logger.warning("Error de validación en el negocio: %s", str(ve))
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Error interno al procesar el recurso: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
