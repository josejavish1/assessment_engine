"""Empirical Data Parser Infrastructure Adapter (RFC 082).

Parses structured numerical questionnaires and telemetry artifacts (.xlsx, .txt, .csv)
into atomic EpistemicFragment domain entities with precise coordinate provenance.
"""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from assessment_engine.domain.contracts.ingestion_ports import IEmpiricalDataParserPort
from assessment_engine.domain.schemas.epistemic_ledger import (
    EpistemicFragment,
    EpistemicState,
    Polarity,
)

_MAX_XML_ENTRY_BYTES = 50 * 1024 * 1024  # 50 MB decompression guard against Zip Bombs
_TXT_SCORE_PATTERN = re.compile(
    r"^(?P<qid>[A-Za-z0-9_\.\-]+)[\s:=,\t]+(?P<val>-?\d+(?:[\.,]\d+)?)(?:\s*/\s*(?P<scale>\d+(?:[\.,]\d+)?))?(?:\s+(?P<notes>.*))?$"
)


def _safe_parse_xml_bytes(raw_bytes: bytes) -> ET.Element:
    """Safely parses XML bytes while blocking XXE and Billion Laughs ENTITY declarations."""
    header_sample = raw_bytes[:4096].upper()
    if b"<!ENTITY" in header_sample or b"<!DOCTYPE" in header_sample:
        raise ValueError("Security violation: XML ENTITY/DOCTYPE declarations are forbidden.")
    return ET.fromstring(raw_bytes)


def _read_zip_xml_safely(zf: zipfile.ZipFile, member_name: str) -> ET.Element:
    info = zf.getinfo(member_name)
    if info.file_size > _MAX_XML_ENTRY_BYTES:
        raise ValueError(
            f"Security violation: XML member '{member_name}' exceeds maximum uncompressed size "
            f"({info.file_size} > {_MAX_XML_ENTRY_BYTES} bytes)."
        )
    return _safe_parse_xml_bytes(zf.read(member_name))


