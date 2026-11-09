"""Phase 5: Automated Multi-Tower Forensic Quality Gate Verification Suite.

Executes end-to-end verification across all compiled specialist technical annexes
and Consolidated AS-IS deliverables against the 6 Quality Gates:
- QG-01: Codebase English Decoupling Law & Cleanliness.
- QG-02: Chapter 2 Completeness (Sections 2.1 & 2.2 non-empty, zero error placeholders).
- QG-03: Causal Risk Impact Purity (Zero raw bare enum tokens in risk tables).
- QG-04: Table 6 Polarity & Orthography (Zero orphaned adversative fragments in strengths).
- QG-05: Closed-World Grounding Audit (Zero unverified tools or paper-and-ink hallucinations).
- QG-06: Consolidated Deliverable Structural Integrity & Multi-Tower Cohesion.

Strictly 100% Technical English, zero hardcoding, multi-tenant and topology-agnostic.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List, Sequence, Set

import pytest
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCALES_PATH = REPO_ROOT / "engine_config/locales.json"

_EXCLUDED_DIR_SUBSTRINGS: Sequence[str] = (
    "baseline",
    "pre_",
    "archive",
    "old",
    "test_",
    "simul",
    ".zip",
    "compar",
    "geodis",
    "starling",
    "chedraui",
    "datadog",
    "rede_d_or",
)


def _load_locales_catalog() -> dict:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _detect_document_locale(doc: Document, fallback: str = "en") -> str:
    env_override = os.getenv("ASSESSMENT_DOC_LOCALE")
    if env_override:
        return env_override.strip().lower()

    catalog = _load_locales_catalog()
    sample_chunks = [p.text for p in doc.paragraphs[:20] if p.text.strip()]
    sample_text = f" {' '.join(sample_chunks).lower()} "

    scores: dict[str, int] = {}
    for lang, loc_data in catalog.items():
        if isinstance(loc_data, dict):
            tokens = loc_data.get("linguistic_signature_tokens", [])
            score = sum(1 for tok in tokens if tok.lower() in sample_text)
            if score > 0:
                scores[lang] = score

    if scores:
        return max(scores, key=lambda k: scores[k])
    return fallback


def _get_locale_config(locale_code: str) -> dict:
    catalog = _load_locales_catalog()
    return catalog.get(locale_code, catalog.get("en", {}))


def _build_bare_enum_regex(tokens: Sequence[str]) -> re.Pattern[str]:
    escaped = [re.escape(t) for t in tokens if t.strip()]
    if not escaped:
        escaped = [r"LOW", r"MEDIUM", r"HIGH", r"CRITICAL"]
    pattern = rf"^\s*(?:{'|'.join(escaped)})\s*[\.:;]?\s*$"
    return re.compile(pattern, re.IGNORECASE)


def _resolve_deliverables_search_roots() -> list[Path]:
    custom_dir = os.getenv("ASSESSMENT_DELIVERABLES_DIR")
    if custom_dir:
        custom_path = Path(custom_dir)
        return [custom_path] if custom_path.exists() else []

    working_out = REPO_ROOT / "working/out"
    if not working_out.exists():
        return []

    candidate_roots: list[Path] = []
    for item in working_out.iterdir():
        if not item.is_dir():
            continue
        name_lower = item.name.lower()
        if any(exc in name_lower for exc in _EXCLUDED_DIR_SUBSTRINGS):
            continue
        docx_files = list(item.glob("**/*ASIS.docx"))
        if docx_files:
            candidate_roots.append(item)

    if candidate_roots:
        with_annexes = [
            d
            for d in candidate_roots
            if any("anexo" in f.name.lower() or "annex" in f.name.lower() for f in d.glob("**/*ASIS.docx"))
        ]
        pool = with_annexes if with_annexes else candidate_roots
        pool.sort(
            key=lambda d: max(f.stat().st_mtime for f in d.glob("**/*ASIS.docx")),
            reverse=True,
        )
        return [pool[0]]

    return [working_out]


def _discover_compiled_annexes() -> list[Path]:
    search_roots = _resolve_deliverables_search_roots()
    catalog = _load_locales_catalog()

    all_vol_tokens: Set[str] = set()
    for loc_data in catalog.values():
        if isinstance(loc_data, dict):
            for tok in loc_data.get("consolidated_filename_markers", []):
                all_vol_tokens.add(tok.lower())

    found: list[Path] = []
    seen_names: set[str] = set()

    for root in search_roots:
        for docx_path in sorted(root.glob("**/*.docx"), key=lambda p: p.stat().st_mtime, reverse=True):
            name = docx_path.name
            if name.startswith("~$"):
                continue
            name_lower = name.lower()
            if any(exc in name_lower for exc in _EXCLUDED_DIR_SUBSTRINGS):
                continue

            is_volume = any(vtok in name_lower for vtok in all_vol_tokens)
            if not is_volume and "asis" in name_lower:
                if name not in seen_names:
                    seen_names.add(name)
                    found.append(docx_path)

    found.sort(key=lambda p: p.name)
    return found


def _discover_consolidated_deliverables() -> list[Path]:
    search_roots = [REPO_ROOT] + _resolve_deliverables_search_roots()
    catalog = _load_locales_catalog()

    all_vol_tokens: Set[str] = set()
    for loc_data in catalog.values():
        if isinstance(loc_data, dict):
            for tok in loc_data.get("consolidated_filename_markers", []):
                all_vol_tokens.add(tok.lower())

    found: list[Path] = []
    seen: set[Path] = set()

    for root in search_roots:
        if not root.exists():
            continue
        for docx_path in root.glob("*.docx"):
            name_lower = docx_path.name.lower()
            if docx_path.name.startswith("~$"):
                continue
            if any(exc in name_lower for exc in _EXCLUDED_DIR_SUBSTRINGS):
                continue

            is_volume = any(vtok in name_lower for vtok in all_vol_tokens)
            if is_volume and "asis" in name_lower:
                real_p = docx_path.resolve()
                if real_p not in seen and real_p.exists():
                    seen.add(real_p)
                    found.append(real_p)

    found.sort(key=lambda p: p.stat().st_size, reverse=True)
    return found


DISCOVERED_ANNEXES = _discover_compiled_annexes()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "annex_docx_path" in metafunc.fixturenames:
        metafunc.parametrize("annex_docx_path", DISCOVERED_ANNEXES, ids=lambda p: p.name)


def test_qg_01_annex_discovery_preflight() -> None:
    """Verifies that compiled technical domain deliverables were discovered in output targets."""
    assert len(DISCOVERED_ANNEXES) >= 1, "No compiled AS-IS technical deliverables found in search targets"


def test_qg_02_chapter_2_completeness_and_zero_placeholders(annex_docx_path: Path) -> None:
    """Verifies that Sections 2.1 and 2.2 exist, are populated (>= 30 words), and contain zero placeholders."""
    doc = Document(str(annex_docx_path))
    locale_code = _detect_document_locale(doc)
    locale_cfg = _get_locale_config(locale_code)

    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text_lower = " ".join(paragraphs).lower()

    banned_markers: Sequence[str] = locale_cfg.get(
        "banned_placeholder_markers",
        ["not available", "placeholder", "undefined"],
    )
    for banned in banned_markers:
        assert banned.lower() not in full_text_lower, (
            f"Failed QG-02: Banned placeholder '{banned}' detected in {annex_docx_path.name}"
        )

    sec_ch2_tokens: Sequence[str] = locale_cfg.get(
        "section_ch2_probe_tokens", ["methodology", "scope"]
    )
    sec_2_1_tokens: Sequence[str] = locale_cfg.get(
        "section_2_1_probe_tokens", ["objective and scope", "scope"]
    )
    sec_2_2_tokens: Sequence[str] = locale_cfg.get(
        "section_2_2_probe_tokens", ["platform description"]
    )
    cmmi_tokens: Sequence[str] = locale_cfg.get(
        "section_cmmi_probe_tokens", ["cmmi", "analytical scale"]
    )
    ch3_tokens: Sequence[str] = locale_cfg.get(
        "section_ch3_probe_tokens", ["technical diagnosis", "dashboard"]
    )

    ch2_idx = next(
        (i for i, p in enumerate(paragraphs) if any(t in p.lower() for t in sec_ch2_tokens)),
        -1,
    )
    start_idx = ch2_idx + 1 if ch2_idx != -1 else 0

    sec_2_1_idx = next(
        (
            i
            for i in range(start_idx, len(paragraphs))
            if any(t in paragraphs[i].lower() for t in sec_2_1_tokens)
            and len(paragraphs[i].split()) <= 6
        ),
        -1,
    )
    sec_2_2_idx = next(
        (
            i
            for i in range(sec_2_1_idx + 1 if sec_2_1_idx != -1 else start_idx, len(paragraphs))
            if any(t in paragraphs[i].lower() for t in sec_2_2_tokens)
            and len(paragraphs[i].split()) <= 6
        ),
        -1,
    )
    sec_cmmi_idx = next(
        (
            i
            for i in range(sec_2_2_idx + 1 if sec_2_2_idx != -1 else start_idx, len(paragraphs))
            if any(t in paragraphs[i].lower() for t in cmmi_tokens)
            and len(paragraphs[i].split()) <= 6
        ),
        -1,
    )
    sec_ch3_idx = next(
        (
            i
            for i in range(sec_2_2_idx + 1 if sec_2_2_idx != -1 else start_idx, len(paragraphs))
            if any(t in paragraphs[i].lower() for t in ch3_tokens)
            and len(paragraphs[i].split()) <= 8
        ),
        len(paragraphs),
    )

    assert sec_2_1_idx != -1, f"Missing Section 2.1 header in {annex_docx_path.name}"
    assert sec_2_2_idx != -1, f"Missing Section 2.2 header in {annex_docx_path.name}"
    assert sec_2_1_idx < sec_2_2_idx, f"Section 2.1 / 2.2 header ordering invalid in {annex_docx_path.name}"

    sec_2_1_text = " ".join(paragraphs[sec_2_1_idx + 1 : sec_2_2_idx])
    end_of_sec_2_2 = sec_cmmi_idx if sec_cmmi_idx > sec_2_2_idx else sec_ch3_idx
    sec_2_2_text = " ".join(paragraphs[sec_2_2_idx + 1 : end_of_sec_2_2])

    assert len(sec_2_1_text.split()) >= 30, (
        f"Section 2.1 under-populated ({len(sec_2_1_text.split())} words) in {annex_docx_path.name}"
    )
    assert len(sec_2_2_text.split()) >= 30, (
        f"Section 2.2 under-populated ({len(sec_2_2_text.split())} words) in {annex_docx_path.name}"
    )


def test_qg_03_risk_impact_narrative_disambiguation(annex_docx_path: Path) -> None:
    """Verifies that no risk card impact field contains a raw bare severity enum."""
    doc = Document(str(annex_docx_path))
    locale_code = _detect_document_locale(doc)
    locale_cfg = _get_locale_config(locale_code)

    impact_prefix = locale_cfg.get(
        "risk_card_operational_impact_label", "Operational and Continuity Impact"
    )
    bare_enum_tokens: Sequence[str] = locale_cfg.get(
        "bare_severity_enum_tokens", ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    )
    bare_enum_re = _build_bare_enum_regex(bare_enum_tokens)

    inspected_cells = 0
    pattern = re.compile(re.escape(impact_prefix), re.IGNORECASE)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text.strip()
                if pattern.search(text):
                    inspected_cells += 1
                    parts = pattern.split(text, maxsplit=1)
                    clause_after = parts[1].lstrip(" :-\t\n").strip()
                    assert not bare_enum_re.fullmatch(clause_after), (
                        f"Failed QG-03: Raw enum impact '{clause_after}' found in {annex_docx_path.name}"
                    )
                    assert len(clause_after.split()) >= 3, (
                        f"Failed QG-03: Impact narrative too terse ('{clause_after}') in {annex_docx_path.name}"
                    )

    assert inspected_cells >= 1, (
        f"Failed QG-03: Vacant pass detected. Zero risk impact cells matched '{impact_prefix}' in {annex_docx_path.name}"
    )


def test_qg_04_table_6_polarity_and_orthography(annex_docx_path: Path) -> None:
    """Verifies Table 6 strength rows contain zero orphaned adversative fragments."""
    doc = Document(str(annex_docx_path))
    locale_code = _detect_document_locale(doc)
    locale_cfg = _get_locale_config(locale_code)

    adversatives = tuple(
        p.lower() for p in locale_cfg.get("adversative_connective_prefixes", [])
    )
    strength_tokens: Sequence[str] = locale_cfg.get(
        "table6_strength_probe_tokens", ["strength", "identified"]
    )

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                lines = [ln.strip() for ln in cell.text.splitlines() if ln.strip()]
                for line in lines:
                    line_lower = line.lower()
                    if any(t in line_lower for t in strength_tokens):
                        clean_body = re.sub(r"^[^:]+:\s*", "", line_lower).strip()
                        for adv in adversatives:
                            assert not clean_body.startswith(adv), (
                                f"Failed QG-04: Orphaned adversative '{adv}' in strength row of {annex_docx_path.name}: '{line}'"
                            )


def test_qg_05_closed_world_grounding_audit(annex_docx_path: Path) -> None:
    """Verifies deliverable contains zero unverified physical instruments or manual paper tools."""
    doc = Document(str(annex_docx_path))
    locale_code = _detect_document_locale(doc)
    locale_cfg = _get_locale_config(locale_code)

    # Scan both paragraphs and table cell text
    all_chunks: List[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    all_chunks.append(cell.text)
    full_text = " ".join(all_chunks)

    speculative_patterns = locale_cfg.get("speculative_artifact_regexes", [])
    for pat in speculative_patterns:
        match = re.search(pat, full_text, flags=re.IGNORECASE)
        assert match is None, (
            f"Failed QG-05: Hallucinated speculative artifact '{match.group(0)}' found in {annex_docx_path.name}"
        )


def test_qg_06_consolidated_deliverable_structural_integrity() -> None:
    """Verifies that Consolidated AS-IS deliverable compiles cleanly and contains full multi-tower synthesis."""
    consolidated_candidates = _discover_consolidated_deliverables()
    assert len(consolidated_candidates) >= 1, "Missing Consolidated AS-IS deliverable in repository"

    primary_consolidated = consolidated_candidates[0]
    assert primary_consolidated.stat().st_size >= 100_000, f"Consolidated deliverable is under-sized: {primary_consolidated.name}"

    doc = Document(str(primary_consolidated))
    locale_code = _detect_document_locale(doc)
    locale_cfg = _get_locale_config(locale_code)

    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text_lower = " ".join(paragraphs).lower()

    banned_markers: Sequence[str] = locale_cfg.get(
        "banned_placeholder_markers",
        ["not available", "placeholder", "undefined"],
    )
    for banned in banned_markers:
        assert banned.lower() not in full_text_lower, (
            f"Consolidated deliverable failed QG-06: Banned placeholder '{banned}' detected"
        )

    # Scale thresholds proportionally with discovered domain topology
    topology_size = max(1, len(DISCOVERED_ANNEXES))
    min_tables = max(3, topology_size * 2)
    min_paragraphs = max(20, topology_size * 4)
    min_words = max(1000, topology_size * 300)

    assert len(doc.tables) >= min_tables, (
        f"Consolidated deliverable has insufficient tables ({len(doc.tables)} < {min_tables})"
    )
    assert len(paragraphs) >= min_paragraphs, (
        f"Consolidated deliverable has insufficient paragraphs ({len(paragraphs)} < {min_paragraphs})"
    )

    total_words = sum(len(p.text.split()) for p in doc.paragraphs)
    seen_cell_ids: Set[int] = set()
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                cell_id = id(cell._tc)
                if cell_id not in seen_cell_ids:
                    seen_cell_ids.add(cell_id)
                    total_words += len(cell.text.split())

    assert total_words >= min_words, (
        f"Consolidated deliverable has insufficient total word count ({total_words} < {min_words})"
    )
