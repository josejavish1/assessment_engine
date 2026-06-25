from typing import Any

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


def setup_structured_logging(level=logging.INFO) -> Any:
    """Configures the root logger for Google Cloud-compatible structured JSON logging.

    This function reconfigures the global root logger to output log records as
    JSON strings formatted for consumption by Google Cloud Logging. It clears all
    pre-existing handlers on the root logger to prevent log duplication and adds a
    new `StreamHandler` directed to standard output.

    The JSON formatter performs several key transformations:
    - Renames the `levelname` field to `severity` and converts its value to
      uppercase (e.g., 'INFO') to align with Google Cloud's `LogSeverity` enum.
    - Detects OpenTelemetry trace context (`otelTraceID`, `otelSpanID`) on the log
      record and maps it to the `logging.googleapis.com/trace` and
      `logging.googleapis.com/spanId` fields. The full trace resource name is
      constructed using the `GOOGLE_CLOUD_PROJECT` environment variable. This
      enables automatic log correlation in Google Cloud Trace.

    If the `python-json-logger` library is not installed, this function falls
    back to a standard, non-JSON `logging.basicConfig` configuration and issues
    a warning.

    Additionally, this function sets the log level for noisy third-party
    libraries like 'google' and 'urllib3' to `WARNING` to reduce log volume.

    Args:
        level (int): The minimum logging level to set for the root logger.
            Defaults to `logging.INFO`.

    Returns:
        None. The function modifies the global logging configuration in place.
    """
    try:
        from pythonjsonlogger import jsonlogger
    except ImportError:
        # Provides a fallback processor for environments where the `opentelemetry-api` package is not installed.
        # This is necessary for local testing or in environments where OpenTelemetry is not configured or instrumentation is disabled.
        logging.basicConfig(level=level)
        logging.warning("python-json-logger no encontrado. Usando formato estándar.")
        return

    # Defines the standard field set to be included in every structured log record, establishing a consistent log schema.
    # In a properly instrumented environment, the `opentelemetry-instrument` agent automatically injects OpenTelemetry context.
    # ...which enriches log records with trace context fields like `otelTraceID` and `otelSpanID`.
    log_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s %(otelTraceID)s %(otelSpanID)s"
    )

    class GCPOpsAgentFormatter(jsonlogger.JsonFormatter):
        r"""{'docstring': "Enrich a log record with Google Cloud-specific observability fields.\n\nExtends the base formatter's `add_fields` method to inject fields\nspecifically recognized by Google Cloud's operations suite (Cloud Logging\nand Cloud Trace). The `log_record` dictionary is modified in-place.\n\nKey transformations include:\n1.  **Severity Normalization**: The `severity` field is converted to its\n    uppercase string representation (e.g., 'info' -> 'INFO') to align\n    with the canonical `LogSeverity` enumeration required by Cloud Logging.\n2.  **Trace Correlation**: OpenTelemetry trace context attributes (`otelTraceID`,\n    `otelSpanID`) are mapped to the `logging.googleapis.com/trace` and\n    `logging.googleapis.com/spanId` fields. The full trace resource name is\n    constructed using the `GOOGLE_CLOUD_PROJECT` environment variable,\n    enabling automatic correlation of logs with traces in Cloud Trace.\n\nArgs:\n    log_record (dict): The log record dictionary to be modified in-place.\n    record (logging.LogRecord): The original `LogRecord` instance from the\n        Python logging framework.\n    message_dict (dict): A dictionary containing the formatted log message\n        and any extra fields."}."""
        def add_fields(self, log_record, record, message_dict):
            """Enriches a log record with fields for integration with Google Cloud Logging.

            This method overrides the base formatter's `add_fields` to inject
            structured data fields specifically recognized by Google Cloud's operations
            suite. The log record dictionary is modified in-place.

            The method performs two primary transformations:
            1.  Normalizes the `severity` field to its uppercase equivalent (e.g.,
                'info' becomes 'INFO') to match the canonical `LogSeverity` enum
                required by Google Cloud Logging for proper display and filtering.
            2.  Integrates OpenTelemetry trace context by mapping `otelTraceID` and
                `otelSpanID` to the `logging.googleapis.com/trace` and
                `logging.googleapis.com/spanId` fields, respectively. This enables
                automatic correlation of logs with traces in Google Cloud Trace.
                The project ID for the trace name is sourced from the
                `GOOGLE_CLOUD_PROJECT` environment variable. The original `otelTraceID`
                and `otelSpanID` fields are removed after processing.

            Args:
                log_record (dict): The log record dictionary to be modified.
                record (logging.LogRecord): The original `LogRecord` instance from the
                    logging framework.
                message_dict (dict): A dictionary containing the formatted log message
                    and any extra fields passed to the logger.
            """
            super().add_fields(log_record, record, message_dict)

            # Maps standard Python log level names to the canonical `LogSeverity` enumeration values required by Google Cloud Logging for proper severity filtering and display.
            if log_record.get("severity"):
                log_record["severity"] = log_record["severity"].upper()

            # Maps OpenTelemetry trace context attributes to the specific field names required by Google Cloud Trace for automatic log-to-trace correlation.
            # The OpenTelemetry instrumentation agent is responsible for injecting trace context fields, e.g., `otelTraceID` and `otelSpanID`.
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

    # Clears all pre-existing handlers from the root logger to prevent log duplication, which can occur if other modules or libraries have already configured handlers.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(log_handler)
    root_logger.setLevel(level)

    # Sets specific, less verbose log levels for chatty third-party libraries to reduce noise.
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.debug("Structured JSON logging initialized successfully")
