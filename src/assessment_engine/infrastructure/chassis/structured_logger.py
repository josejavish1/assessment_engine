"""
Emit deterministic structured JSON logs adhering to RFC 5424.
Ensure immutable injection of trace_id, span_id, and UTC ISO-8601 timestamps.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from assessment_engine.infrastructure.chassis.context import get_current_span_id, get_current_trace_id


class StructuredJsonFormatter(logging.Formatter):
    """
    Formateador de Logging canónico que serializa cada log a JSON estricto en una sola línea.
    No requiere dependencias externas y mantiene latencia de serialización sub-milisegundo.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the specified log record as text."""
        # Extraer traza del contexto activo
        trace_id = getattr(record, "trace_id", None) or get_current_trace_id()
        span_id = getattr(record, "span_id", None) or get_current_span_id()
        latency_ms = getattr(record, "latency_ms", None)

        payload_data: dict[str, Any] = {}
        if hasattr(record, "payload") and isinstance(record.payload, dict):
            payload_data = record.payload
        elif hasattr(record, "extra") and isinstance(record.extra, dict):
            payload_data = record.extra

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "trace_id": trace_id,
            "span_id": span_id,
            "component": record.name,
            "event": record.getMessage(),
        }

        if latency_ms is not None:
            try:
                log_entry["latency_ms"] = round(float(latency_ms), 3)
            except (ValueError, TypeError):
                pass

        if payload_data:
            log_entry["payload"] = payload_data

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """Provide a typed convenience wrapper to emit correlated structured events."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    @property
    def name(self) -> str:
        """Return the name of the logger."""
        return self._logger.name

    def info(self, event: str, *, latency_ms: float | None = None, **kwargs: Any) -> None:
        """Log an event at the INFO level."""
        self._log(logging.INFO, event, latency_ms=latency_ms, **kwargs)

    def warning(self, event: str, *, latency_ms: float | None = None, **kwargs: Any) -> None:
        """Log an event at the WARNING level."""
        self._log(logging.WARNING, event, latency_ms=latency_ms, **kwargs)

    def error(self, event: str, *, exc_info: bool = False, latency_ms: float | None = None, **kwargs: Any) -> None:
        """Log an event at the ERROR level."""
        self._log(logging.ERROR, event, exc_info=exc_info, latency_ms=latency_ms, **kwargs)

    def debug(self, event: str, *, latency_ms: float | None = None, **kwargs: Any) -> None:
        """Log an event at the DEBUG level."""
        self._log(logging.DEBUG, event, latency_ms=latency_ms, **kwargs)

    def _log(
        self,
        level: int,
        event: str,
        *,
        exc_info: bool = False,
        latency_ms: float | None = None,
        **kwargs: Any
    ) -> None:
        if not self._logger.isEnabledFor(level):
            return
        extra: dict[str, Any] = {
            "trace_id": get_current_trace_id(),
            "span_id": get_current_span_id(),
            "latency_ms": latency_ms,
            "payload": kwargs
        }
        self._logger.log(level, event, exc_info=exc_info, extra=extra)


def get_structured_logger(name: str) -> StructuredLogger:
    """Create and configure a StructuredLogger instance."""
    return StructuredLogger(name)


def configure_chassis_logging(level: int = logging.INFO) -> None:
    """Configure the root handler to format all logs as structured JSON."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)
