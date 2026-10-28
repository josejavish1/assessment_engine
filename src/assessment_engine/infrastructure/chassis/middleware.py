"""
Provide W3C Trace Context telemetry and monotonic latency tracking for Starlette and FastAPI.
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from assessment_engine.infrastructure.chassis.context import (
    TraceContext,
    parse_w3c_traceparent,
    set_current_trace_context,
)
from assessment_engine.infrastructure.chassis.metrics import metrics_registry
from assessment_engine.infrastructure.chassis.structured_logger import get_structured_logger

logger = get_structured_logger("telemetry_middleware")


class TelemetryMiddleware:
    """
    Middleware ASGI nativo de ultra-baja latencia con Adaptive Load Shedding.
    - Extrae o genera W3C traceparent y asigna trace_id inmutable.
    - Mide latencia con time.perf_counter_ns() sin desvíos de reloj.
    - Aplica Adaptive Load Shedding ante saturación extrema (descarta con HTTP 503).
    - Inyecta cabeceras 'X-Trace-Id', 'Server-Timing' y 'traceparent' en la respuesta.
    - Emite log estructurado JSON al finalizar cada ciclo de petición.
    """

    def __init__(self, app: Any, max_concurrent_requests: int = 150) -> None:
        self.app = app
        self.max_concurrent_requests = max_concurrent_requests

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_traceparent = headers.get(b"traceparent")
        traceparent_str = raw_traceparent.decode("latin1", errors="ignore") if raw_traceparent else None

        ctx = parse_w3c_traceparent(traceparent_str)
        if ctx is None:
            ctx = TraceContext.generate_new()

        token = set_current_trace_context(ctx)
        metrics_registry.record_request_start()
        start_ns = time.perf_counter_ns()
        status_code = 500
        path = scope.get("path", "/")

        # 3. Adaptive Load Shedding: Drop requests preemptively under extreme saturation.
        is_critical = path.startswith(("/livez", "/readyz", "/startupz", "/metrics"))
        if not is_critical and metrics_registry.active_requests > self.max_concurrent_requests:
            metrics_registry.record_load_shed()
            end_ns = time.perf_counter_ns()
            duration_s = (end_ns - start_ns) / 1_000_000_000.0
            latency_ms = duration_s * 1000.0

            logger.warning(
                "adaptive_load_shed_rejected",
                path=path,
                active_requests=metrics_registry.active_requests,
                limit=self.max_concurrent_requests,
                latency_ms=latency_ms
            )

            metrics_registry.record_request_end(
                method=scope.get("method", "GET"),
                status_code=503,
                path=path,
                duration_seconds=duration_s
            )

            body_bytes = b'{"error":"LOAD_SHEDDING","detail":"Server saturation limit reached. Adaptive backpressure active. Retry after 2 seconds."}'
            resp_headers = [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body_bytes)).encode("ascii")),
                (b"retry-after", b"2"),
                (b"x-load-shed", b"true"),
                (b"x-trace-id", ctx.trace_id.encode("ascii")),
                (b"traceparent", ctx.to_w3c_header().encode("ascii")),
                (b"server-timing", f"app;dur={latency_ms:.2f}".encode("ascii")),
            ]

            await send({
                "type": "http.response.start",
                "status": 503,
                "headers": resp_headers,
            })
            await send({
                "type": "http.response.body",
                "body": body_bytes,
            })
            set_current_trace_context(None)
            return

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                end_ns = time.perf_counter_ns()
                latency_ms = (end_ns - start_ns) / 1_000_000.0

                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-trace-id", ctx.trace_id.encode("ascii")))
                resp_headers.append((b"traceparent", ctx.to_w3c_header().encode("ascii")))
                resp_headers.append((b"server-timing", f"app;dur={latency_ms:.2f}".encode("ascii")))
                message["headers"] = resp_headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as exc:
            end_ns = time.perf_counter_ns()
            latency_ms = (end_ns - start_ns) / 1_000_000.0
            logger.error(
                "unhandled_request_exception",
                exc_info=True,
                latency_ms=latency_ms,
                method=scope.get("method"),
                path=scope.get("path"),
                error_type=type(exc).__name__,
                error_detail=str(exc)
            )
            raise exc
        finally:
            end_ns = time.perf_counter_ns()
            duration_seconds = (end_ns - start_ns) / 1_000_000_000.0
            latency_ms = duration_seconds * 1000.0
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")

            metrics_registry.record_request_end(
                method=method,
                status_code=status_code,
                path=path,
                duration_seconds=duration_seconds
            )

            if not path.startswith(("/static", "/favicon.ico", "/metrics")):
                logger.info(
                    "http_request_finished",
                    latency_ms=latency_ms,
                    method=method,
                    path=path,
                    status_code=status_code
                )

            set_current_trace_context(None)
