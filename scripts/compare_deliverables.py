"""Deliverables Side-by-Side Comparison & Forensic Quality Audit Tool.

Compares a baseline enterprise DOCX deliverable against a newly compiled/remediated
deliverable, producing an empirical Markdown side-by-side audit report.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Any

import docx


def extract_paragraphs(docx_path: Path) -> list[dict[str, Any]]:
    """Extracts non-empty paragraphs and their styles from a DOCX file."""
    doc = docx.Document(str(docx_path))
    extracted = []
    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text:
            extracted.append({
                "index": idx,
                "style": p.style.name if p.style else "Normal",
                "text": text,
            })
    return extracted


def extract_tables(docx_path: Path) -> list[list[list[str]]]:
    """Extracts table contents as 2D string matrices."""
    doc = docx.Document(str(docx_path))
    tables_data = []
    for t in doc.tables:
        t_matrix = []
        for row in t.rows:
            r_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            t_matrix.append(r_cells)
        tables_data.append(t_matrix)
    return tables_data


def audit_forensic_invariants(paragraphs: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Evaluates the 4 critical flaws on the paragraph collection."""
    findings = {
        "scoring_contradictions": [],
        "verbatim_repetitions": [],
        "accusatory_or_informal_tone": [],
        "frankenstein_concatenations": [],
        "generic_filler_quotes": [],
    }

    # 1. Scoring contradiction check
    for p in paragraphs:
        txt = p["text"]
        if ("5.0" in txt or "5,0" in txt) and ("1.00" in txt or "1,00" in txt or "1.0" in txt or "1,0" in txt):
            if "divergencia" not in txt.lower() and "delta" not in txt.lower() and "calibrat" not in txt.lower():
                findings["scoring_contradictions"].append(
                    f"[P{p['index']}] Unreconciled coexistence of 5.0 and 1.0: {txt[:120]}..."
                )

    # 2. Cross-paragraph verbatim repetition
    seen_phrases: dict[str, int] = {}
    for p in paragraphs:
        # Check substantial sentences (> 60 chars)
        sentences = re.split(r"(?<=[.!?])\s+", p["text"])
        for s in sentences:
            s_clean = re.sub(r"\W+", "", s).lower()
            if len(s_clean) > 60:
                if s_clean in seen_phrases:
                    findings["verbatim_repetitions"].append(
                        f"[P{p['index']}] Repetition of phrase previously seen at P{seen_phrases[s_clean]}: {s[:100]}..."
                    )
                else:
                    seen_phrases[s_clean] = p["index"]

    # 3. Tone & dignity check
    pejorative_patterns = [
        r"\b(?:artesanal|artesanales)\b",
        r"\b(?:obsolet[ao]s?)\b",
        r"\b(?:Croacia|Croatia)\b",
        r"\b(?:MoinMoin)\b",
        r"\b(?:un DBA|un arquitecto de Kubernetes)\b",
    ]
    for p in paragraphs:
        txt = p["text"]
        for pat in pejorative_patterns:
            m = re.search(pat, txt, re.IGNORECASE)
            if m:
                findings["accusatory_or_informal_tone"].append(
                    f"[P{p['index']}] Matched pejorative or informal term '{m.group(0)}': {txt[:120]}..."
                )

    # 4. Frankenstein concatenations & regex artifacts
    frankenstein_patterns = [
        r"[a-záéíóú]-[a-záéíóú]",  # glued words with hyphens like "clúster-especialmente"
        r"\b(?:por|en|de)\s+(?:por|en|de)\b",  # double prepositions
        r"\bcondicionad[oa]s?\s+en\s+la\b",  # broken grammar artifact
    ]
    for p in paragraphs:
        txt = p["text"]
        for pat in frankenstein_patterns:
            m = re.search(pat, txt)
            if m:
                findings["frankenstein_concatenations"].append(
                    f"[P{p['index']}] Detected orthopedic syntax pattern '{m.group(0)}': {txt[:120]}..."
                )

    # 5. Generic filler quotes
    filler_patterns = [
        r"\b(?:informes de Gartner|investigaciones de Google SRE|estudios de Forrester)\b",
    ]
    for p in paragraphs:
        txt = p["text"]
        for pat in filler_patterns:
            m = re.search(pat, txt, re.IGNORECASE)
            if m:
                findings["generic_filler_quotes"].append(
                    f"[P{p['index']}] Found generic canned citation '{m.group(0)}': {txt[:120]}..."
                )

    return findings


