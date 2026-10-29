from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class AssessmentContext(BaseModel):
    """Unified in-memory domain context container for a tower assessment lifecycle.

    Replaces intermediate file polling and disk IPC by maintaining the full state
    in RAM, while offering seamless checkpointing for regulatory audit (SR 11-7).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    client_name: str
    tower_id: str
    case_dir: Optional[Path] = None
    industry: str = "default"
    language: str = "en"
    currency: str = "€"

    # In-Memory Pipeline State
    case_input: Optional[Dict[str, Any]] = None
    evidence_ledger: Optional[List[Dict[str, Any]]] = None
    scoring_output: Optional[Dict[str, Any]] = None
    findings: Optional[Dict[str, Any]] = None
    blueprint_payload: Optional[Dict[str, Any]] = None
    annex_payload: Optional[Dict[str, Any]] = None
    commercial_payload: Optional[Dict[str, Any]] = None

    # Telemetry and Execution Stages
    completed_stages: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_stage_done(self, stage_name: str) -> None:
        """Registers a stage as successfully completed in memory."""
        if stage_name not in self.completed_stages:
            self.completed_stages.append(stage_name)

    def has_stage(self, stage_name: str) -> bool:
        """Checks if a stage has been completed in memory."""
        return stage_name in self.completed_stages

    def checkpoint_to_disk(self, target_dir: Optional[Path] = None) -> None:
        """Persists the current in-memory state to disk for regulatory auditability."""
        out_dir = target_dir or self.case_dir
        if not out_dir:
            return
        out_dir.mkdir(parents=True, exist_ok=True)

        if self.case_input:
            (out_dir / "case_input.json").write_text(
                json.dumps(self.case_input, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if self.evidence_ledger is not None:
            (out_dir / "evidence_ledger.json").write_text(
                json.dumps(self.evidence_ledger, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if self.scoring_output:
            (out_dir / "scoring_output.json").write_text(
                json.dumps(self.scoring_output, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if self.findings:
            (out_dir / "findings.json").write_text(
                json.dumps(self.findings, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if self.blueprint_payload:
            (out_dir / f"blueprint_{self.tower_id.lower()}_payload.json").write_text(
                json.dumps(self.blueprint_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if self.annex_payload:
            (out_dir / f"approved_annex_{self.tower_id.lower()}.json").write_text(
                json.dumps(self.annex_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    @classmethod
    def hydrate_from_disk(
        cls, client_name: str, tower_id: str, case_dir: Path
    ) -> AssessmentContext:
        """Hydrates an AssessmentContext from existing disk checkpoints if present."""
        ctx = cls(client_name=client_name, tower_id=tower_id, case_dir=case_dir)

        if (case_dir / "case_input.json").is_file():
            try:
                ctx.case_input = json.loads(
                    (case_dir / "case_input.json").read_text(encoding="utf-8")
                )
                ctx.mark_stage_done("case_input")
            except Exception as ex:
                logger.debug("Error hidratando case_input: %s", ex)

        if (case_dir / "evidence_ledger.json").is_file():
            try:
                ctx.evidence_ledger = json.loads(
                    (case_dir / "evidence_ledger.json").read_text(encoding="utf-8")
                )
                ctx.mark_stage_done("evidence_ledger")
            except Exception as ex:
                logger.debug("Error hidratando evidence_ledger: %s", ex)

        if (case_dir / "scoring_output.json").is_file():
            try:
                ctx.scoring_output = json.loads(
                    (case_dir / "scoring_output.json").read_text(encoding="utf-8")
                )
                ctx.mark_stage_done("scoring")
            except Exception as ex:
                logger.debug("Error hidratando scoring_output: %s", ex)

        if (case_dir / "findings.json").is_file():
            try:
                ctx.findings = json.loads(
                    (case_dir / "findings.json").read_text(encoding="utf-8")
                )
                ctx.mark_stage_done("findings")
            except Exception as ex:
                logger.debug("Error hidratando findings: %s", ex)

        bp_file = case_dir / f"blueprint_{tower_id.lower()}_payload.json"
        if bp_file.is_file():
            try:
                ctx.blueprint_payload = json.loads(bp_file.read_text(encoding="utf-8"))
                ctx.mark_stage_done("blueprint")
            except Exception as ex:
                logger.debug("Error hidratando blueprint: %s", ex)

        annex_file = case_dir / f"approved_annex_{tower_id.lower()}.json"
        if annex_file.is_file():
            try:
                ctx.annex_payload = json.loads(annex_file.read_text(encoding="utf-8"))
                ctx.mark_stage_done("annex")
            except Exception as ex:
                logger.debug("Error hidratando annex: %s", ex)

        return ctx
