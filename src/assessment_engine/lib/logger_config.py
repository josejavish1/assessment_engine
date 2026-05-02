# golden-path: ignore
"""
Configuración centralizada de Logging Estructurado (JSON)

Este módulo configura la librería estándar de logging para que 
escupa logs en formato JSON. Esta es la base para la observabilidad
"Zero-Code" en entornos como Google Cloud Ops Agent, ya que permite
la correlación automática con trazas (ej. trace_id) y la indexación nativa
sin requerir librerías de OpenTelemetry en el código de negocio.
"""

import logging
import logging.config
import os

def setup_structured_logging(level=logging.INFO):
    """
    Configura el logger raíz para usar formato JSON.
    Debe llamarse al inicio de la aplicación o worker.
    """
    try:
        from pythonjsonlogger import jsonlogger
    except ImportError:
        # Fallback en caso de que la librería no esté instalada,
        # útil para tests o entornos no configurados.
        logging.basicConfig(level=level)
        logging.warning("python-json-logger no encontrado. Usando formato estándar.")
        return

    # Definimos los campos estándar que queremos en cada log
    # Cuando opentelemetry-instrument arranca la app, inyectará automáticamente
    # asnc context como `otelTraceID` y `otelSpanID` en estos logs.
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    
    formatter = jsonlogger.JsonFormatter(
        fmt=log_format,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "severity",
            "name": "logger"
        }
    )

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    
    # Limpiamos handlers previos para evitar duplicados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    root_logger.addHandler(log_handler)
    root_logger.setLevel(level)

    # Configuramos niveles específicos para librerías ruidosas
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.debug("Structured JSON logging initialized successfully")
