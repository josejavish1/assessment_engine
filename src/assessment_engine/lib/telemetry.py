# golden-path: ignore
"""
Core Telemetry Module (OpenTelemetry)

Este módulo centraliza la inicialización y configuración de OpenTelemetry
para el proyecto assessment_engine. 

Exporta un `tracer` y un `meter` que DEBEN ser utilizados por todos los 
componentes (endpoints, workers, etc.) creados a través de los Golden Paths.
"""

import logging
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

def setup_telemetry(service_name: str = "assessment_engine") -> None:
    """
    Inicializa los proveedores globales de OpenTelemetry.
    Debe ser llamado lo antes posible en el ciclo de vida de la aplicación.
    """
    try:
        # Define the resource identifying this service
        resource = Resource.create({"service.name": service_name})

        # --- TRACING SETUP ---
        tracer_provider = TracerProvider(resource=resource)
        
        # En entornos locales/desarrollo, exportamos a consola.
        # TODO: En producción, añadir el exportador de GCP: 
        # from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        # tracer_provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
        
        if os.environ.get("ENVIRONMENT", "local").lower() == "local":
            tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            
        trace.set_tracer_provider(tracer_provider)

        # --- METRICS SETUP ---
        meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(meter_provider)
        
        logger.debug(f"OpenTelemetry configurado correctamente para servicio: {service_name}")
        
    except Exception as e:
        # La telemetría no debe romper la aplicación si falla su inicialización
        logger.error(f"Fallo al inicializar OpenTelemetry: {e}", exc_info=True)

# Exportamos el tracer y el meter globales para que puedan ser
# importados directamente desde los Golden Paths.
tracer = trace.get_tracer("assessment_engine.tracer")
meter = metrics.get_meter("assessment_engine.meter")
