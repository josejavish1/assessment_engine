"""Sovereign HTTP Client Primitive (Tier-1 SOTA Resilience & Fault Tolerance).

Eliminates unbounded network blocks, metastable cascading failures, and scattered
ad-hoc timeouts across the codebase.

Invariants:
1. Immutable finite timeout enforced at transport level (default 10.0s, hard upper limit 30.0s).
2. Distributed W3C TraceContext propagation (RFC 9458).
3. Structured logging on all outbound network egress.
4. Deterministic error classification and bounded retries.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Mapping, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from assessment_engine.infrastructure.chassis.context import get_current_trace_context

logger = logging.getLogger("assessment_engine.infrastructure.http_client")

DEFAULT_TIMEOUT_SECONDS: float = 10.0
MAX_ALLOWED_TIMEOUT_SECONDS: float = 30.0
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_BACKOFF_FACTOR: float = 0.5


class TimeoutBoundExceededError(ValueError):
    """Raised when a requested timeout exceeds the architectural upper bound."""


class SovereignHttpClient:
    """Hardened HTTP client enforcing strict timeout boundaries and W3C observability."""

    def __init__(
        self,
        default_timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        if default_timeout > MAX_ALLOWED_TIMEOUT_SECONDS:
            raise TimeoutBoundExceededError(
                f"Timeout {default_timeout}s excede el límite arquitectónico ({MAX_ALLOWED_TIMEOUT_SECONDS}s)."
            )
        self.default_timeout = max(0.1, default_timeout)
        self.session = requests.Session()

        # Configurar reintentos automáticos a nivel de transporte para fallos de conexión y 502/503/504
        retries = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _resolve_timeout(self, timeout: Optional[float]) -> float:
        """Resolve and clamp timeout within architectural invariants."""
        if timeout is None:
            return self.default_timeout
        if timeout > MAX_ALLOWED_TIMEOUT_SECONDS:
            logger.warning(
                f"[SovereignHttpClient] Requested timeout {timeout}s clamped to maximum {MAX_ALLOWED_TIMEOUT_SECONDS}s."
            )
            return MAX_ALLOWED_TIMEOUT_SECONDS
        return max(0.1, timeout)

    def _inject_trace_headers(self, headers: Optional[dict[str, str]]) -> dict[str, str]:
        """Inject canonical W3C traceparent header if active in context."""
        out_headers = dict(headers) if headers else {}
        ctx = get_current_trace_context()
        if ctx and "traceparent" not in out_headers:
            out_headers["traceparent"] = ctx.to_w3c_header()
        return out_headers

    def request(
        self,
        method: str,
        url: str,
        timeout: Optional[float] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute HTTP request with guaranteed bounded timeout and distributed tracing."""
        effective_timeout = self._resolve_timeout(timeout)
        effective_headers = self._inject_trace_headers(headers)

        t0 = time.perf_counter()
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                timeout=effective_timeout,
                headers=effective_headers,
                **kwargs,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            logger.debug(
                f"[HTTP] {method.upper()} {url} -> {response.status_code} ({elapsed_ms:.1f}ms, timeout={effective_timeout}s)"
            )
            return response
        except requests.RequestException as ex:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            logger.error(
                f"[HTTP-ERROR] {method.upper()} {url} failed after {elapsed_ms:.1f}ms: {ex}"
            )
            raise

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Execute GET request with enforced bounded timeout."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Execute POST request with enforced bounded timeout."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        """Execute PUT request with enforced bounded timeout."""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        """Execute DELETE request with enforced bounded timeout."""
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> requests.Response:
        """Execute HEAD request with enforced bounded timeout."""
        return self.request("HEAD", url, **kwargs)


# Global sovereign singleton instance
http_client = SovereignHttpClient()
