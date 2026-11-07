"""Raw Transcript Parser Infrastructure Adapter (RFC 082).

Parses unstructured dialogue streams (.docx, .vtt, .txt, .md) into ordered,
role-attributed RawUtterance domain entities with full Unicode/CJK support.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from uuid import uuid4

import docx
import yaml

from assessment_engine.domain.contracts.ingestion_ports import ITranscriptParserPort
from assessment_engine.domain.schemas.epistemic_ledger import AuthorityRole, RawUtterance
from assessment_engine.infrastructure.runtime_paths import ROOT

# Unicode-aware speaker pattern without catastrophic backtracking
_SPEAKER_PATTERN = re.compile(
    r"^(?P<speaker>[\w\-\.\s]{2,50}?)\s*(?:\((?P<role>[^\)\r\n]{1,60})\))?\s*[:：]\s*(?P<text>.+)$",
    re.DOTALL | re.UNICODE,
)

_VTT_TIMECODE_PATTERN = re.compile(
    r"^(?P<start>(?:\d{2}:)?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(?P<end>(?:\d{2}:)?\d{2}:\d{2}[\.,]\d{3})"
)

_VTT_VOICE_PATTERN = re.compile(
    r"^<v(?:\.[^\s>]+)?\s+([^>]+)>(.*?)(?:</v>)?$",
    re.DOTALL | re.UNICODE,
)

_QUESTION_TERMINATORS = ("?", "？")

_DEFAULT_ROLE_CUES: Dict[str, Set[str]] = {
    "INTERVIEWER": {"interviewer", "consultant", "auditor", "evaluator", "moderator"},
    "EXECUTIVE_SPONSOR": {"cio", "cto", "ciso", "coo", "cfo", "director", "vp", "executive", "sponsor"},
    "SME_TECHNICAL": {"sme", "architect", "engineer", "lead", "specialist", "sysadmin", "devops", "sre"},
}


def _normalize_unicode_text(text: str) -> str:
    """Normalizes Unicode text via NFKC casefolding while preserving CJK and international scripts."""
    return unicodedata.normalize("NFKC", text).casefold().strip()


class RawTranscriptParser(ITranscriptParserPort):
    """Concrete adapter for parsing transcript files (.docx, .vtt, .txt, .md)."""

    def __init__(self, ontology_path: Optional[Path] = None) -> None:
        self.ontology_path = ontology_path or (
            ROOT / "engine_config" / "ontologies" / "global_tech_ontology.yaml"
        )
        self._role_cues: Dict[str, Set[str]] = {
            k: set(v) for k, v in _DEFAULT_ROLE_CUES.items()
        }
        self._load_role_cues()

    def _load_role_cues(self) -> None:
        if not self.ontology_path.exists():
            return
        with open(self.ontology_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        configured_cues = data.get("role_classification_cues", {})
        for role_key, cues in configured_cues.items():
            if isinstance(cues, list):
                self._role_cues[role_key] = {_normalize_unicode_text(c) for c in cues if c}

    def _classify_role(self, speaker: str, role_hint: str = "", text: str = "") -> AuthorityRole:
        """Classifies participant role using token-aware Unicode matching."""
        combined = _normalize_unicode_text(f"{speaker} {role_hint}")
        tokens = set(re.findall(r"\w+", combined, flags=re.UNICODE))

        for role_name, authority_enum in (
            ("INTERVIEWER", AuthorityRole.INTERVIEWER),
            ("EXECUTIVE_SPONSOR", AuthorityRole.EXECUTIVE_SPONSOR),
            ("SME_TECHNICAL", AuthorityRole.SME_TECHNICAL),
        ):
            for cue in self._role_cues.get(role_name, set()):
                if (" " in cue and cue in combined) or (cue in tokens):
                    return authority_enum

        stripped = text.strip()
        if stripped.endswith(_QUESTION_TERMINATORS) and len(stripped.split()) < 30:
            return AuthorityRole.INTERVIEWER

        return AuthorityRole.SME_TECHNICAL

    def parse_transcript(self, file_path: Path) -> List[RawUtterance]:
        """Extracts sequential RawUtterance domain models from a transcript artifact."""
        if not file_path.exists():
            raise FileNotFoundError(f"Transcript artifact not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix == ".docx":
            return self._parse_docx(file_path)
        if suffix == ".vtt":
            return self._parse_vtt(file_path)
        if suffix in (".txt", ".md"):
            return self._parse_txt(file_path)
        raise ValueError(
            f"Unsupported transcript format '{suffix}'. Supported: .docx, .vtt, .txt, .md"
        )

    def _parse_text_blocks(
        self, blocks: Iterable[str], source_file: str
    ) -> List[RawUtterance]:
        utterances: List[RawUtterance] = []
        seq = 1
        current_speaker = "Unknown"
        current_role_hint = ""

        for raw_block in blocks:
            text = raw_block.strip()
            if not text:
                continue

            match = _SPEAKER_PATTERN.match(text)
            if match:
                speaker = match.group("speaker").strip()
                role_hint = (match.group("role") or "").strip()
                speech_text = match.group("text").strip()
                current_speaker = speaker
                current_role_hint = role_hint
                if not speech_text:
                    continue
                role = self._classify_role(speaker, role_hint, speech_text)
                utterances.append(
                    RawUtterance(
                        utterance_id=uuid4(),
                        sequence_index=seq,
                        source_file=source_file,
                        speaker_identifier=speaker,
                        speaker_role=role,
                        raw_text=speech_text,
                    )
                )
                seq += 1
            else:
                role = self._classify_role(current_speaker, current_role_hint, text)
                utterances.append(
                    RawUtterance(
                        utterance_id=uuid4(),
                        sequence_index=seq,
                        source_file=source_file,
                        speaker_identifier=current_speaker,
                        speaker_role=role,
                        raw_text=text,
                    )
                )
                seq += 1

        return utterances

    def _parse_docx(self, path: Path) -> List[RawUtterance]:
        doc = docx.Document(str(path))
        blocks: List[str] = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if row_cells:
                    blocks.append(": ".join(row_cells) if len(row_cells) == 2 else " ".join(row_cells))
        return self._parse_text_blocks(blocks, source_file=path.name)

    def _parse_vtt(self, path: Path) -> List[RawUtterance]:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        utterances: List[RawUtterance] = []
        seq = 1
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            time_match = _VTT_TIMECODE_PATTERN.match(line)
            if time_match:
                t_start = time_match.group("start")
                t_end = time_match.group("end")
                i += 1
                text_lines: List[str] = []
                while (
                    i < len(lines)
                    and lines[i].strip()
                    and not _VTT_TIMECODE_PATTERN.match(lines[i].strip())
                ):
                    text_lines.append(lines[i].strip())
                    i += 1
                raw_payload = " ".join(text_lines).strip()
                if raw_payload:
                    speaker = "Speaker"
                    voice_match = _VTT_VOICE_PATTERN.match(raw_payload)
                    if voice_match:
                        speaker = voice_match.group(1).strip() or "Speaker"
                        raw_payload = voice_match.group(2).strip()
                    # Strip any remaining inline VTT markup tags
                    raw_payload = re.sub(r"<[^>]+>", "", raw_payload).strip()
                    if raw_payload:
                        role = self._classify_role(speaker, "", raw_payload)
                        utterances.append(
                            RawUtterance(
                                utterance_id=uuid4(),
                                sequence_index=seq,
                                source_file=path.name,
                                timestamp_start=t_start,
                                timestamp_end=t_end,
                                speaker_identifier=speaker,
                                speaker_role=role,
                                raw_text=raw_payload,
                            )
                        )
                        seq += 1
                continue
            i += 1

        return utterances

    def _parse_txt(self, path: Path) -> List[RawUtterance]:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        return self._parse_text_blocks(lines, source_file=path.name)
