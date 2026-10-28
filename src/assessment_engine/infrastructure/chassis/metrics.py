"""
Provide an SRE dimensional metrics engine and Prometheus / OpenMetrics exposition (RFC 016 - Phase 2). Implement the four Google SRE Golden Signals (latency, traffic, errors, and saturation)
without heavy external dependencies and with sub-microsecond recording latency.
"""
from __future__ import annotations

import math
import threading
from collections import defaultdict

LATENCY_BUCKETS = (
    0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0, 2.5, 5.0, 10.0
)


RESOURCE_COLLECTIONS = {
    "projects", "users", "jobs", "workspaces", "sessions", "members"
}


def _normalize_path(path: str) -> str:
    """Normalize paths to prevent metric cardinality explosion."""
    if not path or path == "/":
        return "/"
    parts = path.strip("/").split("/")
    normalized: list[str] = []
    for idx, part in enumerate(parts):
        prev = parts[idx - 1] if idx > 0 else ""
        if prev in RESOURCE_COLLECTIONS:
            normalized.append(":id")
        elif part.isdigit() or len(part) >= 24 or (len(part) >= 8 and any(c.isdigit() for c in part) and "-" in part):
            normalized.append(":id")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)


class SREMetricsRegistry:
    """Provide a thread-safe, in-memory unified registry for SRE metrics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

        # Contador de Peticiones: (method, status_group, status_code, path) -> count
        self._http_requests_total: dict[tuple[str, str, int, str], int] = defaultdict(int)

        self._http_duration_buckets: dict[tuple[str, str], list[int]] = defaultdict(
            lambda: [0] * len(LATENCY_BUCKETS)
        )
        self._http_duration_sum: dict[tuple[str, str], float] = defaultdict(float)
        self._http_duration_count: dict[tuple[str, str], int] = defaultdict(int)

        self._recent_latencies: list[float] = []
        self._max_samples = 2000

        # Gauges y SLIs
        self._active_requests: int = 0
        self._sqlite_busy_events: int = 0
        self._concurrency_blocks: int = 0
        self._load_shed_events: int = 0
        self._slo_availability_target: float = 0.999  # 99.9% disponibilidad SLO

    @property
    def active_requests(self) -> int:
        """Return the number of currently active requests."""
        with self._lock:
            return self._active_requests

    def record_request_start(self) -> None:
        """Record the start of a request."""
        with self._lock:
            self._active_requests += 1

    def record_load_shed(self) -> None:
        """Record a preemptive drop event due to extreme saturation (HTTP 503)."""
        with self._lock:
            self._load_shed_events += 1

    def calculate_error_budget(self) -> dict[str, float]:
        """Calculate the error budget and burn rate."""
        with self._lock:
            total_requests = sum(self._http_requests_total.values())
            if total_requests == 0:
                return {
                    "total_requests": 0.0,
                    "error_requests": 0.0,
                    "availability_ratio": 1.0,
                    "budget_remaining_ratio": 1.0,
                    "burn_rate": 0.0,
                }

            error_requests = sum(
                count for (_, _, code, _), count in self._http_requests_total.items() if code >= 500
            )
            availability_ratio = (total_requests - error_requests) / total_requests
            allowed_error_ratio = 1.0 - self._slo_availability_target  # 0.001
            actual_error_ratio = error_requests / total_requests

            remaining_ratio = max(0.0, 1.0 - (actual_error_ratio / allowed_error_ratio)) if allowed_error_ratio > 0 else 0.0
            burn_rate = (actual_error_ratio / allowed_error_ratio) if allowed_error_ratio > 0 else 0.0

            return {
                "total_requests": float(total_requests),
                "error_requests": float(error_requests),
                "availability_ratio": round(availability_ratio, 5),
                "budget_remaining_ratio": round(remaining_ratio, 4),
                "burn_rate": round(burn_rate, 2),
            }

    def record_request_end(
        self,
        method: str,
        status_code: int,
        path: str,
        duration_seconds: float
    ) -> None:
        """Record the completion of a request."""
        norm_path = _normalize_path(path)
        status_group = f"{status_code // 100}xx"

        with self._lock:
            if self._active_requests > 0:
                self._active_requests -= 1

            key_total = (method.upper(), status_group, status_code, norm_path)
            self._http_requests_total[key_total] += 1

            key_hist = (method.upper(), norm_path)
            self._http_duration_sum[key_hist] += duration_seconds
            self._http_duration_count[key_hist] += 1

            buckets = self._http_duration_buckets[key_hist]
            for idx, b_bound in enumerate(LATENCY_BUCKETS):
                if duration_seconds <= b_bound:
                    buckets[idx] += 1

            # Muestra circular
            if len(self._recent_latencies) < self._max_samples:
                self._recent_latencies.append(duration_seconds)
            else:
                self._recent_latencies.pop(0)
                self._recent_latencies.append(duration_seconds)

    def record_sqlite_busy(self) -> None:
        """Record an occurrence of an SQLite busy error."""
        with self._lock:
            self._sqlite_busy_events += 1

    def record_concurrency_block(self) -> None:
        """Record a concurrency blocking event."""
        with self._lock:
            self._concurrency_blocks += 1

    def calculate_percentiles(self) -> dict[str, float]:
        """Calculate P50, P90, P99, and P99.9 from recent samples (in milliseconds)."""
        with self._lock:
            if not self._recent_latencies:
                return {"p50_ms": 0.0, "p90_ms": 0.0, "p99_ms": 0.0, "p999_ms": 0.0}
            sorted_samples = sorted(self._recent_latencies)
            n = len(sorted_samples)

            def get_p(pct: float) -> float:
                """Compute the value at the specified percentile."""
                idx = min(int(math.ceil(pct * n)) - 1, n - 1)
                return round(sorted_samples[max(0, idx)] * 1000.0, 2)

            return {
                "p50_ms": get_p(0.50),
                "p90_ms": get_p(0.90),
                "p99_ms": get_p(0.99),
                "p999_ms": get_p(0.999),
            }

    def generate_prometheus_exposition(self) -> str:
        """Generate the canonical text payload compatible with Prometheus / OpenMetrics."""
        lines: list[str] = []

        with self._lock:
            lines.append("# HELP process_active_requests Numero de peticiones HTTP en vuelo concurrentes.")
            lines.append("# TYPE process_active_requests gauge")
            lines.append(f"process_active_requests {self._active_requests}")

            lines.append("# HELP load_shed_events_total Numero de peticiones descartadas por Adaptive Load Shedding (HTTP 503).")
            lines.append("# TYPE load_shed_events_total counter")
            lines.append(f"load_shed_events_total {self._load_shed_events}")

            budget = self.calculate_error_budget()
            lines.append("# HELP sre_slo_availability_target Objetivo contractual de disponibilidad (SLO).")
            lines.append("# TYPE sre_slo_availability_target gauge")
            lines.append(f"sre_slo_availability_target {self._slo_availability_target}")

            lines.append("# HELP sre_error_budget_remaining_ratio Fraccion restante del presupuesto de error (1.0 = 100%).")
            lines.append("# TYPE sre_error_budget_remaining_ratio gauge")
            lines.append(f"sre_error_budget_remaining_ratio {budget['budget_remaining_ratio']}")

            lines.append("# HELP sre_error_budget_burn_rate Tasa de consumo del presupuesto (1.0 = tasa normal).")
            lines.append("# TYPE sre_error_budget_burn_rate gauge")
            lines.append(f"sre_error_budget_burn_rate {budget['burn_rate']}")

            lines.append("# HELP sqlite_contention_events_total Numero de bloqueos o SQLITE_BUSY detectados.")
            lines.append("# TYPE sqlite_contention_events_total counter")
            lines.append(f"sqlite_contention_events_total {self._sqlite_busy_events}")

            lines.append("# HELP http_requests_total Total de peticiones HTTP procesadas por status y ruta.")
            lines.append("# TYPE http_requests_total counter")
            for (method, status_group, code, path), count in sorted(self._http_requests_total.items()):
                lines.append(
                    f'http_requests_total{{method="{method}",status_group="{status_group}",code="{code}",path="{path}"}} {count}'
                )

            lines.append("# HELP http_request_duration_seconds Histograma de latencia de peticiones HTTP.")
            lines.append("# TYPE http_request_duration_seconds histogram")
            for (method, path), buckets in sorted(self._http_duration_buckets.items()):
                cum_count = 0
                for b_bound, b_count in zip(LATENCY_BUCKETS, buckets):
                    cum_count += b_count
                    lines.append(
                        f'http_request_duration_seconds_bucket{{method="{method}",path="{path}",le="{b_bound}"}} {cum_count}'
                    )
                total_count = self._http_duration_count[(method, path)]
                lines.append(
                    f'http_request_duration_seconds_bucket{{method="{method}",path="{path}",le="+Inf"}} {total_count}'
                )
                total_sum = self._http_duration_sum[(method, path)]
                lines.append(
                    f'http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total_sum:.6f}'
                )
                lines.append(
                    f'http_request_duration_seconds_count{{method="{method}",path="{path}"}} {total_count}'
                )

        lines.append("")  # Append the standard Prometheus trailing newline.
        return "\n".join(lines)


metrics_registry = SREMetricsRegistry()