class EmpiricalResponseParser(IEmpiricalDataParserPort):
    """Parses structured questionnaires and assessment spreadsheets with zero external dependencies."""

    def __init__(self, default_scale_max: float = 5.0) -> None:
        if default_scale_max <= 0:
            raise ValueError("default_scale_max must be positive")
        self.default_scale_max = default_scale_max

    def parse_empirical_file(self, file_path: Path) -> List[EpistemicFragment]:
        """Parse empirical questionnaire responses from file path."""
        if not file_path.exists():
            raise FileNotFoundError(f"Empirical response file not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix == ".xlsx":
            return self._parse_xlsx(file_path)
        if suffix in (".txt", ".dat"):
            return self._parse_txt(file_path)
        if suffix == ".csv":
            return self._parse_csv(file_path)
        raise ValueError(
            f"Unsupported empirical format '{suffix}'. Supported: .xlsx, .txt, .dat, .csv"
        )

    def _parse_txt(self, path: Path) -> List[EpistemicFragment]:
        """Parses key-value score text files with dynamic scale normalization."""
        fragments: List[EpistemicFragment] = []
        lines = path.read_text(encoding="utf-8-sig").splitlines()

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            match = _TXT_SCORE_PATTERN.match(line)
            if match:
                qid = match.group("qid").strip()
                score = float(match.group("val").replace(",", "."))
                scale_max = (
                    float(match.group("scale").replace(",", "."))
                    if match.group("scale")
                    else self.default_scale_max
                )
                notes = (match.group("notes") or "").strip()

                normalized_ratio = score / scale_max if scale_max > 0 else 0.0
                if normalized_ratio >= 0.70:
                    polarity = Polarity.POSITIVE
                elif normalized_ratio < 0.50:
                    polarity = Polarity.NEGATIVE
                else:
                    polarity = Polarity.NEUTRAL

                domain_ref = ".".join(qid.split(".")[:2]) if "." in qid else qid
                assertion = f"Question {qid} scored at {score}/{scale_max}."
                if notes:
                    assertion += f" Notes: {notes}"

                fragments.append(
                    EpistemicFragment(
                        fragment_id=uuid4(),
                        source_type="EMPIRICAL_TXT",
                        source_file=path.name,
                        location_reference=f"Line {line_no}",
                        domain_taxonomy_ref=domain_ref,
                        canonical_assertion=assertion,
                        epistemic_weight=0.85,
                        polarity=polarity,
                        state=EpistemicState.CURRENT,
                        metadata={
                            "question_id": qid,
                            "numeric_score": score,
                            "scale_max": scale_max,
                            "normalized_ratio": round(normalized_ratio, 4),
                            "notes": notes,
                        },
                    )
                )

        return fragments

    def _parse_csv(self, path: Path) -> List[EpistemicFragment]:
        """Parses CSV assessment tables."""
        fragments: List[EpistemicFragment] = []
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for row_no, row in enumerate(reader, start=1):
                if not row or not any(c.strip() for c in row):
                    continue
                content = " | ".join(c.strip() for c in row if c.strip())
                fragments.append(
                    EpistemicFragment(
                        fragment_id=uuid4(),
                        source_type="EMPIRICAL_TXT",
                        source_file=path.name,
                        location_reference=f"Row {row_no}",
                        domain_taxonomy_ref="",
                        canonical_assertion=content,
                        epistemic_weight=0.80,
                        polarity=Polarity.NEUTRAL,
                        state=EpistemicState.CURRENT,
                    )
                )
        return fragments

    @staticmethod
    def _extract_si_text(si_el: ET.Element, ns: Dict[str, str]) -> str:
        """Extracts text from <si> or <is> while excluding <rPh> phonetic furigana runs."""
        direct_t = si_el.find("main:t", ns)
        if direct_t is not None and direct_t.text:
            return direct_t.text
        parts: List[str] = []
        for r_el in si_el.findall("main:r", ns):
            t_el = r_el.find("main:t", ns)
            if t_el is not None and t_el.text:
                parts.append(t_el.text)
        return "".join(parts)

    def _parse_xlsx(self, path: Path) -> List[EpistemicFragment]:
        """Parses native OpenXML .xlsx files with XXE/Zip-Bomb guards and inlineStr support."""
        fragments: List[EpistemicFragment] = []

        with zipfile.ZipFile(path, "r") as z:
            namelist = set(z.namelist())
            if "xl/workbook.xml" not in namelist:
                return fragments

            wb_tree = _read_zip_xml_safely(z, "xl/workbook.xml")
            ns = {
                "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
                "rels": "http://schemas.openxmlformats.org/package/2006/relationships",
            }

            rel_map: Dict[str, str] = {}
            if "xl/_rels/workbook.xml.rels" in namelist:
                rels_tree = _read_zip_xml_safely(z, "xl/_rels/workbook.xml.rels")
                rel_map = {
                    r.attrib.get("Id", ""): r.attrib.get("Target", "").lstrip("/")
                    for r in rels_tree
                }

            shared_strings: List[str] = []
            if "xl/sharedStrings.xml" in namelist:
                ss_tree = _read_zip_xml_safely(z, "xl/sharedStrings.xml")
                for si in ss_tree.findall("main:si", ns):
                    shared_strings.append(self._extract_si_text(si, ns))

            for s in wb_tree.findall("main:sheets/main:sheet", ns):
                sheet_name = s.attrib.get("name", "Sheet")
                r_id = s.attrib.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id",
                    "",
                )
                target = rel_map.get(r_id, "")
                if not target:
                    continue
                target_path = f"xl/{target}" if not target.startswith("xl/") else target
                if target_path not in namelist:
                    continue

                ws_tree = _read_zip_xml_safely(z, target_path)
                for row_el in ws_tree.findall(".//main:sheetData/main:row", ns):
                    row_idx = row_el.attrib.get("r", "?")
                    cells_text: List[str] = []
                    for c_el in row_el.findall("main:c", ns):
                        cell_ref = c_el.attrib.get("r", "")
                        cell_type = c_el.attrib.get("t", "")
                        val = ""

                        if cell_type == "inlineStr":
                            is_el = c_el.find("main:is", ns)
                            if is_el is not None:
                                val = self._extract_si_text(is_el, ns)
                        else:
                            v_el = c_el.find("main:v", ns)
                            if v_el is not None and v_el.text:
                                raw_val = v_el.text
                                if cell_type == "s" and raw_val.isdigit():
                                    idx = int(raw_val)
                                    val = (
                                        shared_strings[idx]
                                        if idx < len(shared_strings)
                                        else raw_val
                                    )
                                else:
                                    val = raw_val

                        if val.strip():
                            cells_text.append(f"{cell_ref}: {val.strip()}")

                    if cells_text:
                        row_content = " | ".join(cells_text)
                        fragments.append(
                            EpistemicFragment(
                                fragment_id=uuid4(),
                                source_type="EMPIRICAL_XLSX",
                                source_file=path.name,
                                location_reference=f"{sheet_name}!Row{row_idx}",
                                domain_taxonomy_ref="",
                                canonical_assertion=row_content,
                                epistemic_weight=0.80,
                                polarity=Polarity.NEUTRAL,
                                state=EpistemicState.CURRENT,
                                metadata={
                                    "sheet": sheet_name,
                                    "row_index": row_idx,
                                },
                            )
                        )

        return fragments
