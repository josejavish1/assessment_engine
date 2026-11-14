"""
Dual-mode ingestion service for the two core assessment artefacts:
1. Context Dossier / Interview Transcript (.docx, .txt, .pdf) -> evidence_vault.json & client_intelligence.json
2. Assessment Matrix / Questionnaire (.xlsx, .txt) -> digital_twin_state.json
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile

import openpyxl

from assessment_engine.domain.schemas.workspace_contracts import (
    ClientDossierV3,
    DigitalTwinStateContract,
    EvidenceFragment,
    EvidenceSourceType,
    EvidenceVaultContract,
    QuestionResponseItem,
    SecurityTowerState,
)
from assessment_engine.infrastructure.storage.workspace_manager import (
    WorkspacePersistenceManager,
)

logger = logging.getLogger(__name__)

RESPONSE_RE = re.compile(r"(T\d+\.P\d+\.K\d+)\.?\s*PR(\d+)[\s:\t]+([1-5](?:[.,]\d+)?)")
QUESTION_ID_PATTERN = re.compile(r"(T\d+)\.P\d+\.K\d+\.PR\d+")


def read_docx_text(path: Path) -> str:
    """Extract raw text content from a DOCX file preserving paragraph boundaries."""
    try:
        with ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
        # Preserve paragraph breaks from Word OpenXML
        xml = xml.replace("</w:p>", "\n")
        text = re.sub(r"<[^>]+>", " ", xml)
        # Collapse multiple spaces on the same line while keeping newlines
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(line for line in lines if line)
    except Exception as ex:
        logger.warning("Failed to parse DOCX archive %s: %s", path, ex)
        return ""


def read_document_text(path: Path) -> str:
    """Dispatches text extraction based on file suffix."""
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


class DocumentIngestionService:
    """Extracts forensic evidence statements from context transcripts and meeting notes (Artefact 1)."""

    def __init__(self, workspace_manager: Optional[WorkspacePersistenceManager] = None) -> None:
        self.workspace_manager = workspace_manager or WorkspacePersistenceManager()

    def ingest_context_transcript(
        self,
        client_slug: str,
        source_path: Path,
        source_filename: str,
    ) -> EvidenceVaultContract:
        """Processes a context meeting transcript and updates evidence_vault.json and client_intelligence.json."""
        raw_text = read_document_text(source_path)
        if not raw_text.strip():
            logger.warning("No text extracted from context transcript: %s", source_path)

        # Chunk text into coherent forensic fragments (paragraphs of ~100-300 words)
        raw_paragraphs = [p.strip() for p in raw_text.split("\n") if len(p.strip()) > 40]
        if not raw_paragraphs:
            raw_paragraphs = [p.strip() for p in re.split(r"(?<=[.!?])\s+", raw_text) if len(p.strip()) > 40]

        now_utc = datetime.now(timezone.utc).isoformat()
        fragments: List[EvidenceFragment] = []

        for idx, para in enumerate(raw_paragraphs[:150]):
            frag_hash = hashlib.sha256(para.encode("utf-8")).hexdigest()[:8].upper()
            evidence_id = f"EV-{frag_hash}"

            # Basic tower keyword inference
            mapped_towers: List[str] = []
            lower_para = para.lower()
            if any(k in lower_para for k in ["cpd", "datacenter", "data center", "eléctric", "ups", "generador", "clima"]):
                mapped_towers.append("T1")
            if any(k in lower_para for k in ["cloud", "aws", "azure", "kubernetes", "hypervisor", "compute", "servidor"]):
                mapped_towers.append("T2")
            if any(k in lower_para for k in ["red", "wan", "lan", "sd-wan", "firewall", "mpls", "switch", "vpn"]):
                mapped_towers.append("T3")
            if any(k in lower_para for k in ["storage", "almacenamiento", "nas", "san", "backup", "block storage", "file storage"]):
                mapped_towers.append("T4")
            if any(k in lower_para for k in ["drp", "bcp", "resiliencia", "rto", "rpo", "contingencia", "desastre"]):
                mapped_towers.append("T5")
            if any(k in lower_para for k in ["seguridad", "ciber", "soc", "siem", "edr", "ransomware", "iam", "mfa"]):
                mapped_towers.append("T6")

            fragments.append(
                EvidenceFragment(
                    evidence_id=evidence_id,
                    source_type=EvidenceSourceType.INTERVIEW_TRANSCRIPT,
                    source_filename=source_filename,
                    ingestion_timestamp_utc=now_utc,
                    raw_verbatim_text=para,
                    normalized_claim=para[:180] + ("..." if len(para) > 180 else ""),
                    mapped_domain_ids=mapped_towers,
                    confidence_score=0.92,
                )
            )

        # Merge with existing evidence vault if present
        existing_vault = self.workspace_manager.load_evidence_vault(client_slug)
        existing_fragments = existing_vault.fragments if existing_vault else []

        seen_ids = {f.evidence_id for f in existing_fragments}
        merged_fragments = list(existing_fragments)
        for f in fragments:
            if f.evidence_id not in seen_ids:
                merged_fragments.append(f)
                seen_ids.add(f.evidence_id)

        vault = EvidenceVaultContract(
            client_slug=client_slug,
            total_fragments=len(merged_fragments),
            integrity_hash=hashlib.sha256(json.dumps([f.evidence_id for f in merged_fragments]).encode("utf-8")).hexdigest(),
            fragments=merged_fragments,
        )
        self.workspace_manager.save_evidence_vault(client_slug, vault)

        # Update client intelligence synthesis
        dossier = self.workspace_manager.load_client_intelligence(client_slug)
        if dossier:
            summary_snippet = " ".join(raw_paragraphs[:3])[:1000]
            dossier.executive_context_synthesis = summary_snippet
            dossier.last_updated_utc = now_utc
            self.workspace_manager.save_client_intelligence(client_slug, dossier)

        return vault


class AssessmentMatrixParserService:
    """Parses Excel spreadsheets or raw response text matrices into DigitalTwinStateContract (Artefact 2)."""

    def __init__(self, workspace_manager: Optional[WorkspacePersistenceManager] = None) -> None:
        self.workspace_manager = workspace_manager or WorkspacePersistenceManager()

    def parse_matrix_file(self, file_path: Path) -> Dict[str, Any]:
        """Parses an Excel workbook or text matrix file and extracts tower ratings and question responses."""
        suffix = file_path.suffix.lower()
        if suffix == ".xlsx":
            return self._parse_excel_matrix(file_path)
        return self._parse_text_matrix(file_path)

    def _parse_excel_matrix(self, file_path: Path) -> Dict[str, Any]:
        """Parses canonical multi-sheet Excel questionnaire."""
        wb = openpyxl.load_workbook(str(file_path), data_only=True, read_only=True)
        tower_scores: Dict[str, List[float]] = {}
        tower_responses: Dict[str, List[QuestionResponseItem]] = {}
        tower_notes: Dict[str, List[str]] = {}

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            # Identify tower from sheet name (e.g. 'T1- Physical Data Center' -> 'T1')
            tower_match = re.match(r"(T\d+)", sheet_name.strip())
            tower_id_hint = tower_match.group(1) if tower_match else None

            for row in ws.iter_rows(values_only=True):
                if not row or len(row) < 3:
                    continue

                # Scan for Question ID format: T1.P1.K1.PR1
                qid = None
                score = None
                comment = None

                for idx, cell in enumerate(row):
                    if cell is not None and isinstance(cell, str) and QUESTION_ID_PATTERN.search(cell):
                        qid = QUESTION_ID_PATTERN.search(cell).group(0)
                        # Check subsequent cells for numeric score 1.0 - 5.0
                        for next_idx in range(idx + 1, min(len(row), idx + 8)):
                            val = row[next_idx]
                            if isinstance(val, (int, float)) and 1.0 <= float(val) <= 5.0:
                                score = float(val)
                            elif isinstance(val, str) and val.strip().replace(",", ".").replace(".0", "").isdigit():
                                try:
                                    s_val = float(val.strip().replace(",", "."))
                                    if 1.0 <= s_val <= 5.0:
                                        score = s_val
                                except ValueError:
                                    pass
                            elif isinstance(val, str) and len(val.strip()) > 15:
                                comment = val.strip()

                if qid and score is not None:
                    tower_prefix = qid.split(".")[0]
                    target_tower = tower_prefix if tower_prefix.startswith("T") else (tower_id_hint or "T1")

                    if target_tower not in tower_scores:
                        tower_scores[target_tower] = []
                        tower_responses[target_tower] = []
                        tower_notes[target_tower] = []

                    tower_scores[target_tower].append(score)
                    tower_responses[target_tower].append(
                        QuestionResponseItem(
                            question_id=qid,
                            response_text=comment or "",
                            maturity_indicator=score,
                        )
                    )
                    if comment:
                        tower_notes[target_tower].append(comment)

        wb.close()
        return self._build_synthesis_dict(tower_scores, tower_responses, tower_notes)

    def _parse_text_matrix(self, file_path: Path) -> Dict[str, Any]:
        """Parses tab-separated or colon-separated question response text file."""
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        tower_scores: Dict[str, List[float]] = {}
        tower_responses: Dict[str, List[QuestionResponseItem]] = {}
        tower_notes: Dict[str, List[str]] = {}

        for q_prefix, pr_num, val_str in RESPONSE_RE.findall(text):
            qid = f"{q_prefix}.PR{pr_num}"
            score = float(val_str.replace(",", "."))
            tower_id = qid.split(".")[0]

            if tower_id not in tower_scores:
                tower_scores[tower_id] = []
                tower_responses[tower_id] = []
                tower_notes[tower_id] = []

            tower_scores[tower_id].append(score)
            tower_responses[tower_id].append(
                QuestionResponseItem(
                    question_id=qid,
                    response_text="",
                    maturity_indicator=score,
                )
            )

        return self._build_synthesis_dict(tower_scores, tower_responses, tower_notes)

    def _build_synthesis_dict(
        self,
        tower_scores: Dict[str, List[float]],
        tower_responses: Dict[str, List[QuestionResponseItem]],
        tower_notes: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        result_towers: Dict[str, SecurityTowerState] = {}
        all_scores: List[float] = []

        for tower_id, scores in tower_scores.items():
            avg_score = round(sum(scores) / len(scores), 2) if scores else 3.0
            all_scores.append(avg_score)
            notes_text = " | ".join(tower_notes.get(tower_id, []))[:500]

            result_towers[tower_id] = SecurityTowerState(
                tower_id=tower_id,
                calibrated_maturity_score=avg_score,
                target_to_be_score=min(5.0, round(avg_score + 1.0, 1)),
                assessor_forensic_notes=notes_text,
                is_applicable=True,
                completed=True,
                question_responses=tower_responses.get(tower_id, []),
            )

        overall_maturity = round(sum(all_scores) / len(all_scores), 2) if all_scores else 3.0
        return {
            "towers": result_towers,
            "overall_maturity_index": overall_maturity,
            "total_questions_parsed": sum(len(items) for items in tower_responses.values()),
        }

    def ingest_assessment_matrix(
        self,
        client_slug: str,
        source_path: Path,
        source_filename: str,
    ) -> DigitalTwinStateContract:
        """Parses matrix file and persists the resulting state vector to digital_twin_state.json."""
        parsed_data = self.parse_matrix_file(source_path)
        now_utc = datetime.now(timezone.utc).isoformat()

        # Merge with existing digital twin state if present
        existing_twin = self.workspace_manager.load_digital_twin_state(client_slug)
        existing_towers = existing_twin.towers if existing_twin else {}

        merged_towers = dict(existing_towers)
        for tower_id, state in parsed_data["towers"].items():
            merged_towers[tower_id] = state

        completed_count = len([t for t in merged_towers.values() if t.completed])
        completion_pct = round((completed_count / max(1, len(merged_towers))) * 100.0, 1)

        digital_twin = DigitalTwinStateContract(
            client_slug=client_slug,
            last_synchronized_utc=now_utc,
            overall_maturity_index=parsed_data["overall_maturity_index"],
            completion_percentage=completion_pct,
            towers=merged_towers,
        )

        self.workspace_manager.save_digital_twin_state(client_slug, digital_twin)
        logger.info(
            "Ingested assessment matrix for %s: %d towers, overall index %.2f",
            client_slug,
            len(merged_towers),
            digital_twin.overall_maturity_index,
        )

        # Native lifecycle hydration of declared scores into tower blueprints and scoring manifests
        client_dir = self.workspace_manager.resolve_client_dir(client_slug)
        if source_path.suffix.lower() == ".xlsx":
            try:
                from assessment_engine.application.services.survey_score_hydrator import (
                    SurveyScoreHydrator,
                )
                SurveyScoreHydrator.hydrate_client_directory(source_path, client_dir)
                logger.info("Successfully hydrated declared scores for client %s across all towers", client_slug)
            except Exception as hyd_ex:
                logger.warning("Automated survey score hydration failed for %s: %s", client_slug, hyd_ex)

        return digital_twin
