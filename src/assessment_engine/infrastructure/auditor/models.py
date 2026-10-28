"""
Provide data models and safe traversal utilities for Soverik Quality Engine.
Standardize reports, findings, certificates, and ephemeral directory pruning.
"""
from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive", "workspaces", "credentials",
    "working", ".evolution", "tmp", ".next"
}

EXCLUDE_FILES = {
    ".env", ".env.local", ".env.production", ".env.test", ".env.development"
}


def find_target_files(target_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Walk the directory tree safely, pruning excluded top-level directories and env files."""
    found: list[Path] = []
    for root, dirs, files in os.walk(str(target_dir), topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f in EXCLUDE_FILES or f.startswith(".env"):
                continue
            if any(f.endswith(ext) for ext in extensions):
                found.append(Path(root) / f)
    return found


@dataclass
class AuditFinding:
    """Represent a vulnerability, defect, or deviation detected in the code."""
    category: str  # "SECURITY", "COMPLEXITY", "MUTATION", "SUPPLY_CHAIN", "RGPD", "PERFORMANCE", "ACCESSIBILITY", "CONTRACT_DRIFT", "RESILIENCE", "AI_SAFETY", "CODE_HYGIENE", "STRUCTURAL_SMELL"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    file_path: str
    line_number: int | None
    rule_id: str
    message: str
    recommendation: str


@dataclass
class ProbeResult:
    """Represent the result emitted by an individual audit probe."""
    probe_name: str
    score_pct: float  # 0.0 a 100.0
    passed: bool
    metrics: dict[str, Any]
    findings: list[AuditFinding] = field(default_factory=list)


@dataclass
class UniversalAuditReport:
    """Represent the consolidated software certification report for a project."""
    project_name: str
    target_path: str
    timestamp: int = field(default_factory=lambda: int(time.time()))
    global_grade: str = "A"  # "A+", "A", "B", "C", "F"
    global_score: float = 100.0  # 0.0 a 100.0
    probes: dict[str, ProbeResult] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete report to a clean JSON dictionary."""
        return asdict(self)
