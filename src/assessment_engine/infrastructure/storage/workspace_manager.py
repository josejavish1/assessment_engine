"""
Atomic, crash-safe physical workspace persistence manager.
Manages tenant directories under `working/[client_slug]/` and deliverable outputs in `working/out/[client_slug]/`.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

from assessment_engine.domain.schemas.workspace_contracts import (
    ClientDossierV3,
    DigitalTwinStateContract,
    EvidenceVaultContract,
    PipelineStatusContract,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]
WORKING_DIR = REPO_ROOT / "working"
WORKING_OUT_DIR = WORKING_DIR / "out"


class WorkspacePersistenceManager:
    """Provides crash-safe, atomic read and write operations for tenant physical workspaces."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = (root_dir or WORKING_DIR).resolve()
        self.out_dir = (self.root_dir / "out").resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def resolve_client_dir(self, client_slug: str) -> Path:
        """Resolves and ensures existence of tenant working directory."""
        sanitized = "".join(c if c.isalnum() or c == "-" else "_" for c in client_slug.lower().strip())
        client_dir = self.root_dir / sanitized
        client_dir.mkdir(parents=True, exist_ok=True)
        (client_dir / "raw_ingested").mkdir(parents=True, exist_ok=True)
        return client_dir

    def resolve_output_dir(self, client_slug: str) -> Path:
        """Resolves and ensures existence of tenant deliverables directory."""
        sanitized = "".join(c if c.isalnum() or c == "-" else "_" for c in client_slug.lower().strip())
        out_dir = self.out_dir / sanitized
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def _atomic_write_json(self, target_path: Path, payload: Union[BaseModel, Dict[str, Any]]) -> None:
        """Writes JSON payload to disk using write-ahead temp file and atomic POSIX replace."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.parent / f".tmp_{target_path.name}_{uuid.uuid4().hex}.json"

        if isinstance(payload, BaseModel):
            json_str = payload.model_dump_json(indent=2)
        else:
            json_str = json.dumps(payload, indent=2, ensure_ascii=False)

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(json_str)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename guaranteed at filesystem level
            os.replace(temp_path, target_path)
        except Exception as ex:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            logger.error("Atomic write failed for %s: %s", target_path, ex)
            raise

    # 1. Client Intelligence Dossier (client_intelligence.json)
    def save_client_intelligence(self, client_slug: str, dossier: ClientDossierV3) -> Path:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "client_intelligence.json"
        self._atomic_write_json(target, dossier)
        logger.info("Saved ClientDossierV3 for %s at %s", client_slug, target)
        return target

    def load_client_intelligence(self, client_slug: str) -> Optional[ClientDossierV3]:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "client_intelligence.json"
        if not target.exists():
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Support canonical schema version validation
            return ClientDossierV3.model_validate(raw)
        except Exception as ex:
            logger.warning("Could not parse client_intelligence.json for %s: %s", client_slug, ex)
            return None

    # 2. Evidence Vault (evidence_vault.json)
    def save_evidence_vault(self, client_slug: str, vault: EvidenceVaultContract) -> Path:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "evidence_vault.json"
        self._atomic_write_json(target, vault)
        logger.info("Saved EvidenceVaultContract for %s (%d fragments)", client_slug, vault.total_fragments)
        return target

    def load_evidence_vault(self, client_slug: str) -> Optional[EvidenceVaultContract]:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "evidence_vault.json"
        if not target.exists():
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return EvidenceVaultContract.model_validate(raw)
        except Exception as ex:
            logger.warning("Could not parse evidence_vault.json for %s: %s", client_slug, ex)
            return None

    # 3. Digital Twin State (digital_twin_state.json)
    def save_digital_twin_state(self, client_slug: str, state: DigitalTwinStateContract) -> Path:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "digital_twin_state.json"
        self._atomic_write_json(target, state)
        logger.info("Saved DigitalTwinStateContract for %s (%d towers)", client_slug, len(state.towers))
        return target

    def load_digital_twin_state(self, client_slug: str) -> Optional[DigitalTwinStateContract]:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "digital_twin_state.json"
        if not target.exists():
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return DigitalTwinStateContract.model_validate(raw)
        except Exception as ex:
            logger.warning("Could not parse digital_twin_state.json for %s: %s", client_slug, ex)
            return None

    # 4. Pipeline Status (pipeline_status.json)
    def save_pipeline_status(self, client_slug: str, status: PipelineStatusContract) -> Path:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "pipeline_status.json"
        self._atomic_write_json(target, status)
        return target

    def load_pipeline_status(self, client_slug: str) -> Optional[PipelineStatusContract]:
        client_dir = self.resolve_client_dir(client_slug)
        target = client_dir / "pipeline_status.json"
        if not target.exists():
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return PipelineStatusContract.model_validate(raw)
        except Exception as ex:
            logger.warning("Could not parse pipeline_status.json for %s: %s", client_slug, ex)
            return None
