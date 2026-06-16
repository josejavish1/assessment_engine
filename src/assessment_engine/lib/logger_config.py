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
    log_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s %(otelTraceID)s %(otelSpanID)s"
    )

    class GCPOpsAgentFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)

            # Formatear la severidad según espera GCP
            if log_record.get("severity"):
                log_record["severity"] = log_record["severity"].upper()

            # Mapeo mágico de OTel a GCP Cloud Trace
            # opentelemetry-instrument inyecta otelTraceID y otelSpanID
            trace_id = log_record.pop("otelTraceID", None)
            span_id = log_record.pop("otelSpanID", None)

            if trace_id and trace_id != "0":
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "UNKNOWN_PROJECT")
                log_record["logging.googleapis.com/trace"] = (
                    f"projects/{project_id}/traces/{trace_id}"
                )
            if span_id and span_id != "0":
                log_record["logging.googleapis.com/spanId"] = span_id

    formatter = GCPOpsAgentFormatter(
        fmt=log_format,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "severity",
            "name": "logger",
        },
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
