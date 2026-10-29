"""
Trace Conditioner — W3C telemetry-conditioned synthesis.
Convert W3C trace execution trees (spans, latencies, bottlenecks)
into deterministic prescriptive diagnostics for the Cognitive Synthesizer.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from assessment_engine.infrastructure.chassis.metrics import metrics_registry

logger = logging.getLogger("assessment_engine.infrastructure.evolution.trace_conditioner")


@dataclass(frozen=True)
class TraceBottleneckSpan:
    """Sub-span responsible for latency degradation."""
    span_id: str
    component: str
    operation: str
    duration_ms: float
    percentage_of_total: float
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance into a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class TraceDiagnosticReport:
    """W3C telemetry forensic report injectable into the surgical ticket."""
    trace_id: str
    total_latency_ms: float
    budget_latency_ms: float
    is_budget_exceeded: bool
    burn_rate: float
    bottlenecks: tuple[TraceBottleneckSpan, ...] = field(default_factory=tuple)
    prescriptive_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance into a dictionary."""
        return {
            "trace_id": self.trace_id,
            "total_latency_ms": self.total_latency_ms,
            "budget_latency_ms": self.budget_latency_ms,
            "is_budget_exceeded": self.is_budget_exceeded,
            "burn_rate": self.burn_rate,
            "prescriptive_hint": self.prescriptive_hint,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
        }

    def to_prompt_markdown(self) -> str:
        """Format the telemetry diagnostic for the Synthesizer prompt."""
        if not self.is_budget_exceeded and not self.bottlenecks:
            return ""

        md_lines = [
            f"### ⏱️ W3C FORENSIC TELEMETRY DIAGNOSIS (Trace ID: `{self.trace_id}`)",
            f"- **Measured Total Latency:** {self.total_latency_ms:.2f} ms (Budget Limit: {self.budget_latency_ms:.2f} ms)",
            f"- **Burn-Rate del Error Budget:** {self.burn_rate:.2f}x de consumo",
            f"- **Prescriptive Remediation:** {self.prescriptive_hint}",
        ]
        if self.bottlenecks:
            md_lines.append("- **Cuellos de Botella Detectados:**")
            for b in self.bottlenecks:
                md_lines.append(
                    f"  * `{b.component}::{b.operation}`: {b.duration_ms:.2f} ms ({b.percentage_of_total:.1f}% del tiempo total) -> {b.recommendation}"
                )
        return "\n".join(md_lines)


class TraceConditioner:
    """W3C trace analysis and conditioning engine for meta-intelligence."""

    @staticmethod
    def analyze_trace_profile(
        trace_id: str,
        total_latency_ms: float,
        budget_latency_ms: float = 100.0,
        spans_breakdown: Optional[list[dict[str, Any]]] = None,
    ) -> TraceDiagnosticReport:
        """Analyze the W3C trace and deterministically extract the bottleneck."""
        budget_metrics = metrics_registry.calculate_error_budget()
        burn_rate = budget_metrics.get("burn_rate", 0.0)
        is_exceeded = total_latency_ms > budget_latency_ms

        bottlenecks_list: list[TraceBottleneckSpan] = []
        hint = "Performance within acceptable SRE thresholds."

        if spans_breakdown:
            for s in spans_breakdown:
                dur = float(s.get("duration_ms", 0.0))
                pct = (dur / max(0.001, total_latency_ms)) * 100.0
                comp = str(s.get("component", "unknown"))
                op = str(s.get("operation", "compute"))

                recom = "Optimizar algoritmo o aislar I/O"
                if comp in ("database", "sqlite", "db"):
                    recom = "Inject B-Tree composite index or use Keyset O(1) pagination."
                elif comp in ("network", "http", "api"):
                    recom = "Configure strict timeout or implement Circuit Breaker with SWR cache."
                elif comp in ("json", "serialization"):
                    recom = "Use fast serializer or reduce payload size."

                if pct >= 30.0 or dur > 50.0:
                    bottlenecks_list.append(TraceBottleneckSpan(
                        span_id=str(s.get("span_id", "span-0")),
                        component=comp,
                        operation=op,
                        duration_ms=round(dur, 2),
                        percentage_of_total=round(pct, 1),
                        recommendation=recom
                    ))

        if is_exceeded:
            if bottlenecks_list:
                slowest = max(bottlenecks_list, key=lambda x: x.duration_ms)
                hint = f"Saturation in '{slowest.component}::{slowest.operation}' ({slowest.duration_ms}ms). {slowest.recommendation}"
            else:
                hint = f"Total latency ({total_latency_ms:.1f}ms) exceeded budget ({budget_latency_ms:.1f}ms). Offload synchronous I/O to worker thread."

        return TraceDiagnosticReport(
            trace_id=trace_id,
            total_latency_ms=round(total_latency_ms, 2),
            budget_latency_ms=round(budget_latency_ms, 2),
            is_budget_exceeded=is_exceeded,
            burn_rate=round(burn_rate, 2),
            bottlenecks=tuple(bottlenecks_list),
            prescriptive_hint=hint,
        )


trace_conditioner = TraceConditioner()
