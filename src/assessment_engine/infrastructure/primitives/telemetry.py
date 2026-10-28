"""
Canonical Telemetry, SRE & Observability Engine — System 14 (OpenMetrics / SRE SOTA 2026).
Consolidated observability and platform reliability suite:
1. OpenMetrics / Prometheus exporter (/metrics endpoint) for request latency and errors.
2. Privacy-first, zero-cookie client analytics stored in SQLite WAL.
3. SRE physical health probes (/healthz & /readyz) with real WAL I/O latency measurement.
4. Client-side crash beacon and structured error capture.
5. AWS Architecture Full Jitter exponential backoff retry calculator.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.openmetrics_exporter import OpenMetricsExporterPrimitive, openmetrics_exporter
from assessment_engine.infrastructure.primitives.zero_cookie_analytics import (
    ZeroCookieAnalyticsPrimitive,
    zero_cookie_analytics
)
from assessment_engine.infrastructure.primitives.health_probes import (
    HealthProbesPrimitive,
    HealthProbesIntegrator,
    health_probes
)
from assessment_engine.infrastructure.primitives.telemetry_beacon import TelemetryBeaconPrimitive, telemetry_beacon
from assessment_engine.infrastructure.primitives.exponential_backoff_jitter import (
    ExponentialBackoffJitterPrimitive,
    exponential_backoff_jitter
)

telemetry_engine = openmetrics_exporter
health_suite = health_probes
