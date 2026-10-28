"""
Chasis de Servicio Unificado Tier-1 (Observabilidad, Trazabilidad W3C y Fiabilidad).
"""
from assessment_engine.infrastructure.chassis.context import (
    TraceContext,
    get_current_span_id,
    get_current_trace_context,
    get_current_trace_id,
    parse_w3c_traceparent,
    set_current_trace_context,
)
from assessment_engine.infrastructure.chassis.lifecycle import ProcessLifecycleManager, lifecycle_manager
from assessment_engine.infrastructure.chassis.metrics import SREMetricsRegistry, metrics_registry
from assessment_engine.infrastructure.chassis.middleware import TelemetryMiddleware
from assessment_engine.infrastructure.chassis.structured_logger import (
    StructuredJsonFormatter,
    StructuredLogger,
    configure_chassis_logging,
    get_structured_logger,
)

__all__ = [
    "TraceContext",
    "parse_w3c_traceparent",
    "get_current_trace_context",
    "set_current_trace_context",
    "get_current_trace_id",
    "get_current_span_id",
    "StructuredJsonFormatter",
    "StructuredLogger",
    "get_structured_logger",
    "configure_chassis_logging",
    "TelemetryMiddleware",
    "metrics_registry",
    "SREMetricsRegistry",
    "ProcessLifecycleManager",
    "lifecycle_manager",
]
