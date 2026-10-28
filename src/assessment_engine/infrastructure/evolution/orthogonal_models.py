"""
Define data models and reports for orthogonal gates. Decoupled from orthogonal_gates.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from assessment_engine.infrastructure.evolution.closure_tribunal import SurgicalCorrectionTicket


@dataclass(frozen=True)
class GateResult:
    """Represent the deterministic result of an individual gate evaluation."""
    gate_name: str
    passed: bool
    failure_signature: str | None = None
    prescriptive_action: str | None = None
    metric_value: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class OrthogonalAuditReport:
    """Represent the canonical evaluation report for the four orthogonal gates."""
    passed: bool
    gates: dict[str, GateResult]
    failed_gate: GateResult | None = None
    yagni_score: float = 1.0
    summary: str = ""
    surgical_ticket: SurgicalCorrectionTicket | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "passed": self.passed,
            "failed_gate": self.failed_gate.to_dict() if self.failed_gate else None,
            "yagni_score": self.yagni_score,
            "summary": self.summary,
            "gates": {k: v.to_dict() for k, v in self.gates.items()},
            "surgical_ticket": self.surgical_ticket.to_dict() if self.surgical_ticket else None,
        }
