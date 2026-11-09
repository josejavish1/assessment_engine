#!/usr/bin/env python3
"""Execute deep empirical review of current AS-IS deliverables and compare against pre-remediation baseline."""

from __future__ import annotations

import re
from pathlib import Path
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_DIR = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS"
TOMO1_PATH = REPO_ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
BASELINE_DIR = REPO_ROOT / "working/out/molins_baseline_pre_argon"

SPECULATIVE_TERMS = (
    r"pinzas?\s+amperim[eé]tricas?",
    r"c[aá]maras?\s+t[eé]rmicas?",
    r"formularios?\s+impresos?",
    r"firmas?\s+manuscritas?",
    r"libretas?\s+f[ií]sicas?",
    r"clamp\s+meters?",
)

BARE_ENUM_RE = re.compile(r"^\s*(?:BAJO|MEDIO|ALTO|CR[IÍ]TICO|CRITICO|LOW|MEDIUM|HIGH|CRITICAL)\s*[\.:;]?\s*$", re.IGNORECASE)
UNRESOLVED_PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z0-9_]+\}")


def inspect_document(doc_path: Path) -> dict:
    doc = Document(str(doc_path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text = " ".join(paragraphs)

    # 1. Check placeholders
    unresolved = UNRESOLVED_PLACEHOLDER_RE.findall(full_text)

    # 2. Check speculative artifacts
    speculative_hits = []
    for pat in SPECULATIVE_TERMS:
        m = re.search(pat, full_text, flags=re.IGNORECASE)
        if m:
            speculative_hits.append(m.group(0))

    # 3. Check Chapter 2 presence
    has_ch2 = any("objetivo, alcance y marco" in p.lower() or "marco metodológico" in p.lower() for p in paragraphs)
    has_sec21 = any("objetivo y alcance" in p.lower() for p in paragraphs)
    has_sec22 = any("descripción de la plataforma" in p.lower() for p in paragraphs)

    # 4. Check tables for bare enums and empty cells
    bare_enum_hits = []
    empty_cells_count = 0
    total_cells = 0
    for t_idx, t in enumerate(doc.tables):
        for r_idx, r in enumerate(t.rows):
            for c_idx, c in enumerate(r.cells):
                total_cells += 1
                txt = c.text.strip()
                if not txt:
                    empty_cells_count += 1
                if BARE_ENUM_RE.fullmatch(txt):
                    bare_enum_hits.append(f"Table {t_idx} [{r_idx},{c_idx}]: '{txt}'")

    # 5. Check Table 6 strengths for orphaned adversatives
    adversative_hits = []
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                lines = [ln.strip() for ln in c.text.splitlines() if ln.strip()]
                for ln in lines:
                    ln_lower = ln.lower()
                    if "fortaleza" in ln_lower:
                        clean = re.sub(r"^[^:]+:\s*", "", ln_lower).strip()
                        if clean.startswith(("no obstante", "sin embargo", "ahora bien", "pero")):
                            adversative_hits.append(ln)

    # Word count
    word_count = sum(len(p.split()) for p in paragraphs)

    return {
        "file_name": doc_path.name,
        "size_bytes": doc_path.stat().st_size,
        "paragraphs_count": len(paragraphs),
        "tables_count": len(doc.tables),
        "total_cells": total_cells,
        "empty_cells": empty_cells_count,
        "total_words": word_count,
        "has_ch2": has_ch2,
        "has_sec21": has_sec21,
        "has_sec22": has_sec22,
        "unresolved_placeholders": unresolved,
        "speculative_hits": speculative_hits,
        "bare_enum_hits": bare_enum_hits,
        "adversative_hits": adversative_hits,
    }


def main() -> None:
    print("=" * 80)
    print("EMPIRICAL FORENSIC INSPECTION OF CURRENT DELIVERABLES (T1 - T10 + TOMO 1)")
    print("=" * 80)

    current_annexes = sorted(CURRENT_DIR.glob("*ASIS.docx"))
    all_current_docs = current_annexes + [TOMO1_PATH]

    current_results = []
    for p in all_current_docs:
        res = inspect_document(p)
        current_results.append(res)
        print(f"\nDocument: {res['file_name']}")
        print(f"  Size: {res['size_bytes']:,} bytes | Paragraphs: {res['paragraphs_count']} | Tables: {res['tables_count']} | Words: {res['total_words']:,}")
        print(f"  Chapter 2 Structure: Ch2={res['has_ch2']}, Sec 2.1={res['has_sec21']}, Sec 2.2={res['has_sec22']}")
        print(f"  Unresolved Placeholders: {len(res['unresolved_placeholders'])} {res['unresolved_placeholders']}")
        print(f"  Hallucinated Speculative Tools: {len(res['speculative_hits'])} {res['speculative_hits']}")
        print(f"  Raw Enum Table Cells: {len(res['bare_enum_hits'])}")
        print(f"  Table 6 Orphaned Adversatives: {len(res['adversative_hits'])}")
        print(f"  Empty Table Cells: {res['empty_cells']} / {res['total_cells']}")

    print("\n" + "=" * 80)
    print("SIDE-BY-SIDE FORENSIC COMPARISON: OLD BASELINE VS CURRENT ARCHITECTURE")
    print("=" * 80)

    comparison_pairs = [
        ("T1", BASELINE_DIR / "T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_01_Data_Center_ASIS.docx"),
        ("T2", BASELINE_DIR / "T2/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx"),
        ("T3", BASELINE_DIR / "T3/Molins_202610_Anexo_03_Redes_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_03_Redes_ASIS.docx"),
        ("T4", BASELINE_DIR / "T4/Molins_202610_Anexo_04_Datos_Storage_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_04_Datos_Storage_ASIS.docx"),
        ("T5", BASELINE_DIR / "T5/Molins_202610_Anexo_05_Resiliencia_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_05_Resiliencia_ASIS.docx"),
        ("T6", BASELINE_DIR / "T6/Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx"),
        ("T7", BASELINE_DIR / "T7/Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx"),
        ("T8", BASELINE_DIR / "T8/Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx"),
        ("T9", BASELINE_DIR / "T9/Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx"),
        ("T10", BASELINE_DIR / "T10/Molins_202610_Anexo_10_Mainframe_Core_ASIS.docx", CURRENT_DIR / "Molins_202610_Anexo_10_Sistemas_Expedicion_Operaciones_ASIS.docx"),
        ("TOMO_1", BASELINE_DIR / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx", TOMO1_PATH),
    ]

    for label, old_p, new_p in comparison_pairs:
        if not old_p.exists() or not new_p.exists():
            print(f"Skipping {label}: missing file")
            continue
        old_res = inspect_document(old_p)
        new_res = inspect_document(new_p)
        print(f"\n--- COMPARISON: {label} ---")
        print(f"  [Metric]                          OLD BASELINE              NEW ARCHITECTURE")
        print(f"  File Size:                        {old_res['size_bytes']:>10,} bytes          {new_res['size_bytes']:>10,} bytes")
        print(f"  Paragraphs:                       {old_res['paragraphs_count']:>10}                {new_res['paragraphs_count']:>10}")
        print(f"  Tables:                           {old_res['tables_count']:>10}                {new_res['tables_count']:>10}")
        print(f"  Total Words:                      {old_res['total_words']:>10,}                {new_res['total_words']:>10,}")
        print(f"  Chapter 2 Present & Populated:    {str(old_res['has_sec21'] and old_res['has_sec22']):>10}                {str(new_res['has_sec21'] and new_res['has_sec22']):>10}")
        print(f"  Hallucinated Tool Count:          {len(old_res['speculative_hits']):>10}                {len(new_res['speculative_hits']):>10}")
        print(f"  Raw Enum Cells (HIGH./etc):       {len(old_res['bare_enum_hits']):>10}                {len(new_res['bare_enum_hits']):>10}")
        print(f"  Orphaned Adversatives (Table 6):  {len(old_res['adversative_hits']):>10}                {len(new_res['adversative_hits']):>10}")


if __name__ == "__main__":
    main()
