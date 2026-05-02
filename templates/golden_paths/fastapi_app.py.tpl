# golden-path: ignore
"""
Golden Path: FastAPI Main App Template
Description: Plantilla base para la aplicación principal (entrypoint) de FastAPI.
Usage: Usar como esqueleto principal para arrancar el servidor web.

Reglas Arquitectónicas:
1. Inicializar siempre el logger estructurado (JSON) al inicio.
2. Incluir el middleware de manejo de errores globales si aplica.
3. Importar y añadir los routers (endpoints) modulares.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from assessment_engine.lib.logger_config import setup_structured_logging
# TODO: Importar tus routers aquí
# from assessment_engine.api.v1 import resource_router

# Inicializar logger estructurado para que Ops Agent procese el formato JSON
setup_structured_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Lógica de arranque ---
    logger.info("Iniciando aplicación FastAPI")
    yield
    # --- Lógica de apagado ---
    logger.info("Apagando aplicación FastAPI")

app = FastAPI(
    title="Assessment Engine API",
    version="1.0.0",
    lifespan=lifespan
)

# TODO: Añadir los routers
# app.include_router(resource_router.router)

@app.get("/health")
async def health_check():
    """Endpoint básico para healthchecks (ej. Cloud Run o Load Balancers)."""
    return {"status": "healthy"}