def generate_side_by_side_report(
    baseline_path: Path,
    target_path: Path,
    output_md: Path,
) -> None:
    """Generates a complete forensic side-by-side Markdown comparison report."""
    base_paras = extract_paragraphs(baseline_path)
    target_paras = extract_paragraphs(target_path)

    base_tables = extract_tables(baseline_path)
    target_tables = extract_tables(target_path)

    base_audit = audit_forensic_invariants(base_paras)
    target_audit = audit_forensic_invariants(target_paras)

    base_words = sum(len(p["text"].split()) for p in base_paras)
    target_words = sum(len(p["text"].split()) for p in target_paras)

    md_lines = [
        "# SIDE-BY-SIDE FORENSIC COMPARISON & QUALITY AUDIT REPORT",
        f"- **Baseline Deliverable:** `{baseline_path}` ({baseline_path.stat().st_size:,} bytes)",
        f"- **Remediated Deliverable:** `{target_path}` ({target_path.stat().st_size:,} bytes)",
        "",
        "---",
        "",
        "## 1. Executive Summary & Structural Invariants",
        "",
        "| Metric | Baseline Version | Remediated Version | Delta |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Paragraph Count** | {len(base_paras)} | {len(target_paras)} | {len(target_paras) - len(base_paras):+d} |",
        f"| **Word Count** | {base_words:,} | {target_words:,} | {target_words - base_words:+d} |",
        f"| **Table Count** | {len(base_tables)} | {len(target_tables)} | {len(target_tables) - len(base_tables):+d} |",
        f"| **Scoring Contradictions** | {len(base_audit['scoring_contradictions'])} | {len(target_audit['scoring_contradictions'])} | {len(target_audit['scoring_contradictions']) - len(base_audit['scoring_contradictions']):+d} |",
        f"| **Verbatim Sentence Repeats** | {len(base_audit['verbatim_repetitions'])} | {len(target_audit['verbatim_repetitions'])} | {len(target_audit['verbatim_repetitions']) - len(base_audit['verbatim_repetitions']):+d} |",
        f"| **Accusatory / Pejorative Terms** | {len(base_audit['accusatory_or_informal_tone'])} | {len(target_audit['accusatory_or_informal_tone'])} | {len(target_audit['accusatory_or_informal_tone']) - len(base_audit['accusatory_or_informal_tone']):+d} |",
        f"| **Frankenstein Syntactic Glitches** | {len(base_audit['frankenstein_concatenations'])} | {len(target_audit['frankenstein_concatenations'])} | {len(target_audit['frankenstein_concatenations']) - len(base_audit['frankenstein_concatenations']):+d} |",
        f"| **Generic Filler Quotes (Gartner/SRE)** | {len(base_audit['generic_filler_quotes'])} | {len(target_audit['generic_filler_quotes'])} | {len(target_audit['generic_filler_quotes']) - len(base_audit['generic_filler_quotes']):+d} |",
        "",
        "---",
        "",
        "## 2. Forensic Flaw Audit: Baseline vs. Remediated",
        "",
    ]

    flaw_titles = [
        ("scoring_contradictions", "1. Scoring Contradictions & Perception Gap"),
        ("verbatim_repetitions", "2. Cross-Pillar Verbatim Echoes"),
        ("accusatory_or_informal_tone", "3. Accusatory, Punitively Biased, or Informal Language"),
        ("frankenstein_concatenations", "4. Frankenstein Concatenations & Regex Mutilations"),
        ("generic_filler_quotes", "5. Generic Canned Filler Citations (Gartner / Google SRE)"),
    ]

    for key, title in flaw_titles:
        md_lines.append(f"### {title}")
        md_lines.append(f"#### Baseline Artifact ({len(base_audit[key])} occurrences):")
        if base_audit[key]:
            for item in base_audit[key][:5]:
                md_lines.append(f"- ❌ {item}")
            if len(base_audit[key]) > 5:
                md_lines.append(f"- *(...and {len(base_audit[key]) - 5} more)*")
        else:
            md_lines.append("- *(Zero defects detected)*")

        md_lines.append(f"#### Remediated Artifact ({len(target_audit[key])} occurrences):")
        if target_audit[key]:
            for item in target_audit[key][:5]:
                md_lines.append(f"- ⚠️ {item}")
            if len(target_audit[key]) > 5:
                md_lines.append(f"- *(...and {len(target_audit[key]) - 5} more)*")
        else:
            md_lines.append("- ✅ **Clean (Zero defects detected)**")
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("## 3. Section-by-Section Key Paragraph Comparisons")
    md_lines.append("")

    # Map headings to find matching sections
    def map_sections(paras: list[dict[str, Any]]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        current_sec = "Preamble"
        sections[current_sec] = []
        for p in paras:
            if p["style"].startswith("Heading") or p["style"].startswith("Título") or (len(p["text"]) < 80 and any(p["text"].startswith(prefix) for prefix in ("3.2", "3.1", "Capítulo", "Chapter"))):
                current_sec = p["text"]
                sections[current_sec] = []
            else:
                sections[current_sec].append(p["text"])
        return sections

    base_secs = map_sections(base_paras)
    target_secs = map_sections(target_paras)

    # Highlight common sections of interest
    all_keys = list(dict.fromkeys(list(base_secs.keys()) + list(target_secs.keys())))
    sample_count = 0
    for sec_name in all_keys:
        if any(term in sec_name.lower() for term in ["kubernetes", "cloud", "automatiz", "observab", "plataforma"]):
            sample_count += 1
            md_lines.append(f"### Section: {sec_name}")
            b_text = "\n\n".join(base_secs.get(sec_name, ["*(Section not present in baseline)*"]))
            t_text = "\n\n".join(target_secs.get(sec_name, ["*(Section not present in remediated version)*"]))

            md_lines.append("#### Baseline Text:")
            md_lines.append(f"> {b_text.replace(chr(10), chr(10) + '> ')}")
            md_lines.append("")
            md_lines.append("#### Remediated Text:")
            md_lines.append(f"> {t_text.replace(chr(10), chr(10) + '> ')}")
            md_lines.append("")

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Comparison report generated at: {output_md}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Side-by-side DOCX deliverable comparator.")
    parser.add_argument("--baseline", type=Path, required=True, help="Path to baseline DOCX")
    parser.add_argument("--target", type=Path, required=True, help="Path to target/remediated DOCX")
    parser.add_argument("--output", type=Path, default=Path("working/out/SIDE_BY_SIDE_COMPARISON.md"), help="Path to output markdown report")
    args = parser.parse_args()

    generate_side_by_side_report(args.baseline, args.target, args.output)


if __name__ == "__main__":
    main()
