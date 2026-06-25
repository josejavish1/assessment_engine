# golden-path: ignore
"""Provides centralized configuration for structured (JSON) logging.

This module configures the standard Python logging library to emit JSON-formatted log records. This enables native parsing and indexing by logging platforms like Google Cloud Logging and supports automatic log-to-trace correlation via specially formatted fields. This approach avoids the need for explicit OpenTelemetry log instrumentation within business logic for standard observability use cases."""

import logging
import logging.config
import os


def setup_structured_logging(level=logging.INFO):
    """Configure the root logger for Google Cloud-compatible structured JSON logging.

    Initializes the root logger to output logs in a structured JSON format
    compatible with Google Cloud Logging. This configuration enriches log
    records with OpenTelemetry trace context, mapping trace and span IDs to
    the specific fields (`logging.googleapis.com/trace`,
    `logging.googleapis.com/spanId`) required by Google Cloud Trace for
    automatic correlation. The full trace name is constructed using the
    `GOOGLE_CLOUD_PROJECT` environment variable.

    This function should be called once at application startup. It removes any
    pre-existing handlers from the root logger to prevent duplicate log
    emissions. To reduce log verbosity, it also sets the logging level for
    noisy third-party libraries (`google`, `urllib3`) to `WARNING`.

    If the `python-json-logger` library is not installed, this function
    configures a basic, non-JSON fallback logger and issues a warning.

    Args:
        level (int, optional): The minimum logging level to be processed by the
            root logger. Defaults to `logging.INFO`.

    Returns:
        None.
    """
    try:
        from pythonjsonlogger import jsonlogger
    except ImportError:
        # Establishes a fallback logging configuration for environments, such as minimal test runners, where the `python-json-logger` dependency is not installed.
        #
        logging.basicConfig(level=level)
        logging.warning("python-json-logger no encontrado. Usando formato estándar.")
        return

    # Defines the standard set of attributes to be included in all structured log records.
    #
    #
    log_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s %(otelTraceID)s %(otelSpanID)s"
    )

    class GCPOpsAgentFormatter(jsonlogger.JsonFormatter):
        """A `jsonlogger.JsonFormatter` subclass that structures log records for native ingestion by the Google Cloud Ops Agent.

        This formatter customizes JSON log output to integrate with Google Cloud's
        operations suite, enabling structured logging and automatic trace correlation.
        It applies the following transformations to each log record:

        1.  The `severity` field is set to its uppercase string representation to
            match the `LogSeverity` enumeration used by Google Cloud Logging.
        2.  OpenTelemetry trace context (`otelTraceID`, `otelSpanID`), if present,
            is mapped to the `logging.googleapis.com/trace` and
            `logging.googleapis.com/spanId` fields. This mapping allows Google Cloud
            Trace to link log entries to specific trace spans automatically.

        The full trace resource name is constructed using the `GOOGLE_CLOUD_PROJECT`
        environment variable. If this variable is not set, a placeholder project ID
        is used in the trace name.
        """

        def add_fields(self, log_record, record, message_dict):
            """Enrich a log record with Google Cloud Logging and Trace correlation fields.

            This method extends the base formatter to automatically add structured data
            required by Google Cloud's operations suite. It performs two key
            transformations:

            1.  Severity Normalization: Converts the `severity` field to uppercase
                (e.g., "info" to "INFO") to match the canonical `LogSeverity`
                enumeration used by Google Cloud Logging.
            2.  Trace Correlation: Maps OpenTelemetry trace context fields, which are
                assumed to be injected into the log record, to the specific keys
                that Google Cloud uses for automatic log-to-trace correlation. It
                constructs the full trace resource name from the `otelTraceID` and
                the `GOOGLE_CLOUD_PROJECT` environment variable.

            Specifically, it maps:
            - `otelTraceID` -> `logging.googleapis.com/trace` (formatted as
              `projects/PROJECT_ID/traces/TRACE_ID`)
            - `otelSpanID` -> `logging.googleapis.com/spanId`

            The original `otelTraceID` and `otelSpanID` fields are removed from the
            final log record.

            Args:
                log_record (dict): The log record dictionary to be enriched. This
                    dictionary is modified in-place.
                record (logging.LogRecord): The original `logging.LogRecord` object from
                    Python's logging module.
                message_dict (dict): The dictionary containing the pre-formatted log
                    message.
            """
            super().add_fields(log_record, record, message_dict)

            # Formats the log level to align with the canonical `severity` enumeration required by Google Cloud Logging.
            if log_record.get("severity"):
                log_record["severity"] = log_record["severity"].upper()

            # Maps OpenTelemetry context fields to the specific `logging.googleapis.com/` keys required by Google Cloud Trace for automatic correlation.
            # Note: The `opentelemetry-instrument` agent automatically injects `otelTraceID` and `otelSpanID` from the active trace context into log records.
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

    # Ensures a clean configuration by removing any pre-existing handlers from the root logger, which prevents duplicate log emission.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(log_handler)
    root_logger.setLevel(level)

    # Adjusts log levels for verbose third-party libraries to reduce log volume.
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.debug("Structured JSON logging initialized successfully")
