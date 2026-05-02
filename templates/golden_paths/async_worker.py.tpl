"""
Golden Path: Python Worker / Service Template
Description: Plantilla base para servicios o workers asíncronos en assessment_engine.
Usage: Usar como esqueleto SIEMPRE que se requiera crear un nuevo servicio o tarea asíncrona.

Reglas Arquitectónicas:
1. No alterar la estructura de logging.
2. Todo el código de negocio debe ir dentro del bloque 'Business Logic'.
3. Las excepciones deben ser capturadas y propagadas ordenadamente.
"""
import logging
import asyncio
from typing import Any, Dict

from assessment_engine.lib.telemetry import tracer

logger = logging.getLogger(__name__)

class WorkerService:
    """
    Servicio worker base para ejecución de tareas.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.debug("WorkerService inicializado con config: %s", config)

    @tracer.start_as_current_span("WorkerService.execute")
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la lógica de negocio del worker.
        """
        logger.info("Iniciando ejecución del worker con payload: %s", payload)
        
        try:
            # --- START OF BUSINESS LOGIC ---
            # El agente debe insertar la lógica de negocio específica aquí.
            
            result = {"status": "success", "processed_data": payload}
            
            # --- END OF BUSINESS LOGIC ---
            
            logger.info("Ejecución completada con éxito.")
            return result
            
        except Exception as e:
            logger.error("Fallo inesperado durante la ejecución del worker: %s", str(e), exc_info=True)
            # Propagar el error de forma controlada o manejarlo según las políticas de reintento
            raise

async def main():
    """Punto de entrada de prueba/ejecución."""
    service = WorkerService(config={})
    await service.execute(payload={"test": "data"})

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
